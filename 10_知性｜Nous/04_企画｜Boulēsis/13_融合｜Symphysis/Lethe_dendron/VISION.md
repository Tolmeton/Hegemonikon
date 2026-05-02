```typos
#prompt ccl-dendron-fusion-vision
#syntax: v8
#depth: L2

<:role: CCL-IR × Dendron 融合ビジョン — 構造と存在の統一理論 :>

<:goal: CCL の構造的忘却 (U_ccl) と Dendron の存在的忘却 (U_purpose) を
  同一の随伴フレームワーク内で統一し、コード品質の新しい次元を開く :>

<:context:
  - [knowledge] CCL-IR (Lēthē): Code → CCL 変換 + 43d/51d 特徴量 + 構造検索。VISION v0.30, 2635行
  - [knowledge] Dendron: 存在誤差最小化によるコード存在証明。VISION.md, 373行
  - [knowledge] 共通基盤: 両者は U⊣N 随伴の異なるインスタンス。CPS1'' (方向付き相補性) が基盤
  - [knowledge] 実装基盤: fusion.py (381行, Phase 0 実装済み)。FusionEntry + 直交性分析
  - [file] 14_忘却｜Lethe/VISION.md (Lēthē の理論的基盤 v0.30)
  - [file] mekhane/dendron/VISION.md (Dendron の存在証明理論)
  - [file] mekhane/symphysis/fusion.py (Phase 0 実装)
/context:>
```

# CCL-IR × Dendron 融合ビジョン

> **Structure × Existence = Complete Understanding**
>
> 名前を忘れて構造を見る (Lēthē)。
> 機能を忘れて存在理由を問う (Dendron)。
> 両方の忘却を組み合わせて、コードの本質を完全に捉える。

**Version**: 0.2.0
**Date**: 2026-03-24
**Status**: 🟡 Phase 0 実装済み → Phase 1 移行準備中
**Authors**: Creator + Claude (Antigravity)

---

## §0. なぜ融合するのか — Problem Statement

### 0.1 Lēthē の到達点 (v0.1.0 以降の進展)

Lēthē は「**何であるか (構造)**」を答える。v0.1.0 時点から大きく進展:

| 到達点 | 指標 | セクション |
|:---|:---|:---|
| 忘却関手の健全性 | LQS = 1.00 (R2=100%, R3=100%) | Lēthē §15 |
| 構造同型検出 | 935 同型グループ (10847関数中) | Lēthē §15.4 |
| CCL embedding | CodeBERT ρ=0.507, Siamese ρ=0.844 | Lēthē §11, §15 |
| LLM 内部の構造情報 | Attentive Probing 偏ρ=0.74 | Lēthē §13 |
| 43d/51d 構造特徴量 | Code→Code 検索実装済み (N 側) | Lēthē §18, §20 |
| 連続 CCL 距離 | Lawvere 距離空間構成済み (三角不等式 100%) | Lēthē §17.8 |
| 準同型発見 | CCL 不一致だが 43d sim>0.9 = 344件 | Lēthē §17.7b |

**しかし、なぜ両方が存在するのかは答えない。**

### 0.2 Dendron の到達点

Dendron は「**なぜ存在するか (目的)**」を答える。

- PURPOSE 推定 (purpose_infer.py, 152行): docstring/手書き/推定の3層
- EPT スコア: 存在証明テンソル
- PROOF.md 検証: 存在理由の形式的記録

**しかし、構造的に冗長であることには気づかない。**

### 0.3 融合が解く問題 (v0.2.0 更新)

| 問い | Lēthē 単独 | Dendron 単独 | **融合** |
|:-----|:-----------|:-----------|:---------|
| 構造的に何か？ | ✅ (43d/51d) | ❌ | ✅ |
| なぜ存在するか？ | ❌ | ✅ | ✅ |
| 構造的に冗長か？ | ✅ (R1: 935群) | ❌ | ✅ + **なぜ冗長なのに分離すべきか** |
| 存在理由は正当か？ | ❌ | ✅ (宣言のみ) | ✅ + **構造的根拠で裏付け** |
| 準同型コード対 | ✅ (344件発見) | ❌ | ✅ + **PURPOSE で真の冗長 vs 正当分離を判定** |
| 設計変更の影響 | ✅ (43d diff) | ✅ (目的 diff) | ✅ + **両軸の交差分析** |

> **単独では見えないものが、融合で見える。**
> 特に: 43d で発見された 344 件の準同型ペアのうち、**PURPOSE が同一なもの = 真のリファクタリング候補**。

---

## §1. 数学的基盤 — 忘却の随伴理論

### 1.1 二つの忘却関手

CCL-IR と Dendron は、同一の U⊣N 随伴構造の異なるインスタンスである。

```
Code ∈ Code    (全情報を持つ圏)
  │
  ├── U_ccl:    Code → CCL         名前を忘却し、構造を残す
  │    ├── N_ccl:    CCL → Code     構造から候補コードを回復
  │    └── 43d/51d 特徴量: CCL の連続表現 (n=1〜2)
  │
  └── U_purpose: Code → Purpose     機能を忘却し、存在理由を残す
       └── N_purpose: Purpose → Code 存在理由から正当なコードを回復
```

### 1.2 積関手 — 同時忘却

```
U_full = U_ccl × U_purpose : Code → CCL × Purpose

  U_full(sort_by_name) = (
    _ >> V:{pred} >> F:[each]{fn} >> fn,    ← 構造
    "ユーザー一覧を名前順で表示する"           ← 存在理由
  )
```

### 1.3 CPS1'' による方向付けの基盤 (NEW)

> Lēthē §19 「力とは忘却である」により、U⊣N の方向に演繹的根拠がある。

| CPS 概念 | 構造 (Lēthē) | 存在 (Dendron) |
|:---|:---|:---|
| 容器 $U_{ctr}$ | Code (CCL より先に在った) | Code (PURPOSE より先に在った) |
| 内容 $U_{cnt}$ | CCL (Code から生成) | PURPOSE (Code から推定) |
| 架橋 $T$ | python_to_ccl() | purpose_infer() |
| $\Theta$ | S(e) 忘却スコア | EPT スコアの逆 |

**両方の忘却が CPS1'' に従う → 積関手 U_full も CPS1'' に従う**。

### 1.4 直交性の定理 (実証済み)

> **直交性の定理**: ∃ x, y ∈ Code s.t. U_ccl(x) = U_ccl(y) ∧ U_purpose(x) ≠ U_purpose(y)
>    かつ  ∃ x, y ∈ Code s.t. U_purpose(x) = U_purpose(y) ∧ U_ccl(x) ≠ U_ccl(y)

[確信] Q2 実験 (2026-03-18) で HGK コードベース全体を計測。直交性スコア 0.924。
A=3,950関数 (同一CCL×異PURPOSE), B=782関数 (同PURPOSE×異CCL), C=390関数 (真の冗長)。

### 1.5 Ξ (忘却不均一度) と融合 (NEW)

Lēthē §19.4 の Ξ_search (43d 特徴量の次元分散の分散) は、**U_ccl の忘却の質**を測る。

融合における Ξ の拡張:

```
Ξ_fusion = Var(σ²_structure, σ²_purpose)

Ξ_fusion ≈ 0: 構造と目的が完全相関 → 融合の価値なし
Ξ_fusion > 0: 構造と目的が直交 → 融合に固有の価値あり
```

直交性スコア 0.924 → Ξ_fusion > 0 [確信]

---

## §2. 融合アーキテクチャ (v0.2.0 更新)

### 2.1 四層コード理解モデル

```
┌──────────────────────────────────────────────────────┐
│  Level 3: 流れ (Flow)    ─ TypeSeq (Lēthē §20)      │
│           計算の型パターンは？                         │
│           [S,T,T,T,S] — 51d 特徴量                   │
├──────────────────────────────────────────────────────┤
│  Level 2: 存在 (Why)     ─ Dendron EPT               │
│           なぜ存在するか？                            │
│           PROOF.md / PURPOSE / REASON                 │
├──────────────────────────────────────────────────────┤
│  Level 1: 構造 (What)    ─ Lēthē                     │
│           構造的に何か？                              │
│           CCL 式 / 43d 特徴量 / Lawvere 距離          │
├──────────────────────────────────────────────────────┤
│  Level 0: 名前 (Surface) ─ テキスト検索               │
│           何と呼ばれているか？                         │
│           grep / ベクトル検索                          │
└──────────────────────────────────────────────────────┘
```

### 2.2 FusionEntry v2 (実装済み + 拡張提案)

```python
@dataclass
class FusionEntry:
    """構造と存在の統合エントリ"""

    # Level 0: 名前 (実装済み)
    filepath: str
    name: str
    lineno: int
    class_name: str

    # Level 1: 構造 — Lēthē (実装済み)
    ccl_expression: str          # CCL 構造式
    # ↓ v0.2.0 追加提案
    ccl_features_43d: np.ndarray # 43d 構造特徴量
    ccl_features_51d: np.ndarray # 51d (+ TypeSeq)
    structural_family: str       # R1 同型族 ID

    # Level 2: 存在 — Dendron (実装済み)
    purpose: str                 # PURPOSE コメント
    purpose_source: str          # manual / inferred / docstring

    # 融合メトリクス (v0.2.0 新規)
    structural_redundancy: float # 同一構造族内の重複度 (43d cosine)
    purpose_similarity: float    # PURPOSE 間のテキスト類似度
    fusion_verdict: str          # "refactor" / "justified" / "investigate"
```

---

## §3. Phase 計画 (v0.2.0 更新)

### 3.0 Phase 0: 基盤接続 — ✅ 実装済み

`fusion.py` (381行) に FusionEntry + scan_codebase + analyze_orthogonality が実装済み。
直交性スコア 0.924 を実測。

**残課題**: fusion.py が Lēthē の最新成果 (43d/51d, TypeSeq) を取り込んでいない。

### 3.1 Phase 1: 構造的冗長性検出 (v0.2.0 再定義)

v0.1.0 では「同一 CCL 構造族で PURPOSE が異なるコードを検出」だった。
v0.2.0 では **43d 準同型 × PURPOSE 類似度** の交差分析に拡張:

```
入力: コードベース全体の FusionEntry[]

分析:
  1. 43d cosine > 0.9 のペアを抽出 (構造的準同型候補)
     ← Lēthē §17.7b で 344 件発見済み

  2. PURPOSE 類似度を計算 (テキスト embedding cosine)

  3. 交差判定:
     🔴 構造 ≈ 同型 + PURPOSE ≈ 同一 → リファクタリング候補
     ⚠️ 構造 ≈ 同型 + PURPOSE ≠ 同一 → 正当な分離 (抽象化候補)
     🟡 構造 ≠ 同型 + PURPOSE ≈ 同一 → 代替実装 (最適化検討)
     ✅ 構造 ≠ 同型 + PURPOSE ≠ 同一 → 独立
```

### 3.2 Phase 2: 融合検索 (v0.2.0 Triple→Quad Embedding)

Lēthē §18.3 の Triple Embedding に PURPOSE 軸を追加:

| インデックス | 内容 | 検索方法 | 忘却レベル |
|:---|:---|:---|:---|
| code.pkl | CCL + purpose + signature | テキスト embedding | n=0 部分保存 |
| code_ccl.pkl | CCL 式のみ | テキスト embedding | n=1 |
| code_ccl_features.pkl | 43d/51d 特徴量 | コサイン類似度 | n=1〜2 |
| **fusion_index.jsonl** | **43d + PURPOSE** | **構造×目的 交差検索** | **n=1〜2 + 存在** |

### 3.3 Phase 3: 強化型 EPT

```
EPT_enhanced = EPT_base × (1 - structural_redundancy × (1 - purpose_justification))

43d cosine > 0.9 のペアが存在する場合:
  purpose が異なる → purpose_justification = 1.0 → EPT 変化なし
  purpose が同一  → purpose_justification = 0.0 → EPT 低下
```

### 3.4 Phase 4: 構造 × 目的 diff

Lēthē §18.7.2 の構造デグレ検出 + PURPOSE 差分:

```
v1 → v2 diff:
  43d Δ = |v1_43d - v2_43d|        → 構造変更の大きさ
  PURPOSE Δ = sim(p1, p2)          → 目的変更の大きさ

  構造変更 + 目的変更 → 整合的 (リファクタ)
  構造変更 + 目的不変 → 要注意 (構造のみ変更 = バグ？)
  構造不変 + 目的変更 → 要注意 (PURPOSE の誤記？)
```

---

## §4. Lēthē VISION との接続 (v0.2.0 更新)

| Lēthē VISION | 融合での発展 |
|:---|:---|
| §15: LQS = 1.00, R1-R4 | Phase 1 の構造的冗長性検出の基盤。R1 同型群 = 融合分析の入力 |
| §17: 43d 連続特徴量 | Phase 1 の準同型検出 (344 件)。CCL 完全一致だけでなく「ほぼ同型」も融合可能 |
| §17.7b: P25 準同型 | 融合の固有価値: 344 件中、PURPOSE 同一のもの = 真のリファクタリング候補 |
| §18: Triple Embedding | Phase 2 の Quad Embedding への拡張 |
| §19: CPS1'' | §1.3 の方向付け基盤。U_full も CPS1'' に従う |
| §20: TypeSeq (51d) | FusionEntry v2 への型情報統合。51d で準同型検出の精度向上 |

---

## §5. 確信度マトリクス (v0.2.0 更新)

| ID | 命題 | 確信度 | 根拠 |
|:---|:---|:---|:---|
| F1 | CCL-IR と Dendron は同一の随伴構造のインスタンス | **[推定] 88%** | CPS1'' が方向付けの基盤を提供 (§1.3)。Lēthē §19 |
| F2 | 二つの忘却関手は直交する情報を保存する | **[確信] 92%** | Q2 実測スコア 0.924。3,950 関数が構造同型・目的異型 |
| F3 | 融合検索は既存の Triple Embedding より有用 | **[推定] 78%** | P25 (344 件準同型) の PURPOSE 交差で リファクタ候補特定が可能 |
| F4 | 強化型 EPT は従来の EPT より正確 | **[仮説] 55%** | 理論的に妥当。43d 準同型 × PURPOSE 類似度のテストが必要 |
| F5 | Phase 0 → Phase 1 の移行は実装可能 | **[確信] 95%** | fusion.py 実装済み + 43d インデックス実装済み。接続のみ |
| F6 | 構造 × 目的 diff は有用 | **[推定] 72%** | Lēthē §18.7.2 の構造デグレ + PURPOSE の交差は直感的に有用 |
| F7 | 43d 準同型 × PURPOSE 交差は真のリファクタリング候補を特定する | **[推定] 70%** | **新規**。344 件の準同型からフィルタリングの実証が必要 |

---

## §6. Anti-Vision (やらないこと)

- ❌ **Lēthē の VISION を書き換える** — 融合は拡張であり、既存理論の置換ではない
- ❌ **Dendron の VISION を書き換える** — 同上
- ❌ **構造比較で PURPOSE を自動生成** — Dendron §7.4 の原則を尊重。SUGGEST のみ
- ❌ **一般化のための一般化** — Hegemonikón 最優先。fusion は HGK コードベースで検証
- ❌ **論文化を急ぐ** — CCL-IR 単独の論文化 (P5: 65%) が先行すべき
- ❌ **43d を Phase 0 に無理に押し込む** — fusion.py の FusionEntry は段階的に拡張

---

## §7. 実装ロードマップ (v0.2.0 更新)

| フェーズ | 内容 | 依存 | 新規性 (v0.2.0) | 優先度 |
|:---|:---|:---|:---|:---|
| Phase 0.5 | fusion.py に 43d/51d 接続を追加 | ccl_feature_index.py | **Lēthē 最新成果のバックポート** | 🔴 最優先 |
| Phase 1 | 43d 準同型 × PURPOSE 交差分析 | Phase 0.5 | **P25 の 344 件を PURPOSE でフィルタ** | 🔴 最優先 |
| Phase 2 | Quad Embedding (構造×目的 交差検索) | Phase 1 | Triple → Quad の拡張 | 🟠 高 |
| Phase 3 | 強化型 EPT | Phase 1 | 43d 冗長度を EPT に統合 | 🟡 中 |
| Phase 4 | 構造 × 目的 diff | Phase 0.5 | 43d diff + PURPOSE diff | 🟢 低 |

**即着手可能な最小ステップ**:
1. `fusion.py` の `scan_file` に `ccl_feature_vector()` 呼出を追加 → FusionEntry に 43d を持たせる
2. `analyze_orthogonality` を 43d cosine ベースに拡張 (CCL 完全一致 → 43d cosine > 0.9)
3. HGK コードベースで `scan_codebase` + `analyze_orthogonality` を実行し、結果を目視

---

## §8. 関連文書

| 文書 | 場所 | 関係 |
|:---|:---|:---|
| Lēthē VISION v0.30 | [`14_忘却｜Lethe/VISION.md`](file:///c:/Users/makar/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/VISION.md) | 構造検索の理論的基盤 (2635行, P1-P33) |
| Dendron VISION | [`mekhane/dendron/VISION.md`](file:///c:/Users/makar/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/dendron/VISION.md) | 存在証明の理論的基盤 |
| fusion.py | [`mekhane/symphysis/fusion.py`](file:///c:/Users/makar/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/symphysis/fusion.py) | Phase 0 実装 (381行) |
| code_ingest.py | [`mekhane/symploke/code_ingest.py`](file:///c:/Users/makar/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/symploke/code_ingest.py) | Code→CCL + 43d/51d 特徴量 |
| ccl_feature_index.py | [`mekhane/symploke/ccl_feature_index.py`](file:///c:/Users/makar/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/symploke/ccl_feature_index.py) | 43d numpy 直接計算インデックス |
| aletheia.md | [`kernel/aletheia.md`](file:///c:/Users/makar/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/00_核心｜Kernel/A_公理｜Axioms/aletheia.md) | U⊣N 随伴の理論的基盤 |
| R1-R4 ROM | [`rom_2026-03-22_lethe_r1r4_framework.md`](file:///c:/Users/makar/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/c_ROM｜rom/rom_2026-03-22_lethe_r1r4_framework.md) | LQS=1.00 の実証記録 |

---

*Origin: CCL-IR VISION v0.30 (2026-03-24) × Dendron VISION (2026-02-13) の融合*
*Version: 0.2.0 (Lēthē 最新成果統合版)*
*Date: 2026-03-24*
*Changelog: v0.1.0→v0.2.0: Lēthē §11-§20 の成果を統合。43d/51d + 準同型 + CPS1'' + TypeSeq。Phase 計画を Phase 0.5 挿入で再構成*
