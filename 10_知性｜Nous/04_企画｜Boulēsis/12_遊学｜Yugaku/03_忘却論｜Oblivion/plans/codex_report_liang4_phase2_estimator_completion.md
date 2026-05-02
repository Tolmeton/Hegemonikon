# 梁4 Phase 2 実装報告

## 0. 実装サマリー

梁4 Phase 2 は、`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/series/論文I_力としての忘却_草稿.md` に対する**論文本体への直接実装**として完了した。今回の核は、Phase 1 で導入された `estimator / lower-bound estimator` 語彙を Appendix E まで落とし切り、`Ξ_theory` の多義性を分解し、`coherence` と `τ` を proxy 語彙から外し、CKA route を「閉じていない partial closure」として可視化したことである。結果として、批評が突ける「proxy 逃避」の逃走路はかなり狭まった。

変更統計は `243 insertions / 15 deletions` で、主要編集面は `§5.5-§5.8`, `Appendix E`, footer の version / open-problem / change-log に限られる。`§4.5 / §6.7-§6.8 / Appendix B / §10` は本文 diff 上も未編集で維持した。brief 内部に「Task 5 で §10 にも言及」と「§10 は触らない」の衝突があったため、ここでは**安全側**を採り、`OP-I-5` は `§5.7` と footer にのみ反映した。

| Task | 状態 | 反映先 (v1.5 行) | 要点 |
|:---|:---:|:---|:---|
| Task 1 | 完了 | 1336-1558 | Appendix E 新設。H1-H1''' と命題 V/G/C/I を本文化 |
| Task 2 | 完了 | 334-373 | `Ξ_coord,theory` / `Ξ_spec,proj` に改名し overload 解消 |
| Task 3 | 完了 | 429-499 | coherence を diagnostic、`τ` を knob / instrument に降格 |
| Task 4 | 完了 | 365-373 | Schur-Horn equality condition の意味を本文昇格 |
| Task 5 | 完了 | 429-433, 1580-1581 | CKA route を partial closure 化し OP-I-5 追加 |

```text
Verification
-----------
Command: git diff --stat -- '/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/series/論文I_力としての忘却_草稿.md'
Result : 1 file changed, 243 insertions(+), 15 deletions(-)

Command: git diff --unified=0 -- '/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/series/論文I_力としての忘却_草稿.md'
Observed hunks: line 3, 334-373, 429-499, 1336-1581
Interpretation : 禁止領域 (§4.5 / §6.7-§6.8 / Appendix B / §10) に diff hunk は出ていない
```

## 1. Task 1: Appendix E 新設

対象は v1.5 の 1336-1558 行。Appendix D の直後に新規 `Appendix E. Estimator 化の詳細 — 仮定 H1-H1''' と命題` を挿入し、Phase 1 report が持っていた estimator 側の仮定・命題・proof sketch を**論文本体の一部**へ昇格した。重要なのは、`raw observable / calibrated estimator / latent target / benchmark` の四層を明示したことで、`raw Gini` や `CV` がそのまま理論量に見えてしまう曖昧さを消した点である。

以下が新 Appendix E の全テキストである。

```markdown
## Appendix E. Estimator 化の詳細 — 仮定 H1-H1''' と命題

§5.5 の $\Xi_{\text{Var}}, \Xi_{\text{Gini}}, \Xi_{\text{CV}}, \Xi_{\text{impl}}$ は、raw observable をそのまま理論量と同一視するための記号ではない。本 Appendix では、それぞれがどの観測モデルの下で $\Xi_{\text{theory}}(\nu)$ の estimator もしくは lower-bound estimator と読めるかを明示する。

### E.1 共通設定

局所忘却曲率密度は

$$
\kappa(\theta) := \|d(\Phi T)\|_g^2 = \frac{4}{\alpha^2}\|F\|_g^2
$$

であり、観測設計 $\nu$ に対する理論的 target は

$$
\Xi_{\text{theory}}(\nu) := \operatorname{Var}_{u \sim \nu}[\kappa(\theta_u)]
$$

である。ここで observation unit $u$ は実験ごとに異なり、turn, trajectory, layer, coordinate などをとる。したがって「同じ $\Xi$ を測っている」とは、同じ latent law を見ているという意味ではなく、同じ curvature density $\kappa$ を**異なる observation design で集約した量**を見ているという意味である。

本 Appendix では、観測される raw quantity を $Z_u$、その背後の latent curvature density を $\kappa_u := \kappa(\theta_u)$ と書く。raw observable から latent target へ戻すには、(i) 観測モデル、(ii) noise baseline、(iii) basis alignment の 3 点が必要である。特に basis alignment とは、観測に用いる coordinate system が共分散行列 $\Sigma$ の principal directions と一致している条件であり、これが破れると recover されるのは full target ではなく lower-bound quantity になる (§5.6)。

### E.2 $\widehat{\Xi}_{\text{Var}}$ — N=416 統制実験

§5.5 の N=416 統制実験では observation unit は turn $u=t$ であり、turn ごとに局所パッチ $\theta_t$ を考える。

**仮定 H1.**
1. 各 turn $t$ には curvature density $\kappa_t := \kappa(\theta_t)$ が対応する。
2. turn-level score $Y_t$ は線形観測モデル

$$
Y_t = \beta_0 + \beta_1 \kappa_t + \varepsilon_t,
\qquad
\mathbb{E}[\varepsilon_t \mid \kappa_t] = 0,
\qquad
\operatorname{Var}(\varepsilon_t)=\sigma_\varepsilon^2 < \infty
$$

を満たす。
3. 比較する policy 間で compression budget は固定され、$\beta_1$ は共通である。
4. $(\kappa_t,\varepsilon_t)$ は i.i.d. にサンプルされ、四次モーメントが有限である。

このとき de-noised variance

$$
\widehat{\Xi}_{\text{Var}}
:=
\frac{1}{\beta_1^2}
\left[
\frac{1}{n-1}\sum_{t=1}^n (Y_t-\bar Y)^2 - \widehat{\sigma_\varepsilon^2}
\right]
$$

を $\Xi_{\text{theory}}(\nu_{\text{turn}})$ の estimator と定義できる。

**命題 V.** H1 のもとで $\widehat{\Xi}_{\text{Var}}$ は unbiased であり、$n \to \infty$ で consistent である。plug-in な noise 推定 $\widehat{\sigma_\varepsilon^2}$ を用いる場合も bias は $O(n^{-1})$、variance は $O(n^{-1})$ である。

*証明スケッチ.* 線形観測モデルより

$$
\operatorname{Var}(Y_t) = \beta_1^2 \operatorname{Var}(\kappa_t) + \sigma_\varepsilon^2
= \beta_1^2 \Xi_{\text{theory}}(\nu_{\text{turn}}) + \sigma_\varepsilon^2.
$$

したがって sample variance から noise baseline を差し引き、$\beta_1^2$ で割れば target に戻る。sample variance の標準漸近論により bias/variance はともに $O(n^{-1})$ であり、consistency が従う。□

### E.3 $\widehat{\Xi}_{\text{Gini}}$ — SWE-bench

SWE-bench 系では observation unit を trajectory-level positive score $W_u$ とし、multiplicative observation model を採る。

**仮定 H1'.**
1. 観測 unit $u$ の正値スコア $W_u$ は

$$
\log W_u = \mu + \beta \kappa_u + \varepsilon_u,
\qquad
\varepsilon_u \sim \mathcal{N}(0,\sigma_\varepsilon^2)
$$

に従う。
2. 観測 basis は $\Sigma$ の principal directions と一致する。あるいは PCA whitening 後に Gini を計算する。
3. $\kappa_u$ の分散が有限で、$n \to \infty$ の極限を考える。

このとき $W_u$ は lognormal family に入り、

$$
\tau_{\log}^2 := \beta^2 \Xi_{\text{theory}}(\nu_{\text{traj}}) + \sigma_\varepsilon^2
$$

とおけば population Gini は

$$
G_\infty = 2\Phi_{\mathcal N}\!\left(\frac{\tau_{\log}}{\sqrt{2}}\right)-1
$$

となる。したがって calibrated estimator を

$$
\widehat{\Xi}_{\text{Gini}}
:=
\frac{1}{\beta^2}
\left(
2\left[\Phi_{\mathcal N}^{-1}\!\left(\frac{\widehat G_n+1}{2}\right)\right]^2
- \widehat{\sigma_\varepsilon^2}
\right)
$$

と定義できる。ここで $\Phi_{\mathcal N}$ は標準正規分布の累積分布関数である。

**命題 G.** H1' のもとで $\widehat{\Xi}_{\text{Gini}}$ は asymptotically unbiased かつ consistent であり、bias は $O(n^{-1})$、variance は $O(n^{-1})$ である。

*証明スケッチ.* sample Gini $\widehat G_n$ は U-statistic 型であり、$G_\infty$ の estimator として bias/variance ともに $O(n^{-1})$ を持つ。逆写像 $G \mapsto 2[\Phi_{\mathcal N}^{-1}((G+1)/2)]^2$ は $(0,1)$ 上で滑らかなので、delta method により $\widehat{\Xi}_{\text{Gini}}$ も同じ次数で収束する。□

**但し書き.** §5.6 の Schur-Horn 条件を満たさないとき、この estimator が回収するのは full target ではなく projected spectral quantity $\Xi_{\text{spec,proj}}$ の lower bound である。すなわち $\widehat{\Xi}_{\text{Gini}}$ は basis alignment が成立する regime でのみ full estimator となる。

### E.4 $\widehat{\Xi}_{\text{CV}}$ — 全保持対照

全保持対照では H1' と同じ lognormal family を使いつつ、CV を zero-curvature limit の diagnostic から calibrated estimator に引き戻す。

**仮定 H1''.**
1. $W_u$ は H1' と同じ lognormal observation model に従う。
2. mean budget $m := \mathbb{E}[W_u]$ は policy 間で固定される。
3. noise baseline $\sigma_\varepsilon^2$ は full-retention control から独立に推定可能である。

lognormal family では

$$
\operatorname{CV}^2 = e^{\tau_{\log}^2} - 1,
\qquad
\tau_{\log}^2 = \beta^2 \Xi_{\text{theory}}(\nu_{\text{traj}}) + \sigma_\varepsilon^2.
$$

よって calibrated estimator は

$$
\widehat{\Xi}_{\text{CV}}
:=
\frac{1}{\beta^2}
\left(
\log(1+\widehat{\operatorname{CV}}^2) - \widehat{\sigma_\varepsilon^2}
\right).
$$

**命題 C.** H1'' のもとで $\widehat{\Xi}_{\text{CV}}$ は asymptotically unbiased かつ consistent である。特に no-forgetting control では $\kappa_u \approx 0$ が全 unit で成立するので $\Xi_{\text{theory}}(\nu_{\text{traj}}) \approx 0$、したがって $\widehat{\Xi}_{\text{CV}} \approx 0$ が予測される。

*証明スケッチ.* $\widehat{\operatorname{CV}}^2$ は plug-in estimator なので有限標本 bias を持つが、CV の漸近展開と delta method により bias/variance は $O(n^{-1})$ に抑えられる。zero-curvature limit では $\tau_{\log}^2 \to \sigma_\varepsilon^2$ であり、noise baseline を引けば target はゼロへ収束する。□

### E.5 $\widehat{\Xi}_{\text{impl}}$ — N=229 CCL 式

CCL 式の測定では observation unit は expression $j=1,\dots,N$、観測座標は $k \in \{1,\dots,6\}$ である。

**仮定 H1'''.**
1. omission indicator $M_{jk} \in \{0,1\}$ は

$$
M_{jk} \sim \operatorname{Bernoulli}(p_k),
\qquad
\operatorname{logit}(p_k) = a + b\kappa_k
$$

に従う。ここで $\kappa_k := \mathbb{E}[\kappa_u \mid \text{coordinate}=k]$ は coordinate-level curvature energy である。
2. 6 座標 basis が principal directions と一致する場合に限り equality が成立し、一致しない場合は §5.6 の lower-bound regime に落ちる。
3. small-spread regime で $p_0 := (1/6)\sum_k p_k$ の近傍に線形化できる。

各座標の omission rate estimator は

$$
\widehat p_k = \frac{1}{N}\sum_{j=1}^N M_{jk}
$$

であり、small-spread regime では

$$
p_k
=
p_0 + b\,p_0(1-p_0)(\kappa_k-\bar\kappa) + O((\kappa_k-\bar\kappa)^2)
$$

となる。したがって Gini は first order で $\sqrt{\operatorname{Var}_k(\kappa_k)}$ に比例するので、

$$
\widehat{\Xi}_{\text{impl}}
:=
c_{\text{impl}}(p_0)^{-2}\,
\operatorname{Gini}(\widehat p_1,\dots,\widehat p_6)^2
$$

を coordinate-level target

$$
\Xi_{\text{theory}}(\nu_{\text{coord}})
:=
\operatorname{Var}_{k=1,\dots,6}[\kappa_k]
$$

の estimator と定義できる。

本文 §5.5 で報告した

$$
\Xi_{\text{coord,theory}} := \operatorname{Gini}(\bar p_1,\dots,\bar p_6)
$$

は、36 動詞を均等使用したときの coordinate-level benchmark を raw Gini scale で書いたものであり、上の calibrated target とは representation scale が異なる。両者を区別することで、raw observable・calibrated estimator・benchmark の三層が分離される。

**命題 I.** H1''' のもとで $\widehat{\Xi}_{\text{impl}}$ は coordinate-level heterogeneity $\Xi_{\text{theory}}(\nu_{\text{coord}})$ の consistent estimator である。basis alignment が壊れている場合は lower-bound estimator に降格する。

*証明スケッチ.* $\widehat p_k$ は unbiased で $\operatorname{Var}(\widehat p_k)=p_k(1-p_k)/N = O(N^{-1})$。Gini は滑らかな対称関数なので multivariate delta method により $\widehat{\Xi}_{\text{impl}}$ の bias/variance は $O(N^{-1})$。basis alignment が成り立つときは coordinate basis が principal directions を表すため full target を recover し、そうでなければ §5.6 の Schur-Horn 不等式により lower bound のみが見える。□

### E.6 推定量間の関係

4 つの estimator はすべて同じ latent curvature density $\kappa$ から出発するが、observation unit と観測モデルが異なるため、target は observation design $\nu$ を通して現れる。

| estimator | observation unit $u$ | raw observable | latent target | full / lower-bound の境界 |
|:---|:---|:---|:---|:---|
| $\widehat{\Xi}_{\text{Var}}$ | turn | de-noised sample variance | $\Xi_{\text{theory}}(\nu_{\text{turn}})$ | noise baseline が既知なら full |
| $\widehat{\Xi}_{\text{Gini}}$ | trajectory | sample Gini of positive score | $\Xi_{\text{theory}}(\nu_{\text{traj}})$ | basis alignment があれば full, なければ lower bound |
| $\widehat{\Xi}_{\text{CV}}$ | trajectory | calibrated CV | $\Xi_{\text{theory}}(\nu_{\text{traj}})$ | noise baseline が既知なら full |
| $\widehat{\Xi}_{\text{impl}}$ | coordinate | Gini of omission rates | $\Xi_{\text{theory}}(\nu_{\text{coord}})$ | basis alignment があれば full, なければ lower bound |

したがって「どの $\Xi$ が正しいか」という問いよりも、「どの observation design の下で何を推定しているか」を明示する方が重要である。本文で導入した $\Xi_{\text{coord,theory}}$ と $\Xi_{\text{spec,proj}}$ は、この設計依存性を可視化するための補助ラベルである。前者は equal-usage benchmark、後者は spectral projection であり、いずれも fundamental quantity $\Xi_{\text{theory}}(\nu)$ そのものではなく、その可観測化の仕方を示している。
```

## 2. Task 2: Ξ_theory overload 解消

対象は v1.5 の 334-373 行である。Phase 1 草稿では `Ξ_theory` が `(a) experiment-level target`, `(b) coordinate-level equal-usage benchmark`, `(c) spectral projection` の三役を兼ねており、議論の足場が揺れていた。今回の実装では、**latent quantity は `Ξ_theory(ν)` のまま保持しつつ、観測設計依存の補助ラベルだけを分解する**方針を採った。

| v1.5 行 | 旧表記 | 新表記 | 意味 |
|:---|:---|:---|:---|
| 278 | `\Xi_{\text{theory}}(\nu)` | 維持 | experiment-level / design-level latent target |
| 338 | `\Xi_\text{theory}` | `\Xi_{\text{coord,theory}}` | equal-usage 下の coordinate benchmark |
| 357, 365, 369, 373 | `\Xi_\text{theory}|_\text{top-d}` 相当 | `\Xi_{\text{spec,proj}}` | spectral projection / Schur-Horn 側 quantity |

差分は次の通り。

```diff
- $$\Xi_\text{theory} = \text{Gini}(\bar{p}_1,...,\bar{p}_6) = 0.271$$
+ $$\Xi_{\text{coord,theory}} = \text{Gini}(\bar{p}_1,...,\bar{p}_6) = 0.271$$

- $$\Xi_\text{impl} = \text{Gini}(p_k) = 0.045 \ll \Xi_\text{theory} = 0.271$$
+ $$\Xi_\text{impl} = \text{Gini}(p_k) = 0.045 \ll \Xi_{\text{coord,theory}} = 0.271$$

- $$\Xi_\text{impl} \equiv \text{Gini}(\text{diag}(\Sigma)) \leq \text{Gini}(\text{spec}(\Sigma)) = \Xi_\text{theory}|_\text{top-d}$$
+ $$\Xi_\text{impl} \equiv \text{Gini}(\text{diag}(\Sigma)) \leq \text{Gini}(\text{spec}(\Sigma)) = \Xi_{\text{spec,proj}}$$
```

これにより、`理論量そのもの` と `理論量の particular observation / benchmark` が混線しなくなった。以後 `Ξ_theory(ν)` は latent target、`Ξ_coord,theory` は equal-usage benchmark、`Ξ_spec,proj` は Schur-Horn の projected quantity という三層で読める。

## 3. Task 3: coherence/τ 降格

対象は v1.5 の 446-499 行である。ここでやったことは、`coherence` を `Ξ` の proxy / estimator から**切り離し**、`G∘F` が到達した不動点の状態を読む diagnostic / invariant として再配置したこと、そして `τ` を**measurement target ではなく intervention parameter**として書き直したことである。

```diff
- §5.5-§5.7 は忘却の**方向**を検証した。本節は忘却の**保存量**を確立する。
+ §5.5-§5.7 は忘却の**方向**を検証した。本節で扱う coherence は $\Xi$ の estimator ではなく、G∘F 不動点の post-distillation diagnostic である。

- τ は G∘F の**初期条件**であり、不動点の coherence $c^*$ は ...
+ τ は G∘F の**初期条件**であり、experimental knob / instrument variable であって、不動点 quality の estimator ではない。

- τ は初期条件であり、G∘F の引力盆地内の異なる初期点を選ぶに過ぎない。
+ τ は experimental knob として引力盆地内の初期点を選ぶに過ぎず、coherence 自体を推定する量ではない。
```

この変更で、`coherence が曲率 heterogeneity を推定している` という誤読は難しくなった。残る意味はむしろ「どの粒度で切っても、蒸留後の fixed-point quality はほぼ保存される」という invariant 読みである。

## 4. Task 4: Schur-Horn equality condition 昇格

対象は v1.5 の 365-373 行である。Phase 1 では「等号条件: PCA 後」と 1 行で済ませていたが、ここは lower-bound estimator と full estimator の分岐点なので、理論本文に昇格させる必要があった。今回の実装では、**basis alignment が立っているときだけ full target を回収し、立っていなければ shadow しか見えない**という意味を明文化した。

```diff
 $$\Xi_\text{impl} \equiv \text{Gini}(\text{diag}(\Sigma)) \leq \text{Gini}(\text{spec}(\Sigma)) = \Xi_{\text{spec,proj}}$$
 
 等号条件: 特徴次元が Σ の固有方向と一致するとき（PCA 後）。
+
+ **等号条件の意味.** 観測 basis が Σ の principal directions と一致するとき、対角成分から計算した Gini は単なる影ではなく projected spectral quantity $\Xi_{\text{spec,proj}}$ そのものを回収する。この regime では Appendix E.3 の $\widehat{\Xi}_{\text{Gini}}$ と Appendix E.5 の $\widehat{\Xi}_{\text{impl}}$ は、選んだ観測設計 $\nu$ に対する full target の estimator と読める。逆に basis alignment が破れると、対角観測は固有方向の混合で平坦化され、recover されるのは lower-bound quantity のみである。
```

この段落追加により、`proxy が悪い` という曖昧な不満が、`basis alignment を満たしていないので lower bound しか見えていない` という**判定可能な条件**へ変わった。

## 5. Task 5: CKA partial closure + OP-I-5

対象は v1.5 の 429-433 行と 1580-1581 行である。ここでは CKA route を「全面否定」せず、「`Φ` 側の投影成分までは見えるが、`T` 側の独立 estimator がないので `d(\Phi T)` 全体はまだ閉じていない」と構造化した。これにより、CKA 経路は誇張でも撤回でもなく、**partial closure** として定位された。

```diff
+ **CKA route の位置づけ (partial closure).** CKA-based Fisher ratio は、$\Phi$ 側を $\Phi_{\text{CKA}}(l) := 1-\operatorname{CKA}(h_l,h_0)$ で観測し、$\operatorname{image}(G)$ への射影で $d\Phi$ の主成分を抽出する限りで、projected quantity $\Xi_{\text{spec,proj}}$ の lower-bound estimator を partial に与える。しかし現行設計には $\widehat T_l$ の独立 estimator がなく、$\Pi_{\operatorname{image}(G)} d\Phi_l \wedge \widehat T_l$ を layerwise に再構成できない。したがって CKA route は $d(\Phi T)$ 全体の full estimator ではなく、$\Phi$ 側の projected component のみを捉える partial closure に留まる。この未閉鎖性を Open Problem OP-I-5 として記録する。

- *Open Problems: ... OP-I-4 (...)*
+ *Open Problems: ... OP-I-4 (...), OP-I-5 (Chebyshev 形式 $T$ の layerwise estimator の独立構成)*
```

brief には「§10 結論にも簡潔に言及」と「§10 は触らない」の衝突があったため、今回は `§10` を**意図的に不編集**とし、その代わり `§5.7` と footer の open-problem list / change history に OP-I-5 を明示した。これは safety-first の偏差処理であり、Phase 2 の内容面は保持している。

## 6. 論文本体への反映提案 (総合 diff)

今回は「提案」ではなく**反映済み**なので、ここでは統合 diff の読み筋だけを残す。主要 hunk は 4 つで、`3`, `334-373`, `429-499`, `1336-1581` に限定される。したがって diff は「版表示同期」「§5.5-§5.8 の概念整理」「Appendix E 新設」「footer 更新」の 4 面に圧縮できる。

| 面 | 反映箇所 | 効果 |
|:---|:---|:---|
| Version sync | 3, 1577-1581 | `v1.5` へ同期、Open Problem / change log 更新 |
| Overload 解消 | 334-373 | `Ξ_theory` の三役を分離 |
| Proxy 語彙の整理 | 429-499 | coherence / `τ` / CKA を再分類 |
| Estimator 本体 | 1336-1558 | Appendix E と proof sketch を追加 |

```diff
- **Paper I — v1.1 (2026-04-11)**
+ **Paper I — v1.5 (2026-04-11)**

- $$\Xi_\text{theory} = \text{Gini}(\bar{p}_1,...,\bar{p}_6) = 0.271$$
+ $$\Xi_{\text{coord,theory}} = \text{Gini}(\bar{p}_1,...,\bar{p}_6) = 0.271$$

- $$\Xi_\text{impl} \equiv \text{Gini}(\text{diag}(\Sigma)) \leq \text{Gini}(\text{spec}(\Sigma)) = \Xi_\text{theory}|_\text{top-d}$$
+ $$\Xi_\text{impl} \equiv \text{Gini}(\text{diag}(\Sigma)) \leq \text{Gini}(\text{spec}(\Sigma)) = \Xi_{\text{spec,proj}}$$

+ ## Appendix E. Estimator 化の詳細 — 仮定 H1-H1''' と命題
+ ...
+
+ *Open Problems: ... OP-I-5 (Chebyshev 形式 $T$ の layerwise estimator の独立構成)*
```

raw path annex は次の 2 本で十分である。

| role | absolute path |
|:---|:---|
| edited paper | /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/series/論文I_力としての忘却_草稿.md |
| this report | /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/plans/codex_report_liang4_phase2_estimator_completion.md |

## 7. 残された open problem (梁4 Phase 3 候補)

1. `OP-I-5` の本体である `\widehat T_l` の layerwise 独立 estimator を構成すること。現状の CKA route は `Φ` 側の projected component にしか触れていない。
2. `§5.7` の 6 座標相関は `Scale / Temporality / Valence` の 3 座標しか proxy を持たない。`Function / Value / Precision` の proxy 設計が Phase 3 の自然な延長になる。
3. `basis alignment` は理論条件として明示されたが、SWE-bench / HGK 側で「どの程度 alignment が成り立っているか」の実証はまだ弱い。PCA-whitening や diagonalization 実験を appendix / supplement に回す余地がある。
4. 版管理 anomaly は解消されたが、旧 change log 内に残る historical line 参照はこの先もずれる。将来的には `line` ではなく `section + anchor` ベースの参照に切り替えた方が壊れにくい。
