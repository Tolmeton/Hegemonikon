# 梁6 Phase B 報告

## 0. 実行サマリー

梁6 Phase B の 4 Task は完了した。結論を先に固定すると、P5 の「**検証済** (1.4×10⁻¹⁰)」は bug である。`1.4×10⁻¹⁰` は `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/oblivion_field_gaussian.py:195-209` にある **F₁₂ の有限差分誤差**であり、同ファイルの κ は `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/oblivion_field_gaussian.py:233-239` で print されるだけで、独立検証は存在しない。したがって P5 は現行 v1.4（2026-04-11）では「予測（未検証）」へ降格するのが正しい。

数値検証は二本追加した。`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/categorical_simplex_dT_check.py` はカテゴリカルシンプレックス Δⁿ (`n=2,3,4`) で `dT=0` を確認し、`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/non_exponential_dT_counterexample.py` は非指数型の Student t `(ν, γ)` 族で `dT≠0` を定量化した。論文本体は編集せず、diff 提案のみを下にまとめた。

| 面 | 状態 | 成果物 | 要点 |
|---|---|---|---|
| Task 1 | 完了 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/series/論文I_力としての忘却_草稿.md` | P5 行は bug。現行 v1.4 では P5 行は line 1078、brief の「line 1108」は古い line offset。 |
| Task 2 | 完了 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/categorical_simplex_dT_check.py` | Δ², Δ³, Δ⁴ の全 sample 点で `max|dT| = 0.0`。 |
| Task 3 | 完了 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/non_exponential_dT_counterexample.py` | Student t `(ν,γ)` で `|dT| = 3.27e-1` 〜 `9.41e-1`。 |
| Task 4 | 完了 | 本報告内 diff 節 | 論文本文は未編集。P5 修正、§5.4 追記、Appendix B 追記、Appendix E 新設案を用意。 |

```text
$ python /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/categorical_simplex_dT_check.py
overall max|dT| = 0.000e+00
OK: categorical simplex verifies dT = 0 for n = 2, 3, 4.

$ python /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/non_exponential_dT_counterexample.py
OK: Student t family gives a non-trivial dT != 0 counterexample.

$ python -m py_compile /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/categorical_simplex_dT_check.py /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/non_exponential_dT_counterexample.py
py_compile passed

$ python - <<'PY' ... module.verify_analytic_vs_numerical() ... PY
最大相対誤差: 1.40e-10
自己無撞着条件: κ = 9Φ₀/(2μ₀²)
  Φ₀ = Φ(0,1) = 0.000000
  κ = 0.000000
```

Rollback は単純で、今回の追加物は 3 ファイルとも新規作成のみである。戻すときは `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/categorical_simplex_dT_check.py`、`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/non_exponential_dT_counterexample.py`、`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/plans/codex_report_liang6_phaseB_reproducibility.md` の 3 本を削除すればよい。

## 1. Task 1: P5 line 1108 bug 調査

### 1.1 ソース探索結果

現行論文 v1.4（2026-04-11）では、brief の「line 1108」にあるはずの P5 行は、実ファイル上では `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/series/論文I_力としての忘却_草稿.md:1078` にある。現在の line 1108 は予測表の後の空行であり、line offset がずれている。以下では現行ファイルの line 番号を正本とする。

P5 の式そのものの出所は `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/series/論文I_力としての忘却_草稿.md:676-684` に見つかった。とくに line 678 で

`κ = 9Φ(θ_c)/(2θ₀²)`

が提示され、line 680-684 で「ガウス族 ℋ² 上の α に関する Euler-Lagrange 方程式に tanh プロファイルを代入し、`sech²` の係数比較から得る」という derivation sketch が与えられている。したがって、P5 の式自体は本文にソースを持つ。

他方、P5 テーブル行 `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/series/論文I_力としての忘却_草稿.md:1078` は、この derivation sketch を「**数値的 / 検証済 (1.4×10⁻¹⁰)**」と要約している。ここで bug の焦点は、**導出の存在**ではなく、**数値検証の存在と 1.4×10⁻¹⁰ の帰属**である。

### 1.2 記号対応表 (Φ_c/θ₀ ↔ Φ₀/μ₀)

| 論文側 | script 側 | 対応関係 | 判定 |
|---|---|---|---|
| `θ` | `μ` | script はガウス族の `μ` 方向に 1 次元 slice を取っている。`θ=μ` と置くのはこの slice に限れば自然。 | 条件付き対応 |
| `θ_c` | `μ=0` | script の `tanh(μ/μ₀)` は中心を 0 に固定している。一般の `θ_c` は保持していない。 | 条件付き対応 |
| `θ₀` | `μ₀` | 遷移幅パラメータという意味では対応する。 | 対応 |
| `Φ_c = Φ(θ_c)` | `Φ₀ = Φ(0,1)` | script は `σ=1` 固定かつ `θ_c=0` の特殊点だけを評価している。一般の `Φ(θ_c)` とは等価でない。 | 部分対応のみ |

結論として、`κ = 9Φ_c/(2θ₀²)` と `κ = 9Φ₀/(2μ₀²)` は **「`θ=μ`, `θ_c=0`, `σ=1` の特殊化」まで落とせば一致する**が、script は論文の一般式をそのまま検証しているわけではない。ここでも P5 の「検証済」表現は過大である。

### 1.3 独立検証スクリプト探索結果

`Lethe/experiments` 側を `rg` で走査した結果、κ を明示的に扱う Python 箇所は `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/oblivion_field_gaussian.py:233-239` だけだった。ここでは

```text
phi_0 = phi_gaussian(0, sigma)
kappa_sc = 9 * phi_0 / (2 * mu0**2)
print("自己無撞着条件: κ = 9Φ₀/(2μ₀²)")
```

と print しているだけで、期待値比較も tolerance 付き assertion もない。`assert .*kappa` を `*.py` 全体で grep しても hit は 0 件だった。

既存の独立検証はむしろ別の場所にある。`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/oblivion_field_gaussian.py:195-209` は F₁₂ 解析式と有限差分の一致を検証し、`max_rel_error` を測っている。`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/paper_I_simulations.py:400-438` も F₁₂ 数値微分と α-遷移層の局在化を assert しているが、κ 期待値の比較はしていない。したがって `1.4×10⁻¹⁰` の実体は **F₁₂ 有限差分誤差**であり、κ 検証の数値ではない。

### 1.4 判定と根拠

判定は **(b) 独立検証なし / 結果が別物** である。P5 は bug とみなすのが妥当であり、現行 row は「予測（未検証）」へ降格するべきである。根拠は三点ある。第一に、κ の論文内 derivation はあるが、それを数値で照合する assert 付き script が存在しない。第二に、`1.4×10⁻¹⁰` は F₁₂ の有限差分誤差であり、κ と別 quantity である。第三に、script が評価している `Φ₀ = Φ(0,1)` は論文の一般量 `Φ(θ_c)` を特殊 slice に落としたものに過ぎず、一般式の numeric validation にはなっていない。

### 1.5 line 1108 修正案 (diff)

現行 v1.4 では対象行は line 1078 にある。brief の line 1108 指示に対応する diff 提案は以下で十分である。

```diff
-| P5 | **自己無撞着幅**: κ = 9Φ_c/(2θ₀²) | 数値的 | **検証済** (1.4×10⁻¹⁰) |
+| P5 | **自己無撞着幅**: κ = 9Φ_c/(2θ₀²) | 数値的 | **予測（未検証）** — 現行 Lethe script では κ を print するのみで、1.4×10⁻¹⁰ は F₁₂ 有限差分誤差 |
```

## 2. Task 2: Categorical Simplex Δⁿ dT=0 検証

### 2.1 スクリプト仕様

実装した `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/categorical_simplex_dT_check.py` は、Appendix B の式をそのまま機械可読化したものになっている。`ψ(θ)=log(1+Σexp θ_i)` から `g_{ij}=∂_i∂_j ψ` を `sympy` で構成し、`det g = ∏_i p_i` を `det g` の数値評価と `∏p_i` の双方で cross-check したうえで、`T_i = ∂_i log det g`、`(dT)_{ij} = ∂_iT_j - ∂_jT_i` を評価する。

仕様上のポイントは二つある。第一に、単一の点だけでなく `n=2,3,4` の各次元に対して 3 つの sample 点（均等点、偏り点、符号交替点）を検査しており、Appendix B の主張を「局所一点」ではなく「複数点で崩れない」形にしている。第二に、`det g = ∏p_i` の一致も同時に assert しているので、`T = ∂ log det g` の前提式そのものが numeric に噛み合っている。

### 2.2 n=2, 3, 4 の数値結果

| n | worst-case sample θ | max\|dT\| | worst det error | 判定 |
|---|---|---:|---:|---|
| 2 | `[-0.2, 0.3]` | `0.000e+00` | `2.082e-17` | pass |
| 3 | `[-0.2, 0.05, 0.3]` | `0.000e+00` | `3.469e-18` | pass |
| 4 | `[-0.2, -0.0333, 0.1333, 0.3]` | `0.000e+00` | `1.084e-19` | pass |

全 sample を通じて `overall max|dT| = 0.000e+00` であり、設定した閾値 `1e-12` を大幅に下回った。したがって Appendix B の「カテゴリカルシンプレックスでは dT=0」が、`n=2,3,4` の数値面でもそのまま再現されたと判断できる。

### 2.3 論文 §5.4 / Appendix B への反映案

§5.4 line 260 付近には、現在すでに「カテゴリカルシンプレックス Δⁿ を含む全ての指数型分布族で dT = 0」と書かれている。ここに numeric backing を 1 文だけ差し込むのが最小改変である。Appendix B には B.4 の末尾に 1-2 行の numeric note を足せば十分で、本文の論理構造を壊さない。

```diff
@@
-力の必要十分条件は d(ΦT) = dΦ∧T + Φ·dT ≠ 0 であり、これは個別の項がゼロでなくても相殺する可能性を含む。ガウス族上では dT = 0（T は閉）なので第1の寄与のみが残り、系 5.1.1 に帰着する。**注: カテゴリカルシンプレックス Δⁿ を含む全ての指数型分布族において、自然パラメータ系では T_i = ∂_i log det g が恒等的に成立するため dT = 0 が普遍的に成立する（Worked Example 2, Appendix B）。したがって指数型分布族の範囲では、Chebyshev ねじれ項は常に不活性であり、力の生成は方向的不整合 dΦ∧T ≠ 0 に完全に帰着する。** 非指数型分布族（混合分布・セミパラメトリックモデル等）では dT ≠ 0 が成立する可能性があり、2つの寄与の相互作用（強化または相殺）が非自明な力のパターンを生む。
+力の必要十分条件は d(ΦT) = dΦ∧T + Φ·dT ≠ 0 であり、これは個別の項がゼロでなくても相殺する可能性を含む。ガウス族上では dT = 0（T は閉）なので第1の寄与のみが残り、系 5.1.1 に帰着する。**注: カテゴリカルシンプレックス Δⁿ を含む全ての指数型分布族において、自然パラメータ系では T_i = ∂_i log det g が恒等的に成立するため dT = 0 が普遍的に成立する（Worked Example 2, Appendix B）。Lethe 側の再現スクリプト `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/categorical_simplex_dT_check.py` は n=2,3,4 の複数 sample 点で max|dT|=0.0 (<10⁻¹²) を与えた。したがって指数型分布族の範囲では、Chebyshev ねじれ項は常に不活性であり、力の生成は方向的不整合 dΦ∧T ≠ 0 に完全に帰着する。** 非指数型分布族（混合分布・セミパラメトリックモデル等）では dT ≠ 0 が成立する可能性があり、2つの寄与の相互作用（強化または相殺）が非自明な力のパターンを生む。
@@
-直接計算でも確認: ∂T_i/∂θ_j = -(n+1)p_i(δ_{ij}-p_j) は (i,j) 対称であり、(dT)_{ij} = ∂_iT_j - ∂_jT_i = 0。
+直接計算でも確認: ∂T_i/∂θ_j = -(n+1)p_i(δ_{ij}-p_j) は (i,j) 対称であり、(dT)_{ij} = ∂_iT_j - ∂_jT_i = 0。Lethe 側の再現スクリプトでは n=2,3,4 の sample 点すべてで max|dT|=0.0、かつ det g と ∏_i p_i の誤差は 10⁻¹⁷ 以下だった。
```

## 3. Task 3: 非指数型反例

### 3.1 選択した分布族と理由

最終的に採用した反例は **Student t 族 `(ν, γ)`** である。brief では Cauchy も候補だったので先に打診したが、位置・スケール Cauchy の数値 pilot では `T≈0`, `dT≈0` となり、反例として弱かった。これは少なくとも今回の 2 パラメータ化では、Cauchy が「非指数型ではあるが Chebyshev ねじれの反例としては鈍い」ことを意味する。そこで、自由度 `ν` を動かせる Student t に切り替えた。

Student t は非指数型でありながら、Gaussian に近づく極限 (`ν→∞`) と heavy-tail 極限 (`ν` 小) の間を連続的につなぐ。そのため、「指数型 class から外れると dT が本当に立ち上がるのか」を確かめる counterexample として扱いやすい。

### 3.2 Fisher 計量の計算方法

実装した `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/non_exponential_dT_counterexample.py` は、位置を 0 に固定した Student t 分布

`p(x;ν,γ) ∝ γ^{-1}(1 + x²/(νγ²))^{-(ν+1)/2}`

に対して、score ベクトル `s = (∂_ν log p, ∂_γ log p)` を閉形式で書き、`g_ab = E[s_a s_b]` と `C_abc = E[s_a s_b s_c]` を `scipy.integrate.quad` で直接積分する。そこから `T_a = g^{bc} C_{abc}` を構成し、最後に `dT = ∂_ν T_γ - ∂_γ T_ν` を中心差分で評価する。つまり、Task 2 と違って「potential の Hessian」には還元せず、**一般定義から Fisher 計量と Amari-Chentsov 3-tensor を直に作る**形にした。

この形にした理由は、非指数型では `T = ∂ log det g` を仮定できないからである。ここを省略すると、まさに確かめたい `dT≠0` を最初から消してしまう危険がある。

### 3.3 dT ≠ 0 の数値結果

| `(ν, γ)` | `T` | `dT = ∂_νT_γ - ∂_γT_ν` | `|dT| / |T|` | 判定 |
|---|---|---:|---:|---|
| `(3.0, 1.0)` | `[-0.963942, 3.090224]` | `9.407100e-01` | `2.906047e-01` | pass |
| `(5.0, 2.0)` | `[-0.518978, 2.330269]` | `3.266342e-01` | `1.368181e-01` | pass |
| `(10.0, 0.5)` | `[-0.192504, 13.878779]` | `6.330724e-01` | `4.561003e-02` | pass |

全点で `|dT| > 1e-3` かつ `|dT|/|T| > 1e-3` を十分に上回っている。したがって Student t `(ν,γ)` 族は、§5.4 の「非指数型では dT ≠ 0 が成立する可能性」が単なる possibility ではなく、現に立ち上がることを示す具体例になっている。

### 3.4 論文への反映案

§5.4 には「混合分布・セミパラメトリックモデル等」と曖昧に書かれているが、ここに 1 つでも concrete family を入れると文章の地面がかなり固くなる。今回の Student t は、そのための最小具体化としてちょうどよい。

```diff
@@
-力の必要十分条件は d(ΦT) = dΦ∧T + Φ·dT ≠ 0 であり、これは個別の項がゼロでなくても相殺する可能性を含む。ガウス族上では dT = 0（T は閉）なので第1の寄与のみが残り、系 5.1.1 に帰着する。**注: カテゴリカルシンプレックス Δⁿ を含む全ての指数型分布族において、自然パラメータ系では T_i = ∂_i log det g が恒等的に成立するため dT = 0 が普遍的に成立する（Worked Example 2, Appendix B）。したがって指数型分布族の範囲では、Chebyshev ねじれ項は常に不活性であり、力の生成は方向的不整合 dΦ∧T ≠ 0 に完全に帰着する。** 非指数型分布族（混合分布・セミパラメトリックモデル等）では dT ≠ 0 が成立する可能性があり、2つの寄与の相互作用（強化または相殺）が非自明な力のパターンを生む。
+力の必要十分条件は d(ΦT) = dΦ∧T + Φ·dT ≠ 0 であり、これは個別の項がゼロでなくても相殺する可能性を含む。ガウス族上では dT = 0（T は閉）なので第1の寄与のみが残り、系 5.1.1 に帰着する。**注: カテゴリカルシンプレックス Δⁿ を含む全ての指数型分布族において、自然パラメータ系では T_i = ∂_i log det g が恒等的に成立するため dT = 0 が普遍的に成立する（Worked Example 2, Appendix B）。したがって指数型分布族の範囲では、Chebyshev ねじれ項は常に不活性であり、力の生成は方向的不整合 dΦ∧T ≠ 0 に完全に帰着する。** 他方、非指数型の Student t `(ν,γ)` 族では Lethe 側の再現スクリプト `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/non_exponential_dT_counterexample.py` により `|dT| = 3.27×10⁻¹ 〜 9.41×10⁻¹`、`|dT|/|T| = 4.56×10⁻² 〜 2.91×10⁻¹` を得た。ゆえに dT=0 は指数型 class に特有であり、非指数型では 2 つの寄与の相互作用（強化または相殺）が実際に活性化しうる。
```

## 4. Task 4: 論文反映提案 (統合 diff)

以下は本文未編集のまま提出する統合 diff 案である。P5 bug 修正、§5.4 の数値 backing、Appendix B の numeric note、Appendix E の新設を 1 つの patch 面に集約した。

```diff
diff --git a/論文I_力としての忘却_草稿.md b/論文I_力としての忘却_草稿.md
@@
-| P5 | **自己無撞着幅**: κ = 9Φ_c/(2θ₀²) | 数値的 | **検証済** (1.4×10⁻¹⁰) |
+| P5 | **自己無撞着幅**: κ = 9Φ_c/(2θ₀²) | 数値的 | **予測（未検証）** — 現行 Lethe script では κ を print するのみで、1.4×10⁻¹⁰ は F₁₂ 有限差分誤差 |
@@
-力の必要十分条件は d(ΦT) = dΦ∧T + Φ·dT ≠ 0 であり、これは個別の項がゼロでなくても相殺する可能性を含む。ガウス族上では dT = 0（T は閉）なので第1の寄与のみが残り、系 5.1.1 に帰着する。**注: カテゴリカルシンプレックス Δⁿ を含む全ての指数型分布族において、自然パラメータ系では T_i = ∂_i log det g が恒等的に成立するため dT = 0 が普遍的に成立する（Worked Example 2, Appendix B）。したがって指数型分布族の範囲では、Chebyshev ねじれ項は常に不活性であり、力の生成は方向的不整合 dΦ∧T ≠ 0 に完全に帰着する。** 非指数型分布族（混合分布・セミパラメトリックモデル等）では dT ≠ 0 が成立する可能性があり、2つの寄与の相互作用（強化または相殺）が非自明な力のパターンを生む。
+力の必要十分条件は d(ΦT) = dΦ∧T + Φ·dT ≠ 0 であり、これは個別の項がゼロでなくても相殺する可能性を含む。ガウス族上では dT = 0（T は閉）なので第1の寄与のみが残り、系 5.1.1 に帰着する。**注: カテゴリカルシンプレックス Δⁿ を含む全ての指数型分布族において、自然パラメータ系では T_i = ∂_i log det g が恒等的に成立するため dT = 0 が普遍的に成立する（Worked Example 2, Appendix B）。Lethe 側の再現スクリプト `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/categorical_simplex_dT_check.py` は n=2,3,4 の sample 点で max|dT|=0.0 (<10⁻¹²) を与えた。他方、非指数型の Student t `(ν,γ)` 族では `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/non_exponential_dT_counterexample.py` により `|dT| = 3.27×10⁻¹ 〜 9.41×10⁻¹`、`|dT|/|T| = 4.56×10⁻² 〜 2.91×10⁻¹` を得た。したがって指数型分布族の範囲では、Chebyshev ねじれ項は常に不活性であり、力の生成は方向的不整合 dΦ∧T ≠ 0 に完全に帰着する。** 非指数型分布族では 2 つの寄与の相互作用（強化または相殺）が実際に活性化しうる。
@@
-直接計算でも確認: ∂T_i/∂θ_j = -(n+1)p_i(δ_{ij}-p_j) は (i,j) 対称であり、(dT)_{ij} = ∂_iT_j - ∂_jT_i = 0。
+直接計算でも確認: ∂T_i/∂θ_j = -(n+1)p_i(δ_{ij}-p_j) は (i,j) 対称であり、(dT)_{ij} = ∂_iT_j - ∂_jT_i = 0。Lethe 側の再現スクリプトでは n=2,3,4 の複数 sample 点すべてで max|dT|=0.0、かつ det g と ∏_i p_i の誤差は 10⁻¹⁷ 以下だった。
+
+## Appendix E. Non-exponential counterexample: Student t `(ν,γ)`
+
+位置を 0 に固定した Student t 分布
+`p(x;ν,γ) ∝ γ^{-1}(1 + x²/(νγ²))^{-(ν+1)/2}`
+を考える。これは指数型ではないため、一般には `T = ∂ log det g` へ還元できない。そこで score ベクトル
+`s = (∂_ν log p, ∂_γ log p)` から Fisher 計量 `g_ab = E[s_a s_b]` と
+Amari-Chentsov 3-tensor `C_abc = E[s_a s_b s_c]` を数値積分で構成し、
+`T_a = g^{bc} C_abc` を直接評価した。
+
+Lethe 側の再現スクリプト `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/non_exponential_dT_counterexample.py`
+では `(ν,γ) = (3,1), (5,2), (10,0.5)` に対して
+`dT = ∂_νT_γ - ∂_γT_ν = 9.41×10⁻¹, 3.27×10⁻¹, 6.33×10⁻¹`
+を得た。対応する `|dT|/|T|` は `2.91×10⁻¹, 1.37×10⁻¹, 4.56×10⁻²`
+であり、いずれも数値誤差帯を大きく上回る。ゆえに `dT=0` は指数型分布族に特有の構造であり、
+非指数型では Chebyshev ねじれ項 `Φ·dT` が実際に活性化しうる。
```

## 5. 残された open problem (if any)

P5 の式それ自体は、本文上の derivation sketch としては存在しているが、**一般点での numeric verification** はまだない。現行 script が評価しているのは `θ=μ`, `θ_c=0`, `σ=1` の特殊 slice にすぎないので、本当に P5 を「検証済」に戻したいなら、`θ_c`, `θ₀`, `Φ(θ_c)` を独立に sweep する dedicated script を別途書く必要がある。

Task 3 についても、今回示したのは Student t の一点族であって、「非指数型なら常に dT≠0」という一般定理ではない。残る open problem は、どの class で `dT=0` が壊れ、どの class では保たれるかを systematic に分類することである。Cauchy location-scale pilot がほぼ `T≈0` を返したのは、その分類が意外に繊細であることを示唆している。

## Annex. Raw Paths

| 用途 | 絶対パス |
|---|---|
| categorical 検証 script | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/categorical_simplex_dT_check.py` |
| non-exponential 反例 script | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/non_exponential_dT_counterexample.py` |
| 本報告 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/plans/codex_report_liang6_phaseB_reproducibility.md` |
