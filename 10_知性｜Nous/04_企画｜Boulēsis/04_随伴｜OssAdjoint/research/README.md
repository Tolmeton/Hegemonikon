# research/ — OSS 深掘り調査ディレクトリ

> **目的**: adjoint_map.yaml の import_candidates を個別に深掘りし、
> 具体的な実装タスクに変換する。

## 構造

```
research/
├── README.md               # 本ファイル
├── openclaw/               # S 優先: 全体参照 (12 import candidates)
│   └── README.md           # → OPENCLAW_ANALYSIS.md へのリンク + 個別モジュール調査
├── dspy/                   # A 優先: MIPROv2, Signature (2 candidates)
│   └── research.md
├── gpt-researcher/         # A 優先: STORM, LangGraph (2 candidates)
│   └── research.md
├── proactive-knowledge/    # B 優先: マルチソース統合 (1 candidate)
│   └── research.md
└── crewai/                 # B 優先: 宣言的エージェント構成 (1 candidate)
    └── research.md
```

## 調査テンプレート

各 `research.md` は以下の構造に従う:

1. **対象 OSS**: 名前、repo、stars、ライセンス
2. **HGK 対象 PJ**: どの HGK PJ に影響するか
3. **import_candidates**: adjoint_map.yaml からの候補一覧
4. **ソースコード調査**: 主要ファイル・アーキテクチャの分析
5. **判定**: Import / Skip / Watch の三択 + 理由
6. **実装タスク**: Import 判定の場合、具体的なタスク定義

---

*Created: 2026-02-28*
