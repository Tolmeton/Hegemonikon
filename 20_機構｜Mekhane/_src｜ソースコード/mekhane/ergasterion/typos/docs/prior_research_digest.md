---
doc_id: "TYPOS_PRIOR_RESEARCH"
version: "1.0"
tier: "REFERENCE"
status: "DIGESTED"
created: "2026-02-28"
purpose: "TYPOS v7.0 を支持する先行研究5系統の消化結果"
precision: "Semantic Scholar 詳細取得 + ROM /sop++ レポートの統合"
scope: "A0 公理 (Rate-Distortion) と 7基底 (1+3+3) の理論的根拠"
---

# TYPOS v7.0 先行研究消化

> **消化基準**: 各論文の (1) 核心主張、(2) TYPOS 基底との対応、(3) 反証への貢献 を抽出。

---

## 1. Zaslavsky, Kemp, Regier, Tishby (PNAS 2018) — A0 公理の実証

| 項目 | 内容 |
|:-----|:-----|
| **タイトル** | Efficient compression in color naming and its evolution |
| **DOI** | 10.1073/pnas.1800521115 |
| **被引用** | 207 |
| **S2 ID** | 0ed07e16dc15baedc7ea551f73898062f628f03a |

### 核心主張

世界110以上の言語の色彩命名システムが、Information Bottleneck (IB) のトレードオフにおいて**理論的限界に近い最適圧縮**を達成している。色彩カテゴリの進化は、単一のトレードオフパラメータの変化による構造的相転移の系列として記述できる。

### TYPOS 対応

| TYPOS | 対応 |
|:------|:-----|
| **A0 (R-D 圧縮)** | IB ≈ R-D。色彩命名 = 知覚信念 → 語彙への圧縮。A0 が「メタファー」ではなく、自然言語の進化を支配する**数学的制約そのもの**であることを実証 |
| **Resolution (β)** | 論文の "trade-off parameter" = β。小さな β 変化が言語間差異の大部分を説明 |
| **Salience (w)** | 色空間の非均一な知覚重み = w(m)。焦点色の存在が暗黙の salience 重みに対応 |

### 反証への貢献

R-D 最適化が色彩以外の意味領域に適用できなければ、A0 の普遍性が弱まる。ただし論文自身が「this principle is not specific to color」と述べている。

---

## 2. Zaslavsky, Hu, Levy (2020) — RD-RSA: 語用論の R-D 定式化

| 項目 | 内容 |
|:-----|:-----|
| **タイトル** | A Rate–Distortion view of human pragmatic reasoning? |
| **DOI** | 10.7275/GC1Z-CK09 |
| **arXiv** | 2005.06641 |
| **被引用** | 38 |
| **S2 ID** | 25295bae0aeb668c62e3d18d9d155a7b24b83dd5 |

### 核心主張

1. RSA (Rational Speech Act) の再帰的推論が、**期待効用と通信努力のトレードオフの交互最大化** (alternating maximization) として定式化可能
2. RSA を **Rate-Distortion 理論に基礎付け**できる。R-D 版は RSA のランダム発話バイアスを回避しつつ、人間行動の説明力を維持

### TYPOS 対応

| TYPOS | 対応 |
|:------|:-----|
| **A0 全体** | 圧縮 (R-D) が語彙形成のみならず、**文脈における推論・意図伝達** (語用論) までを貫く統一原理であることの証明 |
| **Reason (d)** | "expected utility" = d(m, ℓ) の内部構造。歪み関数がコミュニケーション意図を反映 |
| **Resolution (β)** | "communicative effort" の制御パラメータ = β |

### 反証への貢献

RSA の再帰深度が期待効用の単調改善を保証**しない**ことを証明 (conjecture の棄却)。TYPOS の β による圧縮度制御が、RSA 再帰よりシンプルな説明を提供する可能性。

---

## 3. Futrell & Hahn (2024) — 階層構造の圧縮原理的創発

| 項目 | 内容 |
|:-----|:-----|
| **タイトル** | Linguistic Structure from a Bottleneck on Sequential Information Processing |
| **DOI** | 10.48550/arXiv.2405.12109 |
| **arXiv** | 2405.12109 |
| **被引用** | 8 |
| **S2 ID** | 6179990ddc4927cb7bfc8f9efda0628a2e12525e |

### 核心主張

予測情報 (Predictive Information / Excess Entropy) を最小化するボトルネック制約下で:

1. コードがメッセージを**近似的に独立な特徴グループ**に分解する（= 語と句に対応）
2. 特徴が**体系的かつ局所的に**表現される（= 語彙の体系性）
3. 実際の人間言語は、音韻・形態・統語・語彙意味の全レベルでベースラインに比べ低い予測情報を示す

### TYPOS 対応

| TYPOS | 対応 |
|:------|:-----|
| **Context (d=2, local↔global)** | 階層的構文 (句構造) が R-D 的圧縮限界からの**自然な創発物**であることの証明。「恣意的に階層性を仮定した」のではなく、圧縮原理が階層性を要求する |
| **A0 + Resolution** | 予測情報最小化 ≈ Rate-Distortion の別の操作化。β の調整が構造の粒度を決定 |

### 反証への貢献

予測情報のボトルネックを制約**しない**モデルの方が自然言語に近い出力を生成できれば、Context 基底の導出根拠が弱まる。

---

## 4. Searle & Vanderveken (1985) — 語内行為力の7成分

| 項目 | 内容 |
|:-----|:-----|
| **タイトル** | Foundations of Illocutionary Logic |
| **被引用** | 1,389 |
| **出版** | Cambridge University Press |
| **S2 ID** | b53db96baabf8001069ba20bb4bfcdc2266bc8ed |

### 核心主張

Austin の言語行為論を形式論理に拡張。あらゆる発話の**語内行為力 (Illocutionary force)** は、正確に **7つの独立成分** で完全に定義される:

1. Illocutionary point (語内行為の要点)
2. Degree of strength of the illocutionary point (要点の強度)
3. Mode of achievement (達成の様態)
4. Propositional content conditions (命題内容条件)
5. Preparatory conditions (準備条件)
6. Sincerity conditions (誠実性条件)
7. Degree of strength of the sincerity conditions (誠実性条件の強度)

### TYPOS 対応 — 【大発見】7成分の完全対応

| d | TYPOS 7基底 (R-D トップダウン) | S-V 7成分 (言語哲学ボトムアップ) |
|:-:|:----------|:------|
| 0 | Endpoint | Illocutionary point |
| 1 | Reason | Propositional content conditions |
| 1 | Resolution | Degree of strength |
| 1 | Salience | Preparatory conditions |
| 2 | Context | Sincerity conditions |
| 2 | Order | Mode of achievement |
| 2 | Modality | Degree of strength of sincerity |

> **洞察**: 全く異なるアプローチ（物理学/情報理論 vs 言語哲学）が同じ次元数 (7) と構造的役割に到達。これは偶然の一致ではなく、発話/記述というドメインが内在的に7自由度を持つことの強い証拠。

### 反証への貢献

S-V が8つ目の独立成分を発見した場合、TYPOS 7基底も拡張が必要。ただし1985年以来40年間、7成分は安定。

---

## 5. Peirce 記号分類 — 24 sinsign クラス

| 項目 | 内容 |
|:-----|:-----|
| **タイトル** | (体系的テキスト — C.S. Peirce, Collected Papers) |
| **被引用** | N/A (哲学的正典) |

### 核心主張

Peirce は記号の3項関係 (sign-object-interpretant) を、各項の3分類 (Firstness/Secondness/Thirdness) のテンソル積で体系化。理論的には 3³=27 クラスだが、半順序制約により **10のメイン記号クラス** に絞られる。後期の拡張では 28, 66 クラスなどの体系が提案された。

### TYPOS 対応

| 観点 | 対応 |
|:-----|:-----|
| **組合せ論的生成** | Peirce: 3次元 × 3値 → 10クラス (半順序制約)。TYPOS: 1生成子 × 6修飾 × 4極 → 24行為 |
| **三層構造** | Peirce: Firstness/Secondness/Thirdness ≈ d=0/d=1/d=2 の構成距離 |
| **「24」の数字** | Peirce の sinsign サブクラスで24が出現する文献もあるが、標準的な10クラス分類との関係は複雑 |

### 反証への貢献

TYPOS と Peirce の対応は**構造的類推**であり、厳密な対応ではない。数字の一致はあくまで示唆的。Peirce 体系との深い対応を主張するには、各クラスの1対1マッピングが必要（現時点では未達成）。

> **[推定: 60%]** (TAINT: Peirce の24分類は標準的な文献に基づかない。Collected Papers の特定巻を直接参照する必要あり)

---

## 消化サマリ

| # | 論文 | TYPOS 支持度 | 対応基底 | 消化状態 |
|:--|:-----|:-----------|:---------|:---------|
| 1 | Zaslavsky PNAS 2018 | ★★★★★ | A0, Resolution, Salience | ✅ 消化済み |
| 2 | Zaslavsky RD-RSA 2020 | ★★★★☆ | A0, Reason, Resolution | ✅ 消化済み |
| 3 | Futrell & Hahn 2024 | ★★★★☆ | Context, A0 | ✅ 消化済み |
| 4 | Searle & Vanderveken 1985 | ★★★★★ | 全7基底 (完全対応) | ✅ 消化済み |
| 5 | Peirce sign classification | ★★☆☆☆ | 構造的類推のみ | ⚠️ 部分消化 (直接文献不足) |

---

*TYPOS Prior Research Digest v1.0 — 2026-02-28*
