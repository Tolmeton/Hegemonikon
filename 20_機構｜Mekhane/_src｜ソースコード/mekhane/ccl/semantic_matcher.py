# PROOF: [L1/定理] <- mekhane/ccl/semantic_matcher.py CCL→CCLパーサーが必要→semantic_matcher が担う
"""
Semantic Macro Matcher

Uses vector embeddings to match Japanese natural language to CCL macros.
Integrates with Symplokē for semantic search.
"""

from typing import List, Optional
from dataclasses import dataclass
from .macro_registry import MacroRegistry, Macro, BUILTIN_MACROS

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np

    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: A matched macro with similarity score.
class MacroMatch:
    """A matched macro with similarity score."""

    macro: Macro
    score: float
    matched_term: str


# Japanese semantic mappings for macros
MACRO_DESCRIPTIONS_JP = {
    # === Original Macros ===
    "dig": [
        "深く考える",
        "掘り下げる",
        "分析する",
        "熟考する",
        "じっくり考える",
        "深掘りする",
        "検討する",
    ],
    "go": ["実行する", "やる", "進める", "行動する", "走らせる", "動かす", "開始する"],
    "osc": ["往復する", "振動する", "行き来する", "揺れる", "交互に考える", "反復する"],
    "fix": [
        "直す",
        "修正する",
        "改善する",
        "治す",
        "手直しする",
        "修復する",
        "フィックスする",
    ],
    "plan": [
        "計画する",
        "企画する",
        "立案する",
        "設計する",
        "プランを立てる",
        "構想する",
    ],
    "learn": ["学ぶ", "学習する", "覚える", "習得する", "理解する", "勉強する"],
    "nous": ["問う", "尋ねる", "自問する", "探求する", "問いかける", "深く問う"],
    # === Telos (O-Series) ===
    "o": ["目的", "なぜ", "ゴール", "最終目標", "何のために"],
    "noe": ["認識", "直観", "深く見る", "洞察", "理解する"],
    "bou": ["意志", "欲求", "望む", "望み", "本当に欲しいもの"],
    "zet": ["探求", "問い発見", "問う", "質問する", "疑問"],
    "ene": ["行為", "実行", "現実化", "具現化", "具現"],

    # === Methodos (S-Series) ===
    "s": ["方法", "戦略", "やり方", "アプローチ", "どうやって"],
    "ske": ["発散探索", "探索", "拡げる", "可能性を探る", "ブレインストーミング"],
    "sag": ["収束統合", "まとめる", "統合する", "集める", "ひとつにする"],
    "pei": ["実験検証", "試す", "実験する", "検証する", "テストする"],
    "tek": ["技法構築", "手法", "テクニック", "技術", "確立する"],

    # === Krisis (H-Series) ===
    "h": ["確信", "判断", "信頼", "自身", "どれくらい確か"],
    "kat": ["確定", "対象固定", "決める", "固定する", "確定的認識"],
    "epo": ["判断留保", "保留する", "決めないでおく", "ポーズ", "寝かせる"],
    "pai": ["決断", "資源投入", "選ぶ", "選択する", "踏み切る"],
    "dok": ["打診", "テスト", "小さく試す", "反応を見る", "探りを入れる"],

    # === Diástasis (P-Series) ===
    "p": ["空間", "場", "範囲", "どこで", "コンテキスト"],
    "lys": ["局所分析", "細かく見る", "部分", "分解する", "ブレイクダウン"],
    "ops": ["全体俯瞰", "鳥瞰", "全体を見る", "広く見る", "マクロ"],
    "akr": ["精密操作", "正確に", "正確さ", "厳密に", "精度"],
    "arc": ["全体展開", "アーキテクチャ", "一斉行動", "面的展開", "広範に"],

    # === Orexis (K-Series) ===
    "k": ["傾向", "価値", "良し悪し", "アライメント", "価値観"],
    "beb": ["信念肯定", "肯定する", "良い", "信じる", "強化する"],
    "ele": ["批判反証", "批判する", "疑う", "反証する", "問題を見つける"],
    "kop": ["推進前進", "進める", "推進する", "方向性を固める", "ドライブする"],
    "dio": ["是正修正", "正す", "軌道修正", "方向転換", "修正する"],

    # === Chronos (A-Series) ===
    "a": ["時間", "いつ", "タイミング", "過去未来", "時間軸"],
    "hyp": ["過去想起", "思い出す", "記憶", "過去", "振り返る"],
    "prm": ["未来予見", "予測する", "未来", "見通す", "予見"],
    "ath": ["教訓抽出", "教訓", "学ぶこと", "反省", "次に活かす"],
    "par": ["事前準備", "準備する", "仕掛ける", "備える", "布石を打つ"],
}


# PURPOSE: Matches natural language to macros using embeddings.
class SemanticMacroMatcher:
    """Matches natural language to macros using embeddings."""

    MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

    # PURPOSE: Initialize the semantic matcher.
    def __init__(self, registry: Optional[MacroRegistry] = None):
        """
        Initialize the semantic matcher.

        Args:
            registry: Macro registry to use
        """
        self.registry = registry or MacroRegistry()
        self.model = None
        self.embeddings = {}
        self.term_to_macro = {}

        if HAS_EMBEDDINGS:
            try:
                self.model = SentenceTransformer(self.MODEL_NAME)
                self._build_index()
            except Exception:  # noqa: BLE001
                pass  # TODO: Add proper error handling

    # PURPOSE: Build embedding index for all macro descriptions.
    def _build_index(self):
        """Build embedding index for all macro descriptions."""
        if not self.model:
            return

        all_terms = []
        for macro_name, terms in MACRO_DESCRIPTIONS_JP.items():
            for term in terms:
                all_terms.append(term)
                self.term_to_macro[term] = macro_name

        if all_terms:
            embeddings = self.model.encode(all_terms)
            for i, term in enumerate(all_terms):
                self.embeddings[term] = embeddings[i]

    # PURPOSE: Check if semantic matching is available.
    def is_available(self) -> bool:
        """Check if semantic matching is available."""
        return self.model is not None and len(self.embeddings) > 0

    # PURPOSE: Find macros that semantically match the query.
    def match(self, query: str, top_k: int = 3) -> List[MacroMatch]:
        """
        Find macros that semantically match the query.

        Args:
            query: Japanese natural language query
            top_k: Number of top matches to return

        Returns:
            List of MacroMatch sorted by score
        """
        if not self.is_available():
            return []

        # Encode query
        query_embedding = self.model.encode([query])[0]

        # Calculate similarities
        scores = []
        for term, embedding in self.embeddings.items():
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )
            macro_name = self.term_to_macro[term]
            macro = self.registry.get(macro_name) or BUILTIN_MACROS.get(macro_name)
            if macro:
                scores.append(
                    MacroMatch(macro=macro, score=float(similarity), matched_term=term)
                )

        # Sort by score, deduplicate by macro name
        scores.sort(key=lambda x: x.score, reverse=True)
        seen = set()
        results = []
        for match in scores:
            if match.macro.name not in seen:
                seen.add(match.macro.name)
                results.append(match)
                if len(results) >= top_k:
                    break

        return results

    # PURPOSE: Suggest the best macro for a query if confidence is high enough.
    def suggest(self, query: str, threshold: float = 0.6) -> Optional[Macro]:
        """
        Suggest the best macro for a query if confidence is high enough.

        Args:
            query: Japanese natural language query
            threshold: Minimum similarity score

        Returns:
            Best matching Macro or None
        """
        matches = self.match(query, top_k=1)
        if matches and matches[0].score >= threshold:
            return matches[0].macro
        return None
