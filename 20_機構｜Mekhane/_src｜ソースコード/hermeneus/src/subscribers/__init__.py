# PROOF: [L2/Phase2] <- hermeneus/src/subscribers/__init__.py
"""
Cognition Event Subscribers — 認知イベントに自律的に反応するモジュール群

Phase 2 of VISION: Living Cognition

各 subscriber は CognitionEventBus の特定の EventType を subscribe し、
条件が揃えば自律的に発火する。フックではなく、自律発火。

段階的ロールアウト:
    1. convergence_sub   — メトリクスログ (最低リスク)
    2. synteleia_sub     — L0 品質スキャン (読取専用)
    3. gnosis_sub        — 知識注入 (出力に影響)
    4. dendron_sub       — 参照検証
    5. periskope_sub     — 外部検索
    6. drift_guard_sub   — D1→D2 ドリフト検出時の自動検証
"""
# 遅延 import: パッケージ初期化時にネットワーク依存モジュールをロードしない
# 理由: periskope_sub 等が transitively API client を import し、
#        DNS 解決でハングするケースがある (2026-02-28)
_LAZY_IMPORTS = {
    "ConvergenceSubscriber": ".convergence_sub",
    "SynteleiaSubscriber": ".synteleia_sub",
    "GnosisSubscriber": ".gnosis_sub",
    "DendronSubscriber": ".dendron_sub",
    "PeriskopeSubscriber": ".periskope_sub",
    "DriftGuardSubscriber": ".drift_guard_sub",
    "create_verify_guard": ".drift_guard_sub",
    "KalonGateSubscriber": ".kalon_gate_sub",
    "ConeGuardSubscriber": ".cone_guard_sub",
    "EuporiaSubscriber": ".euporia_sub",
    "PlanPreprocessorSubscriber": ".plan_preprocessor",
    "PlanRecorderSubscriber": ".plan_recorder",
    "EventType": "hermeneus.src.event_bus",
}


def __getattr__(name):
    if name in _LAZY_IMPORTS:
        import importlib
        module_path = _LAZY_IMPORTS[name]
        if module_path.startswith("."):
            module = importlib.import_module(module_path, __package__)
        else:
            module = importlib.import_module(module_path)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "ConvergenceSubscriber",
    "SynteleiaSubscriber",
    "GnosisSubscriber",
    "DendronSubscriber",
    "PeriskopeSubscriber",
    "DriftGuardSubscriber",
    "create_verify_guard",
    "KalonGateSubscriber",
    "ConeGuardSubscriber",
    "EuporiaSubscriber",
    "PlanPreprocessorSubscriber",
    "PlanRecorderSubscriber",
]


def create_default_subscribers():
    """デフォルトの subscriber セットを生成

    段階 1-2 (convergence + synteleia) を有効、
    段階 3-5 (gnosis, dendron, periskope) は無効で返す。

    Returns:
        list of subscriber instances
    """
    from .convergence_sub import ConvergenceSubscriber
    from .synteleia_sub import SynteleiaSubscriber
    from .drift_guard_sub import DriftGuardSubscriber
    from .kalon_gate_sub import KalonGateSubscriber
    from .cone_guard_sub import ConeGuardSubscriber
    from .euporia_sub import EuporiaSubscriber
    from hermeneus.src.event_bus import EventType

    return [
        ConvergenceSubscriber(),     # 段階 1: ログのみ (最低リスク)
        SynteleiaSubscriber(),       # 段階 2: L0 スキャン (読取専用)
        DriftGuardSubscriber(),      # D1→D2: ドリフト検出時に verify_step 自動発動
        DriftGuardSubscriber(        # F4: エントロピー変化時の検証ガード
            name="entropy_guard",
            event_type=EventType.ENTROPY_CHANGE,
            score_key="entropy_delta",
        ),
        KalonGateSubscriber(),
        ConeGuardSubscriber(),
        EuporiaSubscriber(),         # 定理³: 行為可能性増大チェック
    ]


def create_all_subscribers():
    """全 subscriber を有効にして返す (フル機能モード)"""
    from .convergence_sub import ConvergenceSubscriber
    from .synteleia_sub import SynteleiaSubscriber
    from .gnosis_sub import GnosisSubscriber
    from .dendron_sub import DendronSubscriber
    from .periskope_sub import PeriskopeSubscriber
    from .drift_guard_sub import DriftGuardSubscriber
    from .kalon_gate_sub import KalonGateSubscriber
    from .cone_guard_sub import ConeGuardSubscriber
    from .euporia_sub import EuporiaSubscriber
    from .plan_preprocessor import PlanPreprocessorSubscriber
    from .plan_recorder import PlanRecorderSubscriber
    from .series import ALL_SERIES_SUBSCRIBERS
    from .taxis_sub import TaxisSubscriber
    from hermeneus.src.event_bus import EventType

    subs = [
        ConvergenceSubscriber(),
        SynteleiaSubscriber(),
        DriftGuardSubscriber(),
        DriftGuardSubscriber(
            name="entropy_guard",
            event_type=EventType.ENTROPY_CHANGE,
            score_key="entropy_delta",
        ),
        GnosisSubscriber(),
        DendronSubscriber(),
        PeriskopeSubscriber(),
        KalonGateSubscriber(),
        ConeGuardSubscriber(),
        EuporiaSubscriber(),         # 定理³: 行為可能性増大チェック
        PlanPreprocessorSubscriber(),   # 層0: 計画前処理
        PlanRecorderSubscriber(),       # 層6: 計画記録
    ]

    # /ax 用: 6 Series + Taxis (Phase 3: 動的 score で自律発火)
    for SubClass in ALL_SERIES_SUBSCRIBERS:
        subs.append(SubClass())
    subs.append(TaxisSubscriber())

    return subs
