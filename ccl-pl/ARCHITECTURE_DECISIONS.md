# CCL-PL Architecture Decisions

## ADR-0001: v0.x のコア方針 (2026-04-12)

### Kernel

CCL-PL は **圏論的構造を第一級に持つ汎用プログラミング言語** を目指す。v0.x では Python トランスパイルを bootstrap backend として使うが、言語意味論の正本は `.ccl` / AST / Extension ABI に置く。`python()` bridge は初期実装と相互運用のための optional FFI であり、標準ライブラリや主要 example が恒久的に Python bridge へ依存する形は採らない。CPL の F,G-dialgebra は VM や表面構文として直輸入せず、Extension/Protocol 層で「データ型と随伴の契約」を表す参照理論として使う。

### Decision Surface

| Question | Decision | 理由 |
|:---------|:---------|:-----|
| Q-002 型システム | **動的実行 + 漸進的型付け** を採用 | 現在の Executor は Python `exec()` と bridge を前提にしており、まず完全静的健全性を求めるより、既存の HGK 定理型・output schema・LSP 診断を接続する方が自然 |
| Q-003 実行モデル | **v0.x は Python bootstrap、v1.0 は bridge-free core を条件化** | AST / Optimizer / Extension を固める前に VM へ進むと実装コストが主戦場になるが、Python 依存を v1.0 正本にすると汎用 PL ではなく Python DSL に縮む |
| Q-004 CPL 継承 | **F,G-dialgebra は Extension 契約へ翻訳して継承** する | CPL の価値は「データ型を随伴から起こす視点」にあり、CCL-PL ではこれを runtime ではなく extension 境界の構造保証に使うのが合う |
| Q-005 Python bridge | **optional FFI に降格する前提で維持** | 初期の ecosystem 利用は必要だが、標準実装の依存核にすると `.ccl` が宣言だけになり、言語の自立性が失われる |

### Trace

1. `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/ccl-pl/ccl/executor.py` は Parse → Optimize → Transpile → `exec()` の Python 実行パイプラインを現在の bootstrap backend として持つ。
2. `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/ccl-pl/ccl/extension.py` は `.ccl` 宣言、`python()` bridge、将来の Protocol 強制という三層をすでに持つ。
3. `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/01_制約｜Constraints/E_CCL｜CCL/SPEC.md` には、CCL の構文凍結、出力スキーマ、定理型、field projection 検証の語彙が統合されている。
4. CCL-PL が汎用 PL を目指すなら、`.ccl` は宣言だけでなく最終的な実装正本にもならなければならない。
5. CPL 論文 abstract は、F,G-dialgebra を「adjunction を拡張したデータ型宣言機構」として位置づけている。したがって CCL-PL では VM よりも declaration / protocol 側へ寄せるのが整合的。

### Adopted Shape

#### 1. 型システム

- v0.x は **実行を止めない型システム** にする。
- 中核は HGK の定理型 (`O/S/H/P/K/A/X`) と output schema の静的警告。
- `fn` / `extension` / `WM` / field projection に対して、LSP と `check` コマンドで「注釈を書くほど早く壊れ方が見える」体験を作る。
- 構造的型付けは捨てないが、まずは **Extension Protocol の契約言語** として導入する。最初から全言語を構造型で縛らない。

#### 2. 実行モデル

- v0.x は Python トランスパイルを **bootstrap backend** として維持する。
- v1.0 の到達条件に、`python()` bridge なしで core / standard library / principal examples が動く **bridge-free baseline** を置く。
- Python bridge は optional FFI として残すが、標準実装の依存核にはしない。
- AST / Optimizer / Extension ABI は **backend 交換可能** に保つ。つまり「Python を本質」とはみなさない。
- VM / WASM は次の条件が揃った時だけ再検討する:
  - bridge-free baseline が成立し、Python bridge が依存核から外れた
  - Extension ABI が凍結され、backend の作り直しが language churn を招かない
  - Python backend の性能限界が実測で繰り返し確認された
  - deterministic sandboxing / portable target / ahead-of-time deployment が実要求になった

#### 3. CPL の継承方法

- CCL-PL は CPL の全面移植をしない。
- 継承するのは次の三点:
  - データ型を随伴から組み立てる見方
  - dual / lazy / recursive data family を対称的に捉える見方
  - 宣言が実行意味に先立つという考え方
- これを `extension` / `adjoint` / 将来の `protocol` へ落とし、constructor / destructor / dual / recursion law を記述できるようにする。
- 逆に、CCL-PL の runtime を CPL 風の停止性証明込み言語へ即座に置換することは採らない。

### Negativa

- **採らない案 1**: いま VM を作る。理由は、最適化・型・拡張境界が未凍結のまま下層を固定すると手戻りが大きいから。
- **採らない案 2**: Python bridge を恒久的な実装核にする。理由は、CCL-PL が Python DSL に縮み、汎用 PL としての自立性を失うから。
- **採らない案 3**: いま完全静的型を約束する。理由は、bootstrap backend と動的 extension を残す限り、約束だけが先に肥大化するから。
- **採らない案 4**: CPL の表面言語をそのまま持ち込む。理由は、CCL-PL の独自性は骨格/肉付け分離にあり、ここを失うと実用系の狙いがぼやけるから。

### Consequences

- Q-002 / Q-003 / Q-004 / Q-005 は個別の open question ではなく、**「CCL-PL は Python bootstrap で始めるが、`.ccl` を実装正本へ育て、bridge-free core + optional theorem typing + protocolized extensions で汎用 PL 化する」** という一つの設計判断に束ねられる。
- `DESIGN.md` の未決定表現はこの memo を正本として更新する。
- Pinakas では 4 問を `answered` に落としてよい。

### Sources

- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/ccl-pl/DESIGN.md`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/ccl-pl/ccl/executor.py`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/ccl-pl/ccl/extension.py`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/01_制約｜Constraints/E_CCL｜CCL/SPEC.md`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/c_ROM｜rom/rom_2026-03-31_ccl-pl-vision.md`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/c_ROM｜rom/rom_2026-04-04_ccl_pl_sprint.md`
- https://arxiv.org/abs/2010.05167

## ADR-0002: Module / Package System (2026-04-13)

### Kernel

`use foo.bar` は Python import 文ではなく、**CCL extension namespace の解決** とみなす。配布面は独自 package manager を作らず、ローカルディレクトリ・ユーザー拡張ディレクトリ・pip package entry point の三層で統一する。

### Decision Surface

| Question | Decision | 理由 |
|:---------|:---------|:-----|
| package manager を独自実装するか | **しない** | v0.x で必要なのは依存解決より extension root の発見であり、pip の流通路を捨てる理由がない |
| `use` の意味 | **Python module ではなく CCL namespace** | `foo.bar` を `ccl-ext-foo/bar.ccl` に写す方が骨格/肉付け分離と整合する |
| pip 連携方式 | **`ccl.extensions.v1` entry point で root を公開** | Python packaging と疎結合に統合でき、Extension ABI を崩さず配布できる |
| Python bridge の対象 | **importable module と extension-root file の両方を許す** | ローカル開発では `ccl-ext-foo/core.py` を直接叩ける方が軽く、pip 配布では通常 import も使える |

### Adopted Shape

#### Resolution Order

1. `CCL_EXT_PATH`
2. `~/.ccl/extensions`
3. workspace root (`./ccl-ext-*`)
4. pip package が `ccl.extensions.v1` で公開した root

#### Packaging Contract

- CCL namespace: `foo.bar`
- artifact path: `ccl-ext-foo/bar.ccl`
- optional Python bridge file: `ccl-ext-foo/bar.py`
- pip package は `get_extension_root() -> Path` のような provider を entry point に載せる

#### Negativa

- **採らない案 1**: npm/pip/独自 registry の三重管理。初期コストだけ高く、利用者が混乱する。
- **採らない案 2**: `use` をそのまま Python import にする。`.ccl` を universal interface とみなす方針が崩れる。
- **採らない案 3**: いま lockfile / semver solver を作る。依存解決は distribution phase の問題で、現段階では過剰。

### Consequences

- `DESIGN.md` の package management は open question ではなくなった。
- 実装上は `ExtensionLoader` が entry point root と local file bridge を解決する。
- 以後の拡張点は package manager ではなく import ergonomics / protocol integration 側へ移る。

## ADR-0004: Qualified Import / Collision Policy (2026-04-14)

### Kernel

`use foo.bar` は後方互換のため残すが、名前衝突を黙って上書きしない。正式な衝突回避手段は `use foo.bar as foo` と `foo.fn(...)` である。

### Decision Surface

| Question | Decision | 理由 |
|:---------|:---------|:-----|
| import surface | **bare import 維持 + alias import 追加** | 既存コードを壊さずに namespace 導入できる |
| qualified call | **alias 経由の `foo.fn(...)` のみ** | 一般的 property access 言語へ広げず、スコープ衝突問題だけを解く |
| collision policy | **hard error** | silent overwrite を止め、alias への移行を機械的に促せる |

### Adopted Shape

- `use foo.bar`
- `use foo.bar as foo`
- `foo.fn(...)`

bare import は export map を global scope に流し込む。
ただし既存 `_globals` / user-defined function / alias 名と衝突したら import 自体を失敗させる。

### Negativa

- **採らない案 1**: warning 付き上書き。衝突を見逃すので fail-fast にならない。
- **採らない案 2**: `use foo.bar` 自体を namespaced import に変更。後方互換を不必要に壊す。
- **採らない案 3**: named import (`use foo.bar { fn }`) まで同時に入れる。今回の問題に対して過剰。

### Consequences

- runtime / transpiler / REPL の import semantics を同一 helper に集約する
- existing bare import code は、衝突がない限りそのまま動く
- 衝突していたコードは alias import へ明示移行が必要になる

## ADR-0003: Inter-Extension Adjunction Composition (2026-04-13)

### Kernel

Extension 間の随伴対合成は、新しい composed symbol を宣言することではなく、Optimizer が `G1(G2(F2(F1(x))))` のような round-trip chain を内側から畳めることとして実装する。

### Decision Surface

| Question | Decision | 理由 |
|:---------|:---------|:-----|
| 合成随伴をどう表すか | **nested unary call chain の縮約として扱う** | 既存 AST / parser / executor を壊さず、圏論の `(F2∘F1) ⊣ (G1∘G2)` を operational に表現できる |
| 何を自動縮約するか | **明示登録された unary adjoint pair のみ** | 副作用や多引数関数まで広げると意味保存が壊れやすい |
| extension 境界をどう越えるか | **関数の出自ではなく登録 pair の列で判定** | Optimizer に必要なのは provenance ではなく round-trip の形だから |

### Adopted Shape

- まず内側の `G(F(x)) -> x` を縮約する
- その結果、外側も新たに `G(F(...))` になれば再帰的に縮約する
- これにより `F1 ⊣ G1`, `F2 ⊣ G2` が登録済みなら `G1(G2(F2(F1(x)))) -> x` が成立する

### Negativa

- **採らない案 1**: composed adjoint を別名で自動生成する。名前爆発と追跡不能を招く。
- **採らない案 2**: multi-arg 関数まで一括で縮約する。unit/counit の意味保存をコード側で証明できない。
- **採らない案 3**: extension provenance を optimizer の必須入力にする。現段階では実装コストが高く、得るものが少ない。

### Consequences

- `DESIGN.md` 上の最後の open question は解消。
- 現在の制約は「unary / explicit / side-effect-free assumption」に境界づけられる。
- 次に深掘るなら named import と protocol 由来の自動 pair 登録が自然な拡張になる。
