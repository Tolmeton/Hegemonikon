# Predictions Descend — 理解関手の普遍的限界

**版**: v0.9 (2026-04-26, **Round 5 G-λ NRFT 完全形式化部分達成** — §8.4.3.1 で vdG-O 2020 (arxiv 2004.10482) + Yanofsky 2003 (arxiv math/0305282) + §5.5 で Goldfeld-Polyanskiy 2020 (arxiv 2011.06208) Corollary 1 完全 PDF Read 経由で Joyal AU の 4 公理 + $U_0$ 構成 + Lan ⊣ Syn equivalence + Cantor categorical Gödel 第二 + Yanofsky restatement 経由 Lawvere FP statement + Gaussian IB scalar closed form 接地。**§8.4.1.1** で **G-θ'-1 部分着手**、**§8.4.3.2** で **G-θ'-2 ~57% 達成**、**§8.4.3.3** で **HA-1 ~30% 部分達成 + Reduction 命題 [仮説 70%]** (HA-1 → G-θ'-1 (2)(4) + topos 公理への構造的帰着を発見)、**§5.5** で **G-ε 60% → 75-80%**。**G-θ'-3 解消** + **G-θ'-4 ~1.7/3 達成** + **G-θ'-1 部分着手** + **G-θ'-2 ~57% 達成** + **G-ε 75-80% 達成**。**honest 訂正**: 旧「Lawvere FP への reduction」は不正確、Lawvere-like FP (vdG-O Lemma 6.12) は Löb 用、Gödel 第二は Cantor categorical 直接使用。**Reduction 命題の含意**: 道 C 達成度の天井は G-θ'-1 (2)(4) 完全解消で律速される。道 C 達成度 60-70% → **86-91.5%** (honest)、C4 主張水準 仮説 65% → **仮説 70%**)
**前版**: v0.8 (2026-04-26, Round 6 G-η 全 10 ペア natural transformation 骨格 追加 — §3.6.1 で 5 分野 5C2=10 ペア全てに対し核となる対応 + natural transformation component (iso / non-iso) + naturality 構造 + 残ギャップを骨格として固定)
**前々版**: v0.7 (2026-04-26, Round 6 軽量着手 — G-ι 部分昇格 (Mayama et al. 2025 arxiv 2510.04084 完全 PDF 取得、Φ ↔ Bayesian surprise 強相関 ρ=0.879 の経験的橋渡しを §6.1 に統合) + G-ε 部分昇格)
**前々々版**: v0.6 (2026-04-25, §8.4 Predictions Descend Theorem の形式証明試行 追加 — 達成度 60-70% で honest 較正)
**メタファイル**: `Predictions_Descend_理解関手の普遍的限界_メタデータ.md` (本稿の F⊣G 台帳 / 核主張レジャー / Gauntlet ログ / 虚→実変換面)
**主張水準ラベル**: 構成的命題 / 命題 / 仮説 / 構造的類似 (本稿内較正、論文間比較禁止)
**SOURCE 強度ラベル**: 強 (PDF verbatim 直接 Read) / 強候補 (subagent verbatim 抽出, 査読時独立検証推奨) / 中 (triangulation) / TAINT (記憶/web 要約)

---

## 序

20 世紀の科学哲学は、ある操作と、その操作の痕跡とを、しばしば取り違えてきた。

操作とは「**理解**」であり、痕跡とは「**予測**」である。Popper の反証可能性、Mangalam の予測至上主義、超ひも理論への「Not Even Wrong」批判 — これら 70 年にわたる三つの誤配位は、すべて**痕跡から操作を読む**という同じ間違いから派生する。

理解と予測は同じ評価軸上に存在しない。理解は対象を別表現に還元し、その表現から元を回復する**二つの関手の組**であり、予測はその組のうち下降関手から漏れ出す痕跡である。両者は**随伴対** $L \dashv R$ として結ばれるが、合成の単位 $\eta_{\text{unit}}: \text{Id} \Rightarrow R \circ L$ は同型ではない。回復は完全ではなく、核 $\text{Ker}(\eta_{\text{unit}})$ が常に残る。

予測₁ (経験的予測) の産出は、理論が真理₀ を捉えた証ではない。それは真理₀ から下降関手 $R$ で生成される **痕跡** にすぎない (Predictions Descend)。本稿はこの誤読に対して、$L$ と $R$ を独立に並置し、両者の随伴を明示する (真理₀ / 真理₁ の定義は §2 で立てる)。

---

