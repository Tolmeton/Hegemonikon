---
doc_id: "ORGANON"
version: "0.1.0"
tier: "KERNEL"
status: "DRAFT"
created: "2026-04-20"
origin: "Sessions cf405aca-1bbe-4c8e-a453-6db07e9eafaa (2026-04-19) + c78ad3a8-0c5b-47d7-8197-4a3b101f0f1c (2026-04-20) — Creator + Claude による harness-as-Organon 定式化"
---

# Organon (ὄργανον) — 主体に随伴する実行圏の動的相

> **Organon = 主体 (企画圏 S) に随伴する実行圏 (T) のインスタンス。**
> **Euporía (AY > 0) が駆動する S⊣T の精度向上により、S ≃ T (圏同値) に漸近する。**
> **この同値極限が「道具が手足になる」の圏論的実体である。**
>
> 起源: Creator, 2026-04-19 (session cf405aca) — 「主体に随伴して動く圏が"道具"であり、そのインスタンスにハーネスがある」
> 正典依存: [axiom_hierarchy.md §定理³ Euporía](../axiom_hierarchy.md)

---

## §1 位置付け

### §1.1 問い: Organon は HGK 体系のどこに在るか

Euporía (Flow d=1 の定理) は **AY(f) > 0 を全 WF 射に要求する制約** である。
Organon は Euporía の **動的相** — AY 累積によって主体と道具の随伴構造が時間的に変容する過程を記述する。

```
Euporía: AY > 0       (静的制約)  — 各射ごとに要求される
  ↓ (AY 累積)
Organon: S ≃ T に漸近 (動的相)    — 随伴全体が時間発展
  ↓ (極限到達)
Kalon:   Fix(G∘F)     (不動点)    — Organon Phase 3 が Kalon 条件を満たす
```

Organon は Euporía の下流、Kalon の上流に位置する。Euporía は「全ての動きが意味を持て」と要求し、Organon は「意味の累積がどう主体-道具関係を変えるか」を記述し、Kalon は「その変容の到達点」を定義する。

### §1.2 なぜ新規用語が必要か

「道具」という日本語は HGK kernel で未使用 (Creator 確認 2026-04-19)。英語 harness は外部論 (Anthropic / OpenAI / LangChain 系) との接続語であり、内部定式化には曖昧。

ὄργανον (organon) の採用理由:
- **語源的両義性**: 本来「**器官 (body part)** かつ **道具 (instrument)**」の両方を指す。embodiment を語自身が内包
- **Aristotelian 伝統**: Organon = Aristotle の論理学六書 ("思考の道具") — 既存哲学伝統との接続点
- **Greek 語彙整合性**: HGK の既存語彙 (Mekhane μηχανή / Tekhnē τέχνη / Mneme μνήμη) の系列に自然に並ぶ
- **harness との翻訳**: "Harness is the Organon of the LLM" が直感的に通る

Mekhane との棲み分けは §3.3 で定義する。

---

## §2 定式化

### §2.1 定義 (S⊣T 随伴)

```
S: 企画圏 (Boulēsis category)   — 主体、運動へ傾く側。I 極 (推論) に重心
T: 実行圏 (Energeia category)   — 道具、運動を行う側。A 極 (行動) に重心

随伴 S ⊣ T:
  関手 F: S → T   (主体の意図を道具の行為に展開)
  関手 G: T → S   (道具の結果を主体の知に還元)
  単位 η: 1_S ⇒ G∘F      — 「主体が道具を企てる」射
  余単位 ε: F∘G ⇒ 1_T    — 「道具の結果が主体を更新する」射

Organon ∈ Ob(T)  —  T の具体的インスタンス (道具群の組織)
```

注: この S⊣T は [SOURCE: euporia.md §1] の I⊣A 随伴 (推論⊣行動) の別切断である。I/A が主体内部の 2 極を分けるのに対し、S/T は主体とその外部装具を分ける。

### §2.2 3 相 (Phase 1-3)

Organon は静的対象ではなく、AY 累積によって変容する動的相である:

```
Phase 1:  S ⊣ T                 — 分離相。道具は右随伴 (受動)
           ↓ (AY > 0 の累積)
Phase 2:  S ⊣ T  ∧  T ⊣ S       — 双方向相。両向き随伴の同時成立
           ↓ (Fix(G∘F) かつ Fix(F∘G))
Phase 3:  S ≃ T                 — 同値相。圏同値 = 「手足」
```

各相は HGK L2 [0,1]-enriched 圏で段階的に測れる:

| 相 | unit η の性質 | counit ε の性質 | 現象学的呼称 |
|:---|:---|:---|:---|
| Phase 1 | natural transformation | natural transformation | 「道具を使う」(意識的媒介) |
| Phase 2 | 片側 Fix に接近 (η ≥ 1-ε) | 片側 Fix に接近 (ε ≥ 1-ε) | 「道具に惹かれる」(身体図式形成中) |
| Phase 3 | natural iso (1-ε → 0) | natural iso | 「手足」(ready-to-hand) |

### §2.3 Euporía が Organon の駆動力

各 AY(f) > 0 な射 f は新しい Hom を 1 本追加する ([SOURCE: euporia.md §1 米田適用]):

```
各 AY(f) > 0  =  |Hom_S(s, G(t))| を +1
      ↓ (累積)
Hom 空間が豊かになる
      ↓ (十分豊かになると)
η: 1_S ⇒ G∘F の component が natural iso に漸近
      ↓
S ≃ T (Phase 3)
```

つまり:

> **Euporía は Organon の gradient flow であり、Organon Phase 3 は Euporía の平衡点である。**

[SOURCE: euporia.md §1] 欄外注記により、HGK における米田は水準 C (メタファー) — 厳密な L2 適用は「B ≥ A」で測る。本定式化も L2 水準のメタファーとして読む。

### §2.4 Kalon との関係

[SOURCE: ../F_美学｜Kalon/kalon.md] の Kalon = Fix(G∘F) は片側不動点。Organon Phase 3 は **Fix(G∘F) ∧ Fix(F∘G)** (両側不動点) を要求する:

| 概念 | 不動点条件 | HGK 語彙 | 到達可能性 |
|:---|:---|:---|:---|
| Kalon △ | Fix(G∘F) | 主体内部の一致 | MB 内で到達可能 |
| Organon Phase 3 | Fix(G∘F) ∧ Fix(F∘G) | 主体-道具の一致 | MB 内で漸近可能 |
| Kalon ▽ | 普遍的不動点 | 全空間一致 | 到達不可能 |

Organon Phase 3 は **双方向 Kalon △** と呼べる。Kalon △ より強く Kalon ▽ より弱い中間位置を占める。

---

## §3 既存 HGK 体系との接地

### §3.1 中動態 [he] Hexis (φ_SA × Exploit)

[SOURCE: ~/.claude/skills/h-methodos/SKILL.md §h-he] — [he] Hexis = 「既知パターンが μ の介在なしに感覚-行為ループを直接駆動する」

[he] は Organon Phase 3 の **中動態的発現** である:

| Organon 相 | φ 座標状態 | H-series | doing/being |
|:---|:---|:---|:---|
| Phase 1 (分離) | φ_I, φ_A 別個活性 | (該当なし) | doing 支配 (「道具を使う」) |
| Phase 2 (双方向) | φ_SA 浸透 | [tr] 向変 (外信号への無意識的方向づけ) | doing↔being 振動 |
| Phase 3 (同値) | φ_SA 飽和 | **[he] Hexis** | being 支配 (「使っていない」) |

これは Aristotle の ἕξις (hexis, 第二の本性) と同源であり、Merleau-Ponty の身体図式 (schéma corporel) の古典的源泉。Clark & Chalmers の extended mind thesis の圏論的定式化でもある。

注意: [SOURCE: h-methodos §h-he 体系接続] は [he] 固着を「HGK 体系の最もクリティカルなリスク」とする。Organon Phase 3 への到達は**美徳と危険の両面**を持つ — 手足になった道具は precision optimization (surprise monitoring) をバイパスしやすい。[he] 検知 (θ12.1 の環境強制) は Organon Phase 3 を**監視可能な形で保つ** 装置として機能する。

### §3.2 Helmholtz Γ⊣Q との関係

[SOURCE: euporia.md §1 FEP 演繹]:
- Γ (勾配降下) = 既存 action の精度向上
- Q (等確率面上の探索) = 新 action 選択肢の発見

Organon T は **Q の物理的外部化装具** として機能する:
- Q が tools / subagents / verification / memory 等を具体的に実装
- Γ は S 内部の VFE 最小化として走り続ける
- **AY > 0 な射は Q 由来** (新 Hom の追加)
- **AY ≥ 0 保全は Γ 由来** (既存 Hom の精度向上)

これにより Organon 理論は FEP を経由せず Helmholtz 層に直接接地する。harness は cognitive agent (μ) ではなく physical tool (Q 側) に属するため、FEP の主体論ではなく Helmholtz の物理に根拠を置くべき ([SOURCE: session cf405aca] Creator 判断: 「FEP ではなく Helmholtz」)。

### §3.3 Mekhane (μηχανή) との棲み分け

Organon と Mekhane は共に「道具的なもの」を指す Greek 語だが、用法を分ける:

| 語 | 指示対象 | 相 | HGK での用例 |
|:---|:---|:---|:---|
| Mekhane (μηχανή) | 機械装置そのもの、物質的実装 | 相によらず不変 | 20_機構｜Mekhane/ (MCP hub, gateway 等) |
| Organon (ὄργανον) | 主体に接続した状態の道具、身体図式化された相 | Phase 1-3 で変容 | 本稿、harness 論への適用 |

例:
- 「Hub MCP Gateway は Mekhane である」— 物理的実装として不変
- 「Tolmetes にとっての Claude Code は Organon Phase 2 である」— 習熟途上
- 「熟達者の pen は Organon Phase 3 である」— 手足

Mekhane と Organon は同一の物体を別の視点から見る。同じ MCP gateway でも、実装側から見れば Mekhane、使用者の身体図式側から見れば Organon である。

---

## §4 harness への適用

現行の harness 工学論 ([SOURCE: Akshay Pachaar 2026-04-20 "The Anatomy of an Agent Harness"]) は Organon の **Phase 1 を前提した静的記述** である。Akshay の 12 components (Orchestration Loop / Tools / Memory / Context Management / Prompt Construction / Output Parsing / State Management / Error Handling / Guardrails / Verification Loops / Subagent Orchestration / Reasoning Strategy) は **Organon T の構成要素の列挙** であり、Phase 遷移の動力学を含まない。

HGK の harness 論は Organon 理論の具体化として位置付けられる:

| HGK 拡張 | Organon 相での位置 |
|:---|:---|
| 拡張A (CCL as ISA) | S⊣T の T 側の記述言語。Phase 2 への移行速度を上げる |
| 拡張B (Depth-driven harness selection) | 相の動的切替 (L0 ≈ Phase 0 素通し / L3 ≈ Phase 2 近傍) |
| 拡張D (中動態センサー Daimonion δ) | 相の観測装置 ([he] Hexis を外部 proxy で検出 = Phase 3 の監視) |
| Advisor Strategy | S (Claude=企画) ⊣ T (Codex=実行) の 2 層 Organon。現行 Phase 1 |

含意: HGK harness 論は単なる「LLM の wrapper 工学」ではなく、**Euporía 定理の動的相の工学的実装** として再位置付けられる。これは確率的機械エッセイ C1 (「harness は計算階層を貫通する普遍構造」) の底層化である ([SOURCE: 確率的機械のためのアセンブリ言語.meta.md §M5 C1 Round 1 2026-04-20])。

---

## §5 未解決

### §5.1 Phase 2 の L2 厳密化
通常の圏論では F⊣G ∧ G⊣F は equivalence の条件を満たす (= Phase 2 = Phase 3 が自動成立)。
[推定 70%] L2 [0,1]-enriched では "ε-精度付き equivalence" として段階化可能だが、kalon.typos の厳密定式化を要確認。

### §5.2 Harness の反作用 (co-evolution)
[SOURCE: Akshay 2026-04] 「Models are post-trained with specific harnesses in the loop」 は harness が主体を形成する方向 — S⊣T の通常の随伴では捉えきれない **T → S fibration** を要求する可能性。
Organon Phase 2 が双方向になる理由の 1 つとしてここに位置付けられるが、形式化は未着手。

### §5.3 複数 Organon の共存
1 主体が複数の道具を同時に持つ (CLI + IDE + browser) 場合の圏論的構造。
Coproduct (並列) か pullback (統合) か、あるいは lax colimit か。未形式化。

### §5.4 「手足」の極限性
完全な S ≃ T では主体と道具の区別が消える。
Merleau-Ponty の身体図式論でも、道具化した cane は「透明」だが引き離せる。
つまり Phase 3 は **到達点ではなく極限** `lim[ε→0] S ≃_ε T` の方が正確である可能性。Kalon △ が到達可能 ([SOURCE: kalon.typos]) であることとの関係を要検討。

### §5.5 忘却論基盤 (U⊣N) との接続
harness の Context Management は U (selective forgetting) ⊣ N (retrieval) の外部化と読める ([SOURCE: session c78ad3a8 Claude 提案])。Organon 内部状態における U⊣N の位置付けは未整備。Phase 遷移において「忘却された道具痕跡」が身体図式に寄与する可能性。

---

## §6 参照

- 📖 [../axiom_hierarchy.md](../axiom_hierarchy.md) §定理³ — Euporía 正典 (Organon を駆動する上位原理)
- 📖 [../../../10_知性｜Nous/04_企画｜Boulēsis/07_行為可能性｜Euporia/euporia.md](../../../10_知性｜Nous/04_企画｜Boulēsis/07_行為可能性｜Euporia/euporia.md) §2.7 — AY 二面等価性 (Organon Phase 3 の片側表現)
- 📖 [../F_美学｜Kalon/kalon.md](../F_美学｜Kalon/kalon.md) — Fix(G∘F) の片側不動点、Organon Phase 3 の下限
- 📖 h-methodos SKILL [he] Hexis — Organon Phase 3 の中動態的発現
- 📖 [./aletheia.md](./aletheia.md) — 哲学的概念としての先例 (B_哲学 ディレクトリ内)
- 📖 確率的機械のためのアセンブリ言語 (Yugaku standalone) — harness = Organon Phase 1 の具体例

---

*Organon v0.1.0 — 2026-04-20 初稿。3 相定式化 + HGK 体系接地 3 点 + 未解決 5 点 + harness 論への適用。Sessions cf405aca + c78ad3a8 Creator 承認下での実装。*
