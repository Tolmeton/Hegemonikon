from __future__ import annotations
# noqa: AI-ALL
# PROOF: [L2/インフラ] <- mekhane/pks/
"""
PROOF: [L2/インフラ] このファイルは存在しなければならない

A0 (FEP) → 知識の能動的表面化には多様な対話フォーマットが必要
→ NotebookLM の Deep Dive / Brief / Critique / Debate の再現
→ narrator_formats.py が担う

# PURPOSE: PKSNarrator のフォーマット定義と LLM プロンプトテンプレート
"""


from enum import Enum
from dataclasses import dataclass


# PURPOSE: Narrative 出力フォーマットの列挙
class NarratorFormat(Enum):
    """Narrative 出力フォーマット — NotebookLM Audio Overview のテキスト版

    DEEP_DIVE: 複数ナゲットを横断する統合対話 (デフォルト)
    BRIEF: 要約のみの短縮版
    CRITIQUE: 批判的フィードバック特化
    DEBATE: 賛否両論を対等に展開
    """
    DEEP_DIVE = "deep_dive"
    BRIEF = "brief"
    CRITIQUE = "critique"
    DEBATE = "debate"

    # PURPOSE: narrator_formats の from str 処理を実行する
    @classmethod
    def from_str(cls, s: str) -> "NarratorFormat":
        """文字列からフォーマットを取得。不明な場合は DEEP_DIVE。"""
        mapping = {
            "deep_dive": cls.DEEP_DIVE,
            "brief": cls.BRIEF,
            "critique": cls.CRITIQUE,
            "debate": cls.DEBATE,
        }
        return mapping.get(s.lower().strip(), cls.DEEP_DIVE)


# PURPOSE: フォーマットごとの LLM プロンプト定義
@dataclass
class FormatSpec:
    """フォーマットの仕様"""
    format: NarratorFormat
    system_prompt: str
    speakers: list[str]  # 登場人物
    min_segments: int     # テンプレートフォールバック時の最小セグメント数
    max_segments: int     # LLM 生成時の最大セグメント数
    icon: str             # Markdown 出力用アイコン


# --- フォーマット仕様定義 ---

_DEEP_DIVE_PROMPT = (
    "以下の知識群について、Advocate（推薦者）と Critic（批判者）の深い対話を生成してください。\n"
    "複数の知識を横断的に結びつけ、全体像を浮かび上がらせてください。\n\n"
    "{context}\n\n"
    "出力形式 (厳密に守ってください):\n"
    "ADVOCATE: (知識群の統合的な価値と、互いの関連性を主張)\n"
    "CRITIC: (見落としている視点、結合の弱さ、前提条件を指摘)\n"
    "ADVOCATE: (批判を受け入れつつ、より深い洞察を提示)\n"
    "CRITIC: (最終的な留意点を簡潔に述べる)\n"
    "ADVOCATE: (結論として、この知識群が Creator に何をもたらすかを述べる)\n\n"
    "各発言は2-3文で。日本語で。"
)

_BRIEF_PROMPT = (
    "以下の知識について、30秒で読める要約を生成してください。\n\n"
    "{context}\n\n"
    "出力形式:\n"
    "NARRATOR: (核心を1-2文で)\n"
    "NARRATOR: (Creator にとっての意味を1文で)\n\n"
    "簡潔に。日本語で。"
)

_CRITIQUE_PROMPT = (
    "以下の知識について、建設的な批判的レビューを生成してください。\n"
    "限界、リスク、改善の余地に焦点を当ててください。\n\n"
    "{context}\n\n"
    "出力形式:\n"
    "CRITIC: (この知識の限界を具体的に指摘)\n"
    "CRITIC: (暗黙の前提条件を明示)\n"
    "CRITIC: (改善のための具体的な提案)\n"
    "ADVOCATE: (批判を受け入れつつ、それでも価値がある理由)\n\n"
    "各発言は1-2文で。日本語で。"
)

_DEBATE_PROMPT = (
    "以下の知識について、対等な立場の2人（PRO と CON）が議論してください。\n"
    "どちらも強い根拠を持ち、最終的に結論は出さないでください。\n\n"
    "{context}\n\n"
    "出力形式:\n"
    "PRO: (この知識を採用すべき根拠)\n"
    "CON: (採用すべきでない根拠)\n"
    "PRO: (反論 — CON の弱点を突く)\n"
    "CON: (再反論 — PRO の見落としを指摘)\n"
    "PRO: (最終主張 — ただし結論は出さない)\n"
    "CON: (最終反論 — ただし結論は出さない)\n\n"
    "各発言は2-3文で客観的に。日本語で。"
)


# --- 仕様レジストリ ---

FORMAT_SPECS: dict[NarratorFormat, FormatSpec] = {
    NarratorFormat.DEEP_DIVE: FormatSpec(
        format=NarratorFormat.DEEP_DIVE,
        system_prompt=_DEEP_DIVE_PROMPT,
        speakers=["Advocate", "Critic"],
        min_segments=3,
        max_segments=5,
        icon="🎙️",
    ),
    NarratorFormat.BRIEF: FormatSpec(
        format=NarratorFormat.BRIEF,
        system_prompt=_BRIEF_PROMPT,
        speakers=["Narrator"],
        min_segments=2,
        max_segments=2,
        icon="📝",
    ),
    NarratorFormat.CRITIQUE: FormatSpec(
        format=NarratorFormat.CRITIQUE,
        system_prompt=_CRITIQUE_PROMPT,
        speakers=["Critic", "Advocate"],
        min_segments=3,
        max_segments=4,
        icon="🔍",
    ),
    NarratorFormat.DEBATE: FormatSpec(
        format=NarratorFormat.DEBATE,
        system_prompt=_DEBATE_PROMPT,
        speakers=["Pro", "Con"],
        min_segments=4,
        max_segments=6,
        icon="⚖️",
    ),
}


# PURPOSE: format spec を取得する
def get_format_spec(fmt: NarratorFormat) -> FormatSpec:
    """フォーマット仕様を取得。未定義の場合は DEEP_DIVE。"""
    return FORMAT_SPECS.get(fmt, FORMAT_SPECS[NarratorFormat.DEEP_DIVE])


# PURPOSE: speaker pattern を取得する
def get_speaker_pattern(fmt: NarratorFormat) -> str:
    """フォーマットのスピーカーパターン (正規表現) を生成。"""
    spec = get_format_spec(fmt)
    speakers_upper = [s.upper() for s in spec.speakers]
    return "|".join(speakers_upper)
