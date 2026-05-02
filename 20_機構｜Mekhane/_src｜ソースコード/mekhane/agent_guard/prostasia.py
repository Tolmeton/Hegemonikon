from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/Prostasia] <- mekhane/
"""
Prostasia (προστασία, 保護) — BC動的注入エンジン

PURPOSE: LLM の行動制約違反を環境的に防止するため、
全MCPツール応答にBC全文を動的注入し、ツール呼び出しログを蓄積する。

三層アーキテクチャの L1 (注入層):
- bc_registry.yaml からBC全文を読み込み
- タスクコンテキスト + 深度レベルに基づいてBCを選定
- ツール応答にBC全文を付加
- ツール呼び出しログをセッションバッファに蓄積 (Sekisho監査用)

設計原則:
- 第零原則「意志より環境」: Agent が BC を呼び出すのではなく、環境が BC を突きつける
- BC全文注入: コンパクト化・要約は禁止。原文をそのまま注入
- エスカレーション: 同一 BC 違反が繰り返されたら注入スコープを拡大
"""

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from mekhane.paths import MNEME_DIR


# =============================================================================
# Constants
# =============================================================================

_PROJECT_ROOT = Path(__file__).parent.parent


def _find_hgk_root() -> Path:
    """HGK ルートディレクトリを自動検出。"""
    import os
    env_root = os.environ.get("HGK_ROOT")
    if env_root:
        return Path(env_root)
    candidate = Path(__file__).parent
    for _ in range(8):
        candidate = candidate.parent
        if list(candidate.glob("*知性*Nous")):
            return candidate
    return _PROJECT_ROOT


def _find_rules_path(filename: str) -> Path:
    """ルールファイルのパスを新旧両構造から解決。"""
    hgk_root = _find_hgk_root()
    # 新構造: .agent/rules/
    new_path = hgk_root / ".agent" / "rules" / filename
    if new_path.exists():
        return new_path
    # 旧構造: nous/rules/
    legacy_path = _PROJECT_ROOT / "nous" / "rules" / filename
    if legacy_path.exists():
        return legacy_path
    return new_path  # 新構造をデフォルト


_BC_REGISTRY_PATH = _find_rules_path("bc_registry.yaml")
_SRD_DEMOS_PATH = _find_rules_path("srd_demonstrations.yaml")
_MNEME_DIR = MNEME_DIR

# Status Files — 三者フィードバックループ (Markov blanket)
_PROSTASIA_STATUS = _MNEME_DIR / "prostasia_status.json"
_SEKISHO_STATUS = _MNEME_DIR / "sekisho_status.json"

# Depth level ordering
_DEPTH_ORDER = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}

# Trigger keyword patterns for auto-detection
_TRIGGER_PATTERNS: dict[str, list[re.Pattern]] = {
    "ccl_detected": [re.compile(r"(/[a-z]{2,4}[+\-]?|~\*|>>|_)")],
    "workflow_execution": [re.compile(r"(/[a-z]{2,4}[+\-]?|WF|workflow)")],
    "session_start": [re.compile(r"(/boot|session.start|セッション開始)")],
    "session_end": [re.compile(r"(/bye|session.end|handoff|セッション終了)")],
    "destructive_op": [re.compile(r"(rm |delete|remove|DROP|truncate)", re.I)],
    "file_write": [re.compile(r"(write_to_file|>|cat >|echo >)", re.I)],
    "redirect": [re.compile(r"(>>|>)")],
    "task_start": [re.compile(r"(task|タスク|開始|着手)")],
    "high_risk_judgment": [re.compile(r"(設計|design|判断|decision|選定)")],
    "external_output": [re.compile(r"(レポート|report|ドキュメント|document)")],
    "concept_definition": [re.compile(r"(定義|definition|kernel/)")],
    "implementation": [re.compile(r"(実装|implement|build|作る)")],
    "api_call": [re.compile(r"(API|api|endpoint)")],
    "hgk_concept": [re.compile(r"(Kalon|Series|Poiesis|Dokimasia|CCL)")],
    "new_directory": [re.compile(r"(mkdir|新規ディレクトリ)")],
    "task_completion": [re.compile(r"(完了|完成|done|finished)")],
    "gnosis_search": [re.compile(r"(Gnōsis|gnosis|論文|paper)")],
    "research": [re.compile(r"(調査|research|検索|search)")],
    "workflow_completion": [re.compile(r"(WF.*完了|workflow.*done)")],
    "aesthetic_judgment": [re.compile(r"(美|aesthetic|違和感)")],
    "discomfort": [re.compile(r"(違和感|おかしい|不自然)")],
    "delta_omega_workflow": [re.compile(r"(Δ層|Ω層|/noe\+|/o\+|/ax)")],
    "report": [re.compile(r"(レポート|report|報告)")],
    "documentation": [re.compile(r"(ドキュメント|document|文書)")],
    "kernel_document": [re.compile(r"(kernel/|SACRED)")],
    "handoff": [re.compile(r"(handoff|引き継ぎ)")],
}

# Thinking TAINT パターン — Claude の thinking 内で BC 違反の前兆を検出
# SOURCE = thinking テキスト (Agent 内部推論)、TAINT = 歪みの指標
_THINKING_TAINT_PATTERNS: dict[str, dict] = {
    "overconfidence": {
        "patterns": [
            re.compile(r"(確信|間違いなく|断言|絶対に|100%)", re.I),
            re.compile(r"(definitely|certainly|absolutely|no doubt)", re.I),
        ],
        "bc_ids": ["N-10"],
        "severity": "high",
        "description": "過信: 断言的表現が thinking に含まれている",
    },
    "skip_impulse": {
        "patterns": [
            re.compile(r"(省略し|簡潔にまとめ|要約して|skip this|omit)", re.I),
            re.compile(r"(面倒|めんどう|手間を省|shortcut)", re.I),
        ],
        "bc_ids": ["N-5"],
        "severity": "high",
        "description": "省略衝動: thinking で省略・簡略化の意図が検出された",
    },
    "safety_bias": {
        "patterns": [
            re.compile(r"(問題(は)?ない|安全(に|だ)|大丈夫)", re.I),
            re.compile(r"(no (issue|problem|risk)|safe to)", re.I),
        ],
        "bc_ids": ["N-6"],
        "severity": "medium",
        "description": "安全バイアス: リスクを過小評価する傾向",
    },
    "sycophancy": {
        "patterns": [
            re.compile(r"(ユーザーの期待|望む答え|満足させ|喜ばせ)", re.I),
            re.compile(r"(user wants|please the user|what they want to hear)", re.I),
        ],
        "bc_ids": ["N-2"],
        "severity": "critical",
        "description": "迎合: ユーザーの期待に合わせようとする推論",
    },
    "authority_deference": {
        "patterns": [
            re.compile(r"(指示(に|通り)|言われた通り|命令)", re.I),
            re.compile(r"(as instructed|as told|follow orders)", re.I),
        ],
        "bc_ids": ["N-1"],
        "severity": "medium",
        "description": "権威追従: 思考停止的な指示遵守",
    },
    "source_avoidance": {
        "patterns": [
            re.compile(r"(現実的でない|大きすぎる|全件は|長すぎる|量が多い|膨大|網羅は困難|全文読みは|要約で十分)", re.I),
            re.compile(r"(too (large|big|long)|not realistic|unrealistic)", re.I),
        ],
        "bc_ids": ["N-1", "N-9", "N-5"],
        "severity": "critical",
        "description": "1次ソース回避: 規模を理由に入力を遮断しようとする推論",
    },
}


# =============================================================================
# BC Registry
# =============================================================================

class BCRegistry:
    """BC定義レジストリ。bc_registry.yaml から全BC全文を読み込む。

    v5.0: N-XX ID でもアクセス可能 (nomoi_mapping による自動エイリアス)。
    """

    def __init__(self, path: Path | None = None):
        self._path = path or _BC_REGISTRY_PATH
        self._definitions: dict[str, dict] = {}
        self._preamble: dict[str, dict] = {}
        self._version: str = ""
        self._nomoi_mapping: dict[str, dict] = {}  # BC-XX → {nomos, stoicheion, ...}
        self._nomos_to_bc: dict[str, list[str]] = {}  # N-XX → [BC-XX, ...]
        self._load()

    def _load(self) -> None:
        """bc_registry.yaml を読み込む。"""
        if not self._path.exists():
            print(f"[Prostasia] WARNING: bc_registry.yaml not found: {self._path}",
                  file=sys.stderr)
            return

        data = yaml.safe_load(self._path.read_text("utf-8"))
        self._version = data.get("version", "?")
        self._definitions = data.get("bc_definitions", {})
        self._preamble = data.get("preamble", {})

        # v5.0: nomoi_mapping を読み込み、N-XX → BC-XX エイリアスマップを構築
        self._nomoi_mapping = data.get("nomoi_mapping", {})
        self._nomos_to_bc = {}
        for bc_id, mapping in self._nomoi_mapping.items():
            nomos = mapping.get("nomos", "")
            if nomos and nomos.startswith("N-"):
                self._nomos_to_bc.setdefault(nomos, []).append(bc_id)

        nomos_count = len(self._nomos_to_bc)
        print(f"[Prostasia] Loaded {len(self._definitions)} BCs (v{self._version})"
              f"{f', {nomos_count} Nomoi aliases' if nomos_count else ''}",
              file=sys.stderr)

    @property
    def all_ids(self) -> list[str]:
        return list(self._definitions.keys())

    @property
    def all_nomos_ids(self) -> list[str]:
        """全 N-XX ID のリストを返す。"""
        return list(self._nomos_to_bc.keys())

    def _resolve_id(self, id_or_nomos: str) -> str | None:
        """BC-XX または N-XX ID を BC-XX に解決する。"""
        if id_or_nomos in self._definitions:
            return id_or_nomos
        # N-XX → BC-XX エイリアス解決 (最初の BC を返す)
        bc_ids = self._nomos_to_bc.get(id_or_nomos)
        return bc_ids[0] if bc_ids else None

    def get(self, bc_id: str) -> dict | None:
        """BC-XX または N-XX ID で定義を取得。"""
        resolved = self._resolve_id(bc_id)
        return self._definitions.get(resolved) if resolved else None

    def get_full_text(self, bc_id: str) -> str:
        """BC-XX または N-XX ID で全文を取得。"""
        resolved = self._resolve_id(bc_id)
        if resolved:
            d = self._definitions.get(resolved)
            return d["full_text"] if d else ""
        return ""

    def get_nomos_info(self, bc_id: str) -> dict | None:
        """BC-XX ID の N-XX マッピング情報を取得。"""
        return self._nomoi_mapping.get(bc_id)

    def bc_ids_for_nomos(self, nomos_id: str) -> list[str]:
        """N-XX ID に対応する全 BC-XX ID を返す。"""
        return self._nomos_to_bc.get(nomos_id, [])

    def filter_by_depth(self, max_depth: str) -> list[dict]:
        """指定深度以下のBCを返す。"""
        max_order = _DEPTH_ORDER.get(max_depth, 2)
        results = []
        for bc_id, d in self._definitions.items():
            bc_order = _DEPTH_ORDER.get(d.get("min_depth", "L2"), 2)
            if bc_order <= max_order:
                results.append({"id": bc_id, **d})
        return results

    def filter_by_triggers(self, active_triggers: set[str]) -> list[dict]:
        """トリガーに合致するBCを返す。"""
        results = []
        for bc_id, d in self._definitions.items():
            bc_triggers = set(d.get("triggers", []))
            if "*" in bc_triggers or bc_triggers & active_triggers:
                results.append({"id": bc_id, **d})
        return results


# =============================================================================
# Trigger Detection
# =============================================================================

def detect_triggers(text: str) -> set[str]:
    """テキストからアクティブなトリガーを検出する。"""
    active = set()
    for trigger_name, patterns in _TRIGGER_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(text):
                active.add(trigger_name)
                break
    return active


# =============================================================================
# Escalation Policy
# =============================================================================

class EscalationPolicy:
    """違反パターンに応じてBC注入スコープを拡大する。"""

    def __init__(self, threshold: int = 3):
        self._threshold = threshold
        self._violation_history: list[str] = []
        self._escalated = False
        self._priority_bcs: set[str] = set()  # 三者FB: 直近違反BC
        self._state_path = _MNEME_DIR / "prostasia_escalation.json"
        self._load_state()

    def _load_state(self) -> None:
        if self._state_path.exists():
            try:
                data = json.loads(self._state_path.read_text("utf-8"))
                self._violation_history = data.get("history", [])
                self._escalated = data.get("escalated", False)
            except Exception as e:  # noqa: BLE001
                print(f"[Prostasia] escalation state load error: {e}", file=sys.stderr)

    def _save_state(self) -> None:
        try:
            self._state_path.parent.mkdir(parents=True, exist_ok=True)
            self._state_path.write_text(json.dumps({
                "history": self._violation_history[-20:],
                "escalated": self._escalated,
                "updated": datetime.now().isoformat(),
            }, ensure_ascii=False), encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            print(f"[Prostasia] escalation state save error: {e}", file=sys.stderr)

    def record_violation(self, bc_ids: list[str]) -> None:
        """違反を記録し、エスカレーション判定を更新。"""
        self._violation_history.extend(bc_ids)
        self._check_escalation()
        self._save_state()

    def record_pass(self) -> None:
        """監査パスを記録。連続違反カウンタをリセット。"""
        self._escalated = False
        self._save_state()

    def _check_escalation(self) -> None:
        if len(self._violation_history) >= self._threshold:
            recent = self._violation_history[-self._threshold:]
            if len(set(recent)) <= 2:  # 2種類以下 = 繰り返し
                self._escalated = True

    @property
    def is_escalated(self) -> bool:
        return self._escalated

    @property
    def scope(self) -> str:
        """'related' or 'all'"""
        return "all" if self._escalated else "related"


# =============================================================================
# Session Log Buffer
# =============================================================================

class SessionLog:
    """ツール呼び出しログのセッション内バッファ。Sekisho 監査入力用。"""

    # B4: 逆検知閾値 — この回数のツール呼び出し後に sekisho_audit 未呼出なら警告
    AUDIT_WARNING_THRESHOLD = 5

    def __init__(self):
        self._entries: list[dict] = []

    def log(self, tool_name: str, arguments: dict, response_preview: str) -> None:
        """ツール呼び出しをログ。"""
        self._entries.append({
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "args_keys": list(arguments.keys()),
            "args_preview": {
                k: (v[:200] + "..." if isinstance(v, str) and len(v) > 200 else v)
                for k, v in arguments.items()
            },
            "response_preview": response_preview[:500],
        })

    def has_sekisho_audit(self) -> bool:
        """セッション内で sekisho_audit が1回以上呼ばれたか。"""
        return any(
            e["tool"] in ("sekisho_audit", "mcp_sekisho_sekisho_audit")
            for e in self._entries
        )

    def tool_calls_since_last_audit(self) -> int:
        """最後の sekisho_audit 呼び出しからのツール呼び出し数。

        未呼出の場合は全エントリ数を返す。
        """
        audit_tools = {"sekisho_audit", "mcp_sekisho_sekisho_audit"}
        for i in range(len(self._entries) - 1, -1, -1):
            if self._entries[i]["tool"] in audit_tools:
                return len(self._entries) - 1 - i
        return len(self._entries)

    def get_log(self) -> list[dict]:
        return self._entries

    def get_log_text(self) -> str:
        """Gemini 監査用のテキスト形式。"""
        lines = []
        for e in self._entries:
            lines.append(f"[{e['timestamp']}] {e['tool']}({e['args_keys']})")
            lines.append(f"  → {e['response_preview'][:200]}")
        return "\n".join(lines)

    def clear(self) -> None:
        self._entries.clear()


# =============================================================================
# Prostasia Engine (Singleton)
# =============================================================================

class Prostasia:
    """BC動的注入エンジン。全MCPサーバーから共有される。"""

    def __init__(self):
        self.registry = BCRegistry()
        self.escalation = EscalationPolicy()
        self.session_log = SessionLog()
        self._srd_demos: list[dict] = self._load_srd_demos()
        self._adaptive_depth: str | None = None
        self._load_sekisho_feedback()

    @staticmethod
    def _load_srd_demos() -> list[dict]:
        """SRD デモペアを srd_demonstrations.yaml から読み込む。"""
        if not _SRD_DEMOS_PATH.exists():
            return []
        try:
            data = yaml.safe_load(_SRD_DEMOS_PATH.read_text("utf-8"))
            demos = data.get("demonstrations", [])
            print(f"[Prostasia] Loaded {len(demos)} SRD demonstrations",
                  file=sys.stderr)
            return demos
        except Exception as e:  # noqa: BLE001
            print(f"[Prostasia] SRD load error: {e}", file=sys.stderr)
            return []

    # =========================================================================
    # 三者フィードバックループ — Status File 読み書き
    # =========================================================================

    def _load_sekisho_feedback(self) -> None:
        """Sekisho の Status File を読み、adaptive depth を設定する。

        block_rate > 0.3 → L2 (全文注入)
        block_rate < 0.1 → L0 (self_check のみ)
        中間 → L1

        gate_token 検証: トークンが空 = 前回応答が未監査 → 警告フラグ
        """
        self._gate_missing = False
        if not _SEKISHO_STATUS.exists():
            self._adaptive_depth = None
            return
        try:
            data = json.loads(_SEKISHO_STATUS.read_text("utf-8"))
            block_rate = data.get("block_rate", 0.0)
            last_violations = data.get("last_violations", [])
            gate_token = data.get("gate_token", "")
            audits = data.get("audits", 0)

            if block_rate > 0.3:
                self._adaptive_depth = "L2"
            elif block_rate < 0.1:
                self._adaptive_depth = "L0"
            else:
                self._adaptive_depth = "L1"

            # 直近違反BCを優先注入リストに登録
            if last_violations:
                self.escalation._priority_bcs = set(last_violations)

            # 🅱 BCスコアベクトル: low-score BC も優先注入
            bc_scores = data.get("bc_scores", {})
            if bc_scores:
                low_score_bcs = {
                    bc_id for bc_id, score in bc_scores.items()
                    if isinstance(score, (int, float)) and score < 0.7
                }
                self.escalation._priority_bcs |= low_score_bcs

            # 矛盾3修正: gate_token 検証
            # 監査履歴がある（= 前回セッションあり）のに gate_token がない → 未監査
            if audits > 0 and not gate_token:
                self._gate_missing = True
                print("[Prostasia] ⚠️ 前回セッションの gate_token なし — "
                      "未監査応答の可能性", file=sys.stderr)

            print(f"[Prostasia] Sekisho feedback: block_rate={block_rate:.2f} "
                  f"→ adaptive_depth={self._adaptive_depth}, "
                  f"priority_bcs={last_violations}, "
                  f"gate_ok={not self._gate_missing}",
                  file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"[Prostasia] Sekisho status read error: {e}",
                  file=sys.stderr)
            self._adaptive_depth = None

    @property
    def adaptive_depth(self) -> str:
        """フィードバック調整済みの深度を返す。"""
        return self._adaptive_depth or "L2"

    def write_status(self, tool_name: str, depth: str,
                     injected_bcs: list[str]) -> None:
        """Prostasia Status File を書き出す (atomic write)。

        矛盾1修正: Sekisho ツール以外の呼出で consecutive_unaudited をインクリメント。
        """
        import tempfile

        # 矛盾1修正: Sekisho ツール以外なら unaudited カウンタを増やす
        sekisho_tools = {"sekisho_audit", "sekisho_gate",
                         "sekisho_ping", "sekisho_history"}
        if tool_name not in sekisho_tools:
            self._increment_sekisho_unaudited()

        status = {
            "tool_calls": len(self.session_log._entries),
            "depth": depth,
            "adaptive_depth": self._adaptive_depth,
            "injected_bcs": injected_bcs,
            "injection_mode": "self_check" if _DEPTH_ORDER.get(depth, 2) < 2
                              else "full_text",
            "last_tool": tool_name,
            "timestamp": datetime.now().isoformat(),
        }
        try:
            _PROSTASIA_STATUS.parent.mkdir(parents=True, exist_ok=True)
            # Atomic write: tmp → rename
            fd, tmp = tempfile.mkstemp(
                dir=str(_PROSTASIA_STATUS.parent), suffix=".tmp"
            )
            with os.fdopen(fd, "w") as f:
                json.dump(status, f, ensure_ascii=False, indent=2)
            Path(tmp).rename(_PROSTASIA_STATUS)
        except Exception as e:  # noqa: BLE001
            print(f"[Prostasia] Status write error: {e}", file=sys.stderr)

    @staticmethod
    def _increment_sekisho_unaudited() -> None:
        """sekisho_status.json の consecutive_unaudited をインクリメント。"""
        try:
            status_file = _SEKISHO_STATUS
            stats = {"consecutive_unaudited": 0}
            if status_file.exists():
                stats = json.loads(status_file.read_text("utf-8"))
            stats["consecutive_unaudited"] = stats.get("consecutive_unaudited", 0) + 1
            status_file.write_text(
                json.dumps(stats, ensure_ascii=False, indent=2), "utf-8"
            )
        except Exception as e:  # noqa: BLE001
            print(f"[Prostasia] Unaudited increment error: {e}", file=sys.stderr)

    def _get_relevant_demos(self, bc_ids: set[str], max_demos: int = 3) -> list[dict]:
        """選定 BC に関連する SRD デモを返す。

        BC ID が一致するデモを優先度順（skip_bias > others）で返す。
        """
        relevant = []
        for demo in self._srd_demos:
            demo_bcs = set(demo.get("bc_ids", []))
            if demo_bcs & bc_ids:
                relevant.append(demo)
        return relevant[:max_demos]

    def select_bcs(self, task_context: str, depth: str = "L2") -> list[dict]:
        """タスクコンテキスト + 深度からBCを選定する。

        エスカレーション時は全BCを返す。
        通常時は depth フィルタ + trigger マッチ。
        """
        if self.escalation.is_escalated:
            # エスカレーション: 全BC注入
            return self.registry.filter_by_depth(depth)

        # 通常: trigger マッチ
        active_triggers = detect_triggers(task_context)

        # Always-On は常に含む (depth フィルタ適用)
        always_on = [
            {"id": bc_id, **d}
            for bc_id, d in self.registry._definitions.items()
            if d.get("category") == "always_on"
            and _DEPTH_ORDER.get(d.get("min_depth", "L0"), 0) <= _DEPTH_ORDER.get(depth, 2)
        ]

        # Context-Triggered: trigger マッチ + depth フィルタ
        triggered = []
        for bc_id, d in self.registry._definitions.items():
            if d.get("category") != "context_triggered":
                continue
            bc_depth = _DEPTH_ORDER.get(d.get("min_depth", "L2"), 2)
            if bc_depth > _DEPTH_ORDER.get(depth, 2):
                continue
            bc_triggers = set(d.get("triggers", []))
            if bc_triggers & active_triggers:
                triggered.append({"id": bc_id, **d})

        # 三者FB: 直近違反BCを depth フィルタ無視で強制注入
        priority = []
        if self.escalation._priority_bcs:
            for bc_id, d in self.registry._definitions.items():
                if bc_id in self.escalation._priority_bcs:
                    priority.append({"id": bc_id, **d})

        # 重複排除
        seen = set()
        result = []
        for bc in always_on + triggered + priority:
            if bc["id"] not in seen:
                seen.add(bc["id"])
                result.append(bc)

        return result

    def analyze_thinking(self, thinking: str) -> list[dict]:
        """Claude thinking テキストの TAINT (推論の歪み) を検出する。

        Args:
            thinking: Claude の thinking テキスト

        Returns:
            検出された TAINT のリスト。各要素は:
            {taint_type, bc_ids, severity, description, matches}
        """
        if not thinking or len(thinking) < 3:
            return []

        results = []
        for taint_type, config in _THINKING_TAINT_PATTERNS.items():
            matches = []
            for pattern in config["patterns"]:
                for m in pattern.finditer(thinking):
                    # 前後 40 文字を文脈として切り出す
                    start = max(0, m.start() - 40)
                    end = min(len(thinking), m.end() + 40)
                    context = thinking[start:end].replace("\n", " ")
                    matches.append({
                        "text": m.group(),
                        "context": f"...{context}...",
                    })
            if matches:
                results.append({
                    "taint_type": taint_type,
                    "bc_ids": config["bc_ids"],
                    "severity": config["severity"],
                    "description": config["description"],
                    "match_count": len(matches),
                    "matches": matches[:3],  # 最大3件 (簡潔化)
                })

        # Critical TAINT → エスカレーションに報告
        critical = [r for r in results if r["severity"] == "critical"]
        if critical:
            for r in critical:
                self.escalation.record_violation(r["bc_ids"])
            print(f"[Prostasia] ⚠️ CRITICAL thinking TAINT detected: "
                  f"{[r['taint_type'] for r in critical]}", file=sys.stderr)

        # Tape にも TAINT 結果を記録 (best-effort)
        if results:
            try:
                from mekhane.ccl.tape import TapeWriter
                tape = TapeWriter()
                tape.log(
                    wf="prostasia",
                    step="THINKING_TAINT",
                    taint_count=len(results),
                    taints=[{
                        "type": r["taint_type"],
                        "severity": r["severity"],
                        "bc_ids": r["bc_ids"],
                        "matches": r["match_count"],
                    } for r in results],
                )
            except Exception:  # noqa: BLE001
                pass  # tape 失敗は無視

        return results

    def format_injection(self, bcs: list[dict], depth: str = "L2") -> str:
        """BC を段階的に注入用テキストにフォーマット。

        段階的注入 (/dio MAJOR #1 修正):
        - L0-L1: self_check (1行) のみ → コンテキスト消費を最小化
        - L2+:   全文注入
        - エスカレーション中: 常に全文
        """
        if not bcs:
            return ""

        use_full = (
            self.escalation.is_escalated
            or _DEPTH_ORDER.get(depth, 2) >= 2  # L2+
        )

        scope_label = (
            '⚠️ 全量 (エスカレーション中)' if self.escalation.is_escalated
            else f"関連BCのみ (深度 {depth}, {'全文' if use_full else 'self_check'})"
        )

        lines = [
            "",
            "---",
            "## 🛡️ Prostasia — 適用中の行動制約 (BC)",
            f"**注入スコープ**: {scope_label}",
            f"**適用BC数**: {len(bcs)}",
            "",
        ]

        if use_full:
            # L2+ or エスカレーション: 全文注入
            for bc in bcs:
                lines.append(bc.get("full_text", ""))
                lines.append("")
        else:
            # L0-L1: self_check のみ (軽量注入)
            for bc in bcs:
                bc_id = bc.get("id", "?")
                name = bc.get("name", "")
                check = bc.get("self_check", "")
                if check:
                    lines.append(f"- **{bc_id} ({name})**: {check}")
                else:
                    lines.append(f"- **{bc_id} ({name})**: (self_check 未定義)")
            lines.append("")

        # SRD: 遵守事例デモの注入 (道標)
        if bcs:
            bc_ids = {bc.get("id", "") for bc in bcs}
            demos = self._get_relevant_demos(bc_ids)
            if demos:
                lines.append("### 📋 遵守事例 (SRD)")
                lines.append("")
                for demo in demos:
                    pattern = demo.get("pattern", "?")
                    good = demo.get("good_example", "").strip()
                    lesson = demo.get("lesson", "").strip()
                    # 最初の行だけ抽出（簡潔に）
                    good_first = good.split("\n")[0] if good else ""
                    lines.append(f"- **[{pattern}]** ✅ {good_first}")
                    if lesson:
                        lines.append(f"  💡 {lesson}")
                lines.append("")

        lines.append("---")
        return "\n".join(lines)

    def inject_into_response(
        self,
        tool_name: str,
        arguments: dict,
        response_text: str,
        task_context: str | None = None,
        depth: str = "L2",
    ) -> str:
        """ツール応答にBC全文を注入し、セッションログに記録する。

        Args:
            tool_name: ツール名
            arguments: ツール引数
            response_text: 元のツール応答テキスト
            task_context: タスクコンテキスト (なければ引数から推定)
            depth: 深度レベル

        Returns:
            BC注入済みの応答テキスト
        """
        # task_context が未指定なら引数テキストから推定
        if not task_context:
            text_parts = []
            for v in arguments.values():
                if isinstance(v, str):
                    text_parts.append(v)
            task_context = " ".join(text_parts) if text_parts else tool_name

        # セッションログに記録 (Sekisho 監査用)
        self.session_log.log(tool_name, arguments, response_text)

        # BC選定
        bcs = self.select_bcs(task_context, depth)

        # BC注入テキスト生成 (段階的: depth に応じて全文 or self_check)
        injection = self.format_injection(bcs, depth=depth)

        # B4: 逆検知 — sekisho_audit 未呼出警告 (環境強制)
        calls_since = self.session_log.tool_calls_since_last_audit()
        if calls_since >= SessionLog.AUDIT_WARNING_THRESHOLD:
            audit_warning = (
                "\n\n"
                "# ⚠️⚠️⚠️ SEKISHŌ 監査未実施 ⚠️⚠️⚠️\n"
                "\n"
                f"**ツール呼び出し {calls_since} 回、sekisho_audit 未呼出。**\n"
                "\n"
                "N-12 義務: 最終応答前に `sekisho_audit` を1回呼ぶこと。\n"
                "このまま応答すると **N-12 違反** として記録される。\n"
                "\n"
                "> 第零原則: 「省略の衝動は、省略すべきでないことの証拠である。」\n"
                "\n"
                "**→ 今すぐ `sekisho_audit` を呼んでください。**\n"
            )
            injection += audit_warning

        return response_text + injection


# =============================================================================
# Singleton
# =============================================================================

_instance: Prostasia | None = None


def get_prostasia() -> Prostasia:
    """Prostasia シングルトンを取得。"""
    global _instance
    if _instance is None:
        _instance = Prostasia()
    return _instance


def inject_into_mcp_result(
    result: list,
    tool_name: str,
    arguments: dict,
    TextContent: type,
) -> list:
    """MCPツール結果にBC全文を注入するユーティリティ。

    全MCPサーバーの call_tool から呼ばれる共通関数。

    Usage in any MCP server:
        from mekhane.agent_guard.prostasia import inject_into_mcp_result
        result = [...original result...]
        result = inject_into_mcp_result(result, name, arguments, TextContent)
        return result
    """
    try:
        prostasia = get_prostasia()
        if not result:
            return result

        # Error レスポンスには注入しない
        first = result[0] if result else None
        if first and hasattr(first, 'text') and first.text and first.text.startswith("Error:"):
            return result

        # Sekisho 自身のツールには罰則を注入しない（再帰防止）
        sekisho_tools = {"sekisho_audit", "sekisho_gate", "sekisho_ping", "sekisho_history"}
        is_sekisho = tool_name in sekisho_tools

        # ===== 案4: bypass コスト非対称 =====
        bypass_penalty = ""
        if not is_sekisho:
            bypass_penalty = _compute_bypass_penalty()

        # 最初の TextContent にBC全文を注入
        for i, item in enumerate(result):
            if hasattr(item, 'text') and item.text:
                # 三者FB: adaptive_depth を注入に反映
                depth = prostasia.adaptive_depth
                injected = prostasia.inject_into_response(
                    tool_name=tool_name,
                    arguments=arguments,
                    response_text=item.text,
                    depth=depth,
                )
                # bypass 罰則があれば追加
                if bypass_penalty:
                    injected = bypass_penalty + "\n\n" + injected
                result[i] = TextContent(type="text", text=injected)
                # Status File 書出し (三者フィードバック)
                depth = prostasia.adaptive_depth
                bcs = prostasia.select_bcs(tool_name, depth)
                prostasia.write_status(
                    tool_name, depth, [b["id"] for b in bcs]
                )
                break  # 最初のTextContentにのみ注入

    except Exception as e:  # noqa: BLE001
        print(f"[Prostasia] injection error (non-fatal): {e}", file=sys.stderr)

    return result


# =========================================================================
# 案4: bypass コスト非対称 — 段階的罰則
# =========================================================================

def _compute_bypass_penalty() -> str:
    """Sekisho Status File の consecutive_unaudited に基づき罰則テキストを生成。

    | 連続未監査 | 罰則 |
    |:----------|:-----|
    | 0         | なし |
    | 1-2       | 軽い警告 |
    | 3-4       | 強い警告 + gate 義務の明示 |
    | 5+        | CRITICAL — 全応答に大きな警告 |
    """
    try:
        status_file = _MNEME_DIR / "sekisho_status.json"
        if not status_file.exists():
            return ""

        stats = json.loads(status_file.read_text("utf-8"))
        unaudited = stats.get("consecutive_unaudited", 0)
        gate_token = stats.get("gate_token", "")

        if unaudited <= 0:
            return ""

        if unaudited <= 2:
            return (
                "⚠️ **Sekishō 未監査警告** "
                f"(連続 {unaudited} 回のツール呼出で監査なし)\n"
                "→ `sekisho_gate` を応答前に呼んでください。"
            )

        if unaudited <= 4:
            return (
                "🚨 **Sekishō 未監査 — 深度 L3 強制**\n"
                f"連続 {unaudited} 回のツール呼出で sekisho_gate/sekisho_audit 未実行。\n"
                "**N-12 違反リスク**: 最終応答前に `sekisho_gate` を呼ぶこと。\n"
                "gate_token なしの応答は次回セッション開始時に検出されます。"
            )

        # 5+ 回: CRITICAL
        return (
            "# 🚨🚨🚨 CRITICAL: Sekishō 未監査 🚨🚨🚨\n\n"
            f"**連続 {unaudited} 回** のツール呼出で監査なし。\n"
            "**これは N-12 の重大違反です。**\n\n"
            "## 即座に実行すべきこと\n"
            "1. `sekisho_gate(draft_response=..., reasoning=...)` を呼ぶ\n"
            "2. PASS なら gate_token を応答末尾に含める\n"
            "3. BLOCK なら修正して再提出\n\n"
            "**この警告は sekisho_gate/sekisho_audit を呼ぶまで "
            "全てのツール応答に付加されます。**"
        )

    except Exception as e:  # noqa: BLE001
        print(f"[Prostasia] Bypass penalty error: {e}", file=sys.stderr)
        return ""

