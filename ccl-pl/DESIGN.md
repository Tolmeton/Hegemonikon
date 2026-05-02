# CCL-PL Design Document

> Version: 0.2.0-draft
> Date: 2026-03-31
> Status: 設計検討中

---

## 1. 哲学: 骨格と肉付け

### 核心命題

> **処理の骨組み（構造）はどのようなドメインでも共通である。**
> CCL-PL は普遍的な処理の構造を扱う。
> ドメインごとの肉付けは、拡張機能で対応する。

### 圏論的定式化

CCL-PL = **CCC + Adjunction + Fix** の内部言語

Curry-Howard-Lambek 対応により:
- **対象** = 型 (データの種類)
- **射** = 関数 (処理の骨格)
- **射の合成** = `_` (パイプライン)
- **指数対象** = ラムダ / `fn` (高階関数)

これに CCL-PL 固有の構造を追加:
- **随伴対** = `adjoint f <=> g` (可逆操作のペア宣言)
- **不動点** = `~*` (収束振動 = Fix(G∘F))
- **自然変換** = `~` (構造を保った変換)

### 「関数」の再定義

CCL-PL における「関数」は Python や Haskell の関数より広い概念:

```
関数 = 射 = 入力から出力への構造化された変換
```

認知動詞 (/noe, /bou...) は関数のインスタンス。
Web操作 (fetch, click...) も関数のインスタンス。
データ変換 (parse, validate...) も関数のインスタンス。

**CCL が制約するのは「構造」だけ。** 構造とは:
- 合成できる (f _ g = g ∘ f)
- 随伴を持てる (adjoint f <=> g)
- 振動できる (f ~* g → 不動点)
- 並列できる (f || g)
- 深度を持てる (f+, f-, f)

---

## 2. アーキテクチャ: 3層モデル

```
┌─────────────────────────────────────────────┐
│ Layer 2: Community Extensions               │
│   ccl-ext-ml, ccl-ext-db, ccl-ext-{任意}    │
├─────────────────────────────────────────────┤
│ Layer 1: Standard Extensions                │
│   ccl-ext-hgk    — 認知動詞 24 + 12随伴対   │
│   ccl-ext-data   — JSON/CSV/XML 変換        │
│   ccl-ext-web    — Web/DOM 操作             │
│   ccl-ext-fs     — ファイルシステム          │
├─────────────────────────────────────────────┤
│ Layer 0: CCL-PL Core (骨格)                 │
│   演算子 + 関数定義 + 制御構造 + Prelude     │
└─────────────────────────────────────────────┘
```

### Layer 0: Core (骨格)

言語が提供する構造的構成要素。ドメイン非依存。

#### 演算子体系

| Tier | 演算子 | 名前 | 圏論的意味 | 直感 |
|:-----|:-------|:-----|:-----------|:-----|
| **単項** | `+` | Deepen | 深度 L3 | 詳しく |
| | `-` | Condense | 深度 L1 | 手短に |
| | `^` | Ascend | メタ化 | 一段上から |
| | `?` | Query | 質問 | 問いかけ |
| | `\` | Dual | 余単位 (ε) | 反対側 |
| **二項** | `_` | Sequence | 射の合成 | パイプライン |
| | `*` | Fusion | Catamorphism (fold) | 融合 |
| | `%` | Outer | Anamorphism (unfold) | 展開 |
| | `~` | Oscillation | 自然変換 | 行き来 |
| | `~*` | Converge | 不動点 Fix(G∘F) | 安定するまで |
| | `>>` | Forward | 収束/Converge | 前進 |
| | `<<` | Reverse | Pullback | 巻き戻し |
| **制御** | `\|\|` | Parallel | 並列 | 同時に |
| **随伴** | `adjoint` | Adjunction | F ⊣ G 宣言 | ペアの操作 |

#### 関数定義

```ccl
// 名前付き関数
fn name(args) { body }

// ラムダ (匿名関数)
L:[args]{ body }

// 随伴対宣言
adjoint compress <=> decompress
```

#### 制御構造

```ccl
// 条件分岐
if condition { then_branch } else { else_branch }

// パターンマッチ (v0.2 予定)
match value {
    pattern1 => result1
    pattern2 => result2
    _ => default
}

// let 束縛
let x = expression
```

#### Prelude (組込み関数)

IO: `print`, `input`, `read_file`, `write_file`
Math: `add`, `sub`, `mul`, `div`, `sqrt`, `sin`, `cos`, `log`, `exp`
Data: `len`, `head`, `tail`, `append`, `map`, `filter`, `reduce`, `sort`
JSON: `json_parse`, `json_dump`
Type: `int`, `float`, `str`, `list`

### Layer 1/2: Extensions (肉付け)

#### 設計決定: H1+H2+H4 合成 + 多言語対応

/ske struct (2026-03-31) で 5 仮説を展開し、以下の合成を選択:
- **H1** (Python bridge) — 今すぐ動く基盤
- **H2** (CCL-PL 自己記述) — `.ccl` で拡張を宣言
- **H4** (Protocol) — 随伴対の実装を構造的に強制

**Creator の洞察**: `.ccl` への変換ができるなら、どの言語でも対応できる。

#### .ccl = Extension の Universal Interface

拡張の **宣言** は `.ccl` ファイルで行う。これが Universal Interface:

```ccl
// === ccl-ext-hgk/telos.ccl ===
extension hgk.telos {
    fn recognize(input)
    fn intend(insight)
    fn explore(data)
    fn execute_plan(goal)

    adjoint recognize <=> explore
    adjoint intend <=> execute_plan
}
```

**実装 (肉) の提供方法 = 3パス:**

```ccl
// Pass A: CCL-PL inline (自己記述 — H2)
extension hgk.telos {
    fn recognize(input) {
        let patterns = map(input, L:[x]{ classify(x) })
        reduce(patterns, L:[a,b]{ merge(a,b) })
    }
}

// Pass B: Python bridge (エコシステム活用 — H1)
extension hgk.telos {
    fn recognize(input) -> python("hgk_telos.recognize")
    fn intend(insight)  -> python("hgk_telos.intend")
}

// Pass C: Any language via FFI (多言語対応)
extension web.browser {
    fn fetch(url)    -> ffi("rust", "ccl_web::fetch")
    fn click(ref_id) -> ffi("node", "ccl-web/click")
}
```

どの言語で書かれていても、`.ccl` に変換できれば Extension。

#### Protocol: 構造を強制する (H4)

```ccl
// Protocol 定義 (Core が提供)
protocol Reversible {
    fn forward(input) -> output
    fn reverse(output) -> input
    adjoint forward <=> reverse  // 随伴の実装を強制
}

// 拡張が Protocol を満たす
extension data.codec : Reversible {
    fn forward(input) { json_dump(input) }
    fn reverse(output) { json_parse(output) }
    // adjoint は Reversible から自動登録
    // → Optimizer が json_parse(json_dump(x)) → x を相殺
}
```

Protocol が随伴対を強制: `forward` を定義したら `reverse` も要求される。

#### 多言語 Bridge 対応表

| 言語 | bridge 構文 | 方式 | v0.2 対応 |
|:-----|:-----------|:-----|:---------|
| **Python** | `-> python("mod.func")` | exec() 内 import | ✅ |
| **CCL-PL** | inline `{ body }` | パーサー直接処理 | ✅ |
| **JavaScript/TS** | `-> ffi("node", "pkg/func")` | subprocess + JSON | v0.3 |
| **Rust** | `-> ffi("rust", "crate::func")` | PyO3 or subprocess | v0.3 |
| **Go** | `-> ffi("go", "pkg.Func")` | subprocess + JSON | v0.3 |

#### Extension ロード順序

```
1. use hgk.telos
2. Executor が "hgk/telos" を検索:
   a. CCL_EXT_PATH → ~/.ccl/extensions/ → ./ccl-ext-*/ → pip entry point roots
   b. hgk/telos.ccl を発見 → パース
   c. extension ブロックの各 fn を処理:
      - inline body → CCL-PL で実行
      - python("importable.mod.fn") → Python import してバインド
      - python("ccl-ext-foo.core.fn") → extension root 配下の Python ファイルを解決
      - ffi("...") → 外部プロセス呼出し
   d. adjoint 宣言 → Optimizer に随伴対を登録
3. 呼出し側の名前空間に関数が登録
```

pip package は `ccl.extensions.v1` entry point で extension root を公開する。root 配下には
`ccl-ext-foo/bar.ccl` と必要なら `ccl-ext-foo/bar.py` を置く。

#### 現状の HGK Stdlib → ccl-ext-hgk への移行

現在 `ccl/stdlib/hgk/` にある 24 動詞 + 12 随伴対は、
Extension 機構が実装され次第 `ccl-ext-hgk/` に分離する。

```
ccl/stdlib/hgk/telos.py     → ccl-ext-hgk/telos.ccl + telos.py (bridge)
ccl/stdlib/hgk/methodos.py  → ccl-ext-hgk/methodos.ccl + methodos.py
ccl/stdlib/hgk/krisis.py    → ccl-ext-hgk/krisis.ccl + krisis.py
ccl/stdlib/hgk/diastasis.py → ccl-ext-hgk/diastasis.ccl + diastasis.py
ccl/stdlib/hgk/orexis.py    → ccl-ext-hgk/orexis.ccl + orexis.py
ccl/stdlib/hgk/chronos.py   → ccl-ext-hgk/chronos.ccl + chronos.py
```

各 `.ccl` が宣言 (骨格)、各 `.py` が実装 (肉)。
将来的に `.py` を `.ccl` inline に置き換えることも可能。

---

## 3. 実行モデル

### 現在: Python トランスパイル

```
CCL Source (.ccl)
    ↓ Parser
CCL AST (categorical nodes)
    ↓ Optimizer (adjunction folding)
Optimized AST
    ↓ Transpiler
Python Source
    ↓ exec()
Result
```

### 将来の選択肢 (Q-003: 2026-04-12 方針確定)

| 選択肢 | 利点 | 欠点 |
|:-------|:-----|:-----|
| Python トランスパイル維持 | エコシステム活用、開発コスト最小 | 性能上限、Python 依存 |
| 独自バイトコード VM | 性能制御、言語固有最適化 | 開発コスト大、エコシステム断絶 |
| WASM コンパイル | ブラウザ実行可能、ポータブル | 開発コスト大 |

**現時点の判断: Python トランスパイル維持。** 骨格の設計を固めることが先決。
v0.x / v1.0 の正本 backend は Python とし、VM / WASM は `AST・Optimizer・Extension ABI が固まり、かつ Python が実測ボトルネックになった時だけ` 再検討する。
詳細は `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/ccl-pl/ARCHITECTURE_DECISIONS.md` を参照。

---

## 4. 型システム (Q-002: 2026-04-12 方針確定)

### 候補

| 方式 | 概要 | CCL-PL との相性 |
|:-----|:-----|:---------------|
| **動的型付け (現状)** | Python 的。実行時に型チェック | 開発速度◎、安全性△ |
| **漸進的型付け** | 型注釈は任意。書けば静的チェック | バランス◎、実装コスト中 |
| **構造的型付け** | 型は構造 (射の入出力) で決まる | 圏論的に自然◎、実装コスト大 |

**採用方針: 動的実行を基底にした optional な漸進的型付け。**
初期段階では HGK の定理型と output schema に基づく警告・LSP 診断・`check` を積み、構造的型付けは Extension / Protocol 層に段階導入する。
詳細は `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/ccl-pl/ARCHITECTURE_DECISIONS.md` を参照。

### 圏論的型の展望

随伴対が言語レベルにあることで、型システムに圏論的保証を組み込める:

```ccl
// 随伴対を宣言すると、コンパイラが以下を保証:
adjoint compress <=> decompress

// 型の保証: decompress(compress(x)) : T → T (恒等射と同型)
// 最適化: decompress(compress(x)) → x (adjunction folding)
```

---

## 5. LSP / IDE 統合

### ロードマップ

| Phase | 内容 | 得られる体験 | 状態 |
|:------|:-----|:-------------|:-----|
| P0 | TextMate 文法 + VS Code 拡張 | `.ccl` にシンタックスハイライト | 未着手 |
| P1 | 基本 LSP (pygls) | エラーの赤線表示 | 未着手 |
| P2 | 補完 + ホバー | 動詞/関数の候補、説明表示 | 未着手 |
| P3 | Go-to-def + symbols | 関数定義へのジャンプ | 未着手 |
| P4 | 随伴対可視化 | 右随伴の自動提示、最適化ヒント | 未着手 |
| P5 | DAP (デバッグ) | ステップ実行 | 未着手 |

### CCL-PL 固有の IDE 体験

1. **随伴対の自動補完**: `adjoint` 宣言後、対になる関数を自動提示
2. **認知動詞のコンテキスト補完**: `/noe` と打つと深度 (+/-) 含め候補表示
3. **パイプライン可視化**: `a _ b _ c` の各段階に型/説明を inline 表示
4. **最適化ヒント**: `G(F(x))` パターンを検出し「相殺可能」と通知

### 前提条件: パーサーのエラー回復

LSP が動くには、**不完全なコードからも AST を返せる**パーサーが必要。
現在のパーサーはエラー時に例外を投げて停止する。
エラー回復 (error recovery) の実装が LSP の命綱。

戦略:
- 同期ポイント (`;`, `}`, `\n\n`) でリカバリ
- エラーノード (`ErrorNode`) を AST に含めて返却
- 正常な部分は正常に解析、壊れた部分はエラーとしてマーク

---

## 6. ディレクトリ構造 (目標)

```
ccl-pl/
├── pyproject.toml
├── README.md
├── DESIGN.md              ← この文書
├── examples/
│   ├── hello.ccl
│   ├── demo_operators.ccl
│   ├── test_pipeline.ccl
│   └── (追加予定)
├── tests/
│   └── test_ccl.py        # 32 tests (現状)
├── ccl/                   # Layer 0: Core
│   ├── __init__.py
│   ├── cli.py
│   ├── repl.py
│   ├── executor.py
│   ├── transpiler.py
│   ├── optimizer.py
│   ├── errors.py
│   ├── prelude.py
│   ├── extension.py       # (新規) Extension ローダー
│   ├── parser/
│   │   ├── core.py
│   │   └── ast.py
│   ├── runtime/
│   │   └── core.py
│   └── stdlib/             # → 将来 ccl-ext-hgk に分離
│       └── hgk/
├── ccl-lsp/               # (新規) LSP サーバー
│   ├── server.py          # pygls ベース
│   ├── diagnostics.py
│   ├── completion.py
│   ├── hover.py
│   └── symbols.py
└── ccl-vscode/            # (新規) VS Code/Cursor 拡張
    ├── package.json
    ├── syntaxes/
    │   └── ccl.tmLanguage.json
    └── language-configuration.json
```

---

## 7. 先行研究との位置づけ

| 言語/研究 | アプローチ | CCL-PL との差異 |
|:---------|:----------|:---------------|
| **Haskell** | 型クラスで圏論パターンを表現 | CCL-PL: 随伴を言語レベルで宣言 |
| **Charity** (1992) | 初代数/終余代数ベース | CCL-PL: 実用的 + 拡張機構 |
| **CPL** (arXiv:2010.05167) | F,G-dialgebra | CCL-PL: 骨格/肉付け分離 + Extension/Protocol 契約へ翻訳 |
| **Idris/Agda** | 依存型で証明 | CCL-PL: 随伴 + 不動点が一級 |
| **Catala** | 法律ドメイン特化 | CCL-PL: ドメイン非依存 + 拡張 |

CCL-PL の独自性:
1. **随伴対が言語プリミティブ** — 他の言語にはない
2. **骨格/肉付けの分離** — Extension as Functor
3. **深度修飾子** (+/-) — 同じ操作の粒度制御が言語レベル

---

## 8. 開発ロードマップ

| Version | マイルストーン | 主要変更 |
|:--------|:-------------|:---------|
| **v0.1.0** (現在) | PoC 動作 | Parser + Transpiler + Executor + 32 tests |
| **v0.2.0** | Extension 機構 | `use` 文、Extension ローダー、HGK 分離 |
| **v0.3.0** | パーサー強化 | エラー回復、パターンマッチ、改善された型推論 |
| **v0.4.0** | LSP P0-P1 | TextMate 文法、基本 diagnostics |
| **v0.5.0** | LSP P2-P3 | 補完、ホバー、Go-to-def |
| **v0.6.0** | 型システム | 漸進的型付け (optional) |
| **v1.0.0** | Cursor でガチ利用可能 | LSP P4 (随伴可視化) + 安定した Extension 機構 |

---

## 9. 現在の制約

Q-002 / Q-003 / Q-004 は 2026-04-12 に `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/ccl-pl/ARCHITECTURE_DECISIONS.md` で方針確定。

2026-04-13 に Extension 間の随伴合成も方針確定。
現在は「未解決の問い」ではなく、**現在の制約** を管理する段階に入っている。

1. Extension 間の随伴合成は、明示登録された unary 関数列の round-trip folding のみ対応
2. 副作用つき関数、multi-arg 関数、暗黙の自然同型は optimizer が自動縮約しない
3. 関数名は unqualified import 前提なので、extension 間の同名衝突は運用で避ける必要がある
