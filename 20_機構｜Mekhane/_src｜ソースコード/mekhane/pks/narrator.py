from __future__ import annotations
# noqa: AI-ALL
# PROOF: [L2/インフラ] <- mekhane/pks/
"""
PROOF: [L2/インフラ] このファイルは存在しなければならない

A0 (FEP) → 知識の能動的表面化には多視点の対話的解説が必要
→ NotebookLM Audio Overview のテキスト版
→ narrator.py が担う

# PURPOSE: 知識を多様なフォーマットで対話形式に表面化する
"""


from dataclasses import dataclass
from typing import Optional
import re

from mekhane.pks.llm_client import PKSLLMClient
from mekhane.pks.pks_engine import KnowledgeNugget
from mekhane.pks.narrator_formats import (
    NarratorFormat,
    get_format_spec,
    get_speaker_pattern,
)
from mekhane.ochema.model_defaults import FLASH


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: 対話の一セグメント
class NarrativeSegment:
    """対話の一セグメント"""

    speaker: str  # "Advocate", "Critic", "Narrator", "Pro", "Con"
    content: str


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: 多フォーマット対応の対話形式サマリー
class Narrative:
    """多フォーマット対応の対話形式サマリー"""

    title: str
    segments: list[NarrativeSegment]
    format: NarratorFormat = NarratorFormat.DEEP_DIVE
    source_nugget: Optional[KnowledgeNugget] = None
    source_nuggets: Optional[list[KnowledgeNugget]] = None  # Deep Dive 用

    # PURPOSE: Markdown 対話形式に出力
    def to_markdown(self) -> str:
        """Markdown 対話形式に出力"""
        spec = get_format_spec(self.format)
        lines = [
            f"## {spec.icon} PKS Narrative ({self.format.value}): {self.title}",
            "",
        ]

        # ソース表示
        if self.source_nugget and self.source_nugget.url:
            lines.append(f"*Source: [{self.source_nugget.source}]({self.source_nugget.url})*")
            lines.append("")
        elif self.source_nuggets:
            for i, n in enumerate(self.source_nuggets, 1):
                src = f"[{n.source}]({n.url})" if n.url else n.source
                lines.append(f"*[{i}] {src}: {n.title[:60]}*")
            lines.append("")

        # スピーカーごとのアイコンマッピング
        speaker_icons = {
            "Advocate": "🟢",
            "Critic": "🔴",
            "Narrator": "📢",
            "Pro": "🔵",
            "Con": "🟠",
        }

        for seg in self.segments:
            icon = speaker_icons.get(seg.speaker, "💬")
            lines.append(f"**{icon} {seg.speaker}**: {seg.content}")
            lines.append("")

        return "\n".join(lines)


# PURPOSE: NotebookLM Audio Overview 相当の「知識が語りかける」機構 (Multi-format)
class PKSNarrator:
    """NotebookLM Audio Overview 相当の「知識が語りかける」機構

    4 フォーマット対応:
      - DEEP_DIVE: 複数ナゲットを横断する統合対話 (デフォルト)
      - BRIEF: 要約のみの短縮版
      - CRITIQUE: 批判的フィードバック特化
      - DEBATE: 賛否両論を対等に展開

    Phase 1: テンプレートベースの簡易生成
    Phase 2: Gemini 経由の高品質対話生成 (フォールバック付き)
    """

    # 後方互換 — 旧 _LLM_PROMPT は DEEP_DIVE の単一ナゲット版として保持
    _LLM_PROMPT_LEGACY = (
        "以下の知識について、Advocate（推薦者）と Critic（批判者）の対話を生成してください。\n\n"
        "タイトル: {title}\n"
        "要約: {abstract}\n"
        "ソース: {source}\n"
        "関連度: {score}\n\n"
        "出力形式 (厳密に守ってください):\n"
        "ADVOCATE: (この知識の価値と応用可能性を具体的に主張)\n"
        "CRITIC: (限界、注意点、前提条件を指摘)\n"
        "ADVOCATE: (批判に応答し、最終的な推薦を述べる)\n\n"
        "各発言は1-2文で簡潔に。日本語で。"
    )

    # PURPOSE: PKSNarrator の初期化
    def __init__(
        self,
        use_llm: bool = True,
        model: str = FLASH,
        default_format: NarratorFormat = NarratorFormat.DEEP_DIVE,
    ):
        self._llm = PKSLLMClient(model=model, enabled=use_llm)
        self._default_format = default_format

    # PURPOSE: narrator の llm available 処理を実行する
    @property
    def llm_available(self) -> bool:
        return self._llm.available

    # PURPOSE: narrator の default format 処理を実行する
    @property
    def default_format(self) -> NarratorFormat:
        return self._default_format

    # PURPOSE: narrator の default format 処理を実行する
    @default_format.setter
    def default_format(self, fmt: NarratorFormat) -> None:
        self._default_format = fmt

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────

    # PURPOSE: 単一ナゲットを対話形式に変換
    def narrate(
        self,
        nugget: KnowledgeNugget,
        fmt: Optional[NarratorFormat] = None,
    ) -> Narrative:
        """KnowledgeNugget を対話形式に変換

        Args:
            nugget: 変換対象
            fmt: 出力フォーマット (省略時はデフォルト)
        """
        fmt = fmt or self._default_format

        if self.llm_available:
            narrative = self._narrate_llm_single(nugget, fmt)
            if narrative:
                return narrative

        return self._narrate_template(nugget, fmt)

    # PURPOSE: 複数ナゲットを横断する統合対話を生成 (Deep Dive 専用)
    def narrate_deep_dive(
        self,
        nuggets: list[KnowledgeNugget],
        fmt: Optional[NarratorFormat] = None,
    ) -> Narrative:
        """複数ナゲットを横断する統合対話を生成

        Deep Dive モードでは複数のナゲットの関連性を分析し、
        統合的な対話を生成する。
        """
        fmt = fmt or NarratorFormat.DEEP_DIVE

        if self.llm_available and len(nuggets) > 1:
            narrative = self._narrate_llm_multi(nuggets, fmt)
            if narrative:
                return narrative

        # フォールバック: 各ナゲットを個別に処理して結合
        return self._narrate_template_multi(nuggets, fmt)

    # PURPOSE: 複数 nugget をバッチで対話化
    def narrate_batch(
        self,
        nuggets: list[KnowledgeNugget],
        fmt: Optional[NarratorFormat] = None,
    ) -> list[Narrative]:
        """複数 nugget をバッチで対話化"""
        fmt = fmt or self._default_format
        return [self.narrate(n, fmt=fmt) for n in nuggets]

    # PURPOSE: ナラティブ群を一つのレポートに整形
    def format_report(self, narratives: list[Narrative]) -> str:
        """ナラティブ群を一つのレポートに整形"""
        if not narratives:
            return "📭 ナラティブ対象なし"

        # フォーマットのアイコンを取得
        fmt_icon = "🎙️"
        fmt_name = "Mixed"
        if narratives:
            spec = get_format_spec(narratives[0].format)
            fmt_icon = spec.icon
            fmt_name = narratives[0].format.value

        lines = [
            f"# {fmt_icon} PKS Narrative Report ({fmt_name})",
            "",
            f"_生成数: {len(narratives)} 件_",
            "",
            "---",
        ]

        for narrative in narratives:
            lines.append("")
            lines.append(narrative.to_markdown())
            lines.append("---")

        return "\n".join(lines)

    # ──────────────────────────────────────────
    # LLM 生成 (Phase 2)
    # ──────────────────────────────────────────

    # PURPOSE: 単一ナゲットの LLM 対話生成
    def _narrate_llm_single(
        self, nugget: KnowledgeNugget, fmt: NarratorFormat
    ) -> Optional[Narrative]:
        """単一ナゲットの LLM 対話生成"""
        spec = get_format_spec(fmt)
        context = (
            f"タイトル: {nugget.title}\n"
            f"要約: {(nugget.abstract or '')[:500]}\n"
            f"ソース: {nugget.source}\n"
            f"関連度: {nugget.relevance_score:.2f}"
        )
        prompt = spec.system_prompt.format(context=context)

        try:
            text = self._llm.generate(prompt)
            if text:
                return self._parse_llm_response(text, fmt, nugget=nugget)
        except Exception as e:  # noqa: BLE001
            print(f"[Narrator] LLM error: {e}")

        return None

    # PURPOSE: 複数ナゲットの LLM 統合対話生成
    def _narrate_llm_multi(
        self, nuggets: list[KnowledgeNugget], fmt: NarratorFormat
    ) -> Optional[Narrative]:
        """複数ナゲットの LLM 統合対話生成"""
        spec = get_format_spec(fmt)
        context_parts = []
        for i, n in enumerate(nuggets, 1):
            context_parts.append(
                f"[{i}] タイトル: {n.title}\n"
                f"    要約: {(n.abstract or '')[:300]}\n"
                f"    ソース: {n.source}\n"
                f"    関連度: {n.relevance_score:.2f}"
            )
        context = "\n\n".join(context_parts)
        prompt = spec.system_prompt.format(context=context)

        try:
            text = self._llm.generate(prompt)
            if text:
                title = f"{len(nuggets)} 知識の統合分析"
                return self._parse_llm_response(
                    text, fmt, title=title, nuggets=nuggets
                )
        except Exception as e:  # noqa: BLE001
            print(f"[Narrator] LLM multi error: {e}")

        return None

    # PURPOSE: LLM 応答をフォーマットに応じてパース
    def _parse_llm_response(
        self,
        text: str,
        fmt: NarratorFormat,
        nugget: Optional[KnowledgeNugget] = None,
        title: Optional[str] = None,
        nuggets: Optional[list[KnowledgeNugget]] = None,
    ) -> Optional[Narrative]:
        """LLM 応答をフォーマットのスピーカーパターンでパース"""
        speaker_pattern = get_speaker_pattern(fmt)
        spec = get_format_spec(fmt)

        pattern = re.compile(
            rf"({speaker_pattern}):\s*(.+?)(?=(?:{speaker_pattern}):|$)",
            re.DOTALL,
        )
        matches = pattern.findall(text)

        segments = []
        speaker_map = {s.upper(): s for s in spec.speakers}

        for speaker_raw, content in matches:
            speaker = speaker_map.get(speaker_raw.upper(), speaker_raw.title())
            content = content.strip()
            if content:
                segments.append(NarrativeSegment(speaker=speaker, content=content))

        if len(segments) >= spec.min_segments:
            narrative_title = title or (nugget.title if nugget else "Untitled")
            return Narrative(
                title=narrative_title,
                segments=segments,
                format=fmt,
                source_nugget=nugget,
                source_nuggets=nuggets,
            )

        return None  # パース失敗 → テンプレートフォールバック

    # ──────────────────────────────────────────
    # テンプレート生成 (Phase 1 フォールバック)
    # ──────────────────────────────────────────

    # PURPOSE: 単一ナゲットのテンプレート生成
    def _narrate_template(
        self, nugget: KnowledgeNugget, fmt: NarratorFormat
    ) -> Narrative:
        """フォーマット別のテンプレートベース対話生成"""
        generators = {
            NarratorFormat.DEEP_DIVE: self._template_deep_dive,
            NarratorFormat.BRIEF: self._template_brief,
            NarratorFormat.CRITIQUE: self._template_critique,
            NarratorFormat.DEBATE: self._template_debate,
        }
        generator = generators.get(fmt, self._template_deep_dive)
        segments = generator(nugget)

        return Narrative(
            title=nugget.title,
            segments=segments,
            format=fmt,
            source_nugget=nugget,
        )

    # PURPOSE: 複数ナゲットのテンプレート結合
    def _narrate_template_multi(
        self, nuggets: list[KnowledgeNugget], fmt: NarratorFormat
    ) -> Narrative:
        """複数ナゲットを統合するテンプレートフォールバック"""
        if not nuggets:
            return Narrative(
                title="(empty)",
                segments=[NarrativeSegment(speaker="Narrator", content="対象なし")],
                format=fmt,
            )

        segments = []

        # 導入: 全体概要
        titles = [n.title[:40] for n in nuggets[:5]]
        segments.append(NarrativeSegment(
            speaker="Advocate",
            content=f"{len(nuggets)} 件の知識が関連しています: {', '.join(titles)}。"
            "これらを横断的に見ることで、より深い理解が得られます。",
        ))

        # 各ナゲットの要約
        for n in nuggets[:3]:
            abstract = (n.abstract or "")[:150]
            segments.append(NarrativeSegment(
                speaker="Advocate",
                content=f"「{n.title}」({n.source}): {abstract}",
            ))

        # 批判
        segments.append(NarrativeSegment(
            speaker="Critic",
            content="ただし、これらの知識の結びつきはベクトル距離に基づくものであり、"
            "因果関係を示すものではありません。表層的な類似性に注意してください。",
        ))

        # 結論
        avg_score = sum(n.relevance_score for n in nuggets) / len(nuggets)
        segments.append(NarrativeSegment(
            speaker="Advocate",
            content=f"平均関連度 {avg_score:.2f} は一読の価値を示唆しています。"
            "Creator の文脈でこれらを再評価してください。",
        ))

        return Narrative(
            title=f"{len(nuggets)} 知識の統合分析",
            segments=segments,
            format=fmt,
            source_nuggets=nuggets,
        )

    # ──────────────────────────────────────────
    # フォーマット別テンプレート
    # ──────────────────────────────────────────

    # PURPOSE: Deep Dive テンプレート (既存互換 + 拡張)
    def _template_deep_dive(self, nugget: KnowledgeNugget) -> list[NarrativeSegment]:
        """Deep Dive: Advocate vs Critic の標準対話 (5 セグメント)"""
        abstract = (nugget.abstract or "")[:200]
        segments = []

        # 1. Advocate: 概要と価値
        parts = ["この研究は注目に値します。"]
        if nugget.push_reason:
            parts.append(f"{nugget.push_reason}。")
        parts.append(f"概要: {abstract}")
        segments.append(NarrativeSegment(speaker="Advocate", content=" ".join(parts)))

        # 2. Critic: 限界と注意
        parts = ["ただし注意が必要です。"]
        if nugget.relevance_score < 0.8:
            parts.append(
                f"関連度スコアは {nugget.relevance_score:.2f} で、"
                "確定的な関連性とは言えません。"
            )
        parts.append("実際のコンテキストとの適合性は人間の判断が必要です。")
        if nugget.source in ("arxiv", "semantic_scholar"):
            parts.append("プレプリントの場合、査読状況も確認すべきです。")
        segments.append(NarrativeSegment(speaker="Critic", content=" ".join(parts)))

        # 3. Advocate: 応答
        segments.append(NarrativeSegment(
            speaker="Advocate",
            content="確かにその通りです。"
            "この知識は参考として提示しているものであり、"
            "最終的な判断は Creator に委ねます。",
        ))

        # 4. Critic: 深掘り提案
        segments.append(NarrativeSegment(
            speaker="Critic",
            content="深掘りするなら、このトピックの周辺分野も合わせて調査することを推奨します。"
            "単一の知識源に依存するリスクを軽減できます。",
        ))

        # 5. Advocate: 結論
        segments.append(NarrativeSegment(
            speaker="Advocate",
            content=f"関連度 {nugget.relevance_score:.2f} は、"
            "少なくとも一読の価値があることを示しています。"
            "知識を広げるきっかけとしてご活用ください。",
        ))

        return segments

    # PURPOSE: Brief テンプレート
    def _template_brief(self, nugget: KnowledgeNugget) -> list[NarrativeSegment]:
        """Brief: 30 秒で読める要約"""
        abstract = (nugget.abstract or "")[:250]
        segments = []

        segments.append(NarrativeSegment(
            speaker="Narrator",
            content=f"「{nugget.title}」({nugget.source}): {abstract}",
        ))

        reason = nugget.push_reason or f"関連度 {nugget.relevance_score:.2f}"
        segments.append(NarrativeSegment(
            speaker="Narrator",
            content=f"プッシュ理由: {reason}。",
        ))

        return segments

    # PURPOSE: Critique テンプレート
    def _template_critique(self, nugget: KnowledgeNugget) -> list[NarrativeSegment]:
        """Critique: 批判的フィードバック特化"""
        segments = []

        # 1. 限界指摘
        segments.append(NarrativeSegment(
            speaker="Critic",
            content=f"「{nugget.title}」の限界: "
            f"関連度 {nugget.relevance_score:.2f} は完全な一致を示すものではなく、"
            "ベクトル空間での近似に基づいています。",
        ))

        # 2. 前提条件の明示
        source_warning = {
            "arxiv": "arXiv プレプリントであり、査読を経ていない可能性があります。",
            "semantic_scholar": "学術論文ですが、引用数や発行年の確認が必要です。",
            "handoff": "セッション引継ぎ文書であり、その時点のコンテキストに依存します。",
            "kernel": "Hegemonikón カーネル文書であり、理論的定義です。",
        }.get(nugget.source, "ソースの信頼性を個別に確認してください。")
        segments.append(NarrativeSegment(
            speaker="Critic",
            content=f"暗黙の前提: {source_warning}",
        ))

        # 3. 改善提案
        segments.append(NarrativeSegment(
            speaker="Critic",
            content="改善提案: 追加の検索クエリを変えて再検索するか、"
            "原典に直接あたることで確信度を上げられます。",
        ))

        # 4. それでもの価値
        segments.append(NarrativeSegment(
            speaker="Advocate",
            content="批判は全て妥当ですが、"
            "知らなかった情報を知ったこと自体に価値があります。"
            "批判的に受け取った上で、視野拡大のきっかけとしてください。",
        ))

        return segments

    # PURPOSE: Debate テンプレート
    def _template_debate(self, nugget: KnowledgeNugget) -> list[NarrativeSegment]:
        """Debate: PRO vs CON の対等な議論"""
        abstract = (nugget.abstract or "")[:150]
        segments = []

        # 1. Pro: 採用理由
        segments.append(NarrativeSegment(
            speaker="Pro",
            content=f"「{nugget.title}」は検討に値します。{abstract} "
            f"関連度 {nugget.relevance_score:.2f} は有意な水準です。",
        ))

        # 2. Con: 不採用理由
        segments.append(NarrativeSegment(
            speaker="Con",
            content="しかし、ベクトル類似度は意味的な同意を保証しません。"
            "文脈のズレが結論を誤導する可能性があります。",
        ))

        # 3. Pro: 反論
        segments.append(NarrativeSegment(
            speaker="Pro",
            content="確かにベクトル類似度だけでは不十分ですが、"
            "Reranker による cross-encoder スコアも考慮されています。"
            "複合的な判断であることを忘れないでください。",
        ))

        # 4. Con: 再反論
        segments.append(NarrativeSegment(
            speaker="Con",
            content="Reranker は相対順位を改善しますが、"
            "絶対的な関連性を保証するものではありません。"
            "最終的な判断は人間の領域です。",
        ))

        # 5. Pro: 最終主張
        segments.append(NarrativeSegment(
            speaker="Pro",
            content="同意します。私の主張は「読む価値がある」であって"
            "「これが正解だ」ではありません。",
        ))

        # 6. Con: 最終反論
        segments.append(NarrativeSegment(
            speaker="Con",
            content="その謙虚さが重要です。"
            "知識はツールであり、使い手の判断が最終的な価値を決めます。",
        ))

        return segments

    # ──────────────────────────────────────────
    # 後方互換 API
    # ──────────────────────────────────────────

    # PURPOSE: 後方互換メソッド群
    def _generate_advocate(self, nugget: KnowledgeNugget) -> str:
        """後方互換: Advocate の発言を生成"""
        segs = self._template_deep_dive(nugget)
        return segs[0].content if segs else ""

    # PURPOSE: [L2-auto] _generate_critic の関数定義
    def _generate_critic(self, nugget: KnowledgeNugget) -> str:
        """後方互換: Critic の発言を生成"""
        segs = self._template_deep_dive(nugget)
        return segs[1].content if len(segs) > 1 else ""

    # PURPOSE: [L2-auto] _generate_response の関数定義
    def _generate_response(self, nugget: KnowledgeNugget) -> str:
        """後方互換: Advocate の応答を生成"""
        segs = self._template_deep_dive(nugget)
        return segs[2].content if len(segs) > 2 else ""
