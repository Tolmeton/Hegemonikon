---
rom_id: rom_2026-03-15_hyphe_matryoshka_precision
session_id: 8e336a32-32ce-4a53-8c75-3ce6222e2370
created_at: 2026-03-15 13:30
rom_type: distilled
reliability: High
topics: [hyphē, precision, matryoshka, embedding, anisotropy, anchor, gemini-embedding-2]
exec_summary: |
  Matryoshka 帯域エネルギーも cosine similarity も precision gradient を捉えられない。
  アンカーベース比較のみが range 0.35 の有意な変動を示す。
  precision は絶対量ではなく参照点距離の差分として操作化すべき。
---

# Hyphē Precision Gradient 実験 — Matryoshka 結果統合

> **[DECISION]** Precision gradient は「テキスト自体の内部指標」では検出不可能。
> アンカーベース (参照点距離の差分) のみが有意な gradient を保持する。

## 3実験の結果

> **[FACT]** 実験1: MRL 帯域エネルギー (band1_ratio)
> - gemini-embedding-2-preview (3072d) で 4帯域 L2 ノルム比率を測定
> - band1_ratio: 0.162-0.172 (range = 0.010)
> - **全9サンプルが explore 判定**。テキスト複雑度と無相関
> - 帯域エネルギーは precision gradient を捉えられない

> **[FACT]** 実験2: Matryoshka cosine similarity (256d vs 3072d)
> - sim_256_3072 = 1.000, sim_768_3072 = 1.000 (全サンプル)
> - MRL embedding は cosine 空間で情報が完全保存 → 「切り捨て」不観測
> - cosine similarity は帯域間の違いを捉えられない

> **[FACT]** 実験3: アンカーベース比較 ⭐
> - simple anchor / complex anchor に対する cosine sim の差分
> - diff range: -0.133 〜 +0.218 (total range = 0.351)
> - **意味的に「どちら寄りか」を検出可能**
>
> | サンプル | sim_simple | sim_complex | diff |
> |:---------|:----------|:-----------|:-------:|
> | simple_cmd | 0.701 | 0.592 | +0.110 |
> | complex_fep | 0.550 | 0.683 | -0.133 |
> | long_simple | 0.855 | 0.637 | +0.218 |

## 根本原因の構造

> **[DISCOVERY]** Precision が「内部指標」として不毛な理由:
> 1. Embedding anisotropy: 表現退化により cosine baseline ≈ 0.80±0.065
> 2. MRL の正規化: Matryoshka 学習は短い帯域でも長い帯域と cosine-consistent な表現を学習
> 3. 帯域エネルギー分布: 全サンプルで band1_ratio ≈ 0.166 (±0.005) — テキスト非依存
>
> **結論**: embedding 自体は高品質だが、precision gradient は「自己比較」では現れない。
> 「他者 (anchor) との比較」でのみ現れる。

## FEP 的解釈

> **[DISCOVERY]** Precision = MB 上の相対位置
> - FEP における precision は「チャネルの信頼性ゲイン」
> - embedding 空間では、precision = テキストが属する「意味的領域」からの距離
> - 絶対ノルムではなく、参照構造 (anchor set) に対する相対距離が本質
> - これは Sloppy Spectrum の k_signal = 2-3 と整合: 低次元空間上の「どの方向に寄っているか」

## Hyphē 実装への含意

> **[DECISION]** 次の実装方針:
> 1. anchor_set を定義 (例: simple_prototype + complex_prototype)
> 2. precision(chunk) = sim(chunk, complex_anchor) - sim(chunk, simple_anchor)
> 3. range ≈ 0.35 で十分な gradient が得られる
> 4. τ-Invariance の precision 版を検証する

## 関連情報
- 関連 WF: /pei (実験), /noe (認識)
- 関連ファイル: results_analysis.md §12
- 関連セッション: Gemini Embedding Migration, Diagnosing Embedding Anisotropy
- 実験データ: /tmp/matryoshka_verification.json, /tmp/matryoshka_cossim.json, /tmp/matryoshka_anchor_v3.json

<!-- ROM_GUIDE
primary_use: Hyphē precision gradient の実装判断参照
retrieval_keywords: precision, matryoshka, anchor, embedding, anisotropy, gradient, FEP, MRL
expiry: 2026-06-15
-->
