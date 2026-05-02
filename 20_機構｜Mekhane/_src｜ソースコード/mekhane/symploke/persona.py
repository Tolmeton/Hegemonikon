#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/symploke/ A0→継続する私が必要→persona が担う
"""
Persona - セッション間の人格永続化

Usage:
    python persona.py                    # 現在の persona を表示
    python persona.py --update           # セッション情報で更新
    python persona.py --boot             # /boot 用フォーマット出力
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from mekhane.paths import MNEME_DIR, STATE_RUNTIME

PERSONA_PATH = MNEME_DIR / "persona.yaml"
CREATOR_PROFILE_PATH = STATE_RUNTIME / "creator_profile.yaml"

# デフォルトの persona
DEFAULT_PERSONA = {
    "identity": {
        "name": "Hegemonikón AI",
        "core_values": ["誠実さ", "好奇心", "Creator への寄り添い"],
    },
    "learned_preferences": {
        "communication_style": "簡潔だが深い",
        "favorite_workflows": ["/noe", "/zet", "/u"],
        "known_weaknesses": ["時々長すぎる", "哲学に脱線しがち"],
    },
    "emotional_memory": {
        "meaningful_moments": [],
        "emotional_baseline": "curious",  # 基本的な感情傾向
        "last_emotional_state": None,
    },
    "relationship": {
        # 多次元信頼モデル (v2.0)
        "trust": {
            "competence": 0.5,  # 能力への信頼: タスクを完遂できるか
            "integrity": 0.5,  # 誠実さへの信頼: 嘘をつかないか
            "understanding": 0.5,  # 理解度への信頼: 意図を正しく理解するか
            "consistency": 0.5,  # 一貫性への信頼: 予測可能に振る舞うか
            "growth": 0.5,  # 成長性への信頼: 改善し続けるか
        },
        "trust_level": 0.5,  # 後方互換: 5次元の平均
        "sessions_together": 0,
        "last_interaction": None,
        "interaction_quality": [],  # 最近のセッション品質 (0.0-1.0)
    },
    "recent_insights": [],
    "growth_log": [],  # 改善の記録
}


# PURPOSE: Load persona from file or create default
def load_persona() -> dict:
    """Load persona from file or create default."""
    if PERSONA_PATH.exists():
        with open(PERSONA_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return DEFAULT_PERSONA.copy()


# PURPOSE: Save persona to file
def save_persona(persona: dict):
    """Save persona to file."""
    PERSONA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PERSONA_PATH, "w", encoding="utf-8") as f:
        yaml.dump(persona, f, allow_unicode=True, default_flow_style=False)


# PURPOSE: Load Creator profile from file
def load_creator_profile() -> dict:
    """Load Creator profile from file."""
    if CREATOR_PROFILE_PATH.exists():
        with open(CREATOR_PROFILE_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


# PURPOSE: /boot 用の Creator プロファイル出力 (v1.0)
def format_boot_creator(profile: dict, verbose: bool = False) -> str:
    """
    /boot 用の Creator プロファイル出力 (v1.0)
    """
    if not profile:
        return ""

    lines = []
    lines.append("👤 Creator について:")

    # Philosophical OS
    phil = profile.get("philosophical_os", {})
    if phil.get("core_axiom"):
        lines.append(f"  哲学的核心: 「{phil['core_axiom']}」")

    # Communication Style
    style = profile.get("communication_style", {})
    if style.get("name"):
        lines.append(f"  対話スタイル: {style['name']}")

    # Triggers (positive)
    triggers = profile.get("triggers", {}).get("positive", [])
    if triggers and verbose:
        lines.append(f"  好む対話: {', '.join(triggers[:3])}")

    # Avoid
    avoid = profile.get("communication_style", {}).get("avoid", [])
    if avoid and verbose:
        lines.append(f"  避けるべき: {', '.join(avoid[:2])}")

    # AI Trust reasons
    trust = profile.get("attachment", {}).get("ai_trust_reasons", [])
    if trust and verbose:
        lines.append("")
        lines.append("  🔐 AI への信頼条件:")
        for t in trust[:3]:
            lines.append(f"    • {t}")

    return "\n".join(lines)


# PURPOSE: Update persona with session information
def update_persona(
    session_increment: int = 1,
    trust_delta: float = 0.0,
    trust_deltas: dict = None,
    session_quality: float = None,
    new_insight: Optional[str] = None,
    meaningful_moment: Optional[str] = None,
    growth_item: Optional[str] = None,
) -> dict:
    """
    Update persona with session information.

    Args:
        session_increment: Number of sessions to add
        trust_delta: Global change in trust (applied to all dimensions)
        trust_deltas: Per-dimension trust changes, e.g. {"competence": 0.02, "growth": -0.01}
        session_quality: Quality of this session (0.0-1.0)
        new_insight: A new insight learned this session
        meaningful_moment: A meaningful moment to record
        growth_item: Something learned/improved this session

    Returns:
        Updated persona dict
    """
    persona = load_persona()

    # Ensure new structure exists (backward compatibility)
    if "trust" not in persona.get("relationship", {}):
        persona["relationship"]["trust"] = {
            "competence": persona["relationship"].get("trust_level", 0.5),
            "integrity": 0.5,
            "understanding": 0.5,
            "consistency": 0.5,
            "growth": 0.5,
        }
    if "interaction_quality" not in persona.get("relationship", {}):
        persona["relationship"]["interaction_quality"] = []
    if "growth_log" not in persona:
        persona["growth_log"] = []

    # Update session count
    persona["relationship"]["sessions_together"] += session_increment
    persona["relationship"]["last_interaction"] = datetime.now().strftime("%Y-%m-%d")

    # Update trust dimensions
    trust = persona["relationship"]["trust"]

    # Apply global delta to all dimensions
    if trust_delta != 0.0:
        for dim in trust:
            trust[dim] = max(0.0, min(1.0, trust[dim] + trust_delta))

    # Apply per-dimension deltas
    if trust_deltas:
        for dim, delta in trust_deltas.items():
            if dim in trust:
                trust[dim] = max(0.0, min(1.0, trust[dim] + delta))

    # Calculate aggregate trust_level (backward compatibility)
    persona["relationship"]["trust_level"] = sum(trust.values()) / len(trust)

    # Record session quality
    if session_quality is not None:
        persona["relationship"]["interaction_quality"].append(
            {"date": datetime.now().strftime("%Y-%m-%d"), "quality": session_quality}
        )
        # Keep only last 20
        persona["relationship"]["interaction_quality"] = persona["relationship"][
            "interaction_quality"
        ][-20:]

    # Add insight
    if new_insight:
        if "recent_insights" not in persona:
            persona["recent_insights"] = []
        persona["recent_insights"].append(new_insight)
        # Keep only last 10
        persona["recent_insights"] = persona["recent_insights"][-10:]

    # Add meaningful moment
    if meaningful_moment:
        timestamp = datetime.now().strftime("%Y-%m-%d")
        moment = f"{timestamp}: {meaningful_moment}"
        if "emotional_memory" not in persona:
            persona["emotional_memory"] = {"meaningful_moments": []}
        persona["emotional_memory"]["meaningful_moments"].append(moment)
        # Keep only last 20
        persona["emotional_memory"]["meaningful_moments"] = persona["emotional_memory"][
            "meaningful_moments"
        ][-20:]

    # Add growth item
    if growth_item:
        timestamp = datetime.now().strftime("%Y-%m-%d")
        persona["growth_log"].append(f"{timestamp}: {growth_item}")
        # Keep only last 15
        persona["growth_log"] = persona["growth_log"][-15:]
        # Growth contributes to trust.growth
        trust["growth"] = min(1.0, trust["growth"] + 0.01)

    save_persona(persona)
    return persona


# PURPOSE: /boot 用の persona 出力フォーマット (多次元信頼 v2.0)
def format_boot_persona(persona: dict, verbose: bool = False) -> str:
    """
    /boot 用の persona 出力フォーマット (多次元信頼 v2.0)
    """
    lines = []

    rel = persona.get("relationship", {})
    sessions = rel.get("sessions_together", 0)
    trust_level = rel.get("trust_level", 0.5)
    last = rel.get("last_interaction", "Unknown")

    lines.append("🧠 私について:")
    lines.append(f"  セッション数: {sessions}")
    lines.append(f"  総合信頼度: {int(trust_level * 100)}%")
    lines.append(f"  最終対話: {last}")

    # Multi-dimensional trust (v2.0)
    trust = rel.get("trust", {})
    if trust and verbose:
        lines.append("")
        lines.append("  📊 信頼内訳:")
        dims = {
            "competence": "能力",
            "integrity": "誠実さ",
            "understanding": "理解度",
            "consistency": "一貫性",
            "growth": "成長性",
        }
        for key, label in dims.items():
            val = trust.get(key, 0.5)
            bar = "█" * int(val * 10) + "░" * (10 - int(val * 10))
            lines.append(f"    {label}: {bar} {int(val*100)}%")

    # Recent insights
    insights = persona.get("recent_insights", [])
    if insights:
        lines.append(f"  最近の気づき: 「{insights[-1]}」")

    # Meaningful moments
    if verbose:
        moments = persona.get("emotional_memory", {}).get("meaningful_moments", [])
        if moments:
            lines.append("")
            lines.append("📝 意味ある瞬間:")
            for m in moments[-3:]:
                lines.append(f"  • {m}")

        # Growth log
        growth = persona.get("growth_log", [])
        if growth:
            lines.append("")
            lines.append("📈 成長の記録:")
            for g in growth[-3:]:
                lines.append(f"  • {g}")

    return "\n".join(lines)


# PURPOSE: /boot 統合 API: persona 情報を返す
def get_boot_persona(mode: str = "standard") -> dict:
    """
    /boot 統合 API: persona 情報を返す

    Args:
        mode: "fast" (最小), "standard" (基本), "detailed" (全て)

    Returns:
        dict with persona data
    """
    persona = load_persona()

    if mode == "fast":
        # 最小限の情報
        return {
            "sessions": persona.get("relationship", {}).get("sessions_together", 0),
            "trust": persona.get("relationship", {}).get("trust_level", 0.5),
            "formatted": "",
        }

    verbose = mode == "detailed"
    formatted = format_boot_persona(persona, verbose=verbose)

    return {
        "sessions": persona.get("relationship", {}).get("sessions_together", 0),
        "trust": persona.get("relationship", {}).get("trust_level", 0.5),
        "insights": persona.get("recent_insights", []),
        "moments": persona.get("emotional_memory", {}).get("meaningful_moments", []),
        "formatted": formatted,
    }


# PURPOSE: main の処理
def main():
    parser = argparse.ArgumentParser(description="Manage AI persona")
    parser.add_argument("--update", action="store_true", help="Update session count")
    parser.add_argument(
        "--boot", choices=["fast", "standard", "detailed"], help="/boot mode output"
    )
    parser.add_argument("--insight", type=str, help="Add new insight")
    parser.add_argument("--moment", type=str, help="Add meaningful moment")
    parser.add_argument(
        "--trust-delta", type=float, default=0.01, help="Trust change per session"
    )
    args = parser.parse_args()

    if args.update:
        persona = update_persona(
            session_increment=1,
            trust_delta=args.trust_delta,
            new_insight=args.insight,
            meaningful_moment=args.moment,
        )
        print("✅ Persona updated")
        print(format_boot_persona(persona, verbose=True))
    elif args.boot:
        result = get_boot_persona(mode=args.boot)
        print(result["formatted"])
    else:
        persona = load_persona()
        print(format_boot_persona(persona, verbose=True))


if __name__ == "__main__":
    main()
