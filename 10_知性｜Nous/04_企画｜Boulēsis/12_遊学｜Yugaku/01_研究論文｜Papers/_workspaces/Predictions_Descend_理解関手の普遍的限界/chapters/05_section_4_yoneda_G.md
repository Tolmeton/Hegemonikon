## §4 Yoneda 接続 (G の極限化 1)

§3 で 5 分野に並列出現した随伴構造 $L_i \dashv R_i$ を、米田の補題によって統一する。本節は §1.4 表「G (収束) その 1」の本体であり、§1.6 で開示した SOURCE 強度ラベルの体系を Riehl 2016 / Mac Lane CWM の verbatim 引用で支える。

### §4.1 Yoneda の補題 (Mac Lane CWM §III.2 + Riehl 2016 §2.2)

Yoneda の補題は次のように述べる:

> **Yoneda Lemma** (Riehl 2016 §2.2 Theorem 2.2.4): For any functor $F: C \to \mathbf{Set}$ whose domain is locally small and any object $c \in C$, the function $\text{Nat}(C(c, -), F) \to F(c)$ defined by $\alpha \mapsto \alpha_c(\text{id}_c)$ is a bijection. Moreover, this correspondence is natural in both $c$ and $F$.

> [SOURCE 強候補: Riehl 2016 §2.2 Theorem 2.2.4 — riehl.txt L4763-4775 verbatim 抽出 / G-ζ 査読時独立検証義務]

> Mac Lane CWM §III.2 Theorem 1 が同じ補題を Hom-functor の言語で述べる。

> [SOURCE 中: Mac Lane CWM 1971/1998 §III.2 Theorem 1 — Wikipedia + Riehl 2016 帰属が triangulation。本稿査読時に Mac Lane CWM 直接 Read で「強」昇格義務 (G-ζ)]

操作的読み替え: **対象 $c$ は、その全ての射 $C(c, -)$ で完全に決まる**。これが §1.2 C1 で公理として置いた「理解 = L⊣R 内在化」の数学的基礎である。

「$c$ を理解している」⟺ 「$c$ への射、$c$ からの射、それらの合成パターンを内側に持つ」⟺ 「$\eta_{\text{unit}}: \text{Id} \Rightarrow R \circ L$ が iso (構造に対して)」

### §4.2 表現可能関手による極限保存 (Riehl §3.5)

Yoneda 埋め込みは極限を保存する:

> **Theorem 3.5.5** (Riehl 2016 §3.5): Covariant representable functors $C(X, -): C \to \mathbf{Set}$ preserve all limits that exist in $C$. The covariant Yoneda embedding $C \hookrightarrow \mathbf{Set}^{C^{\text{op}}}$ both preserves and reflects limits.

> [SOURCE 強候補: Riehl 2016 §3.5 Theorem 3.5.5 — riehl.txt L8702-8709 verbatim 抽出 / G-ζ 査読時独立検証義務]

> 注: 依頼書では §3.4 と表記されていたが、Riehl 2016 の正しい節番号は **§3.5 The representable nature of limits and colimits**。誤記訂正済 (§M5.2 段階 B)。

これが §3.6 の 5 分野横断同型の数学的支持である。各分野で出現した随伴対 $L_i \dashv R_i$ は、Yoneda 埋め込みを通じて presheaf 圏 $\mathbf{Set}^{C^{\text{op}}}$ に埋め込まれ、極限構造が保存される。すなわち、**5 分野で出現した同型は presheaf 圏での極限同型に帰着する**。

### §4.3 kalon §2 L161 補強引用 (Mac Lane-Moerdijk)

kalon.md §2 (L161-166) は HGK の圏 $M$ が presheaf 圏と同型であることを示す:

> 「HGK の圏 M ≅ PSh(J) は presheaf 圏 → 自動的に (co)complete (Mac Lane-Moerdijk)。」

> [SOURCE 強: kalon.md §2 L161-166、HGK 内部一次 SOURCE。Mac Lane CWM Thm X.3.1 の引用部分は §V.6/V.8 と同様 G-ζ 独立検証で「強」昇格義務]

これは §3.6 の 5 分野横断同型が presheaf 圏で実現されることの **構造的支持** である。「HGK の圏 $M$ が presheaf 圏と同型」⟺ 「本稿の L⊣R が Yoneda 埋め込みの像として well-defined」。

### §4.4 圏論的衣装除去テストへの応答 (kalon §2.5)

kalon.md §2.5 (L368-403) は「圏論的衣装除去テスト」を提示する: 「7 主張のうち 4 つは自然言語で十分判定」(L388-389)。本稿は Yoneda の補題を採用するが、これが §2.5 自身が「圏論固有」と認める領域 (Lan 拡張 + LFPT) に該当することを開示する。

> [SOURCE 強: kalon.md §2.5 L368-403 + L388-389、HGK 内部一次 SOURCE]

本稿の Yoneda 採用は kalon §2.5 への **反対方向作用** ではなく、§2.5 の判定枠組み内で「圏論固有領域」として正当化される。具体的には:

- C1 (理解 = L⊣R 内在化) は Yoneda の operational identity を本質的に使う
- C2 (構造保存定理) は faithful functor factorization (Mac Lane Ch. X / Kan 拡張) を本質的に使う
- C3 (補完₁ 単調減少) は §5 の IB Lagrangian と組み合わせて圏論的になる

これらは「自然言語で十分判定」される 4 主張ではなく、kalon §2.5 自身の判定で「圏論固有」とされる領域に入る。本稿の Yoneda 採用は kalon §2.5 と矛盾しない。

注記: kalon.md §9 (L2302-2325) の「概念 ≈ presheaf」は self-label「水準 C (比喩的使用)」であり、本稿の load-bearing 引用には不足である。本稿は §2 L161 (Mac Lane CWM 引用、水準 A 寄り) を主引用、§9 を補助引用に降格する (Block A worker findings, §M5.2 段階 B)。

### §4.5 §1.2 構成的定義の Yoneda 接地

⚠️ **論理飛躍の明示開示** (Round 4 §M5.4 予告): Yoneda の補題は category-theoretic statement (「対象は表現可能関手で完全に決定される」) であって epistemological statement (「人間/科学の理解の必要十分条件」) ではない。両者は同値ではなく、本稿は §1.1 で **構成的定義として L⊣R 内在化を採用する** という立場を明示することでこの飛躍を埋める。Yoneda は本稿の主張の **必要条件の数学的足場** であって十分条件の証明ではない (G-η / G-θ で Round 5 課題)。

§1.2 で構成的定義として置いた L⊣R を、ここまでの Yoneda 接続で **数学的足場の上に置く**:

1. **operational identity** (Yoneda Lemma): 対象 $c$ は $C(c, -)$ で決まる ⟹ $\eta_{\text{unit}}$ が iso ⟺ $C(c, -) \cong C(R(L(c)), -)$
2. **極限保存** (Riehl §3.5): 5 分野横断同型は presheaf 圏での極限同型に帰着
3. **存在条件** (GAFT/SAFT, §2.3): $L \dashv R$ の well-defined 性は SSC または cogenerator で保証
4. **HGK 圏との接続** (kalon §2 L161): HGK 圏 $M \cong \text{PSh}(J)$ により本稿構造が realizable

これら 4 点が §1.2 公理を「単なる定義」ではなく「Yoneda 接続を持つ操作的 anchor」に昇格させる。

---

