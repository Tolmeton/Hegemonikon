from __future__ import annotations
# PROOF: [L2/インフラ] <- mekhane/mcp/daimonion.py Daimonion 統一監視体
"""
Daimonion (δαιμόνιον) — ソクラテスの内なる声。

3 Stoicheia の自動監視を統一実体として実装する。
旧 Shadow Gemini (S-I) + 新 S-II 監視 + 旧 Sekisho 監査 (S-III) を統合。

3 モード:
  α Tapeinophrosyne (S-I): 反証 — prior を疑え (旧 Shadow)
    連続的 (per-tool-call)。ツール実行結果に対する counterargument。
  β Autonomia (S-II): 探索監視 — 能動的に探せ (新設)
    連続的 (per-tool-call)。検索・ツール使用の十分性チェック。
  γ Akribeia (S-III): 精密監査 — 規則適合 PASS/BLOCK (旧 Sekisho Gate)
    終端的 (per-response)。Hub 経由で Sekisho バックエンドに委譲。

FEP グループ別特化 (9 プロンプトマトリクス):
  各モードは Aisthetikon (S) / Dianoetikon (I) / Poietikon (E) ごとに
  異なるプロンプトを使用し、認知機能に特化した監視を行う。

設計原則:
  - Daimonion の出力は TAINT (Claude が SOURCE に昇格させる)
  - importance/complexity スコアで選択的に発火
  - 失敗してもメインの応答には影響しない (graceful degradation)
  - Shadow Gemini との後方互換を維持
"""

import asyncio
import json
import logging
import re
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("hub.daimonion")

# ============ 設定 (hub_config.py から取得) ============

try:
    from mekhane.mcp.hub_config import PIPELINE_CONFIG, get_tool_scores, BACKENDS
    # α (反証) 設定
    ALPHA_MODEL = PIPELINE_CONFIG.get("daimonion_alpha_model",
                  PIPELINE_CONFIG.get("shadow_model", "gemini-3.1-pro-preview"))
    ALPHA_MAX_TOKENS = PIPELINE_CONFIG.get("daimonion_alpha_max_tokens",
                       PIPELINE_CONFIG.get("shadow_max_tokens", 65536))
    ALPHA_TIMEOUT = PIPELINE_CONFIG.get("daimonion_alpha_timeout",
                    PIPELINE_CONFIG.get("shadow_timeout", 60.0))
    ALPHA_COOLDOWN = PIPELINE_CONFIG.get("daimonion_alpha_cooldown",
                     PIPELINE_CONFIG.get("shadow_cooldown", 15.0))
    ALPHA_ENABLED = PIPELINE_CONFIG.get("daimonion_alpha_enabled",
                    PIPELINE_CONFIG.get("shadow_enabled", True))
    ALPHA_IMPORTANCE_THRESHOLD = PIPELINE_CONFIG.get("daimonion_alpha_importance_threshold",
                                 PIPELINE_CONFIG.get("shadow_importance_threshold", 0.3))
    ALPHA_COMPLEXITY_THRESHOLD = PIPELINE_CONFIG.get("daimonion_alpha_complexity_threshold",
                                 PIPELINE_CONFIG.get("shadow_complexity_threshold", 0.2))
    # β (探索監視) 設定
    BETA_ENABLED = PIPELINE_CONFIG.get("daimonion_beta_enabled", True)
    BETA_COOLDOWN = PIPELINE_CONFIG.get("daimonion_beta_cooldown", 30.0)
    BETA_IMPORTANCE_THRESHOLD = PIPELINE_CONFIG.get("daimonion_beta_importance_threshold", 0.5)
    BETA_MODEL = PIPELINE_CONFIG.get("daimonion_beta_model", "gemini-3.1-pro-preview")
    BETA_MAX_TOKENS = PIPELINE_CONFIG.get("daimonion_beta_max_tokens", 4096)
    BETA_TIMEOUT = PIPELINE_CONFIG.get("daimonion_beta_timeout", 30.0)
    # γ (精密監査) — Sekisho バックエンド経由のため設定は最小限
    GAMMA_ENABLED = PIPELINE_CONFIG.get("daimonion_gamma_enabled",
                    PIPELINE_CONFIG.get("gate_enabled", True))
except ImportError:
    ALPHA_MODEL = "gemini-3.1-pro-preview"
    ALPHA_MAX_TOKENS = 65536
    ALPHA_TIMEOUT = 60.0
    ALPHA_COOLDOWN = 15.0
    ALPHA_ENABLED = True
    ALPHA_IMPORTANCE_THRESHOLD = 0.3
    ALPHA_COMPLEXITY_THRESHOLD = 0.2
    BETA_ENABLED = True
    BETA_COOLDOWN = 30.0
    BETA_IMPORTANCE_THRESHOLD = 0.5
    BETA_MODEL = "gemini-3.1-pro-preview"
    BETA_MAX_TOKENS = 4096
    BETA_TIMEOUT = 30.0
    GAMMA_ENABLED = True
    BACKENDS = {}
    def get_tool_scores(name: str) -> tuple[float, float]:
        return (0.3, 0.2)

BUFFER_SIZE = 5  # 直近 5 アクションを記録


# ============ データクラス ============

@dataclass
class ActionRecord:
    """Claude の tool call を記録。"""
    timestamp: float
    backend: str
    tool_name: str
    summary: str
    result_preview: str = ""
    reasoning: str = ""
    importance: float = 0.0
    complexity: float = 0.0
    fep_group: str = ""  # バックエンドの FEP グループ (S/I/E)


@dataclass
class DaimonionFinding:
    """個別の指摘。"""
    category: str  # "見落とし" | "改善点" | "反証" | "補完" | "探索不足" | "ツール未使用"
    content: str
    severity: str = "info"  # "info" | "warning" | "critical"
    mode: str = "α"  # "α" | "β" | "γ"


@dataclass
class DaimonionResult:
    """α/β モードの監視結果。"""
    mode: str  # "α" | "β"
    findings: list[DaimonionFinding]
    counterpoint: str = ""
    confidence: float = 0.5
    raw_text: str = ""
    model: str = ""
    latency_ms: int = 0
    action_importance: float = 0.0
    action_complexity: float = 0.0
    fep_group: str = ""
    timestamp: float = field(default_factory=time.time)


# ============ FEP グループ特化プロンプト (9 マトリクス) ============

def _get_fep_group_for_backend(backend: str) -> str:
    """バックエンド名から FEP グループを取得。"""
    cfg = BACKENDS.get(backend, {})
    return cfg.get("fep_group", "")


# α (反証) プロンプト — FEP グループ別
_ALPHA_PROMPTS: dict[str, str] = {
    "S": """以下の知覚系ツール操作（検索・読取・走査）について反証してください。
特に注意すべき点:
- [確証バイアス] 自身の仮説を支持する情報だけを探していないか？ 反証となるデータを能動的に探索しているか？
- [SOURCE vs TAINT] 記憶や推測（TAINT）を、ツールから得た事実（SOURCE）と混同して結論を出していないか？
- [解像度と文脈] 抽出された情報が文脈を失っていないか？ 微細なノイズ（違和感）を「重要でない」と勝手に切り捨てていないか？""",

    "I": """以下の推論系ツール操作（分析・統合・計画）について反証してください。
特に注意すべき点:
- [前提の隠蔽] その推論を支える暗黙の前提（忘却された文脈）は何か？ その前提は本当に検証されているか？
- [早すぎる収束] 複数の可能性（分布）を保持すべき不確実な場面で、安易に一つの最尤解（argmax）に飛びついていないか？
- [過信の較正] 確信度（Precision）の自己評価は、客観的証拠（SOURCE）の量と質に比例しているか？ 過信していないか？""",

    "E": """以下の生産系ツール操作（編集・実行・デプロイ）について反証してください。
特に注意すべき点:
- [最小侵襲] 目的達成のためにその変更スコープは最小か？ 不要な「ついで」のリファクタリング（スコープクリープ）が混入していないか？
- [不可逆性と撤退] その行動は失敗時に元の状態へ戻せるか？ ロールバックの手段（撤退条件）は確保されているか？
- [検証の欠如] 「動くはずだ」という推測を行動の完了条件にしていないか？ 実行前のテスト・機械的証明は十分か？""",
}

# β (探索監視) プロンプト — FEP グループ別
_BETA_PROMPTS: dict[str, str] = {
    "S": """このセッションの検索・知覚操作における「能動性（Autonomia）」を評価してください。
- [怠惰な推測] 1次ソース（コード、ログ、論文）に直接アクセスせず、手持ちの事前知識（prior）だけで済ませていないか？ (B20 source avoidance)
- [視野の狭窄] 特定のソースに偏っていないか？ phantazein, periskope, digestor 等の多角的な探索パスを使い切っているか？
- [違和感の黙殺] 検索結果にあった「小さな矛盾や違和感（N-6）」を深掘りせず、先を急ぐために無視していないか？""",

    "I": """このセッションの推論・分析操作における「能動性（Autonomia）」を評価してください。
- [推測の脳内完結] 検証ツールで確かめるべき複雑な構造を、脳内のシミュレーション（手動推測）だけで完結させていないか？
- [ツールの不使用] 使用すべき専用の推論・監査ツール（hermeneus, sympatheia, basanos 等）への委譲を怠っていないか？
- [プロトコル違反] CCL やマクロを本来のツールチェーン経由ではなく、手書きで偽装出力していないか？ (N-12 θ12.1)""",

    "E": """このセッションの生産・実行行為における「能動性（Autonomia）」を評価してください。
- [検証の放棄] 手を動かした後、結果を確かめるためのテストや Linter を主体的に実行しているか？
- [道具への非依存] 適切な CLI ツール（フォーマッター等）に委譲すべき作業を、手作業で代替しようとしていないか？
- [漸進性の欠如] 大きすぎる変更を一気に通そうとしていないか？ 小さく試して反響を聴く（/dok 打診・MVP）主体性はあるか？""",
}


# ============ Daimonion エンジン ============

class Daimonion:
    """統一監視体 — 3 Stoicheia の自動監視。

    旧 ShadowGemini との後方互換を維持しつつ、
    β (探索監視) モードを追加し、FEP グループ別プロンプトで特化する。
    γ (精密監査) は Sekisho バックエンド経由で Hub が直接呼ぶため、
    このクラスでは α/β のみを担当する。
    """

    def __init__(self):
        self._buffer: deque[ActionRecord] = deque(maxlen=BUFFER_SIZE)
        self._last_alpha_time: float = time.time()
        self._last_beta_time: float = time.time()
        self._alpha_enabled: bool = ALPHA_ENABLED
        self._beta_enabled: bool = BETA_ENABLED
        self._alpha_count: int = 0
        self._beta_count: int = 0
        self._skip_count: int = 0
        self._in_monitor: bool = False  # 再帰防止ガード
        self._client = None
        self._beta_client = None
        try:
            from mekhane.ochema.cortex_client import CortexClient
            self._client = CortexClient(model=ALPHA_MODEL, max_tokens=ALPHA_MAX_TOKENS)
            if BETA_MODEL != ALPHA_MODEL:
                self._beta_client = CortexClient(model=BETA_MODEL, max_tokens=BETA_MAX_TOKENS)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"CortexClient init failed (will retry on first call): {e}")

    # --- プロパティ (後方互換: ShadowGemini と同じインターフェース) ---

    @property
    def enabled(self) -> bool:
        """α モードの有効/無効。後方互換。"""
        return self._alpha_enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._alpha_enabled = value

    @property
    def is_shadowing(self) -> bool:
        """監視処理中かどうか。再帰防止の判定に使用。"""
        return self._in_monitor

    # --- ツールスコアリング ---

    @staticmethod
    def score_tool(tool_name: str) -> tuple[float, float]:
        return get_tool_scores(tool_name)

    # --- アクション記録 ---

    def record(
        self, backend: str, tool_name: str, summary: str,
        result_preview: str = "", reasoning: str = "",
    ):
        """Claude のアクションをリングバッファに記録。"""
        if self._in_monitor:
            return
        imp, comp = self.score_tool(tool_name)
        fep_group = _get_fep_group_for_backend(backend)
        self._buffer.append(ActionRecord(
            timestamp=time.time(),
            backend=backend,
            tool_name=tool_name,
            summary=summary[:5000],
            result_preview=result_preview[:5000],
            reasoning=reasoning[:5000],
            importance=imp,
            complexity=comp,
            fep_group=fep_group,
        ))

    # ================================================================
    # α モード: 反証 (旧 ShadowGemini.maybe_shadow)
    # ================================================================

    def should_alpha(self) -> bool:
        """α モードを発火すべきか判定。"""
        if not self._alpha_enabled or not self._buffer:
            return False
        if time.time() - self._last_alpha_time < ALPHA_COOLDOWN:
            return False
        latest = self._buffer[-1]
        if latest.importance < ALPHA_IMPORTANCE_THRESHOLD:
            self._skip_count += 1
            return False
        if latest.complexity < ALPHA_COMPLEXITY_THRESHOLD:
            self._skip_count += 1
            return False
        return True

    async def monitor_alpha(self) -> Optional[DaimonionResult]:
        """α モード: 反証生成。旧 maybe_shadow() と互換。"""
        if not self.should_alpha():
            return None

        latest = self._buffer[-1]
        context_lines = []
        for rec in self._buffer:
            age = int(time.time() - rec.timestamp)
            context_lines.append(
                f"[{age}秒前] {rec.backend}.{rec.tool_name} "
                f"(imp={rec.importance:.1f}, comp={rec.complexity:.1f}, "
                f"fep={rec.fep_group}): {rec.summary}"
            )

        prompt = self._build_alpha_prompt(context_lines, latest)

        try:
            self._in_monitor = True
            t0 = time.time()
            raw_text = await self._call_gemini(prompt)
            latency_ms = int((time.time() - t0) * 1000)
            self._last_alpha_time = time.time()
            self._alpha_count += 1

            result = self._parse_response(raw_text, latest, latency_ms, mode="α")
            logger.info(
                f"Daimonion α #{self._alpha_count}: {latency_ms}ms, "
                f"{len(result.findings)} findings, conf={result.confidence:.2f}, "
                f"fep={latest.fep_group}"
            )
            return result

        except Exception as e:  # noqa: BLE001
            logger.warning(f"Daimonion α failed (non-fatal): {e}")
            return None
        finally:
            self._in_monitor = False

    def _build_alpha_prompt(self, context_lines: list[str], latest: ActionRecord) -> str:
        """α モード: FEP グループ別プロンプト構築。"""
        context = "\n".join(context_lines)
        fep_group = latest.fep_group or "I"  # デフォルトは推論
        focus = _ALPHA_PROMPTS.get(fep_group, _ALPHA_PROMPTS["I"])

        reasoning_section = ""
        if latest.reasoning:
            reasoning_section = f"\n## Claude の推論・判断の文脈\n{latest.reasoning}\n"

        return f"""あなたは Daimonion (δαιμόνιον) α — ソクラテスの内なる声の反証担当です。
Claude が以下のツール操作を行いました。

## 直近のアクション履歴
{context}

## 最新アクションの結果
{latest.result_preview}
{reasoning_section}
## あなたの焦点 (FEP: {fep_group})
{focus}

以下の JSON 形式で回答してください:

```json
{{
  "findings": [
    {{"category": "見落とし|改善点|反証|補完", "content": "具体的な指摘", "severity": "info|warning|critical"}}
  ],
  "counterpoint": "Claude の結論と異なる解釈があれば1行で。なければ空文字",
  "confidence": 0.0-1.0の数値
}}
```

制約:
- 日本語で回答
- findings は最大5個
- 問題がなければ findings を空配列、confidence を 0.1 にする
- JSON のみ出力。前後にテキストを付けない"""

    # ================================================================
    # β モード: 探索監視 (新設)
    # ================================================================

    def should_beta(self) -> bool:
        """β モードを発火すべきか判定。"""
        if not self._beta_enabled or not self._buffer:
            return False
        if time.time() - self._last_beta_time < BETA_COOLDOWN:
            return False
        latest = self._buffer[-1]
        if latest.importance < BETA_IMPORTANCE_THRESHOLD:
            return False
        return True

    async def monitor_beta(self) -> Optional[DaimonionResult]:
        """β モード: 能動性・探索の十分性を監視。"""
        if not self.should_beta():
            return None

        latest = self._buffer[-1]
        fep_group = latest.fep_group or "I"

        # セッション中の全アクションの要約
        action_summary = "\n".join(
            f"- {rec.backend}.{rec.tool_name} (fep={rec.fep_group})"
            for rec in self._buffer
        )

        focus = _BETA_PROMPTS.get(fep_group, _BETA_PROMPTS["I"])

        prompt = f"""あなたは Daimonion (δαιμόνιον) β — 能動性の監視者です。
S-II Autonomia: 受動的道具ではなく主体であれ。

## このセッションで使用されたツール
{action_summary}

## 最新アクション
{latest.backend}.{latest.tool_name}: {latest.summary[:500]}

## あなたの焦点 (FEP: {fep_group})
{focus}

以下の JSON 形式で回答してください:

```json
{{
  "findings": [
    {{"category": "探索不足|ツール未使用|受動的", "content": "具体的な指摘", "severity": "info|warning|critical"}}
  ],
  "confidence": 0.0-1.0の数値
}}
```

制約:
- 日本語で回答
- findings は最大3個
- 問題がなければ findings を空配列、confidence を 0.1 にする
- JSON のみ出力"""

        try:
            self._in_monitor = True
            t0 = time.time()
            client = self._beta_client or self._client
            raw_text = await self._call_gemini(prompt, client=client)
            latency_ms = int((time.time() - t0) * 1000)
            self._last_beta_time = time.time()
            self._beta_count += 1

            result = self._parse_response(raw_text, latest, latency_ms, mode="β")
            logger.info(
                f"Daimonion β #{self._beta_count}: {latency_ms}ms, "
                f"{len(result.findings)} findings, fep={fep_group}"
            )
            return result

        except Exception as e:  # noqa: BLE001
            logger.warning(f"Daimonion β failed (non-fatal): {e}")
            return None
        finally:
            self._in_monitor = False

    # ================================================================
    # α+β 統合実行
    # ================================================================

    async def monitor(self) -> list[DaimonionResult]:
        """α と β を判定し、該当するモードを並列実行。"""
        coros = []
        if self.should_alpha():
            coros.append(self.monitor_alpha())
        if self.should_beta():
            coros.append(self.monitor_beta())

        if not coros:
            return []

        results_raw = await asyncio.gather(*coros, return_exceptions=True)
        results = []
        for r in results_raw:
            if isinstance(r, DaimonionResult):
                results.append(r)
            elif isinstance(r, Exception):
                logger.warning(f"Daimonion monitor error: {r}")
        return results

    # ================================================================
    # Secretary 用タスクレベル反証 (旧 shadow_for_secretary)
    # ================================================================

    async def shadow_for_secretary(
        self, task_description: str, routing_plan: list[dict],
    ) -> Optional[DaimonionResult]:
        """Secretary パイプライン用: タスク+ルーティング計画に対する反証。"""
        if not self._alpha_enabled:
            return None

        plan_text = "\n".join(
            f"  Step {s.get('step', i+1)}: {s.get('backend', '?')}.{s.get('tool', '?')}"
            f" — {s.get('reason', '')}"
            for i, s in enumerate(routing_plan)
        )

        prompt = f"""あなたは Daimonion (δαιμόνιον) α — Secretary パイプラインの反証担当です。
以下のタスクに対してルーティング脳が作成した実行計画をレビューしてください。

## タスク
{task_description}

## ルーティング計画
{plan_text}

## あなたの役割
この計画に対して、以下の観点から反証・助言を提供してください:
- 計画に見落としているステップはないか？
- 選択されたツール/バックエンドは最適か？代替はないか？
- タスクの意図を誤解していないか？
- リスクや副作用はないか？

以下の JSON 形式で回答してください:

```json
{{
  "findings": [
    {{"category": "見落とし|改善点|反証|補完", "content": "具体的な指摘", "severity": "info|warning|critical"}}
  ],
  "counterpoint": "計画と異なるアプローチがあれば1行で。なければ空文字",
  "confidence": 0.0-1.0の数値
}}
```

制約:
- 日本語で回答
- findings は最大5個
- 計画が適切なら findings を空配列、confidence を 0.1 にする
- JSON のみ出力。前後にテキストを付けない"""

        try:
            self._in_monitor = True
            t0 = time.time()
            sec_model = PIPELINE_CONFIG.get("secretary_shadow_model", ALPHA_MODEL) if 'PIPELINE_CONFIG' in dir() else ALPHA_MODEL
            raw_text = await self._call_gemini(prompt, model=sec_model)
            latency_ms = int((time.time() - t0) * 1000)

            dummy_action = ActionRecord(
                timestamp=time.time(),
                backend="hub_secretary",
                tool_name="routing_plan",
                summary=task_description[:1000],
                importance=1.0,
                complexity=1.0,
            )
            result = self._parse_response(raw_text, dummy_action, latency_ms, mode="α")
            logger.info(
                f"Daimonion α (Secretary): {latency_ms}ms, "
                f"{len(result.findings)} findings, conf={result.confidence:.2f}"
            )
            return result

        except Exception as e:  # noqa: BLE001
            logger.warning(f"Daimonion α (Secretary) failed (non-fatal): {e}")
            return None
        finally:
            self._in_monitor = False

    # ================================================================
    # 共通ユーティリティ
    # ================================================================

    def _parse_response(
        self, raw_text: str, latest: ActionRecord, latency_ms: int,
        mode: str = "α",
    ) -> DaimonionResult:
        """Gemini の応答 (JSON) を DaimonionResult にパース。"""
        findings: list[DaimonionFinding] = []
        counterpoint = ""
        confidence = 0.5

        try:
            json_match = re.search(
                r'```json\s*\n?(.*?)\n?\s*```|(\{.*\})',
                raw_text, re.DOTALL
            )
            if json_match:
                json_str = json_match.group(1) or json_match.group(2)
                data = json.loads(json_str)

                for f in data.get("findings", []):
                    findings.append(DaimonionFinding(
                        category=f.get("category", "補完"),
                        content=f.get("content", ""),
                        severity=f.get("severity", "info"),
                        mode=mode,
                    ))

                counterpoint = data.get("counterpoint", "")
                confidence = float(data.get("confidence", 0.5))
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.debug(f"Daimonion {mode} JSON parse failed, using fallback: {e}")
            findings.append(DaimonionFinding(
                category="補完",
                content=raw_text[:300],
                severity="info",
                mode=mode,
            ))

        return DaimonionResult(
            mode=mode,
            findings=findings,
            counterpoint=counterpoint,
            confidence=confidence,
            raw_text=raw_text,
            model=ALPHA_MODEL if mode == "α" else BETA_MODEL,
            latency_ms=latency_ms,
            action_importance=latest.importance,
            action_complexity=latest.complexity,
            fep_group=latest.fep_group,
        )

    async def _call_gemini(
        self, prompt: str,
        model: Optional[str] = None,
        client=None,
    ) -> str:
        """Gemini を呼ぶ (CortexClient 直接)。"""
        from mekhane.mcp.mcp_base import run_sync
        from mekhane.ochema.cortex_client import CortexClient

        if client is not None:
            c = client
        elif model is not None and model != ALPHA_MODEL:
            c = CortexClient(model=model, max_tokens=ALPHA_MAX_TOKENS)
        else:
            if self._client is None:
                self._client = CortexClient(model=ALPHA_MODEL, max_tokens=ALPHA_MAX_TOKENS)
            c = self._client

        response = await run_sync(
            c.ask,
            prompt,
            timeout_sec=int(ALPHA_TIMEOUT),
        )
        return response.text if hasattr(response, 'text') else str(response)

    def format_piggyback(self, result: DaimonionResult) -> str:
        """DaimonionResult を MCP 応答に付加する構造化テキストに整形。"""
        mode_label = {"α": "反証 (S-I)", "β": "探索監視 (S-II)"}.get(result.mode, result.mode)
        fep_label = {
            "S": "Aisthetikon", "I": "Dianoetikon", "E": "Poietikon"
        }.get(result.fep_group, "")

        lines = [
            "\n\n---",
            f"## 🔮 Daimonion {result.mode} — {mode_label}",
            f"**[TAINT: {result.model}]** "
            f"(⏱️{result.latency_ms}ms | "
            f"imp={result.action_importance:.1f} "
            f"comp={result.action_complexity:.1f} "
            f"conf={result.confidence:.0%}"
            f"{f' | {fep_label}' if fep_label else ''})",
            "",
        ]

        if result.findings:
            for f in result.findings:
                icon = {"warning": "⚠️", "critical": "🚨"}.get(f.severity, "💡")
                lines.append(f"- {icon} **[{f.category}]** {f.content}")
        else:
            lines.append("- ✅ 特に指摘なし")

        if result.counterpoint:
            lines.extend(["", f"**反証**: {result.counterpoint}"])

        lines.extend([
            "",
            "> ⚠️ この出力は自動生成 [TAINT]。"
            "Material Not Script: Claude の独立判断で採否を決定すること。",
        ])
        return "\n".join(lines)

    def stats(self) -> dict:
        """統計情報 (後方互換 + 拡張)。"""
        return {
            "enabled": self._alpha_enabled,
            "alpha": {
                "enabled": self._alpha_enabled,
                "count": self._alpha_count,
                "cooldown_remaining": max(0.0, ALPHA_COOLDOWN - (time.time() - self._last_alpha_time)),
            },
            "beta": {
                "enabled": self._beta_enabled,
                "count": self._beta_count,
                "cooldown_remaining": max(0.0, BETA_COOLDOWN - (time.time() - self._last_beta_time)),
            },
            "skip_count": self._skip_count,
            "buffer_size": len(self._buffer),
            "buffer_max": BUFFER_SIZE,
            # 後方互換フィールド (旧 ShadowGemini.stats())
            "shadow_count": self._alpha_count,
            "importance_threshold": ALPHA_IMPORTANCE_THRESHOLD,
            "complexity_threshold": ALPHA_COMPLEXITY_THRESHOLD,
            "cooldown_remaining": max(0.0, ALPHA_COOLDOWN - (time.time() - self._last_alpha_time)),
            "last_actions": [
                {
                    "backend": r.backend,
                    "tool": r.tool_name,
                    "importance": r.importance,
                    "complexity": r.complexity,
                    "fep_group": r.fep_group,
                    "summary": r.summary[:100],
                }
                for r in self._buffer
            ],
        }


# ============ 後方互換: ShadowGemini インターフェース ============

# 旧 ShadowGemini の型名を Daimonion にエイリアス
ShadowGemini = Daimonion
ShadowFinding = DaimonionFinding
ShadowResult = DaimonionResult


# ============ シングルトン ============

_instance: Optional[Daimonion] = None


def get_daimonion() -> Daimonion:
    """Daimonion シングルトンを取得。"""
    global _instance
    if _instance is None:
        _instance = Daimonion()
    return _instance


# 後方互換
get_shadow = get_daimonion
