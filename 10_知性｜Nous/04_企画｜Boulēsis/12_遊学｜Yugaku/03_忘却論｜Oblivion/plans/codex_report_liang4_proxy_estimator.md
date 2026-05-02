# 梁4 報告: Proxy の estimator 化

## 0. 判定

本タスクの結論は三つある。第一に、§5.5 の理論核として採るべき量は candidate (B) の

$$
\kappa(\theta) := \|d(\Phi T)\|_g^2 = \frac{4}{\alpha^2}\|F\|_g^2
$$

である。これは定理 5.1 のゼロ曲率条件をそのまま定量化した量であり、Appendix D line 1412-1441 のノルム分離と完全に接続する。第二に、§5.5 の経験的 `Ξ` は pointwise な `\kappa(\theta)` そのものではなく、観測設計 `\nu` に沿ったその不均一性

$$
\Xi_{\text{theory}}(\nu) := \operatorname{Var}_{u \sim \nu}[\kappa(\theta_u)]
$$

として再定義するのが最も自然である。これで line 266 の「分散」という直観を保存しつつ、定理 5.1 との断絶を埋められる。第三に、`Ξ_Var / Ξ_Gini / Ξ_CV / Ξ_impl` は raw のままでは同一量ではなく、観測モデルごとの calibrated estimator もしくは lower-bound estimator として書き直す必要がある。

Step 5 は半分だけ閉じる。CKA-based Fisher ratio は projected estimator として定義できるが、chunk coherence と `τ` は estimator ではない。前者は §5.8 line 427-480 が示す fixed-point diagnostic、後者は line 476 が明示する initial condition であり、proxy と呼ぶと理論が逆流する。

注意すべき source anomaly も一つある。現行草稿では `Ξ_theory` が少なくとも三通りに使われている。line 266 では `Var(λ)`、line 321 では `Gini(\bar p_1,\dots,\bar p_6)`、line 348 では `Gini(spec(\Sigma))` である。この overload を解消しない限り、estimator 化は本文内で閉じない。

## 1. Step 1: 理論量 `Ξ_theory` の選択

### 1.1 候補比較

| 候補 | 定義 | 定理 5.1 との関係 | 長所 | 欠点 | 判定 |
|---|---|---|---|---|---|
| (A) 正規化方向整合度 | `|d\Phi \wedge T|_g^2 / (|d\Phi|_g^2 |T|_g^2)` | `d\Phi \wedge T = 0` を `0` に潰す | 次元なし、方向だけを見る | `d\Phi = 0` または `T = 0` で未定義。全保持対照と simplex 中心で壊れる。scale 情報も捨てる | 補助量なら可、主量には不適 |
| (B) 曲率ノルム | `\|d(\Phi T)\|_g^2 = (4/\alpha^2)\|F\|_g^2` | 定理 5.1 をそのまま定量化 | ゼロ曲率条件と直結。`d\Phi \approx 0` の対照条件をそのまま処理できる。Appendix D と整合 | Fisher 計量と `\alpha` に依存するため、cross-system 比較には calibration が要る | 採用 |
| (C) 方向投影 | `|\langle d\Phi, T\rangle_g| / (|d\Phi|_g |T|_g)` | `d\Phi \parallel T` で最大 | 整列の良さだけを見るには明快 | 力がゼロのとき最大になる。heterogeneity 指標ではなく alignment 指標 | 不採用 |

candidate (A) は `\sin^2\theta` であり、candidate (C) は `|\cos\theta|` である。line 315 の全保持対照や Appendix B line 1262 の均等分布点では `d\Phi = 0` または `T = 0` が現れるため、(A)(C) は主指標として不安定である。これに対し (B) はゼロ条件でもそのまま `0` を返す。ゆえに本報告では (B) を local kernel として採る。

### 1.2 採用定義

pointwise な理論核を

$$
\kappa(\theta) := \|d(\Phi T)\|_g^2 = \frac{4}{\alpha^2}\|F\|_g^2
$$

と置く。経験的 `Ξ` は turn, layer, coordinate などの観測単位 `u` を通じて集計されるので、§5.5 で必要なのは `\kappa` の point estimate ではなく、観測設計 `\nu` に沿った heterogeneity である。したがって experiment-level target を

$$
\Xi_{\text{theory}}(\nu) := \operatorname{Var}_{u \sim \nu}[\kappa(\theta_u)]
$$

と定義する。`u` は §5.5 では turn、SWE-bench では trajectory unit、HGK 実装検証では 6 座標である。こうすれば line 266 の「分散」という語を残したまま、line 202-260 の定理 5.1 および Appendix D line 1412-1441 の定量化と接続できる。

指数型分布族では Appendix B line 1264-1272 により `dT = 0` なので、Appendix D line 1412-1430 から

$$
\kappa(\theta)
= \|d\Phi\|_g^2 \|T\|_g^2 - \langle d\Phi, T\rangle_g^2
$$

が成立する。よって `\kappa` は「忘却勾配の大きさ」「Chebyshev 感受性」「両者の斜交性」の積に分解される。

### 1.3 ガウス族での具体計算

SOURCE は §4 line 151-177 と Appendix D line 1412-1430 である。ガウス族では `T = (0, 6/\sigma)`、`g^{-1} = \sigma^2 \operatorname{diag}(1, 1/2)` なので、

$$
\|T\|_g^2 = 18.
$$

異方的忘却 `\Phi_B(\mu,\sigma) = -\log \sigma + (\sigma^2+\mu^2)/2 - 1/2` に対して

$$
\partial_\mu \Phi_B = \mu,\qquad
\partial_\sigma \Phi_B = \sigma - \frac{1}{\sigma},
$$

したがって

$$
\|d\Phi_B\|_g^2
= \sigma^2 \mu^2 + \frac{(\sigma^2-1)^2}{2},
\qquad
\langle d\Phi_B, T\rangle_g
= 3(\sigma^2-1).
$$

よって採用量は

$$
\kappa_B(\mu,\sigma)
= \|d(\Phi_B T)\|_g^2
= \frac{9}{2}\alpha^2 \sigma^2 \mu^2.
$$

これは §4.4 line 177 の `F_{12} = 3\alpha \mu / \sigma` と整合する。`d\Phi_B` の `\mu` 成分がゼロなら力は消え、`|\mu|` と `\sigma` が増えるほど曲率エネルギーは増える。

比較のため、候補 (A)(C) は

$$
\Xi_{\text{loc}}^{(A)}
= \frac{\sigma^2 \mu^2}{\sigma^2 \mu^2 + (\sigma^2-1)^2/2},
\qquad
\Xi_{\text{loc}}^{(C)}
= \frac{|\sigma^2-1|}{\sqrt{2\sigma^2\mu^2 + (\sigma^2-1)^2}}.
$$

となる。`d\Phi = 0` または `T = 0` で壊れないのは (B) だけである。

等方的忘却 `\Phi_A` では §4.4 line 173-177 の通り `\partial_\mu \Phi_A = 0` なので

$$
\kappa_A(\mu,\sigma) = 0.
$$

この sharp dichotomy はそのまま `\Xi_{\text{theory}}(\nu)` のゼロ/非ゼロに持ち上がる。

### 1.4 カテゴリカルシンプレックスでの具体計算

SOURCE は Appendix B line 1238-1272 である。自然パラメータ系で

$$
T_i = 1-(n+1)p_i
$$

かつ `dT = 0` が成立する。したがって

$$
\kappa_{\Delta^n}(p)
= \frac{\alpha^2}{4}
\left(
\|d\Phi(p)\|_g^2 \|T(p)\|_g^2
- \langle d\Phi(p), T(p)\rangle_g^2
\right).
$$

均等分布点 `p_i = 1/(n+1)` では Appendix B line 1262 により `T = 0` であるから

$$
\kappa_{\Delta^n}(p_{\text{unif}})=0.
$$

ここでも (A)(C) は分母が消えて退化するが、(B) はきれいにゼロへ落ちる。これは simplex の中心が「最大エントロピーだが zero-force」という Appendix B の幾何と整合している。

## 2. Step 2: 各経験的 `Ξ` の estimator 化

この節では raw observable と calibrated estimator を区別する。共通の latent quantity は

$$
\kappa_u := \|d(\Phi T)\|_g^2(\theta_u),
\qquad
\Xi_{\text{theory}}(\nu) := \operatorname{Var}_{u \sim \nu}[\kappa_u].
$$

である。以後の `u` は観測単位であり、turn, trajectory unit, layer, coordinate などに応じて変わる。

### 2.1 `Ξ_Var` (`N=416` 統制実験)

SOURCE は line 277-313 である。

**仮定 H1.**  
1. 観測単位は turn `u = t` であり、各 turn は局所パッチ `\theta_t` に対応する。  
2. turn 情報量スコア `Y_t` は

$$
Y_t = \beta_0 + \beta_1 \kappa_t + \varepsilon_t,
\qquad
\mathbb{E}[\varepsilon_t \mid \kappa_t] = 0,
\qquad
\operatorname{Var}(\varepsilon_t)=\sigma_\varepsilon^2 < \infty
$$

を満たす。  
3. 比較する policy 間で compression budget は固定され、`\beta_1` は共通である。  
4. `\kappa_t` と `\varepsilon_t` は i.i.d. にサンプルされ、四次モーメントが有限である。

このとき de-noised variance

$$
\widehat{\Xi}_{\text{Var}}
:=
\frac{1}{\beta_1^2}
\left[
\frac{1}{n-1}\sum_{t=1}^n (Y_t-\bar Y)^2 - \widehat{\sigma_\varepsilon^2}
\right]
$$

を `\Xi_{\text{theory}}(\nu)` の estimator と定義できる。

**bias / variance.** `\widehat{\sigma_\varepsilon^2}` が full-retention control から独立に unbiased 推定されるなら

$$
\mathbb{E}[\widehat{\Xi}_{\text{Var}}] = \Xi_{\text{theory}}(\nu).
$$

plug-in 推定を使う場合も bias は `O(n^{-1})` に留まる。分散は sample variance の標準式より `O(n^{-1})` である。

**命題 V.** H1 のもとで `\widehat{\Xi}_{\text{Var}}` は unbiased であり、`n \to \infty` で consistent である。  
**スケッチ.** 線形観測モデルのもとで `\operatorname{Var}(Y_t)=\beta_1^2 \Xi_{\text{theory}}+\sigma_\varepsilon^2`。したがって noise を引いた sample variance を `\beta_1^2` で割れば target に戻る。

### 2.2 `Ξ_Gini` (SWE-bench, Paper II)

SOURCE は §5.6 line 342-354 である。

**仮定 H1'.**  
1. 観測単位 `u` の正値スコア `W_u` は multiplicative observation model

$$
\log W_u = \mu + \beta \kappa_u + \varepsilon_u,
\qquad
\varepsilon_u \sim \mathcal{N}(0,\sigma_\varepsilon^2)
$$

に従う。  
2. 観測軸は `\Sigma` の固有方向と一致する。もしくは PCA whitening 後に Gini を計算する。  
3. `\kappa_u` の分散が有限で、`n \to \infty` の極限を考える。

このとき `W_u` は lognormal family に入り、` \tau^2 := \beta^2 \Xi_{\text{theory}}(\nu) + \sigma_\varepsilon^2 ` とおけば population Gini は

$$
G_\infty = 2\Phi\!\left(\frac{\tau}{\sqrt{2}}\right)-1
$$

となる。よって calibrated estimator を

$$
\widehat{\Xi}_{\text{Gini}}
:=
\frac{1}{\beta^2}
\left(
2\left[\Phi^{-1}\!\left(\frac{\widehat G_n+1}{2}\right)\right]^2
- \widehat{\sigma_\varepsilon^2}
\right)
$$

と定義できる。

**bias / variance.** `\widehat G_n` は U-statistic 型であり、`G_\infty` の estimator として bias `O(n^{-1})`、variance `O(n^{-1})` を持つ。上の逆写像は滑らかなので、delta method により `\widehat{\Xi}_{\text{Gini}}` も bias `O(n^{-1})`、variance `O(n^{-1})` である。

**命題 G.** H1' のもとで `\widehat{\Xi}_{\text{Gini}}` は asymptotically unbiased かつ consistent である。  
**但し書き.** §5.6 line 346-354 の Schur-Horn 条件を満たさないとき、この estimator が回収するのは full `\Xi_{\text{theory}}` ではなく projected lower bound `\Xi_{\text{theory}}^{\text{diag}} \le \Xi_{\text{theory}}` である。つまり「proxy が悪かった」で逃げるのではなく、「どの basis では lower bound しか見えないか」を明記すべきである。

### 2.3 `Ξ_CV` (SWE-bench 全保持対照)

SOURCE は line 315 と Appendix D line 1390-1441 である。

**仮定 H1''.**  
1. `W_u` は H1' と同じ lognormal observation model に従う。  
2. mean budget `m := \mathbb{E}[W_u]` は policy 間で固定される。  
3. noise baseline `\sigma_\varepsilon^2` は full-retention control から推定可能である。

lognormal family では

$$
\operatorname{CV}^2 = e^{\tau^2} - 1,
\qquad
\tau^2 = \beta^2 \Xi_{\text{theory}}(\nu) + \sigma_\varepsilon^2.
$$

したがって calibrated estimator は

$$
\widehat{\Xi}_{\text{CV}}
:=
\frac{1}{\beta^2}
\left(
\log(1+\widehat{\operatorname{CV}}^2) - \widehat{\sigma_\varepsilon^2}
\right).
$$

**bias / variance.** `\widehat{\operatorname{CV}}^2` 自体は plug-in なので有限標本 bias を持つが、delta method により bias は `O(n^{-1})`、variance は `O(n^{-1})` である。

**命題 C.** H1'' のもとで `\widehat{\Xi}_{\text{CV}}` は asymptotically unbiased かつ consistent である。特に no-forgetting control では `\kappa_u \approx 0` が全 unit で成立するので `\Xi_{\text{theory}}(\nu) \approx 0`、したがって `\widehat{\Xi}_{\text{CV}} \approx 0` が予測される。

### 2.4 `Ξ_impl` (`N=229` CCL 式, 6 座標 Gini)

SOURCE は line 317-340 と §5.6 line 342-354 である。

**仮定 H1'''.**  
1. 観測単位は expression `j=1,\dots,N`、座標 `k \in \{1,\dots,6\}`。  
2. omission indicator `M_{jk} \in \{0,1\}` は

$$
M_{jk} \sim \operatorname{Bernoulli}(p_k),
\qquad
\operatorname{logit}(p_k) = a + b\kappa_k
$$

に従う。ここで `\kappa_k := \mathbb{E}[\kappa_u \mid \text{coordinate}=k]` は coordinate-level curvature energy である。  
3. 6 座標の basis が principal directions に一致する場合に限り equality が成立し、一致しない場合は §5.6 の lower-bound situation になる。

各座標の omission rate estimator は

$$
\widehat p_k = \frac{1}{N}\sum_{j=1}^N M_{jk}.
$$

small-spread regime で `p_0 := (1/6)\sum_k p_k` の近傍に線形化すると

$$
p_k
=
p_0 + b\,p_0(1-p_0)(\kappa_k-\bar\kappa) + O((\kappa_k-\bar\kappa)^2),
$$

ゆえに Gini は first order で `\sqrt{\operatorname{Var}_k(\kappa_k)}` に比例する。したがって

$$
\widehat{\Xi}_{\text{impl}}
:=
c_{\text{impl}}(p_0)^{-2}\,
\operatorname{Gini}(\widehat p_1,\dots,\widehat p_6)^2
$$

を coordinate-level target

$$
\Xi_{\text{theory}}^{(6)}
:=
\operatorname{Var}_{k=1,\dots,6}[\kappa_k]
$$

の estimator と定義できる。

**bias / variance.** `\widehat p_k` は unbiased で `\operatorname{Var}(\widehat p_k)=p_k(1-p_k)/N = O(N^{-1})`。Gini は滑らかな対称関数なので multivariate delta method により `\widehat{\Xi}_{\text{impl}}` は bias `O(N^{-1})`、variance `O(N^{-1})` を持つ。

**命題 I.** H1''' のもとで `\widehat{\Xi}_{\text{impl}}` は coordinate-level heterogeneity `\Xi_{\text{theory}}^{(6)}` の consistent estimator である。basis alignment が壊れている場合は §5.6 line 346-354 により lower bound estimator に降格する。

## 3. Step 3: §5.5 予測の書き換え

以下では line 266-275 の差し替え候補を、主張の ambition を変えて三段階用意する。推奨は Pattern B である。

### Pattern A: Conservative

```markdown
**定義.** 局所忘却曲率密度を
$$
\kappa(\theta) := \|d(\Phi T)\|_g^2 = \frac{4}{\alpha^2}\|F\|_g^2
$$
とおく。観測設計 $\nu$ に対し、理論的不均一性を
$$
\Xi_{\text{theory}}(\nu) := \operatorname{Var}_{u\sim\nu}[\kappa(\theta_u)]
$$
と定義する。§5.5 で用いる $\Xi_{\text{Var}}, \Xi_{\text{Gini}}, \Xi_{\text{CV}}, \Xi_{\text{impl}}$ は、それぞれ異なる観測モデルの下で $\Xi_{\text{theory}}(\nu)$ の estimator もしくは lower-bound estimator とみなす。

**予測.** 忘却を操作しない系では $\kappa(\theta)\approx 0$ であり、したがって $\Xi_{\text{obs}}\approx 0$ が期待される。逆に、task-relevant structure に沿って忘却が不均一化される系では、$\Xi_{\text{obs}}$ の増大が task persistence $P$ の増大と共起することが期待される。
```

### Pattern B: Balanced / 推奨

```markdown
**定義.** 局所忘却曲率密度を
$$
\kappa(\theta) := \|d(\Phi T)\|_g^2 = \frac{4}{\alpha^2}\|F\|_g^2
$$
とおく。観測設計 $\nu$ に対し、理論的不均一性を
$$
\Xi_{\text{theory}}(\nu) := \operatorname{Var}_{u\sim\nu}[\kappa(\theta_u)]
$$
と定義する。§5.5 の $\Xi_{\text{Var}}, \Xi_{\text{Gini}}, \Xi_{\text{CV}}, \Xi_{\text{impl}}$ は、仮定 H1-H1''' のもとで $\Xi_{\text{theory}}(\nu)$ の estimator または lower-bound estimator である。

**予測（選択的忘却定理, estimator 版）.** 忘却を操作しない系では $d\Phi\approx 0$ であるから $\kappa\approx 0$、したがって $\Xi_{\text{obs}}\approx 0$ が予測される。逆に、task-relevant structure と整列した忘却により $\kappa$ の heterogeneity が増大する系では、sufficiently large $n$ と H1-H1''' の成立のもとで
$$
\operatorname{Corr}(\Xi_{\text{obs}}, P) > 0
$$
が期待される。
```

### Pattern C: Ambitious

```markdown
**定義.** 局所忘却曲率密度を
$$
\kappa(\theta) := \|d(\Phi T)\|_g^2 = \frac{4}{\alpha^2}\|F\|_g^2
$$
とおき、観測設計 $\nu$ に対する理論的不均一性を
$$
\Xi_{\text{theory}}(\nu) := \operatorname{Var}_{u\sim\nu}[\kappa(\theta_u)]
$$
と定義する。

**命題.** 仮定 H1-H1''' のもとで、各観測 proxy $\Xi_{\text{obs}}$ は
$$
\Xi_{\text{obs}} = \Xi_{\text{theory}}(\nu) + O_p(n^{-1/2})
$$
あるいは projected lower bound
$$
\Xi_{\text{obs}} = \Xi_{\text{theory}}^{\text{proj}}(\nu) + O_p(n^{-1/2}), \qquad
\Xi_{\text{theory}}^{\text{proj}}(\nu) \le \Xi_{\text{theory}}(\nu)
$$
を満たす。定理 5.1 と Appendix D より、$|d(\Phi T)|_g$ が task-relevant structure 上で有意に変動する系では
$$
\operatorname{Corr}(\Xi_{\text{theory}}(\nu), P) > 0
$$
が成立し、したがって sufficiently large $n$ では
$$
\operatorname{Corr}(\Xi_{\text{obs}}, P) > 0
$$
が期待される。
```

## 4. Step 4: SWE-bench 全保持対照の再解釈

SOURCE は line 315 と `n=500` である。

line 315 の観測値 `r(\Xi_{\text{CV}}, P) = -0.007` は、「理論の失敗」ではなく no-forgetting control の成功確認として読める。理由は simple である。忘却を操作しない系では `d\Phi \approx 0`、ゆえに Appendix D line 1438-1441 の定量版により `\kappa_u \approx 0` が全 unit で成り立つ。したがって heterogeneity も

$$
\Xi_{\text{theory}}(\nu) = \operatorname{Var}_\nu[\kappa_u] \approx 0
$$

へ落ちる。`Ξ_CV` はその estimator だから、相関もゼロ近傍へ落ちるのが予測である。

Fisher `z` 変換で有限標本誤差範囲を計算すると

$$
z_{\text{obs}} = \operatorname{arctanh}(-0.007) = -0.007000,
\qquad
\operatorname{SE}_z = \frac{1}{\sqrt{500-3}} = 0.044856.
$$

したがって `\pm 2\sigma` 帯域は

$$
z \in [-0.096712,\; 0.082712].
$$

これを `r` へ戻すと

$$
r \in [-0.096412,\; 0.082524].
$$

観測値 `-0.007` はこの有限標本帯域のほぼ中心にあり、`0` から実質的に区別できない。よって line 315 の結果は

> 忘却操作なし (`d\Phi \approx 0`) では `\Xi_{\text{theory}} \approx 0` であり、`Corr(\Xi_{\text{CV}}, P)` は `0` 近傍に落ちる

という予測と整合的である。ここでは「有意な正相関が見えなかった」のではなく、「ゼロ近傍へ落ちるはずの相関が本当にゼロ近傍に落ちた」と読むべきである。

## 5. Step 5: CKA & coherence

### 5.1 CKA-based 曲率推定

§5.7-§5.8 の CKA 系データは完全には閉じないが、partial estimator としては定義できる。必要なのは次の仮定である。

**仮定 H_CKA.**  
1. depth index `l` が 1 次元の観測座標として扱える。  
2. `\Phi(l) := 1-\operatorname{CKA}(h_l,h_0)` が layerwise forgetting potential の proxy である。  
3. E10 line 369-417 の `image(G)` が Chebyshev-sensitive subspace の projection を与える。  
4. residual subspace は isotropic で、projected Fisher ratio が principal curvature heterogeneity を支配する。

このとき projected local kernel を

$$
\kappa_l^{\text{CKA}}
:=
\left\|
\Pi_{\operatorname{image}(G)}\, d\Phi_l \wedge \widehat T_l
\right\|_g^2
$$

で定義し、top-`k` Fisher ratio concentration を `\Xi_{\text{theory}}^{\text{proj}}` の lower-bound estimator とみなせる。

ただし現行草稿には `\widehat T_l` の独立な estimator が存在しない。§5.7 は `\Phi` 側の proxy は持っているが、Chebyshev 形式側の proxy は持っていない。したがって CKA route は

> `d\Phi` の projected proxy はあるが、`d(\Phi T)` 全体の estimator にはまだなっていない

という意味で partial closure に留まる。

### 5.2 Chunk coherence

chunk coherence は estimator にしてはいけない。理由は §5.7 line 386-397 と §5.8 line 427-480 が既に与えている。

1. image(G) 方向を消すと coherence は上がるが、これは意味的改善ではなく chunk collapse である。  
2. line 427-480 が示すように coherence は `τ` に対してほぼ不変であり、fixed point の quality に近い量である。  
3. estimator に必要な「curvature heterogeneity が増えると coherence も単調に増減する」という identifiability がない。

ゆえに coherence は

> `\Xi_{\text{theory}}` の estimator ではなく、G∘F dynamics の post-distillation diagnostic

として位置づけるべきである。

### 5.3 `τ`

`τ` も proxy ではない。§5.8 line 476 は明確で、`τ` は initial partition を決める intervention parameter であり、fixed-point quantity の estimator ではない。本文では `τ` を

> experimental knob / instrument variable

として扱い、`Ξ` と同列の proxy 語彙から外すのがよい。

## 6. 論文本体への反映提案

### 6.1 最小差し替えの核

| 場所 | 現状 | 提案 |
|---|---|---|
| line 266-275 | `Ξ = Var(λ)` と `Corr(Ξ,P)>0` が無媒介に置かれている | Pattern B に差し替える |
| line 315 | no-forgetting control が単なる備考 | Fisher `z` の有限標本帯域を 1 文追加して「成功確認」に昇格させる |
| line 321 | `Ξ_theory = Gini(\bar p_1,\dots,\bar p_6)` | `Ξ_{\text{coord,theory}}` など別名へ改名 |
| line 348 | `Ξ_{\text{theory}}|_{\text{top-d}}` | `Ξ_{\text{spec,proj}}` など spectral lower-bound 名へ改名 |

### 6.2 推奨 diff

```diff
@@ line 266-275 @@
- **定義.** 忘却の不均一性 $\Xi = \text{Var}(\lambda)$（パラメータ間の保持率分散）。
- 
- - $\Xi = 0 \iff$ 等方的忘却 $\implies F_{ij} = 0$（定理 5.1）
- - $\Xi > 0 \iff$ 異方的忘却 $\implies F_{ij} \neq 0$（一般に）
- 
- **予測（選択的忘却定理）.** LLM のアテンション層において、タスク持続性 P（構造化された問題解決を維持する能力）は $\Xi$ と正に相関する:
- 
- $$\text{Corr}(\Xi, P) > 0$$
- 
- これは数学的な曲率 $F_{ij}$（統計多様体上で測定）と経験的な観測量（ニューラルネットワーク上で測定）を接続する。
+ **定義.** 局所忘却曲率密度を
+ $$
+ \kappa(\theta) := \|d(\Phi T)\|_g^2 = \frac{4}{\alpha^2}\|F\|_g^2
+ $$
+ とおく。観測設計 $\nu$ に対し、理論的不均一性を
+ $$
+ \Xi_{\text{theory}}(\nu) := \operatorname{Var}_{u\sim\nu}[\kappa(\theta_u)]
+ $$
+ と定義する。§5.5 で用いる $\Xi_{\text{Var}}, \Xi_{\text{Gini}}, \Xi_{\text{CV}}, \Xi_{\text{impl}}$ は、仮定 H1-H1''' のもとで $\Xi_{\text{theory}}(\nu)$ の estimator または lower-bound estimator である。
+
+ **予測（選択的忘却定理, estimator 版）.** 忘却を操作しない系では $d\Phi\approx 0$ であるから $\kappa\approx 0$、したがって $\Xi_{\text{obs}}\approx 0$ が予測される。逆に、task-relevant structure と整列した忘却により $\kappa$ の heterogeneity が増大する系では、sufficiently large $n$ と H1-H1''' の成立のもとで
+ $$
+ \operatorname{Corr}(\Xi_{\text{obs}}, P) > 0
+ $$
+ が期待される。
```

### 6.3 line 315 への追記案

```markdown
Fisher の $z$ 変換では $z_{\text{obs}}=\operatorname{arctanh}(-0.007)=-0.0070$、$\operatorname{SE}_z=1/\sqrt{500-3}=0.0449$ であり、$\pm 2\sigma$ 帯域は $r \in [-0.0964,\,0.0825]$ となる。観測値 $-0.007$ はこの有限標本誤差範囲内に深く含まれ、no-forgetting control における $Corr(\Xi_{\text{CV}},P)\to 0$ 予測と整合する。
```

## 7. 残された open problem

1. `Ξ_theory` の overload は本文レベルで解消が必要である。line 266, 321, 348 の三箇所で別物を指している。  
2. `Ξ_Gini` と `Ξ_impl` は basis alignment を明示しない限り full target ではなく lower bound である。§5.6 の equality condition を本文に昇格させる必要がある。  
3. `Ξ_Var / Ξ_Gini / Ξ_CV` の calibration には control 由来の noise baseline が要る。現行本文は raw observable と estimator を混同している。  
4. CKA route を full estimator にするには `\widehat T_l` の独立推定が必要である。現在あるのは `\Phi(l)` 側の proxy のみで、`T` 側が空白である。  
5. chunk coherence は proxy ではなく invariant / diagnostic へ降格すべきである。`τ` も同様に instrument variable として再分類すべきである。  
6. SOURCE anomaly として、対象草稿の冒頭見出しは `v1.1` だが、変更履歴 line 1474 は `v1.2` を宣言している。版管理の表記を揃えた方がよい。
