# 06_Hyphē実験｜HyphePoC

Hyphē 理論に基づくセッションログ自動チャンカーの PoC 実験。

## 理論→実装マッピング

| 理論 (linkage_hyphe.md) | 実装 | 概要 |
|:---|:---|:---|
| ρ_MB (§3.3) | cosine similarity | 隣接ステップ間の意味的類似度 |
| τ (§3.4) | 閾値パラメータ | 類似度が τ を下回る = MB 境界 |
| L(c) (§3.6) | Drift 項のみ | `1.0 - coherence` (EFE 項は Phase 2) |
| F (Write) | `_merge_small_chunks` | 短チャンクを隣接に統合 (発散) |
| G (Read) | `_split_incoherent_chunks` | 低 coherence チャンクを再分割 (収束) |
| Fix(G∘F) | `gf_iterate` | 境界が不変になるまで反復 |

## ファイル構成

| ファイル | 行数 | 概要 |
|:---|:---|:---|
| `hyphe_chunker.py` | 487 | コアモジュール (パーサー, 類似度, 境界検出, G∘F, L(c)) |
| `run_chunker.py` | 227 | ランナー (全セッション一括処理, VertexEmbedder 利用) |
| `test_hyphe_chunker.py` | 450+ | テスト (mock embedding + 統合テスト) |
| `results.json` | - | 実行結果 (13セッション分) |

## 実行方法

```bash
# 全セッション (デフォルト: τ=0.7, 768d)
python run_chunker.py

# τ を指定
python run_chunker.py --tau 0.65

# 1ファイルだけ
python run_chunker.py --file path/to/session.md

# 結果を JSON で保存
python run_chunker.py --output results.json
```

## 既知の問題

- **`.env` パス**: `run_chunker.py` L38-39 が4階層上 (`oikos/.env`) を参照するが、
  実際の `.env` は3階層上 (`01_ヘゲモニコン/.env`) にある。修正が必要。
- **依存**: `python-dotenv`, `mekhane.anamnesis.vertex_embedder` (Gemini Embedding API)

## 関連

- **理論的基盤**: [THEORY.md](./THEORY.md) — 溶媒仕様としての Embedding 設計 (ker(G), anisotropy, coherence invariance)
- 理論: `10_知性｜Nous/03_知識｜Epistēmē/linkage_hyphe.md` §3-§3.6
- 親文書: [知性は溶媒である (draft)](../../10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/知性は溶媒である_草稿.md)
- Possati PDE PoC: `05_スペクトル解析｜SloppySpectrum/EXPERIMENT_DESIGN.md`
  (ρ(x) の連続化・PDE シミュレーション設計。本 PoC は離散版の先行実験)
