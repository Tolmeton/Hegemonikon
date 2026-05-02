# PROOF: [L2/インフラ] <- hermeneus/src/workflow_defaults.py
"""
ワークフローデフォルト修飾子 — 動詞ごとの座標プロファイル定数

translator.py から分離した軽量モジュール。
ccl_ast.py 等の重いインポートを避け、forgetfulness_score.py から
安全に参照可能にする。

Origin: translator.py WORKFLOW_DEFAULT_MODIFIERS (v4.1)
v5.0: K₄柱モデル (36動詞) 対応 + X-series w≥0.5 演繹的クロスシリーズ
v5.1: 閾値を w≥0.4 に引き下げ (2026-03-26)
  設計根拠: taxis.md の張力傾向 w に基づく閾値ルール
    族座標 C₁ と他座標 C₂ の結合 w(C₁, C₂) ≥ 0.4 → C₂ を割当
    極性: taxis.md の「自然な組合せ」に従い族座標の極性が決定
  3閾値比較: w≥0.5 Gini=0.125 / w≥0.4 Gini=0.271 / w≥0.3 Gini=0.333(逆天井)
  結果: Pr が 100% カバー (全36動詞) = FEP の precision weighting は全認知に関与
  族別座標数: Tel=4, Met=3, Kri=6(全座標), Dia=2, Ore=3, Chr=2
"""

from typing import Dict

# WFごとのデフォルト修飾子 (v5.1 — X-series w≥0.4 演繹)
# ユーザーが明示した修飾子がデフォルトを上書きする
# 優先順位: 明示修飾子 > プリセット [preset] > デフォルト
#
# クロスシリーズ座標の導出ルール (w≥0.4):
#   Tel(Va): Va×Fu=0.4→Fu, Va×Pr=0.4→Pr, Va×Vl=0.4→Vl  (4座標)
#   Met(Fu): Fu×Pr=0.6→Pr, Fu×Va=0.4→Va                  (3座標)
#   Kri(Pr): Pr×Fu=0.6, Pr×Sc=0.5, Pr×Vl=0.5,
#            Pr×Va=0.4, Pr×Te=0.4                         (6座標=全座標)
#   Dia(Sc): Sc×Pr=0.5→Pr                                 (2座標)
#   Ore(Vl): Vl×Pr=0.5→Pr, Vl×Va=0.4→Va                  (3座標)
#   Chr(Te): Te×Pr=0.4→Pr                                 (2座標)
#
#   極性割当 (taxis.md 自然な組合せ):
#     Va:E→Fu:Explore, Pr:U, Vl:-  /  Va:P→Fu:Exploit, Pr:C, Vl:+
#     Fu:Explore→Va:E, Pr:U        /  Fu:Exploit→Va:P, Pr:C
#     Pr:C→Fu:Exploit, Sc:Ma, Vl:+, Va:P, Te:Past
#     Pr:U→Fu:Explore, Sc:Mi, Vl:-, Va:E, Te:Future
#     Sc:Mi→Pr:C  /  Sc:Ma→Pr:U
#     Vl:+→Pr:C, Va:P  /  Vl:-→Pr:U, Va:E
#     Te:Past→Pr:C  /  Te:Future→Pr:U
WORKFLOW_DEFAULT_MODIFIERS: Dict[str, Dict[str, str]] = {
    # === Telos 族 (族座標: Va + クロス: Fu[0.4], Pr[0.4], Vl[0.4]) ===
    "noe": {"Va": "E", "Fu": "Explore", "Pr": "U", "Vl": "-"},  # I×E — 認識
    "bou": {"Va": "P", "Fu": "Exploit", "Pr": "C", "Vl": "+"},  # I×P — 意志
    "zet": {"Va": "E", "Fu": "Explore", "Pr": "U", "Vl": "-"},  # A×E — 探求
    "ene": {"Va": "P", "Fu": "Exploit", "Pr": "C", "Vl": "+"},  # A×P — 実行
    "the": {"Va": "E", "Fu": "Explore", "Pr": "U", "Vl": "-"},  # S×E — 観照
    "ant": {"Va": "P", "Fu": "Exploit", "Pr": "C", "Vl": "+"},  # S×P — 検知
    # === Methodos 族 (族座標: Fu + クロス: Pr[0.6], Va[0.4]) ===
    "ske": {"Fu": "Explore", "Pr": "U", "Va": "E"},             # I×Explore — 発散
    "sag": {"Fu": "Exploit", "Pr": "C", "Va": "P"},             # I×Exploit — 収束
    "pei": {"Fu": "Explore", "Pr": "U", "Va": "E"},             # A×Explore — 実験
    "tek": {"Fu": "Exploit", "Pr": "C", "Va": "P"},             # A×Exploit — 適用
    "ere": {"Fu": "Explore", "Pr": "U", "Va": "E"},             # S×Explore — 探知
    "agn": {"Fu": "Exploit", "Pr": "C", "Va": "P"},             # S×Exploit — 参照
    # === Krisis 族 (族座標: Pr + クロス: 全座標 [Fu0.6,Sc0.5,Vl0.5,Va0.4,Te0.4]) ===
    "kat": {"Pr": "C", "Fu": "Exploit", "Sc": "Ma", "Vl": "+", "Va": "P", "Te": "Past"},    # I×C — 確定
    "epo": {"Pr": "U", "Fu": "Explore", "Sc": "Mi", "Vl": "-", "Va": "E", "Te": "Future"},  # I×U — 留保
    "pai": {"Pr": "C", "Fu": "Exploit", "Sc": "Ma", "Vl": "+", "Va": "P", "Te": "Past"},    # A×C — 決断
    "dok": {"Pr": "U", "Fu": "Explore", "Sc": "Mi", "Vl": "-", "Va": "E", "Te": "Future"},  # A×U — 打診
    "sap": {"Pr": "C", "Fu": "Exploit", "Sc": "Ma", "Vl": "+", "Va": "P", "Te": "Past"},    # S×C — 精読
    "ski": {"Pr": "U", "Fu": "Explore", "Sc": "Mi", "Vl": "-", "Va": "E", "Te": "Future"},  # S×U — 走査
    # === Diástasis 族 (族座標: Sc + クロス: Pr[0.5]) ===
    "lys": {"Sc": "Mi", "Pr": "C"},                             # I×Mi — 分析
    "ops": {"Sc": "Ma", "Pr": "U"},                             # I×Ma — 俯瞰
    "akr": {"Sc": "Mi", "Pr": "C"},                             # A×Mi — 精密操作
    "arc": {"Sc": "Ma", "Pr": "U"},                             # A×Ma — 全体展開
    "prs": {"Sc": "Mi", "Pr": "C"},                             # S×Mi — 注視
    "per": {"Sc": "Ma", "Pr": "U"},                             # S×Ma — 一覧
    # === Orexis 族 (族座標: Vl + クロス: Pr[0.5], Va[0.4]) ===
    "beb": {"Vl": "+", "Pr": "C", "Va": "P"},                   # I×+ — 強化
    "ele": {"Vl": "-", "Pr": "U", "Va": "E"},                   # I×- — 批判
    "kop": {"Vl": "+", "Pr": "C", "Va": "P"},                   # A×+ — 推進
    "dio": {"Vl": "-", "Pr": "U", "Va": "E"},                   # A×- — 是正
    "apo": {"Vl": "+", "Pr": "C", "Va": "P"},                   # S×+ — 傾聴
    "exe": {"Vl": "-", "Pr": "U", "Va": "E"},                   # S×- — 吟味
    # === Chronos 族 (族座標: Te + クロス: Pr[0.4]) ===
    "hyp": {"Te": "Past", "Pr": "C"},                            # I×Past — 想起
    "prm": {"Te": "Future", "Pr": "U"},                          # I×Future — 予見
    "ath": {"Te": "Past", "Pr": "C"},                            # A×Past — 省顧
    "par": {"Te": "Future", "Pr": "U"},                          # A×Future — 先制
    "his": {"Te": "Past", "Pr": "C"},                            # S×Past — 回顧
    "prg": {"Te": "Future", "Pr": "U"},                          # S×Future — 予感
}
