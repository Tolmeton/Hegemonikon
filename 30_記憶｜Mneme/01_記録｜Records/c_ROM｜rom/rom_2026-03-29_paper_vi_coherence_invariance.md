---
rom_id: rom_2026-03-29_paper_vi_coherence_invariance
session_id: AY-2_coherence_invariance
created_at: 2026-03-29 16:30
rom_type: distilled
reliability: High
topics: [Paper VI, Coherence Invariance, τ-invariance, G∘F, 結晶化, 忘却論, Euporía, AY-2, ker(G), 商写像]
exec_summary: |
  Paper VI「行為可能性は忘却である」の骨子 v0.1 を完成。
  核心命題: G (結晶化) = ker(G) への商写像 = 忘却。商空間が新しい射を開く = AY > 0。
  τ-Invariance の十分条件 S1-S3 を Hyphē 実装レベルで基礎づけた。
---

# Paper VI: 行為可能性は忘却である — セッション蒸留

## [DECISION] 核心命題と位置づけ

- **Paper VI = 忘却論シリーズ (I-V) の認知科学的インスタンス**
- 核心: **忘却 (G) が行為可能性 (AY) を増大させる** — Euporía と忘却論の合流点
- G∘F は「テキスト分割」ではなく「結晶化」(最も Kalon な情報単位の演繹的生成)
- 3ドメイン (Linkage / Cognition / Description) に共通する構造

## [DISCOVERY] d = ker(d) と G = ker(G) の同型 (§2.3)

Paper II §1.1 の修正済み構造との厳密な対応:

| 構造 | Paper II: 微分 d | Paper VI: 結晶化 G |
|:--|:--|:--|
| 操作の本質 | ker(d) = ℝ への商写像 | ker(G) への商写像 |
| 核 | ℝ (1次元) | {Scale, Valence} (2次元) |
| 核の外 | d は可逆 (sin→cos ループ) | G は構造保存 (Coherence 保存) |
| 逆操作の障害 | η の非自然性 (初期条件 C) | η の非自然性 (τ 依存性) |
| 行為可能性の源 | 微分方程式の解空間 | チャンク間の新しい連結 |

**商写像が AY を生むメカニズム**: 商空間の対象は「粗い」が、粗いからこそ**より多くの対象と射を持てる**。同値類の各元が新しい射の起点になる。

**障害の差異**: d⊣∫ は原理的に非自然 (解消不能)。F⊣G は Fix(G∘F) 上で冪等モナドとして機能 (実用的には解消可能)。

## [DISCOVERY] τ-Invariance の十分条件 S1-S3 (§3.3)

**S1 (共通測度)**: F と G が同一の ρ 測度を参照。F は ρ-blind だが操作するペアの ρ は同一分布から。

**S2 (不動点の一意性)**: Fix(G∘F) = {全内部ペア ≥ τ ∧ 全結晶 ≥ min_steps}。有限反復で到達。

**S3 (平均収束)**: C̄(Fix(G∘F; τ)) → μ_ρ (場の内在的平均、τ に非依存)。

**証明の鍵**: F と G は「低類似度ペア」を内部⇔外部で対称的に転送する:
- F (merge): 外部境界ペアを内部に入れる → Coh 下降
- G (split): 内部最低ペアを外部に出す → Coh 上昇
- 両者の擾乱が Fix(G∘F) で打ち消し合う

## [DISCOVERY] ker(G) 次元が τ-invariance 強度を予言

ker(G) が小さい → 商空間が元の空間に近い → τ-invariance が強い。

| ドメイン | ker(G) | 予測 range |
|:--|:--|:--|
| Linkage | 2/6 = 33% | 0.008 (実測) |
| ker < 33% のドメイン | < 33% | < 0.008 |
| ker > 50% のドメイン | > 50% | 崩壊 (τ-invariance 不成立) |

## [DECISION] Creator の4指摘 (2026-03-29)

旧分析「Linkage = 簡単 / Cognition・Description = 難しい」を破壊:
1. **離散は幻想**: depth は連続量。L0-L3 は恣意的離散化
2. **split = 忘却 = 力の生成**: G は削るのではなく自由度を解放する
3. **統計で測れる**: 一般論での一貫性は統計的に問える。測定不能は怠慢
4. **Linkage も結晶化**: 3ドメインは同型。単なるテキスト分割ではない

## 成果物

| ファイル | 内容 |
|:--|:--|
| `paper_VI_draft.md` (500行) | Paper VI 骨子 v0.1。§1-§8 + §2.3 精密化 + §3 精密化 |
| `linkage_crystallization.md` | G∘F = 結晶化の定義。UnifiedIndex に保存 |
| `TASKS_euporia_hyphe_fusion.md` | AY-2 状態を「着手中」に更新 |

## 次回アクション (優先順序)

1. **§5/§6 の実験**: Cognition or Description での τ-invariance PoC
2. **§3.5 P5-P7 の検証**: バイモーダル分布での崩壊確認 (Hyphē 実験で可能)
3. **Paper II への逆流**: §2.3 の同型を Paper II §7 展望に追記

<!-- ROM_GUIDE
primary_use: Paper VI の理論的核心の復元。次セッションで §5/§6 実験に進む際の文脈
retrieval_keywords: Paper VI, Coherence Invariance, τ-invariance, 結晶化, G∘F, ker(G), 商写像, AY-2, Euporía, 忘却論
expiry: permanent
-->
