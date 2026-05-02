# Handoff: Hyphē Precision-Aware λ 実証実験 + Whitening 検証

**日時**: 2026-03-15 15:26 JST
**セッションID**: 8e0f89f3
**Agent**: Claude (Antigravity)

---

## 成果サマリ

### ① v0.7 Precision-Aware λ 実証 ✅

`hyphe_chunker.py` の core bug を修正: precision が `compute_lambda_schedule` に渡されていなかった。

| 指標 | v0.5.1 | v0.7 | 改善 |
|---|---|---|---|
| precision range | 0.012 | **1.000** | 83× |
| δλ₁ range | 0.003 | **0.200** | 67× |
| 弁別率 | 0% | **95% (41/43)** | ∞ |

- **修正箇所**: `hyphe_chunker.py` L949-958 (precision→λ recalculation)
- **修正箇所**: `run_chunker.py` L113 (precision フィールド出力追加)
- 全13セッション/48チャンク G∘F 収束、63テスト全パス

### ② Whitening 実験 ✅

ZCA whitening で narrow cone (cos_sim mean 0.725→-0.002) は解消したが、precision の U字型分布は**解消せず** (BC 0.57→0.66)。

**結論**: U字型分布は embedding anisotropy ではなく、`rho_eff` 自体の分布特性 + min-max 正規化の構造的帰結。

### ③ Quantile 正規化 (v0.8) 実験 ✅

min-max → quantile 正規化に変更すると分布は均一化するが、λ 弁別力が 8% 低下。

**結論**: 正規化手法の差は loss に **9%** — 実質無影響。v0.7 min-max を維持。

---

## 変更ファイル

| ファイル | 変更 |
|---|---|
| `hyphe_chunker.py` L949-958 | precision→λ 接続 (core bug fix) |
| `run_chunker.py` L113 | precision フィールド出力追加 |
| `run_whitening_experiment.py` | **新規** ZCA whitening 実験スクリプト |
| `run_precision_lambda_experiment.py` | **新規** precision-aware λ 実験スクリプト |
| `precision_v07_results.json` | v0.7 全13セッション結果 |
| `embedding_cache.npz` | 5セッション embedding キャッシュ (768d) |

---

## 未完了・→次

1. **§4 AY 理論** — presheaf representability difference (未着手)
2. **v0.9 multilayer precision** — bge-m3 shallow↔deep (未着手)
3. **cross-session λ schedule** — セッション間でのλ正規化 (未着手)

---

## 他セッション統合メモ

- **Anisotropy セッション** (c3196a99): Gemini embedding (3072d) は D_eff/d=0.078、cos_sim mean=0.767。H1 (cone degeneration) を [推定 70%] で支持。
  - `/noe+` 分析が `noe_anisotropy_cognitive_meaning.md` に保存済み
  - Exp-2 (Direction-Selective Precision) と Whitening は本セッションで部分検証済み
- **Gemini Embedding 2 セッション** (a2b4f064): ブートのみで実質作業なし

---

## 教訓

- **min-max 正規化の U字型**: rho_eff の分布が偏っている場合、min/max が外れ値に固定され二極化する。これは anisotropy ではなく正規化手法の構造的性質
- **core bug の長期潜伏**: precision が λ schedule に接続されていないバグは、precision 分散が低い時代には影響が不可視だった。v0.7 で precision range が拡大して初めて修正効果が顕在化
