# HGK-native Spec Protocol v1

> **目的**: HGK の「構想 `.typos` → 状態パケット → `IMPL_SPEC` → `WORK_ORDER` → 実装/レビュー」の正規変換を、Helm ローカル正本として固定する  
> **正本面**: `10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/`  
> **作成日**: 2026-04-17  
> **最終更新日**: 2026-04-17  
> **ステータス**: v1 制定  

---

## 1. 本文書の立場

この protocol は、汎用の `requirements/design/tasks` を HGK に輸入する文書ではない。  
`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/hgk_vision_v4.typos` と
`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/AMBITION.typos`
に散在していた HGK 固有の artifact chain を抽出し、現行の `Helm/specs/` 運用へ接続するための
**current canonical transform rule** である。

### 祖型 (canonical ancestors)

- `hgk_vision_v4.typos`
- `AMBITION.typos`

これらは **置換対象ではなく祖型** として扱う。v1 制定後も参照元として残し、既存文書の一括 retrofitting は行わない。

---

## 2. Canonical Artifact Chain

HGK の canonical artifact は次の 4 層に固定する。

```text
Vision Packet (.typos)
  -> State Packet (project_index.yaml + decisions.md)
  -> IMPL_SPEC (.md)
  -> WORK_ORDER (.md)
  -> Implementation / Review
```

| Artifact | Canonical format | 役割 | 必須面 |
|:---------|:-----------------|:-----|:-------|
| Vision Packet | `.typos` | 構想の核、仮定、完了条件の外化 | `intent / assume / spec / detail / rationale / assert / depends_on / status` |
| State Packet | `project_index.yaml` + `decisions.md` | 実装前の状態固定、前提の採否、次変換先の管理 | `task_id / adopted_assumptions / rejected_assumptions / dependencies / next_transform / acceptance_seed` |
| IMPL_SPEC | `.md` | 実装仕様の reader-facing artifact | `概要 / 既存接続先 or 前提 / interface or data model / 実装ステップ / テスト / 依存関係 / 非対象` |
| WORK_ORDER | `.md` | 実装依頼の縮約面 | `Gap or Task ID / 依頼先 / 実装指示 / 検証基準 / ブロッカー / 参照 IMPL_SPEC` |

### 運用上の注意

- artifact は **概念上の単位** であり、必ずしも 1 artifact = 1 ファイルとは限らない。
- Vision Packet と WORK_ORDER は、単独ファイルでも section 単位でもよい。
- ただし required fields は省略しない。形式の自由は、責務の省略免罪符ではない。

---

## 3. Artifact Definition

### 3.1 Vision Packet

Vision Packet は「何を作りたいか」だけでなく、「どんな前提を置き」「どう完了判定するか」までを先に持つ。

| 面 | 役割 | v1 要件 |
|:---|:-----|:--------|
| `intent` | 原文の着想を保存する | 目的の歪曲禁止 |
| `assume` | operative assumption 候補 | 後で採否判定できる粒度で書く |
| `spec` | 技術構造 | パイプライン、YAML、図、API など |
| `detail` | 実装・工数・未決 | 未決事項を隠さない |
| `rationale` | なぜ必要か | 設計判断の理由 |
| `assert` | acceptance seed | 検証可能な完了条件 |
| `depends_on` | 依存関係 | 先行項目 ID を明示 |
| `status` | 現在地 | 構想 / 要設計 / 実装中 など |

### 3.2 State Packet

State Packet は、Vision Packet をそのまま実装へ流さず、**いま採る前提** と **捨てる前提** を分ける層である。

#### `project_index.yaml`

最低限、次を持つ。

| フィールド | 説明 |
|:-----------|:-----|
| `task_id` | この変換の作業 ID |
| `title` | 作業名 |
| `purpose` | 今回固定する目的 |
| `source_packets` | 参照した Vision Packet / AMBITION / IMPL_SPEC |
| `dependencies` | 依存 ID |
| `acceptance_seed` | Vision Packet の `assert` から降ろした完了条件候補 |
| `next_transform` | 次に作る artifact (`IMPL_SPEC` など) |
| `status` | draft / ready_for_impl_spec / blocked など |

#### `decisions.md`

最低限、次を持つ。

| セクション | 説明 |
|:-----------|:-----|
| `採用前提` | IMPL_SPEC に昇格する前提 |
| `未採用前提` | 今回は捨てる、もしくは保留する前提 |
| `依存判断` | 先行条件の充足有無 |
| `interface freeze` | 仕様面で固定した境界 |
| `open questions` | 未決だが進行上残るもの |
| `next transform` | 次に作る IMPL_SPEC / WORK_ORDER |

### 3.3 IMPL_SPEC

IMPL_SPEC は executor memo ではなく、仕様の reader-facing artifact である。

| セクション | 説明 |
|:-----------|:-----|
| `概要` | 何を実装するか |
| `既存接続先 or 前提` | どこにつなぐか、何を再利用するか |
| `interface or data model` | API / 型 / データ構造 / UI 契約 |
| `実装ステップ` | 実装順序 |
| `テスト` | 機械的検証 |
| `依存関係` | 他コンポーネントとの前提 |
| `非対象` | 今回やらないこと |

### 3.4 WORK_ORDER

WORK_ORDER は IMPL_SPEC を実装単位へ縮約する面であり、spec を失ってはならない。

| セクション | 説明 |
|:-----------|:-----|
| `Gap or Task ID` | 追跡 ID |
| `依頼先` | 担当 agent / 実装主体 |
| `実装指示` | 変更対象と期待される挙動 |
| `検証基準` | 受け入れ条件 |
| `ブロッカー` | 先に解くべきこと |
| `参照 IMPL_SPEC` | 上位仕様へのポインタ |

---

## 4. Transform Rules

### 4.1 Vision Packet -> State Packet

Vision Packet をそのまま実装へ流さない。まず State Packet へ写像する。

| Vision Packet | State Packet での写像先 |
|:--------------|:------------------------|
| `intent` | `purpose` |
| `assume` | `adopted_assumptions` / `rejected_assumptions` の候補 |
| `assert` | `acceptance_seed` |
| `depends_on` | `dependencies` |
| `status` | `status` |

#### ルール

1. `assume` は必ず **採用 / 未採用 / 保留** に分ける。  
2. `assert` は必ず `acceptance_seed` に降ろし、検証可能な文に保つ。  
3. `depends_on` は、State Packet で依存 ID と充足判定に分解する。  
4. `project_index.yaml` には source packet のパスを残す。  

### 4.2 State Packet -> IMPL_SPEC

IMPL_SPEC に昇格できるのは、`decisions.md` で **採用済み** とされた前提だけである。

#### ルール

1. `採用前提` だけを `既存接続先 or 前提` に昇格する。  
2. `未採用前提` は IMPL_SPEC の本文に混ぜず、`非対象` または `未決` として隔離する。  
3. `acceptance_seed` は `テスト` セクションへ具体化する。  
4. `next transform` が `IMPL_SPEC` 以外なら、昇格を止める。  

### 4.3 IMPL_SPEC -> WORK_ORDER

WORK_ORDER は IMPL_SPEC を実装依頼へ縮約するが、acceptance を落としてはならない。

#### ルール

1. WORK_ORDER は、参照する `IMPL_SPEC` のパスを必須で持つ。  
2. `実装指示` は具体化してよいが、上位 spec と矛盾しない。  
3. `検証基準` は IMPL_SPEC の `テスト` から導く。  
4. `非対象` は WORK_ORDER にも暗黙継承させず、必要なら明示する。  

---

## 5. Spec Gate

v1 では、すべての作業に gate を強制しない。  
**Medium+ changes** 以上を `Spec Gate Required` とする。

### 5.1 Spec Gate Required

次の変更は、Vision Packet だけで実装に入ってはならない。

- 新機能
- 複数ファイルの挙動変更
- 外部連携追加 or 変更
- 永続化変更
- ルーティング / 規約変更
- UI フロー変更

#### Required artifact

```text
Vision Packet
  + State Packet
  + IMPL_SPEC
  + WORK_ORDER (必要時)
```

### 5.2 Gate Exempt

次は `Spec Gate` 免除。

- typo 修正
- 文言修正
- コメントのみ
- 局所的で非構造な微小修正

#### Exempt rule

- 免除は「artifact 不要」ではなく「State Packet / IMPL_SPEC を省略可」という意味。  
- ただし影響範囲が途中で拡大した時点で `Spec Gate Required` に昇格する。  

### 5.3 判定例

| 変更 | 判定 | 理由 |
|:-----|:-----|:-----|
| typo 修正 | Exempt | 非構造・局所 |
| 複数ファイルの新機能 | Required | Medium+ |
| 外部連携追加 | Required | 接続面変更 |

---

## 6. Legacy Policy

### 6.1 旧文書の扱い

- `hgk_vision_v4.typos` と `AMBITION.typos` は **canonical ancestors**
- 既存 `IMPL_SPEC` 群は **現行 reader-facing artifacts**
- v1 制定後も、旧文書は置換しない

### 6.2 Retrofit 方針

- 新規作成物のみ protocol 準拠を必須にする
- 既存文書は、変更が入る時だけ漸進 retrofit
- 一括改修は v1 の対象外

---

## 7. Dry-run Validation

### Case A: `hgk_vision_v4.typos` V-003

対象: `V-003 セッション外部コンテキスト + 並列同期`

期待される変換:

- `intent` -> State Packet の `purpose`
- `assume` -> `adopted_assumptions` / `rejected_assumptions`
- `assert` -> `acceptance_seed`
- `depends_on` が無ければ `dependencies: []`
- `project_index.yaml` から `IMPL_SPEC_F2_SESSION_NOTE.md` のような実装面へ自然に落ちる

この case は、protocol が `project_index` と `decisions` を要求することで、
`V-003` の「project_index / decisions / packet / return slip」という旧 vision の核を
欠落なく現代化できることを示す。

### Case B: `AMBITION.typos` F10 -> `IMPL_SPEC_F10_PLUGIN_OS.md`

対象:

- source: `AMBITION.typos` の `F10 Plugin OS`
- target: `Helm/specs/IMPL_SPEC_F10_PLUGIN_OS.md`

期待される整合:

- F10 の goal / constraints が Vision Packet 面として読める
- State Packet で採用前提を固めると、既存 `IMPL_SPEC_F10_PLUGIN_OS.md` の
  `概要 / データモデル / API 仕様 / 実装ステップ` へ自然に降りる
- 既存 IMPL_SPEC を壊さずに protocol の上流面として接続できる

---

## 8. Template Pack

v1 の template pack は次を正本とする。

- `templates/VISION_PACKET_TEMPLATE.typos`
- `templates/PROJECT_INDEX_TEMPLATE.yaml`
- `templates/DECISIONS_TEMPLATE.md`
- `templates/IMPL_SPEC_TEMPLATE.md`
- `templates/WORK_ORDER_TEMPLATE.md`

### 使用原則

1. template は required fields の最小器であり、長文化のための器ではない。  
2. 新規 Medium+ change では template から起こしてよい。  
3. 既存の aggregate doc に section として埋め込む場合も required fields は保持する。  

---

## 9. Non-Goals

この v1 では次を行わない。

- `.agents/rules` への昇格
- `requirements/design/tasks` への全面置換
- 既存全文書の一括 retrofit
- Helm 以外の正本面の再編

---

## 変更履歴

| 日付 | 変更 |
|:-----|:-----|
| 2026-04-17 | v1 初版制定 |
