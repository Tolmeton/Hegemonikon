# implementation_plan.md

作成日: 2026-04-23
対象:

- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/registry.yaml`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/adjoint_map.yaml`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/README.md`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/README.md`

## 目的

`token-optimizer-mcp` の随伴配置を会話上の方針から正本面へ昇格し、
Helm / OssAdjoint / Oblivion の入口から辿れる状態にする。

## 変更対象

1. `registry.yaml` の Aristos / Oblivion / deerflow-adjoint を、
   現物 path と参照文書に合わせて補正する。
1. `adjoint_map.yaml` に `deerflow-adjoint <- token-optimizer-mcp` を追加し、
   可逆核と棄却対象を明示する。
1. `OssAdjoint/README.md` に middleware companion rule への導線を追加する。
1. `Oblivion/README.md` に忘却随伴メモへの導線を追加する。

## 実装手順

1. `registry.yaml` で壊れた path / entry_point を現物に合わせる。
1. `adjoint_map.yaml` に token-optimizer-mcp の companion entry を追加する。
1. README 2 面に導線を足し、入口から辿れるようにする。
1. YAML parse と `git diff --check` を通して、
   文法破損と空白破損を確認する。

## 検証

1. `python` YAML parse

<!-- markdownlint-disable MD013 -->

```bash
python - <<'PY'
import yaml
from pathlib import Path

for path in [
    Path('/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/registry.yaml'),
    Path('/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/adjoint_map.yaml'),
]:
    yaml.safe_load(path.read_text())
    print(f'OK {path}')
PY
```

1. `markdownlint`

```bash
npx --yes markdownlint-cli \
  '/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/implementation_plan.md' \
  '/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/README.md' \
  '/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/README.md'
```

1. `diff check`

```bash
git diff --check -- \
  '/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/registry.yaml' \
  '/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/adjoint_map.yaml' \
  '/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/implementation_plan.md' \
  '/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/README.md' \
  '/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/README.md'
```

<!-- markdownlint-enable MD013 -->
