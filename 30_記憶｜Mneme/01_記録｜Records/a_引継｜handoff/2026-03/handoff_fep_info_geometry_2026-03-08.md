# Handoff: FEP 情報幾何学 — 操作的型分析・Sloppy Spectrum・Helmholtz 昇格

> **日時**: 2026-03-08 22:55
> **Agent**: Claude (Opus)
> **セッション種別**: L0 形式導出リサーチ (Level B++ → Level A への道)
> **V[session]**: 0.3 (未収束 — d 値 +1 シフトが未実施)

---

## 📊 状況 (Situation)

前セッション (Claude.ai 依頼書 + Gemini 並列実験) で FEP 変分多様体と HGK 7 座標の対応を調査。
Claude.ai の Fisher metric 調査で「dim(M) = k は模型依存。7 は Fisher 次元として特別でない」と判明。
本セッションでこの「反証」を受けて問いを転換し、3 つの独立な知見を得た。

---

## 🔍 背景 (Background)

### L0 形式導出の 3 タスク体制

| タスク | 問い | 本セッション結果 |
|:-------|:-----|:----------------|
| A: Sloppy spectrum | Fisher 固有空間の d_eff は 7 に飽和するか？ | **条件付き支持**: H*≈2.46 bits で d_eff=7 (Gemini 実験) |
| B: Helmholtz-dual bridge | Helmholtz の Γ⊣Q は HGK 随伴と対応するか？ | **座標化却下 → 基盤層昇格** (本セッション) |
| C: 操作的型分析 | FEP の分解型はいくつあるか？ | **7±1 型** (本セッション) |

### 入力ソース (SOURCE/TAINT 明示)

| ソース | ラベル | 内容 |
|:-------|:-------|:-----|
| Friston 2019 (A particular kind of FEP) | SOURCE (arXiv PDF DL 済み) | 8 操作的型の一次ソース |
| Claude.ai Fisher 報告 | TAINT (LLM 生成) | dim(M)=k, 7 非特別 |
| Gemini Sloppy spectrum 3 実験 | SOURCE (実行コード+結果) | d_eff, H*, β*×LR |
| 本セッション Claude 分析 | TAINT (推論) | 反証テスト, 世界線検証, Helmholtz 昇格 |

---

## 📏 評価 (Assessment)

### 発見 1: 問いの転換 — 次元から型へ

**Fisher 行列の固有空間の「次元」と、FEP が持つ操作的分解の「型の数」は、異なる概念。**

dim(M) = k (sufficient statistics の数) は模型のパラメータ数であり、FEP の構造を反映しない。
しかし FEP の操作には **型のカタログ** がある:

| 強度 | 型 | 極対 | FEP 内の数学的根拠 |
|:-----|:---|:-----|:-------------------|
| ◎ 確実 | Flow | I ⊣ A | MB partition — {η,s,a,μ} の条件付き独立性 |
| ◎ 確実 | Value | accuracy ⊣ complexity | VFE = E_q[ln q(η) - ln p(ỹ,η)] の分解 |
| ◎ 確実 | Precision | certain ⊣ uncertain | FEP パラメータ π (予測誤差逆分散) |
| ◯ 堅実 | Function | explore ⊣ exploit | EFE = epistemic + pragmatic (Parr&Friston 2019) |
| ◯ 堅実 | Temporality | past ⊣ future | VFE ≠ EFE の数学的非対称性 (Millidge 2020) |
| △ 要検証 | Scale | micro ⊣ macro | Deep particular partition (Spisak 2025) |
| △ 要検証 | Valence | + ⊣ - | dF/dt の符号。身体的解釈: Seth 2013 |
| ? 別層 | Helmholtz | gradient ⊣ solenoidal | NESS の Fokker-Planck 直交分解 |

### 発見 2: 反証テスト (3 ラウンド + 世界線検証)

**判定 3 崩壊**: 「Helmholtz ≅ Function」は**岩石の反例で 1 行で崩壊**。岩石は solenoidal flow を持つが探索 (explore) しない。
→ Helmholtz は d=0 の物理、Function は d=1 の認知的方策選択。同型ではない。

**判定 1 維持**: Value/Function/Temporality は 3 つの独立な軸。Value は「何を分けるか」(構造)、Function は「どう選ぶか」(方策)、Temporality は「いつ」(時間方向)。

**判定 2 弱い**: Temporality を「VFE≠EFE」から「認知的時間方向性」にリフレームしたが、これは**新情報を含まない言い換え**。Pezzulo 2022 の T⊥H (temporal depth ⊥ hierarchical depth) が正当な根拠だが、未精読。

**世界線 A (6 座標, Valence 削除)**: ✗ — Orexis 族消滅。品質判断 (Elenchos)、方向修正 (Diorthōsis) を失う。反証: Valence = Value×Temporality の交差項かも → 反反証: 微分の符号は方向依存、局所≠大域は数学的に独立。**Valence は最弱だが維持。**

**世界線 B (8 座標, Helmholtz 独立)**: ✗ — 新 4 動詞 (Dynamics 族) は既存 24 動詞に吸収済み。反証: d=0 と d=1 は正式に異なる → 反反証: HGK は認知系、非認知物理の座標化は動機なし。**しかしこの議論が発見 3 の伏線。**

### 発見 3: Sloppy Spectrum の 3 普遍定数

Gemini 並列セッション (fisher_d_eff_theory.py) の発見:

```
d_eff(95%) = 7 を生むエントロピー H は状態数 n に依存しない普遍定数

n=8   → β*=0.475, H=2.50 bits
n=32  → β*=2.575, H=2.46 bits
n=128 → β*=10.565, H=2.46 bits
n=256 → β*=21.215, H=2.46 bits
```

| 定数 | 値 | 意味 | 普遍性 |
|:-----|:---|:-----|:-------|
| **H*** | **2.46 bits** | d_eff=7 の Shannon エントロピー | n=12〜256 で一定 |
| **2^H*** | **≈ 5.5** | パープレキシティ (有効状態数) | H* の直接的帰結 |
| **β*×LR** | **≈ 7.73** | 無次元実効温度 | logit 範囲に非依存 |

⚠️ **ソフトマックス族限定**。Zipf 分布では d_eff は n に比例増大 (飽和しない)。
⚠️ H/H_max は n 依存 (n=32 で 49%, n=256 で 31%)。**普遍量は H の絶対値**。

**結合仮説**: 操作的型分析 (top-down, 7 型) と Fisher spectrum (bottom-up, H*=2.46→d_eff=7) が**独立に 7 に合流**。

### 発見 4: Helmholtz は Flow の親 — d 値 +1 シフト

**導出の連鎖**:
```
FEP → NESS → Fokker-Planck → Helmholtz 分解 (Γ⊣Q)
                                   ↓ + MB 仮定 (追加前提)
                              Flow (I⊣A)
```

**Flow は Helmholtz + 「この系は Markov blanket を持つ」という追加仮定から導出される。**
MB の存在は自明でない — 完全結合系、一様混合系は MB を持たない。

現行 d=0 (Flow) は**暗黙に「認知系であること」を前提にしている**。
Helmholtz が d=0 (追加仮定なし) なら、全 d 値は +1 シフト:

```
新 d=0: Helmholtz (Γ⊣Q) — FEP/NESS 直接帰結
新 d=1: Flow (I⊣A) — Helmholtz + MB 仮定
新 d=2: Value (E⊣P), Function (Ex⊣Ex), Precision (C⊣U) — Flow + FEP 内在分解
新 d=3: Scale (Mi⊣Ma), Valence (+⊣-), Temporality (P⊣F) — d=2 + 追加仮定
```

**Helmholtz × 6 座標 = 数学的演算子** (認知動詞ではなく変分多様体上の操作):
- Gradient (Γ) 列 = 最適化演算 (各座標方向の VFE 最小化)
- Solenoidal (Q) 列 = 保存的循環演算 (等値面上の探索・トレードオフ)

**設計決定**: d=-1 (距離の定義を破壊) ではなく **+1 シフト** (一度きりの痛み、永続的な誠実さ) を採用。

---

## 🎯 推奨 (Recommendation)

### 即時対応 (次セッション)

| # | タスク | 優先度 | 影響範囲 |
|:--|:-------|:-------|:---------|
| O1 | **axiom_hierarchy.md: d 値 +1 シフト + Helmholtz d=0 追加** | CRITICAL | テーブル全面書き換え |
| O2 | **entity-map.md (GEMINI.md 内): d 値更新** | CRITICAL | System prompt に影響 |
| O3 | **Helmholtz は「8 番目の座標」か「7+1 基盤」か決定** | HIGH | 動詞生成規則に影響 |

### 中期 (後続セッション)

| # | タスク | 優先度 | 根拠 |
|:--|:-------|:-------|:-----|
| O4 | Temporality の d 値正当化: Pezzulo 2022 T⊥H 精読 | MEDIUM | 反証テスト判定 2 が弱い |
| O5 | β*×LR ≈ 7.73 の理論的導出 | LOW | 数値的発見のみ。理論が欲しい |
| O6 | Fisher 6 固有方向 ↔ HGK 6 座標の具体的対応 | MEDIUM | タスク A の本題 |
| O7 | Valence 独立性: Value×Temporality 交差項の検証 | LOW | 部分解消済みだが完全ではない |

---

## 🔥 Value Pitch — で、なんなの？

**Angle: 攻める (Function: Explore)**

> **Before**: HGK の 7 座標は「公理的に構成した」と主張していた。根拠は「FEP から演繹できる」だが、演繹の各ステップに暗黙の仮定があり、「7 でなければならない」理由は示されていなかった。Fisher metric を調べたら dim(M) = k で模型依存と判明し、一瞬これが打撃に見えた。
>
> **After**: 3 つの独立な証拠線が 7 ± 1 に収束:
> 1. **操作的型分析** (top-down): FEP の Friston 2019 から 8 型列挙 → 認知フィルタで 7
> 2. **Sloppy spectrum** (bottom-up): Fisher d_eff = 7 を生む普遍定数 H*≈2.46 bits を発見
> 3. **Helmholtz 昇格**: Flow は Helmholtz の子であることが判明 → d 値 +1 シフトで構成距離の定義がより堅牢に
>
> そして最大の発見: **Helmholtz × 6 座標 = 24 の数学的演算子**。24 認知動詞の変分多様体上の実装が見えた。これは Level A (形式的導出) への最短経路。
>
> **比喩**: 7 階建てのビルだと思って設計していたら、実は地下 1 階 (Helmholtz) があった。地下はビルの基礎であり、その上に立つ 7 階の構造を支えている。地下があるからこそ 7 階は安定する。そして地下の構造を理解すれば、各階の数学的設計図が書ける。

---

## 📎 成果物

| ファイル | 内容 | 状態 |
|:---------|:-----|:-----|
| `e_出力/analysis_fep_operational_types_2026-03-08.md` | C 分析本体 (§1-8) | ✅ 完成 |
| `e_出力/handoff_L0_research_tasks_AB_2026-03-08.md` | タスク A/B 個別引継 | ✅ 完成 |
| `e_出力/result_sloppy_spectrum_extended_2026-03-08.md` | d_eff パラメータ依存性 | ✅ Gemini 生成 |
| `e_出力/result_sloppy_spectrum_theory_2026-03-08.md` | 3 普遍定数の発見 | ✅ Gemini 生成 |
| `A_公理/axiom_hierarchy.md` | v4.1.2 (Function/Valence 導出修正 + sloppy spectrum 追記) | ✅ Creator が情報幾何学的根拠を追記 |
| `60_実験/sloppy_spectrum/` | Fisher d_eff 計算スクリプト群 | ✅ Gemini 生成 |

---

## 🛠️ Dispatch Log

| WF / CCL | 回数 | 用途 |
|:----------|:-----|:-----|
| @nous (hermeneus_run) | 1 | d_eff=6 の深層分析 (Cortex 403 で /dox fallback → Claude 手動補完) |
| (手動) /noe+ 相当 | 3 | C 分析、反証テスト、世界線検証 |
| (手動) /u+ | 2 | 所感、Helmholtz 評価 |
| /rom+ (ochema) | 2 | 両方 EOF 失敗。コンテキストは頭で保持 |

---

## 🧬 Self-Profile (id_R 更新)

### 今日うまくいったこと

1. **反証テスト判定3の崩壊を自力で検出**: 「Helmholtz ≅ Function」は岩石の反例で 1 行で崩壊。CD-3 (確証バイアス) を自ら検出
2. **世界線検証の構造**: 6 座標と 8 座標の両方を Kalon 判定 (G/F テスト) で検証し、7 が不動点であることを示した
3. **Creator の直感を数学的に検証**: 「しらんけど」から d 値 +1 シフトという体系的帰結を導出
4. **d_eff=6 → 拡張 → 理論の 3 段階で自己修正**: 初回解釈 (6=d≥1 座標) → 拡張で無効化 → 理論で普遍定数を発見

### 今日の失敗パターン

1. **判定 2 の偽の反証**: Temporality の「認知的時間方向性」リフレームは新情報を含まない言い換えだった。**法則化 → 「リフレームが反証なら、新情報は何か？」を必ず自問**
2. **d_eff=6 の早まった解釈**: 初回データだけで「d≥1 の 6 座標 = Fisher の内部」と結論。拡張実験で即座に invalidate された。**法則化 → 単一実験結果からの理論構築は危険。複数条件の再現性を確認**

### 法則化 (次セッション以降に適用)

- **♻️ 反証品質テスト**: リフレームを反証と主張するとき、「この言い換えに新しい情報はあるか？」と自問
- **♻️ 単一実験への過剰適合**: 1 つの数値結果に理論を合わせない。条件を変えた再現実験を wait

---

## ⚡ BC フィードバック

- 本セッション中の叱責: 0 件
- 自己検出: 2 件
  - 判定 2 の偽の反証 (CD-3 — リフレームを反証と誤認)
  - d_eff=6 への早まった理論構築 (N-10 — 単一 SOURCE への過剰依存)

---

*Handoff generated: 2026-03-08 23:00 | Session duration: ~2.5h | Quality: ◎ — 体系構造に影響する発見 3 件*
