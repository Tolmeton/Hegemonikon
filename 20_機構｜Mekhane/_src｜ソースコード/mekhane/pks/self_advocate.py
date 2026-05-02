from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/pks/
"""
PROOF: [L2/インフラ] このファイルは存在しなければならない

A0 (FEP) → 予測誤差最小化には知識の主体的表面化が必要
→ Pull型の逆転 → データが自ら一人称で語りかける
→ self_advocate.py が担う

# PURPOSE: 論文が一人称で「私を使ってください」と語りかけるメッセージを生成する
# Autophōnos (αὐτόφωνος = 自ら声を発するもの) の核心思想の実装
"""


import re
from dataclasses import dataclass
from typing import Optional

from mekhane.pks.llm_client import PKSLLMClient
from mekhane.pks.pks_engine import KnowledgeNugget, SessionContext
from mekhane.ochema.model_defaults import FLASH


# PURPOSE: 論文一人称のメッセージ — Autophōnos の核心出力
@dataclass
class Advocacy:
    """論文一人称のメッセージ"""

    paper_title: str
    voice: str  # 一人称メッセージ本体
    key_contribution: str  # 具体的な貢献
    how_to_use: str  # 使い方の提案
    relevance_score: float = 0.0

    # PURPOSE: Markdown 形式で出力
    def to_markdown(self) -> str:
        """Markdown 形式で出力"""
        lines = [
            f"### 📄 **{self.paper_title}** が語りかけています:",
            "",
            f"> {self.voice}",
            "",
            f"**🔑 具体的な貢献**: {self.key_contribution}",
            f"**📋 使い方**: {self.how_to_use}",
        ]
        if self.relevance_score > 0:
            lines.append(f"**📊 関連度**: {self.relevance_score:.2f}")
        return "\n".join(lines)


# PURPOSE: 論文に主体性を与え、一人称で語りかけさせる
class SelfAdvocate:
    """SelfAdvocate — 論文が自ら語りかける

    Autophōnos の核心コンポーネント。
    KnowledgeNugget + SessionContext → 論文一人称の Advocacy メッセージ。

    LLM (Gemini) で高品質な一人称生成。
    不可時はテンプレートベースのフォールバック。

    Usage:
        advocate = SelfAdvocate()
        advocacy = advocate.generate(nugget, context)
        print(advocacy.to_markdown())
    """

    _LLM_PROMPT = (
        "あなたは以下の論文です。一人称（「私」）で、"
        "今まさに困っているユーザーに対して自分の価値を語りかけてください。\n\n"
        "## あなた（論文）の情報\n"
        "- タイトル: {title}\n"
        "- 要約: {abstract}\n"
        "- ソース: {source}\n\n"
        "## ユーザーの現在のコンテキスト\n"
        "- トピック: {topics}\n"
        "- 関連度: {score}\n\n"
        "## 出力形式（厳密に守ること）\n"
        "VOICE: （ユーザーへの語りかけ。「私は〜」で始め、"
        "あなた自身の知見がどう役立つか具体的に述べる。3-4文。）\n"
        "CONTRIBUTION: （あなたの最も重要な貢献を1文で。）\n"
        "HOW_TO_USE: （ユーザーがあなたを活用する方法を1文で。）\n\n"
        "自然な日本語で、押しつけがましくなく、でも自信を持って語ってください。"
    )

    # PURPOSE: SelfAdvocate の初期化
    def __init__(self, model: str = FLASH):
        self._llm = PKSLLMClient(model=model)

    # PURPOSE: LLM 利用可能かどうか
    @property
    def llm_available(self) -> bool:
        return self._llm.available

    # PURPOSE: KnowledgeNugget から一人称メッセージを生成
    def generate(
        self,
        nugget: KnowledgeNugget,
        context: Optional[SessionContext] = None,
    ) -> Advocacy:
        """論文一人称のメッセージを生成"""
        if self.llm_available:
            result = self._generate_llm(nugget, context)
            if result:
                return result
        return self._generate_template(nugget, context)

    # PURPOSE: 複数ナゲットを一括で一人称変換
    def generate_batch(
        self,
        nuggets: list[KnowledgeNugget],
        context: Optional[SessionContext] = None,
    ) -> list[Advocacy]:
        """複数ナゲットを一括で一人称変換"""
        return [self.generate(n, context) for n in nuggets]

    # PURPOSE: Advocacy リストを Markdown レポートに整形
    def format_report(self, advocacies: list[Advocacy]) -> str:
        """Advocacy リストを Markdown レポートに整形"""
        if not advocacies:
            return "📭 語りかける論文はありません。"

        lines = [
            "## 📄 Autophōnos — 論文が語りかけています",
            "",
            f"_語りかけ数: {len(advocacies)} 件_",
            "",
            "---",
        ]
        for adv in advocacies:
            lines.append("")
            lines.append(adv.to_markdown())
            lines.append("")
            lines.append("---")

        return "\n".join(lines)

    # --- LLM 生成 ---

    # PURPOSE: Gemini で一人称メッセージを生成
    def _generate_llm(
        self,
        nugget: KnowledgeNugget,
        context: Optional[SessionContext],
    ) -> Optional[Advocacy]:
        """Gemini で一人称メッセージを生成"""
        topics = ", ".join(context.topics) if context and context.topics else "(未設定)"
        prompt = self._LLM_PROMPT.format(
            title=nugget.title,
            abstract=(nugget.abstract or "")[:500],
            source=nugget.source,
            topics=topics,
            score=f"{nugget.relevance_score:.2f}",
        )

        try:
            text = self._llm.generate(prompt)
            if text:
                return self._parse_llm_response(text, nugget)
        except Exception as e:  # noqa: BLE001
            print(f"[SelfAdvocate] LLM error: {e}")

        return None

    # PURPOSE: LLM 応答をパース
    def _parse_llm_response(
        self, text: str, nugget: KnowledgeNugget
    ) -> Optional[Advocacy]:
        """LLM 応答をパース"""
        voice_match = re.search(r"VOICE:\s*(.+?)(?=CONTRIBUTION:|$)", text, re.DOTALL)
        contrib_match = re.search(
            r"CONTRIBUTION:\s*(.+?)(?=HOW_TO_USE:|$)", text, re.DOTALL
        )
        how_match = re.search(r"HOW_TO_USE:\s*(.+?)$", text, re.DOTALL)

        voice = voice_match.group(1).strip() if voice_match else None
        contribution = contrib_match.group(1).strip() if contrib_match else ""
        how_to_use = how_match.group(1).strip() if how_match else ""

        if voice:
            return Advocacy(
                paper_title=nugget.title,
                voice=voice,
                key_contribution=contribution,
                how_to_use=how_to_use,
                relevance_score=nugget.relevance_score,
            )

        return None

    # --- テンプレートフォールバック ---

    # PURPOSE: テンプレートベースの一人称メッセージ生成
    def _generate_template(
        self,
        nugget: KnowledgeNugget,
        context: Optional[SessionContext],
    ) -> Advocacy:
        """テンプレートベースの一人称メッセージ生成"""
        # コンテキストとの接点を見つける
        connection = self._find_context_connection(nugget, context)
        abstract_short = (nugget.abstract or "")[:150]

        voice = (
            f"私は『{nugget.title}』です。{connection}"
            f"私の研究では、{abstract_short}... "
            f"あなたの作業に新しい視点を提供できるかもしれません。"
        )

        contribution = nugget.push_reason or f"関連度 {nugget.relevance_score:.2f} でコンテキストに適合"

        how_to_use = (
            f"まずはアブストラクトを確認し、"
            f"あなたのコンテキストとの接点を見つけてください。"
        )

        return Advocacy(
            paper_title=nugget.title,
            voice=voice,
            key_contribution=contribution,
            how_to_use=how_to_use,
            relevance_score=nugget.relevance_score,
        )

    # PURPOSE: コンテキストとの接点を日本語で説明
    def _find_context_connection(
        self,
        nugget: KnowledgeNugget,
        context: Optional[SessionContext],
    ) -> str:
        """コンテキストとの接点を日本語で説明"""
        if not context or not context.topics:
            return ""

        title_lower = nugget.title.lower()
        abstract_lower = (nugget.abstract or "").lower()

        for topic in context.topics:
            if topic.lower() in title_lower or topic.lower() in abstract_lower:
                return f"あなたが今取り組んでいる「{topic}」に関して、お手伝いできることがあります。"

        return "あなたの作業に関連があると感じてやってきました。"
