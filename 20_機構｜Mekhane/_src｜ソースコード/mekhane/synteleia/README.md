# Synteleia Cognitive Ensemble Layer

> **12法 (Nomoi) 3×4 テンソル積アーキテクチャ** — メタ認知と社会的認知を実装する認知アンサンブル層

## 概要

Synteleia は Hegemonikón の 12法 (Nomoi) を **3原理 × 4位相** の構造で実装する
メタ認知・社会的認知の実装層。

| 原理 | 位相 | エージェント |
|------|------|-------------|
| **S-I Tapeinophrosyne** (P1-P4) | 知覚推論 | N01Source, N02Uncertainty, N03Confidence, N04Safety |
| **S-II Autonomia** (P1-P4) | 能動推論 | N05Probe, N06Anomaly, N07Voice, N08Tool |
| **S-III Akribeia** (P1-P4) | 精度最適化 | N09Primary, N10Taint, N11Actionable, N12Execution |

## ディレクトリ構造

```
synteleia/
├── __init__.py          # メインパッケージ
├── base.py              # 基底クラス
├── orchestrator.py      # 3×4 オーケストレーター
├── pattern_loader.py    # YAML パターンローダー
├── README.md            # このファイル
│
├── nomoi/               # 12法エージェント (推奨)
│   ├── __init__.py      # S1/S2/S3 + P1-P4 グループ
│   ├── n01_source.py    # N-01 実体を読め
│   ├── ...              # N-02 〜 N-11
│   ├── n12_execution.py # N-12 正確に実行せよ
│   └── patterns.yaml    # 統合パターン定義
│
├── poiesis/             # [非推奨] 旧生成層 → nomoi を使用
│   └── ...
│
└── kritai/              # [非推奨] 旧審査層 → nomoi を使用
    └── ...
```

## 使い方

```python
from mekhane.synteleia import SynteleiaOrchestrator, AuditTarget, AuditTargetType

# ターゲット作成
target = AuditTarget(
    content="監査対象のテキスト",
    target_type=AuditTargetType.CODE
)

# 内積モード (デフォルト: 12法全エージェント)
orchestrator = SynteleiaOrchestrator()
result = orchestrator.audit(target)

# 深度別
l0 = SynteleiaOrchestrator.with_depth(depth=0)  # N06Anomaly のみ
l3 = SynteleiaOrchestrator.with_depth(depth=3)  # 外積 + SemanticAgent

print(orchestrator.format_report(result))
```

## CCL 構文

| 構文 | 意味 |
|------|------|
| `@syn·` | 内積: 12法を統合実行 |
| `@syn×` | 外積: 原理内 P1×P2-P4 交差検証 |

## 参照

- [設計文書](synteleia_design.md)
- [SKILL 定義](../../../10_知性｜Nous/02_手順｜Procedures/C_技能｜Skills/34_統合｜Synteleia/SKILL.md)
