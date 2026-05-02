# Implementation Plan — token-optimizer adjoint bridge

## Goal

`token-optimizer` の `measure / checkpoint / archive refs` を、
`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/projects/PJ-20260417-001_v003-session-context/00_control/token_optimizer_adjoint_surface.yaml`
で定義した sidecar field に写す最小 bridge を作る。

## In Scope

- `measure --json` 相当の JSON から `quality_score` を生成する
- checkpoint JSON から `checkpoint_summary` を生成する
- archive refs JSON から `archive_refs` を生成する
- sidecar instance YAML を書き出す CLI を追加する
- bridge の単体テストを追加する

## Out Of Scope

- `project_index.yaml` と `decisions.md` の canonical authority を変更すること
- `token-optimizer` plugin の導入や hook chain の接続
- `Mekhane` 本体への組み込み
- raw prompt history や full tool output の保存

## Target Files

- `00_control/scripts/token_optimizer_bridge.py`
- `00_control/tests/test_token_optimizer_bridge.py`
- `00_control/token_optimizer_adjoint_surface.yaml`

## Execution Steps

1. sidecar schema を読み、bridge が扱ってよい field を固定する
2. `measure / checkpoint / archive` の各 mapper を実装する
3. CLI で sidecar instance YAML を生成する
4. synthetic fixture で単体テストする

## Verification

```bash
python3 -m unittest discover \
  -s '/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/projects/PJ-20260417-001_v003-session-context/00_control/tests' \
  -p 'test_*.py'
```
