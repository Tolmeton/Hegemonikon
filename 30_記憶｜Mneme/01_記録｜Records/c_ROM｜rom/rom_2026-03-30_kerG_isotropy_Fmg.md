---
rom_id: rom_2026-03-30_kerG_isotropy_Fmg
session_id: claude-code_2026-03-30
created_at: 2026-03-30
rom_type: distilled
reliability: High
topics: [ker(G), image(G), isotropy, F=mg, forgetting-duality, abstraction, Paper-I, E12]
exec_summary: |
  E12 (30 sessions/6053 steps) で ker(G) の等方性と image(G) の低ランク性を実証。
  Creator の洞察「忘却=重力、方向は受け手の構造が決める」を F=mg 対応として定式化。
  Paper I §5.9 に広義/狭義忘却の二重性、忘却-抽象化同一性の系を新設。
---

# E12 ker(G) 等方性 + F=mg 忘却の二重性

## [DISCOVERY] E12 実験結果

30 sessions, 6053 steps, 248 chunks (tau=0.70):

| 手法 | k_signal | Participation Ratio | 解釈 |
|:---|:---|:---|:---|
| M1 Boundary Drift | 1 | 44.2 | 第1成分が 11.8% |
| M2 Within-Chunk Residual | 3 | 106.4 | ker(G) は高次元的に等方的 |
| M3 Fisher | image(G)=6, ker(G)=0 | - | image(G) は低ランク、ker(G) は等方的 |

image(G) の最強プロキシ: Precision (embedding norm), r=-0.295, p<1e-121

## [DECISION] 忘却の二重性: 広義と狭義

- **広義忘却** = alpha = g (重力加速度): 全要素に MECE に等しく作用。定数。
- **狭義忘却** = F_{ij} = F (力): 受け手の構造 (射の密度) により方向を持つ結果。
- **忘却感受性** = ||T||_g = m (質量): 射の密度の逆数。圏の構造が決める。

対応: F_{ij} = (alpha/2)[d(PhiT)]_{ij} <=> F = mg

Paper I §5.3「忘却の方向が力を決める」= 狭義忘却の記述 (そのまま正しい)
Creator「忘却は等方的」= 広義忘却の記述 (E12 が実証)
両者は共存する (広義が狭義を包含)。

## [DECISION] 忘却耐性と抽象化

定義: R(X) = |Hom(X, -)| (対象 X から出る射の数)

予想: 閾値 R_crit(alpha) が存在し、R(X) > R_crit => 保存、R(X) < R_crit => 忘却。
R_crit は alpha の単調増加関数。

系 (忘却-抽象化同一性):
- 普遍的構造 = R(X) 最大 = 忘却耐性最大
- alpha 増大 => R_crit 増大 => image(G) 縮小 => より抽象的な構造のみ生存
- **忘却の強化は抽象化を必然的に生産する**

認知科学的帰結:
- AuDHD (alpha 大) => 具体を失い構造を保持 => 抽象的思考に秀でる
- チンパンジー (alpha ≈ 0) => 具体が全て残る => 抽象化の圧力ゼロ (対偶)
- Composer2 (extended thinking = alpha 動的増大) => コーディング (構造操作) 性能向上

## [DISCOVERY] ニュートン近似と GR 補正

PR = 106.4 (完全等方なら 768) => ker(G) は厳密には等方的でない。
残差 = m -> g バックリアクション = 忘却対象が忘却場を変形する。
一般相対論との同型: g = g[m] (双方向的結合)。
定量化は §6 alpha-動力学の射程。

## 成果物

| コミット | 内容 |
|:---|:---|
| e15b5b8 | Pinakas 7層インフラ |
| 9cc216b | E12 実験コード + 結果 JSON |
| 38a914b | Paper I §5.9 新設 (広義/狭義忘却, F=mg, 忘却-抽象化同一性) |

## 関連情報
- 関連 WF: /pei (E12), /u+ (3層対話), /bou (方向選択)
- 関連 Paper: Paper I §5.9, Paper II (商空間), Paper III (alpha パラメータ)
- 関連 Pinakas: T-002 (ker(G) 実測), S-006 (Paper接続マップ)

<!-- ROM_GUIDE
primary_use: ker(G) 等方性の実験的証拠と忘却の二重性理論の参照
retrieval_keywords: ker(G), image(G), isotropy, F=mg, forgetting duality, abstraction, Paper I §5.9, E12, Fisher ratio, participation ratio, forgetting resistance
expiry: permanent (理論的発見)
-->
