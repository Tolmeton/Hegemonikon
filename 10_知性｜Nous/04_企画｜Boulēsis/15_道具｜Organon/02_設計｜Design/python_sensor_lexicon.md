# Python Sensor — SKILL.md 48 からの Lexicon 抽出設計

> **位置付け**: [sensor_triad_formal.md §4.2](./sensor_triad_formal.md) で定義した関手 $F_{\text{text}}$ の Python 実装側 (keyword / regex / embedding) の辞書構築設計。
>
> **前提**: 本文書は **SKILL.md 48 を Single Source of Truth として辞書を機械的に抽出する規則**を定める。手書きチューニングは最小化。
>
> **対象外**: LLM Sensor (Haiku/Codex 意味分類) は次文書 B で扱う。
>
> **確信度**: [確信 88%] 抽出規則の機械性は SKILL.md 構造の均質性から演繹的 (Level B)。discriminability の実測精度は pilot 後に較正 (Level C)。

---

## §1 目的

`~/.claude/skills/` 配下の 48 SKILL.md ファイルから、以下を機械的に抽出し単一の lexicon artifact に統合する:

1. 各 verb の 48 座標メタデータ
2. 発話テキスト → verb weight を計算する keyword/regex 辞書
3. embedding 類似度計算用 anchor prompt 集合
4. 近接 verb の discriminability 規則

この lexicon が Python Sensor (`F_{\text{text}}^{\text{python}}$) の決定論的バックエンドとなる。SKILL.md の改訂に追従する**片道関手** (SKILL.md → lexicon.yaml) として実装する。

---

## §2 用語固定

| 用語 | 定義 | 根拠 |
|---|---|---|
| **Lexicon** | 48 verb の分類辞書 (yaml/json 化された artifact) | 本文書固有 |
| **Anchor prompt** | 各 verb の canonical 発話例 (embedding 類似度計算用) | 本文書固有 |
| **Discriminator rule** | 近接 verb 間の曖昧性を解消する規則 | 本文書固有 |
| **trigonon metadata** | SKILL.md typos block 内の `[knowledge] trigonon: series=..., type=..., verb_id=V.., coordinates=[...]` 行 | [SOURCE: ~/.claude/skills/the/SKILL.md L48] |

---

## §3 入力: SKILL.md 48 の構造

### §3.1 均質な frontmatter + description 構造

全 SKILL.md は以下の構造を持つ [SOURCE: ~/.claude/skills/noe/SKILL.md L1-8, ~/.claude/skills/the/SKILL.md L1-10 の目視確認]:

```yaml
---
name: {slash_verb}
description: >
  V{N} {Greek} ({Japanese_meaning}) — {族}族 {座標 e.g. T1/S1/S2/T3} ({flow description})。
  {trigger description 1-2 sentences}
  Use for: {positive_phrase_list}.
  NOT for: {exclusion_phrase_list (→ /other_verb)}.
  (optional: 派生, 接続, 原則)
---
```

### §3.2 Typos block 内の構造化メタデータ

Typos block 内に以下のフィールドが含まれる [SOURCE: ~/.claude/skills/the/SKILL.md L36-50]:

| field | 位置 | 内容 |
|---|---|---|
| `<:scope:` 発動 | L37 付近 | 強い positive trigger 語彙 |
| `<:scope:` 非発動 | L38 付近 | exclusion (→ /other) |
| `<:scope:` 混同注意 | L39 付近 | 近接 verb との discriminator 規則 |
| `<:focus:` トリガー | L43 付近 | 短い誘発句 |
| `<:focus:` 停止ワード | L44 付近 | **anti-signal** (stop patterns) |
| `trigonon` metadata | L48 付近 | 48 座標の機械可読表現 |
| `adjunction` | L50 付近 | H型/D型/X型 接続先 verb |

### §3.3 H-series (S∩A) の取扱

H-series 12 前動詞 ([tr], [sy], [pa], [he], [ek], [th], [eu], [sh], [ho], [ph], [an], [pl]) は `h-telos`, `h-methodos` 等の compound skill として存在するが、§[sensor_triad_formal.md §3.3](./sensor_triad_formal.md) の規則により **F_text は S∩A を所管しない** (F_being 専属)。したがって Python Sensor の lexicon からは H-series を除外し、**36 Poiesis verb のみを対象**とする。ただし S∩A の発話的 proxy (例: 「何かおかしい」「そろそろ」) は **Pattern 6 検出**のため別辞書 (h_series_proxy_lexicon) として分離記録する。

---

## §4 出力: Lexicon Schema

### §4.1 ファイル配置

```
mekhane/organon/telemetry/
├── sensor_lexicon.yaml        # メイン辞書 (36 Poiesis)
├── h_series_proxy.yaml        # S∩A 発話 proxy (Pattern 6 用)
├── anchors/                    # embedding anchor prompts
│   ├── V01_noe.txt
│   ├── V25_the.txt
│   └── ... (36 files)
└── discriminators.yaml        # 近接 verb discriminator rules
```

### §4.2 per-verb entry schema

```yaml
- verb_id: V01
  canonical_slash: /noe
  greek_root: Noēsis
  japanese_meaning: 認識
  coordinate:
    quadrant: I          # S / I / A (S∩A は別辞書)
    family: Telos        # Telos / Methodos / Krisis / Diástasis / Orexis / Chronos
    pole: Internal       # family 固有 (E/P, Explore/Exploit, C/U, Mi/Ma, +/-, Past/Future)
    flow_cell: T1        # T1/T2/T3/T4/S1/S2 (SKILL.md 内表記)

  positive_lexicon:
    primary:             # Use for から抽出 (weight 1.0)
      - 本質理解
      - 構造分析
      - 深い認識
      - 前提の根本的再考
      - 圏論的普遍性
    triggers:            # focus: トリガー から抽出 (weight 0.8)
      - 深く理解
      - 本質を捉え
      - 構造的な洞察
    stems:               # 形態素レベル lemma (weight 0.6)
      - 理解
      - 本質
      - 構造
      - 洞察

  negative_lexicon:
    exclusions:          # NOT for から抽出 (→ other_verb)
      - target: "単純な実装"
        redirect_to: /tek
      - target: "発散だけ"
        redirect_to: /ske
      - target: "意思決定"
        redirect_to: /pai
    stop_words:          # focus: 停止ワード から抽出 (negative weight)
      - 表面で十分
      - 前に見た

  anchor_prompts:        # 埋め込み類似度用 (3-5 文)
    - "この概念の本質を構造として理解したい"
    - "前提を深く透徹し、結合点を見通す"
    - "圏論的普遍性の観点から核を抽出する"

  confidence: direct     # direct / inferred (SKILL.md の明示性で決まる)
  extracted_at: 2026-04-20
  source_skill: ~/.claude/skills/noe/SKILL.md
```

### §4.3 discriminator schema

```yaml
- pair: [V01_noe, V05_ske]   # 近接 verb ペア
  axis: Function              # 差異軸 (族レベル)
  rules:
    - if_contains: 発散 | 代替案 | 可能性
      prefer: V05_ske
      weight: 0.9
    - if_contains: 本質 | 構造 | 核
      prefer: V01_noe
      weight: 0.9
  source: ~/.claude/skills/noe/SKILL.md "NOT for: 発散だけ (→ /ske)"
```

---

## §5 抽出パイプライン

### §5.1 Stage 1: Parse SKILL.md

1. `~/.claude/skills/*/SKILL.md` を glob
2. YAML frontmatter を pyyaml で parse
3. `description` multi-line 文字列から正規表現で field 抽出:
   - `V(\d+) (\w+)` → verb_id + greek_root
   - `Use for: (.+)\.` → positive_lexicon.primary
   - `NOT for: (.+)\.` → negative_lexicon.exclusions
4. typos block (````typos ... ````) を抽出し:
   - `<:scope:` の 発動 / 非発動 / 混同注意 を parse
   - `<:focus:` の トリガー / 停止ワード を parse
   - `trigonon:` 行から座標を parse

### §5.2 Stage 2: 形態素解析 → stems

primary_lexicon と triggers から janome/sudachi (日本語) で名詞・動詞の lemma を抽出 → `stems` field。英語は spaCy の lemmatizer。

### §5.3 Stage 3: Anchor prompt 生成

3-5 文の anchor を以下のテンプレートで合成:

- "{primary_lexicon[0]}したい"
- "{primary_lexicon[1]}が必要"
- "{triggers[0]}を {japanese_meaning}する"
- {SKILL.md 内の「原則」行 (存在すれば)}

### §5.4 Stage 4: Discriminator 抽出

`NOT for: X (→ /other)` と `混同注意: /A vs /B — X→/A、Y→/B` から自動生成。両方向の redirect rule を記録。

### §5.5 Stage 5: Validation

1. 48 verb 全てが extract された (H-series 12 除外後 36 verb)
2. trigonon 座標と description の flow_cell が整合
3. 全 verb の anchor prompt が 3 件以上
4. primary_lexicon ∩ other_verb.primary_lexicon のサイズが閾値未満 (§7 参照)

---

## §6 分類スコアリング規則

text chunk $t$ に対する verb $v$ の Python Sensor weight:

$$
w_v(t) = \alpha \cdot \text{KeywordScore}_v(t) + \beta \cdot \text{SyntacticScore}_v(t) + \gamma \cdot \text{EmbeddingScore}_v(t)
$$

初期パラメータ: $\alpha=0.3, \beta=0.2, \gamma=0.5$。pilot で較正。

### §6.1 KeywordScore

```
score = Σ(weight_i × tf(lexicon_i, t))
      - Σ(stop_weight_i × tf(stop_word_i, t))
```

where:
- primary_lexicon: weight 1.0
- triggers: weight 0.8
- stems: weight 0.6
- stop_words: negative weight -1.0

正規化: sigmoid で [0, 1] に cap。

### §6.2 SyntacticScore

形態素解析の結果から:
- 動詞 / 名詞 の比率
- 「〜したい」「〜が必要」等の modal expression
- Phase marker (Phase 0-N) 存在で **/noe, /bou, /ene 系を boost**

### §6.3 EmbeddingScore

multilingual sentence-transformer (候補: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`) で text と anchor の cos sim の max を取る。

### §6.4 最終正規化

36 verb の raw weight を softmax で soft distribution に。閾値 $\theta=0.3$ 以上を「発火」とする (multi-label 許容)。

---

## §7 Discriminability 検証手続き

### §7.1 Pairwise Jaccard 検査

全 (36 choose 2) = 630 ペアで primary_lexicon の Jaccard 係数を計算:

$$J(v_i, v_j) = \frac{|L_i \cap L_j|}{|L_i \cup L_j|}$$

- $J > 0.5$: **高重複** (discriminator rule 追加必須)
- $0.2 < J \leq 0.5$: 中重複 (discriminator 推奨)
- $J \leq 0.2$: 低重複 (問題なし)

### §7.2 想定される高重複ペア

[推定 70%] 以下のペアは pilot 前から high-J の懸念:

| ペア | 族内/族間 | 重複懸念 | 解消手段 |
|---|---|---|---|
| /the vs /ere | Telos S1 vs Methodos S1 | 「見る」「走査」「対象」 | 混同注意の自動抽出 [SOURCE: ~/.claude/skills/the/SKILL.md L39] |
| /the vs /sap vs /ski vs /prs | 全 S 象限 | 「知覚」「読む」「確認」 | pole で分離: External/C/U/Mi が決定的 |
| /noe vs /lys | Telos T1 vs Diástasis T1 | 「深く」「分析」「構造」 | Scale pole (Internal vs Micro) で分離 |
| /ske vs /zet | Methodos T1 Explore vs Telos T3 E | 「発散」「問い」 | Flow (I vs A) で分離 — Text Sensor では曖昧 → Tool Sensor crosscheck で補正 |
| /beb vs /kat | Orexis T1+ vs Krisis T1 C | 「確信」「承認」 | Precision (承認 vs 固定) で分離 |

### §7.3 Discriminator rule の自動生成

§4.3 の schema に従い、`NOT for:` と `混同注意:` から両方向の redirect rule を生成。pilot で誤分類が残るペアには手動 rule を追加。

---

## §8 近接 verb の Handling

### §8.1 階層的解決

1. **Family 判定**: trigonon metadata で決定 (曖昧性なし)
2. **Quadrant 判定**: Flow marker (Phase 構造、動詞時制) で決定
3. **Pole 判定**: 族固有の pole lexicon (例: Telos なら "目的" vs "認識" で E/P 分離)

### §8.2 Quadrant 曖昧時の fallback

Text chunk が「考える (I か S か A か曖昧)」だけの場合:

- Tool Sensor の直近 event と crosscheck (Pattern 8 検出の逆利用)
- Syntactic marker で推定: 「〜している」= S/I, 「〜する」= A
- それでも決まらなければ confidence=inferred として multi-label 出力

### §8.3 相互排他性の緩和

axiom L250 象限純粋性原則は**認知操作の定義面**での規則であり、**発話テキストの分類**では単一 chunk が複数 verb に貢献しうる。Python Sensor は multi-label を許容し、曖昧性は weight distribution で表現する。

---

## §9 実装段階

| Phase | 内容 | 工数 |
|---|---|---|
| **P0** | SKILL.md 48 parse → yaml skeleton (36 Poiesis) | 半日 |
| **P1** | KeywordScore (primary + triggers) 実装 + 24 verb で pilot | 2-3 日 |
| **P2** | SyntacticScore + EmbeddingScore 追加 | 1 週 |
| **P3** | Discriminator rule extraction + pairwise Jaccard 検証 | 3 日 |
| **P4** | h_series_proxy.yaml (S∩A 発話 proxy) 作成 | 2 日 |
| **P5** | pytest: 36 × 5 synthetic examples → top-1 accuracy > 0.8 | 3 日 |

総計: 2-3 週 (Codex 委託想定で 1.5 週に短縮可能)。

---

## §10 未決事項

1. **Stems 抽出の形態素解析器選択**: janome (軽量、pure Python) vs sudachi (辞書大、精度高)。pilot で比較
2. **Embedding モデル選択**: paraphrase-multilingual-mpnet-base-v2 で十分か、日本語特化 (ruri 等) が必要か
3. **閾値 $\theta$**: pilot で precision-recall curve を描いて決定
4. **α/β/γ の較正**: 初期 0.3/0.2/0.5 は仮。実データで MLE/grid search
5. **H-series 36 → 48 拡張の可能性**: 将来 F_text が S∩A の発話的 proxy も限定的に担う場合、h_series_proxy_lexicon を本 lexicon と統合する設計余地を残す
6. **SKILL.md 改訂追従**: ファイル監視 hook で SKILL.md 変更時に lexicon 再生成するか、明示的 rebuild command にするか

---

## §11 次文書への接続

| 次 | 目的 | 担当 |
|---|---|---|
| **D: Codex 全体委託 plan** | Wave 0 gap analysis 相当の Sensor Triad MVP 実装委託。本文書 A と sensor_triad_formal.md (C) を spec として Codex に投入 | Tolmetes 承認後に Codex |
| **B: LLM Sensor prompt 雛形** | Haiku/Codex 用の意味分類プロンプト設計。本文書の lexicon を system prompt に固定 | Codex prototype |
| **後続 E (未命名)**: telemetry runtime / detection rule runtime の統合設計 | — | Organon Wave 4 |

---

## §12 改訂履歴

| Version | Date | 変更 |
|---|---|---|
| 0.1 | 2026-04-20 | 初版。Tolmetes 承認下で §1-§11 を書き下ろし。SKILL.md 48 の実構造 (trigonon + Use for + NOT for + 混同注意) を確認した上で、機械的抽出規則を固定。H-series 12 除外 (F_being 専属) を明示 |
