# Codex 委託 brief: 梁4 — Proxy の estimator 化

## 目的

論文I「力としての忘却」§5.5 で使われている経験的量 Ξ (様々な定義: Ξ_Var, Ξ_Gini, Ξ_CV, Ξ_impl) を、**理論的量 Ξ_theory の estimator** として正式に定義する。これにより定理 5.1 (方向性定理) と経験的相関予測 Corr(Ξ, P) > 0 の間の**断絶**を補修する。

## 背景

論文I §5.5 は次の予測を立てる:

> 定理 5.1 (方向性定理): F_ij = 0 ⟺ d(ΦT) = 0
> 予測: Corr(Ξ, P) > 0 (不均一性 Ξ とタスク持続 P の正相関)

しかし:
- Ξ の理論的定義は line 266 で「Var(λ) (パラメータ間の保持率分散)」
- 実験で使われる Ξ は複数の operationalization がある (Var, Gini, CV, impl 等)
- 定理 5.1 はバイナリ命題 (曲率の 0/非 0) であり、Corr > 0 という定量的予測は**定理 5.1 から直接導出されない**
- つまり「理論 → 予測」の跳躍が無証明

外部監査 (批評) は次の点を攻撃する:
> §5.5 は (Ξ, P) の対応を示すが、Ξ が T, Φ, d(ΦT) とどう定量的に結びつくかが本文内で閉じていない。実験結果が「proxy が悪かった」という退避で逃げられる

## 目標

Ξ (および関連する proxy: CKA, chunk coherence, τ) を**理論量の estimator** として定義することで、proxy 逃避を構造的に不可能にする。

## タスクの具体

### Step 1: 理論量 Ξ_theory の選択と定義 (1-2 時間)

統計多様体 (M, g, C) 上の忘却場 Φ と Chebyshev 1-形式 T が与えられたとき、定理 5.1 (F_ij = 0 ⟺ d(ΦT) = 0) と整合する**定量的な**不均一性指標を定義せよ。

候補:
- **(A) 正規化された方向整合度**: $\Xi_{\text{theory}}^{(A)} := \frac{|d\Phi \wedge T|_g^2}{|d\Phi|_g^2 \cdot |T|_g^2}$ (∈ [0,1], dimensionless)
- **(B) 曲率ノルム**: $\Xi_{\text{theory}}^{(B)} := \|d(\Phi T)\|_g^2 = \|F\|_g^2 \cdot (2/\alpha)^2$ (曲率の大きさ)
- **(C) 方向投影**: $\Xi_{\text{theory}}^{(C)} := \frac{|\langle d\Phi, T\rangle_g|}{|d\Phi|_g \cdot |T|_g}$ (コサイン整合)

各候補について:
1. 定理 5.1 との関係 (定量的予測に使える形か)
2. 実験的推定可能性 (実在のデータから計算できるか)
3. ガウス族での具体的計算 (§4 の Φ_B, T = (0, 6/σ) に対する値)
4. カテゴリカルシンプレックス Δⁿ での具体的計算 (Appendix B に対応)

**推奨**: (A) または (B) を採用。(C) は sign 情報を失うので最後の選択肢。理由付きで選べ。

### Step 2: 各経験的 Ξ を estimator として再定義 (1-2 時間)

論文I §5.5 で使われる以下の量を、Step 1 で選んだ Ξ_theory の estimator として定義する:

1. **Ξ_Var** (§5.5 N=416 統制実験): ターン情報量の分散
   - 仮定 H1: <明記せよ — 例: 線形化忘却モデル + i.i.d. ターンサンプリング>
   - estimator: Ξ_Var = estimator of Ξ_theory under H1
   - bias: E[Ξ_Var] - Ξ_theory = O(何?)
   - variance: Var[Ξ_Var] = O(n^?)

2. **Ξ_Gini** (§5.5 SWE-bench, Paper II): Gini 係数
   - 仮定 H1': <明記せよ>
   - estimator: Ξ_Gini = estimator of Ξ_theory under H1'
   - bias, variance 同様に

3. **Ξ_CV** (SWE-bench 全保持対照): 変動係数
   - 仮定 H1'': <明記せよ>
   - estimator, bias, variance

4. **Ξ_impl** (§5.5 体系内検証, 229 CCL 式): 6 座標の忘却率 Gini
   - 仮定 H1''': <明記せよ>
   - estimator, bias, variance

各 estimator について、「どの条件下で unbiased か」「どの条件下で consistent か」を**命題として**述べよ (証明はスケッチで良い)。

### Step 3: §5.5 予測の書き換え提案 (30 分)

現行:
> Corr(Ξ, P) > 0

新:
> 仮定 H1 のもとで、Ξ_obs は Ξ_theory を $O(n^{-1/2})$ 誤差で推定し、定理 5.1 より Corr(Ξ_theory, P) は $|d\Phi \wedge T|$ が有意な系で正値を取る。したがって sufficiently large n と H1 の成立のもとで Corr(Ξ_obs, P) > 0 が期待される。

この書き換えを Markdown で提案し、論文I §5.5 の line 266-275 への差し替え候補として**3 パターン**用意せよ (ambition の強さを変えた 3 段階)。

### Step 4: SWE-bench N=500 全保持対照の再解釈 (30 分)

§5.5 line 315 の:
> r(Ξ_CV, P) = -0.007, p = 0.87 (全保持エージェント)

を「定理の成功確認」として再解釈する命題を書く:

> 定理: 忘却操作なし (dΦ ≈ 0) の条件下では Ξ_theory ≈ 0。したがって Ξ_CV → 0, Corr(Ξ_CV, P) → 0 が**予測**される。観測値 r = -0.007 はこの予測の $n = 500$ 有限サンプル誤差範囲内にある。

誤差範囲を**定量的に計算**せよ (Fisher z 変換の standard error で r ± 2σ の範囲を出す)。

### Step 5: CKA と chunk coherence の proxy 対応 (1 時間, 余裕があれば)

§5.7-§5.8 で使われる:
- **CKA-based 曲率推定**: G∘F の image(G) 方向の Fisher ratio
- **Chunk coherence**: pairwise cosine similarity

これらも理論量の estimator として定義できるか試みよ。できなければ「open problem」と明記。

## 出力形式

同じディレクトリの `codex_report_liang4_proxy_estimator.md` に書き出す。構成:

```markdown
# 梁4 報告: Proxy の estimator 化

## 0. 判定
<Step 1 でどの候補を選んだか、Step 2 の定義作業が可能だったか、Step 5 が閉じたか>

## 1. Step 1: 理論量 Ξ_theory の選択
<候補 (A)(B)(C) の比較 + 選択 + 理由 + ガウス族とカテゴリカルでの具体値>

## 2. Step 2: 各経験的 Ξ の estimator 化
<4 つの Ξ_obs それぞれについて、仮定・estimator 式・bias・variance・命題>

## 3. Step 3: §5.5 予測の書き換え
<3 段階の ambition レベルで書き換え候補を並べる>

## 4. Step 4: SWE-bench 全保持対照の再解釈
<予測誤差範囲の定量計算>

## 5. Step 5: CKA & coherence (余裕があれば)
<できたら定義、できなければ open problem 化>

## 6. 論文本体への反映提案
<line 266 付近への差し替えを diff 形式 or before/after 形式で提示>

## 7. 残された open problem
<次のステップで扱うべき論点>
```

## 制約

- **時間**: 3-5 時間で収める (深追いしすぎない)
- **SOURCE 厳格**: 論文I の line 番号を必ず明示。引用する式は論文内の記号を保つ
- **推測禁止**: 「こうだろう」は書かない。仮定 H1 の形で明示する
- **言語**: 日本語
- **読んで欲しい論文部分**:
  - §5.1-§5.4 (方向性定理と曲率の定義)
  - §5.5 line 262-320 (選択的忘却定理と N=416 実験)
  - §5.6 Schur-Horn 橋渡し
  - §5.7-§5.8 CKA / coherence
  - Appendix B カテゴリカルシンプレックス
  - Appendix D ノルム分離

## 補足

- 本タスクは論文I §5.5 の核心的補強である。定理 5.1 と経験的予測の間の断絶を埋める
- 梁6 Phase A (数値再現) と並行して梁5 (g^(α) 定義) が完了済み (Option C 採用)
- Codex の既存 report `codex_report_g_alpha_literature.md` を参考にして良い (Ay et al. 2017 Thm 2.10(2) の引用など)
- 論文I の最新 version は v1.2 (2026-04-11)

## 推奨: 不確実な判断点

Step 1 の (A)(B)(C) の選択で判断がつかない場合、**推奨は (B) 曲率ノルム** (定理 5.1 の F_ij と直接結びつき、scale 情報を保つ)。
