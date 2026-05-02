# Ergon プロジェクト 設計文書 01

## Isolate パターン（サブエージェント委譲）

本書は、Active States の旧定義を保持したまま、それを**Isolate パターン**として再定式化する。核命題は Paper X §4.3 に従う。

> **サブエージェント委譲とは、既存の MB の外にもう一つの MB を作ることである。**

ここで MB は Markov blanket を指す。委譲とは仕事の移送ではない。**局所的な忘却場を別系として増設する操作**である。

## 1. MB の外に MB を作るとは何か

親系と子系の関係は次のように表せる。

```text
親 HGK
  (μ_p, s_p, a_p)
      |
      | isolate = child boot
      v
子 blanket
  (μ_c, s_c, a_c)
      |
      | child bye
      v
親 HGK へ distilled result を返す
```

親系は自分の blanket を拡張するのではなく、**外部に局所閉包した子 blanket** を立ち上げる。これにより、

- 親の作業面は肥大化しない
- 子の探索は子の忘却場に閉じる
- 戻り値は raw transcript ではなく蒸留結果になる

という 3 つの効果が得られる。

## 2. Active States ($a_c$) の再定義

子 blanket における Active States ($a_c$) は、親から boot された制約のもとで局所環境へ作用する能動面である。

| 項目 | 旧定義 | Isolate 再解釈 |
|:---|:---|:---|
| 入力 | Internal States ($\mu$) | 親から蒸留された `C/E/M` 核 + 子の局所 context |
| 出力 | External States ($\eta$) への直接作用 | 子 blanket が許可された環境面への局所作用 |
| 制約 1 | $a$ は意図を持たない | 子系は親の Telos を再定義してはならない |
| 制約 2 | $a$ は決定論的であるべき | LLM 判断は $\mu_c$ に閉じ、副作用は Hook / tool へ落とす |
| 制約 3 | 実行後に $s$ を生成する | 子系は `s_c` と蒸留済み `R_{bye}` を返す |

重要なのは、**親が子に全部を渡さない**ことである。忘却論では、blanket が均一に厚いほどよいのではない。必要な制約だけを濃く通し、残りは意図的に忘れさせる必要がある。

## 3. Isolate のライフサイクル

### 3.1 child boot

親系は `L (boot)` を局所適用し、子系へ `C/E/M` の核だけを注入する。これは「文脈の複製」ではなく、**必要最小限の boot** である。

### 3.2 child execute

子系は自分の blanket の内部で探索・実行する。ここで発生する揺らぎや試行錯誤は、親の MB に直接混入してはならない。

### 3.3 child observe

子系は `s_c` としてログ、テスト結果、失敗信号を観測する。観測は raw のまま親へ返すのではなく、後段の蒸留対象として束ねる。

### 3.4 child bye

子系は `R (bye)` によって結果を蒸留し、親へは `summary / diff / next_action / evidence path` を返す。これにより親は**子系の全思考ではなく、再利用可能な belief kernel** だけを受け取る。

## 4. Offload との違い

- **Offload**: 状態を blanket の外へ逃がす。ROM、Handoff、外部ファイル。
- **Isolate**: blanket の外に新しい blanket を作る。サブエージェント、分離ワーカー。

両者は対立しない。典型的には、**Isolate で生成した子 blanket が最後に Offload として結果を返す**。

## 5. 防御的設計

Isolate は自由化ではない。MB を 1 つ増やすごとに、境界契約は厳しくしなければならない。

1. **Capability Budget**
   - 子系に許す `tool / path / write scope` を先に固定する
   - これは `C` 軸を子系へ注入する操作である
2. **Deterministic Boundary**
   - 設計判断は $\mu_c$ に残してよいが、環境変更は Hook / script / typed tool に限定する
   - `LLM がそのままファイルを書く` は Isolate ではなく blanket 破りである
3. **Raw Output Offload**
   - 子系の transcript 全量を親の作業面へ混入させない
4. **Irreversible Confirmation**
   - 子系が不可逆操作を含むなら、親系の確認ゲートを必ず通す

## 6. 設計上の帰結

- サブエージェント委譲は、認知負荷を外に捨てる設計ではない。**局所閉包して封じ込める設計**である。
- Active States は単独の手足ではない。**分離された blanket の内部でのみ意味を持つ能動面**である。
- Isolate の成否は、子の賢さではなく、**boot で何を渡し、bye で何を返すか**で決まる。

---
*Created: 2026-03-09*
*Refreshed: 2026-04-13 — ハーネス設計学への転換*
