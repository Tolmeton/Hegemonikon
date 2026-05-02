# PROOF: [L2/インフラ] <- hermeneus/src/modifier_presets.py
"""
Modifier Presets — 修飾子の名前付きパッケージ定義 (v4.1)

CCL 構文の修飾子において、複数の座標パラメーターをひとまとめにした
「プリセット」を管理するモジュール。
"""

from typing import Dict

# 名前と座標の対応表
# S(e) 実験 (2026-03) の知見: Te(65%), Fu(57%) が最も欠落しやすい座標
MODIFIER_PRESETS: Dict[str, Dict[str, str]] = {
    # 分析・志向系
    "critical": {"Vl": "-", "Pr": "C"},
    "creative": {"Fu": "Explore", "Pr": "U"},
    "practical": {"Va": "P", "Fu": "Exploit"},
    "cautious": {"Pr": "U", "Vl": "-"},
    "decisive": {"Pr": "C", "Fu": "Exploit"},
    "innovative": {"Fu": "Explore", "Vl": "+"},
    
    # 空間・時間系
    "deep": {"Va": "E", "Sc": "Mi", "Te": "Past"},       # Te 追加 (S(e) 知見)
    "overview": {"Va": "E", "Sc": "Ma"},
    "retrospect": {"Te": "Past", "Sc": "Ma"},
    "foresight": {"Te": "Future", "Fu": "Explore"},

    # S(e) 駆動プリセット — Te/Fu 欠落の体系的補完
    "thorough": {"Te": "Past", "Pr": "U", "Fu": "Explore"},  # Te+Fu 2大欠落を同時カバー
    "action": {"Va": "P", "Fu": "Exploit", "Te": "Future"},  # 実行指向 + Te を未来側でカバー
    "balanced": {"Fu": "Explore", "Pr": "U", "Te": "Past", "Sc": "Mi"},  # 4座標同時活性化
}

def get_preset(name: str) -> Dict[str, str] | None:
    """指定された名前のプリセットを取得する"""
    return MODIFIER_PRESETS.get(name.lower())

def is_valid_preset(name: str) -> bool:
    """有効なプリセット名かチェックする"""
    return name.lower() in MODIFIER_PRESETS
