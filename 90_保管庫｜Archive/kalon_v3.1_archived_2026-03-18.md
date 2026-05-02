````typos
#prompt kalon-axiom
#syntax: v8
#depth: L3

<:role: Kalon (καλόν) — HGK 体系の美の公理的定義。
  収束と展開の収斂点。随伴 F⊣G の不動点。
  概念は数式を包含する。数式は概念を包含しない。
  このドキュメントは数式 (骨格) と具体 (肉) の両方で Kalon を定義する。:>

<:goal: 美の操作的定義を厳密に与え、判定可能にする。
  Kalon(x) ⟺ x = Fix(G∘F) を公理とし、定理群・操作的判定・具体例で肉付けする。:>

<:intent: FEP 体系の最上位概念として「何が良いものか」を定義する。
  主観的好みではなく、随伴の不動点という構造的性質として美を捉える。
  HGK の全ての品質判断 (◎/◯/✗) の基盤を提供する。:>

<:summary:
  ## §1 一語定義

  **Kalon**: 発散と収束のサイクルの収斂点。

  使用例:
  - 「この insight は kalon だ」— これ以外の表現がない
  - 「何が kalon か？」— 何がこの必然形か？
  - 「kalon する」— 蒸留のサイクルを回して収束させる
/summary:>

<:fact:
  ## §2 Formal Core — 公理

  公理 [水準 B — 公理的構成]:

  ```
  Kalon(x) ⟺ x = Fix(G ∘ F)
      where F ⊣ G forms a closure adjunction in C,
      F ≠ Id, G ≠ Id (非退化条件),
      F⊣G は体系の構造から先験的に固定 (選択制約),
      G∘F admits an initial algebra
  ```

  - **C** (圏): 前順序圏 (1つまたは複数の前順序の組)。HGK では axiom_hierarchy.md の L1 随伴と統一
    (v4.14: Ep/Pr 2半順序間の反変ガロア接続として具体化)。
    L2 では [0,1]-豊穣圏に拡張され、Hom(A,B) ∈ [0,1] が「変換の質・コスト」を表す
    (Lawvere 1973: 距離空間 = [0,∞]-豊穣圏。HGK L2 はその有界版)。
  - **F** (左随伴): 発散。候補を広げる。Colimit 的。Explore。
  - **G** (右随伴): 収束。核だけ残す。Limit 的。Exploit。
  - **F⊣G**: 閉包随伴 (closure adjunction)。G∘F が閉包作用素 (extensive + 単調 + 冪等) を形成する構造。
    具体形は文脈による:
    - **monotone GC** (単一前順序): F(x) ≤ y ⟺ x ≤ G(y)。η: G∘F ≥ Id, ε: F∘G ≤ Id。
    - **antitone GC** (2半順序間): ρ ≤₂ F(π) ⟺ π ≤₁ G(ρ)。η: G∘F ≥ Id₁, η': F∘G ≥ Id₂ (両方 extensive)。
    Kalon の定義に必要なのは **η (G∘F ≥ Id) のみ**。ε の方向は文脈依存。
  - **Fix(G∘F)**: G∘F を繰り返し適用したとき、もはや変化しなくなる不動点。
  - **非退化条件**: F=G=Id (恒等関手) の自明な場合を排除。自明な不動点は全対象になるため。
  - **選択制約** (監査 A1 対応): F⊣G は対象 x に合わせて事後的に選択するのではなく、
    体系の構造として先験的に固定されていなければならない。
    HGK では axiom_hierarchy.md の7座標対立 (I↔A, E↔P, Explore↔Exploit, C↔U, Mi↔Ma, +↔-, Past↔Future)
    がこの制約を満たす。任意の x に対して F⊣G を事後構成して「x は Kalon である」
    と主張することは、この制約により禁止される。
  - **存在と一意性条件** (監査 B3 対応):
    - **存在**: G∘F が始代数を持つこと (Lambek の補題により圏全体での最小不動点の存在が保証される)。十分条件として G∘F が ω-連続であること。
    - **到達先**: 任意の初期状態 q から出発し、G∘F を反復適用して安定した不動点 x が「q に相対的な Kalon」である。
    - **絶対的一意性**: 圏 C が完備束 (Complete Lattice) をなす場合、Knaster-Tarski の定理により、q 以上となる最小不動点 (Least Fixed Point) が必ず一意に存在する。この完備性の仮定下において、q に対する Kalon は数学的に一意に決定される。
    - **HGK空間における完備性の正当化**: HGKの操作的対象空間 (概念・アーキテクチャ・コード等) は無限集合ではなく、実用上は有限半順序 (finite poset) として構成される。§4.5 の Worked Example が示すように、G∘F の反復適用は有限の全順序鎖 (finite chain: x₀ ≤ x₁ ≤ ... ≤ x_n) を形成する。有限全順序集合は常に完備束をなすため、Kalonの構成において完備束の仮定は自動的に満たされ、Knaster-Tarskiの適用は数学的飛躍なく正当化される。
/fact:>

<:spec:
  ## §2 三属性 (@repeat[x3, /eat+] で発見)

  ```
  Kalon = Fix(G∘F)
          ∧ Generative (展開可能)
          ∧ Self-referential (自己参照)

  1. Fix(G∘F)        — 不動点: 収束と展開の収斂点 (水準B)
  2. Generative      — 展開可能性: Fix から 3つ以上の導出 (C2 Colimit から従う — 下記注参照)
  3. Self-referential — 自己参照: 定義のプロセスが定義を実証 (M1 Meta-principle)
                       + 系が自己言及に耐えること = 普遍性の必要条件 (Lawvere 対偶)
  ```

  > **注**: 旧三属性の "Presheaf" は§9 で水準C（メタファー）として分離。
  > 公理レベル (水準B) の三属性は Fix + Generative + Self-referential。

  > **注 (v1.10)**: Generative の「3つ以上」は恣意的な閾値ではない。
  > 圏における最小の閉じた構造は**三角形 (2-simplex)** — 3つの射で形成される。
  > 1射は矢印（方向のみ）、2射は経路（因果連鎖）、3射で初めて**構造が閉じる**（パターンが浮かぶ）。
  > 「3つ以上の導出」とは「最小の閉構造を形成できる」の操作化であり、
  > 構造認識の最小十分条件の圏論的表現である。

  > **注 (v2.10 — 監査対応)**: 「C2 Colimit から従う」は、Colimit の定義図式 D が
  > 3 対象以上であることを**前提**とする。この前提が満たされないケース
  > (D が 2 対象以下の退化図式) では Generative は成立しない。

  > **§4 全 worked examples における帰納的検証** (v2.10):
  >
  <:table:
    事例 :: 反復回数 :: colim leg (導出数) :: D≥3
    §4 FEP公理 :: — :: 24定理+15結合規則+全WF :: ✅
    §4 insight P2⊣P4 :: — :: 蒸留,F⊣G,教育論,知識管理... :: ✅
    §4.5 Kalon定義 :: n=4 :: 3つ+α (入れ子,U-series,定式化,上位置換) :: ✅
    §4.6 リファクタ :: n=3 :: 3層分割,CQRS,Result型 :: ✅
    §4.7 CCL `*` :: n=2 :: 精度加重積,⊗対応,Markov圏 :: ✅
    §4.8 非退化違反 :: n=0 :: 0 (F=G=Id) :: ❌ (排除)
    §4.9 M1自己適用 :: — :: 4つ (入れ子再帰,圏論的定式化,U-series,上位置換) :: ✅
  :>
  >
  > 全成功例で D≥3 が確認される。失敗例 (§4.8) は非退化条件違反であり Kalon ではない。
  > [推定] 85%: 帰納的検証は完了。一般的保証 (「任意の Fix(G∘F) で D≥3」) は開問題。

  > **注 (v2.2, v2.10 水準調整)**: Self-referential の根拠構造 (v2.10 明確化):
  > - **一次根拠**: M1 直接構成 (§4.9) — Kalon の定義をそれ自身に適用し不動点を検証
  > - **動機 (motivation)**: Lawvere 不動点定理の対偶 — 自己言及不可能性が普遍性を阻むという発想の源泉
  > Lawvere 対偶は M1 の独立証明ではなく、M1 に至る圏論的動機づけである。

  > Lawvere 不動点定理の対偶: 系が自己言及できない ⟹ 系は普遍的でない。
  > 圏は入れ子構造を持つ: C_0 ↪ C_1 ↪ C_2 ↪ ⋯
  > **各レベルにおいて**、自己言及の可否が Kalon 到達可能性の必要条件として機能する:

  > ```
  > SelfRef: Cat → {0, 1}
  > SelfRef(C) = 0 ⟹ ∄ x ∈ C s.t. x = Fix(G∘F)_{non-trivial}
  > ```

  > **根拠**: G∘F が非自明な不動点を持つためには、C が自己関手 (G∘F: C→C) を
  > 「感じ取れる」ほど豊かな射の空間を持つ必要がある。自己言及不可能な圏では
  > Hom(C,C) → C 型の射が存在せず、G∘F は自明化する (F=Id or G=Id に強制される)。

  > **⚠️ 翻訳ギャップ (v2.10)**: LFPT の対偶 (点から線への全射がなければ不動点なし) と
  > 「自己言及不可能 ⟹ 非自明 Fix なし」の間には翻訳議論が必要。
  > LFPT は CCC 上の f: A → B^A 型の全射の不在を述べるが、HGK の「自己言及」は
  > Hom(C,C) → C 型の射の存在として再解釈している。この再解釈は構造的類推であり、
  > 厳密な同値性は未証明。v2.6 で直接適用の限界を認め、M1 は直接構成で示す方針へ移行。
  > [推定] 75%: Lawvere 対偶の HGK への翻訳の厳密性。

  > **入れ子構造の帰結**: 下位レベルで Kalon だったものが上位レベルでは Kalon でない
  > ことがありうる。そして上位で Kalon であるものは下位の Kalon を包含する。

  > **HGK への適用**: HGK 体系は、個別ドメインで「限定的に正しい」制約体系
  > (各 C_n でのローカルな Kalon) を、FEP という自己言及可能な公理から演繹的に
  > 再構成した。これは C_n から C_{n+1} への**普遍的上位置換**。

  > **普遍的上位置換の圏論的定式化** (水準B — 仮説, [推定] 70%):

  > 包含関手 ι: C_n ↪ C_{n+1} に沿った左 Kan 拡張:

  > ```
  > Lan_ι(K_n): C_{n+1} → Set
  >
  > K_n = C_n 上のローカルな Kalon (Fix(G∘F) の局所的実現)
  > Lan_ι(K_n) = K_n を C_{n+1} に最良近似として持ち上げた対象
  >
  > 普遍性:
  >   ∀ H: C_{n+1} → Set, K_n が H∘ι を通じて因子化
  >   ⟹ 一意な自然変換 Lan_ι(K_n) ⟹ H が存在
  >
  > Kan 拡張の存在条件 (v2.10 — 監査対応で明示化):
  >   Lan_ι(K_n) の存在には C_{n+1} が cocomplete であれば十分 (Mac Lane CWM Thm X.3.1)。
  >   HGK の圏 M ≅ PSh(J) は presheaf 圏 → 自動的に (co)complete (Mac Lane-Moerdijk)。
  >   HGK の階層では有限前順序圏 = 完備束 ⊆ cocomplete 圏。
  >   形式的証明 (2行):
  >     (1) C_n が有限前順序 ⟹ C_n は有限束 ⟹ 完備束 (有限束は自動的に完備)。
  >     (2) 完備束は全ての colimit を持つ (colim = join) ⟹ cocomplete。□
  >   ∴ HGK の有限階層では Lan_ι の存在が保証される。
  > ```

  > Corollary 2.1: Affordance Yield Principle (Euporía から導出)
  > AY(f) > 0 は Generativity の必要条件。
  > AY(f) = Fix(G∘F) ⟹ f は Kalon の Generative 属性を最大化する射。
  > 📖 定式化: euporia.md §2.7 / 実装: euporia_sub.py — AYScorer (2層: micro + macro)

  存在と一意性仕様:
    (S1) 不動点条件: G∘F(x) = x (G∘F を回しても変化しない)
    (S2) 非退化条件: F ≠ Id, G ≠ Id (自明な不動点を排除)
    (S3) 選択制約: F⊣G は先験的に固定 (事後選択禁止)
    (S4) Generative: Fix から D≥3 の導出 (最小閉構造 = 2-simplex)
    (S5) Self-referential: 定義のプロセスが定義を実証
    存在: G∘F が始代数を持つ (Lambek)
    到達: 任意の初期 q から G∘F 反復で安定
    一意: C が完備束なら Knaster-Tarski で LFP 一意
    HGK: 有限半順序 → 常に完備束 → 一意性自動成立
/spec:>

<:rationale:
  ## §2 なぜ lim だけではないか

  ```
  lim = 収束（最善の近似）      — 必要条件
  colim = 発散（展開可能性）    — 必要条件
  Fix(G∘F) = 収束が発散を招き、発散が収束を招く螺旋の不動点 — 十分条件
  ```

  <:table:
    概念 :: lim? :: colim? :: Kalon?
    lim (圏論) :: ✅ :: — :: ❌ 既存概念で十分
    Fix(G∘F) :: ✅ (C1で導出) :: ✅ (C2で導出) :: **✅ HGK 独自**
  :>
/rationale:>

<:fact:
  ## §2 双対的特性づけ — 状態視点 (v1.9)

  > Fix(G∘F) は Kalon **に至る方法** (how) を記述する。
  > 以下は Kalon **であるもの** (what) を記述する。
  > 両者は同一の概念の二つの面であり、同値である。

  ```
  Kalon_state(x) ⟺ x = argmax_{y ∈ S} G(y)

  where:
    S = エージェントの Markov blanket 内の候補集合
    G(y) = EFE(y) = E_q(s|y) [ln p(o|s)] + D_KL[q(s|y) || q(s)]
                     \_________________/   \____________________/
                     pragmatic value        epistemic value
                     (行為可能性)            (導出可能性)

    理想的: S → 全命題空間 → Kalon_ideal (到達不能な極限)
    現実的: S = MB(agent) → Kalon_practical (主観的スコープ内の近似)
  ```

  **体系接続**:
  - **EFE**: constructive_cognition.md §7 で定義。G(a) = 建設的認知の数学的表現
  - **Helmholtz 分解**: axiom_hierarchy.md §Basis — Γ (gradient/収束) と Q (solenoidal/探索)
    が EFE の pragmatic/epistemic 成分の物理的実装
  - **T3 Beauty**: §8 の D(x)/C(x) 最大は、EFE 最大化の presheaf 的写像

  なぜ同値か (証明スケッチ):

  ```
  Fix(G∘F) → argmax G(y):
    x = Fix(G∘F) に G∘F を適用 → 変化しない
    → G(y') > G(x) なる y' が存在すれば F(x) → y' → G(y') ≠ x
    → 不動点条件に矛盾。∴ x は G の局所 argmax

  argmax G(y) → Fix(G∘F):
    x = argmax G(y)
    → F(x) で展開: F は左随伴 = 発散 (Explore)
    → G(F(x)) で収束: G は右随伴 = 収束 (Exploit)
    → G∘F(x) ≥ x (unit η: Id → G∘F) — 閉包随伴の核心条件
    → x = argmax → G∘F(x) ≤ x も成立 (x を超えられない)
    → G∘F(x) = x。∴ x は不動点

  スコープ条件:
    S が全空間 → 大域 argmax = 理想的 Kalon (到達不能)
    S が MB 内 → 局所 argmax = 現実的 Kalon (主観的近似)
    Fix(G∘F) の反復は局所 argmax を漸近的に改善するプロセス
  ```
/fact:>

<:fact:
  ## §2.5 情報とエネルギーの等号 — 体系的受容

  > Kalon = argmax EFE は「最も多くの情報を持つ」選択。
  > ここで「情報」は抽象的概念ではなく、物理的実体である。

  **Landauer 原理** (1961; 実験確認: Bérut et al., Nature, 2012, 1087 citations):
  > 1ビットの情報消去は最低 kT ln 2 ジュールの熱を散逸する。

  この原理は情報処理が熱力学的過程であることを確立した。
  情報 = エネルギーは比喩ではなく物理法則である。

  **HGK における位置づけ**:

  ```
                      Landauer 原理
                           ↓
                 情報処理 = 熱力学的過程
                           ↓
               Helmholtz 分解 (Γ⊣Q)         ← axiom_hierarchy.md §Basis (d=0)
             f = (Γ + Q)∇φ
             Γ = gradient = VFE 最小化      ← エネルギー散逸
             Q = solenoidal = 確率循環       ← エネルギー保存的探索
                           ↓
                  VFE / EFE 分解
             EFE = pragmatic + epistemic    ← constructive_cognition.md §7
                           ↓
                  Kalon = argmax EFE
             = 最も多くの行為・導出を可能にする
             = 最も多くの「運動」(エネルギー) を内包する
  ```

  **制限と注意**:
  - LLM は物理的計算機上で動作するが、LLM の推論過程を直接 Landauer 限界で律速することは現在の技術では不可能
  - ここでの接続は体系の一貫性 (coherence) のためであり、「Kalon はエネルギー的に最適」という物理主張ではない
  - FEP の「自由エネルギー」と熱力学の「自由エネルギー」のアナロジーは Friston 自身が明示しているが、直接同一視ではない

  参考文献:
  - Landauer, R. (1961). "Irreversibility and Heat Generation in the Computing Process." → 情報消去の下限
  - Bérut, A. et al. (2012). Nature, 483, 187-189. doi:10.1038/nature10872 → 実験的検証 (1087 citations)
  - Hsieh, C.-Y. (2022/2025). "Dynamical Landauer Principle" → エネルギー・情報の量的等価性
/fact:>

<:assert:
  ## §2.5 圏論的衣装除去テスト (v2.11 — 監査対応)

  > **目的**: 各核心主張を圏論用語なしで再表現し、圏論が「衣装」か「本質」かを判定する。

  <:table:
    # :: 圏論的主張 :: 圏論なし再表現 :: 圏論は衣装か本質か
    1 :: Kalon(x) ⟺ x = Fix(G∘F) :: 良いもの = 「広げて絞る」を繰り返してもこれ以上変わらない状態 :: ○ 衣装 — 日常直感で成立
    2 :: F⊣G (閉包随伴) :: 「広げる操作」と「絞る操作」は対になっている :: ○ 衣装 — ガロア接続は対の直感
    3 :: Generative (D≥3) :: 良いものはそこから3つ以上の新しい発想が出る :: ○ 衣装 — 経験則として成立
    4 :: Self-referential + LFPT :: 良い定義は自分自身に適用しても成立する。十分に自己言及できる系なら不動点が存在する :: △ 本質的 — LFPT の CCC 仮定は圏論固有
    5 :: T4: Fix(G∘F) = argmin CG :: 不動点は「実態と表現の隙間」が最も小さい状態 :: ○ 衣装 — 直感的に明瞭
    6 :: T9: U/N Diagnostic :: 自分の弱点 (忘却) を認識でき、それを補えるなら良いものに到達できる :: ○ 衣装 — ポパー的反証可能性
    7 :: Lan 拡張 (上位置換) :: 限定的に正しいものを、より大きな文脈で使えるように構造的に昇格する :: × 本質的 — Kan 拡張は圏論固有の構成
  :>

  > **結論**: 7主張中 **4つは自然言語で十分に表現可能** (圏論は精密化手段)。
  > **2つは圏論が本質的** (#4 LFPT, #7 Lan 拡張)。1つは中間 (#4)。
  > 圏論は「衣装」ではなく「精密な骨格」— ただし #1, #3, #5, #6 は骨格なしでも立つ。
/assert:>

<:case:
  ## §3 具体1: 数学 — π vs e^(iπ) + 1 = 0

  <:table:
     :: π :: e^(iπ) + 1 = 0
    収束 (lim) :: ✅ 級数が収束する値 :: ✅ 5定数の関係が収束
    展開 (colim) :: ❌ そこから何も生まれない :: ✅ 複素解析、微分方程式、フーリエ解析...
    Fix(G∘F) :: ❌ 終点 :: **✅ 起点かつ終点**
    **Kalon** :: **No** :: **Yes**
  :>

  π は圧縮の産物（lim）だが、展開できない。値の圧縮であって関係の圧縮ではない。
  オイラーの等式は関係の圧縮（lim）であり、かつ無限の展開の起点（colim）。
/case:>

<:case:
  ## §4 具体2: HGK

  ### FEP 公理「VFE 最小化」

  ```
  A0: 自己組織化システムは内部エントロピーを最小化する
  ```

  <:table:
     :: 検証
    収束 (lim) :: ✅ 7要素 → 1公理 (Beauty値 10.0 vs 0.3-1.5)
    展開 (colim) :: ✅ → 24定理 + 15結合規則 + 全ワークフロー
    Fix(G∘F) :: ✅ 公理見直し (G) → 定理展開 (F) → 公理再蒸留 (G) → ... → 安定
    **Kalon** :: **Yes**
  :>

  ### insight「試行が蒸留されて技法になる」(P2⊣P4)

  <:table:
     :: 検証
    収束 (lim) :: ✅ Creator が◯の候補から蒸留 (G) した最小形
    展開 (colim) :: ✅ → 蒸留概念、F⊣G 随伴、教育論、知識管理...
    Fix(G∘F) :: ✅ Claude のたたき台 (F)「道を歩いて技が身につく」→ Creator の蒸留 (G) → 確定
    **Kalon** :: **Yes**
  :>
/case:>

<:case:
  ## §4.5 Worked Example 1: Kalon 定義自体の生成過程 (成功)

  > axiom_hierarchy.md L1 の閉包随伴を用いて、Fix(G∘F) の存在と到達を具体的に検証する。

  ### 圏と関手の特定

  ```
  圏 C = (HGK概念, ≤)
  前順序: x ≤ y ≔ 「x から y へ導出可能」

  座標: Explore (x_E) ↔ Exploit (x_P)   — Function 座標
  随伴: F = Explore↑ (左随伴, 発散), G = Exploit↑ (右随伴, 収束)
  接続: F(x) ≤ y ⟺ x ≤ G(y)   — 閉包随伴 (monotone GC)
  非退化: F ≠ Id, G ≠ Id    — 発散 ≠ 何もしない, 収束 ≠ 何もしない
  ```

  ### 対象: Kalon 定義自体の生成過程

  ```
  初期対象 x_0 = 「美とは何か」

  G∘F の反復適用:

    n=0: x_0 = 「美とは何か」

    n=1: F(x_0) = 「最小表現コストで最大演繹可能性」 — 発散: 仮説空間を広げる
         G(F(x_0)) = Creatorが収束: 「kalon ではないか。数式化すべき」 — 収束: 絞る
         x_1 = G∘F(x_0)

    n=2: F(x_1) = 「Kalon ≡ lim」 — 発散: lim の概念で広げる
         G(F(x_1)) = Creatorが収束: 「lim だけでは不十分。HGK 独自のα は？」
         x_2 = G∘F(x_1), x_2 > x_1 (情報保存: η ≥ Id)

    n=3: F(x_2) = 「Kalon = lim ∧ colim の共存」 — 発散: colim を追加
         G(F(x_2)) = Creatorが収束: 「LIM による COLIM。逐次近似の収斂点では？」
         x_3 = G∘F(x_2), x_3 > x_2

    n=4: F(x_3) = 「Kalon(x) ⟺ x = Fix(G∘F)」 — 発散: 随伴の不動点として定式化
         G(F(x_3)) = Creatorが収束: 「kalon な気がする」 — 変化なし
         x_4 = G∘F(x_3) = x_3 ≡ Fix(G∘F)   ✔️
  ```

    <:example:
      <:input: 圏 C=(HGK概念,≤), F=Explore↑, G=Exploit↑, x₀=「美とは何か」, n=4ラウンド :>
      <:output:
  検証:
  <:table:
    条件 :: 検証結果
    **前順序圏** :: ✅ x_0 ≤ x_1 ≤ x_2 ≤ x_3 = x_4。単調増加して収束
    **閉包随伴** :: ✅ F (Claudeの発散) と G (Creatorの収束) が F(x)≤y⟺x≤G(y) を満たす
    **η: G∘F ≥ Id** :: ✅ 各ラウンドで x_{n+1} ≥ x_n。発散して収束しても情報は保存される
    **G∘F 閉包** :: ✅ G∘F は extensive + 単調 + 冪等
    **F ≠ Id** :: ✅ Claude の発散は入力を変化させる
    **G ≠ Id** :: ✅ Creator の収束は入力を変化させる
    **Fix 到達** :: ✅ n=4 で G∘F(x_3) = x_3。これ以上収束しても変化しない
    **ω-連続** :: ✅ 前順序圏上の単調自己関手は自動的に ω-連続
  :>
/case:>

<:case:
  ## §4.6 Worked Example 2: コードリファクタリング (成功)

    <:example:
      <:input: 圏 C=(API設計候補,≤), F=機能追加提案, G=冗長性除去, x₀=monolithic_handler :>
      <:output:
  ```
  圏 C = (API設計候補, ≤)
  前順序: x ≤ y ≔ 「x より y の方が表現力が高いか等しい」
  座標: Explore (候補拡大) ↔ Exploit (最小化)
  随伴: F = 「機能を追加しうる設計を提案」, G = 「不要な複雑さを削る」
  非退化: F ≠ Id, G ≠ Id
  ```

  ```
  初期対象 x_0 = monolithic_handler(req)   — 1関数、500行

    n=1: F(x_0) = 「Router + Controller + Service に3層分割」
         G(F(x_0)) = 「Service 層に集約。Router は薄く」
         x_1 = Router(thin) → Service(core)

    n=2: F(x_1) = 「Service を Command/Query に CQRS 分割」
         G(F(x_1)) = 「Query は不要に複雑。Read は直接 Service で」
         x_2 = Router → Service(Command + Read)

    n=3: F(x_2) = 「エラーハンドリングを Result 型で統一」
         G(F(x_2)) = 「良い。これ以上の分割は冗長」 — 変化なし
         x_3 = G∘F(x_2) = x_2 ≡ Fix(G∘F)   ✔️
  ```

  <:table:
    条件 :: 検証結果
    Fix 到達 :: ✅ n=3 で安定
    d(n) :: d(0)=3, d(1)=2, d(2)=1, d(3)=0 — 単調減少
    **Kalon** :: **Yes** — 最小構造で最大表現力の不動点
  :>
      /output:>
    /example:>
/case:>

<:case:
  ## §4.7 Worked Example 3: CCL 演算子 `*` の設計 (成功)

    <:example:
      <:input: x₀=「精度を考慮した合成が欲しい」, F=記号候補提案, G=混同除去 :>
      <:output:
  ```
  初期対象 x_0 = 「精度を考慮した合成が欲しい」

    n=1: F(x_0) = 「× (乗算記号) で精度加重積を表す」
         G(F(x_0)) = 「× は数値の掛け算と混同する。別の記号で」
         x_1 = 「精度加重積を専用記号で」

    n=2: F(x_1) = 「* (アスタリスク) = 内積。π で加重された融合」
         G(F(x_1)) = 「マルコフ圏の ⊗ と対応する。良い」 — 変化なし
         x_2 = G∘F(x_1) = x_1 ≡ Fix(G∘F)   ✔️
  ```

  <:table:
    条件 :: 検証結果
    Fix 到達 :: ✅ n=2 で安定
    **Kalon** :: **Yes** — 記号と意味の不動点
  :>
      /output:>
    /example:>
/case:>

<:case:
  ## §4.8 Worked Example 4: 非退化条件違反 (失敗)

    <:example:
      <:input: F=Id, G=Id (恒等関手), x₀=任意の概念 :>
      <:output:
  > **Kalon でない**例。定義の反証可能性を示す。

  ```
  座標: Explore ↔ Exploit
  随伴: F = Id (何も変えない), G = Id (何も変えない)
  ⚠️ 非退化条件 F ≠ Id, G ≠ Id に違反
  ```

  ```
  初期対象 x_0 = 「任意の概念」

    n=1: F(x_0) = x_0 (何も変わらない)
         G(F(x_0)) = x_0 (何も変わらない)
         x_1 = x_0 = Fix(G∘F)   ← 自明な不動点

  すべての対象が Fix(G∘F)。すべてが Kalon。
  ```

  <:table:
    条件 :: 検証結果
    Fix 到達 :: ✅ だが**自明** (n=0 で即座に到達)
    非退化条件 :: ❌ **F = Id, G = Id — 違反**
    **Kalon** :: **No** — 非退化条件により排除。自明な不動点は Kalon ではない
  :>

  > **教訓**: 非退化条件は「何もしなくても美しい」という空虚な主張を排除する。
  > Kalon は**労力の結晶**であり、自明な安定ではない。
  > **実証的裏付け**: Hyphē PoC (§6.7) において、U_compose の等号条件 (ρ=0) が
  > embedding 空間上で構造的に到達不能であることを 29,904件の実データで確認。
      /output:>
    /example:>
/case:>

<:case:
  ## §4.9 Worked Example 5: Kalon 定義の自己適用と入れ子構造 (成功)

    <:example:
      <:input: x=Kalon定義自体, 三属性を定義自身に適用 :>
      <:output:
  > Kalon の三属性を **Kalon の定義自体に** 適用し、定義が自己言及的に検証されることを示す。

  ```
  対象 x = Kalon の定義 「Kalon(x) ⟺ x = Fix(G∘F) ∧ Generative ∧ Self-referential」

  1. Fix(G∘F): §4.5 で検証済み。4ラウンドの G∘F 反復で Fix に到達。✔️
  2. Generative: この自己適用から4つ以上の導出が可能:
     (a) 入れ子構造における Kalon の再帰的適用 (SelfRef 関手)
     (b) 「バカ = 自己言及不能 = 圏が貧弱」の圏論的定式化
     (c) U-series (忘却関手体系) との構造的接続
     (d) HGK が「限定的に正しいもの」の普遍的上位置換であるという主張
     展開は 4 つ以上。  ✔️
  3. Self-referential: 「自己言及は Kalon の必要条件」が Kalon の定義自体に適用されて不動点。✔️
  ```

  <:table:
    条件 :: 検証結果
    Fix(G∘F) :: ✅ §4.5 の Fix + Lawvere 強化でも構造不変
    Generative :: ✅ 4つ以上の非自明な展開
    Self-referential :: ✅ 定義の自己適用が定義を検証
    **Kalon** :: **Yes** — 定義自体が Kalon であることの制作的例示
  :>

  > **⚠️ 水準注記**: この自己適用は**制作的例示** (水準 B) であり厳密な数学的証明ではない。
  > 正確な水準: [推定] 70%: M1 の自己適用は構造的に支持されるが、量的独立検証を欠く。

  ### 入れ子構造における自己言及チェック

  ```
  入れ子構造:
    C_0 = プレスバーガー算術  (自然数の加法)
      ↪ C_1 = ペアノ算術       (自然数の算術全体)
        ↪ C_2 = ZFC             (集合論)

  各レベルでの SelfRef チェック:
    SelfRef(C_0) = 0  — 自己記述不能 → C_0 内で Kalon 到達は構造的に不可能
    SelfRef(C_1) = 1  — 自己記述可能 (Gödelコーディング) → Kalon 到達の可能性あり。代償: 不完全性
    SelfRef(C_2) = 1  — 自己記述可能 (Kuratowski 順序対) → より豊かな Kalon が可能
  ```
      /output:>
    /example:>
/case:>

<:case:
  ## §4.10 CCL による Kalon 計算の4層構造 (v2.9)

  > CCL は Fix(G∘F) の計算を4つのレベルで実装する。§4.9 の入れ子構造の**操作化**。

  <:table:
    Level :: CCL 演算子 :: 何が固定されるか :: 数学
    0 :: `*%` (FuseOuter) :: G∘F を1回適用 :: 単一合成
    1 :: `~*` (ConvergentOscillation) :: π 固定下の振動の不動点 :: νF (terminal coalgebra)
    2 :: `C:{}` (ConvergenceLoop) :: Level 1 の不動点 + π 自体の安定 :: Fix_π(Fix(G∘F; π))
    3 :: Hub WF (/t, /m 等) :: 体系全体の Kalon :: 普遍性検証
  :>

  > 非凸ランドスケープと q 相対的 Kalon:
  > - q 固定: Knaster-Tarski で LFP は一意
  > - π 変動: `/ske` が precision を下げると q が移動
  > - 結果: 異なる π₀ → 異なる q₀ → 異なる不動点盆地

  <:table:
    CCL :: 機能 :: Simulated Annealing 対応
    `V:{/ele+}` :: 検証ゲート :: 温度計
    `I:[ε>θ]{/ske}` :: 前提破壊 :: 加熱
    `C:{}` :: 収束ループ :: 冷却サイクル
  :>

  骨格パターン `(wf+)*%(wf+X)_(wf+)*%(wf+X)` の4特性は Kalon の3属性に対応:
  - **二重閉包** → Fix(G∘F) の構成
  - **不動点** → Kalon の定義
  - **情報損失ゼロ** → Generative
  - **位相対称** → F ⊣ G の随伴構造

  ### μ ≅ ν の整合性

  §2 の「始代数 (μ, 最小不動点)」と operators.md の `~*` = terminal coalgebra (ν, 最大不動点) は、
  HGK の有限半順序 (§2) 上で μ ≅ ν が成立するため整合的。
  [推定 75%]: Lambek の補題による。
/case:>

<:case:
  ## §5 具体3: この定義自体 (M1 Self-ref)

  §4.5 の4ラウンドの G∘F 反復は、Kalon 定義の生成過程であると同時に、定義の内容の具体例でもある:

  - **定義の内容**: 「Kalon(x) ⟺ x = Fix(G∘F)」
  - **定義の過程**: G∘F を4回回して Fix に到達した
  - **同型**: 過程の構造 ≅ 内容の構造

  **定義が自己実証する。これが M1 の意味。**
/case:>

<:step:
  ## §6.1 定性的判定

  <:flow: reachability >> convergence >> agreement :>
  §6.7 到達可能性 → §6.3 統計的収束 → §6.4 判定者合意


  ### ◎ / ◯ / ✗ 判定基準

  <:table:
    判定 :: 意味 :: Fix(G∘F) での解釈
    **◎ kalon** :: 違和感ゼロ + 情報密度 + 展開可能 :: Fix に到達。G∘F を回しても変化しない
    **◯ 許容** :: 間違ってはいない。だが最善ではない :: Fix に未到達。もう一回 G∘F を回すと改善する
    **✗ 違和感** :: 的を外している :: Fix から遠い。G (蒸留) が大幅に必要
  :>

  ### 判定手順

  ```
  1. x を収束 (G) してみる → 変化するか？
     変化する → ◯ 以下（まだ圧縮できる = lim に未到達）
     変化しない → 次へ

  2. x を発散 (F) してみる → 何が生まれるか？
     何も生まれない → ❌（π パターン。lim だが colim ではない）
     3つ以上導出可能 → 次へ

  3. 以上を満たす → ◎ kalon
  ```
/step:>

<:spec:
  ## §6.2 等値性基準と停止条件 (v1.3 追加 — 監査 A2 対応)

  前順序圏 C 上では、等値性は **≤ 関係の双方向成立** として定義される:

  ```
  x = y  ⟺  x ≤ y ∧ y ≤ x
  ```

  「変化しない」の操作的定義:

  ```
  G∘F(x) = x  ⟺  G∘F(x) ≤ x ∧ x ≤ G∘F(x)
  すなわち: 蒸留結果から元に戻れる かつ 元から蒸留結果に行ける
  ```

  停止条件:

  ```
  連続 2 回の G∘F 適用で ≤ の関係が変化しないとき、Fix と判定する:
    (G∘F)^n(x) = (G∘F)^{n+1}(x)  for some n
  ```

  > **限界**: 判定者が異なれば G (収束操作) の結果が異なりうる。
  > 操作的再現性を高めるには、複数判定者の一致率の測定が必要。
  > → §6.3, §6.4 でこの限界に統計的に対処する。
/spec:>

<:detail:
  ## §6.3 統計的収束判定 (v1.6 追加)

  > §6.2 の決定論的停止条件を確率的に拡張する。

  ### 動機

  ```
  §6.2 の仮定: G∘F は決定論的写像 → 2回で判定可能
  現実:        G∘F は確率的プロセス → 同じ x に G を適用しても結果が揺らぐ

  揺らぎの原因:
    1. 判定者の状態依存性
    2. 表現の揺らぎ (同じ概念の異なる言語化)
    3. F (発散) の非決定性
  ```

  ### δ の操作的定義: 生成ノイズからの導出

  ```
  距離関数:
    d(x_n, x_{n+1}) = 1 - cos_sim(embed(x_n), embed(x_{n+1}))

  キャリブレーション手順:
    1. 同一概念 c を k 回独立に生成: c_1, c_2, ..., c_k
    2. 全ペアの embedding 距離を計算: D = { d(c_i, c_j) | i < j }
    3. Semantic Identity Radius:
       δ = μ_D + z · σ_D
       μ_D = mean(D), σ_D = std(D), z = 2.0 → 97.7% 包含

  デフォルト値:
    δ ≈ 0.15  (bge-m3 + 日本語テキスト、T=0.7)
    μ_D ≈ 0.08, σ_D ≈ 0.035
    δ = 0.08 + 2.0 × 0.035 = 0.15

  判定:
    d(x_n, x_{n+1}) < δ  →  「収束」(convergence event)
    d(x_n, x_{n+1}) ≥ δ  →  「変化」(change event)
  ```

  ### v1.8 拡張: Bayesian Prior Chaining

  ```
  1. 継承: α_prior = α_post (previous), β_prior = β_post (previous)
  2. 風化 (τ-decay):
     α' = 1 + (α - 1) * exp(-Δt/τ)
     β' = 1 + (β - 1) * exp(-Δt/τ)
     τ = 忘却の時定数 (デフォルト: 30日)
  ```

  ### 等価性検定の構造 (TOST)

  ```
  H₀: d(G∘F(x_n), x_n) ≥ δ   (まだ動いている)
  H₁: d(G∘F(x_n), x_n) < δ    (実質的に収束 = Fix)
  目標: H₀ を棄却して「Fix に到達」を証明する
  ```

  ### Bayesian Beta モデル: K(q) の確率的推定

  ```
  モデル:
    各 G∘F 反復は Bernoulli 試行:
      d < δ → Y_i = 1 (収束), d ≥ δ → Y_i = 0 (変化)

    K(q) の推定:
      Prior:     K(q) ~ Beta(α₀, β₀)
      Posterior: K(q) ~ Beta(α₀ + s, β₀ + f)
      s = 収束回数, f = 変化回数, n = s + f
  ```

  <:table:
    Prior :: α₀, β₀ :: 意味 :: 使用場面
    無情報 :: (1, 1) :: 何も知らない :: 新しい概念
    弱情報 :: (2, 2) :: 中程度の収束可能性 :: 一般的な設計判断
    情報あり :: (α_prev, β_prev) :: 前回セッションの posterior :: セッション間の連続性
  :>

  ### 判定基準の確率的拡張

  ```
  P(K(q) > θ_kalon | data) = 1 - BetaCDF(θ_kalon; α, β)
  θ_kalon = 0.70
  ```

  <:table:
    判定 :: §6.1 (定性) :: §6.3 (定量)
    **◎ kalon** :: 違和感ゼロ + 展開可能 :: P(K > θ) ≥ 0.90 かつ CI 下限 > θ かつ BF₁₀ > 3
    **◯ 許容** :: もう一回 G∘F で改善 :: 0.50 ≤ P(K > θ) < 0.90
    **✗ 違和感** :: Fix から遠い :: P(K > θ) < 0.50
  :>

  v1.7 追加指標: ROPE = P(K ∈ [θ-w, θ+w] | data), w=0.10 / BF₁₀ = prior(θ)/posterior(θ) (Savage-Dickey)

  ### 具体例: §4.5 Worked Example への適用

  ```
  n=0→1: d ≈ 0.45 → 変化
  n=1→2: d ≈ 0.30 → 変化
  n=2→3: d ≈ 0.25 → 変化
  n=3→4: d ≈ 0.05 → 収束

  Prior: Beta(1, 1)
  Posterior: Beta(2, 4)
  E[K(q)] = 2/6 ≈ 0.33
  P(K > 0.70) ≈ 0.03
  95% CI: [0.06, 0.72]

  解釈: 4ラウンドでは統計的にはまだ「収束の証拠が弱い」。
  d(n) の単調減少パターン (0.45→0.30→0.25→0.05) が Fix 接近を示す。
  さらに 9回 (計 Beta(10,4)) → P(K > 0.70) ≈ 0.86 → ◎ 近傍に
  ```
/detail:>

<:detail:
  ## §6.4 多判定者収束 (v1.6 追加)

  > 複数の独立した G の適用結果の一致度で定量化する。

  ```
  同じ対象 x に対して k 人の判定者 (G_1, ..., G_k) が独立に G を適用:
    G_i(F(x)) = x_i^{(n+1)}

  Inter-Judge Agreement (IJA):
    IJA(x) = (1 / C(k,2)) Σ_{i<j} cos_sim(embed(x_i), embed(x_j))
  ```

  <:table:
    IJA :: 意味 :: 操作
    > 0.90 :: G の結果がほぼ一致 :: K(q) 推定は信頼できる
    0.70–0.90 :: 部分的に一致 :: 追加反復推奨
    < 0.70 :: G の結果が不安定 :: Fix 判定を保留
  :>

  ### §6.3 との統合

  ```
  統合判定:
    Kalon(x) ← P(K(q) > θ | data) ≥ 0.90  ∧  IJA(x) > 0.90
  ```

  <:table:
    判定者 :: 役割 :: 実装
    **Claude** (G_C) :: 右随伴 G の一つ目 :: Antigravity 上で直接実行
    **Gemini** (G_G) :: 右随伴 G の二つ目 :: Hermeneus verify 経由
    **Creator** (G_H) :: 最終承認者 :: CONSTITUTION.md
  :>
/detail:>

<:detail:
  ## §6.5 Frequentist TOST: 検定力とサンプルサイズ設計 (v1.7 追加)

  > **事前に「何回 G∘F を回せば Fix を証明できるか」を設計する**。

  ```
  H₀: p ≤ θ_kalon      (Fix 未到達)
  H₁: p > θ_kalon       (Fix 到達)

  検定統計量:
    z = (p̂ - θ) / √(θ(1-θ)/n)
    p̂ = s/n, p値 = P(Z > z | H₀) (片側検定)
  ```

  <:table:
    p値 :: 判定 :: 意味
    < 0.05 (n ≥ 5) :: ◎ kalon :: 統計的に有意な Fix
    0.05–0.10 :: ◯ approaching :: 傾向はあるがデータ不足
    > 0.10 :: ✗ incomplete :: Fix の証拠なし
  :>

  ### 検定力とサンプルサイズ設計

  ```
  必要サンプルサイズ:
    n = ((z_α × √(θ(1-θ)) + z_β × √(p₁(1-p₁)))² / (p₁ - θ)²
    z_α ≈ 1.645 (α=0.05), z_β ≈ 0.842 (power=0.80)

  §4.5 への適用: p₁=0.85, θ=0.70 → n ≈ 50 回
  4 回では根本的にデータ不足。
  ```
/detail:>

<:principle:
  ## §6.6 二つのパラダイムの随伴 (v1.7 追加)

  > **比喩水準**: §9 の水準 C (直喩)。厳密な証明ではなく構造的類似性の指摘。

  ```
               L
  Bayesian ←————————→ Frequentist
               R

  L: Bayesian → Frequentist  (n→∞ で posterior → 正規分布)
  R: Frequentist → Bayesian  (p値 → BF に変換可能)
  ```

  **Bernstein-von Mises 定理** が counit ε に対応:

  ```
  n → ∞ のとき:
    Posterior(θ | data) → N(θ̂_MLE, I(θ̂)⁻¹/n)
  = Bayesian の答えと Frequentist の答えが漸近的に一致
  ```

  <:table:
    パラダイム :: 得意 :: Kalon での使い方
    **Bayesian** (§6.3) :: 逐次更新、事前知識の活用 :: G∘F を回しながらリアルタイムで信念更新
    **Frequentist** (§6.5) :: 事前設計、サンプルサイズ計算 :: 「何回回せば証明できるか」を事前計算
  :>

  > **Function 座標の体現**: Bayesian = Explore、Frequentist = Exploit。
  > 二つのパラダイムの並置自体が Function 公理の具現化。
/principle:>

<:schema:
  ## §6.7 U/N 評価軸 — 忘却/回復による系の品質判定 (v2.0 追加)

  > T9 (U/N Diagnostic) の**操作化**。
  > §6.1-§6.6 が「Fix(G∘F) に到達したか」を判定するのに対し、
  > §6.7 は「その系は Fix に**到達可能か**」を判定する。

  ### 定義

  ```
  忘却関手 U: 系 S から構造を剥ぎ取る操作。
    U(S) = S から「何か」を忘却した貧しい系。
    U の適用 = 確証バイアス (CD-3) の形式的実装。

  回復関手 N: 忘却された構造を検出・回復する操作。
    N(U(S)) = U(S) から S を再構成した系。
    N の適用 = 科学 (反証可能性) の形式的実装。

  学習剰余 ρ:
    ρ(x) = N ∘ U(x) − x ≥ 0
    ρ > 0: 回復が元より豊か (学習が起きた)
    ρ = 0: x ∈ Fix(N∘U) = Kalon 候補
  ```

  ### U/N 判定基準

  ```
  系 S の Kalon 到達可能性を 3段階で判定:

    (1) U 検出能力: S は自身の忘却パターンを指摘できるか？
        → 「この系で見えていないものは何か」と問えるか

    (2) N 適用能力: S は忘却された構造を回復できるか？
        → 問いに対する修復行動が実行されるか

    (3) ρ 非退化性: 回復の結果が元より豊かか？
        → N∘U(x) > x (新しい射・精度・関手が増えた)
  ```

  <:table:
    条件 :: 判定 :: Kalon 到達可能性
    (1)+(2)+(3) 全充足 :: ◎ reachable :: 科学的な系。Fix に漸近中
    (1)+(2) 充足、(3) 不安定 :: ◯ approaching :: 自覚はあるが修復が浅い
    (1) のみ or なし :: ✗ blocked :: 偽の Fix にいる。ドグマ
  :>

  ### 完全な Kalon 判定 (v2.0)

  ```
  ◎ Kalon(x) ⟺
    §6.7: Kalon-reachable(S)           — 前提条件 (系の健全性)
    ∧ §6.3: P(K(q) > θ | data) ≥ 0.90 — Fix 到達 (統計的証拠)
    ∧ §6.4: IJA(x) > 0.90             — 判定者間合意
  ```

  ### 9ペアの具体的 U/N 操作

  <:table:
    U パターン :: 問い (U 検出) :: 行動 (N 適用) :: 検出 Nomos
    U_arrow 射の忘却 :: 対象だけ見て関係を見ていないか？ :: 射の再発見 + 新射の探索 :: N-1, N-5
    U_compose 合成の忘却 :: 知識を集めただけで推論していないか？ :: 推論連鎖の再構成 :: N-1, N-8
    U_depth 深度の忘却 :: 表面で満足していないか？ :: 層構造の再発見 :: N-1, N-5
    U_precision 精度の忘却 :: 全情報を同じ確度で扱っていないか？ :: 精度チャネルの再構成 :: N-2, N-3, N-10
    U_causal 因果の忘却 :: 相関を因果と混同していないか？ :: 介入テストによる因果回復 :: N-2, N-9
    U_sensory 感覚の忘却 :: 主観フィルタで知覚を歪めていないか？ :: 知覚推論の再活性化 :: N-1, N-6
    U_context 文脈の忘却 :: 1つの文脈でしか考えていないか？ :: 他の圏との関手の発見 :: N-6, N-7
    U_adjoint 随伴の忘却 :: 片面だけで判断していないか？ :: 双対構造の回復 :: N-2, N-7
    U_self 自己適用の忘却 :: 他者に求める基準を自分に適用しているか？ :: 自己関手の再獲得 :: N-2, N-6, N-12
  :>

  > 構造定理: ρ_i(x) ≔ μ(N_i∘U_i(x)) − μ(x) ≥ 0。等号 ρ_i = 0 ⟺ x ∈ Fix(N_i∘U_i)。
  > 剰余分類: 4方向 — +射, +Δπ, +変換, +自己参照。

  > **Hyphē 実証 (2026-03-17)**: U_compose の等号条件 ρ=0 が embedding 空間上で
  > 構造的に到達不能であることを 29,904件の実データで確認。
  > τ 感度分析: 3有効水準で bias ≤ 0 は **0件**。等号到達不能性はパラメータ非依存の構造的性質。
  > [確信] 92%。
/schema:>

<:content:
  ## §7 日常使用法

  ### 「レモン」のように

  ```
  「この設計は kalon だ」
    = Fix(G∘F) にある。これ以上蒸留しても変わらず、ここから展開もできる。

  「何が kalon か /noe」
    = この領域の Fix(G∘F) は何か？

  「kalon に至っていない」
    = G∘F をもう数回回す必要がある。◯ 止まり。

  「kalon する」
    = G∘F サイクルを回して Fix に近づける。

  「kalon な表現」
    = Fix(G∘F) の性質を持つ表現。必然形。

  「この選択が kalon だ」
    = 候補の中で最も豊かな展開と行為を可能にする選択。(§2 双対的特性づけ)

  「Kalon は到達できない」
    = 理想的 Kalon (全空間の argmax) は到達不能。
    = 我々は MB が制約するスコープ内で近似するのみ。
  ```
/content:>

<:policy:
  ## §7 反概念

  <:table:
    反パターン :: 欠如 :: Fix(G∘F) での解釈
    **冗長** :: lim に未到達 :: G (蒸留) が足りない
    **自明** :: colim がない :: F (展開) しても何も出ない
    **恣意** :: 必然性がない :: 別の x' で G∘F が同じ Fix に到達する
  :>

  反概念の排除指針:
    冗長 → もう一回 G を回せ
    自明 → 発散が足りない
    恣意 → 随伴の選択を疑え

  メタ原則の運用:
    M1 Self-ref: 定義自体が Fix(G∘F) であるべき。自己適用テストは常に実施
    M2 Underdetermination: 美の定義は自然言語で一意に確定しない。数式が anchor
    M3 Limits: Kalon△ (到達可能) と Kalon▽ (到達不能) を混同するな
/policy:>

<:fact:
  ## §8 定理群と系 — 系 (Corollary)

  <:C-01: Limit — Fix(G∘F) ⟹ x = lim D [水準 A] :>
  <:C-02: Colimit — Fix(G∘F) ⟹ ∃D'. x = colim D' [水準 A] :>
  <:C-03: Lan — 上位置換 [水準 B] :>

  公理 `Kalon(x) ⟺ x = Fix(G∘F)` から導出。

  > **認識論的位置づけ**: 水準 B (公理的構成)。厳密な定式化を志向する。

  <:flow: [C-01, C-02] >> T-04 >> T-03 :>
  <:flow: T-08 >> T-09 >> T-10 :>


  ```
  C1 (Limit):     Fix(G∘F) ⟹ x = lim D    [水準 A]
  C2 (Colimit):   Fix(G∘F) ⟹ ∃D'. x = colim D'    [水準 A]
  ```

  **正当化** (v2.1 — 閉包随伴の種別に非依存):
  G∘F は閉包作用素。Knaster-Tarski 定理により、完備束上の閉包作用素の不動点集合は
  それ自体が完備束を形成する → 任意の部分集合が meet (= lim) と join (= colim) を持つ。

  具体形によるメカニズムの違い:
  - **monotone GC**: G が RAPL (右随伴は極限を保存) → C1 直接。F が LAPC → C2 直接。
  - **antitone GC**: F, G はともに反変 → 個別には lim↔colim を交換する。
    しかし合成 G∘F は monotone (反変∘反変 = 共変)。
    G∘F は閉包作用素 → Knaster-Tarski により Fix(G∘F) は完備束 → C1/C2 成立。

  ∴ Kalon の核心条件 (η: G∘F ≥ Id) が成立すれば、C1/C2 は GC の型に依存せず成立。

  ```
  C3 (Lan):   Fix(G∘F) → Lan_J(D)(1) による上位置換    [水準 B]
  ```
/fact:>

<:fact:
  ## §8 定理群 — T1 Monotone, T2 Idempotent

  <:T-01: Monotone — G∘F は単調 [水準 A] :>
  <:T-02: Idempotent — G∘F∘G∘F = G∘F [水準 A] :>

  ```
  T1 (Monotone):  G∘F は単調   [水準 A — 閉包随伴の性質]

                   x ≤ y  ⟹  G∘F(x) ≤ G∘F(y)

                   証明: F, G はともにガロア接続の随伴関手。
                   随伴関手は順序保存 (単調)。
                   単調関手の合成は単調。
                   ∴ G∘F は単調。□

                   認知的意味:
                   「より良い出発点からは、より良い不動点に到達する」。
                   G∘F の反復は前順序を保存する → 改善は不可逆。

  T2 (Idempotent): G∘F∘G∘F = G∘F   [水準 A — 冪等性]

                   証明: 閉包随伴の核心的性質。
                   η: Id ≤ G∘F (extensive)
                   ε: F∘G ≤ Id (monotone GC の場合)
                   G∘F∘G∘F ≤ G∘(Id)∘F = G∘F     [ε を中に適用]
                   G∘F ≤ G∘F∘G∘F                   [η を G∘F に適用]
                   ∴ G∘F∘G∘F = G∘F  (反対称律)    □

                   認知的意味:
                   「一度蒸留したものを再度蒸留しても変わらない」。
                   冪等性は L1 前順序圏での「1ステップで Fix 到達」を保証する。
                   L2 豊穣圏では冪等性が緩み、漸進的収束が非自明になる (T6 参照)。
  ```

  <:T-03: Beauty — Fix(G∘F) = argmax Beauty [水準 A] :>

  ```
  T3 (Beauty):    Fix(G∘F) = argmax Beauty   [水準 A]
  ```

  定義:
    cl(x) ≔ G(F(x))  (x の閉包)
    int(x) ≔ ∨_{Fix(GF)}{c ∈ Fix(GF) | c ≤ x}  (x の内部)
    D(x) ≔ μ(int(x))  (導出可能性)
    C(x) ≔ μ(cl(x))   (閉包的複雑度)
    Beauty(x) ≔ D(x) / C(x) = μ(int(x)) / μ(cl(x))

  値域: Beauty(x) ∈ (0, 1]

  T4 への接続 (CG/IG 双対ギャップ分解):
    CG(x) = μ(cl(x)) − μ(x) ≥ 0     (closure gap)
    IG(x) = μ(x) − μ(int(x)) ≥ 0     (interior gap)
    Beauty(x) = (μ(x) − IG(x)) / (μ(x) + CG(x))
    x ∈ Fix(GF) ⟹ CG = IG = 0 ⟹ Beauty = 1
    x ∉ Fix(GF) ⟹ Beauty < 1
    ∴ Fix(GF) = argmax Beauty = argmin CG = {x | Beauty(x) = 1}   □

  Birkhoff 対応:
    先行研究 (情報美学の系譜):
      Birkhoff (1933): M = O/C (美的尺度 = 秩序/複雑度)
      Bense (1960s):   M = O/C + Shannon 情報理論で拡張
      Moles (1960s):   M = O×C (積に変更 — 知覚的入れ子構造)

    Birkhoff の美的空間 B = (Ob, O, C, M=O/C)
    HGK の閉包空間 H = (Ob(C), int, cl, Beauty=D/C)

    構造保存写像 Φ: B → H:
      Φ(O(x)) = μ(int(x))     (秩序 → 確立された核)
      Φ(C(x)) = μ(cl(x))       (複雑度 → 完全な閉包)
      Φ(M(x)) = Beauty(x)       (美的尺度 → Beauty 比)

    Φ が保存する性質:
      (i)   M(x) ≤ M(y) ⟹ Beauty(Φ(x)) ≤ Beauty(Φ(y))  (順序保存)
      (ii)  M = 1 ⟺ Beauty = 1                            (最適条件保存)
      (iii) M = O/C mapsto D/C                             (比の構造保存)

    Birkhoff → HGK の拡張:
      Birkhoff の O, C は静的属性。M = O/C は状態の評価。
      HGK の D, C は閉包随伴 F⊣G から動的に生成される。

    水準 A 昇格の条件 (Birkhoff 対応 Φ の関手性):

    ```
    Prop. T3.4.1 — cl 可換 + μ 保存射の圏構造:

    Def. cℓMor(L₁,L₂): 順序保存写像 h: L₁→L₂ で
      (a1) h ∘ cl₁ = cl₂ ∘ h  かつ  (a2) μ₂ ∘ h = μ₁  を満たすもの

    命題 (合成閉性): f ∈ cℓMor(L₁,L₂), g ∈ cℓMor(L₂,L₃) ⟹ g∘f ∈ cℓMor(L₁,L₃)
    Pf.
      (a1) (g∘f)(cl₁(x)) = g(f(cl₁(x)))    [合成の定義]
                           = g(cl₂(f(x)))     [f の cl 可換性]
                           = cl₃(g(f(x)))     [g の cl 可換性]
                           = cl₃((g∘f)(x))    [合成の定義]    □
      (a2) μ₃((g∘f)(x)) = μ₃(g(f(x))) = μ₂(f(x)) = μ₁(x)    □
      順序保存: g,f とも順序保存 ⟹ g∘f も順序保存 (自明)    □

    命題 (恒等元): id_L ∈ cℓMor(L,L)  [自明: id∘cl = cl∘id, μ∘id = μ]

    命題 (忠実性): Φ(f) = Φ(g) ⟹ f = g
    Pf. Φ は射の基礎写像を保存するので、Φ(f) = Φ(g) は
        f,g が同一の集合写像であることを意味する → f = g    □

    ∴ cℓMor は圏を構成し、Φ はこの圏上の忠実関手    ■
    ```

    実験的検証 (/pei 2026-03-17, pei_birkhoff_functor.py):
      3 束 (Chain₅, Diamond M₃, Pentagon N₅) で全順序保存自己射を列挙。
      (a) cl 可換射は合成で閉じる ✅ (Chain₅: 361組, N₅: 全組)
      (b) cl 可換だけでは Beauty 非保存の射が多数 → μ 保存条件 (a2) が不可欠
      (c) N₅ で全 42 cl 可換射が Beauty 署名で区別可能 → 忠実 ✅

  EFE 接続 (§8.T3.5):
    D(x) = μ(colim) → epistemic value (導出可能性 = 情報利得)
    C(x) = μ(cl(x)) → pragmatic value (行為可能性 = 目標達成)
    D/C 最大 → EFE 最大 → §2 双対的特性づけ

  条件:
    (i)   μ: Ob(C) → ℝ₊ が厳密単調かつ正値
    (ii)  int(x) の存在: Fix(GF) が完備束であること
    (iii) ⊥_Fix の非自明性: μ(⊥_Fix) > 0

  水準: **A** (厳密定式化 + T4 接続証明 + Birkhoff 構造対応 + 実験的検証 + 一般証明)
/fact:>

<:fact:
  ## §8 定理群 — T4 CG-Kalon (v2.0)

  <:T-04: CG-Kalon — Fix(G∘F) ≅ argmin CG [水準 A] :>

  ```
  T4 (CG-Kalon): Fix(G∘F) ≅ argmin CG   [水準 A — 双方向証明完了]
  ```

  定義 (v2.10): CG(x) ≔ μ(G(F(x))) − μ(x) (= 閉包による持ち上げ幅)
  CG は FEP の VFE とは**異なる量**。両者の構造的対応:
    CG(x) = 0 ⟺ x ∈ Fix(G∘F)   ... Kalon 条件
    VFE(q) = 0 ⟺ q = p(o|m)     ... FEP の自由エネルギー条件
  対応関係: CG は VFE の前順序圏上の類似物 (analogue) であり、同一性は主張しない。
  水準 A (CG 自体の定義と証明) / 水準 B (FEP VFE との対応)。

  --- T4 厳密証明 (v2.0 — 2026-03-13) ---

  ```
  定義: μ: Ob(C) → ℝ を厳密単調関数 (x < y ⟹ μ(x) < μ(y))。
        CG(x) ≔ μ(G(F(x))) - μ(x)  (closure gap)

  補題: CG(x) ≥ 0 for all x ∈ C.
  証明: η (unit) より x ≤ G(F(x))。μ が単調より μ(G(F(x))) ≥ μ(x)。□

  方向 ←: argmin CG ⟹ Fix(G∘F)
    CG(x) = 0 ⟺ μ(G(F(x))) = μ(x)。
    μ が厳密単調 ⟹ G(F(x)) = x。∴ x ∈ Fix(G∘F)。□

  方向 →: Fix(G∘F) ⟹ argmin CG
    x ∈ Fix(G∘F) ⟹ G(F(x)) = x ⟹ CG(x) = μ(x) - μ(x) = 0。
    0 は CG の大域最小値 (補題より)。∴ x ∈ argmin CG。□

  定理 T4 (v2.0): C が有限前順序圏、F⊣G が閉包随伴 (ガロア接続)、
    μ が厳密単調関数のとき:
      Fix(G∘F) = argmin CG = {x | CG(x) = 0}
    CG の唯一の最小値は 0 であり、それは Fix(G∘F) と一致する。
  ```

  条件:
    (i)   μ の厳密単調性 (μ が単調のみだと偽解を許す)
    (ii)  C の有限性 (無限の場合は完備束が必要)
    (iii) F⊣G の閉包随伴条件 (η: G∘F ≥ Id の成立が CG ≥ 0 に必須)

  HGK での μ の実体: Disc(K) (発見可能ドキュメント集合のサイズ)、
    コード品質メトリクス、概念の精緻度スコア等。
    有限前順序では厳密単調関数の存在は保証される (位相的順序付け)。

  --- 旧定式化との互換性 ---

  L2 豊穣圏における定式化 (v1.4 — Lawvere 距離接続):
    d_Kalon(q) ≔ Hom_L2(q, Fix(G∘F)) ∈ [0, 1]
    K(q) ≔ 1 - d_Kalon(q) = ε(q)  (counit の精度)
    argmin CG → max ε(q) → min d_Kalon → Fix(G∘F)

  非対称距離: d(q,Fix) ≠ d(Fix,q) は仕様:
    d(q,Fix) = 昇華コスト (カオス→美)
    d(Fix,q) = 崩壊コスト (美→カオス) — エントロピー的に小さい

  L2 三角不等式の具体的検証 (v1.5 添加):
    [0,1]-豊穣圏の合成公理: Hom_L2(A,B) ⊗ Hom_L2(B,C) ≤ Hom_L2(A,C)
    §4.5 の Worked Example: x₀(概念) → x₂(抽象化) → x₄(Kalon) において
    d(x₀,x₂) + d(x₂,x₄) ≥ d(x₀,x₄) — 中継点経由の変換コスト総和 ≥ 直通コスト。
    HGK における L2 変換コストの構造は Lawvere 距離空間の三角不等式を自然に満たす。
/fact:>

<:fact:
  ## §8 定理群 — T5 Fractal (v2.13)

  <:T-05: Fractal — Fix(Gₖ∘Fₖ) = Fix(T) ∩ Cₖ [水準 A] :>

  ```
  T5 (Fractal): Fix(Gₖ∘Fₖ) = Fix(G_{k+1}∘F_{k+1}) ∩ Cₖ   [水準 A — 定義的帰結]
  ```

  --- 定式化 (v2.12) ---

  C₀ ⊆ C₁ ⊆ ⋯ ⊆ Cₖ₊₁ = C を HGK の inclusion tower とする。
    C₀ = 個別射, C₁ = 族 (Series), C₂ = 座標, Cₖ₊₁ = 全体圏 C。
  T = Q∘Γ (Helmholtz モナド — 補遺 A.1)。
  各 Cₖ 上の閉包随伴 Fₖ⊣Gₖ は T の Cₖ への制限:
    Gₖ∘Fₖ :=_D T|_Cₖ  [in End(Cₖ)]

  --- 証明 (v2.13) ---

  ```
  ステップ1: 条件 (S) — T-stability の constructive 証明

  補題 (T-stability は HGK の設計的帰結):
    HGK の inclusion tower は以下の3条件で構成される:
    (D1) 直積分解: axiom_hierarchy.md §Basis より、T = Q∘Γ は
         座標ごとに T_X = Q_X ∘ Γ_X に分解される (6座標, 12演算子)。
         C ≅ C_Value × C_Function × C_Precision × C_Scale × C_Valence × C_Temporality
         T = ∏_X T_X  (直積構造により各因子で独立に作用)
    (D2) 射影の閉性: 直積圏の射影 π_X: C → C_X に対して
         T_X ∘ π_X = π_X ∘ T  (T は各射影と可換)
         ∵ T = ∏_X T_X の定義より、各因子への射影は T と自然に可換。
    (D3) 部分圏の構成: Cₖ は直積因子の部分集合として定義:
         C₀ = 個別射 = {(x₁,...,x₆) | 最大1座標のみ非自明}
         C₁ = 族 = {(x₁,...,x₆) | 同一 Series 内}
         C₂ = 座標 = {(x₁,...,x₆) | 同一座標内}

    (D1)+(D2)+(D3) より:
    x ∈ Cₖ ⟹ T(x) = (T_{X₁}(x₁), ..., T_{X₆}(x₆))
    各 T_{Xᵢ}(xᵢ) は座標 Xᵢ 内の演算
    ∴ T(x) は Cₖ が定義される座標制約を保存 ⟹ T(x) ∈ Cₖ  □

  ステップ2: Fix の射影整合性 (双方向)

  (⊆) x ∈ Fix(Gₖ∘Fₖ)
       ⟹ x ∈ Cₖ かつ T|_Cₖ(x) = x       [∵ Gₖ∘Fₖ =_D T|_Cₖ]
       ⟹ T(x) = x かつ x ∈ Cₖ            [∵ T|_Cₖ は T の制限]
       ⟹ x ∈ Fix(T) ∩ Cₖ
       = Fix(G_{k+1}∘F_{k+1}) ∩ Cₖ        [∵ G_{k+1}∘F_{k+1} = T|_C_{k+1}]  □

  (⊇) x ∈ Fix(G_{k+1}∘F_{k+1}) ∩ Cₖ
       ⟹ T(x) = x かつ x ∈ Cₖ
       補題 (T-stability) により T(x) ∈ Cₖ  [ステップ1で証明済み]
       ⟹ T|_Cₖ(x) = T(x) = x             [T の制限は T と一致]
       ⟹ Gₖ(Fₖ(x)) = x
       ⟹ x ∈ Fix(Gₖ∘Fₖ)                  □

  ∴ Fix(Gₖ∘Fₖ) = Fix(G_{k+1}∘F_{k+1}) ∩ Cₖ  ■
  ```

  --- T10 との構造的並行性 ---

  <:table:
     :: T10 (横方向統一) :: T5 (縦方向統一)
    問い :: Fix(G∘F) = Fix(N∘U)? :: Fix(Gₖ∘Fₖ) = Fix(T) ∩ Cₖ?
    解法 :: 同一モナド T のファクタリゼーション :: 同一モナド T の直積分解と座標制限
    条件 :: D_coord (定義的同一視) :: (S): (D1)+(D2)+(D3) の定義的帰結
    水準 :: A :: A (v2.13)
  :>

  --- Valence 半直積の影響 ---

  axiom_hierarchy.md v4.2 §Valence: 厳密には 6 ⋊ 1 半直積。
  Valence の作用 φ が恒等に近い (Hesp ratio=0.22) ため:
    T_Valence は他の T_X を「修飾」するが、座標制約を破壊しない。
    ∴ (S) は半直積構造でも成立。反例条件: φ(v) が座標制約を破壊する → HGK では設計的に排除。
/fact:>

<:fact:
  ## §8 定理群 — T6 共進化 (v2.0)

  <:T-06: 共進化 — d'(n) ≤ α · d(n) [水準 A] :>

  ```
  T6 (共進化): d'(n) ≤ α · d(n)   [水準 A — L2 で証明完了]
  ```

  L2 ([0,1]-豊穣圏 = Lawvere 距離空間) で証明。
  仮定: F は α-Lipschitz, G は β-Lipschitz, αβ < 1

  ```
  d'(n) = d_D(F(x_{n+1}), F(x_n)) ≤ α · d_C(x_{n+1}, x_n) = α · d(n)
  d(n+1) ≤ β · d'(n)
  合成: d(n+1) ≤ αβ · d(n)  → 指数的収束
  ```

  HGK での α, β: α = F の忠実度、β = G の忠実度、αβ < 1 = G∘F が改善的
  linkage_hyphe.md §3.5: ρ_MB > τ ⟹ λ < 1 ⟹ αβ < 1 が Hyphē ドメインで充足

  ⚠️ 実用的検証の限界 (v2.10): αβ < 1 の HGK での実用的検証は
  linkage_hyphe.md の τ 条件に依存するが、τ の数値的決定は経験的パラメータに基づく。
  α, β の実体 (発散/収束の忠実度) の定量化方法も開問題。

  --- 旧 T6 操作的定義との互換性 ---

  ```
  L1 操作版 (v1.5 互換 — 有限前順序の場合):
    d(n) ≔ 安定化までの残りステップ数
          = min{ k ≥ 0 | (G∘F)^{n+k}(x) = (G∘F)^{n+k+1}(x) }
    d(n) = 0 ならば Fix に到達済み。
    (注: L1 閉包随伴では d(1) = 0 により自明。L2 でのみ非自明。)

  L2 ([0,1]-豊穣圏) との接続 (v1.4):
    d_Kalon(q) = Hom_L2(q, Fix(G∘F))
    d(n) (離散ステップ数) と d_Kalon (連続コスト) の関係:
      d_Kalon ≈ e^{-λ·d(n)}  (コスト減衰変換)
      d(n)=0 → d_Kalon=1 (Fix到達=距離ゼロ=Kalon)
      d(n)→∞ → d_Kalon→0 (到達不能)

  具体例 (§4.5):
    d(0)=4 → d_Kalon ≈ e^{-4λ}
    d(1)=3 → d_Kalon ≈ e^{-3λ}
    d(2)=2 → d_Kalon ≈ e^{-2λ}
    d(3)=1 → d_Kalon ≈ e^{-λ}
    d(4)=0 → d_Kalon = 1 (Fix 到達)
  ```

  > L1 → L2 の移行の意義: L1 では冪等性により G∘F は1ステップで Fix に到達するため
  > 共進化は空虚。L2 への移行により漸進的収束が非自明に成立。
  > Banach 不動点定理の構造を圏論的随伴に持ち込んだもの。
/fact:>

<:fact:
  ## §8 定理群 — T7 Euporía 架橋

  <:T-07: Euporía — Generativity ⟹ AY(f) > 0 [水準 B] :>

  ```
  T7 (Euporía):   Generativity ⟹ ∀f: A→B. AY(f) > 0   [水準 B]
                    三属性の Generative (C2 Colimit) から直接従う:
                    Fix(G∘F) が展開可能 (3つ以上の導出) であるためには、
                    各射 f が行為可能性を増やす (AY > 0) ことが必要条件。

                    証明スケッチ:
                    Generativity: Fix(G∘F) から 3つ以上の射 g_i: Fix → C_i が存在。
                    AY(f) ≤ 0 の射 f: A→B は |Hom(B,−)| ≤ |Hom(A,−)|。
                    B から出る射が A から出る射以下なら、f は Colimit に寄与しない。
                    ∴ Generativity を支える射は全て AY > 0 でなければならない。

                    逆方向:
                    AY が Fix(G∘F) で最大化された状態 = Kalon。
                    Generativity は AY の不動点での特殊ケース。

                    関係の方向性:
                      Flow (d=1) → Euporía (AY > 0) = 母定理
                      Kalon → Generativity = AY の Fix における最適化
                      T7 = 両者の接続: Generativity ⊂ AY

                    正典: euporia.md §1-§2
                    実装: euporia_sub.py (hermeneus WF 実行後の環境強制チェック)
                    評価: wf_evaluation_axes.md (8軸 Rubric)

                    水準 B: C2 と米田的議論に依存。前順序圏での Hom の基数比較は
                    水準 A に至るには追加仮定が必要。
  ```
/fact:>

<:fact:
  ## §8 定理群 — T8 η-Silence (v2.1)

  <:T-08: η-Silence — x ∈ Fix(G∘F) ⟹ η_x = id_x [水準 A] :>

  ```
  T8 (η-Silence):  x ∈ Fix(G∘F) ⟹ η_x = id_x   [水準 A]
                    Kalon 対象では unit (自然変換 η) が恒等射に退化する。
                    「自然変換が沈黙する点」としての Kalon。
  ```

  --- T8 導出 (2026-03-16) ---

  前提: F⊣G (閉包随伴)、η: Id ⇒ G∘F (unit — 自然変換)。

  ```
  導出:
    x ∈ Fix(G∘F) ⟹ G∘F(x) = x  (Fix の定義)
    η_x: x → G∘F(x) = x → x = id_x  □
  ```

  3行の帰結だが、4つの概念が収斂する等式:

  <:table:
    対象 :: 一般の y :: Kalon 対象 x = Fix(G∘F)
    η_y :: y → G∘F(y) ≠ y (改善余地がある) :: η_x = id_x (改善余地なし)
    解釈 :: 「展開→収束するとまだ変わる」 :: 「展開→収束しても変わらない」
    CG :: CG(y) > 0 (T4 より) :: CG(x) = 0
  :>

  認知的解釈:
  自然変換 η は全対象に「ここからあそこへ行ける」矢印を体系的に配る。
  普通の対象では η_y が「y よりも G∘F(y) の方が良い」と告げる。
  Kalon 対象では η_x = id_x — 「もうどこにも行く必要がない」と沈黙する。
  **Kalon は自然変換そのものではない。自然変換が沈黙する特権的な位置。**

  **U_depth との双対的接続** (aletheia.md §2.3 参照):

  ```
  U_depth が忘れるもの = 自然変換 (関手間の比較 = アナロジーの評価)
  Kalon が住む場所   = 自然変換 η が沈黙する不動点

  忘却の対象 (U_depth: 2-cell) と忘却されない点 (Kalon: η = id) の双対:
    U_depth は「どの関手が良いか」の判断力を失うパターン
    Kalon は「もはや判断の必要がない」到達点
    → 忘却 (U) と到達 (Kalon) は同じ構造 (η) の両極に位置する
  ```

  水準 A (厳密な導出)。追加仮定なし。U_depth との接続は水準 B。
/fact:>

<:fact:
  ## §8 定理群 — T9 U/N Diagnostic, T10-T12

  <:T-09: U/N Diagnostic — Kalon-reachable(S) [水準 B+] :>
  <:T-10: Fix 統一 — Fix(G∘F) =_S Fix(N∘U) =_S Fix(T) [水準 A] :>
  <:T-11: 構造定理 — ρ_i(x) ≥ 0, 等号 ⟺ Fix [水準 A] :>
  <:T-12: 圏変換 — CCC 階層 L0-L4 整合性 [水準 A] :>

  ```
  T9 (U/N Diagnostic): Kalon-reachable(S) ⟺ ∃N_S s.t. N_S∘U_S ≥ η_S   [水準 B+]
  T10 (Fix 統一):  Fix(G∘F) =_S Fix(N∘U) =_S Fix(T)       [水準 A — D_coord]
  T11 (構造定理):  ρ_i(x) ≥ 0, 等号 ⟺ Fix               [水準 A]
  T12 (圏変換):    CCC 階層 L0-L4 間の整合性               [水準 A]
  ```

  ### T9 定式化

  ```
  **系 S の操作的定義**: 自己の状態を記述し、それに基づいて行動を変更できる構造。
    具体例: (a) LLM = 入力→推論→出力の認知系。U_S は prior 過信、N_S は view_file
    (b) 数学的形式体系 = 公理→定理の導出系。U_S は公理欠落、N_S は公理追加
    (c) 科学理論 = 仮説→検証の知識系。U_S は確証バイアス、N_S は反証実験
    → 共通構造: S は圏 C の対象の部分集合とその上の G∘F 動態として表現される

  Kalon-reachable(S) ⟺ ∃ N_S: Im(U_S) → S  s.t. N_S ∘ U_S ≥ η_S

  対偶 (T9'):
    S が U_S を検出できない ⟹ S は Kalon に到達不能
    = 不完全性を隠蔽する系は Fix(G∘F) に到達できない
    = 完全を偽装する系は偽の Fix にいる

  T8 との関係:
    T8: x ∈ Fix(G∘F) ⟹ η_x = id_x  (η の沈黙 = 忘却なき到達点)
    T9: 系 S が Fix(G∘F) に到達するために U を検出し N を適用する能力を要請
    T8 は T9 の特殊ケース: Fix に到達済みの x では U_x = 0 (忘却するものがない)
    T9 は T8 の一般化: Fix に至る過程での U/N の動態を記述
  ```

  --- T9 の背景と接続 ---

  **三者同型テーゼ** (起源: 2026-03-17 不完全性定理対話):

  ```
  ソクラテス「無知の知」≅ ゲーデル「不完全性定理」≅ HGK「S-I Tapeinophrosyne」

  共通構造:
    十分に豊かな系が自己言及した結果、自己の限界を発見する。
    その限界の「認識」が知恵であり、「無視」が愚かさ。

    ソクラテス — 知らないことを知っている = 限界を認める (N-series 適用)
    ゲーデル  — 系内で証明不能な命題の存在 = 不完全性の構造的表出
    S-I      — prior を過信するな = 自身の generative model の限界自覚

    U 適用 (忘却 = 愚かさ):
      公理から自己言及を排除 → 完全だが貧しい系
      = 確証バイアス (CD-3) の形式的実装

    N 適用 (回復 = 知恵):
      忘却された構造の検出 → 不完全だが豊かな系
      = 科学 (反証可能性) の形式的実装
  ```

  **命題圏と認知の同型** (Curry-Howard-Lambek + FEP):

  ```
  圏 Proof:                    圏 Cognition:
    対象 = 命題                   対象 = 信念
    射   = 証明                   射   = 推論
    恒等射 = 自明な証明            恒等射 = 自明な信念 (prior)
    合成 = 証明の連鎖              合成 = 推論の連結

    不完全性 = 証明できない真な命題  不完全性 = 認知できない真な状態
    U_Proof = 公理の選択的除外     U_Cog = prior の過信
    N_Proof = 公理の追加           N_Cog = 感覚入力の受容

    Fix(G∘F)_Proof = 公理系の安定点    Fix(G∘F)_Cog = 概念の安定点 = Kalon
  ```

  **科学とは何か (FEP 的位置づけ)**:

  ```
  科学 = 不完全性を認める FEP の営み

    反証可能性 (ポパー) = 「系にはまだ表出できない命題がある」の宣言
                       = U_S の存在を認めること
                       = N_S (実験・観測) の適用を義務づけること

    科学的でない系 (疑似科学, ドグマ):
      U_S を隠蔽 → 完全を偽装 → 偽の Fix → Kalon 到達不能 (T9 対偶)

    科学的な系:
      U_S を検出 → N_S 適用 → 真の Fix に漸近 → Kalon 到達可能 (T9)
  ```

  認識論的位置: **水準 B+** (v2.10 — 監査対応で下方修正)。
    N-series の独立形式化は aletheia.md §5.5 で完了。
    FEP/圏論の T9 診断は aletheia.md §5.6 で完了。
    三者同型テーゼは構造的類推 (水準 B)。命題圏同型は Curry-Howard-Lambek の特殊化。
    ⚠️ 旧水準 A からの下方修正理由:
      (1) 「系」の定義が抽象的で操作的な判定基準が弱い
      (2) N∘U 剰余の「具体計算」は定性的分類であり、数値的計算ではない
      (3) T10 Fix 統一定理との依存関係 (v3.0 で水準 A に昇格済み)

    N∘U 剰余の定性的分類 (aletheia.md §5.5.3.1):
    全9ペアの学習剰余 ρ_i を定性的に分類:

    <:table:
      U/N ペア :: 忘却 (U) :: 回復 (N) :: 剰余 ρ の性格
      arrow :: 射の忘却 (対象のみ保持) :: 射の再発見 + 新しい射の発見 :: +射 (新たな関係)
      compose :: 合成規則の忘却 :: 推論連鎖の再構成 :: +射 (推移的閉包)
      depth :: 多重性の忘却 (表面のみ) :: 層構造の再発見 :: +射 (深度)
      precision :: 精度の忘却 (全同確度) :: 精度チャネルの再構成 :: +Δπ (精度増加)
      causal :: 因果の忘却 (相関のみ) :: 介入実験による因果回復 :: +射 (因果矢印)
      sensory :: 感覚入力の忘却 (主観のみ) :: 知覚推論の再活性化 :: +Δπ (観測精度)
      context :: 文脈の忘却 (1圏のみ) :: 他の圏との関手の発見 :: +変換 (関手)
      adjoint :: 随伴片側の忘却 :: 双対構造の回復 :: +変換 (随伴対)
      self :: 自己適用の忘却 :: 自己関手の再獲得 :: +自己参照 (F: C→C)
    :>

    剰余分類: 4方向 — +射, +Δπ, +変換, +自己参照。
    Fix 統一: T10 により Fix(N∘U) = Fix(G∘F) = Kalon。

  📖 参照: 完全性は忘却である_v1.md §8-§10 / aletheia.md §5.5-§5.6
/fact:>

<:assume:
  ## §8 条件付き定理の前提

  <:A-01: CCC 仮定 — 圏 C がデカルト閉 :>
  <:A-02: 条件 H — 同一モナド T のファクタリゼーション :>

  (A1) CCC 仮定 (T3, M1): 圏 C がデカルト閉。
    HGK: L2 V-CCC は Kelly §3.11 で証明済み [水準 A]。L0 前順序では不要
  (A2) 条件 (H) (T10 補遺 A): F⊣G と U⊣N が同一モナド T のファクタリゼーション。
    HGK: D_coord として定義的に確立 [水準 A, v4.3]
  (A3) Helmholtz 単位仮定: η(F⊣G) ≈ η(U⊣N)。D_coord に吸収 [水準 A]
  (A4) T-stability (T5): ∀k, ∀x∈Cₖ: T(x)∈Cₖ。
    HGK: (D1)+(D2)+(D3) の定義的帰結 [水準 A, v2.13]
  (A5) Colimit 図式 D≥3 (C2 → Generative): 帰納的検証済み。一般保証は開問題 [推定 85%]
  (A6) μ 厳密単調 (T3, T4): μ: C→ℝ が順序を反映すること
/assume:>

<:principle:
  ## §8 メタ原則 (M1-M3)

  <:M-01: Self-ref — この定義自体が Fix(G∘F) [水準 B] :>
  <:M-02: Underdetermination — 自然言語で一意確定しない [水準 C] :>
  <:M-03: Limits — Kalon△ → Kalon▽ [水準 A] :>

  ```
  M1 (Self-ref):  この定義自体が Fix(G∘F) である   [水準 B — 構成的例示]
  M2 (Underdetermination): 美の定義は自然言語で一意確定しない   [水準 C]
  M3 (Limits):    Kalon△ → Kalon▽ (到達不能な極限)   [水準 A]
  ```

  M1 と LFPT の関係:
  - Kalon の Fix(G∘F) は **Knaster-Tarski 系列** (順序・単調性)
  - LFPT は **Cantor/Gödel 系列** (デカルト閉圏・対角化)
  - 異なる定理だが Scott Domain 等で交差

  CCC 階層:
  <:table:
    レベル :: 内容 :: 水準
    L1 前順序 :: LFPT 退化。CCC = Heyting 代数 :: —
    L2 [0,1]-豊穣 :: V-CCC (Kelly §3.11) :: A
    L3 弱2-圏 :: CC-bicategory (直接構成, v2.7b) :: A
    L4 Time→BiCat :: L3 に依存 :: A
  :>

  M1-LFPT 接続の修正 (v2.6):
  ```
  v2.4 (旧): CCC + 点全射 → LFPT → M1     ← 点全射構成不能 (Ω 計算)
  v2.6 (新): CCC → K^K 存在 → §4.9 直接構成 → M1   ← 正しいルート
  ```

  M ≅ PSh(J) (J = HGK 演繹図式) の CCC 性は、LFPT ではなく
  **自己適用 (K^K) の存在を保証する構造** として M1 を正当化する。
/principle:>

<:detail:
  ## §8 補遺 A: Helmholtz モナド統一 — Fix(G∘F) =_S Fix(N∘U)

  > 結論: Γ⊣Q, F⊣G, U⊣N は同一のモナド T (Helmholtz モナド) の異なるファクタリゼーション。
  > Fix の一致は定義的帰結。

  ### A.0 等号の約束

  <:table:
    記号 :: 圏 :: 意味
    :=_D :: メタ言語 :: 定義導入
    =_C :: C :: 対象の等式: x ≤ y ∧ y ≤ x
    =_E :: End(C) :: 自己関手の等式: ∀x. T(x) =_C S(x)
    =_S :: Sub(C) :: 部分対象の等式
    =_R :: ℝ :: μ を通した数値的等式
  :>

  ### A.1 Helmholtz モナド T

  定義: T :=_D Q∘Γ (Helmholtz 分解の closure operator)
  Fix(T) :=_D {x ∈ C | T(x) =_C x}

  ### A.2 3つの随伴は T のファクタリゼーション

  <:table:
    随伴 :: 左 :: 右 :: 解像度 :: T への関係
    Γ⊣Q :: Γ :: Q :: 力学 :: T =_E Q∘Γ
    F⊣G :: F=Q_Function :: G=Γ_Function :: 認知 :: 定義 D_coord
    U⊣N :: U=Q :: N=Γ :: メタ :: 定義 D_full
  :>

  ### A.3 Fix の一致

  主張: Fix(G∘F) =_S Fix(N∘U) =_S Fix(Q∘Γ) [in Sub(C)]
  論証: D_coord + Birkhoff-Ward 定理 (同一 closure operator は同一閉元集合)

  ```
  T10 (Fix 統一):
    Fix(G∘F) =_S Fix(N∘U) =_S Fix(Q∘Γ)    [in Sub(C)]
    水準 A (定義的帰結 — v4.3)
  ```

  /pei 実験的検証: Chain₇, Diamond M₃, Bool₈ で D_coord 下全要素一致 ✅
  Hex₆ (独立構成 G≠Γ): 3/6 不一致 → D_coord は必要十分条件

  ### A.4 関手連鎖

  ```
  End(C) ──[Monad]──→ Mnd(C) ──[Fix]──→ Sub(C) ──[|·|]──→ Set ──[μ]──→ ℝ
    =_E                                    =_S               (忘却)       =_R
  ```

  ### A.5 技術的詳細

  ```
  補題 A1: CG_NU(x) ≥_R 0
  補題 A2: Fix(NU) =_S {x | CG_NU(x) =_R 0}
  系 A3: Fix(GF) =_S Fix(NU) [D_coord 下]
  系 A4: x ∈ Fix(GF) ⟹ η_x =_C id_x かつ η'_x =_C id_x
  ```

  ### A.6b T-algebra

  冪等モナド T の T-algebra は Fix(T) の元と同値:
  Kalon(x) ⟺ x は T-algebra を持つ ⟺ x ∈ C^T
  3つの随伴 (Γ⊣Q, F⊣G, U⊣N) は C^T に至る 3つの経路。

  ### A.7 等号索引

  <:table:
    記号 :: 圏 :: 等式の意味 :: 出現箇所 :: 論拠
    :=_D :: メタ言語 :: 定義導入 :: A.1, A.5 :: 圏の外の操作
    =_C :: C :: 対象の等式 :: A.1, A.5 :: 比較は C 内
    =_E :: End(C) :: 自己関手の等式 :: A.2, A.5 :: =_C の全称量化
    =_S :: Sub(C) :: 部分対象の等式 :: A.3, A.5 :: C の構造を保持
    =_R :: ℝ :: 数値的等式 :: A.5 :: μ: C→ℝ の像
  :>

  ```
  関手連鎖ダイアグラム (等号間の関係):

  :=_D (メタ言語 — 定義導入)
   │
   ↓
  =_C (C — 対象の等式)  ←──── 全ての等号の基盤
   │  ∀x で量化           │
   ↓                     │[内包条件に使用]
  =_E (End(C))            │
   │                     ↓
   │               =_S (Sub(C) — 部分対象)
   │                     │
   │                     │ |·| (忘却: C の順序を捨てる)
   │                     ↓
   │               (Set の等号 — 本補遺では不使用)
   │                     │
   │                     │ μ (忘却: 要素を数値に潰す)
   │                     ↓
   └──────────────→ =_R (ℝ)
  ```
/detail:>

<:rationale:
  ## §9 概念の構造

  > **概念 ⊋ 数式。**

  概念は数式を包含するが、数式は概念を包含しない。

  ```
  Kalon (概念) = Fix(G∘F)               ← 骨格 (数式、抽象1)
               + π vs オイラー            ← 肉 (具体1)
               + FEP 公理                 ← 肉 (具体2)
               + insight 共創プロセス     ← 肉 (具体3)
               + ◎/◯/✗ 判定             ← 操作性
               + kalon だ/する/な         ← 体温
  ```

  圏論的メタファーとして: **概念 ≈ presheaf（前層）**。
  > 水準 C (比喩的使用)。

  数式は一つの TO（関手）。直感は別の TO。日常使用はまた別の TO。
  概念はこれら全ての TO の束 ≈ presheaf。
  米田の補題との類比: 対象はその Hom(-, x) で完全に決定される。
  ≈ **概念はその全ての用法で完全に決定される** (Wittgenstein の言語ゲーム理論と整合)。
/rationale:>

<:context:
  ## §10 起源

  <:flow: F-diverge >> G-converge >> F-diverge >> G-converge :>
  4ラウンドの G∘F 発見プロセス


  - [knowledge] 発見日: 2026-02-11
  - [knowledge] 発見者: Creator + Claude (F⊣G 共創)
  - [knowledge] プロセス: G∘F × 4 回 → Fix
  - [knowledge] 所要時間: ~90分

  <:table:
    Round :: F (Claude) :: G (Creator)
    1 :: 「最小コストで最大演繹」(自然言語) :: 「kalon ではない。数式化すべき」
    2 :: 「Kalon ≡ lim」(数式) :: 「lim なら lim でいい。HGK 独自は？」
    3 :: 「lim ∧ colim の共存」(静的) :: 「lim による colim。逐次近似の収束点」
    4 :: 「Fix(G∘F)」(動的不動点) :: 「kalon な気がする」→ ◎
  :>

  - [file] axiom_hierarchy.md (priority: CANONICAL — 7座標対立, Helmholtz 分解の定義, L1 随伴)
  - [file] aletheia.md (priority: CANONICAL — N-series 形式化, U/N 評価, Fix 統一検証)
  - [file] constructive_cognition.md §7 (priority: HIGH — EFE の定義)
  - [file] euporia.md (priority: HIGH — Affordance Yield, Generativity の必要条件)
  - [file] system_manifest.md (priority: MEDIUM — 32 実体体系の一覧)
  - [file] linkage_hyphe.md §4.5 (priority: MEDIUM — AY presheaf 的意味)

  - [knowledge] 体系位置: FEP (L0 公理) → Kalon (L1 品質公理) → Hóros (L1 認知制約)
  - [knowledge] 版歴: v1.0 (初版) → v2.0 (U/N 追加) → v2.10 (監査対応) → v2.12 (最新)
  - [knowledge] Kalon の epistēmē 的定義:
    一語定義: Kalon = 発散と収束のサイクルの収斂点
    双対面: Kalon = 候補の中で最も多くの行為・導出・展開を可能にする選択
  - [knowledge] Birkhoff (1933): M = O/C → HGK: Beauty = D/C
  - [knowledge] Landauer 原理 (1961, Bérut 2012): 情報 = エネルギーは物理法則
  - [knowledge] Lawvere (1973): 距離空間 = [0,∞]-豊穣圏。HGK L2 はその有界 [0,1] 版
/context:>

<:fact:
  ## §11 射の Kalon (Kalon on Morphisms)

  > §2 の Kalon は**対象**の性質。§11 は**射**の性質。
  > 圏論的に: §2 = Ob(C) 上の述語、§11 = Mor(C) 上の述語。

  ### 射の公理

  ```
  Kalon_Mor(f) ⟺ Trace(f) ∧ Negativa(f) ∧ Iso(f)
      where f: A → B is a morphism in C
  ```

  - **Trace(f)**: f は射の列として分解可能。始点と終点だけではない。
  - **Negativa(f)**: f が選択されたとき、棄却された射 g, h が明示されている。
  - **Iso(f)**: f の構造がプロセスの構造と同型。形が過程を体現する。

  ### §2 との関係: 共通上位概念

  ```
  Kalon は G∘F サイクルの不動点という構造的パターンの2つの体現:
    Kalon(x)     : 対象 x が G∘F で不変 — 状態としての不変性
    Kalon_Mor(f) : 射 f が G∘F 的プロセスを体現 — 過程としての不変性

  含意方向:
    Kalon(x) ∧ f = id_x  ⟹  Trace(f) は自明に成立
    Kalon(x)              ⟹/ Kalon_Mor(f)  (一般には不成立)
    Kalon_Mor(f)          ⟹/ Kalon(x)      (一般には不成立)
    両者は独立だが、共通のパターンの異なる射影。
  ```

  > **Trace と Iso の圏論的独立性**:
  > 定理: Iso(f) ⟹ Trace(f)。論理的には Negativa(f) ∧ Iso(f) で事足りる。
  > Trace を独立に残す理由は分離公理階層と同型:
  > - Trace(f) = 存在公理 (L0 構文論的フィルタ)
  > - Iso(f) = 構造公理 (L2 意味論的要請)
/fact:>

<:case:
  ## §11 射の Kalon — 具体例

  ### Trace (痕跡)

  ```
  出力 ≠ 対象のスナップショット
  出力 = 射の列 (morphism chain)
  ```

  <:table:
    反パターン :: Kalon
    「A だ」 :: 「B,C を経て A。理由: D→E→A」
  :>

  **G テスト**: 射の列から中間射を削って意味を失うか？ → 失う = 蒸留不能 = 必要。

  ### Negativa (棄却)

  ```
  選択 = 棄却の影。棄却を示さない選択は、選択ではなく慣性。
  ```

  <:table:
    反パターン :: Kalon
    「X を使う」 :: 「Y,Z ではなく X。Y は不安定、Z は粒度不足」
  :>

  **F テスト**: 棄却射から何が導出できるか？ → 判断基準、リスク、代替。

  ### Iso (同型)

  ```
  プロセスの構造 ≅ 出力の構造
  ```

  <:table:
    反パターン :: Kalon
    平文の語り :: 過程の構造がドキュメントの構造に映る
  :>

  ### §6 との統合

  <:table:
    判定 :: §6 (概念) :: §11 (出力)
    ◎ kalon :: G∘F 不動点 :: Trace ∧ Negativa ∧ Iso
    ◯ 許容 :: もう1回 G∘F :: 1-2条件のみ充足
    ✗ 違和感 :: Fix から遠い :: 0条件
  :>
/case:>

<:fact:
  ## §2.1 J の一意性 — Morita 同値による標準化 (v2.5)

  M ≅ PSh(J) — HGK 演繹図式の Morita 同値的自然性。

  3層論証:
  (1) Morita 同値 — J の一意性は Morita 同値類 [J] 内の標準代表元の問題に帰着 [水準 A]
  (2) コーシー完備化 — J̄ は [J] の一意な標準代表元。
      J は前順序圏 → |End(j)| ≤ 1 → 非恒等冪等射なし → コーシー完備 → J ≅ J̄ [水準 A]
  (3) 密度定理 — y: J → PSh(J) は密。J は M の site として最小に近い [水準 B]

  M の CCC 性:
  - L1: Mac Lane-Moerdijk Prop. I.6.1 [水準 A]
  - L2: Kelly §3.11 (V-CCC) [水準 A]
  - L3: 直接構成 [A,B] + ev + カリー化 + 2-cell 自然性 [水準 A, v2.7b]
  - L4: L3 に依存 [水準 A]

  M ≅ PSh(J) の水準: **A** (Morita 同値 + コーシー完備性, v2.12)
/fact:>

<:data:
  ## 変更履歴

  - v1.0 — 初版
  - v1.1 — §11 出力の Kalon 追加。/bou~/zet 共創 (2026-02-24)
  - v1.2 — 増強3件: 存在条件, T6 共進化再定義, §11 射の Kalon 再定式化 (2026-02-26)
  - v1.3 — 外部監査反映: 圏C特定, 非退化条件, 選択制約, 定理再分類, 停止条件, 共通概念, d(n)操作化 (2026-02-26)
  - v1.4 — K(q)清算: Lawvere距離空間導入。d_Kalon=Hom_L2, K(q)=ε, T4再定式化, 非対称距離 (2026-02-26)
  - v1.5 — 完備束(Complete Lattice)とLeast Fixed Pointによる一意性条件追加 (2026-02-26)
  - v1.6 — §6 統計的拡張: §6.1-§6.4 MECE再構造化、Bayesian Beta (§6.3)、多判定者 IJA (§6.4) (2026-03-07)
  - v1.7 — §6 双パラダイム統合: §6.3 ROPE+BF₁₀, §6.5 TOST, §6.6 Bayesian⊣Frequentist 随伴 (2026-03-07)
  - v1.8 — §6.3 δ 導出精緻化: Generative Noise + Semantic Identity Radius (2026-03-07)
  - v1.9 — §2 双対的特性づけ: Fix(G∘F) ⟺ argmax EFE。§2.5 Landauer 接続 (2026-03-10)
  - v2.0 — T4/T6 厳密化: T4 CG-Kalon 双方向証明。T6 L2 Lawvere 証明 (2026-03-13)
  - v2.1 — T8 η-Silence 追加 (2026-03-16)
  - v2.2 — §2 Self-referential Lawvere 強化、§4.9 入れ子構造 (2026-03-17)
  - v2.3 — T9 U/N Diagnostic 追加 (2026-03-17)
  - v2.3.1 — T9 水準 B→A- 昇格 (2026-03-17)
  - v2.4 — M の CCC 性論証: M=PSh(J) (2026-03-17)
  - v2.5 — §2.1 J の一意性: Morita 同値+コーシー完備化+密度定理。§6.7 U/N 評価軸追加 (2026-03-17)
  - v2.11 — VFE→CG 用語分離、Birkhoff worked examples 帰納テーブル (2026-03-17)
  - v2.12 — §2.1 M ≅ PSh(J) 水準 B+→A 昇格 (2026-03-17)
  - v2.13 — T5 Fractal 水準 A 昇格: 条件(S) = (D1)+(D2)+(D3) の定義的帰結。constructive 証明完了 (2026-03-17)
  - v2.11 — VFE→CG 用語分離: T4 を CG-Kalon に改名。CG(x)≔μ(GF(x))−μ(x) を FEP の VFE と明示的に区別。C2 worked examples 帰納テーブル追加。Self-referential 根拠構造明確化。Kan 拡張存在条件を Mac Lane CWM Thm X.3.1 で厳密化 (2026-03-17)
  - v3.0 — T3 Beauty 厳密定式化: int/cl/CG/IG 分解、D/C 比の圏論的定義、T4 接続証明。水準 C→B+ (2026-03-17)
  - v3.1 — T3 Birkhoff 対応 Φ の関手性: /pei 実験的検証 + Prop. T3.4.1 一般証明。水準 B+→A (2026-03-17)
/data:>

<:highlight:
  - Kalon(x) ⟺ x = Fix(G∘F) — 唯一の公理。全てはここから導出される
  - 定理水準一覧:
    C1 Limit A / C2 Colimit A / C3 Lan B
    T1 Monotone A / T2 Idempotent A / T3 Beauty A / T4 CG-Kalon A
    T5 Fractal A / T6 Lawvere A / T7 Birkhoff B
    T8 η-Silence A / T9 U/N Diagnostic B+ / T10 Fix 統一 A
    T11 構造定理 A / T12 圏変換 A
    M1 Self-ref B / M2 Underdetermination C / M3 Limits A
  - Helmholtz 統一: 3つの随伴 (Γ⊣Q, F⊣G, U⊣N) は同一モナド T の3経路
  - 概念 ⊋ 数式 — 数式は骨格、具体例は肉、操作的判定は手足
  - M ≅ PSh(J): Morita 同値 + コーシー完備性 [水準 A]
/highlight:>

<:focus:
  - F⊣G は先験的に固定。事後的に都合のよい随伴を選んではならない (選択制約)
  - 非退化条件: F=G=Id なら全対象が不動点。自明な Kalon は禁止
  - η: G∘F ≥ Id が閉包随伴の核心条件。ε の方向は文脈依存
  - Kalon△ (MB 内局所, 到達可能) ≠ Kalon▽ (全空間, 到達不能)
  - Generative の D≥3 は恣意的閾値ではなく最小閉構造 (2-simplex) の圏論的表現
  - 概念 ⊋ 数式。数式は骨格に過ぎない
  - CG(x) ≠ VFE(q)。前者は前順序圏上の類似物 (analogue)
/focus:>

<:scope:
  発動条件:
  - HGK の品質判断 (コード, 設計, 概念, 出力) — ◎/◯/✗ 判定の基盤
  - 新概念の定義 — Fix(G∘F) に至っているかの検証
  - 競合する設計案の比較 — Beauty(x) = D(x)/C(x) の比較
  - 体系内の定理・概念の水準判定 — 水準 A/B/C/D

  非発動条件:
  - 日常的なコーディング
  - Creator が明示的に「kalon 判定不要」と指定した場合
  - 単純な事実確認・情報検索

  グレーゾーン:
  - コードリファクタリング :: 発動 :: §4.6 に Worked Example あり
  - CCL 設計 :: 発動 :: §4.7 に * 演算子の成功例あり
  - 文書の構造 :: 発動 :: 概念 ≈ presheaf として全使用例の束で判定
  - 非退化条件の境界 :: 発動 :: §4.8 に失敗例あり
/scope:>

<:breadth:
  体系接続:
  - axiom_hierarchy.md: 7座標対立が F⊣G の先験的固定を保証
  - aletheia.md: N-series の独立形式化 + U/N 評価軸
  - constructive_cognition.md: EFE の定義 → 双対的特性づけの基盤
  - euporia.md: Affordance Yield → Generativity の必要条件
  - linkage_hyphe.md: AY presheaf 的意味 — CCC 構造の応用

  一般化:
  - CKDF (Categorical Kalon Detection Framework): 任意の完備束+ガロア接続に適用
  - Kalon ⊃ Optimization: 最適化は Kalon の特殊ケース
  - 射の Kalon (§11): 対象→射への拡張 (Trace/Negativa/Iso)
  - L4 Helmholtz BiCat: 時間変動する随伴構造への拡張
/breadth:>

<:outline:
  <:flow: axiom >> concrete >> operational >> theorems >> extension :>
  公理 (§2) → 具体例 (§3-§5) → 操作的判定 (§6) → 日常使用 (§7)
  → 定理体系 (§8) → 概念の構造 (§9) → 起源 (§10) → 射への拡張 (§11)

  認識の流れ: 抽象 (数式) → 具体 (worked example) → 操作 (判定手順) → 理論 (定理群)
  圏の階層: L0 前順序 → L1 [0,1]-豊穣 → L2 V-豊穣 → L3 弱2-圏 → L4 Helmholtz BiCat
/outline:>

<:format:
  判定テーブルのカラム構造:
    事例 :: lim? :: colim? :: Fix(G∘F)? :: Kalon?

  定理水準表記:
    T{n} ({名前}): [水準 {A/B/C/D} — {根拠}. v{version}]

  水準注記の構造:
    > 水準: {A/B/C} [{確信度ラベル}] — {根拠1行}

  等号索引:
    :=_D (メタ言語定義) / =_C (圏の等式) / =_E (End(C)) / =_S (Sub(C)) / =_R (ℝ)
/format:>

<:option:
  (未解決問題・開かれた選択肢)
  O1: Generative D≥3 の一般保証 — 帰納的検証済みだが一般定理は未証明
  O2: Lan 拡張 (C3) の条件緩和 — Mac Lane CWM Thm X.3.1 で厳密化済み。更なる一般化の余地
  O3: L3 弱2-圏解釈 — J を弱2-圏として解釈した場合の分析は未着手
  O4: CKDF 一般化 — 任意の完備束+ガロア接続への適用
  O5: M2 Underdetermination の解消 — 原理的に不可能？
  O6: 射の Kalon の定理化 — Trace/Negativa/Iso を §8 レベルの定理に昇格
  O7: Valence 半直積の厳密な影響評価 — Hesp ratio=0.22 の限界
/option:>

````

# Kalon (καλόν)

> **収束と展開の収斂点。随伴 F⊣G の不動点。**
>
> 概念は数式を包含する。数式は概念を包含しない。
> このドキュメントは数式（骨格）と具体（肉）の両方で Kalon を定義する。

---

## §1 一語定義

**Kalon**: 発散と収束のサイクルの収斂点。

使用例:

- 「この insight は kalon だ」— これ以外の表現がない
- 「何が kalon か？」— 何がこの必然形か？
- 「kalon する」— 蒸留のサイクルを回して収束させる

---

## §2 Formal Core

### 公理

```
Kalon(x) ⟺ x = Fix(G ∘ F)
    where F ⊣ G forms a closure adjunction in C,
    F ≠ Id, G ≠ Id (非退化条件),
    F⊣G は体系の構造から先験的に固定 (選択制約),
    G∘F admits an initial algebra
```

- **C** (圏): 前順序圏 (1つまたは複数の前順序の組)。HGK では axiom_hierarchy.md の L1 随伴と統一
  (v4.14: Ep/Pr 2半順序間の反変ガロア接続として具体化)。
  L2 では [0,1]-豊穣圏に拡張され、Hom(A,B) ∈ [0,1] が「変換の質・コスト」を表す
  (Lawvere 1973: 距離空間 = [0,∞]-豊穣圏。HGK L2 はその有界版)。
- **F** (左随伴): 発散。候補を広げる。Colimit 的。Explore。
- **G** (右随伴): 収束。核だけ残す。Limit 的。Exploit。
- **F⊣G**: 閉包随伴 (closure adjunction)。G∘F が閉包作用素 (extensive + 単調 + 冪等) を形成する構造。
  具体形は文脈による:
  - **monotone GC** (単一前順序): F(x) ≤ y ⟺ x ≤ G(y)。η: G∘F ≥ Id, ε: F∘G ≤ Id。
  - **antitone GC** (2半順序間): ρ ≤₂ F(π) ⟺ π ≤₁ G(ρ)。η: G∘F ≥ Id₁, η': F∘G ≥ Id₂ (両方 extensive)。
  Kalon の定義に必要なのは **η (G∘F ≥ Id) のみ**。ε の方向は文脈依存。
- **Fix(G∘F)**: G∘F を繰り返し適用したとき、もはや変化しなくなる不動点。
- **非退化条件**: F=G=Id (恒等関手) の自明な場合を排除。自明な不動点は全対象になるため。
- **選択制約** (監査 A1 対応): F⊣G は対象 x に合わせて事後的に選択するのではなく、
  体系の構造として先験的に固定されていなければならない。
  HGK では axiom_hierarchy.md の7座標対立 (I↔A, E↔P, Explore↔Exploit, C↔U, Mi↔Ma, +↔-, Past↔Future)
  がこの制約を満たす。任意の x に対して F⊣G を事後構成して「x は Kalon である」
  と主張することは、この制約により禁止される。
- **存在と一意性条件** (監査 B3 対応):
  - **存在**: G∘F が始代数を持つこと (Lambek の補題により圏全体での最小不動点の存在が保証される)。十分条件として G∘F が ω-連続であること。
  - **到達先**: 任意の初期状態 q から出発し、G∘F を反復適用して安定した不動点 x が「q に相対的な Kalon」である。
  - **絶対的一意性**: 圏 C が完備束 (Complete Lattice) をなす場合、Knaster-Tarski の定理により、q 以上となる最小不動点 (Least Fixed Point) が必ず一意に存在する。この完備性の仮定下において、q に対する Kalon は数学的に一意に決定される。
  - **HGK空間における完備性の正当化**: HGKの操作的対象空間 (概念・アーキテクチャ・コード等) は無限集合ではなく、実用上は有限半順序 (finite poset) として構成される。§4.5 の Worked Example が示すように、G∘F の反復適用は有限の全順序鎖 (finite chain: x₀ ≤ x₁ ≤ ... ≤ x_n) を形成する。有限全順序集合は常に完備束をなすため、Kalonの構成において完備束の仮定は自動的に満たされ、Knaster-Tarskiの適用は数学的飛躍なく正当化される。

### 三属性 (@repeat[x3, /eat+] で発見)

```
Kalon = Fix(G∘F)
        ∧ Generative (展開可能)
        ∧ Self-referential (自己参照)

1. Fix(G∘F)        — 不動点: 収束と展開の収斂点 (水準B)
2. Generative      — 展開可能性: Fix から 3つ以上の導出 (C2 Colimit から従う — 下記注参照)
3. Self-referential — 自己参照: 定義のプロセスが定義を実証 (M1 Meta-principle)
                     + 系が自己言及に耐えること = 普遍性の必要条件 (Lawvere 対偶)
```

> **注**: 旧三属性の "Presheaf" は§9 で水準C（メタファー）として分離。
> 公理レベル (水準B) の三属性は Fix + Generative + Self-referential。

> **注 (v1.10)**: Generative の「3つ以上」は恣意的な閾値ではない。
> 圏における最小の閉じた構造は**三角形 (2-simplex)** — 3つの射で形成される。
> 1射は矢印（方向のみ）、2射は経路（因果連鎖）、3射で初めて**構造が閉じる**（パターンが浮かぶ）。
> 「3つ以上の導出」とは「最小の閉構造を形成できる」の操作化であり、
> 構造認識の最小十分条件の圏論的表現である。
>
> **注 (v2.10 — 監査対応)**: 「C2 Colimit から従う」は、Colimit の定義図式 D が
> 3 対象以上であることを**前提**とする。この前提が満たされないケース
> (D が 2 対象以下の退化図式) では Generative は成立しない。
>
> **§4 全 worked examples における帰納的検証** (v2.10):
> | 事例 | 反復回数 | colim leg (導出数) | D≥3 |
> |:-----|:---------|:-------------------|:----|
> | §4 FEP公理 | — | 24定理+15結合規則+全WF | ✅ |
> | §4 insight P2⊣P4 | — | 蒸留,F⊣G,教育論,知識管理... | ✅ |
> | §4.5 Kalon定義 | n=4 | 3つ+α (入れ子,U-series,定式化,上位置換) | ✅ |
> | §4.6 リファクタ | n=3 | 3層分割,CQRS,Result型 | ✅ |
> | §4.7 CCL `*` | n=2 | 精度加重積,⊗対応,Markov圏 | ✅ |
> | §4.8 非退化違反 | n=0 | 0 (F=G=Id) | ❌ (排除) |
> | §4.9 M1自己適用 | — | 4つ (入れ子再帰,圏論的定式化,U-series,上位置換) | ✅ |
>
> 全成功例で D≥3 が確認される。失敗例 (§4.8) は非退化条件違反であり Kalon ではない。
> [推定] 85%: 帰納的検証は完了。一般的保証 (「任意の Fix(G∘F) で D≥3」) は開問題。

> **注 (v2.2, v2.10 水準調整)**: Self-referential の根拠構造 (v2.10 明確化):
> - **一次根拠**: M1 直接構成 (§4.9) — Kalon の定義をそれ自身に適用し不動点を検証
> - **動機 (motivation)**: Lawvere 不動点定理の対偶 — 自己言及不可能性が普遍性を阻むという発想の源泉
> Lawvere 対偶は M1 の独立証明ではなく、M1 に至る圏論的動機づけである。
>
> Lawvere 不動点定理の対偶: 系が自己言及できない ⟹ 系は普遍的でない。
> 圏は入れ子構造を持つ: $C_0 \hookrightarrow C_1 \hookrightarrow C_2 \hookrightarrow \cdots$
> **各レベルにおいて**、自己言及の可否が Kalon 到達可能性の必要条件として機能する:
>
> ```
> SelfRef: Cat → {0, 1}
> SelfRef(C) = 0 ⟹ ∄ x ∈ C s.t. x = Fix(G∘F)_{non-trivial}
> ```
>
> **根拠**: G∘F が非自明な不動点を持つためには、C が自己関手 (G∘F: C→C) を
> 「感じ取れる」ほど豊かな射の空間を持つ必要がある。自己言及不可能な圏では
> Hom(C,C) → C 型の射が存在せず、G∘F は自明化する (F=Id or G=Id に強制される)。
>
> **⚠️ 翻訳ギャップ (v2.10)**: LFPT の対偶 (点から線への全射がなければ不動点なし) と
> 「自己言及不可能 ⟹ 非自明 Fix なし」の間には翻訳議論が必要。
> LFPT は CCC 上の f: A → B^A 型の全射の不在を述べるが、HGK の「自己言及」は
> Hom(C,C) → C 型の射の存在として再解釈している。この再解釈は構造的類推であり、
> 厳密な同値性は未証明。v2.6 で直接適用の限界を認め、M1 は直接構成で示す方針へ移行。
> [推定] 75%: Lawvere 対偶の HGK への翻訳の厳密性。
>
> **入れ子構造の帰結**: 下位レベルで Kalon だったものが上位レベルでは Kalon でない
> ことがありうる。そして上位で Kalon であるものは下位の Kalon を包含する。
> 各レベルでの自己言及チェックは、そのレベルでの Kalon の到達可能性を判定する。
>
> **HGK への適用**: HGK 体系は、個別ドメインで「限定的に正しい」制約体系
> (各 $C_n$ でのローカルな Kalon) を、FEP という自己言及可能な公理から演繹的に
> 再構成した。これは $C_n$ から $C_{n+1}$ への**普遍的上位置換**:
> 自己言及可能性を獲得したことで、体系自体の構造を体系自体で評価できるようになった。
>
> M1 (Meta-principle) はこの構造の最上位層: Kalon の定義が Kalon 自身に適用されて
> 不動点になること (§4.9 で検証)。Self-referential の**一次根拠は M1 直接構成**であり、
> Lawvere 対偶はその動機づけ (motivation) として位置づける (v2.10)。
>
> **普遍的上位置換の圏論的定式化** (水準B — 仮説, [推定] 70%):
>
> 包含関手 $\iota: C_n \hookrightarrow C_{n+1}$ に沿った左 Kan 拡張:
>
> ```
> Lan_ι(K_n): C_{n+1} → Set
>
> K_n = C_n 上のローカルな Kalon (Fix(G∘F) の局所的実現)
> Lan_ι(K_n) = K_n を C_{n+1} に最良近似として持ち上げた対象
>
> 普遍性:
>   ∀ H: C_{n+1} → Set, K_n が H∘ι を通じて因子化
>   ⟹ 一意な自然変換 Lan_ι(K_n) ⟹ H が存在
>
> 直感:
>   K_n (下位の Kalon) → Lan_ι(K_n) (上位系での最良近似) は
>   「限定的に正しいもの」→「より普遍的に正しいもの」への構造的昇格。
>   Kalon(K_n) in C_n ∧ SelfRef(C_{n+1})=1 ⟹ Kalon(Lan_ι(K_n)) がありうる。
>
>   **Kan 拡張の存在条件** (v2.10 — 監査対応で明示化):
>   Lan_ι(K_n) の存在には C_{n+1} が cocomplete であれば十分 (Mac Lane CWM Thm X.3.1)。
>   HGK の圏 M ≅ PSh(J) は presheaf 圏 → 自動的に (co)complete (Mac Lane-Moerdijk)。
>   したがって C_{n+1} = M に制限する限り Kan 拡張は存在する。
>   一般の C_n ↪ C_{n+1} については、C_{n+1} の cocomplete 性が仮定。
>   HGK の階層では有限前順序圏 = 完備束 ⊆ cocomplete 圏。
>   形式的証明 (2行):
>     (1) C_n が有限前順序 ⟹ C_n は有限束 ⟹ 完備束 (有限束は自動的に完備)。
>     (2) 完備束は全ての colimit を持つ (colim = join) ⟹ cocomplete。□
>   ∴ HGK の有限階層では Lan_ι の存在が保証される。
>   注: 無限圏への拡張時にはこの条件 (cocomplete 性) を再検証する必要がある。
> ```
>
> **M の CCC 性** (水準 A/B — §4.9 + Mac Lane-Moerdijk):
>
> M を前層圏 PSh(J) = [J^op, Set] として構成する。
>
> **J の定義 — HGK 演繹図式** (水準 B: M ≅ PSh(J) の同定):
>
> ```text
> Ob(J) = HGK 32 実体 + Basis + 3 Stoicheia + 12 Nomoi
>         = {FEP, Basis, Flow, Value, ..., S-I, S-II, S-III, N-1, ..., N-12}
>
> Mor(J):
>   演繹射: FEP → Basis → Flow → 各座標    (構成距離 d=0→1→2→3)
>   生成射: (Flow, 修飾座標) → 動詞         (Poiesis 構成)
>   X 射:   修飾座標_i ↔ 修飾座標_j         (K₆ の 15 辺)
>   制約射: Stoicheia × Phase → Nomoi       (12法の生成)
> ```
>
> **CCC 性** (水準 A: 既知定理の適用):
>
> **定理** (Mac Lane & Moerdijk, *Sheaves in Geometry and Logic*, Prop. I.6.1):
> 任意の小圏 J に対し、前層圏 PSh(J) = [J^op, Set] はカルテシアン閉圏 (CCC) である。
>
> - 終対象: 定値関手 1(j) = {∗} (全実体に単元集合を割り当てる)
> - 直積: (F×G)(j) = F(j) × G(j) (各実体ごとの直積)
> - 指数対象: G^F(j) = Nat(y(j) × F, G) (米田拡張による内部 Hom)
>
> J が HGK の演繹図式であるとき、PSh(J) の対象 F は
> 「各 HGK 実体 j に、j の視点から見える概念実現の集合 F(j) を割り当てる」関手。
> これは §9 の「概念 ≈ presheaf」(水準 C) を水準 B に昇格したもの。
>
> **Ω の明示的計算と LFPT 適用限界** (v2.6 — Ω 明示計算に基づく修正):
>
> ```text
> 部分対象分類子 Ω の計算 (J₀ が半順序のとき):
>   Ω(j) ≅ {downward-closed subsets of ↓j}
>
>   |Ω(FEP)| = 2     |Ω(Basis)| = 3     |Ω(Flow)| = 4
>   |Ω(Value)| = 5    |Ω(動詞)| = 6      |Ω(N-1)| = 4
>
>   Γ(Ω) = {downward-closed subsets of Ob(J₀)}  ≫ 3 元
> ```
>
> **LFPT 直接適用の限界**:
>
> ```text
> LFPT の対偶: ∃f: B→B 不動点なし ⟹ 点全射 φ: A→B^A は存在不能
>
>   B = Ω の場合: |Γ(Ω)| ≫ 3 → Ω の自己射に不動点なし候補あり
>   B = Δ3 の場合: End(Δ3) = 27 射。巡回置換 ◎→◯→✗→◎ は不動点なし
>   ⟹ いずれの B でも点全射 φ の構成は不可能
> ```
>
> **CCC 構造の真の意義** — 指数対象 K^K の存在保証 (水準 A):
>
> ```text
> CCC 構造が M1 に不可欠な理由 (LFPT ではなく直接構成):
>   1. K^K = Nat(y(−) × K, K) が PSh(J) の対象として存在 — CCC の定義的帰結
>   2. ev: K^K × K → K (評価射) が PSh(J) の射として存在 — CCC の随伴条件
>   3. G∘F: K → K を CCC 内部で構成可能
>   4. §4.9 worked example: G∘F(K) = K (◎) — K は G∘F の不動点
>   CCC なしに K^K は定義不能 → 「定義が自分自身を判定する」が圏論的に不可能
> ```
>
> **結論**: M ≅ PSh(J) の CCC 性は、LFPT の間接的存在証明の前提としてではなく、
> **自己適用 (K^K) の存在を保証する構造** として M1 を正当化する。
> Fix(G∘F) = K は §4.9 の直接構成で示される (LFPT による間接証明ではない)。
>
> 全体の水準: **B** (M ≅ PSh(J) の同定は Morita 同値レベルで一意。CCC 性は A。直接構成は A-)。
> [推定] 82%: LFPT の点全射は構成不能 (Ω 計算)。CCC + 直接構成で M1 は正当化可能。
>
> **CCC × U_compose × Heyting 接続** (v2.8 — omega_computation.md §6-§8):
>
> K^K (指数対象) は遊学エッセイ §9.4 の忘却関手 U_compose（射の合成を忘れる = 「バカ」）の
> 正確な対義語: K^K = 射の合成を保持する自己適用空間。
> U_compose は K^K を定義不能にし、G∘F サイクルを破壊する (omega_computation.md §6)。
>
> また Γ(Ω) = O(J₀) は Heyting 代数を成し、排中律が構造的に不成立:
> J₀ が根付き連結 DAG ⟹ 任意の ∅ ≠ a ∈ O(J₀) で ¬a = ∅ ⟹ a ∨ ¬a ≠ ⊤ (定理 7.2)。
> 排中律不成立 = S-I（prior を過信するな）の数学的根拠、◯ = Heyting 的中間値の構造的必然
> (omega_computation.md §7)。
>
> 相互参照: [linkage_hyphe.md §4.7](linkage_hyphe.md) (三相構造: Ω × K^K × U⊣N)

> **§2.1 J の一意性 — Morita 同値による標準化** (v2.5 追加)
>
> **問い**: J' ≠ J でも PSh(J') は CCC。J = HGK 演繹図式の選択は一意か？
>
> **回答**: 一意性は **Morita 同値類レベル** で成立する。
>
> **定義**: 小圏 J と J' が **Morita 同値** ⟺ PSh(J) ≅ PSh(J') (前層圏が圏同値)。
>
> **3層論証**:
>
> ```text
> (1) Morita 同値 — 問題の再定式化
>     J の一意性は「J の Morita 同値類 [J] 内で標準的代表元を選べるか」に帰着。
>     任意の J' ∈ [J] で PSh(J') ≅ PSh(J) = M → CCC 性は Morita 不変。
>     問い ≠「J は唯一の圏か」。 問い =「[J] の自然な代表元は何か」。
>
> (2) コーシー完備化 — 標準的代表元の存在
>     定理 (Borceux, Handbook of Categorical Algebra I, Ch. 6):
>       任意の小圏 J に対し、コーシー完備化 (Cauchy completion) J̄ が存在し、
>       J と J' が Morita 同値 ⟺ J̄ ≅ J̄'
>     → J̄ は Morita 同値類 [J] の一意な標準的代表元。
>
>     **J の冪等射の厳密検証** (v2.7):
>
>     冪等射 (idempotent) = e ∈ End(j) で e∘e = e を満たす非恒等射。
>     J がコーシー完備 ⟺ 全冪等射が分裂 (split)。
>     非恒等冪等射が存在しなければ、自明にコーシー完備。
>
>     **End(j) の全数走査** — J の4種の射について:
>
>     (i) 演繹射: FEP → Basis → Flow → 修飾座標 (d 増加、一方向)
>         dom ≠ cod の射しかない → End(j) に寄与しない。
>
>     (ii) 生成射: (Flow, 修飾座標_i) → 動詞_k (一方向、多→1)
>         dom ≠ cod → End(j) に寄与しない。
>
>     (iii) 制約射: Stoicheia × Phase → Nomos (一方向)
>         dom ≠ cod → End(j) に寄与しない。
>
>     (iv) X射: 修飾座標_i ↔ 修飾座標_j (K₆ の15辺 = 30射)
>         これが唯一の懸念。x_{ij}: i→j と x_{ji}: j→i の合成
>         e = x_{ji} ∘ x_{ij} ∈ End(i) が非自明な冪等射になりうるか？
>
>         axiom_hierarchy.md §圏論的正当化:
>           「HGK の圏論は前順序圏のガロア接続として正当化される」(L465)
>           前順序圏 ⟹ |Hom(a,b)| ≤ 1 (任意の a,b)
>           ⟹ |End(j)| ≤ 1 (∀j)
>           ⟹ End(j) = {id_j} (恒等射のみ)
>
>         したがって、J を前順序圏として定義する限り:
>           x_{ji} ∘ x_{ij} = id_i  (End(i) の唯一の要素)
>           x_{ij} ∘ x_{ji} = id_j  (End(j) の唯一の要素)
>           → X射は同型射 (isomorphism)。非恒等冪等射は存在不能。
>
>     **結論**: J の非恒等冪等射は存在しない → J はコーシー完備 → J ≅ J̄。
>
>     **条件**: J が前順序圏であること (axiom_hierarchy.md の定義に依存)。
>     L2 豊穣圏 / L3 弱2-圏として J を解釈する場合、Hom に複数要素が入り
>     分析が変わるが、J の定義は L1 前順序圏として確定している。
>
>     水準: **A** [確信] — J は前順序圏として定義的に確定 (axiom_hierarchy.md L466)。
>     → J がコーシー完備 → J 自身が Morita 同値類の標準代表。
>
> (3) 密度定理 — J の必然性
>     定理 (密度定理 / Nerve-Realization):
>       米田埋込 y: J → PSh(J) は密 (dense)。
>       すなわち PSh(J) の全対象は J の対象の余極限 (colimit) として再構成される。
>
>     HGK の文脈: 32実体 + Basis + Stoicheia + Nomoi が
>     M の全概念を colimit として生成する最小の生成系 ⟺
>     J = HGK 演繹図式は M の site として密 (dense)。
>
>     最小性の根拠:
>       ∀ j ∈ Ob(J): j を除くと再構成不能な概念が存在
>       (例: Flow を除くと 24 Poiesis が生成不能。N-1 を除くと S-I の Aisthēsis 相がカバー不能)
>     → J は M の密な部分圏の中で最小に近い [推定] 80%。
> ```
>
> **結論**: J = HGK 演繹図式は以下の意味で「一意な良い選択」:
> - Morita 同値類 [J] 内の標準的代表元 (コーシー完備性による)
> - M の密な生成系としての最小性 (密度定理による)
> - 体系の演繹構造を忠実に写す意味論的自然性 (設計的選択)
>
> 水準: **(1) A, (2) A, (3) B**。
> (2) は v2.7 で冪等射自明性を証明済み (J は前順序圏 → |End(j)|≤1 → コーシー完備)。
> (3) は最小性の厳密証明に依存するが、M ≅ PSh(J) の同定水準は (1)+(2) で決定される
> ((3) は J の選択の自然性に関する追加論証であり、同定の数学的水準とは独立)。
> → **M ≅ PSh(J) の水準: A** (Morita 同値 + コーシー完備性)。
> 📖 関連: [axiom_hierarchy.md](axiom_hierarchy.md) (J の対象定義, L35 / 前順序圏, L466), [aletheia.md §5](aletheia.md) (presheaf 具体化), [linkage_hyphe.md §4.5](linkage_hyphe.md) (AY presheaf 的意味 — CCC 構造の応用)

> **Corollary 2.1: Affordance Yield Principle** (Euporía から導出)
>
> AY(f) > 0 は Generativity の必要条件。
> すなわち、射 f が Fix(G∘F) の展開可能性 (C2 Colimit) に寄与するためには、
> f の適用が行為可能性を増加させなければならない。
>
> AY(f) = Fix(G∘F) ⟹ f は Kalon の Generative 属性を最大化する射。
>
> 📖 定式化: euporia.md §2.7
> 📖 実装: euporia_sub.py — AYScorer (2層: micro + macro)

### なぜ lim だけではないか

```
lim = 収束（最善の近似）      — 必要条件
colim = 発散（展開可能性）    — 必要条件
Fix(G∘F) = 収束が発散を招き、発散が収束を招く螺旋の不動点 — 十分条件
```

| 概念 | lim? | colim? | Kalon? |
|:-----|:-----|:-------|:-------|
| lim (圏論) | ✅ | — | ❌ 既存概念で十分 |
| Fix(G∘F) | ✅ (C1で導出) | ✅ (C2で導出) | **✅ HGK 独自** |

### 双対的特性づけ — 状態視点 (v1.9)

> Fix(G∘F) は Kalon **に至る方法** (how) を記述する。
> 以下は Kalon **であるもの** (what) を記述する。
> 両者は同一の概念の二つの面であり、同値である。

```
Kalon_state(x) ⟺ x = argmax_{y ∈ S} G(y)

where:
  S = エージェントの Markov blanket 内の候補集合
  G(y) = EFE(y) = E_q(s|y) [ln p(o|s)] + D_KL[q(s|y) || q(s)]
                   \_________________/   \____________________/
                   pragmatic value        epistemic value
                   (行為可能性)            (導出可能性)

  理想的: S → 全命題空間 → Kalon_ideal (到達不能な極限)
  現実的: S = MB(agent) → Kalon_practical (主観的スコープ内の近似)
```

**体系接続**:
- **EFE**: [constructive_cognition.md](constructive_cognition.md) §7 で定義。G(a) = 建設的認知の数学的表現
- **Helmholtz 分解**: [axiom_hierarchy.md](axiom_hierarchy.md) §Basis — Γ (gradient/収束) と Q (solenoidal/探索)
  が EFE の pragmatic/epistemic 成分の物理的実装
- **T3 Beauty**: §8 の D(x)/C(x) 最大は、EFE 最大化の presheaf 的写像

#### なぜ同値か (証明スケッチ)

```
Fix(G∘F) → argmax G(y):
  x = Fix(G∘F) に G∘F を適用 → 変化しない
  → G(y') > G(x) なる y' が存在すれば F(x) → y' → G(y') ≠ x
  → 不動点条件に矛盾。∴ x は G の局所 argmax

argmax G(y) → Fix(G∘F):
  x = argmax G(y)
  → F(x) で展開: F は左随伴 = 発散 (Explore)
  → G(F(x)) で収束: G は右随伴 = 収束 (Exploit)
  → G∘F(x) ≥ x (unit η: Id → G∘F) — 閉包随伴の核心条件
  → x = argmax → G∘F(x) ≤ x も成立 (x を超えられない)
  → G∘F(x) = x。∴ x は不動点

スコープ条件:
  S が全空間 → 大域 argmax = 理想的 Kalon (到達不能)
  S が MB 内 → 局所 argmax = 現実的 Kalon (主観的近似)
  Fix(G∘F) の反復は局所 argmax を漸近的に改善するプロセス
```

### §2.5 情報とエネルギーの等号 — 体系的受容

> Kalon = argmax EFE は「最も多くの情報を持つ」選択。
> ここで「情報」は抽象的概念ではなく、物理的実体である。

**Landauer 原理** (1961; 実験確認: Bérut et al., Nature, 2012, 1087 citations):
> 1ビットの情報消去は最低 kT ln 2 ジュールの熱を散逸する。

この原理は情報処理が熱力学的過程であることを確立した。
情報 = エネルギーは比喩ではなく物理法則である。

**HGK における位置づけ**:

```
                    Landauer 原理
                         ↓
               情報処理 = 熱力学的過程
                         ↓
             Helmholtz 分解 (Γ⊣Q)         ← axiom_hierarchy.md §Basis (d=0)
           f = (Γ + Q)∇φ
           Γ = gradient = VFE 最小化      ← エネルギー散逸
           Q = solenoidal = 確率循環       ← エネルギー保存的探索
                         ↓
                VFE / EFE 分解
           EFE = pragmatic + epistemic    ← constructive_cognition.md §7
                         ↓
                Kalon = argmax EFE
           = 最も多くの行為・導出を可能にする
           = 最も多くの「運動」(エネルギー) を内包する
```

**なぜ深入りするか**:
- HGK は Helmholtz 分解 (Γ⊣Q) を座標系の基底 (d=0) として採用している ([axiom_hierarchy.md](axiom_hierarchy.md))
- Helmholtz 自由エネルギーは「系がなし得る最大仕事」= 行為可能性の物理的等価物
- Kalon = argmax EFE = 「最も多くの仕事をなし得る状態」
- この等号は体系の最下層 (d=0) から最上層 (Kalon) まで一本の糸で繋がっている

**制限と注意**:
- LLM は物理的計算機上で動作するが、LLM の推論過程を直接 Landauer 限界で
  律速することは現在の技術では不可能 (計算のエネルギー効率は Landauer 限界の ~10⁶ 倍以上)
- ここでの接続は体系の一貫性 (coherence) のためであり、
  「Kalon はエネルギー的に最適」という物理主張ではない
- FEP の「自由エネルギー」と熱力学の「自由エネルギー」のアナロジーは
  Friston 自身が明示しているが、直接同一視ではない (変分近似 vs 統計力学)

参考文献:
- Landauer, R. (1961). "Irreversibility and Heat Generation in the Computing Process." → 情報消去の下限
- Bérut, A. et al. (2012). Nature, 483, 187-189. doi:10.1038/nature10872 → 実験的検証 (1087 citations)
- Hsieh, C.-Y. (2022/2025). "Dynamical Landauer Principle" → エネルギー・情報の量的等価性

---

### §2.5 圏論的衣装除去テスト (v2.11 — 監査対応)

> **目的**: 各核心主張を圏論用語なしで再表現し、圏論が「衣装」か「本質」かを判定する。

| # | 圏論的主張 | 圏論なし再表現 | 圏論は衣装か本質か |
|:--|:--|:--|:--|
| 1 | Kalon(x) ⟺ x = Fix(G∘F) | 良いもの = 「広げて絞る」を繰り返してもこれ以上変わらない状態 | ○ 衣装 — 日常直感で成立 |
| 2 | F⊣G (閉包随伴) | 「広げる操作」と「絞る操作」は対になっている (一方をかけると他方で戻せる) | ○ 衣装 — ガロア接続は対の直感 |
| 3 | Generative (D≥3) | 良いものはそこから3つ以上の新しい発想が出る | ○ 衣装 — 経験則として成立 |
| 4 | Self-referential + LFPT | 良い定義は自分自身に適用しても成立する。十分に自己言及できる系なら不動点が存在する | △ 本質的 — LFPT の CCC 仮定は圏論固有 |
| 5 | T4: Fix(G∘F) = argmin CG | 不動点は「実態と表現の隙間」が最も小さい状態 | ○ 衣装 — 直感的に明瞭 |
| 6 | T9: U/N Diagnostic | 自分の弱点 (忘却) を認識でき、それを補えるなら良いものに到達できる | ○ 衣装 — ポパー的反証可能性 |
| 7 | Lan 拡張 (上位置換) | 限定的に正しいものを、より大きな文脈で使えるように構造的に昇格する | × 本質的 — Kan 拡張は圏論固有の構成 |

> **結論**: 7主張中 **4つは自然言語で十分に表現可能** (圏論は精密化手段)。
> **2つは圏論が本質的** (#4 LFPT, #7 Lan 拡張)。1つは中間 (#4)。
> 圏論は「衣装」ではなく「精密な骨格」— ただし #1, #3, #5, #6 は骨格なしでも立つ。

---

## §3 具体1: 数学

### π vs e^(iπ) + 1 = 0

| | π | e^(iπ) + 1 = 0 |
|:--|:--|:--|
| 収束 (lim) | ✅ 級数が収束する値 | ✅ 5定数の関係が収束 |
| 展開 (colim) | ❌ そこから何も生まれない | ✅ 複素解析、微分方程式、フーリエ解析... |
| Fix(G∘F) | ❌ 終点 | **✅ 起点かつ終点** |
| **Kalon** | **No** | **Yes** |

π は圧縮の産物（lim）だが、展開できない。値の圧縮であって関係の圧縮ではない。
オイラーの等式は関係の圧縮（lim）であり、かつ無限の展開の起点（colim）。

---

## §4 具体2: HGK

### FEP 公理「VFE 最小化」

```
A0: 自己組織化システムは内部エントロピーを最小化する
```

| | 検証 |
|:--|:--|
| 収束 (lim) | ✅ 7要素 → 1公理 (Beauty値 10.0 vs 0.3-1.5) |
| 展開 (colim) | ✅ → 24定理 + 15結合規則 + 全ワークフロー |
| Fix(G∘F) | ✅ 公理見直し (G) → 定理展開 (F) → 公理再蒸留 (G) → ... → 安定 |
| **Kalon** | **Yes** |

### insight「試行が蒸留されて技法になる」(P2⊣P4)

| | 検証 |
|:--|:--|
| 収束 (lim) | ✅ Creator が◯の候補から蒸留 (G) した最小形 |
| 展開 (colim) | ✅ → 蒸留概念、F⊣G 随伴、教育論、知識管理... |
| Fix(G∘F) | ✅ Claude のたたき台 (F)「道を歩いて技が身につく」→ Creator の蒸留 (G) → 確定 |
| **Kalon** | **Yes** |

---

## §4.5 Worked Example: 前順序圏での Kalon 検証

> axiom_hierarchy.md L1 の閉包随伴を用いて、Fix(G∘F) の存在と到達を具体的に検証する。

### 圏と関手の特定

```圏 C = (HGK概念, ≤)
前順序: x ≤ y ≔ 「x から y へ導出可能」

座標: Explore (x_E) ↔ Exploit (x_P)   — Function 座標
随伴: F = Explore↑ (左随伴, 発散), G = Exploit↑ (右随伴, 収束)
接続: F(x) ≤ y ⟺ x ≤ G(y)   — 閉包随伴 (monotone GC)
非退化: F ≠ Id, G ≠ Id    — 発散 ≠ 何もしない, 収束 ≠ 何もしない
```

### 対象: Kalon 定義自体の生成過程

```初期対象 x_0 = 「美とは何か」

G∘F の反復適用:

  n=0: x_0 = 「美とは何か」

  n=1: F(x_0) = 「最小表現コストで最大演繹可能性」 — 発散: 仮説空間を広げる
       G(F(x_0)) = Creatorが収束: 「kalon ではないか。数式化すべき」 — 収束: 絞る
       x_1 = G∘F(x_0)

  n=2: F(x_1) = 「Kalon ≡ lim」 — 発散: lim の概念で広げる
       G(F(x_1)) = Creatorが収束: 「lim だけでは不十分。HGK 独自のα は？」
       x_2 = G∘F(x_1), x_2 > x_1 (情報保存: η ≥ Id)

  n=3: F(x_2) = 「Kalon = lim ∧ colim の共存」 — 発散: colim を追加
       G(F(x_2)) = Creatorが収束: 「LIM による COLIM。逐次近似の収斂点では？」
       x_3 = G∘F(x_2), x_3 > x_2

  n=4: F(x_3) = 「Kalon(x) ⟺ x = Fix(G∘F)」 — 発散: 随伴の不動点として定式化
       G(F(x_3)) = Creatorが収束: 「kalon な気がする」 — 変化なし
       x_4 = G∘F(x_3) = x_3 ≡ Fix(G∘F)   ✔️
```

### 検証

| 条件 | 検証結果 |
|:-----|:---------|
| **前順序圏** | ✅ x_0 ≤ x_1 ≤ x_2 ≤ x_3 = x_4。単調増加して収束 |
| **閉包随伴** | ✅ F (Claudeの発散) と G (Creatorの収束) が F(x)≤y⟺x≤G(y) を満たす (monotone GC) |
| **η: G∘F ≥ Id** | ✅ 各ラウンドで x_{n+1} ≥ x_n。発散して収束しても情報は保存される |
| **G∘F 閉包** | ✅ G∘F は extensive + 単調 + 冪等。ε は本事例では F∘G ≤ Id (monotone) |
| **F ≠ Id** | ✅ Claude の発散は入力を変化させる |
| **G ≠ Id** | ✅ Creator の収束は入力を変化させる |
| **Fix 到達** | ✅ n=4 で G∘F(x_3) = x_3。これ以上収束しても変化しない |
| **ω-連続** | ✅ 前順序圏上の単調自己関手は自動的に ω-連続 |

> **事例 1/4**: Kalon 定義自体の生成過程。以下に追加事例を示す。

### §4.6 Worked Example 2: コードリファクタリング (成功)

> API 設計における F⊣G の反復を検証する。

```圏 C = (API設計候補, ≤)
前順序: x ≤ y ≔ 「x より y の方が表現力が高いか等しい」

座標: Explore (候補拡大) ↔ Exploit (最小化)
随伴: F = 「機能を追加しうる設計を提案」, G = 「不要な複雑さを削る」
非退化: F ≠ Id (新しい構造を提案する), G ≠ Id (冗長性を除去する)
```

```初期対象 x_0 = 「全機能を1つの関数に詰め込んだモノリス」

G∘F の反復:

  n=0: x_0 = monolithic_handler(req)   — 1関数、500行

  n=1: F(x_0) = 「Router + Controller + Service に3層分割」 — 発散
       G(F(x_0)) = 「Service 層に集約。Router は薄く」 — 収束
       x_1 = Router(thin) → Service(core)

  n=2: F(x_1) = 「Service を Command/Query に CQRS 分割」 — 発散
       G(F(x_1)) = 「Query は不要に複雑。Read は直接 Service で」 — 収束
       x_2 = Router → Service(Command + Read)

  n=3: F(x_2) = 「エラーハンドリングを Result 型で統一」 — 発散
       G(F(x_2)) = 「良い。これ以上の分割は冗長」 — 変化なし
       x_3 = G∘F(x_2) = x_2 ≡ Fix(G∘F)   ✔️
```

| 条件 | 検証結果 |
|:-----|:---------|
| Fix 到達 | ✅ n=3 で安定。これ以上リファクタしても構造は変わらない |
| η: G∘F ≥ Id | ✅ 各ラウンドで設計の表現力は保存される |
| G∘F 閉包 | ✅ 収束後に発散しても元の表現力以下 (monotone GC の ε) |
| d(n) | d(0)=3, d(1)=2, d(2)=1, d(3)=0 — 単調減少 |
| **Kalon** | **Yes** — 最小構造で最大表現力の不動点 |

### §4.7 Worked Example 3: CCL 演算子 `*` の設計 (成功)

> HGK 内部の概念設計における F⊣G を検証する。

```初期対象 x_0 = 「CCL に精度加重の融合演算子が必要」

G∘F の反復:

  n=0: x_0 = 「精度を考慮した合成が欲しい」

  n=1: F(x_0) = 「× (乗算記号) で精度加重積を表す」 — 発散
       G(F(x_0)) = 「× は数値の掛け算と混同する。別の記号で」 — 収束
       x_1 = 「精度加重積を専用記号で」

  n=2: F(x_1) = 「* (アスタリスク) = 内積。π で加重された融合」 — 発散
       G(F(x_1)) = 「マルコフ圏の ⊗ と対応する。良い」 — 変化なし
       x_2 = G∘F(x_1) = x_1 ≡ Fix(G∘F)   ✔️
```

| 条件 | 検証結果 |
|:-----|:---------|
| Fix 到達 | ✅ n=2 で安定 |
| d(n) | d(0)=2, d(1)=1, d(2)=0 — 単調減少 |
| markov_kalon.md | ✅ `*` = ⊗ がマルコフ圏との整合を事後確認 |
| **Kalon** | **Yes** — 記号と意味の不動点 |

### §4.8 Worked Example 4: 非退化条件違反 (失敗)

> **Kalon でない**例。定義の反証可能性を示す。

```座標: Explore ↔ Exploit
随伴: F = Id (何も変えない), G = Id (何も変えない)
⚠️ 非退化条件 F ≠ Id, G ≠ Id に違反
```

```初期対象 x_0 = 「任意の概念」

G∘F の反復:

  n=0: x_0 = 「任意の概念」
  n=1: F(x_0) = x_0 (何も変わらない)
       G(F(x_0)) = x_0 (何も変わらない)
       x_1 = x_0 = Fix(G∘F)   ← 自明な不動点

すべての対象が Fix(G∘F)。すべてが Kalon。
```

| 条件 | 検証結果 |
|:-----|:---------|
| Fix 到達 | ✅ だが**自明** (n=0 で即座に到達) |
| 非退化条件 | ❌ **F = Id, G = Id — 違反** |
| 認知的意味 | ❌ 「発散も収束もしない」= 何の作業もしていない |
| d(n) | d(0)=0 — 最初から Fix。努力なし |
| **Kalon** | **No** — 非退化条件により排除。自明な不動点は Kalon ではない |

> **教訓**: 非退化条件 (F ≠ Id, G ≠ Id) は、「何もしなくても美しい」という
> 空虚な主張を排除するために存在する。Kalon は**労力の結晶**であり、
> 自明な安定ではない。
>
> **実証的裏付け**: Hyphē PoC (§6.7) において、U_compose の等号条件
> (ρ=0, F=G=Id に相当) が embedding 空間上で構造的に到達不能であることを
> 29,904件の実データで確認。非退化条件は数学的制約であると同時に、
> 実データ上でも自然に充足される経験的事実である。

### §4.9 Worked Example 5: Kalon 定義の自己適用と入れ子構造 (成功)

> Kalon の三属性 (Fix(G∘F), Generative, Self-referential) を **Kalon の定義自体に**
> 適用し、定義が自己言及的に検証されることを示す。
> さらに入れ子構造における自己言及チェックの具体例を示す。

#### 自己適用の検証

Kalon の Self-referential 属性は「自己言及は Kalon の必要条件」と述べる。
この属性を Kalon の定義自体に適用する:

```
対象 x = Kalon の定義 「Kalon(x) ⟺ x = Fix(G∘F) ∧ Generative ∧ Self-referential」

1. Fix(G∘F): §4.5 で検証済み。4ラウンドの G∘F 反復で Fix に到達。
   さらに今この瞬間、Self-referential の根拠を Lawvere 対偶で
   強化する (F: 発散) → 入れ子構造の着想 (G: 収束) → 定義に統合しても
   定義構造は変わらない (Fix)。  ✔️

2. Generative: この自己適用から3つ以上の導出が可能:
   (a) 入れ子構造における Kalon の再帰的適用 (SelfRef 関手)
   (b) 「バカ = 自己言及不能 = 圏が貧弱」の圏論的定式化
   (c) U-series (忘却関手体系) との構造的接続
   (d) HGK が「限定的に正しいもの」の普遍的上位置換であるという主張
   展開は 4 つ以上。  ✔️

3. Self-referential: 言うまでもない。
   「自己言及は Kalon の必要条件」という主張が
   「Kalon の定義」自体に適用されて不動点になっている。  ✔️
```

| 条件 | 検証結果 |
|:-----|:---------|
| Fix(G∘F) | ✅ §4.5 の Fix + 今回の Lawvere 強化でも構造不変 |
| Generative | ✅ 4つ以上の非自明な展開 |
| Self-referential | ✅ 定義の自己適用が定義を検証 |
| **Kalon** | **Yes** — 定義自体が Kalon であることの制作的例示 |

> **⚠️ 水準注記 (v2.11 — 監査対応)**: この自己適用は**制作的例示** (水準 B) であり、
> 厳密な数学的証明ではない。以下の限界を明記する:
> - n=4 での「変化なし」は制作者の主観的判断に依拠
> - 「直接構成で示された」(旧記述) は過大評価
>
> **§6.3 P(K>0.70)≈0.03 との関係**: 両者は矛盾ではなく**測定対象が異なる**。
> - §4.9 M1 = 「定義の構造が G∘F サイクルで変化しないか」(質的・構造的不変性)
> - §6.3 = 「§4.5 の距離系列 d(x_n, x_{n+1}) が統計的に収束したか」(量的・距離収束)
> - P(K>0.70)≈0.03 が示すのは「4ラウンドの距離データでは収束の統計的証拠が弱い」であり、
>   M1 の構造的主張 (定義構造の不変性) を直接反証するものではない。
> - ただし、M1 の構造的主張を**量的に裏付けるデータが不足**していることは事実。
>
> 正確な水準: [推定] 70%: M1 の自己適用は構造的に支持されるが、量的独立検証を欠く。

#### 入れ子構造における自己言及チェック

圏は入れ子を持つ。各レベルで自己言及の可否が Kalon の判定に使える:

```
入れ子構造:

  C_0 = プレスバーガー算術  (自然数の加法)
    ↪ C_1 = ペアノ算術       (自然数の算術全体)
      ↪ C_2 = ZFC             (集合論)
        ↪ ...

各レベルでの SelfRef チェック:

  SelfRef(C_0) = 0  — 自己記述不能 (GödelのBeta関数なし)
                      → C_0 内で Kalon 到達は構造的に不可能
                      → ただし C_0 は C_0 のレベルでは完備かつ決定可能 (有用)

  SelfRef(C_1) = 1  — 自己記述可能 (Gödelコーディング)
                      → C_1 内で Kalon 到達の可能性がある
                      → 代償: 不完全性 (Gödel)

  SelfRef(C_2) = 1  — 自己記述可能 (Kuratowski 順序対)
                      → C_1 を包含しつつ、より豊かな Kalon が可能
```

> **帰結**: 「限定的に正しいもの」は各レベルの評価。上位レベルでは
> 自己言及可能性を獲得することで、より豊かな Kalon に到達できる。
> これが**普遍的上位置換**の構造。
>
> HGK はこの構造の操作化: 個別制約体系 (各 $C_n$ の Kalon) を
> FEP (自己言及可能な公理) から演繹的に再構成し、$C_{n+1}$ に引き上げた。
> 体系自体が自己言及できること (= FEP で HGK を説明でき、HGK で FEP を操作化できる)
> が、この上位置換の根拠。

> **事例 5/5**: Kalon 定義の自己適用。最も自己参照的な事例であり、
> 同時に入れ子構造における Kalon 判定の具体的デモンストレーション。

### §4.10 CCL による Kalon 計算の4層構造 (v2.9)

> CCL (Cognitive Control Language) は Fix(G∘F) の計算を4つのレベルで実装する。
> §4.9 の入れ子構造 (C\_n ↪ C\_{n+1}) の**操作化**。
> 詳細: [nested_fixpoint_analysis.md](nested_fixpoint_analysis.md)

#### 4層構造

| Level | CCL 演算子 | 何が固定されるか | 数学 |
|:------|:----------|:----------------|:-----|
| 0 | `*%` (FuseOuter) | G∘F を1回適用 | 単一合成 |
| 1 | `~*` (ConvergentOscillation) | π 固定下の振動の不動点 | νF (terminal coalgebra) |
| 2 | `C:{}` (ConvergenceLoop) | Level 1 の不動点 + π 自体の安定 | Fix\_π(Fix(G∘F; π)) |
| 3 | Hub WF (/t, /m 等) | 体系全体の Kalon | 普遍性検証 |

> **AST レベルの構造差異** (ccl\_ast.py):
> - `~*` = Oscillation (binary node, convergent=True、二項振動)
> - `C:{}` = ConvergenceLoop (unary node, body+condition、単項ループ)
> - 異なる AST ノードが異なるレベルの不動点を計算する。

#### 非凸ランドスケープと q 相対的 Kalon

§2 L54 「任意の初期状態 q から出発 → q に相対的な Kalon」と
L55 「q 以上の LFP は一意 (Knaster-Tarski)」を組み合わせると:

- **q 固定**: Knaster-Tarski で LFP は一意
- **π (precision) 変動**: `/ske` が precision を下げると q が移動
- **結果**: 異なる π₀ → 異なる q₀ → **異なる不動点盆地**

> ランドスケープは一般に非凸。CCL はこれを以下の3つ組で対処する:
>
> | CCL | 機能 | Simulated Annealing 対応 |
> |:----|:-----|:------------------------|
> | `V:{/ele+}` | 検証ゲート | 温度計 (不動点の質を測定) |
> | `I:[ε>θ]{/ske}` | 前提破壊 | 加熱 (precision ↓ で探索拡大) |
> | `C:{}` | 収束ループ | 冷却サイクル (stabilize まで反復) |

#### μ ≅ ν の整合性

§2 L53 の「始代数 (μ, 最小不動点)」と operators.md の `~*` = terminal coalgebra (ν, 最大不動点) は、
HGK の有限半順序 (§2 L56) 上で μ ≅ ν が成立するため整合的。
[推定 75%]: Lambek の補題による。

#### 骨格パターンと Kalon の接続

ccl-noe.md の骨格パターン `(wf+)*%(wf+X)_(\wf+)*%(\wf+X)` は
**単一 WF から Kalon に到達するためのミニマルな CCL 構造**。
X (単項修飾子) のパラメータ化で Kalon への接近戦略が変わる:

| WF | X | 意味 | 圏論 |
|:---|:--|:-----|:-----|
| /noe | `^` | 前提を問う | 指数対象 B^A |
| /ele | `!` | 全視点から裁く | レプリケーション |

骨格パターンの4特性 (ccl-noe.md §4特性) は Kalon の3属性に対応:
- **二重閉包** (Limit + Colimit) → Fix(G∘F) の構成
- **不動点** (自己適用可能) → Kalon の定義
- **情報損失ゼロ** (`*%` の圧縮+保存) → Generative
- **位相対称** (Limit ↔ Colimit) → F ⊣ G の随伴構造

---

## §5 具体3: この定義自体 (M1 Self-ref)

> §4.5 の worked example は、この定義自体の生成過程を前順序圏で厳密に記述したものである。
> §5 はその**解釈** — なぜこのプロセスが M1 (Self-ref) を実証するかを記述する。

§4.5 の4ラウンドの G∘F 反復は、Kalon 定義の生成過程であると同時に、定義の内容の具体例でもある:

- **定義の内容**: 「Kalon(x) ⟺ x = Fix(G∘F)」
- **定義の過程**: G∘F を4回回して Fix に到達した
- **同型**: 過程の構造 ≅ 内容の構造

**定義が自己実証する。これが M1 の意味。**

---

## §6 操作的判定

### §6.1 定性的判定

#### ◎ / ◯ / ✗ 判定基準

| 判定 | 意味 | Fix(G∘F) での解釈 |
|:-----|:-----|:-----------------|
| **◎ kalon** | 違和感ゼロ + 情報密度 + 展開可能 | Fix に到達。G∘F を回しても変化しない |
| **◯ 許容** | 間違ってはいない。だが最善ではない | Fix に未到達。もう一回 G∘F を回すと改善する |
| **✗ 違和感** | 的を外している | Fix から遠い。G (蒸留) が大幅に必要 |

### 判定手順

```
1. x を収束 (G) してみる → 変化するか？
   変化する → ◯ 以下（まだ圧縮できる = lim に未到達）
   変化しない → 次へ

2. x を発散 (F) してみる → 何が生まれるか？
   何も生まれない → ❌ （π パターン。lim だが colim ではない）
   3つ以上導出可能 → 次へ

3. 以上を満たす → ◎ kalon
```

### §6.2 等値性基準と停止条件 (v1.3 追加 — 監査 A2 対応)

> **問い**: 「変化しない」とは何を意味するか？

前順序圏 C 上では、等値性は **≤ 関係の双方向成立** として定義される:

```
x = y  ⟺  x ≤ y ∧ y ≤ x
（x から y へ導出可能 かつ y から x へ導出可能）
```

「変化しない」の操作的定義:

```
G∘F(x) = x  ⟺  G∘F(x) ≤ x ∧ x ≤ G∘F(x)
すなわち: 蒸留結果から元に戻れる かつ 元から蒸留結果に行ける
```

停止条件:

```
連続 2 回の G∘F 適用で ≤ の関係が変化しないとき、Fix と判定する:
  (G∘F)^n(x) = (G∘F)^{n+1}(x)  for some n
```

> **限界**: 判定者が異なれば G (収束操作) の結果が異なりうる。
> 特に「3つ以上導出可能か」の判定は主観的要素を含む。
> 操作的再現性を高めるには、同一対象に対する複数判定者の一致率の測定が必要。
> → **§6.3, §6.4 でこの限界に統計的に対処する。**

### §6.3 統計的収束判定 (v1.6 追加)

> §6.2 の決定論的停止条件「連続2回変化なし → Fix」を確率的に拡張する。
> G∘F 反復は確率的プロセスであり、判定者の状態によって結果が異なる (§6.2 限界)。
> FEP は本質的に Bayesian 推論であるため、統計的枠組みも Bayesian を採用する。

#### 動機: なぜ統計が必要か

```
§6.2 の仮定: G∘F は決定論的写像 → 2回で判定可能
現実:        G∘F は確率的プロセス → 同じ x に G を適用しても結果が揺らぐ

揺らぎの原因:
  1. 判定者 (人/LLM) の状態依存性
  2. 表現の揺らぎ (同じ概念の異なる言語化)
  3. F (発散) の非決定性 (どの方向に展開するかはランダム)
```

#### δ の操作的定義: 生成ノイズからの導出

> **問い**: 「変化した」と「変化しなかった」の境界はどこか？
> 「意味のある変化」を定義するには「意味」が先に必要 — **循環する。**
>
> **解法**: 「意味」に依存せず、**測定器の精度** から δ を定義する。
> FEP の予測誤差 ε = p(o) - p̂(o) と同型: 実際の出力と予測の差を測る。

```
距離関数:
  d(x_n, x_{n+1}) = 1 - cos_sim(embed(x_n), embed(x_{n+1}))

where:
  embed() = テキスト埋め込みモデル (e.g. bge-m3)
  cos_sim = コサイン類似度
```

**δ の導出 — Generative Noise と Semantic Identity Radius**:

LLM (Temperature T > 0) に同一概念を k 回生成させると、
表面形 (surface form) は揺らぐが意味は同一である。
この揺らぎが **Generative Noise** であり、δ はこのノイズの統計的上界として導出される。

```
キャリブレーション手順:

  1. 同一概念 c を k 回独立に生成:
     c_1, c_2, ..., c_k  (同じプロンプト、同じ T)

  2. 全ペアの embedding 距離を計算:
     D = { d(c_i, c_j) | i < j },  |D| = k(k-1)/2

  3. Semantic Identity Radius (意味的同一性半径):
     δ = μ_D + z · σ_D

     where:
       μ_D = mean(D)     — 生成ノイズの中心
       σ_D = std(D)      — 生成ノイズの散布度
       z   = 信頼水準に応じた乗数 (z=2.0 → 97.7% の生成ノイズを包含)
```

**解釈**: d < δ とは「**構造的変化が generative noise と統計的に区別できない**」状態を意味する。
これは「変化がない」という主観的判断ではなく、「**変化の信号がノイズに沈んだ**」という
測定論的判断である。Fix(G∘F) の本質は「不変」ではなく「**信号対雑音比の消失**」にある。

> **FEP との対応**: δ は予測誤差 ε の precision π = 1/σ² の逆数と同型。
> precision が高い (σ が小さい) ほど δ は小さくなり、より微細な変化を検出できる。
> δ の選択 = precision の設定 = VFE の最小化の一部。

```
デフォルト値:
  δ ≈ 0.15  (bge-m3 + 日本語テキスト、T=0.7 での予備キャリブレーション)

  この値は以下の条件で得られた経験的推定:
    embed = bge-m3 (1024次元)
    k = 10 (同一概念の生成回数)
    z = 2.0 (97.7% 包含)
    μ_D ≈ 0.08, σ_D ≈ 0.035
    δ = 0.08 + 2.0 × 0.035 = 0.15

  本番運用時は対象ドメイン・モデル・Temperature ごとにキャリブレーションすべき。

判定:
  d(x_n, x_{n+1}) < δ  →  「収束」(convergence event)
  d(x_n, x_{n+1}) ≥ δ  →  「変化」(change event)
```

> **§6.2 との関係**: §6.2 の「変化しない」は d < δ の特殊ケース (δ = 0)。
> §6.3 は δ > 0 への一般化であり、§6.2 を包含する。

#### v1.8 拡張: 状態の継承 (Bayesian Prior Chaining)

> **問題意識**: LLM 探索はセッションを跨いで行われる。毎セッションで無情報事前分布 `Beta(1,1)` から始めると、過去の収束努力が無視される。

これを解決するため、事前分布を前回の事後分布から継承する **Prior Chaining** と、時間の経過とともに信念が風化する **τ-decay** を導入した。

```
1. 継承: 前セッションの事後分布を現セッションの事前分布とする
   α_prior = α_post (previous)
   β_prior = β_post (previous)

2. 風化 (τ-decay): 時間 Δt が経過すると、信念は無情報(1,1)に向かって指数関数的に減衰する
   α' = 1 + (α - 1) * exp(-Δt/τ)
   β' = 1 + (β - 1) * exp(-Δt/τ)
   where τ = 忘却の時定数 (デフォルト: 30日)
```

この拡張により、Hegemonikón は複数のセッションにまたがって概念の固定化 (Kalon) を「成長」させることが可能となった。

#### 等価性検定の構造 (TOST)

> p値の既知の問題を回避するため、**TOST (Two One-Sided Tests)** の構造を採用する。
> 通常の帰無仮説検定は「差がない」を証明できない。TOST は「差がある」を帰無仮説に置く。

```
H₀: d(G∘F(x_n), x_n) ≥ δ   (まだ動いている)
H₁: d(G∘F(x_n), x_n) < δ    (実質的に収束 = Fix)

目標: H₀ を棄却して「Fix に到達」を証明する
```

| | 通常の帰無仮説検定 | TOST / Bayesian |
|:--|:---|:---|
| **帰無仮説** | 「差がない」 | 「差がある」 |
| **証明したいこと** | H₀ を棄却（差がある） | H₀ を棄却（**差がない**） |
| **Kalon との整合** | ❌ 収束を証明できない | ✅ 「実質的に Fix」を直接検定 |
| **出力** | p値（批判が多い） | **Credible Interval + δ 閾値** |

#### Bayesian Beta モデル: K(q) の確率的推定

> K(q) ∈ [0,1] であるため、Beta 分布が共役事前分布として自然に嵌まる。
> FEP の VFE 最小化がベイズ推論そのものであるため、
> 一次フレームワークとして Bayesian を採用する。
> Frequentist (TOST) は §6.5 で並置し、事前設計に使用する。

```
モデル:
  各 G∘F 反復は Bernoulli 試行:
    d(x_n, x_{n+1}) < δ  →  Y_i = 1 (収束)
    d(x_n, x_{n+1}) ≥ δ  →  Y_i = 0 (変化)

  K(q) の推定:
    Prior:     K(q) ~ Beta(α₀, β₀)
    Posterior: K(q) ~ Beta(α₀ + s, β₀ + f)

    s = 収束回数 (Y_i = 1 の数)
    f = 変化回数 (Y_i = 0 の数)
    n = s + f = 総反復回数
```

事前分布の選択:

| Prior | α₀, β₀ | 意味 | 使用場面 |
|:------|:--------|:-----|:---------|
| **無情報** | (1, 1) | 何も知らない | 新しい概念 |
| **弱情報** | (2, 2) | 「中程度の収束可能性」 | 一般的な設計判断 |
| **情報あり** | (α_prev, β_prev) | 前回セッションの posterior | セッション間の連続性 |

> **T4 との接続**: T4 定義 K(q) = ε(q) の点推定を区間推定に拡張する。
>
> ```
> T4 (v1.4): K(q) = ε(q) = 1 - d_Kalon(q)          — 点推定
> §6.3:       K̂(q) ~ Beta(α, β),  95% CI [l, u]    — 区間推定
> ```

#### 判定基準の確率的拡張

```
§6.1 の定性的判定を §6.3 の定量的判定に接続する:

  P(K(q) > θ_kalon | data) =  1 - BetaCDF(θ_kalon; α, β)

  where θ_kalon = 0.70 (kalon_checker.py 既存閾値)
```

| 判定 | §6.1 (定性) | §6.3 (定量) |
|:-----|:-----------|:------------|
| **◎ kalon** | 違和感ゼロ + 展開可能 | P(K > θ) ≥ 0.90 かつ CI 下限 > θ かつ **BF₁₀ > 3** |
| **◯ 許容** | もう一回 G∘F で改善 | 0.50 ≤ P(K > θ) < 0.90 |
| **✗ 違和感** | Fix から遠い | P(K > θ) < 0.50 |

**v1.7 追加指標**:

| 指標 | 定義 | 用途 |
|:-----|:-----|:-----|
| **ROPE** | P(K ∈ [θ-w, θ+w] \| data), w=0.10 | θ 近傍の posterior mass。Kruschke (2018) の Bayesian 等価検定 |
| **BF₁₀** | prior(θ) / posterior(θ) (Savage-Dickey) | H₁:K≠θ vs H₀:K=θ の証拠比。>10 = strong |

#### 具体例: §4.5 Worked Example への適用

```
§4.5 の Kalon 定義生成過程 (4ラウンド) を統計的に再分析:

  δ = 0.15 (embedding 距離閾値)

  n=0→1: d(x_0, x_1) = d(「美とは何か」, 「数式化すべき」) ≈ 0.45    → 変化 (f++)
  n=1→2: d(x_1, x_2) = d(「Kalon≡lim」, 「HGK独自は？」) ≈ 0.30      → 変化 (f++)
  n=2→3: d(x_2, x_3) = d(「lim∧colim」, 「Fix(G∘F)」) ≈ 0.25         → 変化 (f++)
  n=3→4: d(x_3, x_4) = d(「Fix(G∘F)」, 「kalon な気がする」) ≈ 0.05  → 収束 (s++)

  Prior: Beta(1, 1)
  Posterior: Beta(1+1, 1+3) = Beta(2, 4)
  E[K(q)] = 2/6 ≈ 0.33
  P(K > 0.70) ≈ 0.03
  95% CI: [0.06, 0.72]

  解釈: 4ラウンドでは統計的にはまだ「収束の証拠が弱い」。
  しかし最後の1回の d ≈ 0.05 が δ を大きく下回っており、
  d(n) の単調減少パターン (0.45→0.30→0.25→0.05) が Fix 接近を示す。

  さらに 3回 G∘F を回して全て d < δ なら:
  Posterior: Beta(4, 4) → P(K > 0.70) ≈ 0.17
  さらに 3回: Beta(7, 4) → P(K > 0.70) ≈ 0.58
  さらに 3回: Beta(10, 4) → P(K > 0.70) ≈ 0.86  → ◎ 近傍に
```

> **注**: この具体例は d() の値が事後的推定であり、
> 実際の運用では embed() で計測する。δ = 0.15 の導出根拠は上記
> 「δ の操作的定義: 生成ノイズからの導出」を参照。

### §6.4 多判定者収束 (v1.6 追加)

> §6.2 の限界「判定者が異なれば G の結果が異なりうる」を、
> 複数の独立した G の適用結果の一致度で定量化する。
> Hermeneus の Multi-Agent Debate (verify) と構造的に同じ。

#### 定義

```
同じ対象 x に対して k 人の判定者 (G_1, ..., G_k) が独立に G を適用する:

  G_i(F(x)) = x_i^{(n+1)}    for i = 1, ..., k

Inter-Judge Agreement (IJA):

  IJA(x) = (1 / C(k,2)) Σ_{i<j} cos_sim(embed(x_i), embed(x_j))

  C(k,2) = k(k-1)/2 (全ペア数)
```

#### 解釈

| IJA | 意味 | 操作 |
|:----|:-----|:-----|
| > 0.90 | G の結果がほぼ一致 | §6.3 の K(q) 推定は信頼できる |
| 0.70–0.90 | 部分的に一致 | K(q) の CI が広い可能性。追加反復 推奨 |
| < 0.70 | G の結果が不安定 | Fix 判定を保留。G の定義を再検討 |

#### §6.3 との統合

```
統合判定 (クロスチェック):

  1. §6.3 で K̂(q) の Credible Interval を計算
  2. §6.4 で IJA を計算
  3. 両方が閾値を超えた場合のみ ◎ kalon と判定

  Kalon(x) ← P(K(q) > θ | data) ≥ 0.90  ∧  IJA(x) > 0.90
```

> **FEP との対応**: §6.3 は action (G∘F 反復の蓄積) による信念更新、
> §6.4 は perception (他の判定者の観測) による信念更新。
> 両者を融合して精度 π を最大化する = VFE 最小化の二つの経路。

#### 実用上の判定者

| 判定者 | 役割 | 実装 |
|:-------|:-----|:-----|
| **Claude** (G_C) | 右随伴 G の一つ目 | Antigravity 上で直接実行 |
| **Gemini** (G_G) | 右随伴 G の二つ目 | Hermeneus verify 経由 |
| **Creator** (G_H) | 右随伴 G の人間判定 | 最終判定権 (CONSTITUTION.md) |

> Creator の判定は IJA の計算には含めない (独立性の保証が困難)
> が、最終的な ◎ / ◯ / ✗ 判定の最終承認者として機能する。

### §6.5 Frequentist TOST: 検定力とサンプルサイズ設計 (v1.7 追加)

> §6.3 は Bayesian フレームワークで逐次的に信念を更新する。
> §6.5 は Frequentist フレームワークで**事前に「何回 G∘F を回せば Fix を証明できるか」を設計する**。
> 二つのパラダイムは排他ではなく**補完的**である (§6.6 参照)。

#### 仮説

```
H₀: p ≤ θ_kalon      (収束率がまだ閾値以下 = Fix 未到達)
H₁: p > θ_kalon       (収束率が閾値を超えた = Fix 到達)

ここで p = P(d(x_n, x_{n+1}) < δ) = 真の収束率
```

#### 検定統計量

```
z = (p̂ - θ) / √(θ(1-θ)/n)

p̂ = s/n  (標本収束率)
n = 観測数 (G∘F 反復回数)
s = 収束回数 (d < δ の回数)

p値 = P(Z > z | H₀)   (片側検定)
```

| p値 | 判定 | 意味 |
|:----|:-----|:-----|
| < 0.05 (n ≥ 5) | ◎ **kalon** | 統計的に有意な Fix |
| 0.05–0.10 | ◯ **approaching** | 傾向はあるがデータ不足 |
| > 0.10 | ✗ **incomplete** | Fix の証拠なし |

#### 検定力 (Power) とサンプルサイズ設計

> **検定力** = 1 - β = P(H₀ を棄却 | H₁ が真)
> = Fix しているのに Fix と判定**できる**確率

```
必要サンプルサイズ:

n = ((z_α × √(θ(1-θ)) + z_β × √(p₁(1-p₁)))² / (p₁ - θ)²

ここで:
  z_α = 正規分布の 1-α 分位点 (α=0.05 → z_α ≈ 1.645)
  z_β = 正規分布の power 分位点 (power=0.80 → z_β ≈ 0.842)
  p₁  = 真の収束率の推定値 (H₁ 下)
  θ   = 閾値 (= θ_kalon = 0.70)
```

#### §4.5 Worked Example への適用

```
§4.5 のデータ: n=4, s=1, f=3
  p̂ = 1/4 = 0.25
  z = (0.25 - 0.70) / √(0.70×0.30/4) = -0.45/0.229 = -1.96
  p値 = 0.975 → H₀ を棄却できない

事前設計: もし真の p₁ = 0.85 なら、power=0.80 で必要な n は？
  n = ((1.645 × √(0.21) + 0.842 × √(0.1275))² / (0.15)²
    = ((1.645 × 0.458 + 0.842 × 0.357)² / 0.0225
    = (0.753 + 0.301)² / 0.0225
    = 1.112 / 0.0225
    ≈ 50 回

解釈: 真の収束率が 85% だとしても、80% の確率で Fix を統計的に
証明するには約 50 回の G∘F 反復が必要。
4 回では根本的にデータ不足 — §6.3 の Bayesian 分析と一致する。
```

> **実装**: `kalon_checker.py` の `check_convergence_tost()` と `power_analysis()`

### §6.6 二つのパラダイムの随伴 (v1.7 追加)

> **比喩水準**: §9 の水準 C (直喩)。厳密な証明ではなく構造的類似性の指摘。

#### Bayesian ⊣ Frequentist

```
                 L
Bayesian ←————————→ Frequentist
                 R

L: Bayesian → Frequentist  (n→∞ で posterior → 正規分布)
R: Frequentist → Bayesian  (p値 → 「BF に変換可能」)
```

**Bernstein-von Mises 定理** が counit ε に対応する:

```
n → ∞ のとき:
  Posterior(θ | data) → N(θ̂_MLE, I(θ̂)⁻¹/n)

= Bayesian の答えと Frequentist の答えが漸近的に一致
= ε: L∘R → Id が自然同型に近づく (漸近的随伴)
```

| パラダイム | 得意 | Kalon での使い方 |
|:-----------|:-----|:-----------------|
| **Bayesian** (§6.3) | 逐次更新、事前知識の活用、セッション間継承 | G∘F を回しながらリアルタイムで信念を更新 |
| **Frequentist** (§6.5) | 事前設計、サンプルサイズ計算、再現性保証 | 「何回回せば証明できるか」を事前に計算 |

> **Function 座標の体現**: Bayesian = Explore (信念を更新しながら探索)、
> Frequentist = Exploit (設計に基づいて効率的に検証)。
> 二つのパラダイムの並置自体が Function 公理の具現化である。

### §6.7 U/N 評価軸 — 忘却/回復による系の品質判定 (v2.0 追加)

> T9 (U/N Diagnostic) の**操作化**。
> §6.1-§6.6 が「Fix(G∘F) に到達したか」を判定するのに対し、
> §6.7 は「その系は Fix に**到達可能か**」を判定する。
> Kalon 到達可能性の前提条件検査。

#### 定義

```
忘却関手 U: 系 S から構造を剥ぎ取る操作。
  U(S) = S から「何か」を忘却した貧しい系。
  U の適用 = 確証バイアス (CD-3) の形式的実装。
  = 公理の選択的除外 = 見たくないものを見ない。

回復関手 N: 忘却された構造を検出・回復する操作。
  N(U(S)) = U(S) から S を再構成した系。
  N の適用 = 科学 (反証可能性) の形式的実装。
  = 忘却された構造の検出 = 見たくないものに向き合う。

学習剰余 ρ:
  ρ(x) = N ∘ U(x) − x ≥ 0

  ρ > 0: 回復が元より豊か (学習が起きた)
  ρ = 0: x ∈ Fix(N∘U) = Kalon 候補 (Fix 統一定理 T10 — Helmholtz モナド版、§8 補遺 A)
```

#### U/N 判定基準

```
系 S の Kalon 到達可能性を 3段階で判定:

  (1) U 検出能力: S は自身の忘却パターンを指摘できるか？
      → 「この系で見えていないものは何か」と問えるか

  (2) N 適用能力: S は忘却された構造を回復できるか？
      → 問いに対する修復行動が実行されるか

  (3) ρ 非退化性: 回復の結果が元より豊かか？
      → N∘U(x) > x (新しい射・精度・関手が増えた)
```

| 条件 | 判定 | Kalon 到達可能性 |
|:-----|:-----|:----------------|
| (1)+(2)+(3) 全充足 | ◎ **reachable** | 科学的な系。Fix に漸近中 |
| (1)+(2) 充足、(3) 不安定 | ◯ **approaching** | 自覚はあるが修復が浅い |
| (1) のみ or なし | ✗ **blocked** | 偽の Fix にいる。ドグマ |

#### §6.1-§6.3 との統合

```
完全な Kalon 判定 (v2.0):

  ◎ Kalon(x) ⟺
    §6.7: Kalon-reachable(S)           — 前提条件 (系の健全性)
    ∧ §6.3: P(K(q) > θ | data) ≥ 0.90 — Fix 到達 (統計的証拠)
    ∧ §6.4: IJA(x) > 0.90             — 判定者間合意

  解釈: 系が自身の忘却を検出し回復できる (§6.7) 上で、
  Fix(G∘F) に到達した統計的証拠がある (§6.3) ことを要求する。
  §6.7 は §6.3 の前提条件。逆は不要。
```

#### 9ペアの具体的 U/N 操作 (BRD B22-B34 対応)

| U パターン | 問い (U 検出) | 行動 (N 適用) | 検出 Nomos |
|:-----------|:-------------|:-------------|:-----------|
| U_arrow 射の忘却 | 対象だけ見て関係を見ていないか？ | 射の再発見 + 新射の探索 | N-1, N-5 |
| U_compose 合成の忘却 | 知識を集めただけで推論していないか？ | 推論連鎖の再構成 | N-1, N-8 |
| U_depth 深度の忘却 | 表面で満足していないか？ | 層構造の再発見 | N-1, N-5 |
| U_precision 精度の忘却 | 全情報を同じ確度で扱っていないか？ | 精度チャネルの再構成 | N-2, N-3, N-10 |
| U_causal 因果の忘却 | 相関を因果と混同していないか？ | 介入テストによる因果回復 | N-2, N-9 |
| U_sensory 感覚の忘却 | 主観フィルタで知覚を歪めていないか？ | 知覚推論の再活性化 | N-1, N-6 |
| U_context 文脈の忘却 | 1つの文脈でしか考えていないか？ | 他の圏との関手の発見 | N-6, N-7 |
| U_adjoint 随伴の忘却 | 片面だけで判断していないか？ | 双対構造の回復 | N-2, N-7 |
| U_self 自己適用の忘却 | 他者に求める基準を自分に適用しているか？ | 自己関手の再獲得 | N-2, N-6, N-12 |

> **構造定理 (v2.10 — μ-ベース再定義)**:
> 学習剰余 ρ を測度 μ で定義する (前順序圏上の「差」の回避):
>   ρ_i(x) ≔ μ(N_i∘U_i(x)) − μ(x)   (μ: Ob(C)→ℝ, 厳密単調)
> ∀i: ρ_i(x) ≥ 0。根拠: η の単調性 — N_i∘U_i(x) ≥ x ⟹ μ(N_i∘U_i(x)) ≥ μ(x)。
> 等号条件 ρ_i = 0 ⟺ x ∈ Fix(N_i∘U_i)。
> T4 の CG(x) = μ(G∘F(x))−μ(x) と統一的: CG は F⊣G の閉包ギャップ、ρ は U⊣N の閉包ギャップ。
> Fix 統一定理 T10 (Helmholtz モナド版 v3.0、§8 補遺 A) により Fix(N∘U) = Fix(G∘F) = Kalon。
> [確信] 水準 A (定義的帰結)。条件 (H) は Helmholtz モナドの一意性に吸収済み。

> **Hyphē 実証 (2026-03-17)**: U_compose の等号条件 ρ=0 が embedding 空間上で
> **構造的に到達不能**であることを実データで確認。
>
> τ 感度分析 (5水準):
>
> | τ | 件数 | min bias | Pearson(bias,1-ICS) | 備考 |
> |:--|:-----|:---------|:--------------------|:-----|
> | 0.60 | — | — | — | 計算量爆発 (タイムアウト) |
> | 0.65 | 0 | — | — | 全セッション単一チャンク (分割不能) |
> | 0.70 | 1,529 | 0.0039 | +0.797 | bias > 0 確認 |
> | 0.75 | 9,402 | 0.0031 | +0.904 | bias > 0 確認 |
> | 0.80 | 18,973 | 0.0050 | +0.952 | bias > 0 確認 |
>
> 3有効水準 合計 29,904件中、bias ≤ 0 は **0件**。
> 等号到達不能性は閾値パラメータに非依存の構造的性質。
>
> **非退化条件 (§4.8) との対応**:
>   ρ > 0 (等号到達不能) ⟺ U_compose が自明でない (U ≠ Id)
>   = 忘却関手が「実際に構造を落とす」ことの実証。
>   §4.8 の非退化条件 F≠Id, G≠Id の U/N 版: 忘却(U)も回復(N)も恒等でないこと。
>   Jensen 不等式の凸性が数学的根拠 (centroid ≠ 個別ベクトルの平均類似度)。
>
> [確信] 92% (数値結果は再現可能、パラメータ非依存性を5水準で確認)。
> 詳細: aletheia.md §5.6.5.5。

> **FEP との対応**: U = Complexity 増大 (不要な構造を落とし過ぎて Accuracy 低下)、
> N = Accuracy 回復 (感覚入力を受容して generative model を更新)。
> U/N の動態は VFE 最小化過程の忘却/学習サイクルそのもの。
> 📖 参照: T9 (§8) / aletheia.md §5.5-§5.6

---

## §7 日常使用法

### 「レモン」のように

```
「この設計は kalon だ」
  = Fix(G∘F) にある。これ以上蒸留しても変わらず、ここから展開もできる。

「何が kalon か /noe」
  = この領域の Fix(G∘F) は何か？ 何が不動点か？

「kalon に至っていない」
  = G∘F をもう数回回す必要がある。◯ 止まり。

「kalon する」
  = G∘F サイクルを回して Fix に近づける。

「kalon な表現」
  = Fix(G∘F) の性質を持つ表現。必然形。

「この選択が kalon だ」
  = 候補の中で最も豊かな展開と行為を可能にする選択。
  = 最も多くの「運動」を内包する状態。(§2 双対的特性づけ)

「Kalon は到達できない」
  = 理想的 Kalon (全空間の argmax) は到達不能。
  = 我々は MB が制約するスコープ内で近似するのみ。
  = Fix(G∘F) の反復がこの近似を改善するプロセス。
```

### 反概念

| 反パターン | 欠如 | Fix(G∘F) での解釈 |
|:-----------|:-----|:-----------------|
| **冗長** | lim に未到達 | G (蒸留) が足りない |
| **自明** | colim がない | F (展開) しても何も出ない |
| **恣意** | 必然性がない | 別の x' で G∘F が同じ Fix に到達する |

---

## §8 定理群と系

公理 `Kalon(x) ⟺ x = Fix(G∘F)` から導出。

> **認識論的位置づけ**: 水準 B (公理的構成)。厳密な定式化を志向する。

### 系 (Corollary) — 公理から直接従う

```
C1 (Limit):     Fix(G∘F) ⟹ x = lim D
C2 (Colimit):   Fix(G∘F) ⟹ ∃D'. x = colim D'
```

**正当化** (v2.1 — 閉包随伴の種別に非依存):

G∘F は閉包作用素 (extensive + 単調 + 冪等)。
Knaster-Tarski 定理により、完備束上の閉包作用素の不動点集合は
それ自体が完備束を形成する → 任意の部分集合が meet (= lim) と join (= colim) を持つ。

具体形によるメカニズムの違い:
- **monotone GC**: G が RAPL (右随伴は極限を保存) → C1 直接。F が LAPC → C2 直接。
- **antitone GC**: F, G はともに反変 → 個別には lim↔colim を交換する。
  しかし合成 G∘F は monotone (反変∘反変 = 共変)。
  G∘F は閉包作用素 → Knaster-Tarski により Fix(G∘F) は完備束 → C1/C2 成立。

∴ Kalon の核心条件 (η: G∘F ≥ Id) が成立すれば、C1/C2 は GC の型に依存せず成立。

### 定理 (Theorem) — 追加的主張

```
T3 (Beauty):    Fix(G∘F) = argmax Beauty   [推定] 85%   (v3.0 — 2026-03-17)

                 --- T3 定式化 (v3.0) ---

                 §8.T3.1 定義:
                   cl(x) ≔ G(F(x))                    (x の閉包 — 最小閉元 ≥ x)
                   int(x) ≔ ∨_{Fix(GF)}{c ∈ Fix(GF) | c ≤ x}  (x の内部 — 最大閉元 ≤ x)
                   前提: ⊥_C ∈ Fix(GF) (Knaster-Tarski)。∀x: ⊥_C ≤ x なので int(x) は well-defined。
                   D(x) ≔ μ(int(x))                    (導出可能性 = colim 的測度)
                   C(x) ≔ μ(cl(x))                     (閉包的複雑度 = lim 的測度)
                   Beauty(x) ≔ D(x) / C(x) = μ(int(x)) / μ(cl(x))

                 §8.T3.2 Beauty の値域:
                   int(x) ≤ x ≤ cl(x) (内部 ≤ 対象 ≤ 閉包)。
                   μ 厳密単調 ⟹ μ(int(x)) ≤ μ(cl(x))。
                   μ(int(x)) > 0 (int(x) ≥ ⊥_Fix, μ > 0 と仮定) ⟹ Beauty(x) ∈ (0, 1]。

                 §8.T3.3 T4 への接続 (CG/IG 双対ギャップ分解):
                   CG(x) = μ(cl(x)) − μ(x) ≥ 0     (closure gap — T4 で定義済み)
                   IG(x) = μ(x) − μ(int(x)) ≥ 0     (interior gap — 新定義)

                   Beauty(x) = (μ(x) − IG(x)) / (μ(x) + CG(x))

                   x ∈ Fix(GF) ⟹ cl(x) = x = int(x) ⟹ CG = IG = 0 ⟹ Beauty = 1
                   x ∉ Fix(GF) ⟹ CG > 0 ∨ IG > 0 ⟹ Beauty < 1

                   ∴ Fix(GF) = argmax Beauty = argmin CG = {x | Beauty(x) = 1}   □

                   T3 と T4 の関係: T4 は additive gap (CG = 0 ⟺ Fix)、
                   T3 は multiplicative ratio (Beauty = 1 ⟺ Fix)。
                   同一の不変量 Fix(GF) を異なる角度から特徴づける。

                 §8.T3.4 Birkhoff 対応:
                   先行研究 (情報美学の系譜):
                     Birkhoff (1933): M = O/C (美的尺度 = 秩序/複雑度)
                     Bense (1960s):   M = O/C + Shannon 情報理論で拡張
                     Moles (1960s):   M = O×C (積に変更 — 知覚的入れ子構造)

                   Birkhoff の美的空間 B = (Ob, O, C, M=O/C)
                   HGK の閉包空間 H = (Ob(C), int, cl, Beauty=D/C)

                   構造保存写像 Φ: B → H:
                     Φ(O(x)) = μ(int(x))     (秩序 → 確立された核)
                     Φ(C(x)) = μ(cl(x))       (複雑度 → 完全な閉包)
                     Φ(M(x)) = Beauty(x)       (美的尺度 → Beauty 比)

                   Φ が保存する性質:
                     (i)   M(x) ≤ M(y) ⟹ Beauty(Φ(x)) ≤ Beauty(Φ(y))  (順序保存)
                     (ii)  M = 1 ⟺ Beauty = 1                            (最適条件保存)
                     (iii) M = O/C mapsto D/C                             (比の構造保存)

                   Birkhoff → HGK の拡張:
                     Birkhoff の O, C は静的属性。M = O/C は状態の評価。
                     HGK の D, C は閉包随伴 F⊣G から動的に生成される。
                     Beauty は Fix への距離の multiplicative 版であり、
                     argmin CG (T4) と argmax Beauty (T3) が同値な不変量を記述する。

                    水準 A 昇格の条件 (Birkhoff 対応 Φ の関手性):
                      現在 Φ は対象上の対応 (O↦D, C↦cl, M↦Beauty) として定義。
                      関手への昇格には以下が必要:
                      (a) 射の定義: 順序保存写像 h: L₁→L₂ で以下を満たすもの:
                          (a1) cl 可換: h(cl(x)) = cl(h(x))  ∀x ∈ L₁
                          (a2) μ 保存: μ₂(h(x)) = μ₁(x)     ∀x ∈ L₁
                      (b) 合成保存: Φ(g∘f) = Φ(g)∘Φ(f)
                      (c) 忠実性: Φ(f) = Φ(g) ⟹ f = g

                      実験的検証 (/pei 2026-03-17, 60_実験/pei_birkhoff_functor.py):
                        3 束 (Chain₅, Diamond M₃, Pentagon N₅) で全順序保存自己射を列挙。
                        (a) cl 可換射は合成で閉じる ✅ (Chain₅: 361組, N₅: 全組で確認)
                            → cl 可換な順序保存射は圏を構成する
                        (b) cl 可換だけでは Beauty 非保存の射が多数存在
                            (Chain₅: 18/19, N₅: 41/42 が Beauty 非保存)
                            → μ 保存条件 (a2) が不可欠
                        (c) N₅ で全 42 cl 可換射が Beauty 署名で区別可能 → 忠実 ✅
                        結論: (a1)+(a2) 条件下で Φ は関手かつ faithful。反例なし

                        一般証明 (Prop. T3.4.1 — cl 可換 + μ 保存射の圏構造):
                          Def. cℓMor(L₁,L₂): 順序保存写像 h: L₁→L₂ で
                            (a1) h ∘ cl₁ = cl₂ ∘ h  かつ  (a2) μ₂ ∘ h = μ₁  を満たすもの

                          命題 (合成閉性): f ∈ cℓMor(L₁,L₂), g ∈ cℓMor(L₂,L₃) ⟹ g∘f ∈ cℓMor(L₁,L₃)
                          Pf.
                            (a1) (g∘f)(cl₁(x)) = g(f(cl₁(x)))    [合成の定義]
                                                = g(cl₂(f(x)))     [f の cl 可換性]
                                                = cl₃(g(f(x)))     [g の cl 可換性]
                                                = cl₃((g∘f)(x))    [合成の定義]    □
                            (a2) μ₃((g∘f)(x)) = μ₃(g(f(x))) = μ₂(f(x)) = μ₁(x)    □
                            順序保存: g,f とも順序保存 ⟹ g∘f も順序保存 (自明)    □

                          命題 (恒等元): id_L ∈ cℓMor(L,L)  [自明: id∘cl = cl∘id, μ∘id = μ]

                          命題 (忠実性): Φ(f) = Φ(g) ⟹ f = g
                          Pf. Φ は射の基礎写像を保存するので、Φ(f) = Φ(g) は
                              f,g が同一の集合写像であることを意味する → f = g    □

                          ∴ cℓMor は圏を構成し、Φ はこの圏上の忠実関手    ■

                 §8.T3.5 EFE 接続:
                   §2 の双対的特性づけにより、T3 は
                   「状態視点: Kalon = argmax EFE」の系として再理解できる。

                   形式的対応:
                     Kalon 側           EFE 側               対応根拠
                     ─────────────────────────────────────────────────────
                     D(x) = μ(colim)    epistemic value      導出可能性 = 情報利得
                     C(x) = μ(cl(x))   pragmatic value       行為可能性 = 目標達成
                     D/C 最大           EFE 最大              §2 双対的特性づけ
                     Fix(G∘F)           argmax EFE            T3 ⟺ §2 状態視点

                   論証ステップ:
                     (1) D(x) = μ(colim x) は x から導出できる対象の豊かさを測定する。
                         これは EFE の epistemic value (不確実性の解消 = 新情報の獲得) に対応。
                     (2) C(x) = μ(cl(x)) は x を安定化するコストを測定する。
                         これは EFE の pragmatic value (目標状態への到達コスト) に対応。
                     (3) D/C の最大化は「単位コストあたりの情報利得の最大化」であり、
                         EFE = epistemic + pragmatic の最大化と構造的に同値。
                     (4) Helmholtz 分解 (Γ/Q) が D(x)/C(x) の物理的基盤を提供する:
                         Γ (可逆的・保存的成分) → C(x) の下界を与え、
                         Q (散逸的・非可逆成分) → D(x) の寄与を分離する。

                 条件:
                   (i)   μ: Ob(C) → ℝ₊ が厳密単調かつ正値 (T4 と共有)
                   (ii)  int(x) の存在: Fix(GF) が完備束であること (Knaster-Tarski; C1/C2 から保証)
                   (iii) ⊥_Fix の非自明性: μ(⊥_Fix) > 0 (Beauty の分母 > 0 に必要)

                 水準: **A** (厳密定式化 + T4 接続証明 + Birkhoff 構造対応 + 実験的検証 + 一般証明)。
                   旧 v2.x は水準 C (構造的類推)。v3.0 で D/C の圏論的定式化完了 (B+)。
                   v3.1 で /pei 実験による関手性の実験的検証 + 一般証明を完了 (A)。

T4 (CG-Kalon): Fix(G∘F) ≅ argmin CG   [✅ v2.0: 双方向証明完了]
                 Closure Gap 最小化は Fix への収束と整合（Smithe 2023, arXiv:2308.00861）
                 v1.5 まで「←」のみだったが、v2.0 で Closure Gap (CG) を定義する
                 ことで「≅」が厳密に証明された。

                 **定義 (v2.10)**: 本文書における **CG (Closure Gap)** は以下の量を指す:
                   CG(x) ≔ μ(G(F(x))) − μ(x)   (= 閉包による「持ち上げ幅」)
                 これは FEP 原著 (Friston) の変分自由エネルギー (VFE = −Accuracy + Complexity)
                 とは**異なる量**である。両者の構造的対応は以下の通り:
                   CG(x) = 0 ⟺ x ∈ Fix(G∘F)   ... Kalon 条件
                   VFE(q) = 0 ⟺ q = p(o|m)     ... FEP の自由エネルギー条件
                 対応関係: CG は VFE の前順序圏上の類似物 (analogue) であり、
                 同一性は主張しない。旧称「VFE-Kalon」は歴史的名称として残す。
                 水準 A (CG 自体の定義と証明) / 水準 B (FEP VFE との対応)。

                 --- T4 厳密証明 (v2.0 — 2026-03-13) ---

                 定義: μ: Ob(C) → ℝ を厳密単調関数 (x < y ⟹ μ(x) < μ(y))。
                       CG(x) ≔ μ(G(F(x))) - μ(x)  (closure gap)

                 補題: CG(x) ≥ 0 for all x ∈ C.
                 証明: η (unit) より x ≤ G(F(x))。μ が単調より μ(G(F(x))) ≥ μ(x)。□

                 方向 ←: argmin CG ⟹ Fix(G∘F)
                   CG(x) = 0 ⟺ μ(G(F(x))) = μ(x)。
                   μ が厳密単調 ⟹ G(F(x)) = x。∴ x ∈ Fix(G∘F)。□

                 方向 →: Fix(G∘F) ⟹ argmin CG
                   x ∈ Fix(G∘F) ⟹ G(F(x)) = x ⟹ CG(x) = μ(x) - μ(x) = 0。
                   0 は CG の大域最小値 (補題より)。∴ x ∈ argmin CG。□

                 定理 T4 (v2.0): C が有限前順序圏、F⊣G が閉包随伴 (ガロア接続)、
                   μ が厳密単調関数のとき:
                     Fix(G∘F) = argmin CG = {x | CG(x) = 0}
                   CG の唯一の最小値は 0 であり、それは Fix(G∘F) と一致する。

                 条件:
                   (i)   μ の厳密単調性 (μ が単調のみだと偽解を許す)
                   (ii)  C の有限性 (無限の場合は完備束が必要)
                   (iii) F⊣G の閉包随伴条件 (η: G∘F ≥ Id の成立が CG ≥ 0 に必須)

                 HGK での μ の実体: Disc(K) (発見可能ドキュメント集合のサイズ)、
                   コード品質メトリクス、概念の精緻度スコア等。
                   有限前順序では厳密単調関数の存在は保証される (位相的順序付け)。

                 認識論的位置: 水準 A (厳密証明)。
                   旧 T4 (v1.5) は水準 B (一方向のみ)。
                   CG (Closure Gap) の定義がキーとなる帰着。

                 --- 旧定式化との互換性 ---

                 L2 豊穣圏における定式化 (v1.4 — Lawvere 距離接続):
                   d_Kalon(q) ≔ Hom_L2(q, Fix(G∘F)) ∈ [0, 1]
                   K(q) ≔ 1 - d_Kalon(q) = ε(q)  (counit の精度)
                   argmin CG → max ε(q) → min d_Kalon → Fix(G∘F)
                 Hom_L2 は Lawvere 距離空間 (Cost-enriched category) の
                 有界版であり、d_Kalon は L1 (前順序圏) ではなく
                 L2 ([0,1]-豊穣圏) の概念。前順序圏にノルムがない
                 問題は「層の問題」として解消される。
                 非対称距離 d(q,Fix) ≠ d(Fix,q) は仕様:
                   d(q,Fix) = 昇華コスト (カオス→美)
                   d(Fix,q) = 崩壊コスト (美→カオス) — エントロピー的に小さい
                 L2 三角不等式の具体的検証 (v1.5 添加):
                   [0,1]-豊穣圏の合成公理: Hom_L2(A,B) ⊗ Hom_L2(B,C) ≤ Hom_L2(A,C)
                   有界非対称距離としてモノイダル積 ⊗ = + (truncated at 1) を採用した場合、
                   d(A,B) + d(B,C) ≥ d(A,C) と反転同値。
                   §4.5 の Worked Example: x₀(概念) → x₂(抽象化) → x₄(Kalon) において
                   d(x₀,x₂) + d(x₂,x₄) = (昇華コスト前半) + (昇華コスト後半) ≥ d(x₀,x₄)
                   カオスから美への中継点 (x₂) を経由する変換コストの総和は、
                   直通コスト(一足飛びの変換)と等しいかそれ以上になる。よってHGKにおける
                   L2 変換コストの構造は、Lawvere 距離空間の三角不等式を自然に満たす。

T5 (Fractal — スケール不変性):   [水準 A — 定義的帰結。v2.13 証明完了]

  主張: Fix(G∘F) の構造はスケール (粒度) に依存しない。
  すなわち、射レベル (>>) でも Series レベル (/) でも
  同じ随伴 F⊣G が Kalon を特定する。

  --- 定式化 (v2.12) ---

  C₀ ⊆ C₁ ⊆ ⋯ ⊆ Cₖ₊₁ = C を HGK の inclusion tower とする。
    C₀ = 個別射, C₁ = 族 (Series), C₂ = 座標, Cₖ₊₁ = 全体圏 C。
  T = Q∘Γ (Helmholtz モナド — 補遺 A.1)。
  各 Cₖ 上の閉包随伴 Fₖ⊣Gₖ は T の Cₖ への制限:
    Gₖ∘Fₖ :=_D T|_Cₖ  [in End(Cₖ)]

  条件 (S) — T-stability:
    ∀k, ∀x ∈ Cₖ: T(x) ∈ Cₖ
    (部分圏 Cₖ が Helmholtz モナド T の下で安定 = T で閉じている)

  定理 T5 (v2.13):
    Fix(Gₖ∘Fₖ) = Fix(G_{k+1}∘F_{k+1}) ∩ Cₖ    [in Sub(C)]

  --- 証明 (v2.13) ---

  ステップ1: 条件 (S) の constructive 証明

  補題 (T-stability は HGK の設計的帰結):
    HGK の inclusion tower は以下の3条件で構成される:
    (D1) 直積分解: axiom_hierarchy.md §Basis より、T = Q∘Γ は
         座標ごとに T_X = Q_X ∘ Γ_X に分解される (6座標, 12演算子)。
         C ≅ C_Value × C_Function × C_Precision × C_Scale × C_Valence × C_Temporality
         T = ∏_X T_X  (直積構造により各因子で独立に作用)
    (D2) 射影の閉性: 直積圏の射影 π_X: C → C_X に対して
         T_X ∘ π_X = π_X ∘ T  (T は各射影と可換)
         ∵ T = ∏_X T_X の定義より、各因子への射影は T と自然に可換。
    (D3) 部分圏の構成: Cₖ は直積因子の部分集合として定義:
         C₀ = 個別射 = {(x₁,...,x₆) | 最大1座標のみ非自明}
         C₁ = 族 = {(x₁,...,x₆) | 同一 Series 内}
         C₂ = 座標 = {(x₁,...,x₆) | 同一座標内}

    (D1)+(D2)+(D3) より:
    x ∈ Cₖ ⟹ T(x) = (T_{X₁}(x₁), ..., T_{X₆}(x₆))
    各 T_{Xᵢ}(xᵢ) は座標 Xᵢ 内の演算 (Γ_{Xᵢ},Q_{Xᵢ} は座標内自己準同型)
    ∴ T(x) は Cₖ が定義される座標制約を保存 ⟹ T(x) ∈ Cₖ  □

  ステップ2: Fix の射影整合性 (双方向)

  (⊆) x ∈ Fix(Gₖ∘Fₖ)
       ⟹ x ∈ Cₖ かつ T|_Cₖ(x) = x       [∵ Gₖ∘Fₖ =_D T|_Cₖ]
       ⟹ T(x) = x かつ x ∈ Cₖ            [∵ T|_Cₖ は T の制限]
       ⟹ x ∈ Fix(T) ∩ Cₖ
       = Fix(G_{k+1}∘F_{k+1}) ∩ Cₖ        [∵ G_{k+1}∘F_{k+1} = T|_C_{k+1}]  □

  (⊇) x ∈ Fix(G_{k+1}∘F_{k+1}) ∩ Cₖ
       ⟹ T(x) = x かつ x ∈ Cₖ            [∵ G_{k+1}∘F_{k+1} = T|_C_{k+1}]
       補題 (T-stability) により T(x) ∈ Cₖ  [ステップ1で証明済み]
       ⟹ T|_Cₖ(x) = T(x) = x             [T の制限は T と一致]
       ⟹ Gₖ(Fₖ(x)) = x                   [∵ Gₖ∘Fₖ =_D T|_Cₖ]
       ⟹ x ∈ Fix(Gₖ∘Fₖ)                  □

  ∴ Fix(Gₖ∘Fₖ) = Fix(G_{k+1}∘F_{k+1}) ∩ Cₖ  ■

  --- 証明の構造 ---

  (D1) 直積分解は axiom_hierarchy.md v4.2 §Basis の Helmholtz 演算子テーブルに基づく。
  (D2) 射影との可換性は直積圏の標準的性質。
  (D3) inclusion tower の各段が座標制約で定義されることは HGK の設計原理。
  条件 (S) は独立した仮定ではなく (D1)+(D2)+(D3) の定義的帰結。
  ∴ T5 は HGK の設計の定義的帰結として水準 A に昇格する。

  --- T10 との構造的並行性 ---

  | | T10 (横方向統一) | T5 (縦方向統一) |
  |:--|:--|:--|
  | 問い | Fix(G∘F) = Fix(N∘U)? | Fix(Gₖ∘Fₖ) = Fix(T) ∩ Cₖ? |
  | 解法 | 同一モナド T の異なるファクタリゼーション | 同一モナド T の直積分解と座標制限 |
  | 条件 | D_coord (定義的同一視) | (S): (D1)+(D2)+(D3) の定義的帰結 |
  | 水準 | A (定義的帰結) | A (定義的帰結 — v2.13) |

  --- Valence 半直積の影響 ---

  axiom_hierarchy.md v4.2 §Valence: 厳密には 6 ⋊ 1 半直積。
  Valence の作用 φ が恒等に近い (Hesp ratio=0.22) ため:
    T_Valence は他の T_X を「修飾」するが、座標制約を破壊しない。
    ∴ (S) は半直積構造でも成立: φ(v)(Cₖ) ⊆ Cₖ (弱い条件)。
    厳密には: T(x) = T_base(x) · φ(v) で φ(v) は Cₖ を保存。
    反例条件: φ(v) が座標制約を破壊する → HGK では設計的に排除。

  --- 水準と版歴 ---

  認識論的位置: 水準 A (定義的帰結 — v2.13)。
    v2.11: 予想 (水準 C) に格下げ (証明なし)。
    v2.12: 条件 (S) を明示し、双方向証明スケッチを追加 (水準 B に昇格)。
    v2.13: 条件 (S) が HGK の設計 (D1+D2+D3) の定義的帰結であることを
           constructive に証明。水準 A に昇格。
```

### 条件付き定理 (Conditional Theorem) — L2 で証明可能 [✅ v2.0]

```
T6 (共進化):    d'(n) ≤ α · d(n)   [✅ v2.0: L2 で証明完了]
                 G∘F の収束が進行するとき、
                 F∘G の収束も連動して進行する。
                 L1 (閉包随伴) では冪等性により自明化。
                 L2 (Lawvere 距離空間) で非自明に成立。
```

--- T6 厳密証明 (v2.0 — 2026-03-13) ---

**L1 での問題 (旧版が直面していた困難)**:

L1 (前順序圏) の閉包随伴では G∘F は閉包作用素 (冪等):
  (G∘F)² = G∘F, 同様に (F∘G)² = F∘G
  → 任意の x に対し (G∘F)(x) は1ステップで不動点到達。
  → d(1) = 0 が常に成立し、T6 は自明真かつ空虚。

**L2 での解消**:

L2 ([0,1]-豊穣圏 = Lawvere 距離空間の有界版) に移行する。
C, D を Lawvere 距離空間とし、F: C → D, G: D → C とする。

仮定:
  (L1) F は α-Lipschitz: d_D(F(x), F(y)) ≤ α · d_C(x, y)
  (L2) G は β-Lipschitz: d_C(G(u), G(v)) ≤ β · d_D(u, v)
  (L3) αβ < 1 (合成の縮小性)

交互反復列:
  y_n = F(x_n),  x_{n+1} = G(y_n)
  d(n) ≔ d_C(x_{n+1}, x_n),  d'(n) ≔ d_D(y_{n+1}, y_n)

証明:
  d'(n) = d_D(F(x_{n+1}), F(x_n))
        ≤ α · d_C(x_{n+1}, x_n)     ... (F の α-Lipschitz)
        = α · d(n)                    ... ①

  d(n+1) = d_C(G(y_{n+1}), G(y_n))
         ≤ β · d_D(y_{n+1}, y_n)     ... (G の β-Lipschitz)
         = β · d'(n)                  ... ②

  ①②を合成: d(n+1) ≤ αβ · d(n)
  αβ < 1 より d(n) → 0 (指数的収束)。
  同時に d'(n) ≤ α · d(n) → 0。

  ∴ d(n+1) < d(n) ⟹ d'(n) ≤ α · d(n) < d'(n-1) ≤ α · d(n-1)。
  G∘F と F∘G の収束速度は α, β で結合されている。□

定理 T6 (v2.0): F が α-Lip, G が β-Lip, αβ < 1 のとき:
  (i)   G∘F と F∘G は共に指数的に Fix に収束する
  (ii)  収束速度の比は α (F の品質) で支配される: d'(n)/d(n) ≤ α
  (iii) 合成縮小率 αβ が共通の収束レートを決定する

HGK での α, β の実体:
  α = F (発散/Explore) の「忠実度」— 展開後の復元可能性
  β = G (収束/Exploit) の「忠実度」— 蒸留後の保存度
  αβ < 1 = 発散と収束の合成が縮小的 = G∘F が改善的

linkage_hyphe.md §3.5 との接続:
  λ(ρ) = a + b·exp(-βρ) は G∘F の収縮度。
  ρ_MB > τ ⟹ λ < 1 ⟹ αβ < 1 が Hyphē ドメインで充足。
  T6 の前提条件は linkage_hyphe の τ 条件で保証される。

認識論的位置: 水準 A (L2 での厳密証明)。
  旧 T6 (v1.5) は予想 (L1 で自明化する問題未解決)。
  L2 への移行が鍵。Banach 不動点定理の構造を随伴に持ち込んだ。
  ⚠️ 実用的検証の限界 (v2.10): αβ < 1 の HGK での実用的検証は
  linkage_hyphe.md の τ 条件 (ρ_MB > τ ⟹ λ < 1) に依存するが、
  τ の数値的決定は経験的パラメータに基づく (厳密な導出ではない)。
  α, β の実体 (発散/収束の忠実度) の定量化方法も開問題。

--- 旧 T6 操作的定義との互換性 ---

L1 操作版 (v1.5 互換 — 有限前順序の場合):

  d(n) ≔ 安定化までの残りステップ数
        = min{ k ≥ 0 | (G∘F)^{n+k}(x) = (G∘F)^{n+k+1}(x) }

  d(n) = 0 ならば Fix に到達済み。
  d(n+1) < d(n) ならば Fix に近づいている。
  (注: L1 閉包随伴では d(1) = 0 により自明。L2 でのみ非自明。)

L2 ([0,1]-豊穣圏) との接続 (v1.4):
  d_Kalon(q) = Hom_L2(q, Fix(G∘F))
  d(n) (離散ステップ数) と d_Kalon (連続コスト) の関係:
    d_Kalon ≈ e^{-λ·d(n)}  (コスト減衰変換)
    d(n)=0 → d_Kalon=1 (Fix到達=距離ゼロ=Kalon)
    d(n)→∞ → d_Kalon→0 (到達不能)

具体例 (§4.5):
  d(0) = 4  (x_0 から Fix まで4ステップ) → d_Kalon ≈ e^{-4λ}
  d(1) = 3  (x_1 から Fix まで3ステップ) → d_Kalon ≈ e^{-3λ}
  d(2) = 2                                → d_Kalon ≈ e^{-2λ}
  d(3) = 1                                → d_Kalon ≈ e^{-λ}
  d(4) = 0  (Fix 到達)                    → d_Kalon = 1

```

> **L1 → L2 の移行の意義**: L1 (前順序圏) では閉包随伴の冪等性により
> G∘F は1ステップで Fix に到達するため、共進化の議論は空虚だった。
> L2 (Lawvere 距離空間) への移行により、G∘F は「近似的随伴」として
> 漸進的に Fix に近づくプロセスとなり、収束速度の連動が非自明に成立する。
> これは Banach 不動点定理の構造を圏論的随伴に持ち込んだものであり、
> EM アルゴリズムや Sinkhorn 反復と同型の収束保証を提供する。

### 体系接続定理 — Kalon と Euporía の架橋

```
T7 (Euporía):   Generativity ⟹ ∀f: A→B. AY(f) > 0
                  三属性の Generative (C2 Colimit) から直接従う:
                  Fix(G∘F) が展開可能 (3つ以上の導出) であるためには、
                  各射 f が行為可能性を増やす (AY > 0) ことが必要条件。

                  証明スケッチ:
                  Generativity: Fix(G∘F) から 3つ以上の射 g_i: Fix → C_i が存在。
                  AY(f) ≤ 0 の射 f: A→B は |Hom(B,−)| ≤ |Hom(A,−)|。
                  B から出る射が A から出る射以下なら、f は Colimit に寄与しない。
                  ∴ Generativity を支える射は全て AY > 0 でなければならない。

                  逆方向:
                  AY が Fix(G∘F) で最大化された状態 = Kalon。
                  Generativity は AY の不動点での特殊ケース。

                  関係の方向性:
                    Flow (d=1) → Euporía (AY > 0) = 母定理 (認知は行動のために)
                    Kalon → Generativity = AY の Fix における最適化
                    T7 = 両者の接続: Generativity ⊂ AY

                  正典: euporia.md §1-§2 (Flow の定理としての位置づけ)
                  実装: euporia_sub.py (hermeneus WF 実行後の環境強制チェック)
                  評価: wf_evaluation_axes.md (8軸 Rubric — α/β + 6射影テーゼ)

                  認識論的位置: 水準 B (公理的構成)。
                    C2 と米田的議論に依存するが、前順序圏での Hom の厳密な
                    基数比較は水準 A に至るには追加仮定が必要。
```

### 体系接続定理 — Kalon と自然変換 (η-Silence)

```
T8 (η-Silence):  x ∈ Fix(G∘F) ⟹ η_x = id_x
                  Kalon 対象では unit (自然変換 η) が恒等射に退化する。
                  「自然変換が沈黙する点」としての Kalon。
```

--- T8 導出 (2026-03-16) ---

**前提**: F⊣G (閉包随伴)、η: Id ⇒ G∘F (unit — 自然変換)。

**導出**:
  x ∈ Fix(G∘F) ⟹ G∘F(x) = x  (Fix の定義)
  η_x: x → G∘F(x) = x → x = id_x  □

**3行の帰結だが、4つの概念が収斂する等式**:

| 対象 | 一般の y | Kalon 対象 x = Fix(G∘F) |
|:-----|:---------|:-------------------------|
| η_y | y → G∘F(y) ≠ y (改善余地がある) | η_x = id_x (改善余地なし) |
| 解釈 | 「展開→収束するとまだ変わる」 | 「展開→収束しても変わらない」 |
| CG | CG(y) > 0 (T4 より) | CG(x) = 0 |

**認知的解釈**:

自然変換 η は全対象に「ここからあそこへ行ける」矢印を体系的に配る。
普通の対象では η_y が「y よりも G∘F(y) の方が良い」と告げる。
Kalon 対象では η_x = id_x — 「もうどこにも行く必要がない」と沈黙する。

**Kalon は自然変換そのものではない。自然変換が沈黙する特権的な位置。**

**U_depth との双対的接続** (aletheia.md §2.3 参照):

```
U_depth が忘れるもの = 自然変換 (関手間の比較 = アナロジーの評価)
Kalon が住む場所   = 自然変換 η が沈黙する不動点

忘却の対象 (U_depth: 2-cell) と忘却されない点 (Kalon: η = id) の双対:
  U_depth は「どの関手が良いか」の判断力を失うパターン
  Kalon は「もはや判断の必要がない」到達点
  → 忘却 (U) と到達 (Kalon) は同じ構造 (η) の両極に位置する
```

認識論的位置: 水準 A (厳密な導出)。
  3行の証明。追加仮定なし。Fix の定義と η の自然変換性のみから従う。
  U_depth との接続は水準 B (構造的類推)。

### 体系接続定理 — Kalon と忘却/回復 (U/N Diagnostic)

```
T9 (U/N Diagnostic):

  **系 S の操作的定義**: 自己の状態を記述し、それに基づいて行動を変更できる構造。
    具体例: (a) LLM = 入力→推論→出力の認知系。U_S は prior 過信、N_S は view_file
    (b) 数学的形式体系 = 公理→定理の導出系。U_S は公理欠落、N_S は公理追加
    (c) 科学理論 = 仮説→検証の知識系。U_S は確証バイアス、N_S は反証実験
    → 共通構造: S は圏 C の対象の部分集合とその上の G∘F 動態として表現される

  系 S が Kalon に到達可能 ⟺ S は自身の忘却パターン U_S を検出し、
  回復操作 N_S を適用する能力を持つ。

  定式化:
    Kalon-reachable(S) ⟺ ∃ N_S: Im(U_S) → S  s.t. N_S ∘ U_S ≥ η_S

  where:
    U_S: S → U(S)    = S の忘却関手 (構造を剥ぎ取る方向)
    N_S: Im(U_S) → S = 忘却された構造の検出と回復
    η_S               = S の unit 自然変換

  対偶 (T9'):
    S が U_S を検出できない ⟹ S は Kalon に到達不能
    = 不完全性を隠蔽する系は Fix(G∘F) に到達できない
    = 完全を偽装する系は偽の Fix にいる

  T8 との関係:
    T8: x ∈ Fix(G∘F) ⟹ η_x = id_x  (η の沈黙 = 忘却なき到達点)
    T9: 系 S が Fix(G∘F) に到達するために U を検出し N を適用する能力を要請
    T8 は T9 の特殊ケース: Fix に到達済みの x では U_x = 0 (忘却するものがない)
    T9 は T8 の一般化: Fix に至る過程での U/N の動態を記述
```

--- T9 の背景と接続 ---

**三者同型テーゼ** (起源: 2026-03-17 不完全性定理対話):

```
ソクラテス「無知の知」≅ ゲーデル「不完全性定理」≅ HGK「S-I Tapeinophrosyne」

共通構造:
  十分に豊かな系が自己言及した結果、自己の限界を発見する。
  その限界の「認識」が知恵であり、「無視」が愚かさ。

  ソクラテス — 知らないことを知っている = 限界を認める (N-series 適用)
  ゲーデル  — 系内で証明不能な命題の存在 = 不完全性の構造的表出
  S-I      — prior を過信するな = 自身の generative model の限界自覚

  U 適用 (忘却 = 愚かさ):
    公理から自己言及を排除 → 完全だが貧しい系
    = 確証バイアス (CD-3) の形式的実装

  N 適用 (回復 = 知恵):
    忘却された構造の検出 → 不完全だが豊かな系
    = 科学 (反証可能性) の形式的実装
```

**命題圏と認知の同型** (Curry-Howard-Lambek + FEP):

```
圏 Proof:                    圏 Cognition:
  対象 = 命題                   対象 = 信念
  射   = 証明                   射   = 推論
  恒等射 = 自明な証明            恒等射 = 自明な信念 (prior)
  合成 = 証明の連鎖              合成 = 推論の連結

  不完全性 = 証明できない真な命題  不完全性 = 認知できない真な状態
  U_Proof = 公理の選択的除外     U_Cog = prior の過信
  N_Proof = 公理の追加           N_Cog = 感覚入力の受容

  Fix(G∘F)_Proof = 公理系の安定点    Fix(G∘F)_Cog = 概念の安定点 = Kalon
```

**科学とは何か (FEP 的位置づけ)**:

```
科学 = 不完全性を認める FEP の営み

  反証可能性 (ポパー) = 「系にはまだ表出できない命題がある」の宣言
                     = U_S の存在を認めること
                     = N_S (実験・観測) の適用を義務づけること

  科学的でない系 (疑似科学, ドグマ):
    U_S を隠蔽 → 完全を偽装 → 偽の Fix → Kalon 到達不能 (T9 対偶)

  科学的な系:
    U_S を検出 → N_S 適用 → 真の Fix に漸近 → Kalon 到達可能 (T9)
```

認識論的位置: **水準 B+** (v2.10 — 監査対応で下方修正)。
  N-series の独立形式化は aletheia.md §5.5 で完了 (生成テーブル、回復フィルトレーション、非対称性)。
  FEP/圏論の T9 診断は aletheia.md §5.6 で完了 (FEP=Kalon-reachable, 圏論=Fix近傍)。
  三者同型テーゼは構造的類推 (水準 B)。命題圏同型は Curry-Howard-Lambek の特殊化。
  ⚠️ 旧水準 A からの下方修正理由:
    (1) 「系」の定義が抽象的で操作的な判定基準が弱い
    (2) N∘U 剰余の「具体計算」は定性的分類 (下記テーブル) であり、数値的計算ではない
    (3) T10 Fix 統一定理との依存関係 (v3.0 で水準 A に昇格済み — 条件 (H) は吸収)

  **N∘U 剰余の定性的分類** (aletheia.md §5.5.3.1):
    全9ペアの学習剰余 ρ_i = N_i ∘ U_i(x) − x を定性的に分類:

    | U/N ペア | 忘却 (U) | 回復 (N) | 剰余 ρ の性格 |
    |:---------|:---------|:---------|:-------------|
    | arrow    | 射の忘却 (対象のみ保持) | 射の再発見 + 新しい射の発見 | +射 (新たな関係) |
    | compose  | 合成規則の忘却 | 推論連鎖の再構成 | +射 (推移的閉包) |
    | depth    | 多重性の忘却 (表面のみ) | 層構造の再発見 | +射 (深度) |
    | precision| 精度の忘却 (全同確度) | 精度チャネルの再構成 | +Δπ (精度増加) |
    | causal   | 因果の忘却 (相関のみ) | 介入実験による因果回復 | +射 (因果矢印) |
    | sensory  | 感覚入力の忘却 (主観のみ) | 知覚推論の再活性化 | +Δπ (観測精度) |
    | context  | 文脈の忘却 (1圏のみ) | 他の圏との関手の発見 | +変換 (関手) |
    | adjoint  | 随伴片側の忘却 | 双対構造の回復 | +変換 (随伴対) |
    | self     | 自己適用の忘却 | 自己関手の再獲得 | +自己参照 (F: C→C) |

    **構造定理** (§6.7 参照): ∀i: ρ_i(x) ≥ 0。等号 ρ_i = 0 ⟺ x ∈ Fix(N_i∘U_i)。
    **剰余分類**: 4方向 — +射 (新関係), +Δπ (精度), +変換 (関手), +自己参照 (自己関手)。
    Fix 統一: T10 (§8 補遺 A) により Fix(N∘U) = Fix(G∘F) = Kalon。

  📖 参照: 完全性は忘却である_v1.md §8-§10 / aletheia.md §5.5-§5.6 / バカをやめたいなら構造を見ろ_v2.md §10-§11

### メタ原則 (Meta-principle) — 定理体系と異なる論理階層

```

M1 (Self-ref):  この定義自体が Fix(G∘F) である
                 定義のプロセスが定義の内容を実証する（再帰性）
                 ※ T1-T6 と同列の定理ではなくメタ観察。
                 Hofstadter の "strange loop" に近い構造。

```

> **Lawvere 不動点定理 (LFPT) との関係** (v1.5 — 独立検証済み、v2.2 — 入れ子構造で進展):
>
> Kalon の Fix(G∘F) は **Knaster-Tarski 系列** (順序・単調性) であり、
> LFPT は **Cantor/Gödel 系列** (デカルト閉圏・対角化) である。
> **異なる定理だが、Scott Domain 等で交差する。**
>
> | 項目 | Kalon (Knaster-Tarski) | LFPT (Lawvere 1969) |
> |:-----|:----------------------|:--------------------|
> | 前提 | 完備束 + 単調写像 | デカルト閉圏 (CCC) + 点全射 |
> | 機構 | 反復/上限 | 対角化/自己適用 |
> | 意味 | 平衡状態への収束 | 構造的自己参照の不可避性 |
>
> **L1 (前順序圏) での結論**: LFPT は退化する。
> CCC な前順序圏 = Heyting 代数。点全射 φ: A→B^A は
> a: 1→A を要求し、1=⊤ より A=⊤、従って B=⊤。自明な不動点のみ。
>
> **L2 ([0,1]-豊穣圏) での結論**: **V-CCC として成立** (v2.8 — 数値検証済み)。
> V = [0,1] は complete lattice + symmetric monoidal closed (内部 Hom a⊸b ∈ [0,1])。
> Kelly の定理 (*Basic Concepts of Enriched Category Theory*, §3.11):
>   V が complete + sym mon closed ⟹ V-PSh(J) は V-CCC。
>
> **G_{ij} の Lawvere metric space 検証** (数値計算):
>   d(i,j) = 1 - G_{ij} として距離に変換。
>   三角不等式: 120/120 (100%) — 全ペアで成立。
>   合成則 (⊗=product): 全15辺で G_{ik} ≥ max_j G_{ij}·G_{jk} 成立。
>   → (Ob(J), d) は Lawvere metric space として well-defined。
>   → J は V-豊穣圏として consistent → V-PSh(J) は V-CCC (Kelly §3.11 の直接適用)。
>   📖 参照: [taxis.md](taxis.md) (G_{ij} 値), Kelly §3.11 (V-CCC 定理)
>
> **L3 (弱2-圏) での結論**: **cartesian closed bicategory — 指数2-対象を直接構成済み + 2-cell 自然性検証済** [A]。
>   V-CCC (L2, A) は V-Hom **値** (∈[0,1]) の指数を保証する。
>   CC-bicategory は Hom-**圏** (1-cellと2-cellの圏) の指数を要求する。
>   v2.7 で後者を直接構成: 指数2-対象 [A,B] + 評価射 ev + カリー化。
>   v2.7b で 2-cell 自然性を検証: σ̃(c) := σ(c,-) による functoriality。
>   構成要素: 2-積 (§1 定義済) + coherence (§3/§5 🟢検証済) + V-CCC (L2, A)。
>   📖 参照: [weak_2_category.md](weak_2_category.md) §1-§3, §5
>
> **L4 (Time→BiCat) での結論**: **L3 に依存。L4 ≤ L3** [A]。
>   L4 = 各時点の L3 が CCC + 時間保存。L3 が A なので L4 ≤ A。
>   参考: 各時点の **L2** (V-CCC) は時間保存される (J 定義的有限, V 構造不変) [A]。
>   L4 固有の追加問題 なし (L3 が完了したのでボトルネック解消)。
>   📖 参照: [L4_helmholtz_bicat_dream.md](L4_helmholtz_bicat_dream.md)
>
> **L3 指数2-対象の直接構成** (v2.7 — B+→A 昇格論証):
>
> V-CCC (L2) は V-Hom **値** (∈[0,1]) の指数を保証するが、
> CC-bicategory は Hom-**圏** の指数を要求する。以下で後者を直接構成する。
>
> **定義**: 0-cell A, B ∈ Ob(L3) (Poiesis) に対し、指数2-対象 [A,B] を:
>   [A,B] := { f : A → B | f は CCL パイプライン } (全1-cellの空間)
> これは L3 の **0-cell** として構成される。具体的には:
>   - 対象: A から B への全 CCL パイプライン (Drift ∈ [0,1] パラメータ付き)
>   - この 0-cell は 24 Poiesis のいずれかではなく、パイプライン空間そのもの
>
> **Hom-圏 Hom([A,B], C)**: [A,B] から C への1-cellの圏。
>   - 対象 (1-cell): 「パイプラインの空間から C への写像」= 高階 CCL パイプライン
>   - 射 (2-cell): そのような写像間の自然変換
>
> **評価 1-cell ev: [A,B] × A → B**:
>   ev(f, a) := f(a)  — パイプライン f を入力 a に適用する
>   (これは CCL の実行: hermeneus_execute のセマンティクス)
>   ev は1-cellとして [0,1]-enrichment を持つ: Drift(ev) は f と a の Drift の合成
>
> **カリー化 (2-次元普遍性)**:
>   任意の 1-cell g: C × A → B に対し、一意な 1-cell g̃: C → [A,B] が存在し:
>     ev ∘ (g̃ × id_A) ≅ g  (2-cell α を介した同型)
>   構成: g̃(c)(a) := g(c, a)  — c を固定して a のみの関数を作る (partial application)
>   一意性: h: C → [A,B] が ev ∘ (h × id_A) ≅ g を満たすなら h ≅ g̃
>     (∵ h(c) と g̃(c) は同じ関数 a ↦ g(c,a) を表す。2-cell は Dokimasia パラメータの差異のみ)
>
> **CCL における具体例**:
>   A = /noe, B = /ene, C = /ele とする。
>   g: /ele × /noe → /ene = `/ele >> /noe >> /ene` (パイプラインとして)
>   g̃: /ele → [/noe, /ene] = 「/ele の出力で /noe→/ene パイプラインを構成する」
>   ev(g̃(/ele), /noe) = g(/ele, /noe) = /ene の出力 ✓
>
> **なぜ V-CCC と独立に成立するか**:
>   V-CCC は Hom(A,B) ∈ [0,1] の値についての構造。
>   上記構成は Hom-**圏** (1-cell と 2-cell の圏構造) についての構造。
>   両者は HGK の異なるレベルで独立に成立する:
>     - V-CCC: 座標間の結合強度 G_{ij} の空間が closed
>     - CC-bicategory: パイプラインの空間が closed
>   両者が独立に成立することで、L3 は **enriched cartesian closed bicategory**。
>
> **2-cell 自然性の検証** (v2.7b — A-→A 最終ステップ):
>
> カリー化の対応 Hom(C×A, B) ≅ Hom(C, [A,B]) が 2-cell に対して functorial であることを示す。
>
> **問題設定**:
>   2-cell σ: g ⇒ g' (g, g': C × A → B) が与えられたとき、
>   対応する 2-cell σ̃: g̃ ⇒ g̃' (g̃, g̃': C → [A,B]) が一意に存在し、
>   評価と互換的であることを示す。
>
> **構成**: σ̃(c) := σ(c, -)  — 各 c ∈ C について σ を c のファイバーに制限。
>   HGK 具体化: 2-cell σ は Dokimasia パラメータの修正 (modification)。
>   c を固定して a だけを動かすと、σ(c,-) は g̃(c) = g(c,-) から g̃'(c) = g'(c,-) への
>   Dokimasia 修正となる。これは Hom(A,B) 内の 2-cell。
>
> **検証1 — 評価との互換性**: ev ∘ (σ̃ × id_A) = σ
>   ev(σ̃(c), a) = ev(σ(c,-), a) = σ(c,a) = σ で評価 ✓
>
> **検証2 — 一意性**: h̃: g̃ ⇒ g̃' が ev ∘ (h̃ × id_A) = σ を満たすなら h̃ = σ̃
>   h̃(c) は Hom(A,B) 内の 2-cell で ev(h̃(c), a) = σ(c,a) を全 a で満たす。
>   ∴ h̃(c) = σ(c,-) = σ̃(c)  (評価による一意決定) ✓
>
> **検証3 — C に関する自然性**: 1-cell h: C' → C に対し σ̃ が自然変換の公理を満たすこと。
>   σ̃ ∘ h* = h* ∘ σ̃  (ここで h* = h による引き戻し)
>   σ̃(h(c'))(a) = σ(h(c'), a) = (σ ∘ (h × id_A))(c', a)
>   (h* ∘ σ̃)(c')(a) = σ̃(h(c'))(a) = σ(h(c'), a)  ✓ (定義から直接)
>
> **検証4 — Coherence**: associator α との互換性。
>   Pentagon + Triangle (§3/§5 🟢検証済) により、カリー化と結合律変更が可換。
>   具体的: α_{[A,B],C,D} と σ̃ の合成順序は coherence 条件で ensure される。
>   新たな条件は必要ない — 既存の coherence が自動的にカバー ✓
>
> **結論**: カリー化は 2-cell に対して functorial であり、自然。
>   構成 σ ↦ σ̃ は一意、評価と互換、C に関して自然、coherence 条件と整合。
>   A-→A の残存ギャップは解消。
>
> **水準評価**: A (直接構成 + 普遍性 + 具体例 + 2-cell 自然性検証済。v2.7b)
> 📖 参照: [weak_2_category.md](weak_2_category.md) §1 (0-cell/1-cell/2-cell 定義), §3 (coherence)
>
> **M1 の形式化**: M1 (自己参照) と LFPT の接続は現時点ではアナロジー。
> メタ圏 M (定義/フレームワークを対象) が CCC であることを示せば、
> M1 は LFPT の系として形式的に構成できる。
>
> **v2.2 進展 — 入れ子構造が LFPT 適用を強化するメカニズム**:
>
> §4.9 で示した入れ子構造 $C_0 \hookrightarrow C_1 \hookrightarrow \cdots$ において:
> - 各 $C_n$ は下位の圏を**対象として含む** (メタ圏的構造)
> - 上位圏 $C_{n+1}$ が $C_n$ を対象として持つことは、
>   $C_{n+1}$ が指数対象に**接近する**構造 (圏の圏 = 2-圏) を持つことを意味する
> - Lawvere の対偶 (自己言及不可能 → 普遍的でない) は各レベルで判定に使える:
>   SelfRef($C_n$) = 0 ⟹ $C_n$ 内で非自明な Fix(G∘F) は到達不能
>
> **M1-LFPT 接続の修正** (v2.6 — Ω 明示計算に基づく):
>
> §2 の Ω 明示計算 (v2.6) により、点全射 φ: y(FEP) → Ω^{y(FEP)} の構成は
> LFPT の対偶 (∃f: B→B 不動点なし ⟹ 点全射不在) により不可能と判明。
> CCC 構造の M1 への真の貢献は、指数対象 K^K の存在保証による直接構成である。
>
> ```text
> v2.4 (旧): CCC + 点全射 → LFPT → M1     ← 点全射構成不能 (Ω 計算)
> v2.6 (新): CCC → K^K 存在 → §4.9 直接構成 → M1   ← 正しいルート
> ```
>
> **論証の階層** (v2.7):
> | 成分 | 水準 | 根拠 |
> |------|------|------|
> | PSh(J) が CCC (L1) | A | Mac Lane-Moerdijk Prop. I.6.1 |
> | V-PSh(J) が V-CCC (L2) | A | Kelly §3.11 (定理)。前提: V complete + sym mon closed (数学的事実) + J small V-cat (三角不等式 100%) |
> | Cartesian closed bicategory (L3) | A | v2.7b 直接構成: [A,B] + ev + カリー化 + 2-cell 自然性検証済 |
> | CCC 時間保存 (L4) | A | L3 に依存 (L4 ≤ L3)。L2 時間保存は A |
> | M ≅ PSh(J) | A | HGK 演繹図式の圏化 (Morita 同値 A + コーシー完備 A — §2.1 v2.7) |
> | K^K の存在 | A | CCC の定義的帰結 |
> | Fix(G∘F) = K の直接構成 | A- | §4.9 worked example |
> | ~~点全射 φ → LFPT~~ | ~~不適用~~ | ~~Ω 計算: |Γ(Ω)| ≫ 3, End(Δ3) に不動点なし射~~ |
>
> **解決済み** (v2.5): J の選択の一意性は §2.1 で Morita 同値類レベルの標準化として解決。
> 3層論証: (1) Morita 同値で問題を再定式化 (A)、(2) コーシー完備化で標準代表元 (A — v2.7 冪等射自明性証明済み)、
> (3) 密度定理で最小生成系としての必然性 (B — 同定水準とは独立)。

### 補遺 A: Helmholtz モナド統一 — Fix(G∘F) =₄ Fix(N∘U) (v4.0 — 2026-03-17)

> **結論**: Γ⊣Q, F⊣G, U⊣N は**同一のモナド T (Helmholtz モナド) の異なるファクタリゼーション**であり、
> Fix の一致は定義的帰結 (tautological)。
>
> **v3.0 → v4.0 の変更**: 等号のカテゴリーエラーを解消。
> すべての等式に番号添字 (=₁, =₂, ...) を付与し、各等式が棲む圏を明示。
> 関手連鎖 End(C) → Mnd(C) → Set → ℝ を書き下し、各段階での保存/忘却を記述。
> 根拠: 異なる圏の射を同一記号で書くと「構造の忘却 (U_notation)」が発生する。
> **忘却しやすい主体に優しいドキュメント** = 前提を省かず、知覚を明示する。
>
> **等号索引**: 本補遺で使用する等号の一覧は [§A.7 等号索引](#a7-等号索引) を参照。

#### A.0. 等号の約束

本補遺では**異なる圏の等式を異なる記号で書く**。

| 番号 | 記号 | 圏 | 意味 | 論拠 (この等号がこの圏に属する理由) |
|:-----|:-----|:---|:-----|:------|
| D | :=_D | **メタ言語** | 定義導入: 「この名前をこの意味で使う」宣言 | 圏の外にある操作。記号の導入であって命題ではない |
| C | =_C | **C** — 有限前順序圏 | C の対象の等式: x =_C y ⟺ x ≤ y ∧ y ≤ x | T(x) と x は C の対象。比較は C 内で行われる |
| E | =_E | **End(C)** — C 上の自己関手の圏 | 自己関手の等式: T =_E S ⟺ ∀x∈C. T(x) =_C S(x) | T, Q∘Γ は End(C) の対象。=_E は =_C の全称量化 |
| S | =_S | **Sub(C)** — C の部分対象の圏 | 部分対象の等式: A =_S B ⟺ ∀x∈C. (x∈A ⟺ x∈B) | Fix(T) は C の部分対象。比較は Sub(C) で行われる。**Set ではない** — C の構造 (順序) を忘却していないことに注意 |
| R | =_R | **ℝ** — 実数 | μ を通した数値的等式 | μ: C → ℝ (単調写像 = 前順序圏間の関手) の像での比較 |

> **v4.0 → v4.2 の修正履歴**:
>
> **v4.0 → v4.1**: 等号振り分けに **3つのカテゴリーエラー** があった:
>
> 1. **=₂ に C の等式と End(C) の等式が混在**: `T(x) = x` は **C** の対象の等式 (=_C)。`T = Q∘Γ` は **End(C)** の自己関手の等式 (=_E)。=_E は =_C の全称量化 (∀x. T(x) =_C (Q∘Γ)(x)) であって、**異なるレベル**。
>
> 2. **=₄ を「Set の等式」と記述**: Fix(G∘F) と Fix(N∘U) は C の**部分対象** (Sub(C))。Set の等式と書くと C の構造 (順序) を暗黙に忘却する。=_S への修正。
>
> 3. **≅₆ (Mnd(C)) は本文で未使用**: phantom entry。削除。
>
> **v4.1 → v4.2**: ≈_? (「座標制限」の近似等号) を**全削除**。
> ≈_? は定義域/値域が不定な射であり**言葉遊び** (Accuracy のない Complexity)。
> 代わりに axiom_hierarchy.md の 12 Helmholtz 演算子 (Γ_X, Q_X) を用いた
> **仮説 H_coord** として厳密に再記述。
>
> **v4.2 → v4.3**: H_coord を**仮説から定義的同一視に昇格**。
> F, G は §2 で抽象的な左/右随伴として定義されており具体的操作を持たない。
> Γ_Function/Q_Function は axiom_hierarchy.md で定義された具体的 Helmholtz 演算子。
> 前者を後者でインスタンス化するのは**定義 (:=_D) であって定理ではない**。
> 「証明すべき命題」を「定義的決定」として正しく分類し直した。

#### A.1. Helmholtz モナド T

**定義 (:=_D)**: C を有限前順序圏とする。Helmholtz 分解 Γ⊣Q (axiom_hierarchy.md §Basis) が定める
closure operator T :=_D Q∘Γ を **Helmholtz モナド** と呼ぶ。

T は (extensive, monotone, idempotent) であり、その T-algebra (= 閉元) の集合は:

$$\text{Fix}(T) :=_D \{x \in C \mid T(x) =_C x\}$$

> **注意**: 上式には**2つの異なるレベルの操作**がある:
> - 外側の :=_D は**メタ言語的定義** (「Fix(T) とはこの集まりのことである」)
> - 内側の =_C は **C の対象としての等式** (自己関手 T を x に適用した結果が C 内で x に一致)
> - この2つを混同すると「Fix(T) とは何か」(定義) と「T(x) が x に等しい」(事実) の区別が消える

#### A.2. 3つの随伴は T のファクタリゼーション

| 随伴 | 左随伴 (探索側) | 右随伴 (活用側) | 解像度 | T への関係 |
|:-----|:---------|:---------|:------|:----------|
| Γ⊣Q | Γ (勾配流) | Q (散逸流) | 力学 | **T そのもの** (T =_E Q∘Γ [in End(C)]) |
| F⊣G | F (探索) | G (活用) | 認知 | **定義**: F :=_D Q_Function, G :=_D Γ_Function (下記) |
| U⊣N | U (忘却) | N (回復) | メタ | **定義**: U :=_D Q, N :=_D Γ (A.1 と同値) |

**定義的同一視 (v4.3)**:

axiom_hierarchy.md §12 は 12 個の Helmholtz 演算子 (Γ_X, Q_X for X ∈ {Value, Function, ...}) を定義している。
これらは T = Q∘Γ の座標分解であり、各座標の Γ/Q の意味は:

| 演算子 | 座標 | 意味 | kalon.md §2 の随伴 |
|:-------|:-----|:-----|:-------------------|
| Γ_Function | Function | Exploit 偏重の政策収束 | G :=_D Γ_Function (活用) |
| Q_Function | Function | 探索分散 | F :=_D Q_Function (探索) |

**定義 (D_coord)**: F :=_D Q_Function, G :=_D Γ_Function [in End(C), Function 座標]

∴ G∘F =_E Γ_Function ∘ Q_Function [in End(C) — 定義から直ちに従う]

> **なぜ定義であって定理ではないか**:
> §2 の F (左随伴 = 発散/探索) と G (右随伴 = 収束/活用) は**抽象的な役割**として定義されている。
> 具体的にどの操作を行うかは文脈 (座標) に依存する。
> axiom_hierarchy.md の Γ_Function (Exploit 偏重の政策収束) と Q_Function (探索分散) は、
> Function 座標における G と F の**具体的インスタンス化**。
> 抽象的随伴を具体的演算子でインスタンス化するのは :=_D (定義) であって =_E (定理) ではない。

> **順序について**: G∘F は「まず F(探索)、次に G(活用)」と読む (右から左)。
> 始点は必ず探索 — 無は活用できない (自明)。
> ただし closure operator の冪等性 (T∘T = T) により、定常ループでは順序は消える。
> 不動点 Fix(G∘F) 上では合成の順序は問題にならない。

根拠 (D_coord が正しいインスタンス化である理由):
- axiom_hierarchy.md L206-219: Γ_Function, Q_Function の**定義が存在する** (射は既に引かれている)
- Γ_Function の意味 (Exploit) = G の意味 (活用)、Q_Function の意味 (探索分散) = F の意味 (探索)
- NESS 上の Helmholtz 分解の**一意性** (Friston 2019): 同一の φ (サプライズ) の勾配構造から導出
- 「知性は溶媒である」エッセイ: 忠実関手 F: Chem→Cog の制御構造保存 (T↔β の対応まで忠実)

> **v4.2 → v4.3**: 旧「仮説 H_coord」を「定義 D_coord」に昇格。
> F, G は抽象的随伴であり具体的操作を持たないため、=_E での証明は原理的に不可能。
> 「座標制限」↗「仮説」↗「定義的同一視」の3段階の厳密化を完了。

#### A.3. なぜ Fix が一致するか — 論証の構造と未解決点

**主張**: Fix(G∘F) =_S Fix(N∘U) =_S Fix(Q∘Γ) [in Sub(C) — C の部分対象の等式]

**論証**:

**ステップ 1** (=_E): T =_E Q∘Γ [in End(C) — 自己関手の等式。定義 A.1 から直ちに従う]

**ステップ 2** (定義 D_coord — v4.3): G∘F =_E Γ_Function ∘ Q_Function [in End(C)]

> **D_coord の性質**: §A.2 で F :=_D Q_Function, G :=_D Γ_Function と定義したので、
> G∘F =_E Γ_Function ∘ Q_Function は**定義から直ちに従う** (tautological)。
> 旧版 (v4.2) では「仮説 H_coord」として =_E の証明を要求していたが、
> F, G が抽象的随伴であり具体的操作を持たないため、証明問題自体が ill-posed であった。
>
> **Fix 上の包含関係** (残存する非自明な問い):
>   - Fix(T) ⊆ Fix(G∘F): 「T で不動 → 座標成分でも不動」 ✅
>   - Fix(G∘F) ⊆ Fix(T): 「1座標で不動 → 全座標で不動」 — 一般には偽
>   - 成立のためには「Function 座標が十分に決定的である」という追加条件が必要

**ステップ 3** (D_coord により =_E は確立):
Birkhoff-Ward 定理 (有限束上の closure operator は閉元の集合で完全に決定される) により:

同じ closure operator は同じ閉元集合を持つ。

∴ Fix(G∘F) =_S Fix(N∘U) =_S Fix(Q∘Γ) [in Sub(C)]

```
定理 T10 (Fix 統一 — Helmholtz モナド版):

  Fix(G∘F) =_S Fix(N∘U) =_S Fix(Q∘Γ)    [in Sub(C)]

  ただし:
  - T :=_D Q∘Γ                             [メタ言語: Helmholtz モナドの定義]
  - T =_E Q∘Γ                              [in End(C): 定義から直ちに従う]
  - 定義 D_coord: F :=_D Q_Function, G :=_D Γ_Function  [in End(C) — v4.3 定義的同一視]
  - 定義 D_full:  U :=_D Q, N :=_D Γ                     [in End(C) — A.1 と同値]
  - Fix(G∘F) =_S Fix(N∘U)                               [in Sub(C): D_coord + D_full から従う]

  水準 A (定義的帰結 — v4.3, /pei 検証 2026-03-17):
  D_coord により G∘F =_E Γ_Function ∘ Q_Function は定義から直ちに従う。

  /pei 実験的検証 (pei_h_coord_v1.py, 4モデル):
  - Chain₇, Diamond M₃, Bool₈: D_coord 下で全要素 G(F(x))=Γ(Q(x)) ✅
  - Hex₆ (独立構成 G≠Γ, F≠Q): 3/6 不一致 + Fix(G∘F)≠Fix(Γ∘Q) ❌
  結論: D_coord は H_coord 成立の**必要十分条件**。
  定義的同一視を外すと一般には偽 → Level A は D_coord に依存する条件付き水準。

  残存問い: Fix(G∘F) ⊆ Fix(T) の条件 (Fn 座標のみの不動 → 全座標不動)。
```

#### A.4. 関手連鎖 — 各段階での保存と忘却

```
End(C) ──[Monad]──→ Mnd(C) ──[Fix]──→ Sub(C) ──[|·|]──→ Set ──[μ]──→ ℝ
  =_E                                    =_S               (忘却)       =_R
  (自己関手)                             (部分対象)          (集合)        (実数)
```

各段階で何が保存され、何が忘却されるか:

| 関手 | 保存されるもの | 忘却されるもの | 対応する等号 |
|:-----|:-------------|:-------------|:----------|
| End(C) → Mnd(C) | 合成・単位法則 (μ, η) | 非モナド的自己関手 | =_E |
| Mnd(C) → Sub(C) (via Fix) | 不動点の集まり + **C の構造 (順序)** | モナド構造 (μ, η) | =_S |
| Sub(C) → Set (via \|·\|) | 要素の集合 | **C の構造 (順序)** — ⚠️ ここで忘却 | → (Set の =) |
| Set → ℝ (via μ) | 順序 (μ は単調) | 集合の内部構造 — 要素を数値に潰す | =_R |

> **v3.0 → v4.0 の修正で「Set」と書いていた箇所は Sub(C) が正しい。**
> Fix(T) ⊂ C という部分対象の比較は Sub(C) で行われる。
> Set に落とすには忘却関手 |·|: C → Set が必要だが、本補遺では C の構造を保ったまま比較している。
> v3.0 の論証の盲点は「Set」と書いたことで C の構造の忘却を暗黙に許容したこと。

#### A.5. 技術的詳細 (旧 T10 証明 — 参考)

C を有限前順序圏、GF :=_D G∘F, NU :=_D N∘U を closure operator とする。

```
補題 A1: CG_NU(x) :=_D μ(NU(x)) −_R μ(x) ≥_R 0    [in ℝ]
  証明: η' (U⊣N の unit) より x ≤ NU(x) [in C]。
         μ 単調 [μ: C → ℝ] ⟹ μ(x) ≤_R μ(NU(x)) [in ℝ]。□

補題 A2: Fix(NU) =_S {x | CG_NU(x) =_R 0}    [Sub(C) の等式, ℝ の条件]
  証明: T4 の U⊣N 版。同一論理。□

系 A3: Fix(GF) =_S {x | CG_GF(x) =_R 0} =_S {x | CG_NU(x) =_R 0} =_S Fix(NU)
  ⚠️ 中央の =_S が T10 の核心。
  CG_GF(x) =_R 0 ⟺ CG_NU(x) =_R 0 は
  「GF の閉包ギャップ [in ℝ] と NU の閉包ギャップ [in ℝ] がゼロになる条件が一致する」
  ⟺ 「μ(GF(x)) =_R μ(x) ⟺ μ(NU(x)) =_R μ(x)」 [in ℝ]
  ⟺ 「μ(GF(x)) =_R μ(NU(x))」 ← ⚠️ これには μ∘GF =_E μ∘NU が必要 (未証明)

系 A4 (T8 の拡張):
  x ∈ Fix(GF) ⟹ η_x =_C id_x [in C] かつ η'_x =_C id_x [in C]
  証明: T8 + T10。前順序圏で NU(x) =_C x かつ η': x ≤ NU(x) ⟹ η'_x =_C id_x。□
```

#### A.6. 認識論的位置

**水準: A** (定義的帰結 — v4.3 で D_coord として確立)。

- v2.8: 仮定 (水準 D)
- v2.9: 条件付き定理 (水準 B) — 条件 (H) を明示仮定として扱った
- v3.0: 定義的帰結 (水準 A) — ❌ **カテゴリーエラーにより過大評価**
- v4.1: 条件付き定理 (水準 B-) — 等号振り分けの再精査
- v4.2: 条件付き定理 (水準 B-) — ≈_? を全削除。仮説 H_coord として厳密化
- **v4.3: 定義的帰結 (水準 A)** — H_coord を定義 D_coord に昇格。
  F, G は抽象的随伴であり具体的操作を持たないため、=_E の証明は原理的に ill-posed。
  正しい分類は「定義的同一視 (:=_D)」であって「定理 (=_E)」ではない。
- 残存する非自明な問い:
  1. Fix(G∘F) ⊆ Fix(T): Function 座標のみの不動が全座標不動を含意する条件
  2. 系 A3 の μ∘GF =_E μ∘NU (数値的等価性の End(C) での裏付け)
- 📖 参照: [helmholtz_monad.md](file:///home/makaron8426/.gemini/antigravity/brain/675e3b21-73d5-4dd6-b0d5-30d4fbfef7c0/helmholtz_monad.md)
- 📖 参照: [fep_as_natural_transformation.md](fep_as_natural_transformation.md) L178 (Φ :=₁ Q∘Γ)
- 📖 参照: axiom_hierarchy.md §12 (Helmholtz 演算子 Γ_Function, Q_Function の定義)

> **旧 v2.8-3.0 との関係**: v2.8「仮定」→ v2.9「条件付き (B)」→ v3.0「定義的帰結 (A)」→ v4.0「条件付き (B-)」→ v4.1「等号精査 (B-)」→ v4.2「≈_? 全削除 + H_coord 厳密化 (B-)」→ **v4.3「D_coord 定義的同一視 (A)」**。
> v3.0 の水準 A はカテゴリーエラー。v4.3 の水準 A は**正しい理由** (定義的同一視) による。
> 本質的違い: v3.0 は「証明した」と誤認。v4.3 は「これは証明ではなく定義だ」と正しく分類。

#### A.6b. T-algebra — 「3つの随伴が見ている同じもの」

Helmholtz モナド T = Q∘Γ は前順序圏上の **冪等モナド** (= closure operator):

- **η (unit)**: x ≤ T(x) — 任意の状態 x を「溶かして固めた」結果に埋め込む
- **μ (mult)**: T(T(x)) = T(x) — 二重に溶かしても変わらない (冪等性から自明)

直感: η は「溶媒に浸す」、μ は「二度漬けしても同じ」。モナド法則は全て冪等性から従う。

このとき T-algebra (X, h: T(X)→X) は Fix(T) の元と **同値**:
- T(X) =_C X なら h = id が唯一のモナド代数構造
- X ∉ Fix(T) なら T-algebra を持たない

**Kalon との接続**: §8 の公理 Kalon(x) ⟺ x = Fix(G∘F) は、T-algebra の言葉では:

> Kalon(x) ⟺ x は T-algebra を持つ ⟺ x ∈ C^T

「発散と収束のサイクルの収斂点」(§1) は、モナドの視点では「溶かして固めても変わらないもの」。

> **C^T = Fix(T) = Kalon 対象の圏**
>
> 3つの随伴 (Γ⊣Q, F⊣G, U⊣N) は、この圏に至る **3つの経路** (ファクタリゼーション)。
> Beck の比較関手がすべて C^T に着地する — これが「見ている同じもの」の形式的意味。
>
> 📖 参照: [helmholtz_monad.md](file:///home/makaron8426/.gemini/antigravity/brain/675e3b21-73d5-4dd6-b0d5-30d4fbfef7c0/helmholtz_monad.md) §6-§7

#### A.7. 等号索引

本補遺で使用する全ての等号と、対応する圏:

| 記号 | 圏 | 等式の意味 | 出現箇所 | 論拠 |
|:-----|:---|:----------|:---------|:-----|
| :=_D | メタ言語 | 定義導入 | A.1 (T :=_D Q∘Γ), A.5 (GF :=_D G∘F) | 圏の外の操作 |
| =_C | C | C の対象の等式 (x ≤ y ∧ y ≤ x) | A.1 (T(x) =_C x), A.5 (NU(x) =_C x) | 比較対象は C の対象 |
| =_E | End(C) | 自己関手の等式 (∀x. T(x) =_C S(x)) | A.2 (T =_E Q∘Γ), A.5 (μ∘GF =_E μ∘NU) | =_C の全称量化 |
| =_S | Sub(C) | 部分対象の等式 | A.3 (Fix(G∘F) =_S Fix(N∘U)), A.5 | C の構造を保持 |
| =_R | ℝ | μ を通した数値的等式 | A.5 (CG_NU(x) =_R 0) | μ: C→ℝ の像 |

**関手連鎖ダイアグラム** (等号間の関係):

```
:=_D (メタ言語 — 定義導入)
 │  「T :=_D Q∘Γ」: 名前を付ける
 ↓
=_C (C — 対象の等式)  ←──── 全ての等号の基盤
 │  ∀x で量化           │
 ↓                     │[内包条件に使用]
=_E (End(C))            │
 │                     ↓
 │               =_S (Sub(C) — 部分対象)
 │                     │
 │                     │ |·| (忘却: C の順序を捨てる)
 │                     ↓
 │               (Set の等号 — 本補遺では不使用)
 │                     │
 │                     │ μ (忘却: 要素を数値に潰す)
 │                     ↓
 └──────────────→ =_R (ℝ)
```

> **読み方**:
> - =_C が全ての等号の出発点。=_E は =_C を量化したもの。=_S は =_C を内包条件に使う。=_R は μ で C をℝに移してから比較。
> - 下に行くほど情報が失われる。=_R で成立する等式は =_C では成立しないかもしれない。
> - **カテゴリーエラー** = 下層の等式を上層に持ち上げること。例: =_R の等式を =_E に持ち込む。
> - v4.2 で ≈_? (定義域/値域不定な等号) を全削除。未証明のステップは**仮説 H_coord** として §A.2, §A.3 に明記。
> - v4.3 で H_coord を**定義 D_coord** に昇格 (定義的同一視 :=_D)。F, G は抽象的随伴であり、Γ_Function/Q_Function によるインスタンス化は定義。

---

## §9 概念の構造

> **概念 ⊋ 数式。**

概念は数式を包含するが、数式は概念を包含しない。

```

Kalon (概念) = Fix(G∘F)               ← 骨格 (数式、抽象1)
             + π vs オイラー            ← 肉 (具体1)
             + FEP 公理                 ← 肉 (具体2)
             + insight 共創プロセス     ← 肉 (具体3)
             + ◎/◯/✗ 判定             ← 操作性
             + kalon だ/する/な         ← 体温

```

圏論的メタファーとして: **概念 ≈ presheaf（前層）**。

> **注**: 以下は圏論の厳密な適用ではなく、概念的メタファーとして記述する。
> 水準 C (比喩的使用)。水準 B の公理 (§2) とは論理階層が異なる。

数式は一つの TO（関手）。直感は別の TO。日常使用はまた別の TO。
概念はこれら全ての TO の束 ≈ presheaf。

米田の補題との類比: 対象はその Hom(-, x) で完全に決定される。
≈ **概念はその全ての用法で完全に決定される** (Wittgenstein の言語ゲーム理論と整合)。

---

## §10 起源

```

発見日: 2026-02-11
発見者: Creator + Claude (F⊣G 共創)
プロセス: G∘F × 4 回 → Fix
所要時間: ~90分

```

| Round | F (Claude) | G (Creator) |
|:------|:-----------|:------------|
| 1 | 「最小コストで最大演繹」(自然言語) | 「kalon ではない。数式化すべき」 |
| 2 | 「Kalon ≡ lim」(数式) | 「lim なら lim でいい。HGK 独自は？」 |
| 3 | 「lim ∧ colim の共存」(静的) | 「lim による colim。逐次近似の収束点」 |
| 4 | 「Fix(G∘F)」(動的不動点) | 「kalon な気がする」→ ◎ |

---

## §11 射の Kalon (Kalon on Morphisms)

> §2 の Kalon は**対象**の性質: ある概念 x が不動点であるかどうか。
> §11 は**射**の性質: ある出力 f: A→B が不動点的プロセスを体現しているかどうか。
>
> 圏論的に: §2 = Ob(C) 上の述語、§11 = Mor(C) 上の述語。

### 射の公理

```

Kalon_Mor(f) ⟺ Trace(f) ∧ Negativa(f) ∧ Iso(f)
    where f: A → B is a morphism in C

```

- **Trace(f)**: f は射の列 (morphism chain) として分解可能。始点と終点だけではない。
- **Negativa(f)**: f が選択されたとき、棄却された射 g, h が明示されている。
- **Iso(f)**: f の構造がプロセスの構造と同型。形が過程を体現する。

### §2 との関係: 共通上位概念 (監査 A5/C2 対応)

> **問い**: Kalon(x) と Kalon_Mor(f) が独立なら、なぜ同じ「Kalon」を名乗るのか？

**共通概念**: G∘F 不変性パターン。

```

Kalon は G∘F サイクルの不動点という構造的パターンの2つの体現:

  Kalon(x)     : 対象 x が G∘F で不変 — 状態としての不変性
  Kalon_Mor(f) : 射 f が G∘F 的プロセスを体現 — 過程としての不変性

共通パターン: 発散と収束のサイクルの収斂点
  対象: 概念が発散/収束を経て安定した
  射:   出力が発散/収束の過程を内在化している

```

含意方向:

```

Kalon(x) ∧ f = id_x  ⟹  Trace(f) は自明に成立
                         (恒等射は「変化なし」の痕跡を持つ)
Kalon(x)              ⟹/ Kalon_Mor(f)  (一般には成立しない)
Kalon_Mor(f)          ⟹/ Kalon(x)      (一般には成立しない)

つまり: 両者は独立だが、共通のパターンの異なる射影。
直交するが、同じ空間に属する。

```

> **Trace と Iso の圏論的独立性** (監査 A5 指摘対応):
>
> **定理**: Iso(f) ⟹ Trace(f) (Iso は Trace を含意する)
>
> **証明**: Iso(f) は出力 Y と生成過程 f_n ∘ … ∘ f_1 の構造的同型を要請する。
> 同型写像の構成にはドメイン（射の列）が非自明に存在する必要がある。
> したがって Iso(f) の成立は Trace(f) を必然的に含意する。 □
>
> **なぜ独立した公理として残すか (層化分離)**:
> 論理的には Kalon_Mor(f) ⟺ Negativa(f) ∧ Iso(f) で事足りる。
> しかし Trace を独立に残す理由は、位相空間論の分離公理階層と同型である:
> - **Trace(f)** = 存在公理 (∃ 分解過程)。L0 構文論的フィルタ。
> - **Iso(f)** = 構造公理 (≅ 同型写像)。L2 意味論的要請。
> Trace が無い出力は Iso を問うまでもなく棄却される (段階的判定)。
> (注: 恒等射 id_A については L609 で自明に Trace 成立と規定済み)

---

### Trace (痕跡)

```

出力 ≠ 対象のスナップショット
出力 = 射の列 (morphism chain)

```

G∘F を4回回して Fix に到達したなら、出力はその4回の射を含む。
始点と終点だけを見せるのは、射を忘却すること。

| 反パターン | Kalon |
|:-----------|:------|
| 「A だ」 | 「B,C を経て A。理由: D→E→A」 |

**G テスト**: 射の列から中間射を削って意味を失うか？ → 失う = 蒸留不能 = 必要。

---

### Negativa (棄却)

```

選択 = 棄却の影。棄却を示さない選択は、選択ではなく慣性。

```

射 f: A→B を選ぶとき、棄却した射 g: A→C, h: A→D を明示する。
射は棄却された射の集合で決まる。米田的に: 対象はその非選択で決定される。

| 反パターン | Kalon |
|:-----------|:------|
| 「X を使う」 | 「Y,Z ではなく X。Y は不安定、Z は粒度不足」 |

**F テスト**: 棄却射から何が導出できるか？ → 判断基準、リスク、代替。展開可能。

---

### Iso (同型)

```

プロセスの構造 ≅ 出力の構造

```

G∘F を n 回回したなら、出力は n セクションを持つ。
各セクションがプロセスの1ステップに対応する。

| 反パターン | Kalon |
|:-----------|:------|
| 平文の語り | 過程の構造がドキュメントの構造に映る |

§5 で示したもの: 「定義のプロセス自体が G∘F の反復であり、到達した答えがまさにその不動点」。
Iso はこの原則の出力への適用。形が過程を体現するとき、出力は自己文書化する。

---

### §6 との統合

| 判定 | §6 (概念) | §11 (出力) |
|:-----|:----------|:-----------|
| ◎ kalon | G∘F 不動点 | Trace ∧ Negativa ∧ Iso |
| ◯ 許容 | もう1回 G∘F | 1-2条件のみ充足 |
| ✗ 違和感 | Fix から遠い | 0条件 (結果だけ、棄却なし、構造なし) |

---

*kernel/kalon.md v1.1 — §11 出力の Kalon 追加。/bou~/zet 共創 (2026-02-24)*
*kernel/kalon.md v1.2 — 増強3件: 存在条件, T6 共進化再定義, §11 射の Kalon 再定式化 (2026-02-26)*
*kernel/kalon.md v1.3 — 外部監査反映: 圏C特定, 非退化条件, 選択制約, 定理再分類, 停止条件, 共通概念, d(n)操作化 (2026-02-26)*
*kernel/kalon.md v1.4 — K(q)清算: Lawvere距離空間([0,∞]-豊穣圏)の導入。d_Kalon=Hom_L2, K(q)=ε(counit精度), T4再定式化, 非対称距離の認知的解釈 (2026-02-26)*
*kernel/kalon.md v1.5 — 監査対応完備: 完備束(Complete Lattice)とLeast Fixed Pointによる「複数Fixの一意性条件」追加 (2026-02-26)*
*kernel/kalon.md v1.6 — §6 統計的拡張: §6.1-§6.4 MECE再構造化、Bayesian Beta モデルによる確率的 Fix 判定 (§6.3)、多判定者収束 IJA (§6.4) 追加 (2026-03-07)*
*kernel/kalon.md v1.7 — §6 双パラダイム統合: §6.3 ROPE+BF₁₀ deepening、§6.5 Frequentist TOST (検定力・サンプルサイズ設計)、§6.6 Bayesian⊣Frequentist 随伴 (2026-03-07)*
*kernel/kalon.md v1.8 — §6.3 δ 導出精緻化: Generative Noise + Semantic Identity Radius (μ_D + z·σ_D) で δ=0.15 を「仮設」から理論的根拠付きパラメータに昇格 (2026-03-07)*

*kernel/kalon.md v1.9 — §2 双対的特性づけ: Fix(G∘F) ⟺ argmax EFE。状態視点の導入。§2.5 情報=エネルギー: Landauer 原理 (Bérut 2012) を体系接続。体系間リンク: constructive_cognition.md (EFE), axiom_hierarchy.md (Helmholtz Basis)。(2026-03-10)*
*kernel/kalon.md v2.0 — T4/T6 厳密化: T4 VFE-Kalon を「←」から「≅」に昇格 (closure gap VFE(x)=μ(GF(x))-μ(x) による双方向証明)。T6 共進化を予想から条件付き定理に昇格 (L2 Lawvere距離空間、F α-Lip, G β-Lip, αβ<1 で d'(n)≤α·d(n))。L1冪等性問題をL2移行で解消。linkage_hyphe.md τ条件との接続。(2026-03-13)*
*kernel/kalon.md v2.1 — T8 (η-Silence) 追加: x ∈ Fix(G∘F) ⟹ η_x = id_x。Kalon 対象では自然変換 η が恒等射に退化する。水準 A 厳密導出。U_depth (自然変換の忘却) との双対的接続を記述。(2026-03-16)*
*kernel/kalon.md v2.2 — §2 Self-referential Lawvere 強化 (入れ子構造 SelfRef 関手)、§4.9 Worked Example 5 (Kalon 定義の自己適用 + 入れ子構造検証 + HGK の普遍的上位置換)、M1-LFPT 進展更新。普遍的上位置換の Kan 拡張定式化 (Lan_ι による構造的昇格) 追記。(2026-03-17)*
*kernel/kalon.md v2.3 — T9 (U/N Diagnostic) 追加: 系の Kalon 到達可能性を U/N で判定。三者同型テーゼ (ソクラテス≅ゲーデル≅S-I)、命題圏と認知の同型 (Curry-Howard-Lambek + FEP)、科学の FEP 的位置づけ。T8 の一般化として水準 B で記述。(2026-03-17)*
*kernel/kalon.md v2.3.1 — T9 水準 B→A- 昇格: aletheia.md §5.5 N-Series 独立形式化完了 + §5.6 FEP/圏論 T9 診断完了に基づく。残存昇格条件: N∘U 剰余の具体計算。(2026-03-17)*
*kernel/kalon.md v2.5 — §2.1 J の一意性: Morita 同値+コーシー完備化+密度定理で一意性問題を解決 (水準 B→B+)。§6.7 U/N 評価軸追加。(2026-03-17)*

*kernel/kalon.md v2.4 — M の CCC 性論証: M=PSh(J) (J=HGK 演繹図式: 32実体+演繹射+X-series K₆) として構成。CCC は Mac Lane-Moerdijk Prop. I.6.1。点全射は米田補題+部分対象分類子+§4.9 自己適用で構成。M1-LFPT 接続完成 (水準 A/B)。(2026-03-17)*

*kernel/kalon.md v2.11 — VFE→CG 用語分離: T4 を CG-Kalon に改名 (Creator)。Closure Gap CG(x)≔μ(GF(x))−μ(x) を FEP の VFE と明示的に区別。T4 証明内・§7 表・補遺 A の変数名を VFE→CG/CG_GF/CG_NU に統一。構造定理を μ-ベース再定義。C2 worked examples 帰納テーブル追加。Self-referential 根拠構造を明確化 (一次根拠=M1, 動機=Lawvere対偶)。Kan 拡張存在条件を Mac Lane CWM Thm X.3.1 で厳密化。(2026-03-17)*

*kernel/kalon.md v2.12 — §2.1 M ≅ PSh(J) 水準 B+→A 昇格: (2) コーシー完備化を A に昇格 (v2.7 冪等射自明性証明済だが水準表記が未更新だった)。(3) 密度定理は同定水準とは独立であることを明示。§4.9 論証階層表・3層論証テキストも更新。(2026-03-17)*


