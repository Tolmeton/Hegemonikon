# PROOF: [L2/インフラ] <- hermeneus/src/oblivion_lut.py Lēthē 忘却スコア LUT
"""
Oblivion Score φ — Static Look-Up Table

各 CCL 動詞の忘却確率 φ(verb) ∈ [0.0, 1.0] を定義する。
    0.0 = 絶対保持 (この推論ステップは決して忘却されない)
    1.0 = 最大忘却 (このステップは容易に省略される)

設計原理:
    ∇Φ ≠ 0 — 忘却勾配は一様ではない。
    核心的認識 (Telos/noe) は低忘却、手続的操作 (Chronos/hyp) は高忘却。
    これは LLM の Think Anywhere 挙動の実測にも合致する:
    推論の「位置」より「必然性」が推論の保持/省略を決定する。

参照:
    - kat_TA_Oblivion_Isomorphism_v2_2026-04-03.md (核心命題)
    - Lethe_PhaseC_Design_Specification.md (設計仕様書)
    - forgetfulness_score.py (0-cell 忘却スコア S(e))

⚠️ 初期値は仮構成。M3 の BBH 実験で較正予定。
    較正前の値は [TAINT: 理論的推定] である。
"""

from typing import Dict, List, Optional, Any


# =============================================================================
# φ LUT: 動詞 → 忘却確率
# =============================================================================

# PURPOSE: 各動詞の忘却確率 φ を定義する静的テーブル
# 設計根拠: 族 (Series) ごとの認知的重要度に基づく段階配分
#   Telos (目的): 推論の核心 → 低忘却
#   Methodos (方法): 手法の選択 → 中忘却
#   Krisis (判断): 判断プロセス → 中忘却
#   Diástasis (分析): 構造的分析 → 中高忘却
#   Orexis (動機): 動機づけ → 中忘却
#   Chronos (時間): 時間的操作 → 高忘却
PHI_LUT: Dict[str, float] = {
    # ── Telos 族 (認識の核心 — 低忘却) ──
    "noe": 0.15,   # Noēsis: 認識 (推論の根幹)
    "bou": 0.20,   # Boulēsis: 計画 (意図の形成)
    "zet": 0.40,   # Zētēsis: 探索 (情報収集)
    "ene": 0.25,   # Energeia: 実行 (行為の遂行)
    # Telos S極
    "the": 0.20,   # Theōria: 観照
    "ant": 0.25,   # Antilepsis: 掌握

    # ── Methodos 族 (手法 — 中忘却) ──
    "ske": 0.35,   # Skepsis: 懐疑
    "sag": 0.30,   # Synagōgē: 収集
    "pei": 0.50,   # Peira: 試行 (失敗許容)
    "tek": 0.25,   # Tekhnē: 技術 (確立された手法)
    # Methodos S極
    "ere": 0.35,   # Ereuna: 探究
    "agn": 0.30,   # Anagnōsis: 精読

    # ── Krisis 族 (判断 — 中忘却) ──
    "kat": 0.20,   # Katalēpsis: 確信
    "epo": 0.45,   # Epochē: 判断保留
    "pai": 0.55,   # Paideia: 教育的展開
    "dok": 0.40,   # Dokimasia: 試問
    # Krisis S極
    "sap": 0.25,   # Saphēneia: 精明
    "ski": 0.50,   # Skiagraphia: 素描

    # ── Diástasis 族 (分析 — 中高忘却) ──
    "lys": 0.30,   # Analysis: 分解
    "ops": 0.50,   # Synopsis: 俯瞰 (概観で十分なら省略可)
    "akr": 0.25,   # Akribeia: 精密 (精度が必要)
    "arc": 0.35,   # Architektonikē: 設計

    # ── Orexis 族 (動機 — 中忘却) ──
    "beb": 0.20,   # Bebaiōsis: 確認 (検証は省略困難)
    "ele": 0.35,   # Elenchos: 論駁
    "kop": 0.60,   # Prokopē: 進捗 (進捗報告は省略可能)
    "dio": 0.45,   # Diorthōsis: 矯正

    # ── Chronos 族 (時間 — 高忘却) ──
    "hyp": 0.55,   # Hypomnēsis: 想起 (文脈依存性高)
    "prm": 0.50,   # Promētheia: 予見
    "ath": 0.30,   # Anatheōrēsis: 再考 (反省は保持)
    "par": 0.45,   # Proparaskeuē: 準備

    # ── Meta 動詞 (最低忘却) ──
    "boot": 0.05,  # ブート (絶対保持)
    "bye": 0.10,   # 終了 (ほぼ保持)
    "u": 0.10,     # 主観引出 (保持)
    "ax": 0.05,    # Peras の Peras (絶対保持)
}

# デフォルト φ (LUT に存在しない動詞用)
PHI_DEFAULT: float = 0.50


# =============================================================================
# API
# =============================================================================

# PURPOSE: 動詞 ID から忘却スコア φ を取得する
def get_phi(verb_id: str) -> float:
    """動詞 ID から忘却スコア φ を取得する。

    Args:
        verb_id: 動詞 ID (e.g., "noe", "bou", "hyp")

    Returns:
        φ ∈ [0.0, 1.0]。LUT に存在しない場合は PHI_DEFAULT を返す。
    """
    return PHI_LUT.get(verb_id, PHI_DEFAULT)


# PURPOSE: 動詞のステップが忘却閾値を超えるか判定する
def should_skip(verb_id: str, theta: float) -> bool:
    """動詞のステップが忘却閾値 θ を超えるか判定する。

    φ(verb) > θ ならば True (このステップは忘却される)。
    φ(verb) ≤ θ ならば False (このステップは保持される)。

    Args:
        verb_id: 動詞 ID
        theta: 忘却閾値 θ ∈ [0.0, 1.0]

    Returns:
        True if φ > θ (忘却), False if φ ≤ θ (保持)
    """
    return get_phi(verb_id) > theta


# PURPOSE: Sequence の steps リストを φ でフィルタリング・再配置する
def filter_steps_by_phi(
    steps: List[Any],
    theta: float,
    extract_verb_id: Optional[Any] = None,
) -> List[Any]:
    """Sequence の steps リストを φ でフィルタリングする。

    1-cell 忘却: φ > θ のステップをスキップし、
    φ ≤ θ のステップのみ残す。

    Args:
        steps: AST ノードのリスト
        theta: 忘却閾値 θ
        extract_verb_id: AST ノードから verb_id を抽出する関数
            (None の場合はデフォルト抽出を使用)

    Returns:
        φ ≤ θ のステップのみ含むリスト
    """
    if extract_verb_id is None:
        extract_verb_id = _default_extract_verb_id

    retained = []
    for step in steps:
        verb_id = extract_verb_id(step)
        if verb_id is None or not should_skip(verb_id, theta):
            retained.append(step)

    return retained


# PURPOSE: AST ノードから verb_id を抽出するデフォルト実装
def _default_extract_verb_id(node: Any) -> Optional[str]:
    """AST ノードから verb_id を抽出する。

    Workflow ノード → id を返す。
    その他 → None (フィルタリングをスキップ)。
    """
    # 循環 import 回避: 型名で判定
    if hasattr(node, 'id') and hasattr(node, 'operators'):
        # Workflow ノード
        return node.id
    return None


# PURPOSE: φ のカバレッジを検証する (テスト用)
def verify_lut_coverage(verb_set: set) -> Dict[str, str]:
    """φ LUT のカバレッジを検証する。

    Args:
        verb_set: パーサーが認識する動詞 ID の集合

    Returns:
        {"missing": [...], "extra": [...]} の辞書
    """
    lut_verbs = set(PHI_LUT.keys())
    return {
        "missing": sorted(verb_set - lut_verbs),
        "extra": sorted(lut_verbs - verb_set),
    }
