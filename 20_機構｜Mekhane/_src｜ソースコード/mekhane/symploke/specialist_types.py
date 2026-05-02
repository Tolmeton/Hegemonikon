#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/symploke/ 型定義の共有モジュール
"""
Symploke 専門家定義の型定義。

specialist_prompts.py と phase{0,2,3}_specialists.py 間の
循環依存を解消するために型定義を独立モジュールに抽出。
"""

from dataclasses import dataclass, field
from enum import Enum


# PURPOSE: tekhne-maker 5 Archetypes
class Archetype(Enum):
    """tekhne-maker 5 Archetypes"""

    PRECISION = "precision"  # 🎯 誤答率 < 1%
    SPEED = "speed"  # ⚡ レイテンシ < 2秒
    AUTONOMY = "autonomy"  # 🤖 人間介入 < 10%
    CREATIVE = "creative"  # 🎨 多様性 > 0.8
    SAFETY = "safety"  # 🛡 リスク = 0


# PURPOSE: 発見事項の重大度
class Severity(Enum):
    """発見事項の重大度"""

    CRITICAL = "critical"  # 即時修正必須
    HIGH = "high"  # 早期修正推奨
    MEDIUM = "medium"  # 改善推奨
    LOW = "low"  # 任意
    NONE = "none"  # 問題なし


# PURPOSE: 専門家定義
@dataclass
class SpecialistDefinition:
    """専門家定義"""

    id: str
    name: str
    category: str
    archetype: Archetype
    focus: str
    quality_standards: list[str] = field(default_factory=list)
    edge_cases: list[str] = field(default_factory=list)
    fallback: str = ""
