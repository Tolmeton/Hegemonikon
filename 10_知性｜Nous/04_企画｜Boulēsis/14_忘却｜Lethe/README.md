```typos
#prompt lethe-readme
#syntax: v8
#depth: L1

<:role: Lēthē (λήθη) — 忘却関手の計算的実現 :>

<:goal: CCL を圏論的中間表現として用い、コード構造の忘却と回復を実証する :>

<:context:
  - [knowledge] 命名: Lēthē = ギリシャ語で「忘却」。忘却関手 U の研究だから
  - [knowledge] 核心主張: CCL は自由モノイダル圏の構文的実現であり、忘却関手 U の左随伴として機能する
  - [knowledge] CodeBERT 反転 (2026-03-20): LLM は構造を知っている。問題はアクセスだ
  - [file] ビジョン.md — 研究ビジョン (60KB, v0.9+)
  - [file] experiments/ — 全実験スクリプト・データ・結果
  - [file] ../12_遊学/01_研究論文/llm_body_draft.md — 関連論文 (Lēthē より広いスコープ)
/context:>
```

# Lēthē — 忘却関手の計算的実現

## 概要

CCL (Cognitive Control Language) を圏論的中間表現として用い、コード構造の **忘却** (U: Code → CCL) と **回復** (N: CCL → Code) を理論的・実験的に研究するプロジェクト。

## 構造

| パス | 内容 |
|:---|:---|
| `ビジョン.md` | 研究ビジョン・理論・実験計画・結果の統合文書 |
| `experiments/` | 実験スクリプト・データセット・結果ファイル |

## 関連ドキュメント

- **[11_肌理｜Hyphē](../11_肌理｜Hyphē/)** — 理論的基盤 (CKDF 4層, チャンク公理, NP-hard 回避)。Lethe の実験結果が Hyphē 理論を支持し、Hyphē の研究プログラムが Lethe の次の実験を規定する
- [llm_body_draft.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/llm_body_draft.md) — "Does an LLM Have a Body?" 論文 (Lēthē の structural probing は §7.0)
- [aletheia.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/00_核心｜Kernel/A_公理｜Axioms/aletheia.md) — 忘却関手 U の理論的基盤
- [code_ingest.py](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/symploke/code_ingest.py) — Code→CCL トランスパイラ (本体)

### 理論 ⊣ 実験 接続 (→ [Hyphē 対応マップ](../11_肌理｜Hyphē/README.md#理論--実験-対応マップ))

| Lethe 実験成果 | 支持する Hyphē 理論 |
|:---|:---|
| Phase 4: ρ=0.507, AUC=0.967 | Chunk = MB (構造検出の可能性) |
| Phase B: PC 3軸 (合成長/変換密度/MB比率) | CKDF L2 座標検出 |
| Phase B: Ξ=1.083, Gini=0.613 | CKDF L3 Fix(G∘F) 存在示唆 |
| 5-bin分析: Bin 2-4 の ρ 低下 | Kleinberg Scale-Invariance 放棄 |

### ⚠️ 49d 特徴量空間の既知脆弱性

| 問題 | 深刻度 | 詳細 |
|:-----|:-------|:-----|
| スケール支配 | 🔴 | PC1 (33%) = nt (関数サイズ)。Z-score 正規化なしで cos≈0.98 に崩壊 |
| 有効次元 | 🟠 | d_eff=18.8/49 — 61.7% が冗長 |
| v3→v4 劣化 | 🟠 | Recall@1: 85.2%→68.7%。同一データ A/B テスト未実施 |
| Z-score 依存 | 🔴 | 正規化必須 = raw 空間が自然なスケールを捕えていない |

これらの脆弱性は、Hyphē 研究プログラムの実験 (Fix(G∘F) 収束, MB 境界検出) を実施する**前に**解決が必要。

## 主要な発見 (2026-03-20 時点)

1. **CCL ≅ 圏論** — 14演算子が圏論の概念と1対1対応
2. **Code→CCL は機械的** — AST 解析 + 9変換ルール。LLM 不要
3. **CCL embedding > Text embedding** — 構造検索で +20pp recall@1
4. **CodeBERT 反転** — 線形プローブ ρ≈0 → 注意的プローブ ρ=0.745。構造情報は**ある**がアクセスが困難
