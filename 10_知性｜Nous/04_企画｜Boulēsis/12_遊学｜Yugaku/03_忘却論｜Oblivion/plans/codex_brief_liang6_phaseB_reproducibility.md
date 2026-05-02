# Codex 委託 brief: 梁6 Phase B — P5 bug 確定 + 数値検証拡張

## 目的

論文I「力としての忘却」v1.4 の **P5 line 1108 の κ 検証主張**の真偽を確定し、**カテゴリカルシンプレックス Δⁿ での dT=0 数値検証**と**非指数型分布族での反例数値**を追加する。

## 背景 — Phase 1 での調査で確定済みの事実

### 既知の状態

- **Phase A (完了)**: §4.5 を「算術的健全性」に降格、§10 line 1203 の「最大相対誤差 0.11%」誤記を削除
- **`oblivion_field_gaussian.py` の既読確認**: line 1-254 まで全読済み。以下を確認:
  - line 49-63: `curvature_numerical` (有限差分) と `curvature_analytic` (F₁₂ = 6μ/σ) の比較 → 相対誤差 1.4×10⁻¹⁰ 主張の出所
  - line 195-209: `verify_analytic_vs_numerical()` で `max_rel_error = 1.4e-10` を assert (line 208: `assert max_rel_error < 1e-8`)
  - **line 233-239**: `κ = 9Φ₀/(2μ₀²)` を**計算して print する**のみ — assert も期待値比較もない
  - RNG の使用は見当たらない (seed 不要)

### Phase A で flag した P5 bug 疑惑

論文I line 1108:
```
P5 | 自己無撞着幅: κ = 9Φ_c/(2θ₀²) | 数値的 | 検証済 (1.4×10⁻¹⁰)
```

**確認済みの矛盾**:
1. `oblivion_field_gaussian.py` line 235 は `κ = 9 * phi_0 / (2 * mu0**2)` を**計算するが検証していない** (print のみ, assert なし)
2. `1.4×10⁻¹⁰` は F₁₂ 有限差分検証 (line 196-209) の数値であって、κ 検証の数値ではない
3. **記号不一致**: 論文は `Φ_c`, `θ₀` だが、script は `Φ₀ = Φ(0, 1)`, `μ₀` を使う。物理的に同じ量を指しているか未確認

### Phase A で更に発見した問題 (Codex advisor が指摘)

**実験ディレクトリが 2 系統存在**:
- **`10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/`** — 論文§4-§6 の幾何学的数値検証 (`oblivion_field_gaussian.py` 含む)
- **`10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/experiments/`** — 論文§5.5-§5.8 の LLM/SWE-bench 経験実験 (`swe_bench_xi_experiment.py`, `cka_kl_bridge_numerical.py`, `alpha_transition_layer.py` 等)

**本 brief は前者 (Lethe 側) のみを扱う**。後者は §5.5 の Ξ 実験系統であり、梁4 Phase 2 の担当範囲。

**図ファイルの provenance 不整合**:
- `Lethe/experiments/` 配下に **4 つの関連 PNG** が存在: `oblivion_curvature.png`, `alpha_dynamics.png`, `fig1_oblivion_field.png`, `fig2_curvature_F12.png`
- 論文 §4.5 line 193-194 は `fig1_oblivion_field.png`, `fig2_curvature_F12.png` を参照
- しかし `oblivion_field_gaussian.py` の現行版が生成するのは **`oblivion_curvature.png`, `alpha_dynamics.png`** のみ (line 116-117, 171-172)
- `fig1_*`, `fig2_*` は旧版スクリプトの残骸か、手動コピーの可能性が高い (grep で該当保存コードなし)

**Python RNG 確認**: `oblivion_field_gaussian.py` 内に `numpy.random`, `random.*`, `seed` は存在しない。スクリプトは決定論的。**seed 追加は不要**。

## タスク (4 つ、優先度順)

### Task 1 (最優先): P5 bug 真偽確定 (1 時間) 🔍

論文 line 1108 の主張を以下の手順で検証:

1. **論文内のソース特定**: `κ = 9Φ_c/(2θ₀²)` の導出がどこにあるか全文検索せよ
   - Appendix C の変分的安定性関連か?
   - §6.3 の α-遷移層力関連か?
   - 見つからなければその事実を報告 (bug の強い証拠)

2. **記号対応確認**:
   - 論文の `Φ_c`, `θ₀` は script の `phi_0 = Φ(0,1)`, `mu₀` と対応するか?
   - 対応するなら、スクリプトの `κ = 9 * phi_0 / (2 * mu0**2)` は論文の主張 `κ = 9Φ_c/(2θ₀²)` と**記号的に一致する**
   - 対応しないなら、さらに bug の証拠

3. **検証の実在確認**: 独立した κ 検証スクリプト (assertion 付きで κ の値を期待値と比較するもの) が存在するか? `Lethe/experiments/` 全体を grep
   - `grep -rn 'kappa\|κ' --include='*.py'`
   - `grep -rn '9.*phi\|9.*Φ' --include='*.py'`

4. **判定と修正提案**:
   - (a) 独立検証スクリプト発見 + 結果 1.4×10⁻¹⁰ → P5 正当 (稀ケース)
   - (b) 独立検証なし / 結果が異なる → **P5 は bug**, line 1108 の「検証済 (1.4×10⁻¹⁰)」を「予測 (未検証)」に降格する diff を用意
   - (c) 記号対応が不明 → 記号の対応表を作り flag として残す

5. **論文 line 1108 の修正案を diff 形式で提出** (実際の編集は行わない)

### Task 2: Categorical Simplex Δⁿ の dT=0 数値検証 (1 時間) — 新規スクリプト

論文I §5.4 と Appendix B line 1238-1272 が主張する **「指数型分布族では dT = 0 が成立」** を数値的に確認するスクリプトを作成。

**スクリプト仕様**:
- **ファイル名**: `10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/categorical_simplex_dT_check.py`
- **座標系**: 自然パラメータ θ_i = log(p_i / p_{n+1}), i = 1, ..., n
- **対数正規化定数**: ψ(θ) = log(1 + Σ exp(θ_i))
- **Fisher 計量**: g_{ij} = ∂_i ∂_j ψ (symbolic with sympy OR numerical with autograd/jax)
- **Chebyshev 1-form**: T_i = ∂_i log det g (Appendix B line 1262 の式に従う)
- **外微分**: dT = ∂_i T_j - ∂_j T_i を数値計算
- **検証**: |dT| < 機械精度 (1e-10 等)
- **実行次元**: n = 2, 3, 4 で各々検証
- **出力**: print 文で各次元の結果を報告 + assert

**非 RNG スクリプトなので seed 不要**。

### Task 3: 非指数型分布族での反例 (1 時間) — 新規スクリプト

論文I §5.4 line 260 が示唆する **「非指数型分布族では dT ≠ 0」** を具体例で示すスクリプト。

**スクリプト仕様**:
- **ファイル名**: `10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/non_exponential_dT_counterexample.py`
- **候補** (1 つ選択、**Cauchy 推奨**):
  - Cauchy 分布族: 位置 x_0, スケール γ のパラメータ空間
  - Student t 分布族 (自由度ν を動かす版)
- **Fisher 計量の計算**:
  - Cauchy: g は closed form (標準公式あり)
  - 計算方法: symbolic (sympy) or Monte Carlo + autograd
- **T_i = g^{jk} C_{ijk}** を数値計算 (C_{ijk} は Amari-Chentsov 3-tensor)
- **dT を計算し、ゼロでないことを示す**
- **定量的基準**: 典型 parameter 値で |dT| / |T| > 10^{-3} 等の非自明な値
- **実行**: Cauchy の (x_0, γ) = (0, 1), (1, 2), (-1, 0.5) 等の数点で検証

この結果により、論文§5.4 の「dT=0 は指数型分布族 class に特有」という主張が数値的に裏付けられる。

### Task 4: 論文本体への反映提案 (30 分)

以下の修正案を **diff 形式** (before/after) で用意せよ。**実際の編集は行わないこと** — 梁4 Phase 2 Codex と並行稼働中でコンフリクトリスクがあるため。

1. **P5 line 1108 の修正** (Task 1 の結論に応じて)
2. **§5.4 line 260 付近**: Categorical simplex (Task 2) と Cauchy 反例 (Task 3) の結果を引用
3. **Appendix B**: Categorical の数値確認結果を追記 (1-2 行)
4. **新規小節または Appendix E**: Cauchy 反例の記述 (10-20 行程度)

## 出力形式

同じディレクトリの `codex_report_liang6_phaseB_reproducibility.md` に書き出す。

```markdown
# 梁6 Phase B 報告

## 0. 実行サマリー
<Task 1-4 の完了状況、bug 判定結果、作成したスクリプト一覧>

## 1. Task 1: P5 line 1108 bug 調査
### 1.1 ソース探索結果
### 1.2 記号対応表 (Φ_c/θ₀ ↔ Φ₀/μ₀)
### 1.3 独立検証スクリプト探索結果
### 1.4 判定と根拠
### 1.5 line 1108 修正案 (diff)

## 2. Task 2: Categorical Simplex Δⁿ dT=0 検証
### 2.1 スクリプト仕様
### 2.2 n=2, 3, 4 の数値結果
### 2.3 論文 §5.4 / Appendix B への反映案

## 3. Task 3: 非指数型反例
### 3.1 選択した分布族と理由
### 3.2 Fisher 計量の計算方法
### 3.3 dT ≠ 0 の数値結果
### 3.4 論文への反映案

## 4. Task 4: 論文反映提案 (統合 diff)

## 5. 残された open problem (if any)
```

## 制約

- **時間**: 3-4 時間で収める
- **コンフリクト回避**: 論文本体の編集は**行わない** — 提案のみ。梁4 Phase 2 Codex が並行稼働中
- **SOURCE 厳格**: line 番号を必ず明示
- **実行検証**: Task 2, 3 のスクリプトは**実際に実行して結果を確認**する (ドライラン禁止)
- **bug 報告歓迎**: Tolmetes は「バイブコーディング」前提
- **言語**: 日本語
- **触らない**: `§4.5`, `§10`, `§6.7-§6.8`, `Appendix B` 本体 (梁5, 梁6 Phase A, 梁4 Phase 2 の担当範囲)

## 参考ファイル (この順で読むこと)

1. **論文 v1.4**: `10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/series/論文I_力としての忘却_草稿.md`
   - §4.5 line 183-200 (現状の数値検証セクション)
   - §5.4 line 256-262 (dT=0 主張の境界)
   - §9 line 1100-1115 (P5 を含む予測一覧テーブル)
   - Appendix B line 1234-1291 (カテゴリカル計算)
   - Appendix C line 1291-1389 (Φ=0 安定性、κ の可能な出所)
2. **`oblivion_field_gaussian.py`**: `10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/oblivion_field_gaussian.py` (全 254 行)
3. 梁5 Codex report: `plans/codex_report_g_alpha_literature.md` (Option C 採用の背景)
4. 梁4 Phase 1 Codex report: `plans/codex_report_liang4_proxy_estimator.md` (Appendix D の定量化への接続)

## 補足

- **Lethe 側のみ扱う**: `Oblivion/experiments/` は梁4 Phase 2 の担当
- **2 新規スクリプトは `Lethe/experiments/` に作成**: categorical と Cauchy の検証コード
- **論文 v1.4** 以降で本タスクが完了すれば、論文の数値主張は「F₁₂ 解析の健全性 (§4.5)」「Δⁿ での dT=0 (Task 2)」「Cauchy での dT≠0 反例 (Task 3)」「P5 の正しい扱い (Task 1)」の 4 点が整合して並ぶ

## Codex advisor (前回) の警告への対応

この brief は以下の警告をすべて反映済み:

- **N-01**: `oblivion_field_gaussian.py` を全読 (line 1-254) した上で書いている。script 内の κ 計算 (line 235) と F₁₂ 検証 (line 196-209) の位置を事前確認済み
- **N-05 (1)**: 実験ディレクトリが 2 系統あることを明記し、本タスクの範囲を Lethe 側に限定
- **N-05 (2)**: 論文参照 fig1/fig2 と script 出力の provenance 不整合を**既知の flag**として記述。seed 追加は不要 (RNG なし) として除外
- **N-08 (1)**: Step 数を 6 → 4 に圧縮、reproducibility package 全体の整備は撤回。核心 (P5 bug 確定 + 数値検証 2 本) に絞る
- **N-08 (2)**: 「seed 追加」を cargo-cult として削除。RNG を使うスクリプトだけが seed 対象
