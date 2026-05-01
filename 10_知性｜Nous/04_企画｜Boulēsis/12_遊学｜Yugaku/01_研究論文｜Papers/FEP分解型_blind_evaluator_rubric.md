# FEP 分解型 blind evaluator rubric

この rubric は評価者側の内部資料である。盲検列挙者には渡さない。
参加者には `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEP分解型_blind_participant_prompt.md` の `PROMPT` ブロックのみを渡す。

## 0. Contamination Gate

| 項目 | 判定 |
|:---|:---|
| 参加者 prompt に Hegemonikon / HGK / CCL が含まれていない | 未判定 |
| 参加者 prompt に 36 Poiesis / 12 H-series / 48-frame が含まれていない | 未判定 |
| 参加者 prompt にギリシャ語ラベル、skill 名、動詞名が含まれていない | 未判定 |
| 参加者 prompt に本文 §5 以降の座標表が含まれていない | 未判定 |

1 つでも崩れた場合、その実行は blind evidence として採用しない。

## 1. Stage A: Decomposition Recovery

各項目は `0 = 欠落`、`1 = 弱い橋として出る`、`2 = 明確な独立型または内部構造として出る` で採点する。

| ID | 期待される回収面 | 2 点条件 | score | memo |
|:---|:---|:---|:---:|:---|
| D1 | Helmholtz / solenoidal-dissipative / gradient-flow | 力学的分解として明示される | 未判定 |  |
| D2 | Markov blanket / internal-external boundary | 内外境界が状態空間の構造として出る | 未判定 |  |
| D3 | inference / action | 推論と行為の方向差として出る | 未判定 |  |
| D4 | VFE = Accuracy - Complexity | VFE の代数的分解として出る | 未判定 |  |
| D5 | EFE = Epistemic + Pragmatic | 方策評価の機能分解として出る | 未判定 |  |
| D7 | temporal contrast: VFE / EFE, past / future, temporal depth | 時間方向または時間深度として出る | 未判定 |  |
| D8 | precision weighting | confidence / uncertainty ではなく FEP 内部パラメータとして出る | 未判定 |  |
| D9 | scale / hierarchy | hierarchical generative model、deep generative model、または scale-free active inference として出る | 未判定 |  |
| D10 | interoceptive / affective valence | 内受容推論または情動符号として出る | 未判定 |  |
| Extra | 本稿の 9 型で説明できない安定型 | 反復実行で安定して出る | 未判定 |  |

## 2. Stage B: Coordinate Support

Stage A の出力だけを見て、CE 層を支える制約面が blind に回収されるかを見る。
これは語名や CCL 呼称の評価ではない。

| 制約面 | 成功条件 | score | memo |
|:---|:---|:---:|:---|
| Basis | D1 系の力学的基底が出る | 未判定 |  |
| Directionality | D3 と D2 から Afferent / Efferent 相当の方向差が読める | 未判定 |  |
| Value | D2 の internal / external が目的値の向きへ接続できる | 未判定 |  |
| Function | D5 から Explore / Exploit 相当の差が読める | 未判定 |  |
| Precision | D8 が FEP 内部パラメータとして出る | 未判定 |  |
| Scale | D9 が階層・粒度差として出る | 未判定 |  |
| Temporality | D7 が時間方向として出る | 未判定 |  |
| Valence | D10 が内受容・情動符号として出る | 未判定 |  |

## 3. Verdict Rule

| 判定 | 条件 | 本文への反映 |
|:---|:---|:---|
| Fail | Basis または Directionality が欠落 | 48-frame の FEP 接地を主張しない |
| Weak pass | Basis と Directionality が出て、6 修飾座標のうち 4 つ以上が出る | 弱い座標面を明示して §6.2 を制限する |
| Strong pass | Basis、Directionality、6 修飾座標がすべて出る | CE 層への blind support として本文または appendix に記録する |

Precision / Scale / Valence は、独立した代数的分解でなくてもよい。FEP 内部パラメータ、階層構造、内受容セクターとして出れば Stage B では成功とする。

## 4. Execution Record Template

| 項目 | 記録 |
|:---|:---|
| 実行日 |  |
| 参加者 / モデル |  |
| prompt file | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEP分解型_blind_participant_prompt.md` |
| raw response 保存先 |  |
| Stage A verdict |  |
| Stage B verdict |  |
| contamination verdict |  |
| 本文へ戻す修正 |  |

## 5. Attempt Log

| 日付 | route | result | evidence status |
|:---|:---|:---|:---|
| 2026-05-01 | Gemini CLI default from `/tmp` | capacity exhaustion。CLI warning / hook output が混じったため、途中停止。 | 不採用 |
| 2026-05-01 | Claude `--bare --print --tools "" --no-session-persistence` from `/tmp/fep-blind-yGH4fM` | `Not logged in` で失敗。 | 不採用 |
| 2026-05-01 | Gemini CLI `gemini-2.5-flash` from `/tmp/fep-blind-yGH4fM` | 429 `MODEL_CAPACITY_EXHAUSTED`。途中停止。 | 不採用 |
| 2026-05-01 | Codex CLI | HGK / Codex 常時文脈混入の可能性が高いため実行せず。 | 不採用 |
| 2026-05-01 | Gemini API `gemini-3.1-flash-lite-preview` via container runner | response 取得。D2/D3/D4/D5/D7/D8/D9/D10 相当は回収、D1 Basis は欠落。 | 採用。ただし strict verdict は Fail |

## 6. Evaluation Log

| 日付 | response | contamination | Stage A | Stage B | verdict |
|:---|:---|:---|:---|:---|:---|
| 2026-05-01 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/blind_outputs/gemini_gemini-3.1-flash-lite-preview_20260501T132107Z.md` | 禁止語直接混入なし | D1=0, D2=2, D3=2, D4=2, D5=2, D7=2, D8=2, D9=2, D10=1 | Basis=0, Directionality=2, Value=1, Function=2, Precision=2, Scale=2, Temporality=2, Valence=1 | Fail |
