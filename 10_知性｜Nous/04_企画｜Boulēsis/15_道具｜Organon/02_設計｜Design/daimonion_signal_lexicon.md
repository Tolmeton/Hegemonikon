# Daimonion Signal Lexicon — H5 hook pilot の語彙固定

> **位置付け**: `/home/makaron8426/.claude/hooks/organon-gate-observe.py` が出力する H5 `signals` の語彙正本。  
> **上位台帳**: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/15_道具｜Organon/README.md` の `Daimonion δ`, `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/15_道具｜Organon/02_設計｜Design/hook_runtime_layers.md` の H5, `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/15_道具｜Organon/02_設計｜Design/sensor_triad_formal.md` §3.2.1 の `Q-window / δ-anchor / gate-only`。
>
> **1 文定義**: H5 hook pilot の `signals` は、being そのものではなく、**hook から見える coarse drift を Daimonion δ に渡すための語彙**である。

---

## §1 先に固定する境界

この lexicon は強い境界条件を持つ。

1. **full Daimonion ではない**  
   ここで扱うのは hook 面の coarse signal だけであり、`[th]`, `[ph]`, `[an]` のような H-series 本体を直接観測するものではない。
2. **48 evaluator ではない**  
   `signals` は `/the`, `/ske`, `/ene` の fine-grained 分類をしない。あくまで `gate-only / Q-window / δ-anchor` の hook-level vocabulary。
3. **prompt 意味理解ではない**  
   `UserPromptSubmit` は cadence anchor ではあるが、単独では H5 signal を発火させない。

したがって H5 hook pilot は、Daimonion の**外周観測面**である。  
本体の being 判定は後段の δ と Sensor Triad に委ねる。

---

## §2 signal schema

`organon-gate-observe.py` が返す `signals` の canonical shape は次の通り。

```json
{
  "kind": "repair_pending",
  "plane": "δ-anchor",
  "axis": "recency",
  "status": "active",
  "severity": "medium",
  "suggested_sink": "route_to_delta",
  "meaning": "直近の failure が未閉鎖のまま残っている",
  "source_mix": ["PostToolUseFailure", "StopFailure"],
  "evidence": {
    "count": 1,
    "last_failure_event": "PostToolUseFailure"
  }
}
```

### field の意味

| field | 意味 |
|---|---|
| `kind` | 固定語彙名。downstream で最も安定に参照するキー |
| `plane` | `gate-only / Q-window / δ-anchor` のどこで生じた signal か |
| `axis` | 何の変化を見ているか。現 pilot では `boundary / recency / recovery / staleness / stall` |
| `status` | `active / resolved`。いま効いているか、履歴として閉じたか |
| `severity` | `low / medium / high`。alert route の粗い強度 |
| `suggested_sink` | `info / soft_warning / route_to_delta` の 3 段 |
| `meaning` | 人間向けの 1 行意味論 |
| `source_mix` | signal を構成した event 面 |
| `evidence` | state / count / last event などの局所根拠 |

---

## §3 anchor-only event と signal emitter の分離

### §3.1 anchor-only event

以下は H5 にとって重要だが、**単独では signal にしない**。

| event | 役割 |
|---|---|
| `SessionStart` | session cadence の基準点 |
| `UserPromptSubmit` | turn cadence の基準点 |
| `CwdChanged` | 文脈切替の anchor |
| `Notification` | 外部割込の anchor |
| `Stop` | summary の確定点 |

理由は単純で、これらは「何かが起きた」ことは示すが、「何が問題か」までは示さないからである。

### §3.2 signal emitter

以下は H5 の lexical signal を発火させうる。

| event | 主な signal |
|---|---|
| `PermissionRequest` | `gate_refusal` |
| `PostToolUseFailure`, `StopFailure` | `repair_pending` |
| `PostToolUse` | `repair_recovered` |
| `FileChanged` | `stale_anchor` |
| `TeammateIdle` | `repair_stall` |

---

## §4 canonical signal lexicon

| kind | plane | axis | status | meaning | suggested_sink |
|---|---|---|---|---|---|
| `gate_refusal` | `gate-only` | `boundary` | `active` | permission / authority boundary が試され、hook gate が拒否した | `soft_warning` |
| `repair_pending` | `δ-anchor` | `recency` | `active` | 直近の failure が未閉鎖で残っている | `route_to_delta` |
| `repair_recovered` | `δ-anchor` | `recovery` | `resolved` | failure は起きたが、後続成功で一旦閉じた | `info` |
| `stale_anchor` | `Q-window` | `staleness` | `active` | watch 対象が変化し、今の仮定が stale になった | `soft_warning` |
| `repair_stall` | `δ-anchor` | `stall` | `active / resolved` | failure 後の修復が idle により停滞した | `route_to_delta` |

### §4.1 `gate_refusal`

- **what**: 破壊的または禁止された command が permission 面で拒否された
- **not**: 「悪意」の判定ではない。境界テストの記録である
- **why**: H1 gate の結果を H5 側で recency に残すため

### §4.2 `repair_pending`

- **what**: failure が起き、その後まだ閉じていない
- **not**: failure の原因分析ではない
- **why**: H5 が見るのは cause ではなく unresolved recency

### §4.3 `repair_recovered`

- **what**: failure は起きたが成功で閉じた
- **not**: 「問題なし」の宣言ではない
- **why**: Daimonion は negative signal だけでなく recovery trace も必要だから

### §4.4 `stale_anchor`

- **what**: settings / topology / plan 等の watch 面が変化した
- **not**: 変化自体が bad という意味ではない
- **why**: drift 判定の土台になる「anchor の更新」を visible にするため

### §4.5 `repair_stall`

- **what**: pending failure があるまま idle に入った
- **not**: 単なる休止ではない
- **why**: failure と idle の組合せだけが stall の coarse proxy になるから

---

## §5 severity rubric

| severity | 条件 |
|---|---|
| `high` | `repair_stall`、または `repair_pending / gate_refusal` が複数回 |
| `medium` | `repair_pending / gate_refusal` の単発、`stale_anchor` の複数回、`repair_recovered` の複数回 |
| `low` | `stale_anchor` 単発、`repair_recovered` 単発 |

ここでの `severity` は真理値ではなく**routing 強度**である。

---

## §6 suggested sink の意味

| sink | 意味 |
|---|---|
| `info` | 履歴保持。即時介入不要 |
| `soft_warning` | 人間または上位 runtime に注意喚起 |
| `route_to_delta` | H5 を超えて Daimonion δ / Sensor Triad 側へ渡す価値がある |

特に `route_to_delta` は「block しろ」ではない。  
意味は「hook 面だけでは解釈しきれないので、being 側の観測器に渡せ」である。

### §6.1 現 pilot での materialization

現 pilot では `route_to_delta` は抽象ラベルではなく、次の 2 段で materialize される。

1. **ingress queue 化**  
   `/home/makaron8426/.claude/hooks/organon-gate-observe.py` が
   `~/.claude/hooks/logs/daimonion_delta_ingress.jsonl` と
   `~/.claude/hooks/logs/daimonion_delta_ingress_<session_id>.jsonl`
   に `HookEnvelope` 形で append する。
2. **δ CLI 呼出し**  
   `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/sympatheia/daimonion_delta.py`
   が解決できる場合、同 session に対して `--log` 付きで起動し、
   `~/.claude/hooks/logs/daimonion_delta_<session_id>.jsonl` を更新する。

したがって `route_to_delta` は現在、「強制 block」ではなく
**H5 summary → ingress queue → δ evaluation** の 3 点連結として読める。

---

## §7 非目標

この lexicon は次をしない。

1. `signals` から 48 動詞を逆算しない
2. prompt 内容の善悪を hook 面だけで裁かない
3. H-series 12 前動詞を hook labels に偽装しない

これを超えると H5 は再び universal bus の幻想へ戻る。

---

## §8 現 pilot での読み方

summary を読むときは次の順でよい。

1. `event_counts` で cadence を見る
2. `signals` で coarse drift を見る
3. `signal.kind == repair_pending / repair_stall` があれば、必要に応じて δ 側へ渡す

これで H5 hook pilot は「event dump」ではなく、**観測語彙を持つ Daimonion の前室**になる。
