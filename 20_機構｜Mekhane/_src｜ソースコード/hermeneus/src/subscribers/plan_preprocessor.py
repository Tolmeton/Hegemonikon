from __future__ import annotations
# PROOF: [L2/Phase3] <- hermeneus/src/subscribers/plan_preprocessor.py
# PURPOSE: 計画実行前に記憶と推薦を注入する層0サブスクライバ
"""
PlanPreprocessorSubscriber — 計画マクロの前処理 (v11.0)

VISION: 全機構が1つの認知の営みにシームレスに収束する (vision_living_cognition.md)
v9.x までのキーワードマッチを廃止し、Symploke SearchEngine によるベクトル検索に統合。

層0: 計画実行前に以下の HGK 機構を統合注入する
  Phase A — 統合記憶検索 (Symploke):
    全ドメイン (Gnōsis/Sophia/Kairos/Chronos) をベクトル検索で横断。
    結果が後続の Attractor/PolicyCheck に伝播する（不可分連動）。
  Phase B — 環境検査 (Peira + Basanos):
    システムヘルスと対象コード品質をチェック。
  Phase C — 推薦 (Attractor + PolicyCheck + Týpos):
    Phase A の結果を入力として定理推薦と収束/発散判定。
  Phase D — 調査提案 (Periskopē):
    Phase A で情報が不足していた場合に検索クエリを提案。

不可分連動: Phase A の結果が Phase C/D に流れる (情報伝播)。
各 Phase は孤島ではなく、1つの認知プロセスの部分。

発火条件:
    - MACRO_START イベント
    - マクロ名が "plan" を含む (@plan, @plan-, @plan+)
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from mekhane.paths import HANDOFF_DIR
from mekhane.symploke.handoff_files import list_handoff_files

from ..activation import BaseSubscriber, ActivationPolicy
from ..event_bus import CognitionEvent, EventType

logger = logging.getLogger(__name__)

# プロジェクトルートの解決 (symlink 対応)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


@dataclass
class PreprocessContext:
    """Phase 間の情報伝播コンテキスト (不可分連動の実現)

    各 Phase の出力がここに蓄積され、後続 Phase の入力になる。
    """
    query: str = ""
    # Phase A の結果
    memory_hits: list[dict] = field(default_factory=list)
    memory_summary: str = ""
    memory_sources: set[str] = field(default_factory=set)  # どのドメインがヒットしたか
    # Phase B の結果
    health_issues: list[str] = field(default_factory=list)
    # Phase C: Attractor が memory_hits を見て推薦を変える
    recommended_verbs: list[str] = field(default_factory=list)
    # Phase D: memory_hits が少なければ研究提案が濃くなる
    information_deficit: float = 1.0  # 0=十分, 1=不足


class PlanPreprocessorSubscriber(BaseSubscriber):
    """計画マクロの前処理: 統合記憶検索 + 環境チェック + 知識連動推薦

    FEP 同型: 事前予測モデルの注入 — 計画策定前に過去の経験と
    環境の構造を注入し、予測誤差の初期値を下げる。

    v10.0: Symploke SearchEngine 統合。Phase 間情報伝播。
    v11.0: Blackboard 統合。PreprocessContext → event.blackboard に同期。
           score() を動的化 (blackboard に既存 memory があれば価値低下)。
    """

    def __init__(self, fire_threshold: float = 0.0):
        super().__init__(
            name="plan_preprocessor",
            policy=ActivationPolicy(
                event_types={EventType.MACRO_START},
                custom_predicate=self._is_plan_macro,
            ),
            fire_threshold=fire_threshold,
        )
        self._search_engine = None
        self._search_init_attempted = False

    @staticmethod
    def _is_plan_macro(event: CognitionEvent) -> bool:
        """@plan, @plan-, @plan+ のいずれかか"""
        name = event.metadata.get("macro_name", "")
        return "plan" in name.lower()

    def score(self, event: CognitionEvent) -> float:
        """計画マクロの情報価値を動的評価 (Phase 3)

        Blackboard に既に memory_hits がある場合、追加注入の価値は低い。
        """
        bb = getattr(event, 'blackboard', None)
        if bb and bb.memory:
            # 既に記憶が注入済み → 追加価値は低いが非ゼロ
            s = 0.4
        else:
            s = 1.0
        self._score_history.append(s)
        return s

    def handle(self, event: CognitionEvent) -> Optional[str]:
        """統合認知パイプライン: Phase A→B→C→D の不可分連動 (v11.0)

        v11.0: Phase 結果を event.blackboard に同期。
        後続 Subscriber が blackboard 経由で結果を参照可能。
        """
        query = event.metadata.get("context", "")
        ctx = PreprocessContext(query=query)
        parts: list[str] = []

        # ═══ Phase A: 統合記憶検索 ═══
        memory_result = self._phase_a_memory_search(ctx)
        if memory_result:
            parts.append(memory_result)

        # ═══ Phase B: 環境検査 ═══
        env_result = self._phase_b_environment(ctx)
        if env_result:
            parts.append(env_result)

        # ═══ Phase C: 推薦 (Phase A の結果を入力) ═══
        rec_result = self._phase_c_recommend(ctx)
        if rec_result:
            parts.append(rec_result)

        # ═══ Phase D: 調査提案 (Phase A の不足を補う) ═══
        research_result = self._phase_d_research(ctx)
        if research_result:
            parts.append(research_result)

        # ═══ Blackboard 同期 (v11.0) ═══
        bb = getattr(event, 'blackboard', None)
        if bb is not None:
            self._sync_to_blackboard(ctx, bb)

        if not parts:
            return None

        return "\n\n".join(parts)

    def _sync_to_blackboard(self, ctx: PreprocessContext, bb) -> None:
        """PreprocessContext の結果を CognitionBlackboard に同期

        PreprocessContext (v10 の内部状態) → Blackboard (v11 の共有状態)。
        他の Subscriber がこの結果を読める。
        """
        src = "plan_preprocessor"
        if ctx.memory_hits:
            bb.write("memory.plan_search", ctx.memory_hits, source=src)
        if ctx.memory_sources:
            for s in ctx.memory_sources:
                bb.write("memory_sources", s, source=src)
        if ctx.recommended_verbs:
            bb.write("recommended_verbs", ctx.recommended_verbs, source=src)
        bb.write("information_deficit", ctx.information_deficit, source=src)
        if ctx.health_issues:
            bb.write("health.plan_issues", ctx.health_issues, source=src)

    # ─── Phase A: 統合記憶検索 ─────────────────────────────

    def _phase_a_memory_search(self, ctx: PreprocessContext) -> Optional[str]:
        """Symploke SearchEngine で全ドメインを横断検索"""
        if not ctx.query:
            return None

        # Symploke SearchEngine を遅延初期化
        if not self._search_init_attempted:
            self._search_init_attempted = True
            try:
                from mekhane.symploke.search.search_factory import get_search_engine
                self._search_engine, errors = get_search_engine(
                    ["gnosis", "sophia", "kairos", "chronos"]
                )
                if errors:
                    logger.info("SearchEngine init errors: %s", errors)
            except Exception as e:  # noqa: BLE001
                logger.debug("Symploke SearchEngine not available: %s", e)

        # ベクトル検索実行
        if self._search_engine is not None:
            try:
                results = self._search_engine.search(ctx.query, k=5)
                if results:
                    lines = ["[🧠 統合記憶検索 (Symploke)]"]
                    for r in results:
                        source = r.source.value if hasattr(r.source, 'value') else str(r.source)
                        title = r.metadata.get("title", r.doc_id)[:80]
                        lines.append(f"  [{source}] {title} (score: {r.score:.2f})")
                        ctx.memory_hits.append({
                            "source": source, "title": title,
                            "score": r.score, "content": r.content[:200],
                        })
                        ctx.memory_sources.add(source)
                    ctx.information_deficit = max(0.0, 1.0 - len(results) * 0.2)
                    ctx.memory_summary = "; ".join(
                        r.metadata.get("title", r.doc_id)[:40] for r in results[:3]
                    )
                    return "\n".join(lines)
            except Exception as e:  # noqa: BLE001
                logger.debug("Symploke search failed: %s", e)

        # Fallback: ファイルベース検索 (Symploke 初期化失敗時)
        return self._fallback_file_search(ctx)

    def _fallback_file_search(self, ctx: PreprocessContext) -> Optional[str]:
        """Symploke 不在時のフォールバック (キーワード検索)"""
        if not ctx.query:
            return None
        results: list[str] = []

        # Kairos (Handoff)
        if HANDOFF_DIR.exists():
            hits = self._keyword_search_files(
                ctx.query, list_handoff_files(HANDOFF_DIR)[:5]
            )
            for name, score in hits:
                results.append(f"  [kairos] {name} (match: {score})")
                ctx.memory_hits.append({"source": "kairos", "title": name, "score": score / 10})
                ctx.memory_sources.add("kairos")

        # Chronos (Sessions)
        sessions_dir = _PROJECT_ROOT / "mneme" / ".hegemonikon" / "sessions"
        if sessions_dir.exists():
            hits = self._keyword_search_files(
                ctx.query, sorted(sessions_dir.glob("*.md"), reverse=True)[:10]
            )
            for name, score in hits:
                results.append(f"  [chronos] {name} (match: {score})")
                ctx.memory_hits.append({"source": "chronos", "title": name, "score": score / 10})
                ctx.memory_sources.add("chronos")

        # Sophia (KI) — SOURCE: find で確認した正しいパス
        ki_dir = _PROJECT_ROOT / "hegemonikon" / "nous" / "knowledge_items"
        if ki_dir.exists():
            overviews = list(ki_dir.glob("*/artifacts/overview.md"))
            flat_kis = [f for f in ki_dir.glob("*.md") if f.is_file()]
            hits = self._keyword_search_files(ctx.query, (overviews + flat_kis)[:20])
            for name, score in hits:
                results.append(f"  [sophia] {name} (match: {score})")
                ctx.memory_hits.append({"source": "sophia", "title": name, "score": score / 10})
                ctx.memory_sources.add("sophia")

        if results:
            ctx.information_deficit = max(0.0, 1.0 - len(results) * 0.15)
            lines = ["[🧠 記憶検索 (fallback/keyword)]"] + results[:6]
            return "\n".join(lines)
        ctx.information_deficit = 1.0
        return None

    # ─── Phase B: 環境検査 ─────────────────────────────────

    def _phase_b_environment(self, ctx: PreprocessContext) -> Optional[str]:
        """Peira Health + Basanos Scan"""
        lines: list[str] = []

        # Peira: Heartbeat + Handoff + MCP
        try:
            hb_file = _PROJECT_ROOT / "hegemonikon" / "mekhane" / "sympatheia" / "state" / "heartbeat.json"
            if hb_file.exists():
                import json, time
                data = json.loads(hb_file.read_text(encoding="utf-8"))
                age_min = (time.time() - data.get("timestamp", 0)) / 60
                if age_min > 30:
                    lines.append(f"  💔 Heartbeat 古い ({age_min:.0f}分前)")
                    ctx.health_issues.append("heartbeat_stale")
                else:
                    lines.append(f"  💚 Heartbeat ({age_min:.0f}分前)")

            if HANDOFF_DIR.exists():
                count = len(list_handoff_files(HANDOFF_DIR))
                lines.append(f"  💚 Handoff: {count}件")
        except Exception as e:  # noqa: BLE001
            logger.debug("Peira check failed: %s", e)

        # Basanos: PROOF ヘッダー
        if ctx.query:
            import re
            paths = re.findall(r'[\w/]+\.py', ctx.query)
            for p in paths[:3]:
                fpath = _PROJECT_ROOT / "hegemonikon" / p
                if fpath.exists():
                    try:
                        head = fpath.read_text(encoding="utf-8")[:200]
                        if "# PROOF:" in head:
                            lines.append(f"  ✅ {p}")
                        else:
                            lines.append(f"  ❌ PROOF欠如: {p}")
                            ctx.health_issues.append(f"no_proof:{p}")
                    except Exception:  # noqa: BLE001
                        pass

        if lines:
            return "[🏥 環境検査 (Peira+Basanos)]\n" + "\n".join(lines)
        return None

    # ─── Phase C: 推薦 (Phase A 結果を入力) ────────────────

    def _phase_c_recommend(self, ctx: PreprocessContext) -> Optional[str]:
        """Attractor + PolicyCheck — Phase A の結果に基づいて推薦を変える"""
        lines: list[str] = []

        # Attractor: Phase A の結果で推薦を動的変更
        verb_map = {
            "noe": (["本質", "深い", "理解", "構造", "ontology"], "深い認識"),
            "bou": (["目的", "意志", "望む", "ゴール", "vision"], "意志の明確化"),
            "zet": (["問い", "探求", "なぜ", "原因", "investigate"], "問いの発見"),
            "ene": (["実装", "作る", "コード", "build", "implement"], "行為の具現化"),
            "dia": (["判定", "評価", "検証", "review", "verify"], "判定力"),
            "tek": (["手法", "方法", "手順", "workflow", "process"], "既知手法の適用"),
            "ske": (["破壊", "前提", "疑問", "仮説", "assumption"], "仮説空間の拡大"),
            "ops": (["全体", "俯瞰", "概要", "overview", "architecture"], "全体推論"),
            "ele": (["問い直", "信念", "検知", "精査", "reexamine"], "信念の問い直し"),
        }

        # コンテキスト + Phase A の memory_summary を結合して推薦
        combined_text = (ctx.query + " " + ctx.memory_summary).lower()[:400]
        scored: list[tuple[str, str, int]] = []
        for verb, (keywords, label) in verb_map.items():
            score = sum(1 for kw in keywords if kw in combined_text)
            # Phase A で関連知識が見つかった場合、/noe+ より /ene+ を推薦
            if "gnosis" in ctx.memory_sources and verb == "noe":
                score += 1  # 論文があるなら深堀りの価値あり
            if "kairos" in ctx.memory_sources and verb == "tek":
                score += 1  # 過去の計画があるなら既知手法を再利用
            if score > 0:
                scored.append((verb, label, score))
                ctx.recommended_verbs.append(verb)

        if scored:
            scored.sort(key=lambda x: x[2], reverse=True)
            lines.append("[🧲 定理推薦 (Attractor)]")
            for verb, label, score in scored[:3]:
                source_hint = ""
                if verb in ("noe",) and "gnosis" in ctx.memory_sources:
                    source_hint = " ← 論文あり"
                elif verb in ("tek",) and "kairos" in ctx.memory_sources:
                    source_hint = " ← 過去計画あり"
                lines.append(f"  /{verb}+ ({label}, match:{score}){source_hint}")

        # PolicyCheck: 収束/発散判定
        CONVERGENT = ["実装", "修正", "バグ", "テスト", "デプロイ", "fix", "build", "refactor"]
        DIVERGENT = ["探索", "アイデア", "調査", "設計", "戦略", "research", "explore", "design"]
        c_score = sum(1 for kw in CONVERGENT if kw in combined_text)
        d_score = sum(1 for kw in DIVERGENT if kw in combined_text)
        if c_score > d_score:
            lines.append("[🎯 タスク分類] 収束型 → .prompt 推奨")
        elif d_score > c_score:
            lines.append("[🎯 タスク分類] 発散型 → 自由形式推奨")

        # Týpos: .prompt コンパイル (存在すれば)
        try:
            prompt_dirs = [
                _PROJECT_ROOT / "hegemonikon" / "nous" / "workflows" / "ccl",
                _PROJECT_ROOT / "hegemonikon" / "nous" / "skills",
            ]
            for d in prompt_dirs:
                for pf in (d.glob("*plan*.prompt") if d.exists() else []):
                    from mekhane.ergasterion.typos.typos import TyposParser
                    prompt = TyposParser().parse(pf.read_text(encoding="utf-8"))
                    lines.append(f"[📝 Týpos] {pf.name}: role={bool(prompt.role)}, "
                                 f"制約={len(prompt.constraints)}, ブロック={len(prompt.blocks)}")
                    break
        except Exception:  # noqa: BLE001
            pass

        if lines:
            return "\n".join(lines)
        return None

    # ─── Phase D: 調査提案 (Phase A の不足を補う) ──────────

    def _phase_d_research(self, ctx: PreprocessContext) -> Optional[str]:
        """Periskopē: Phase A の情報不足度に応じて検索提案を生成"""
        if ctx.information_deficit < 0.5:
            return None  # 十分な情報がある → 調査不要
        if not ctx.query or len(ctx.query) < 10:
            return None

        import re
        jp_words = re.findall(r'[\u4e00-\u9fff\u30a0-\u30ff]{3,}', ctx.query[:300])
        en_words = re.findall(r'[a-zA-Z]{4,}', ctx.query[:300])
        keywords = list(set(jp_words[:5] + en_words[:5]))
        if not keywords:
            return None

        lines = [f"[🔭 調査提案 (Periskopē) — 情報不足度: {ctx.information_deficit:.1f}]"]
        main_query = " ".join(keywords[:3])
        lines.append(f"  推奨: `periskope_research('{main_query}')`")

        # Phase A の結果で推奨ソースを変える
        sources = []
        missing = {"gnosis", "sophia", "kairos", "chronos"} - ctx.memory_sources
        if "gnosis" in missing:
            sources.append("semantic_scholar")
        if any(kw in ctx.query.lower() for kw in ["実装", "コード", "python"]):
            sources.append("github")
        if not sources:
            sources = ["searxng", "brave"]
        lines.append(f"  推奨ソース: {', '.join(sources)}")

        return "\n".join(lines)

    # ─── 共通ユーティリティ ────────────────────────────────

    @staticmethod
    def _keyword_search_files(
        query: str, files: list[Path], max_results: int = 3
    ) -> list[tuple[str, int]]:
        """フォールバック用キーワード検索"""
        query_lower = query[:200].lower()
        words = [w for w in query_lower.split() if len(w) > 2]
        if not words:
            return []
        matches: list[tuple[str, int]] = []
        for f in files:
            try:
                content = f.read_text(encoding="utf-8")[:800].lower()
                score = sum(1 for w in words if w in content)
                if score > 0:
                    matches.append((f.stem, score))
            except Exception:  # noqa: BLE001
                pass
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:max_results]
