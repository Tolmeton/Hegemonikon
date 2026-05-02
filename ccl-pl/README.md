# CCL-PL

**圏論的構造を持つ汎用プログラミング言語**

CCL-PL (Cognitive Control Language - Programming Language) は、演算子に圏論的意味論が直接埋め込まれたプログラミング言語です。随伴関手・自然変換・不動点計算が言語の第一級構成要素として機能します。

## 特徴

- **随伴が first-class**: `adjoint compress <=> decompress` で随伴対を宣言。コンパイラが `G(F(x)) → x` を自動相殺
- **振動が first-class**: `analyze ~* synthesize` で不動点計算 Fix(G∘F) が言語レベル
- **モジュールシステム**: `use hgk.telos` で認知動詞を汎用関数としてインポート
- **圏論的 AST 最適化**: Parse → **Optimize** → Transpile → Exec — 随伴の Folding がコンパイル時に発生
- **Python エコシステム互換**: Python へのトランスパイル実行。既存ライブラリがそのまま使える

## クイックスタート

```bash
# REPL を起動
python -m ccl

# ファイルを実行
python -m ccl run examples/hello.ccl

# CCL 式を Python に変換
python -m ccl transpile "/noe+_/dia"

# AST をダンプ
python -m ccl parse "/ske~*/sag"
```

## 言語構文

### 関数定義と呼出

```
fn greet(name) { "Hello, " + name + "!" }
fn double(x) { x * 2 }

print(greet("CCL-PL"))    # Hello, CCL-PL!
print(double(21))          # 42
```

### モジュールシステム

```
use hgk.telos

# 認知動詞を汎用関数名で使用
insight = recognize("problem statement")
goal = intend(insight)
result = execute_plan(goal)
```

### Extension 配布

`use foo.bar` は Python import ではなく、**CCL extension namespace** を引く。

- ローカル開発: `./ccl-ext-foo/bar.ccl`
- ユーザー領域: `~/.ccl/extensions/ccl-ext-foo/bar.ccl`
- pip 配布: `ccl.extensions.v1` entry point が返す root 配下の `ccl-ext-foo/bar.ccl`

pip package は次のように root を公開する:

```toml
[project.entry-points."ccl.extensions.v1"]
foo = "ccl_ext_foo:get_extension_root"
```

Python bridge は 2 形態を許す:

- import 可能モジュール: `python("ccl_ext_foo.core.ask")`
- extension root 配下のローカルファイル: `python("ccl-ext-foo.core.ask")`

後者は workspace / entry point root を基準に `ccl-ext-foo/core.py` を解決する。

### 随伴対の宣言

```
fn compress(data) { data[:len(data)//2] }
fn decompress(data) { data + data }

# コンパイラに随伴関係を教える
adjoint compress <=> decompress

# オプティマイザが G(F(x)) → x を自動相殺
# decompress(compress(x)) はコンパイル時に x に縮約される
```

### Lambda

```
let double = L:[x]{x * 2}
let add = L:[a,b]{a + b}

# Lambda body 内の算術演算子は自動的に Python として解釈
# * は CCL 融合ではなく乗算として扱われる
```

### CCL 演算子（圏論的操作）

```
# シーケンス (射の合成)
/noe+_/dia

# 融合 (Catamorphism)
/ske*/sag

# 収束振動 (不動点探索 Fix(G∘F))
/ske~*/sag

# パイプライン (Forward morphism)
/noe+>>/ele+>>/dio
```

## CCL 演算子一覧

| 演算子 | 名前 | 圏論 |
|:---|:---|:---|
| `_` | シーケンス | 射の合成 |
| `*` | 融合 | Catamorphism (fold) |
| `%` | 展開 | Anamorphism (unfold) |
| `~` | 振動 | 自然変換 (2操作の循環) |
| `~*` | 収束振動 | 不動点探索 Fix(G∘F) |
| `>>` | 順射 | Forward morphism |
| `<<` | 逆射 | Pullback |
| `\` | 双対 | Dual (counit ε) |

## hgk-stdlib: 認知動詞標準ライブラリ

6族 × 4関数 = 24関数 + 12随伴対。HGK 認知動詞を汎用関数名で提供。

| 族 | 関数 |
|:---|:---|
| Telos | `recognize`, `intend`, `explore`, `execute_plan` |
| Methodos | `diverge_strategy`, `converge_strategy`, `experiment`, `apply_technique` |
| Krisis | `commit`, `suspend`, `decide`, `probe` |
| Diástasis | `analyze_detail`, `overview`, `refine`, `orchestrate` |
| Orexis | `affirm`, `critique`, `advance`, `correct` |
| Chronos | `recall`, `forecast`, `reflect`, `prepare` |

```
use hgk

# 認識 → 批判 → 是正 のパイプライン
insight = recognize(data)
issues = critique(insight)
fix = correct(issues)
```

## アーキテクチャ

```
CCL Source (.ccl)
    │
    ▼
┌─────────┐
│  Parser  │  CCL → AST (圏論的ノード)
└────┬────┘
     │
     ▼
┌──────────────┐
│  Optimizer   │  随伴 Folding: G(F(x)) → x
└────┬─────────┘
     │
     ▼
┌──────────────┐
│  Transpiler  │  AST → Python ソースコード
└────┬─────────┘
     │
     ▼
┌──────────────┐
│  Executor    │  Python exec() で実行
└──────────────┘
```

## プロジェクト構造

```
ccl-pl/
├── pyproject.toml
├── README.md
├── examples/
│   ├── hello.ccl
│   └── demo_operators.ccl
├── tests/
│   └── test_ccl.py          # 32 テスト
└── ccl/
    ├── cli.py               # run/repl/parse/transpile/check/version
    ├── repl.py               # 対話的実行
    ├── executor.py           # 統合実行エンジン
    ├── transpiler.py         # AST → Python
    ├── optimizer.py          # 圏論的 AST 最適化
    ├── errors.py             # エラー報告
    ├── prelude.py            # 組込み関数
    ├── parser/               # CCLパーサー + AST
    ├── runtime/              # 圏論的ランタイム
    └── stdlib/hgk/           # 認知動詞標準ライブラリ
```

## 要件

- Python 3.11+

## ライセンス

MIT
