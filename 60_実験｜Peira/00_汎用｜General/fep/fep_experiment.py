# PROOF: [L3/ユーティリティ] <- mekhane/scripts/fep_experiment.py O4→運用スクリプトが必要→fep_experiment が担う
#!/usr/bin/env python3
"""
FEP Interactive Experiment: Explore pymdp behavior in real-time.

Allows manual observation input and shows how beliefs evolve.

Usage:
    python scripts/fep_experiment.py
"""

import sys

sys.path.insert(0, ".")

from mekhane.fep import HegemonikónFEPAgent
from mekhane.fep.state_spaces import (
    OBSERVATION_MODALITIES,
)
import numpy as np


# PURPOSE: Print available observations.
def print_observation_menu():
    """Print available observations."""
    print("\n📋 利用可能な観測:")
    idx = 0
    for modality, values in OBSERVATION_MODALITIES.items():
        print(f"   [{modality}]")
        for val in values:
            print(f"      {idx}: {val}")
            idx += 1
    print(f"   [control]")
    print(f"      r: リセット")
    print(f"      h: 履歴表示")
    print(f"      q: 終了")


# PURPOSE: Print current state beautifully.
def print_state(result: dict):
    """Print current state beautifully."""
    print(f"\n🧠 現在の信念状態:")
    print(f"   MAP: {result['map_state_names']}")
    print(f"   エントロピー: {result['entropy']:.3f}")

    # Visual entropy bar
    max_entropy = np.log(8)  # 8 states
    normalized = result["entropy"] / max_entropy
    bar_len = 20
    filled = int(normalized * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"   不確実性: [{bar}] {normalized:.1%}")

    # Epochē check
    if normalized > 0.7:
        print(f"   ⚠️  Epochē 推奨: 判断を保留すべき")
    elif normalized < 0.3:
        print(f"   ✅ 高確信: 行動推奨")


# PURPOSE: Print policy selection.
def print_policy(q_pi, neg_efe):
    """Print policy selection."""
    print(f"\n🎯 政策選択 (O2 Boulēsis):")
    actions = ["observe (O1 継続)", "act (O4 実行)"]
    for i, (prob, efe) in enumerate(zip(q_pi, neg_efe)):
        bar = "█" * int(prob * 15)
        efe_indicator = "⬆" if -efe > 2.1 else "⬇"
        print(f"   {actions[i]:20s}: {prob:.1%} {bar}")
        print(f"      EFE: {-efe:.3f} {efe_indicator}")

    recommended = "observe" if q_pi[0] > q_pi[1] else "act"
    print(f"\n   ➤ 推奨行動: {recommended}")


# PURPOSE: Main interactive loop.
def interactive_loop():
    """Main interactive loop."""
    agent = HegemonikónFEPAgent(use_defaults=True)
    step_count = 0

    print("=" * 60)
    print("  Hegemonikón FEP Interactive Experiment")
    print("=" * 60)
    print("\nストア派認知モデルをリアルタイムで探索します。")
    print("観測を入力すると、信念が更新されます。")

    print_observation_menu()

    # Show initial state
    initial_beliefs = agent.beliefs
    print(f"\n🔹 初期状態 (Epistemic Humility):")
    print(
        f"   エントロピー: {-np.sum(initial_beliefs * np.log(initial_beliefs + 1e-10)):.3f}"
    )

    while True:
        try:
            user_input = input("\n観測を入力 (0-7, r, h, q): ").strip().lower()

            if user_input == "q":
                print("\n👋 実験終了")
                break

            if user_input == "r":
                agent = HegemonikónFEPAgent(use_defaults=True)
                step_count = 0
                print("\n🔄 リセット完了")
                continue

            if user_input == "h":
                history = agent.get_history()
                print(f"\n📜 履歴 ({len(history)} 件):")
                for i, entry in enumerate(history[-5:]):  # Last 5
                    print(f"   {i+1}. {entry['type']}")
                continue

            try:
                obs_idx = int(user_input)
                if obs_idx < 0 or obs_idx > 7:
                    print("❌ 0-7 の範囲で入力してください")
                    continue
            except ValueError:
                print("❌ 数値または r/h/q を入力してください")
                continue

            # Process observation
            step_count += 1
            print(f"\n{'─' * 60}")
            print(f"ステップ {step_count}: 観測 {obs_idx}")

            # O1 Noēsis
            result = agent.infer_states(observation=obs_idx)
            print_state(result)

            # O2 Boulēsis
            q_pi, neg_efe = agent.infer_policies()
            print_policy(q_pi, neg_efe)

        except KeyboardInterrupt:
            print("\n\n👋 中断されました")
            break
        except Exception as e:
            print(f"\n❌ エラー: {e}")
            import traceback

            traceback.print_exc()


# PURPOSE: Entry point.
def main():
    """Entry point."""
    try:
        interactive_loop()
        return 0
    except Exception as e:
        print(f"❌ 致命的エラー: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
