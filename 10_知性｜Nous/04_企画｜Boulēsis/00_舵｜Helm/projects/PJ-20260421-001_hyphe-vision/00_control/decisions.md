# Decisions: T-001 — Hyphē Vision Packet

> **Task ID**: `T-001`  
> **Project ID**: `PJ-20260421-001_hyphe-vision`  
> **Canonical definition**: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/00_核心｜Kernel/A_公理｜Axioms/D_座標｜Coordinates/linkage_hyphe.md`  
> **Downstream slice**: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/specs/IMPL_SPEC_F2_SESSION_NOTE.md`  
> **作成日**: `2026-04-21`

## 採用前提

- Hyphē の一語定義は `Active Inference on eta` を採る。
- SessionNotes は Hyphē の memory slice であり、Hyphē 全体の名前ではない。
- Claude Code hooks、retrieval、graph、index_op は同じ engine family の別面として扱う。
- 実装 spec を厚くする前に、何を Hyphē と呼ぶかの境界を vision で固定する。

## 未採用前提

- `IMPL_SPEC_F2_SESSION_NOTE.md` をそのまま Hyphē 全体の正本として昇格させる。
- Obsidian 風 UI の印象を Hyphē の identity とみなす。
- hooks 実験を先に進めながら後で vision を合わせれば十分である。

## Interface Freeze

- canonical control surface は `00_control/project_index.yaml` と `00_control/decisions.md`。
- canonical vision surface は `10_vision/VP-HYPHE-001_hyphe-active-inference-on-eta.typos`。
- この PJ では Hyphē の全体像のみを固定し、実装の詳細枝は F2 など既存 IMPL_SPEC 側へ残す。
- F2 は downstream slice として参照するが、この PJ の total definition にはしない。

## Open Questions

- Search / Embedding / Graph / index_op のうち、どこまでを first implementation wave に入れるか。
- Claude Code hooks は Hyphē の core slice か adapter slice か。
- `session_state.yaml` や return slip を Hyphē の canonical object に含めるか、周辺制御面にとどめるか。
- SessionNotes を Hyphē/Memory slice として再命名するか、現名を残すか。

## Next Transform

- 対象: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/specs/IMPL_SPEC_F2_SESSION_NOTE.md`
- 変換内容:
  - Hyphē 全体ではなく `session-memory slice` であることを明記する
  - 上位参照として `VP-HYPHE-001` を接続する
  - Search / Embedding / Graph / index_op の4面のうち F2 がどこに属するかを明示する

## 撤回条件

- `linkage_hyphe.md` の定義が Hyphē = Active Inference on eta から外れた場合。
- `VP-HYPHE-001_hyphe-active-inference-on-eta.typos` が F2 を total system と誤読可能な書き方になった場合。
- downstream spec 側で再び SessionNotes が Hyphē 全体を代表する記述に戻った場合。
