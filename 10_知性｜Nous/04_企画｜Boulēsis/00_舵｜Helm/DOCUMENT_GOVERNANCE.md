# ドキュメントガバナンス規則

> **目的**: Helm を正本として、HGK-native Spec Protocol v1 の artifact chain を維持する  
> **作成日**: 2026-02-25  
> **最終更新**: 2026-04-17  

---

## 基本ルール

1. **Helm 正本**: Helm 関連の企画・仕様・作業変換規則は
   `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/`
   を正本とする。
2. **バージョン管理必須**: `git add && commit` されていない文書は「存在しない」と見なす。
3. **必須ヘッダー**: reader-facing artifact には以下を含める。
   - タイトル
   - 作成日
   - 最終更新日
   - 必要なら変更履歴
4. **祖型と現行規則を分ける**:
   `hgk_vision_v4.typos` と `AMBITION.typos` は canonical ancestors、
   `HGK_NATIVE_SPEC_PROTOCOL_v1.md` は current canonical transform rule として扱う。

---

## Canonical Artifact Families

| 種別 | Canonical format | 命名 / 代表 | 役割 |
|:-----|:-----------------|:------------|:-----|
| Vision Packet | `.typos` | `hgk_vision_v4.typos`, `AMBITION.typos` | 構想面 |
| State Packet | `project_index.yaml` + `decisions.md` | template から起こす | 実装前の状態固定 |
| 実装仕様 | `.md` | `IMPL_SPEC_{コンポーネント名}.md` | 仕様面 |
| 作業指示 | `.md` | `HGK_APP_WORK_ORDERS.md` など | 実装依頼面 |
| Protocol | `.md` | `HGK_NATIVE_SPEC_PROTOCOL_v1.md` | 変換規則 |
| Templates | `.typos` / `.yaml` / `.md` | `templates/` 配下 | 最小器 |

### 命名規則

| 種別 | 命名規則 | 例 |
|:-----|:---------|:---|
| 実装仕様 | `IMPL_SPEC_{コンポーネント名}.md` | `IMPL_SPEC_F10_PLUGIN_OS.md` |
| 作業指示 | `{DOMAIN}_WORK_ORDERS.md` または aggregate work-order file | `HGK_APP_WORK_ORDERS.md` |
| Protocol | `HGK_NATIVE_SPEC_PROTOCOL_v{n}.md` | `HGK_NATIVE_SPEC_PROTOCOL_v1.md` |
| Governance | `DOCUMENT_GOVERNANCE.md` | 本文書 |

---

## Spec Gate

### Spec Gate Required

次の変更は、Vision Packet だけで実装に入らず、State Packet と IMPL_SPEC を要求する。

- 新機能
- 複数ファイルの挙動変更
- 外部連携追加 or 変更
- 永続化変更
- ルーティング / 規約変更
- UI フロー変更

### Gate Exempt

次は State Packet / IMPL_SPEC を省略できる。

- typo 修正
- 文言修正
- コメントのみ
- 局所的で非構造な微小修正

### Required Artifact Matrix

| 変更種別 | Vision Packet | State Packet | IMPL_SPEC | WORK_ORDER |
|:---------|:--------------|:-------------|:----------|:-----------|
| Gate Exempt | 任意 | 不要 | 不要 | 不要 |
| Medium+ change | 必須 | 必須 | 必須 | 必要時 |

---

## レビュープロセス

- PR で Helm 配下の protocol / spec / work-order / governance が変更された場合、レビュー対象とする。
- 新規 Medium+ change では、少なくとも `purpose / adopted assumptions / acceptance` の 3 面が見えることを確認する。
- WORK_ORDER は上位 IMPL_SPEC を参照し、acceptance を失っていないことを確認する。

---

## アーカイブポリシー

- 古くなった文書は `90_保管庫｜Archive/` 配下等に移動する。
- 移動時に「アーカイブ理由」を追記する。
- アーカイブ内の文書は参照のみ。正本として使用しない。
- 旧 vision は archive に送らず、canonical ancestors として残す。

---

## Retrofit ポリシー

- v1 制定後は **新規作成物のみ protocol 準拠を必須** とする。
- 既存 `IMPL_SPEC` 群は一括改修しない。
- 既存文書は変更が入る時だけ漸進 retrofit する。

---

## 変更履歴

| 日付 | 変更 |
|:-----|:-----|
| 2026-04-17 | Helm 正本、artifact family、Spec Gate、retrofit 方針を追加 |
| 2026-02-25 | 初版作成 |
