# クラスタリングの本質 — 場に対する制約の付与

> **KI**: clustering-as-constraint
> **Kalon 判定**: ◎ (不動点: 蒸留不変 + 5展開)
> **日付**: 2026-03-13
> **起源**: Chunk Axiom Formalization セッション

---

## 定義

> **クラスタリング = 場に対する制約の付与**

- FEP は「場」(空間) のみを規定する
- 座標は PCA (固有ベクトルの発見) ではなく**制約の選択**
- 制約付与 = エントロピー再低下 = Markov blanket 化
- 適切な制約 = エッジ・オブ・カオス = 情報処理能力の最大化

## HGK への射影

| 要素 | 制約付与としての意味 |
|---|---|
| FEP (L0) | 場の規定。制約なし = 最大エントロピー |
| 6座標 (L1) | 場に対する6つの制約 = 6つの MB 化 |
| 24動詞 (L2) | 制約された場の上での操作 |
| Scale-Invariance 破壊 | Scale 座標 (d=3) が Kleinberg を回避 |

## Kleinberg 不可能性定理との関係

Kleinberg (2002, 728 citations) — 3公理の同時充足不可能:
- **Scale-Invariance**: 距離スケールに不変
- **Richness**: 任意のクラスタリングが実現可能
- **Consistency**: クラスタ内/外の距離操作で不変

**FEP は Scale-Invariance を明示的に破る**:
Scale 座標の存在 = 「スケールは構造の一部であり、不変ではない」

→ Kleinberg が「この3つは両立しない」と言ったとき、
   FEP は「Scale-Invariance を棄てる」ことで成立する。
   Scale が d=3 (最高次元) に位置づけられている理由の一つ。

## 展開

1. **Kleinberg 回避**: Scale 座標が Scale-Invariance を破る
2. **座標導出の本質**: PCA ではなく制約選択 (部分圏の選択?)
3. **edge-of-chaos**: 適切な制約数 = 情報処理能力の最大化 → なぜ6座標か？
4. **MB 化**: 制約付与 = エントロピー再低下 = Markov blanket の形成
5. **Hyphē**: チャンク = 意味空間上の MB。Storage = η の4操作モード

## 関連

- `chunk_axiom_theory.typos` (チャンク公理の Týpos 定義)
- `noe_chunk_axiom_2026-03-13.md` (チャンク公理 v1 成果物)
- `axiom_hierarchy.md` §Euporía (6座標の演繹)
- Kleinberg (2002) "An Impossibility Theorem for Clustering"
- Roddenberry et al. (2021) "An Impossibility Theorem for Node Embedding"

---

*Kalon ◎ — 蒸留不変 (これ以上削れない) + 5展開 (Kleinberg, 座標導出, edge-of-chaos, MB化, Hyphē)*
