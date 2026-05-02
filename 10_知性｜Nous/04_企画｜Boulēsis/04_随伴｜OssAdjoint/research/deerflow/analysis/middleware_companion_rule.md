# Middleware 型 OSS を Companion Project として吸収する規則

> 例: `token-optimizer-mcp`
> 目的: middleware 型の外部 OSS を、HGK の core backend ではなく companion project として随伴吸収する際の一般則を定義する。

---

## 0. なぜ companion project なのか

middleware 型 OSS は、ふつう「思考そのもの」ではなく「思考の周辺配線」を変える。

具体例:

- hook
- cache
- compression
- memory injection
- sandbox
- session tracking

こうしたものを core backend としてそのまま入れると、
HGK の座標系より先に、外部配線の作法が支配権を取る。

したがって、まずは companion project として受け、
どの部分が HGK の血肉になり、どの部分が単なる外殻かを分離しなければならない。

---

## 1. 吸収前に分解する軸

middleware 型 OSS を読むときは、最低でも次の 6 軸に分解する。

| 軸 | 問い |
|:---|:---|
| Hook 軸 | どの時点で介入するか |
| State 軸 | 何を記録し、何を次へ渡すか |
| Safety 軸 | どのガードを持つか |
| Reversibility 軸 | 元へ戻せるか |
| Ownership 軸 | 設定主導権を誰が握るか |
| Surface 軸 | ユーザーに何が見えるか |

この分解なしに「便利だから入れる」は禁止する。

---

## 2. companion project 判定

次の条件を満たすものは companion project 候補である。

1. 外部 OSS が独自の hook / lifecycle を持つ
2. そのまま入れると HGK 既存の hook や gate と衝突する
3. 機能の一部だけは強く有用である
4. core backend ではなく middleware / orchestration / memory 周辺で価値を持つ

`token-optimizer-mcp` はこの 4 条件を満たす。

理由:

- Claude Code hook 群を自前で握る
- installer が設定主導権を取りに行く
- 可逆圧縮や session metrics は有用
- 価値の中心は thinking ではなく middleware である

---

## 3. companion project にした後の処理

吸収手順は 4 段でよい。

### 1. 外殻の棄却

まず installer、hook takeover、global settings 改変を捨てる。

ここは機能ではなく運用主導権の層である。
HGK 側がすでに同じ層を持っているなら、重ねるのではなく棄却する。

### 2. 可逆核の抽出

次に、元 OSS のうち可逆な核だけを抽出する。

`token-optimizer-mcp` なら:

- `optimize_text`
- `get_cached`
- token metrics

### 3. 近似層の降格

可逆でないが有用なものは、core へ昇格させず補助層に降格する。

`token-optimizer-mcp` なら:

- `smart_read`
- `smart_grep`
- `smart_glob`

これらは convenience layer であって、truth layer ではない。

### 4. HGK 語彙への再命名

最後に、外部名称ではなく HGK の言葉へ写す。

例:

| 外部名 | HGK 側の読み替え |
|:---|:---|
| optimize_text | Forget |
| get_cached | Recall |
| session stats | Token Budget Metrics |
| smart_read | Approximate Observation Layer |

---

## 4. DeerFlow 随伴との関係

DeerFlow 随伴が教えることは、
実装を技術ごと食べるなら、まず middleware の hook point を棚卸しせよ、ということである。

`token-optimizer-mcp` でも同じである。

読むべき順序:

1. lifecycle
2. safety
3. state persistence
4. restore / undo
5. UI or dashboard

この順序を飛ばして tool list だけ眺めると、構造を取り逃がす。

---

## 5. token-optimizer-mcp を例にした判定

### companion に残すもの

- 可逆 cache
- token counting
- session analytics
- chunk / restore の政策面

### HGK core に直接入れないもの

- installer
- global hook takeover
- transparent `Read -> smart_read` 置換
- AI tool 全面 auto-config

### 補助ヒューリスティクスとして保留するもの

- diff-only read
- prompt compaction 補助
- predictive cache

---

## 6. companion project の成果物

middleware 型 OSS を companion project にするとき、
最低限の成果物は 3 つでよい。

| 成果物 | 役割 |
|:---|:---|
| Absorption Memo | 何を採り、何を捨てるか |
| Mapping Table | 外部機能を HGK のどこへ写すか |
| Rejection Ledger | 捨てたものと棄却理由 |

この 3 つがない companion project は、単なる欲張り箱になる。

---

## 7. 当面の結論

middleware 型 OSS の評価軸は「高機能か」ではない。
「HGK の主導権を壊さず、可逆核だけを抽出できるか」である。

その意味で `token-optimizer-mcp` は、
core backend ではなく companion project としてなら良い素材である。

正しい吸収順序は次である。

1. 外殻を捨てる
2. 可逆核を抜く
3. 近似層を降格する
4. HGK 語彙へ再命名する

これが middleware 型 OSS 一般に対する companion rule である。
