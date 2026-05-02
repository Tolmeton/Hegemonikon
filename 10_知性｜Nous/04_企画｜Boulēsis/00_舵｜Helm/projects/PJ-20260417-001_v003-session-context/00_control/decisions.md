# Decisions: T-001 — V-003 State Packet Exemplar

> **Task ID**: `T-001`  
> **Source packet**: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/hgk_vision_v4.typos` (`V-003`)  
> **Next transform**: `IMPL_SPEC -> /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/specs/IMPL_SPEC_F2_SESSION_NOTE.md`  
> **作成日**: `2026-04-17`  
> **最終更新日**: `2026-04-20`  

## 採用前提

- 20+ ターン規模では Context Rot が起こりうるため、制御面の外部化は先行価値がある。
- Creator は Gemini と Claude を並走しうるため、共有 path と固定 field を先に作る意味がある。
- 最初の exemplar は `00_control` のみを対象にし、`project_index.yaml` と `decisions.md` の責務分離を優先する。
- 次変換は既存 `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/specs/IMPL_SPEC_F2_SESSION_NOTE.md` を利用し、新規 IMPL_SPEC は起こさない。

## 未採用前提

- CRDT merge と Syncthing 同期までを v1 exemplar に含める。
- 10 ターンごとの自動要約と `/bye` 時の自動変換をこの exemplar で扱う。
- `10_packs/`、`20_outputs/`、`90_archive/` の実ファイルを今回同時生成する。

## 依存判断

- 依存 ID: なし。`V-003` には `depends_on` の明示がない。
- 判定: State Packet 単体では充足済み。実装面の接続は既存 `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/specs/IMPL_SPEC_F2_SESSION_NOTE.md` を参照する。
- 補足: F2 側の backend/API/UI 実装は別作業であり、この exemplar は上流 state fixation に限定する。

## Interface Freeze

- control surface の canonical files は `00_control/project_index.yaml` と `00_control/decisions.md`。
- `project_index.yaml` は `purpose / source_packets / adopted_assumptions / rejected_assumptions / acceptance_seed / next_transform` を持つ。
- `decisions.md` は採否、依存判断、interface freeze、open questions を持ち、意思決定ログの最小面を兼ねる。
- `next_transform` の受け皿は `IMPL_SPEC_F2_SESSION_NOTE.md` に固定し、他の IMPL_SPEC には広げない。
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/projects/PJ-20260417-001_v003-session-context/00_control/token_optimizer_adjoint_surface.yaml` は restore telemetry 用の noncanonical sidecar とし、なくても State Packet の可読性は壊れない。

## Open Questions

- `project_index.yaml` と将来の `session_state.yaml` の責務境界をどこで切るか。
- 並列 AI セッション間の decision merge をどこで canonicalize するか。
- `return slip` を `decisions.md` 内 section にするか、独立 artifact にするか。
- F2 実装時に `resume_context()` 系の acceptance をどこまで V-003 の assert と直結させるか。
- `token_optimizer_adjoint_surface.yaml` を token-optimizer 専用 sidecar のまま維持するか、一般化した adjoint surface に昇格させるか。

## Next Transform

- 出力先: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/specs/IMPL_SPEC_F2_SESSION_NOTE.md`
- 昇格条件:
  - adopted / rejected assumptions が分離済みであること
  - acceptance seed が F2 の API / UI / restore 要件へ写像できること
  - path 参照が欠落せず、次の実装者が迷わないこと

## 確定ログ

- 2026-04-18 に `/kat.commit` を通し、V-003 exemplar を HGK-native Spec Protocol v1 の最初の working-tree exemplar として確定した。
- 判定の射程は「repo 履歴に永続化済み」ではなく、「現 working tree 上で canonical transform を実在化している」である。
- 確信度は `93%`。根拠は file existence, YAML parse, required section completeness, reverse link, versionability recovery の 5 面。

## 撤回条件

- `project_index.yaml`、`decisions.md`、または `next_transform.path` が欠落した場合。
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/specs/IMPL_SPEC_F2_SESSION_NOTE.md` から `Connected State Packet` 接続が消えた場合。
- `git check-ignore` で exemplar の State Packet が再び ignore 側へ落ちた場合。
