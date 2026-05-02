"""Phase 1 実験条件の設定
4条件: SGD / SAM / OA-SAM (λ<0) / 反転制御 (λ>0)
"""

# 共通パラメータ
COMMON = dict(
    lr=0.1,
    momentum=0.9,
    weight_decay=5e-4,
    epochs=200,
    batch_size=128,
)

# Phase 1 の4条件
PHASE1 = {
    'sgd': {
        **COMMON,
        'use_sam': False,
        'rho': 0.0,
        'lam_base': 0.0,
        'lam_sign': 0,
        'label': 'SGD (baseline)',
    },
    'sam': {
        **COMMON,
        'use_sam': True,
        'rho': 0.05,
        'lam_base': 0.0,
        'lam_sign': 0,
        'label': 'SAM (ρ=0.05)',
    },
    'oa_sam': {
        **COMMON,
        'use_sam': True,
        'rho': 0.05,
        'lam_base': 0.01,
        'lam_sign': -1,
        'label': 'OA-SAM (λ<0)',
    },
    'oa_sam_pos': {
        **COMMON,
        'use_sam': True,
        'rho': 0.05,
        'lam_base': 0.01,
        'lam_sign': 1,
        'label': '反転制御 (λ>0)',
    },
}
