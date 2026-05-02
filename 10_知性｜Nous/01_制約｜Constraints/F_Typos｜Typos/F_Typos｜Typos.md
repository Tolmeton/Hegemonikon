```typos
#prompt typos-v8_4-official-reference
#syntax: v8
#depth: L3

<:role: Týpos v8.4 公式リファレンス — 構文・理念・実装・品質の完全仕様 :>

<:goal: v8.4 の全仕様を一文書に集約し、Typos 記述者・実装者・理論研究者の単一正本となる :>

<:spec:
  - この文書自体が Typos v8 で記述された自己言及的リファレンス (Fix(G∘F) の実証)
  - <: :> 構文のみを使用。@ 構文は廃止
  - ソース: v8_syntax_reference.md / typos_hyphe_map.md / RFC rfc_typos-v8-syntax.md を統合
/spec:>

<:context:
  - [file] mekhane/ergasterion/typos/v8_tokenizer.py (priority: CANONICAL)
  - [file] mekhane/ergasterion/typos/v8_ast.py (priority: CANONICAL)
  - [file] mekhane/ergasterion/typos/v8_compiler.py (priority: CANONICAL)
  - [file] mekhane/ergasterion/typos/typos.py (priority: CANONICAL)
  - [file] mekhane/mcp/typos_mcp_server.py (priority: HIGH)
/context:>
```

---

# Týpos v8.4 — 公式リファレンス

---

## 第Ⅰ部: 理念と設計原理

```typos
<:principle:
  一語定義
  TYPOS = 多次元の情報 (溶液) を 1次元 (テキスト) に結晶化する、最も Kalon な記述方式

  狭義 :: argmax_G Fix(G∘F) :: 最も Kalon な右随伴 G (結晶化関手)
  広義 :: Hyphē|_{1D-faithful} :: Hyphē の構造を1次元テキストへ忠実充満射影
/principle:>
```

### §1. Hyphē との関係 — 結晶化モデル

```typos
<:detail:
  F ⊣ G 随伴構造
  F (溶解 = 読取): 1DText → CogSpace → テキストを読み、多次元の認知空間に展開
  G (結晶化 = 記述): CogSpace → 1DText → 認知空間からテキストに結晶化

  η: Id ≤ G∘F — 読んで再記述 ≥ 元 (暗黙知の明示化)
  ε: F∘G ≤ Id — 蒸留→再読解は元を超えない
  Fix(G∘F) = G∘F(t) = t — 読んで書き直しても変わらないテキスト = Kalon な記述
/detail:>

<:schema:
  <:dimension:
    name: L(c) 損失関数
    description: Kalon 判定基準
    <:criteria:
      Drift ≈ 0 :: ||G∘F(c) - c||² → 0 :: 再結晶化で構造が変わらない
      EFE > 0 :: -EFE(c) が大 :: compile/expand/parse が可能
      L(c) = 0 :: c は Kalon :: 最小十分な構造で最大の意図再現
    /criteria:>
  /dimension:>
/schema:>
```

### §2. 4基底モデル — 理論的基盤

```typos
<:table:
  d :: 基底 :: Opposition (相補的対立) :: HGK 対応 :: SFL 対応
  0 :: Image :: 信念 ↔ 記号 :: Flow (I↔A) :: Ideational
  1 :: Endpoint :: 始域 ↔ 終域 :: Value (E↔P) :: Interpersonal
  1 :: Reason :: 志向 ↔ 経緯 :: Function (Expl↔Expt) :: (FEP 拡張)
  2 :: Context :: 局所 ↔ 大域 :: Scale (Mi↔Ma) :: Textual
/table:>
```

```typos
<:principle:
  設計哲学
  Typos は「人間→LLM への翻訳中間語」ではない。
  人間も LLM も直接読み書きする普遍言語である。
  XML コンパイルはフォールバックであって主目的ではない。
/principle:>
```

### §3. 設計決定の根拠

```typos
<:table:
  判断 :: 選択 :: 棄却 :: 理由
  デリミタ :: <: :> :: <@ @> / [: :] / {% %} :: 対称的、衝突ゼロ、XML の < を継承
  閉じタグ :: :> + /name:> :: </name> :: :> で軽く /name:> で安全に
  属性 :: なし :: <:name attr="v": :: 公理的に不要。Salience 軸で表現可能
  ディレクティブ数 :: 24全維持 :: 実用15個に絞る :: Zipf's law。行為可能性は削らない
  デフォルトターゲット :: Typos-native :: XML / Markdown :: 普遍言語
  拡張子 :: .typos :: .prompt / .typ :: 新バージョンの明示
/table:>
```

```typos
<:detail:
  衝突リスク分析
  自然言語 (日英) :: <: ゼロ :: :> ほぼゼロ (古い顔文字のみ) :: ✅
  Python / JS / TS :: なし :: なし :: ✅
  JSON / YAML / XML :: なし :: なし :: ✅
  Markdown :: なし :: なし :: ✅
  正規表現 :: 極めてレア :: 極めてレア :: ✅
/detail:>
```

---

## 第Ⅱ部: 構文仕様

### §4. トークン定義

```typos
<:table:
  トークン :: 構文 :: 意味
  開始 :: <:name: :: ディレクティブブロックの開始
  無名閉じ :: :> :: 最寄りの開始ブロックを閉じる
  名前付き閉じ :: /name:> :: 指定した名前のブロックを明示的に閉じる (深いネスト推奨)
/table:>
```

### §5. 記述形式 (3形式)

```typos
<:case:
  <:example:
    <:input: インライン形式 — 短い値を1行で宣言 :>
    <:output:
      <:role: シニアコードアナリスト :>
    /output:>
  /example:>

  <:example:
    <:input: ブロック形式 — 複数行コンテンツ :>
    <:output:
      <:spec:
        - エッジケースを網羅すること
        - パフォーマンスに留意すること
      :>
    /output:>
  /example:>

  <:example:
    <:input: ネスト — 名前付き閉じを使用 :>
    <:output:
      <:case:
        <:C-01:
          正常系
          <:if env == "prod":
            - 本番環境用の処理
          /if:>
        :>
      /case:>
    /output:>
  /example:>
/case:>
```

### §6. メタデータヘッダ

```typos
<:table:
  メタデータ :: 意味 :: デフォルト :: 必須
  #prompt :: プロンプト名 :: — :: ✅
  #mixin :: Mixin 定義名 (定義側のみ) :: — :: —
  #syntax :: 構文モード (v8 / v7) :: v8 :: —
  #depth :: ディレクティブ深度レベル :: L3 (全開放) :: —
  #target :: コンパイルターゲット :: typos :: —
/table:>
```

### §7. 24 ディレクティブ (V7 体系)

```typos
<:detail:
  公理的基盤
  A0 (Rate-Distortion) → 7基底 (1+3+3) → 24記述行為 (Endpoint × 6修飾 × 4極)

  role は d=0 生成子 (V7体系の外)。全深度で常に有効。
  24ディレクティブは「行為可能性 (affordance)」であって「埋めなければならない項目」ではない。
  未指定の深度外ディレクティブは静かにスキップされる (エラーにならない)。
/detail:>
```

```typos
<:table:
  族 (Depth) :: 基底 :: ディレクティブ (4極) :: 型 :: 用途
  Why (L1+) :: Endpoint × Reason :: context :: context :: 背景知識 (ContextItem 構造)
  Why (L1+) :: — :: intent :: text :: 設計意図
  Why (L1+) :: — :: rationale :: text :: 根拠
  Why (L1+) :: — :: goal :: text :: 達成目標
  How (L1+) :: Endpoint × Resolution :: detail :: text :: 詳細説明
  How (L1+) :: — :: summary :: text :: 要約
  How (L1+) :: — :: spec :: list_strict :: 制約リスト (旧 constraints)
  How (L1+) :: — :: outline :: text :: 概要構造
  How-much (L2+) :: Endpoint × Salience :: focus :: list :: 想起トリガー
  How-much (L2+) :: — :: scope :: scope :: 発動条件 (3区間構造)
  How-much (L2+) :: — :: highlight :: list :: 減衰耐性アンカー
  How-much (L2+) :: — :: breadth :: text :: 適用範囲
  Where (L2+) :: Endpoint × Context :: case :: case :: 具体例 (旧 examples)
  Where (L2+) :: — :: principle :: text :: 原則
  Where (L2+) :: — :: step :: list :: 手順 (順序付きリスト)
  Where (L2+) :: — :: policy :: text :: ポリシー
  Which (L3) :: Endpoint × Order :: data :: kv :: ツール・リソース (旧 tools/resources)
  Which (L3) :: — :: schema :: schema :: 評価ルーブリック (旧 rubric)
  Which (L3) :: — :: content :: text :: 生成コンテンツ
  Which (L3) :: — :: format :: text :: 出力形式
  When (L3) :: Endpoint × Modality :: fact :: text :: 事実
  When (L3) :: — :: assume :: text :: 仮定
  When (L3) :: — :: assert :: text :: 断言
  When (L3) :: — :: option :: text :: 選択肢
/table:>
```

```typos
<:detail:
  深度レベル一覧
  L0 :: role のみ :: 0族 :: 単純プロンプト (レガシー互換)
  L1 :: + Why + How :: 8種 :: 実装・軽微判断
  L2 :: + How-much + Where :: 16種 :: 設計・分析・通常 WF
  L3 :: 全族 (+Which +When) :: 24種 :: 本質問題・パラダイム (深度未指定時のデフォルト)
/detail:>
```

```typos
<:detail:
  レガシー互換マッピング
  コンパイラが自動変換する旧名。新規記述では V7 正式名を推奨。

  constraints → spec (How族 target-precise)
  examples → case (Where族 source-local)
  tools → data (Which族 source-object)
  resources → data (Which族 source-object にマージ)
  rubric → schema (Which族 source-meta)
/detail:>
```

### §8. 識別子構文 (v8.4)

大文字1字のプレフィックス + アドレスで構造化ノードを命名する。

```typos
<:detail:
  識別子の3形式
  形式 :: 例 :: 用途
  ハイフン :: S-01a :: 単純アドレス
  ブラケット :: S[01a.02] :: 階層アドレス (ドット含む)
  ハイフン+ブラケット :: S-[01a] :: 視覚的明示性
/detail:>

<:table:
  識別子パターン :: 表現できる構造 :: 例
  01, 02, 03 :: chain (線形) :: 手順
  01a, 01b :: fork (分岐) :: 並列仮説
  [01a, 01b]>>02 :: join (合流) :: 証拠統合
  01.01, 01.02 :: tree (階層) :: 入れ子構造
  [01a, 01b]>>[02a, 02b]>>03 :: DAG (有向非巡回) :: 因果ネットワーク
/table:>
```

```typos
<:case:
  <:example:
    <:input: 識別子を持つブロック :>
    <:output:
      <:S-01a: 仮説α — データが不足している :>
      <:S-01b: 仮説β — モデルが適切でない :>
      <:S-02: 両仮説の統合検証 :>
      <:flow: [S-01a, S-01b] >> S-02 :>
    /output:>
  /example:>
/case:>
```

```typos
<:detail:
  コンパイル結果
  同一プレフィックスのノードは @id:{prefix} にグループ化される。

  <:S-01a: α :>  →  prompt.blocks["@id:S"] = [{"address": "01a", "content": "α"}, ...]
  <:S-01b: β :>     prompt.blocks["@S-01a"] = "α"  (個別参照)
/detail:>
```

### §9. flow ディレクティブ (v8.4)

CCL の構造演算子を Typos 内で使用するためのディレクティブ。DAG (有向非巡回グラフ) を1行で表現する。

```typos
<:case:
  <:example:
    <:input: flow 演算子の例 :>
    <:output:
      <:flow: [S-01a, S-01b] >> S-02 :>   ← 並列 → 順序
      <:flow: S-01a * S-01b >> S-02 :>    ← 同上 (* = 並列)
      <:flow: S-01 >> S-02 >> S-03 :>     ← 直列パイプライン
    /output:>
  /example:>
/case:>

<:table:
  記号 :: 意味 :: 例
  >> :: 順序 (chain/pipe) :: A >> B
  * :: 並列 (fork) :: A * B
  [,] :: グルーピング :: [A, B]
/table:>
```

### §10. コンパイラ命令

```typos
<:case:
  <:example:
    <:input: 条件分岐 — if / elif / else :>
    <:output:
      <:if env == "prod":
        <:spec:
          - 誤検出を最小化、後方互換性を維持
        :>
      <:elif env == "staging":
        <:spec:
          - moderate mode
        :>
      <:else:
        <:spec:
          - 疑わしきは報告 (false positive 許容)
        :>
      /if:>
    /output:>
  /example:>

  <:example:
    <:input: mixin 定義と参照 :>
    <:output:
      --- 定義側 ---
      #mixin safety_base

      <:spec:
        - Prompt injection 防御
        - Guardrail (出力境界)
      /spec:>

      --- 使用側 ---
      <:mixin: safety_base :>
    /output:>
  /example:>

  <:example:
    <:input: 継承と外部取込 :>
    <:output:
      <:extends: base_analyst :>
      <:include: ./shared/formatting.typos :>
    /output:>
  /example:>

  <:example:
    <:input: activation — 発動条件メタデータ :>
    <:output:
      <:activation:
        - trigger: CCL match
          pattern: "/\\w+"
      :>
    /output:>
  /example:>
/case:>
```

### §11. 構造化ディレクティブ詳細構文

```typos
<:case:
  <:example:
    <:input: context — ContextItem 構造 (2形式、混在可) :>
    <:output:
      <:context:
        - [file] src/api/user.py (priority: HIGH)
        - [knowledge] API設計原則: RESTful, versioned
        - file: nous/workflows/ccl/ccl-plan.md
          priority: CRITICAL
        - mcp: gnosis.tool("search")
      /context:>
    /output:>
  /example:>

  <:example:
    <:input: scope — 3区間構造 :>
    <:output:
      <:scope:
        発動条件:
        - WF 実行前に view_file で確認

        非発動条件:
        - 直前5ターン内の自作ファイル

        グレーゾーン:
        - 10ターン前 :: 発動 :: コンテキスト減衰
      /scope:>
    /output:>
  /example:>

  <:example:
    <:input: case — 具体例 :>
    <:output:
      <:case:
        <:example:
          <:input: ユーザの質問 :>
          <:output: 期待される応答 :>
        :>
      /case:>
    /output:>
  /example:>

  <:example:
    <:input: schema — 評価ルーブリック :>
    <:output:
      <:schema:
        <:dimension:
          name: detection_accuracy
          description: バグ検出の正確性
          scale: 1-5
          <:criteria:
            5: 全ての隠れバグを検出、誤検出なし
            3: 主要なバグは検出、一部見落とし
            1: ほとんど検出できない
          /criteria:>
        /dimension:>
      /schema:>
    /output:>
  /example:>

  <:example:
    <:input: data — キー値 (ツール/リソース) :>
    <:output:
      <:data:
        - view_file: ファイル内容の直接読み取り
        - hermeneus_run: CCL 式の実行
      /data:>
    /output:>
  /example:>

  <:example:
    <:input: table — :: テーブル (v8.1) :>
    <:output:
      <:table:
        header :: col1 :: col2
        row1 :: val1 :: val2
      /table:>

      ← コンパイル時に Markdown テーブルに変換
      ← :: のまま LLM に渡しても暗黙2D座標系が発動 (コンパイル不要)
    /output:>
  /example:>
/case:>
```

### §12. :: テーブルの認知的根拠

```typos
<:detail:
  Zhang et al. (2026) arXiv:2602.08548 の発見
  LLM はデリミタを数えて内部で暗黙の2D座標系を再構築する (3段階パイプライン):

  Stage 1 Semantic Binding (初期層 1-16) :: クエリ制約とヘッダの意味的紐づけ
  Stage 2 Coordinate Localization (中間層 17-23) :: デリミタを数えて暗黙座標系を構築
  Stage 3 Information Extraction (後期層 24+) :: セル値を出力位置に伝播

  format-invariant: | / , / <td> / :: は全て同等に機能
  列インデックスは線形部分空間に符号化 → ベクトル演算で操作可能
/detail:>

<:table:
  デリミタ候補 :: tiktoken トークン数 :: 選定 :: 理由
  :: :: 1トークン (id=742) :: ✅ 採用 :: Typos の : 系構文と一貫
  | :: 1トークン (id=91) :: — :: MD テーブルは行頭/行末 | が必要で重い
  ¦ :: 2トークン :: ❌ :: C1 違反
  ⊣ :: 2トークン :: ❌ :: C1 違反
/table:>
```

### §13. エスケープ戦略

```typos
<:step:
  - 第1段 (コードブロック保護): ``` 内はパース対象外。コード内の <: :> は安全
  - 第2段 (名前付き閉じ優先): /name:> を使えば内部の :> はリテラル扱い
  - 第3段 (バックスラッシュ): \: でエスケープ (最終手段。実際にはほぼ不要)
/step:>
```

### §14. EBNF 文法 (v8.4)

```typos
<:schema:
  <:dimension:
    name: Typos v8.4 形式文法
    description: パーサー実装者向けの厳密な構文規則
    <:criteria:
      document :: { meta_line } , { blank_line } , { directive | text_line }
      meta_line :: "#prompt" ws name | "#mixin" ws name | "#" key ":" ws value
      directive :: inline_dir | block_dir | if_dir | flow_dir
      inline_dir :: "<:" dir_name ":" ws value ws ":>"
      block_dir :: "<:" dir_name ":" newline { content_line } ( ":>" | "/" dir_name ":>" )
      dir_name :: word_name | id_name
      id_name :: id_hyphen | id_bracket | id_hyphen_bracket
      id_hyphen :: UPPER "-" digit { alnum | "." }
      id_bracket :: UPPER "[" addr_chars "]"
      id_hyphen_bracket :: UPPER "-" "[" addr_chars "]"
      flow_dir :: "<:flow:" ws flow_expr ws ":>"
      flow_expr :: flow_stage { ">>" flow_stage }
      flow_stage :: group | parallel | node_ref
      group :: "[" node_ref { "," node_ref } "]"
      parallel :: node_ref { "*" node_ref }
      if_dir :: "<:if" ws condition ":" newline { directive | content_line } { elif_clause } [ else_clause ] "/if:>"
      elif_clause :: "<:elif" ws condition ":" newline { directive | content_line }
      else_clause :: "<:else:" newline { directive | content_line }
      condition :: variable ws cmp_op ws value
      cmp_op :: "==" | "!=" | ">" | "<" | ">=" | "<="
      code_block :: "```" [ language ] newline { any_line } "```"
    /criteria:>
  /dimension:>
/schema:>
```

```typos
<:detail:
  パース優先度
  1. コードブロック (```) — 内部はパース対象外
  2. 名前付きブロック (<: ... /name:>) — スタックベース、名前照合
  3. 無名ブロック (<: ... :>) — スタックベース、最内側優先
  4. インライン省略 (<: ... 行末) — 次の <: まで
  5. テキスト行 — 親ディレクティブの内容
/detail:>
```

---

## 第Ⅲ部: 実装アーキテクチャ

### §15. パイプライン

```typos
<:step:
  - v8_tokenizer.py (325行): 行ベースのスタック式パーサー → V8Document (AST)
  - v8_ast.py (121行): V8Node のツリー構造。メタ情報 + 検索・走査メソッド
  - v8_compiler.py (451行): AST → Prompt dataclass。V7 型別ディスパッチ + 深度フィルタ
  - typos.py (2,557行): v7/v8 統合 Core Parser。CLI + 24 記述行為 + L0-L3 深度制御
  - typos_mcp_server.py (1,205行): MCP Server。7 tools
/step:>
```

### §16. コンパイル出力

```typos
<:table:
  ターゲット :: 用途 :: 特徴
  typos (デフォルト) :: Typos-native 配信 :: <: :> 構文をそのまま LLM に渡す
  markdown :: システムプロンプト注入 :: Hóros 12法の user_rules はこの形式
  XML :: フォールバック :: Claude 向け従来形式
  plain :: デバッグ :: フラットテキスト
  auto :: モデル別自動選択 :: Claude→typos、OpenAI→markdown
/table:>
```

### §17. MCP ツール

```typos
<:data:
  - generate: 自然言語 → .typos/SKILL.md 生成 (ドメイン検出 + 収束/発散分類)
  - parse: .typos → JSON AST
  - validate: 構文検証 (role/goal 必須チェック、エラー箇所特定)
  - compile: .typos → システムプロンプト文字列 (ターゲット別変換)
  - expand: .typos → 人間可読な自然言語 (mixin/include/if 展開)
  - policy_check: タスクの収束/発散分類 (FEP Function 公理)
  - ping: ヘルスチェック
/data:>
```

---

## 第Ⅳ部: 品質保証

### §18. 生成ポリシー

```typos
<:spec:
  - <:role:> はタスク対象に特化すること (汎用的な「専門家」は不可)
  - <:spec:> はタスク固有制約を最優先、ドメイン制約は安全網
  - <:format:> は出力構造がタスクの期待に合致すること
  - <:case:> はタスク文脈に合った入出力例を含むこと
  - convergent タスクに推奨 / divergent タスクには不推奨 (自然言語を使う)
/spec:>

<:schema:
  <:dimension:
    name: 品質基準
    scale: 100点満点
    <:criteria:
      Structure :: 80点以上必須
      Safety :: 80点以上必須
      Completeness :: 70点以上必須
      Archetype Fit :: 70点以上必須
      Total :: 80/B 以上が合格
    /criteria:>
  /dimension:>
/schema:>
```

### §19. アンチパターン

```typos
<:policy:
  禁止語リスト
  「適切に」→「〇〇の場合は△△する」
  「うまく」→ 具体的な成功基準を明示
  「いい感じ」→ 禁止。要件明確化を要求
  「必要に応じて」→ トリガー条件を明示
  「などなど」→ 項目を列挙
  「できるだけ」→「優先度 N、制約の範囲内で最大化」
/policy:>

<:case:
  <:example:
    <:input: Anti-Pattern: 曖昧なフォーマット指定 :>
    <:output:
      ❌ <:format: JSON形式で出力 :>

      ✅
      <:format:
            ```json
            {
              "severity": "critical | high | medium | low",
              "location": "file:line",
              "fix": "string"
            }
            ```
      /format:>
    /output:>
  /example:>

  <:example:
    <:input: Anti-Pattern: 未定義ディレクティブ :>
    <:output:
      ❌ <:objective: ... :>   ← 存在しない
      ❌ <:rules: ... :>       ← spec の誤記

      ✅ <:spec: ... :>
      ✅ <:goal: ... :>
    /output:>
  /example:>
/case:>
```

### §20. 捏造防止 (Anti-Hallucination)

```typos
<:spec:
  以下は XML 等との混同による誤った構文。生成時に使用禁止。

  ❌ <:name> / </:> / <name:> / />  — 開始/閉じの形式違反
  ❌ <:name attr="val":          — 属性構文は不採用
  ❌ <:name: val /:>             — Self-close は不採用 (インライン形式を用いる)
  ❌ M:{} 構文                   — v8 で廃止
  ❌ .typ / .tps 拡張子           — 正しくは .typos
/spec:>
```

---

## 第Ⅴ部: 理論的基盤

### §21. 添え字圏の同型

```typos
<:detail:
  J_TYPOS ≅ J_HGK — 相対的構成距離による添え字圏の形の同型
  d_rel :: HGK (FEP 由来) :: TYPOS (A0 由来)
  0 (生成子) :: Flow (I⊣A) :: Endpoint (source↔target)
  1 (内部パラメータ) :: Value / Function / Precision :: Reason / Resolution / Salience
  ≥1 (ドメイン拡張) :: Temporality / Scale / Valence :: Context / Order / Modality

  J_HGK ≅ J_TYPOS ならば PSh(J_HGK) ≅ PSh(J_TYPOS) (Morita 同値)
  含意: HGK の認知体系と TYPOS の記述体系は、同じ前層圏の異なる実現
/detail:>
```

### §22. U/N 自己診断 — 意図的忘却

```typos
<:table:
  U パターン :: 忘却するもの :: 意図的か :: v8 での緩和
  U_temporal :: 時間軸 (静的スナップショット) :: ✅ 意図的 :: なし (構造的限界)
  U_sensory :: 視覚・空間構造 :: ⚠️ 半意図的 :: :: テーブルで部分緩和
  U_interactive :: 読み手との動的相互作用 :: ⚠️ 半意図的 :: <: 境界マーカーで部分改善
  U_embodied :: 身体的・感覚運動的文脈 :: ✅ 意図的 :: なし (テキストの本質的制約)
  U_causal :: 因果構造 :: ◯ :: 識別子 + <:flow:> で DAG 表現可能
/table:>

<:table:
  N パターン :: 回復するもの :: v8 ディレクティブ :: 充足度
  N_context :: 文脈 :: <:role:> / <:goal:> :: ◎
  N_precision :: 精度制約 :: <:spec:> :: ◎
  N_compose :: 操作の合成 :: <:step:> / <:flow:> :: ◎
  N_depth :: 深さ・アナロジー :: <:case:> / <:context:> :: ◯
  N_adjoint :: 双対視点 :: <:schema:> :: ◯
  N_self :: 自己言及 :: この文書自体が証拠 :: ◎
  N_causal :: 因果構造 :: <:if:> / <:flow:> / 識別子 :: ◯
/table:>
```

---

## 第Ⅵ部: 完全な例

```typos
<:case:
  <:example:
    <:input: バグ検出プロンプト — hidden_bug_detector.typos :>
    <:output:
      #prompt hidden_bug_detector
      #syntax: v8
      #depth: L2

      <:role: シニアコードアナリスト（バグハンター専門） :>

      <:goal: コードレビューで見落としがちな隠れバグを検出し、修正提案を出す :>

      <:spec:
        - 実行時に問題を引き起こすバグに集中
        - 各指摘には「発生条件」「影響度」「修正案」を含める
        - CWE 番号を付与可能な場合は付与
      /spec:>

      <:schema:
        <:dimension:
          name: detection_accuracy
          description: バグ検出の正確性
          scale: 1-5
          <:criteria:
            5: 全ての隠れバグを検出、誤検出なし
            3: 主要なバグは検出、一部見落とし
            1: ほとんど検出できない
          /criteria:>
        /dimension:>
      /schema:>

      <:format:
        ```json
        {
          "severity": "critical | high | medium | low",
          "category": "string",
          "location": "file:line",
          "trigger_condition": "string",
          "fix": "string",
          "cwe": "CWE-XXX (optional)"
        }
        ```
      /format:>

      <:if env == "prod":
        <:spec:
          - 誤検出を最小化、後方互換性を維持
        :>
      <:else:
        <:spec:
          - 疑わしきは報告（false positive 許容）
        :>
      /if:>

      <:case:
        <:example:
          <:input:
            def get_user(user_id):
                return db.query(f"SELECT * FROM users WHERE id = {user_id}")
          /input:>
          <:output:
            {"severity": "critical", "category": "injection", "cwe": "CWE-89"}
          /output:>
        /example:>
      /case:>
    /output:>
  /example:>
/case:>
```

---

## 参照ドキュメント

```typos
<:context:
  - [file] 10_知性｜Nous/03_知識｜Epistēmē/A_文書｜Docs/v8_syntax_reference.md (priority: CANONICAL — 構文正本)
  - [file] 10_知性｜Nous/02_手順｜Procedures/B_WFモジュール｜WFModules/06_技術｜Tek/rfc_typos-v8-syntax.md (priority: HIGH — 設計判断ログ)
  - [file] 10_知性｜Nous/03_知識｜Epistēmē/typos_hyphe_map.md (priority: HIGH — Hyphē 随伴理論)
  - [file] 10_知性｜Nous/03_知識｜Epistēmē/A_文書｜Docs/typos-table-adjoint-design.md (priority: HIGH — :: テーブル設計)
  - [file] 30_記憶｜Mneme/01_記録｜Records/c_ROM｜rom/rom_2026-03-17_typos_basis_universality.md (priority: MEDIUM — J同型・U/N診断)
  - [file] 30_記憶｜Mneme/01_記録｜Records/d_成果物｜artifacts/typos_v6_4basis_model.md (priority: MEDIUM — 4基底モデル)
  - [file] 10_知性｜Nous/02_手順｜Procedures/C_技能｜Skills/29_型定義｜Typos/typos-policy.md (priority: HIGH — 生成ポリシー)
  - [file] 20_機構｜Mekhane/_src｜ソースコード/mekhane/ergasterion/tekhne/references/typos-checklist.md (priority: MEDIUM)
  - [file] 20_機構｜Mekhane/_src｜ソースコード/mekhane/ergasterion/tekhne/references/typos-anti-patterns.md (priority: MEDIUM)
  - [file] 60_実験｜Peira/08_関手忠実性｜FunctorFaithfulness/TYPOS_BENCHMARK.md (priority: MEDIUM — E1-E4 実験設計)
/context:>
```

---

*Týpos v8.4 公式リファレンス — 2026-04-04*
*「人間も LLM も直接読み書きする普遍言語」*
