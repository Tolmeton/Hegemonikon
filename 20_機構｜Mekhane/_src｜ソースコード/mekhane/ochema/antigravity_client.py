# PROOF: [L2/インフラ] <- mekhane/ochema/ A0→外部LLM接続→LS ConnectRPC クライアント実装
# PURPOSE: Ochēma — Antigravity Language Server クライアント
# REASON: Ultra プランの LLM + セッション管理 + Quota 監視を HGK から利用する橋渡し
"""Ochēma (ὄχημα, 乗り物) — Antigravity Language Server Client.

Local Language Server の ConnectRPC JSON エンドポイントを介して
LLM テキスト生成を行う非公式 Python クライアント。

4-Step API Flow:
    1. StartCascade          → cascade_id 取得
    2. SendUserCascadeMessage → メッセージ送信
    3. GetAllCascadeTrajectories → trajectory_id 取得
    4. GetCascadeTrajectorySteps → LLM 応答取得 (ポーリング)

WARNING: ToS グレーゾーン。実験用途限定。公開禁止。
"""


from __future__ import annotations
from typing import Any, Generator, Optional
import json
import re
import ssl
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

import psutil

# ブリッジ (openai_compat_server 等) → LS の TCP 接続先。ls_daemon.json の "host" が無いときの上書きに使用。
_ENV_LS_CONNECT_HOST = "HGK_LS_CONNECT_HOST"


# --- Data Classes ---

# PURPOSE: 応答テキスト・思考過程・Quota 消費を統一的に返し、呼び出し側の分岐を不要にする
@dataclass
class LLMResponse:
    """LLM からの応答を保持する。"""
    text: str = ""
    thinking: str = ""
    model: str = ""
    token_usage: dict = field(default_factory=dict)
    cascade_id: str = ""
    trajectory_id: str = ""
    raw_steps: list = field(default_factory=list)


# PURPOSE: [L2-auto] Language Server の接続情報。
@dataclass
class LSInfo:
    """Language Server の接続情報。"""
    pid: int = 0
    csrf: str = ""
    port: int = 0
    workspace: str = ""
    all_ports: list = field(default_factory=list)
    is_https: bool = True
    #: ConnectRPC の HTTP(S) 接続先。None のときは環境変数 HGK_LS_CONNECT_HOST または 127.0.0.1
    host: Optional[str] = None
    source: str = "local"
    tunnel_pid: int = 0
    remote_pid: int = 0
    remote_host: Optional[str] = None
    remote_port: int = 0


# --- Constants (from proto.py) ---

from mekhane.ochema.proto import (  # noqa: E402
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT,
    POLL_INTERVAL,
    RPC_START_CASCADE,
    RPC_SEND_MESSAGE,
    RPC_GET_TRAJECTORIES,
    RPC_GET_STEPS,
    RPC_GET_STATUS,
    RPC_MODEL_CONFIG,
    RPC_EXPERIMENT_STATUS,
    STEP_TYPE_PLANNER,
    STEP_STATUS_DONE,
    build_start_cascade,
    build_send_message,
    cascade_turn_complete,
    extract_planner_response,
)

USER_AGENT = "ochema/0.1"

# Episode memory
BRAIN_DIR = os.path.expanduser("~/.gemini/antigravity/brain")


# --- Client ---

# PURPOSE: [L2-auto] Antigravity Language Server の非公式クライアント。
class AntigravityClient:
    """Antigravity Language Server の非公式クライアント。

    Usage:
        client = AntigravityClient()
        response = client.ask("Say hello world")
        print(response.text)
    """

    # PURPOSE: [L2-auto] LS を自動検出して接続する。
    def __init__(self, workspace: str = "oikos", ls_info: Optional[LSInfo] = None):
        """LS を自動検出して接続する。

        Args:
            workspace: ワークスペース名 (psutil プロセス検出のフィルタに使用)
            ls_info: 外部から注入する LSInfo (Non-Standalone LS 等)。
                     指定時は自動検出をスキップする。
        """
        import os
        os.environ["no_proxy"] = "*"
        self.workspace = workspace
        self._ssl_ctx = self._make_ssl_context()
        if ls_info is not None:
            self.ls = ls_info
        else:
            # 1. ~/.gemini/antigravity/ls_daemon.json (デーモン) を優先
            daemon_info = self._load_daemon_info()
            if daemon_info:
                self.ls = daemon_info
            else:
                # 2. 自動検出
                self.ls = self._detect_ls()

    def _load_daemon_info(self) -> Optional[LSInfo]:
        import json
        from pathlib import Path
        path = Path.home() / ".gemini/antigravity/ls_daemon.json"
        
        if not path.exists():
            return None
            
        try:
            with open(path, "r") as f:
                data = json.load(f)

            def _entry_alive(entry: dict) -> bool:
                source = entry.get("source", "local")
                pid = int(entry.get("pid", 0) or 0)
                tunnel_pid = int(entry.get("tunnel_pid", pid) or 0)
                port = int(entry.get("port", 0) or 0)
                if source == "remote":
                    if tunnel_pid > 0:
                        return psutil.pid_exists(tunnel_pid) and port > 0
                    return port > 0
                return psutil.pid_exists(pid)

            def _to_ls_info(entry: dict) -> LSInfo:
                pid = int(entry.get("pid", 0) or 0)
                tunnel_pid = int(entry.get("tunnel_pid", pid) or 0)
                return LSInfo(
                    pid=pid,
                    port=entry.get("port", 0),
                    csrf=entry.get("csrf", ""),
                    workspace=entry.get("workspace", ""),
                    is_https=entry.get("is_https", True),
                    all_ports=[entry.get("port", 0)],
                    host=entry.get("host"),
                    source=entry.get("source", "local"),
                    tunnel_pid=tunnel_pid,
                    remote_pid=int(entry.get("remote_pid", 0) or 0),
                    remote_host=entry.get("remote_host"),
                    remote_port=int(entry.get("remote_port", 0) or 0),
                )
            
            if isinstance(data, list):
                # プール対応 (複数インスタンスからランダム選択)
                valid_instances = [entry for entry in data if _entry_alive(entry)]
                if not valid_instances:
                    return None

                # remote source があれば優先して使用する。
                remote_instances = [e for e in valid_instances if e.get("source") == "remote"]
                if remote_instances:
                    valid_instances = remote_instances
                
                # ラウンドロビン選択
                rr_file = Path("/tmp/hgk_ls_rr_index")
                idx = 0
                if rr_file.exists():
                    try:
                        idx = int(rr_file.read_text().strip())
                    except (OSError, ValueError):
                        pass
                
                idx = (idx + 1) % len(valid_instances)
                try:
                    rr_file.write_text(str(idx))
                except OSError:
                    pass
                
                selected = valid_instances[idx]
                return _to_ls_info(selected)
            else:
                # 従来の単一辞書
                if not _entry_alive(data):
                    return None

                return _to_ls_info(data)
        except (json.JSONDecodeError, KeyError):
            return None

    # PURPOSE: [L2-auto] 関数: pid
    @property
    def pid(self) -> int:
        return self.ls.pid

    # PURPOSE: [L2-auto] 関数: port
    @property
    def port(self) -> int:
        return self.ls.port

    # PURPOSE: [L2-auto] 関数: csrf
    @property
    def csrf(self) -> str:
        return self.ls.csrf

    # --- Public API ---

    # PURPOSE: [L2-auto] LLM にメッセージを送り、応答を取得する。
    def ask(
        self,
        message: str,
        model: str = DEFAULT_MODEL,
        timeout: float = DEFAULT_TIMEOUT,
        response_model: Optional[Any] = None,
    ) -> LLMResponse:
        """LLM にメッセージを送り、応答を取得する。

        4-Step フローを内部で実行:
        1. StartCascade → cascade_id
        2. SendUserCascadeMessage → {}
        3. GetAllCascadeTrajectories → trajectory_id
        4. GetCascadeTrajectorySteps → response (polling)

        Args:
            message: LLM に送るテキスト
            model: モデル名 (enum string)
            timeout: 最大待機秒数
            response_model: 構造化出力のための Pydantic モデル

        Returns:
            LLMResponse with text, thinking, model, token_usage
        """
        import json

        if response_model is not None:
            try:
                schema = response_model.model_json_schema()
            except AttributeError:
                schema = response_model.schema()
            
            # Inject schema into the prompt for Claude via LS
            message = (
                f"{message}\n\n"
                f"IMPORTANT: Respond EXACTLY with a valid JSON object matching the following schema. "
                f"Do not include markdown formatting or any other text before or after the JSON.\n\n"
                f"{json.dumps(schema, indent=2)}\n\n"
                "{"
            )

        # LS は SendUserCascadeMessage で HTTP 応答が返るまで数十秒かかることがある。
        # _raw_rpc 既定 5s だと socket 読み取りで TimeoutError になる（get_status だけ成功する症状）。
        rpc_http = max(30.0, float(timeout))

        # Step 1: Start Cascade
        cascade_id = self._start_cascade(rpc_http)

        # Step 2: Send Message
        self._send_message(cascade_id, message, model, rpc_http)

        # Step 3-4: Poll for response
        resp = self._poll_response(
            cascade_id, timeout, min_planner_count=1, http_timeout=rpc_http,
        )

        if response_model is not None and not resp.text.strip().startswith("{") and not resp.text.strip().startswith("[") and not resp.text.strip().startswith("```"):
            resp.text = "{" + resp.text
            
        return resp

    def chat(
        self,
        message: str,
        model: str = DEFAULT_MODEL,
        cascade_id: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        response_model: Optional[Any] = None,
    ) -> LLMResponse:
        """ステートフルチャット: cascadeId を再利用して会話履歴を保持する。

        LS はサーバーサイドで cascadeId ごとに会話履歴を管理するため、
        同じ cascadeId に追加メッセージを送ると文脈を維持した応答が返る。

        Args:
            message: LLM に送るテキスト
            model: モデル名 (enum string)
            cascade_id: 再利用する cascade_id (None → 新規開始)
            timeout: 最大待機秒数
            response_model: 構造化出力のための Pydantic モデル

        Returns:
            LLMResponse with text, thinking, model, cascade_id
            cascade_id を保持して次回の呼び出しに渡すこと。
        """
        import json

        if response_model is not None:
            try:
                schema = response_model.model_json_schema()
            except AttributeError:
                schema = response_model.schema()
            
            # Inject schema into the prompt for Claude via LS
            message = (
                f"{message}\n\n"
                f"IMPORTANT: Respond EXACTLY with a valid JSON object matching the following schema. "
                f"Do not include markdown formatting or any other text before or after the JSON.\n\n"
                f"{json.dumps(schema, indent=2)}\n\n"
                "{"
            )

        rpc_http = max(30.0, float(timeout))

        # cascade_id が未指定なら新規開始
        if not cascade_id:
            cascade_id = self._start_cascade(rpc_http)
            min_planner_count = 1
        else:
            # 既存 cascade: 送信前のプランナーステップ数を取得
            min_planner_count = self._count_planner_steps(cascade_id) + 1

        # 同じ cascade に追加メッセージを送信
        self._send_message(cascade_id, message, model, rpc_http)

        # ポーリングで応答を取得 (min_planner_count 以上の DONE ステップを待つ)
        resp = self._poll_response(
            cascade_id, timeout, min_planner_count, http_timeout=rpc_http,
        )

        if response_model is not None and not resp.text.strip().startswith("{") and not resp.text.strip().startswith("[") and not resp.text.strip().startswith("```"):
            resp.text = "{" + resp.text
            
        return resp

    def chat_stream(
        self,
        message: str,
        model: str = DEFAULT_MODEL,
        timeout: float = DEFAULT_TIMEOUT,
        **kwargs,
    ) -> Generator[str, None, None]:
        """LLM にメッセージを送り、応答をトークン単位 (疑似ストリーミング) で取得する。
        
        Args:
            message: LLM に送るテキスト
            model: モデル名 (enum string)
            timeout: 最大待機秒数
            kwargs: 無視される引数 (thinking_budgetなど)
            
        Yields:
            生成されたテキストの差分 (デルタ)
        """
        import time
        from mekhane.ochema.proto import (
            RPC_GET_TRAJECTORIES,
            RPC_GET_STEPS,
            STEP_TYPE_PLANNER,
            STEP_STATUS_DONE,
            POLL_INTERVAL,
        )

        rpc_http = max(30.0, float(timeout))

        # Step 1: Start Cascade
        cascade_id = self._start_cascade(rpc_http)

        # Step 2: Send Message
        self._send_message(cascade_id, message, model, rpc_http)

        # Step 3-4: Poll for response and yield deltas
        start_time = time.time()
        trajectory_id = ""
        yielded_length = 0

        while time.time() - start_time < timeout:
            if not trajectory_id:
                try:
                    trajs = self._rpc(
                        RPC_GET_TRAJECTORIES, {}, http_timeout=rpc_http,
                    )
                    summaries = trajs.get("trajectorySummaries", {})
                    cascade_summary = summaries.get(cascade_id, {})
                    if cascade_summary:
                        trajectory_id = cascade_summary.get("trajectoryId", "")
                except (json.JSONDecodeError, KeyError):
                    pass

            if trajectory_id:
                try:
                    steps_result = self._rpc(
                        RPC_GET_STEPS,
                        {
                            "cascadeId": cascade_id,
                            "trajectoryId": trajectory_id,
                        },
                        http_timeout=rpc_http,
                    )
                    steps = steps_result.get("steps", [])
                    turn_state = steps_result.get("turnState", "")

                    # 現在の LLM 応援テキスト (plannerResponse) を抽出
                    current_text = ""
                    for s in steps:
                        if s.get("type") == STEP_TYPE_PLANNER:
                            parsed = extract_planner_response(s)
                            current_text = parsed.get("text") or ""

                    if current_text and len(current_text) > yielded_length:
                        chunk = current_text[yielded_length:]
                        yield chunk
                        yielded_length = len(current_text)

                    if cascade_turn_complete(
                        turn_state, steps, min_planner_count=1,
                    ):
                        return
                except (json.JSONDecodeError, KeyError):
                    pass

            time.sleep(POLL_INTERVAL)

        yield "\\n[Error: Stream timed out]"

    # PURPOSE: [L2-auto] LS のユーザーステータスを取得する。接続確認にも使用。
    def get_status(self) -> dict:
        """LS のユーザーステータスを取得する。接続確認にも使用。"""
        return self._rpc(RPC_GET_STATUS, {
            "metadata": {
                "ideName": "antigravity",
                "extensionName": "antigravity",
                "locale": "en",
            }
        })

    # PURPOSE: [L2-auto] 利用可能なモデル一覧を取得する。
    def list_models(self) -> list[dict]:
        """利用可能なモデル一覧を取得する。"""
        status = self.get_status()
        configs = (
            status.get("userStatus", {})
            .get("cascadeModelConfigData", {})
            .get("clientModelConfigs", [])
        )
        return [
            {
                "name": c.get("modelOrAlias", {}).get("model", ""),
                "label": c.get("label", ""),
                "remaining": round(
                    c.get("quotaInfo", {}).get("remainingFraction", 0) * 100
                ),
            }
            for c in configs
            if c.get("quotaInfo")
        ]

    # PURPOSE: [L2-auto] 全モデルの Quota 残量と設定をリアルタイムで取得する。
    def quota_status(self) -> dict:
        """全モデルの Quota 残量と設定をリアルタイムで取得する。

        Returns:
            dict with models (list), experiments (list), total_models (int)
        """
        # モデル設定と Quota
        config = self._rpc(RPC_MODEL_CONFIG, {})
        models = []
        for c in config.get("clientModelConfigs", []):
            quota = c.get("quotaInfo", {})
            models.append({
                "label": c.get("label", ""),
                "model": c.get("modelOrAlias", {}).get("model", ""),
                "remaining_pct": round(
                    quota.get("remainingFraction", 0) * 100
                ),
                "reset_time": quota.get("resetTime", ""),
                "images": c.get("supportsImages", False),
                "recommended": c.get("isRecommended", False),
            })

        # Experiment flags (context/memory 関連のみ)
        exp_data = self._rpc(RPC_EXPERIMENT_STATUS, {})
        context_keys = {
            "CASCADE_USE_EXPERIMENT_CHECKPOINTER",
            "CASCADE_GLOBAL_CONFIG_OVERRIDE",
            "CASCADE_USER_MEMORIES_IN_SYS_PROMPT",
            "CASCADE_ENABLE_AUTOMATED_MEMORIES",
            "CHAT_TOKENS_SOFT_LIMIT",
            "CHAT_COMPLETION_TOKENS_SOFT_LIMIT",
            "CASCADE_MEMORY_CONFIG_OVERRIDE",
            "MAX_PAST_TRAJECTORY_TOKENS_FOR_RETRIEVAL",
            "CUMULATIVE_PROMPT_CASCADE_CONFIG",
            "CORTEX_CONFIG",
        }
        experiments = [
            {
                "key": s.get("experimentKey", ""),
                "enabled": s.get("enabled", False),
            }
            for s in exp_data.get("status", [])
            if s.get("experimentKey", "") in context_keys
        ]

        return {
            "models": models,
            "experiments": experiments,
            "total_models": len(models),
        }

    # PURPOSE: [L2-auto] セッション情報を取得する。
    def session_info(self, cascade_id: Optional[str] = None) -> dict:
        """セッション情報を取得する。

        Args:
            cascade_id: 特定セッションの ID (省略時は全セッション一覧)

        Returns:
            dict with sessions (list) or session detail
        """
        data = self._rpc(RPC_GET_TRAJECTORIES, {})
        summaries = data.get("trajectorySummaries", {})

        sessions = []
        for cid, info in summaries.items():
            session = {
                "cascade_id": cid,
                "trajectory_id": info.get("trajectoryId", ""),
                "step_count": info.get("stepCount", 0),
                "summary": info.get("summary", ""),
                "status": info.get("status", ""),
                "created": info.get("createdTime", ""),
                "modified": info.get("lastModifiedTime", ""),
                "last_input_time": info.get("lastUserInputTime", ""),
            }
            sessions.append(session)

        if cascade_id:
            # 特定セッションの詳細
            for s in sessions:
                if s["cascade_id"] == cascade_id:
                    # ステップ詳細も取得
                    steps_data = self._rpc(RPC_GET_STEPS, {
                        "cascadeId": cascade_id,
                        "trajectoryId": s["trajectory_id"],
                    })
                    step_types: dict[str, int] = {}
                    for step in steps_data.get("steps", []):
                        st = step.get("type", "UNKNOWN")
                        step_types[st] = step_types.get(st, 0) + 1
                    s["step_types"] = step_types
                    return s
            return {"error": f"cascade_id {cascade_id} not found"}

        # 最新順にソート
        sessions.sort(key=lambda x: x.get("modified", ""), reverse=True)
        return {
            "total": len(sessions),
            "sessions": sessions[:20],  # 最新20件
        }

    # PURPOSE: [L2-auto] セッションの会話内容を読み取る。
    def session_read(
        self,
        cascade_id: str,
        max_turns: int = 10,
        full: bool = False,
    ) -> dict:
        """セッションの会話内容を読み取る。

        ステップを種別ごとにパースし、時系列の会話ログとして返す。

        Args:
            cascade_id: セッションの cascade_id
            max_turns: 返す最大ターン数 (デフォルト: 10)
            full: True → フル取得 (上限 30000 文字)

        Returns:
            dict with conversation (list of turns), metadata
        """
        # trajectory_id を取得
        info = self.session_info(cascade_id)
        if "error" in info:
            return info
        trajectory_id = info.get("trajectory_id", "")
        if not trajectory_id:
            return {"error": f"No trajectory for cascade {cascade_id}"}

        # 全ステップを取得
        steps_data = self._rpc(RPC_GET_STEPS, {
            "cascadeId": cascade_id,
            "trajectoryId": trajectory_id,
        })
        steps = steps_data.get("steps", [])

        # ステップを会話ターンにパース
        conversation: list[dict] = []
        max_content = 30000 if full else 2000

        for step in steps:
            step_type = step.get("type", "")
            status = step.get("status", "")

            if step_type == "CORTEX_STEP_TYPE_USER_REQUEST":
                # ユーザー入力
                items = step.get("userRequest", {}).get("items", [])
                text = ""
                for item in items:
                    if "text" in item:
                        text += item["text"]
                if text:
                    conversation.append({
                        "role": "user",
                        "content": text[:max_content],
                        "truncated": len(text) > max_content,
                    })

            elif step_type == "CORTEX_STEP_TYPE_PLANNER_RESPONSE":
                # Claude 応答
                pr = step.get("plannerResponse", {})
                text = pr.get("response", "")
                model = pr.get("generatorModel", "")
                if text:
                    conversation.append({
                        "role": "assistant",
                        "content": text[:max_content],
                        "model": model,
                        "truncated": len(text) > max_content,
                    })

            elif step_type == "CORTEX_STEP_TYPE_MCP_TOOL":
                # ツール呼出し (サマリのみ)
                tool_info = step.get("mcpToolCall", step.get("toolCall", {}))
                tool_name = tool_info.get("toolName", tool_info.get("name", "unknown"))
                tool_status = "done" if status == "CORTEX_STEP_STATUS_DONE" else status
                conversation.append({
                    "role": "tool",
                    "tool": tool_name,
                    "status": tool_status,
                })

            elif step_type == "CORTEX_STEP_TYPE_TOOL_CALL":
                # 内部ツール呼出し
                tool_call = step.get("toolCall", {})
                tool_name = tool_call.get("name", "unknown")
                conversation.append({
                    "role": "tool",
                    "tool": tool_name,
                    "status": "done" if status == "CORTEX_STEP_STATUS_DONE" else status,
                })

        # 最新 N ターン
        if not full and len(conversation) > max_turns * 3:
            # user+assistant+tool で約3エントリ/ターン
            conversation = conversation[-(max_turns * 3):]

        return {
            "cascade_id": cascade_id,
            "trajectory_id": trajectory_id,
            "total_steps": len(steps),
            "total_turns": len(conversation),
            "summary": info.get("summary", ""),
            "conversation": conversation,
        }

    # PURPOSE: [L2-auto] 過去セッションのエピソード記憶 (.system_generated/steps/) にアクセスする。
    def session_episodes(self, brain_id: Optional[str] = None) -> dict:
        """過去セッションのエピソード記憶 (.system_generated/steps/) にアクセスする。

        Args:
            brain_id: 特定 brain の ID (省略時は全 brain 一覧)

        Returns:
            dict with episodes summary or specific episode contents
        """
        if not os.path.isdir(BRAIN_DIR):
            return {"error": f"Brain directory not found: {BRAIN_DIR}"}

        if brain_id:
            # 特定 brain のエピソード取得
            brain_path = os.path.join(BRAIN_DIR, brain_id, ".system_generated", "steps")
            if not os.path.isdir(brain_path):
                return {"error": f"No episodes for brain {brain_id}"}

            episodes = []
            for step_dir in sorted(os.listdir(brain_path)):
                output_file = os.path.join(brain_path, step_dir, "output.txt")
                if os.path.isfile(output_file):
                    size = os.path.getsize(output_file)
                    # 先頭200文字だけ読む
                    with open(output_file, "r", errors="replace") as f:
                        preview = f.read(200)
                    episodes.append({
                        "step": int(step_dir) if step_dir.isdigit() else step_dir,
                        "size_bytes": size,
                        "preview": preview,
                    })
            return {
                "brain_id": brain_id,
                "total_episodes": len(episodes),
                "episodes": episodes,
            }

        # 全 brain 一覧
        brains = []
        for entry in os.listdir(BRAIN_DIR):
            sys_gen = os.path.join(BRAIN_DIR, entry, ".system_generated", "steps")
            if os.path.isdir(sys_gen):
                count = len([
                    d for d in os.listdir(sys_gen)
                    if os.path.isfile(os.path.join(sys_gen, d, "output.txt"))
                ])
                if count > 0:
                    # brain のアーティファクト名を取得
                    task_file = os.path.join(BRAIN_DIR, entry, "task.md")
                    title = ""
                    if os.path.isfile(task_file):
                        with open(task_file, "r", errors="replace") as f:
                            for line in f:
                                if line.startswith("# "):
                                    title = line[2:].strip()
                                    break
                    brains.append({
                        "brain_id": entry,
                        "episode_count": count,
                        "title": title,
                    })
        brains.sort(key=lambda x: x["episode_count"], reverse=True)
        return {
            "total_brains": len(brains),
            "brains": brains,
        }

    # --- Proposal A: Context Rot Detection ---

    # PURPOSE: [L2-auto] コンテキスト健全性を評価する (v2 積極介入型)。
    def context_health(self, cascade_id: Optional[str] = None) -> dict:
        """コンテキスト健全性を評価する (v2 積極介入型)。

        tool-mastery.md §5.5 v2 の N chat messages 閾値に基づく:
            ≤30:  🟢 HEALTHY
            31-40: 🟡 WARNING     — 中間セーブ強制
            41-50: 🟠 PRE_DANGER  — 新規タスク受付停止
            >50:  🔴 DANGER      — /bye 強制

        Args:
            cascade_id: 特定セッション (省略時は最新の RUNNING セッション)

        Returns:
            dict with level, message, step_count, recommendation, actions
        """
        sessions = self.session_info()
        if "error" in sessions:
            return sessions

        target = None
        if cascade_id:
            for s in sessions.get("sessions", []):
                if s["cascade_id"] == cascade_id:
                    target = s
                    break
        else:
            # 最新の RUNNING セッション
            for s in sessions.get("sessions", []):
                if "RUNNING" in s.get("status", ""):
                    target = s
                    break
            # なければ最新セッション
            if not target and sessions.get("sessions"):
                target = sessions["sessions"][0]

        if not target:
            return {"level": "unknown", "message": "No sessions found"}

        step_count = target.get("step_count", 0)

        if step_count <= 30:
            level = "healthy"
            icon = "🟢"
            message = "Context is healthy"
            recommendation = None
            actions = []
        elif step_count <= 40:
            level = "warning"
            icon = "🟡"
            message = "Context pressure rising — savepoint recommended"
            recommendation = "Generate savepoint NOW. Consider /bye soon"
            actions = ["savepoint", "wm_record"]
        elif step_count <= 50:
            level = "pre_danger"
            icon = "🟠"
            message = "Context Rot imminent — no new tasks"
            recommendation = "Stop accepting new tasks. Complete current work and /bye"
            actions = ["no_new_tasks", "propose_bye"]
        else:
            level = "danger"
            icon = "🔴"
            message = "Context Rot risk HIGH — /bye mandatory"
            recommendation = "/bye NOW — generate Handoff immediately"
            actions = ["force_bye", "auto_handoff"]

        # Quota も統合
        try:
            quota = self.quota_status()
            low_quota_models = [
                m["label"] for m in quota.get("models", [])
                if m["remaining_pct"] < 20
            ]
        except (json.JSONDecodeError, KeyError):
            low_quota_models = []

        return {
            "level": level,
            "icon": icon,
            "message": message,
            "step_count": step_count,
            "cascade_id": target.get("cascade_id", ""),
            "summary": target.get("summary", ""),
            "recommendation": recommendation,
            "actions": actions,
            "low_quota_models": low_quota_models,
        }

    # PURPOSE: [L2-auto] コンテキスト圧縮の提案を生成する (N-4 (旧 BC-18) 連携)。
    def suggest_compression(self, cascade_id: Optional[str] = None) -> dict:
        """コンテキスト圧縮の提案を生成する。

        BC-18 (→N-4/θ4.1: コンテキスト予算意識) と連携し、セッションの健全性に基づいて
        圧縮戦略を提案する。

        分析:
        1. context_health() でセッション状態を取得
        2. ステップ数に応じた圧縮戦略を決定
        3. Chroma Research の知見を適用した提案を生成

        Args:
            cascade_id: 特定セッション (省略時は最新)

        Returns:
            dict with health, strategies, academic_insights
        """
        health = self.context_health(cascade_id)
        if health.get("level") == "unknown":
            return {"error": "No session found for compression analysis"}

        step_count = health.get("step_count", 0)
        strategies = []

        # --- 段階別圧縮戦略 ---
        if step_count > 20:
            strategies.append({
                "type": "savepoint",
                "priority": "medium",
                "description": "中間セーブを生成し、現在の作業状態を永続化",
                "path": "~/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/a_引継_handoff/savepoint_*.md",
            })

        if step_count > 30:
            strategies.append({
                "type": "topic_pruning",
                "priority": "high",
                "description": "完了済みトピックの要約化。詳細をドロップし要約のみ保持",
                "estimated_savings": "30-50% of completed topic tokens",
            })

        if step_count > 40:
            strategies.append({
                "type": "tool_output_summary",
                "priority": "critical",
                "description": "過去のツール出力を要約に置換。view_file 結果等の大量テキストを圧縮",
                "estimated_savings": "up to 90% of tool output tokens",
            })
            strategies.append({
                "type": "session_split",
                "priority": "critical",
                "description": "/bye → Handoff → 新セッション。コンテキストを完全リセット",
                "estimated_savings": "100% (fresh context)",
            })

        # --- Chroma Research 知見の運用化 ---
        academic_insights = [
            {
                "finding": "importance_over_category",
                "description": "情報は論理的カテゴリ順ではなく重要度順に配置すべき",
                "action": "Handoff 内の情報を重要度降順に再配置",
                "source": "Chroma Research: shuffled > logically ordered",
            },
            {
                "finding": "assembly_phase",
                "description": "検索結果はそのまま注入せず組立フェーズを挟むべき",
                "action": "PKS/Mneme の検索結果を要約してからコンテキストに注入",
                "source": "Chroma Research: small-grain search → large-grain assembly",
            },
            {
                "finding": "noise_filter",
                "description": "無関連情報は性能を急速に劣化させる",
                "action": "コンテキストに含める情報を現タスクとの関連度でフィルタ",
                "source": "Chroma Research: low-similarity needles → rapid degradation",
            },
        ]

        return {
            "health": health,
            "strategies": strategies,
            "strategy_count": len(strategies),
            "academic_insights": academic_insights,
            "summary": (
                f"{health['icon']} Step {step_count}: "
                f"{len(strategies)} compression strategies available"
            ),
        }

    # --- Proposal C: Multi-Model Orchestration ---

    # Model routing table: task keywords → preferred model
    _MODEL_ROUTES = {
        # Claude Thinking — deep analysis, security, architecture
        "MODEL_PLACEHOLDER_M35": [
            "security", "audit", "architecture", "design", "review",
            "analyze", "explain", "why", "philosophy", "proof",
        ],
        # Gemini Flash — speed, simple tasks
        "MODEL_PLACEHOLDER_M18": [
            "translate", "format", "list", "simple", "quick",
            "calculate", "convert", "summarize",
        ],
        # Gemini Pro — general purpose, multimodal
        "MODEL_PLACEHOLDER_M8": [
            "image", "video", "multimodal", "diagram", "chart",
        ],
    }

    # Fallback chain
    _MODEL_FALLBACK = {
        "MODEL_PLACEHOLDER_M35": "MODEL_PLACEHOLDER_M26",
        "MODEL_PLACEHOLDER_M26": "MODEL_PLACEHOLDER_M37",
        "MODEL_PLACEHOLDER_M37": "MODEL_PLACEHOLDER_M18",
        "MODEL_PLACEHOLDER_M8": "MODEL_PLACEHOLDER_M18",
        "MODEL_PLACEHOLDER_M18": "MODEL_PLACEHOLDER_M35",
    }

    # PURPOSE: [L2-auto] タスク内容に応じて最適モデルを自動選択し、LLM に問い合わせる。
    def smart_ask(
        self,
        message: str,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> LLMResponse:
        """タスク内容に応じて最適モデルを自動選択し、LLM に問い合わせる。

        T2 Krisis priority rules を内部で再現:
            1. キーワードマッチでモデルを選択
            2. Quota 残量チェック (20%未満ならフォールバック)
            3. デフォルトは Claude Sonnet 4.6

        Args:
            message: LLM に送るテキスト
            timeout: 最大待機秒数

        Returns:
            LLMResponse (model フィールドに実際に使用されたモデル名)
        """
        selected = self._select_model(message)
        return self.ask(message, model=selected, timeout=timeout)

    # PURPOSE: [L2-auto] メッセージ内容と Quota に基づいてモデルを選択する。
    def _select_model(self, message: str) -> str:
        """メッセージ内容と Quota に基づいてモデルを選択する。"""
        msg_lower = message.lower()

        # Step 1: キーワードマッチ
        best_model = DEFAULT_MODEL
        best_score = 0
        for model, keywords in self._MODEL_ROUTES.items():
            score = sum(1 for kw in keywords if kw in msg_lower)
            if score > best_score:
                best_score = score
                best_model = model

        # Step 2: Quota チェック → フォールバック
        try:
            quota = self.quota_status()
            model_quota = {
                m["model"]: m["remaining_pct"]
                for m in quota.get("models", [])
            }

            current = best_model
            attempts = 0
            while attempts < 3:
                remaining = model_quota.get(current, 100)
                if remaining >= 20:
                    return current
                # Quota 不足 → フォールバック
                fallback = self._MODEL_FALLBACK.get(current)
                if not fallback:
                    break
                current = fallback
                attempts += 1
        except (urllib.error.URLError, json.JSONDecodeError, KeyError):
            pass

        return best_model

    # --- Proposal D: Session Archive ---

    # PURPOSE: [L2-auto] セッションを Markdown でアーカイブする。
    def archive_sessions(
        self,
        output_dir: Optional[str] = None,
        max_sessions: int = 5,
        since: Optional[str] = None,
    ) -> dict:
        """セッションを Markdown でアーカイブする。

        Args:
            output_dir: 出力ディレクトリ (デフォルト: ~/oikos/mneme/.ochema/sessions/)
            max_sessions: 最大エクスポート数
            since: この日時以降のセッションのみ (ISO format)

        Returns:
            dict with exported (list of paths), skipped (int)
        """
        if output_dir is None:
            output_dir = os.path.expanduser(
                "~/oikos/mneme/.ochema/sessions"
            )
        os.makedirs(output_dir, exist_ok=True)

        sessions = self.session_info()
        if "error" in sessions:
            return sessions

        exported: list[str] = []
        skipped = 0

        for s in sessions.get("sessions", [])[:max_sessions]:
            cid = s["cascade_id"]
            modified = s.get("modified", "")

            # since フィルタ
            if since and modified < since:
                skipped += 1
                continue

            # 既にエクスポート済みか確認
            filename = f"session_{cid[:12]}_{modified[:10]}.md"
            filepath = os.path.join(output_dir, filename)
            if os.path.exists(filepath):
                skipped += 1
                continue

            # 会話を取得
            try:
                conv = self.session_read(cid, max_turns=50, full=True)
            except (OSError, json.JSONDecodeError, KeyError):
                skipped += 1
                continue

            # Markdown 生成
            lines = [
                f"# Session {cid[:12]}",
                "",
                f"- **Cascade ID**: `{cid}`",
                f"- **Modified**: {modified}",
                f"- **Steps**: {conv.get('total_steps', 0)}",
                f"- **Summary**: {conv.get('summary', '(none)')}",
                "",
                "---",
                "",
            ]

            for turn in conv.get("conversation", []):
                role = turn.get("role", "")
                if role == "user":
                    lines.append("## 👤 User\n")
                    lines.append(turn.get("content", ""))
                    lines.append("")
                elif role == "assistant":
                    model = turn.get("model", "")
                    lines.append(f"## 🤖 Assistant ({model})\n")
                    lines.append(turn.get("content", ""))
                    lines.append("")
                elif role == "tool":
                    tool = turn.get("tool", "")
                    lines.append(f"- 🔧 `{tool}` ({turn.get('status', '')})")

            # ファイル書き出し
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            exported.append(filepath)

        return {
            "exported": exported,
            "skipped": skipped,
            "output_dir": output_dir,
        }

    # --- Internal: LS Detection ---

    # PURPOSE: [L2-auto] Language Server プロセスを検出し、接続情報を返す。
    def _detect_ls(self) -> LSInfo:
        """Language Server プロセスを検出し、接続情報を返す。

        find_ls_processes() + get_process_ports() ベースの
        クロスプラットフォーム実装。
        """
        from mekhane.ochema.ls_manager import find_ls_processes, get_process_ports

        info = LSInfo(workspace=self.workspace)
        ws_normalized = self.workspace.replace("-", "_")

        # Step 1: 共通関数でプロセス検出
        # K9 fix: workspace_filter を渡して Non-Standalone LS (nonstd_*) を除外
        candidates = find_ls_processes(self.workspace)

        # ワークスペースで絞り込む (Non-Standalone LS を明示除外)
        target = None
        for c in candidates:
            # K9 fix: nonstd_ workspace は IDE LS ではないため除外
            if "nonstd_" in c.cmdline_str:
                continue
            cmdline_normalized = c.cmdline_str.replace("-", "_")
            if ws_normalized in cmdline_normalized or "oikos" in c.cmdline_str:
                target = c
                break

        # 完全一致がなく候補が1つだけなら採用 (Windows 等への対応)
        # K9 fix: ただし Non-Standalone LS は除外
        if not target and len(candidates) == 1:
            c = candidates[0]
            if "nonstd_" not in c.cmdline_str:
                target = c

        if not target:
            raise RuntimeError(
                f"Language Server not found (workspace: {self.workspace})"
            )

        info.pid = target.pid

        # CSRF トークン取得
        csrf_match = re.search(r"csrf_token[=\s]+(\S+)", target.cmdline_str)
        if not csrf_match:
            raise RuntimeError("CSRF token not found in process cmdline")
        info.csrf = csrf_match.group(1)

        # Step 2: 共通関数でリスニングポートを取得 (権限問題なし)
        ports = get_process_ports(info.pid)
        if not ports:
            raise RuntimeError(f"No listening ports for PID {info.pid}")
        info.all_ports = ports

        # Step 3: 全ポート試行 → GetUserStatus 成功で確定
        for port in info.all_ports:
            try:
                result = self._raw_rpc(port, info.csrf, RPC_GET_STATUS, {
                    "metadata": {
                        "ideName": "antigravity",
                        "extensionName": "antigravity",
                        "locale": "en",
                    }
                }, timeout=3)
                if "userStatus" in result:
                    info.port = port
                    return info
            except (json.JSONDecodeError, KeyError):
                continue

        raise RuntimeError(
            f"All ports failed ({info.all_ports}) for GetUserStatus"
        )

    # --- Internal: 4-Step Flow ---

    # CortexTrajectorySource enum (from extension.js proto3 定義):
    #   0=UNSPECIFIED, 1=CASCADE_CLIENT, 2=EXPLAIN_PROBLEM,
    #   12=INTERACTIVE_CASCADE (IDE 標準), 15=SDK
    SOURCE_INTERACTIVE_CASCADE = 12

    # PURPOSE: [L2-auto] Step 1: StartCascade → cascade_id を取得。
    def _start_cascade(self, http_timeout: float) -> str:
        """Step 1: StartCascade → cascade_id を取得 (v8 proto via proto.py)."""
        result = self._rpc(
            RPC_START_CASCADE, build_start_cascade(), http_timeout=http_timeout,
        )
        cascade_id = result.get("cascadeId", "")
        if not cascade_id:
            raise RuntimeError(f"StartCascade returned no cascadeId: {result}")
        return cascade_id

    # PURPOSE: [L2-auto] Step 2: SendUserCascadeMessage → メッセージ送信。
    def _send_message(
        self, cascade_id: str, message: str, model: str, http_timeout: float,
    ) -> None:
        """Step 2: SendUserCascadeMessage → メッセージ送信 (v8 proto via proto.py)."""
        self._rpc(
            RPC_SEND_MESSAGE,
            build_send_message(cascade_id, message, model),
            http_timeout=http_timeout,
        )

    # PURPOSE: [L2-auto] Step 3-4: ポーリングで LLM 応答を取得。
    def _count_planner_steps(self, cascade_id: str) -> int:
        """既存 cascade のプランナーレスポンス DONE ステップ数を返す。"""
        try:
            trajs = self._rpc(RPC_GET_TRAJECTORIES, {})
            summary = trajs.get("trajectorySummaries", {}).get(cascade_id, {})
            trajectory_id = summary.get("trajectoryId", "")
            if not trajectory_id:
                return 0
            steps_result = self._rpc(RPC_GET_STEPS, {
                "cascadeId": cascade_id,
                "trajectoryId": trajectory_id,
            })
            steps = steps_result.get("steps", [])
            return sum(
                1 for s in steps
                if s.get("type") == STEP_TYPE_PLANNER
                and s.get("status") == STEP_STATUS_DONE
            )
        except (json.JSONDecodeError, KeyError):
            return 0

    def _poll_response(
        self,
        cascade_id: str,
        timeout: float,
        min_planner_count: int = 1,
        *,
        http_timeout: float | None = None,
    ) -> LLMResponse:
        """Step 3-4: ポーリングで LLM 応答を取得。

        Args:
            min_planner_count: DONE なプランナーステップがこの数以上で完了とみなす。
                              Turn 2 以降では、送信前のステップ数 + 1 を指定する。
            http_timeout: GetTrajectories/GetSteps の urllib 読み取り上限 (秒)。
        """
        rpc_http = (
            float(http_timeout)
            if http_timeout is not None
            else max(30.0, float(timeout))
        )
        start_time = time.time()
        trajectory_id = ""

        while time.time() - start_time < timeout:
            # Step 3: trajectory_id を取得
            if not trajectory_id:
                try:
                    trajs = self._rpc(
                        RPC_GET_TRAJECTORIES, {}, http_timeout=rpc_http,
                    )
                    summaries = trajs.get("trajectorySummaries", {})
                    cascade_summary = summaries.get(cascade_id, {})
                    if cascade_summary:
                        trajectory_id = cascade_summary.get(
                            "trajectoryId", ""
                        )
                except (json.JSONDecodeError, KeyError):
                    pass

            # Step 4: trajectory のステップを取得
            if trajectory_id:
                try:
                    steps_result = self._rpc(
                        RPC_GET_STEPS,
                        {
                            "cascadeId": cascade_id,
                            "trajectoryId": trajectory_id,
                        },
                        http_timeout=rpc_http,
                    )
                    steps = steps_result.get("steps", [])
                    turn_state = steps_result.get("turnState", "")

                    if cascade_turn_complete(
                        turn_state, steps, min_planner_count,
                    ):
                        return self._parse_steps(
                            steps, cascade_id, trajectory_id
                        )
                except (json.JSONDecodeError, KeyError):
                    pass

            time.sleep(POLL_INTERVAL)

        raise TimeoutError(
            f"LLM response timed out after {timeout}s "
            f"(cascade_id={cascade_id})"
        )

    # PURPOSE: [L2-auto] ステップから LLM 応答をパースする。
    def _parse_steps(
        self,
        steps: list,
        cascade_id: str,
        trajectory_id: str,
    ) -> LLMResponse:
        """ステップから LLM 応答をパースする。

        walkthrough.md の構造:
        - type: CORTEX_STEP_TYPE_PLANNER_RESPONSE
        - plannerResponse: {response, thinking, generatorModel, ...}
        """
        response = LLMResponse(
            cascade_id=cascade_id,
            trajectory_id=trajectory_id,
            raw_steps=steps,
        )

        for step in steps:
            step_type = step.get("type", "")
            if step_type == STEP_TYPE_PLANNER:
                parsed = extract_planner_response(step)
                if parsed["text"]:
                    response.text += parsed["text"]
                if parsed["thinking"]:
                    response.thinking += parsed["thinking"]
                if parsed["model"]:
                    response.model = parsed["model"]
                if parsed["token_usage"]:
                    response.token_usage = parsed["token_usage"]
                # Thinking metadata — 最後のステップの値で上書き
                if parsed["thinking_signature"]:
                    response.thinking_signature = parsed["thinking_signature"]
                if parsed["thinking_duration"]:
                    response.thinking_duration = parsed["thinking_duration"]
                if parsed["stop_reason"]:
                    response.stop_reason = parsed["stop_reason"]
                if parsed["message_id"]:
                    response.message_id = parsed["message_id"]

        return response

    # --- Internal: HTTP/RPC ---

    # PURPOSE: [L2-auto] ConnectRPC JSON で RPC を呼び出す。
    def _rpc(
        self,
        endpoint: str,
        payload: dict,
        *,
        http_timeout: float | None = None,
    ) -> dict:
        """ConnectRPC JSON で RPC を呼び出す。

        http_timeout: urllib ソケット読み取り上限（秒）。None のときは軽量 RPC 向け 5s。
        StartCascade / SendMessage は ask の timeout に合わせ長めにする必要がある。
        """
        return self._raw_rpc(
            self.ls.port,
            self.ls.csrf,
            endpoint,
            payload,
            is_https=self.ls.is_https,
            host=self._ls_rpc_host(),
            timeout=5.0 if http_timeout is None else float(http_timeout),
        )

    def _ls_rpc_host(self) -> str:
        """LS ConnectRPC の接続ホスト（ブリッジ→LS の到達先。壁時計ではなくここが本番）。"""
        h = getattr(self.ls, "host", None)
        if isinstance(h, str) and h.strip():
            return h.strip()
        env = os.environ.get(_ENV_LS_CONNECT_HOST, "").strip()
        if env:
            return env
        return "127.0.0.1"

    # PURPOSE: [L2-auto] 低レベル RPC 呼び出し。
    def _raw_rpc(
        self, port: int, csrf: str, endpoint: str, payload: dict,
        timeout: float = 5.0, is_https: bool = True,
        host: Optional[str] = None,
    ) -> dict:
        """低レベル RPC 呼び出し。

        host が None のときは同一マシン上の LS 探索用に 127.0.0.1 を使う（_detect_ls のポート試行）。
        """
        scheme = "https" if is_https else "http"
        bind_host = host if (host is not None and str(host).strip()) else "127.0.0.1"
        url = f"{scheme}://{bind_host}:{port}/{endpoint}"
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-Codeium-Csrf-Token": csrf,
                "Connect-Protocol-Version": "1",
                "User-Agent": USER_AGENT,
            },
        )

        try:
            ctx = self._ssl_ctx if is_https else None
            with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
                body = resp.read().decode("utf-8")
                if not body:
                    return {}
                return json.loads(body)
        except urllib.error.HTTPError as e:
            # LS の 500 エラー等でレスポンスボディを読み出す
            error_body = ""
            try:
                error_body = e.read().decode("utf-8", errors="replace")[:500]
            except OSError:
                pass
            raise RuntimeError(
                f"LS RPC {endpoint} failed: HTTP {e.code} — {error_body or e.reason}"
            ) from e

    # --- Internal: Utilities ---

    # PURPOSE: [L2-auto] 自己署名証明書を許可する SSL コンテキスト。
    @staticmethod
    def _make_ssl_context() -> ssl.SSLContext:
        """自己署名証明書を許可する SSL コンテキスト。"""
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    # PURPOSE: [L2-auto] 現在のユーザー名を取得。
    @staticmethod
    def _get_user() -> str:
        """現在のユーザー名を取得。"""
        import os
        return os.environ.get("USER", "makaron8426")
