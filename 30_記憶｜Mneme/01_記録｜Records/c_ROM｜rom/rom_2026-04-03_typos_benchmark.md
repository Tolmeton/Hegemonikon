---
rom_id: rom_2026-04-03_typos_benchmark
session_id: ae288504-0b5e-4786-828c-b816abc7bd87
created_at: 2026-04-03 23:09
rom_type: distilled
reliability: High
topics: [typos, benchmark, e1, e3, e4, compression, parse, dry, experiment]
exec_summary: |
  D4b (圧縮耐性のみ) を Typos Benchmark (4軸) にリフレーム。
  E4 (パース衝突) と E3 (DRY効率) は完了。E1 (圧縮耐性) は素材+スクリプト完了、実行待ち。
---

# Typos Empirical Benchmark — 4軸で殴る

> **[DECISION]** D4b (圧縮耐性のみの狭い実験) を **Typos Benchmark** (4軸) にリフレーム

typos v8 の強みは圧縮耐性だけではない。5層の強みを認識し、うち4つを定量的に検証する:

1. **意味論的デフォルト** (24ディレクティブ体系) → E2
2. **コンパイラビリティ** (@if/@mixin/@include) → E3
3. **構文衝突ゼロ** (`<:` / `:>` の衝突リスク分析) → E4
4. **圧縮耐性** (ICR 劣化曲線) → E1
5. **段階的複雑性** (Depth Level) → 未実験化

## E4: Parse Robustness ✅ 完了

> **[FACT]** typos v8 の構文衝突は **ゼロ**

| 形式 | 衝突件数 | 影響テストケース数 |
|:-----|:---------|:------------------|
| plain | 0 | 0 |
| md | 0 | 0 (コードブロック保護前提) |
| xml | **4** | **4** (Python `<`, f-string, JSX, 正規表現) |
| typos v7 | **2** | **2** (Python `@decorator`, YAML `@retry`) |
| **typos v8** | **0** | **0** |

xml は構造的に勝てない。`<input>` 内の `<` は XML として不正。CDATA やエスケープが必要だが可読性が破壊される。

成果物: `typos-benchmark/e4_parse_robustness/e4_results.json`

## E3: DRY Efficiency ✅ 完了

> **[FACT]** typos は md/xml に対して「機能の有無」で勝つ。程度の差ではない

| メトリクス | md | xml | typos v8 |
|:-----------|:---|:----|:---------|
| ファイル数 (3環境管理) | 3 | 3 | **1** |
| SLoC | 42 | 36 | **30** |
| 共通部分の重複率 | 71% | 75% | **0%** |
| 共通制約1つ追加時の編集箇所 | 3 | 3 | **1** |
| 条件分岐 | 不可能 | XSLT (別言語) | **ネイティブ** |

成果物: `typos-benchmark/e3_dry_efficiency/E3_DEMO.md`

## E1: Compression Shield ✅ パイロット完了

> **[DECISION]** パイロット: 4形式 × 4圧縮率 × Q2 × r0 = 16 試行 (正式版は後日)

### パイロット ICR 結果 (gemini-3-flash-preview, Q2, r0)

| Format | L0 (0%) | L2 (~60%) | L3 (~75%) | L4 (~95%) |
|:-------|:-------:|:---------:|:---------:|:---------:|
| **plain** | **1.00** | 0.93 | **1.00** | **0.67** |
| **typos** | **1.00** | **1.00** | 0.80 | 0.60 |
| **md** | **1.00** | **1.00** | 0.80 | 0.60 |
| **xml** | **1.00** | **1.00** | 0.80 | 0.60 |

> **[DISCOVERY]** L2 で構造化 (typos/md/xml) が plain を上回る (1.00 vs 0.93)。構造タグが制約境界を保持。
> **[DISCOVERY]** L3 で逆転。構造タグの文字コストが制約バジェットを圧迫 (plain 1.00 vs 構造化 0.80)。
> **[DISCOVERY]** 「行動指定」型制約 (C4,C7,C8,C10) は圧縮に最も脆弱 (L4で100%脱落)。「禁止」型は堅牢。

### 正式データ取り (後日)

- 反復: r0/r1/r2 (最低3反復で統計的信頼性)
- 質問: Q1/Q2/Q4 (ドメイン多様性)
- Ochema cortex + account rotation で RPM 制限を回避
- 生データ: `results/pilot_icr_data.json`

成果物:
- `typos-benchmark/e1_compression/compressed/` — **48件全配置済み**
- `typos-benchmark/e1_compression/results/pilot_icr_data.json` — パイロット生データ

## E2: Structural Consensus 📋 後日

LLM 10体 or 人間 8-10人 が同一タスクのプロンプトを書いたときの構造的一致度 (Fleiss' κ)。

## 設計監査の軌跡

> **[DISCOVERY]** 設計の精密化に /exe+ → /ele+ → /dio+ の 3イテレーションを費やしたが、本質的な価値は /u+ で再定義した「4軸で殴る」リフレーム

- D4b v1.0 → v1.1 (/exe+ 9件修正)
- v1.1 → v1.2 (/ele+ 5件是正: ANCOVA×Mediation 衝突解消、段階的実行、FDR exploratory 格下げ)
- v1.2 → Typos Benchmark v1.0 (/u+ リフレーム: 圧縮耐性のみ → 4軸)

> **[DECISION]** ANCOVA を使わない。通常 ANOVA のみ。トークン差は TER で別途報告。FDR は exploratory (因果主張しない)

> **[DECISION]** 殴る順序: E4 (直感) → E3 (直感) → E1 (学術) → E2 (学術)。先に直感で掴み、後で証拠で固める

## 次回アクション

1. E1 正式データ取り: 3反復 × 3質問 × 4形式 × 4圧縮率 = 144 試行
2. Ochema account rotation (Tolmeton/makaron) で RPM 制限回避
3. E2 の LLM 代替版設計
4. 全 E1-E4 統合レポート作成

## ファイル構成

```
60_実験｜Peira/08_関手忠実性｜FunctorFaithfulness/
├── TYPOS_BENCHMARK.md              # 全体設計書
├── MARKUP_COMPRESSION_EXPERIMENT.md # D4b v1.2 (E1 の詳細版)
└── typos-benchmark/
    ├── e1_compression/
    │   ├── prompts/                # 4形式の system prompt
    │   ├── compressed/             # 圧縮後 prompt (L0 配置済み)
    │   ├── results/                # バッチ定義 JSON
    │   ├── run_e1.py               # バッチ生成 + 採点
    │   ├── run_e1_auto.py          # 自動実行 (Gemini API)
    │   └── execute_batch.py        # バッチヘルパー
    ├── e3_dry_efficiency/
    │   └── E3_DEMO.md              # 3環境管理デモ
    └── e4_parse_robustness/
        ├── run_e4.py               # 10テストケース × 5形式
        ├── e4_results.json         # 結果
        └── prompt_samples/         # サンプル prompt
```

<!-- ROM_GUIDE
primary_use: Typos v8 の実証的ベンチマーク。公開時の「見えるつかみ」
retrieval_keywords: typos benchmark, compression resilience, parse robustness, DRY, markup comparison, ICR, e1, e3, e4
expiry: permanent
-->
