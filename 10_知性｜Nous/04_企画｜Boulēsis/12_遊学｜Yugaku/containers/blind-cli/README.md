# Blind CLI Runner

FEP 分解型 blind protocol を、API 課金経路ではなく Claude Code CLI / Codex CLI の subscription CLI 経路で実行するための隔離 runner。

## 目的

この runner は、host 側の `~/.claude`、`~/.codex`、project `AGENTS.md`、project `.claude`、memory、hooks を blind participant に渡さないために使う。

渡すものは次だけに限定する。

| mount | mode | 用途 |
|:---|:---|:---|
| participant prompt | read-only | `PROMPT` block 抽出元 |
| output dir | write | model response 保存 |
| provider-specific named volume | write | container 内 CLI login 状態 |

## Build

```bash
/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/containers/blind-cli/blind-cli.sh build
```

## 初回 login

Claude と Codex は別 volume に保存する。

```bash
/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/containers/blind-cli/blind-cli.sh login claude
/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/containers/blind-cli/blind-cli.sh login codex
```

Claude は interactive CLI が開いたら `/login` を実行する。Codex は `codex login` flow に従う。

## Run

```bash
/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/containers/blind-cli/blind-cli.sh run claude
/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/containers/blind-cli/blind-cli.sh run codex
/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/containers/blind-cli/blind-cli.sh run gemini
```

既定の prompt:

```text
/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEP分解型_blind_participant_prompt.md
```

既定の output dir:

```text
/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/blind_outputs
```

## Contamination Check

```bash
/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/containers/blind-cli/blind-cli.sh check-output /absolute/path/to/output.md
```

何も出なければ、禁止語の直接混入は検出されていない。

## Gemini API

Gemini は host 側の `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/.env` から指定 key だけを読み、container へ `GOOGLE_API_KEY` として渡す。`.env` 全体は mount しない。

既定:

```text
YUGAKU_GEMINI_ENV_KEY=GOOGLE_API_KEY
YUGAKU_GEMINI_MODEL=gemini-3.1-flash-lite-preview
```

利用可能 model の確認:

```bash
/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/containers/blind-cli/blind-cli.sh models gemini
```

## 注意

- host の home directory は mount しない。
- Yugaku project root は mount しない。
- Claude と Codex の login volume は分ける。
- Codex CLI は coding-agent の既定 system prompt を持つため、完全な意味での raw LLM ではない。ただし host HGK 文脈は渡さない。
- Claude Code CLI も product-level system prompt を持つため、完全な raw LLM ではない。ただし host HGK 文脈は渡さない。
