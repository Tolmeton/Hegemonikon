# FEP 分解型 blind protocol 実行ログ — 2026-05-01

## 実行対象

- participant prompt: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEP分解型_blind_participant_prompt.md`
- evaluator rubric: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEP分解型_blind_evaluator_rubric.md`
- timestamp: `2026-05-01T18:09:57+09:00`

## 結果

blind response は得られなかった。したがって、Stage A / Stage B の採点は未実施であり、本文への empirical support としては使わない。

| route | working directory | observed result | adopted as blind evidence |
|:---|:---|:---|:---|
| Gemini CLI default | `/tmp` | capacity exhaustion retry に入った。unreadable `/tmp` directory warning と SessionEnd hook output が混じった。 | no |
| Claude bare print | `/tmp/fep-blind-yGH4fM` | `Not logged in · Please run /login` | no |
| Gemini CLI `gemini-2.5-flash` | `/tmp/fep-blind-yGH4fM` | 429 `MODEL_CAPACITY_EXHAUSTED` | no |
| Codex CLI | not run | HGK / Codex 常時文脈混入の可能性が高いため、blind participant としては使わなかった。 | no |

## 次の実行条件

次回は、少なくとも 1 つの条件を満たす経路で再実行する。

1. Gemini capacity が回復している。
2. Claude bare print が認証済みで使える。
3. OpenAI / Anthropic / Gemini API を、project-local AGENTS / memory / hooks を読まない単発スクリプトから呼べる。

Codex CLI は、本文作業者と同じ常時文脈を持つため、blind participant としては採用しない。

## 2026-05-01 追記: CLI container runner

API 課金経路を避けるため、Claude Code CLI / Codex CLI を clean container HOME で隔離して実行する runner を追加した。

- runner: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/containers/blind-cli`
- image: `yugaku-blind-cli:latest`
- build: success
- image versions: Claude Code `2.1.126`, Codex CLI `0.128.0`
- login status: 未実施。Tolmetes が `blind-cli.sh login claude` / `blind-cli.sh login codex` を一度実行する必要がある。

この runner は host の `~/.claude` / `~/.codex` / Yugaku project root を mount しない。mount するのは participant prompt、output dir、provider-specific named volume のみ。
