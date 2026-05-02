# Pinakas (πίνακας) — セッション横断タスクボード プロトコル

**v1.3** | 2026-04-11

## 概要

Pinakas = セッション間の共有ホワイトボード。
どのセッション (Claude Code / Gemini / Jules / Creator) からでも読み書きできる、
YAML ベースの付箋ボード。

## ボード一覧 (MECE)

| ボード | ファイル | ID接頭辞 | 温度 | 用途 |
|:-------|:---------|:---------|:----:|:-----|
| **Task** | `PINAKAS_TASK.yaml` | `T-` | ⚡即時 | 具体的な作業項目・バグ・修正依頼 |
| **Seed** | `PINAKAS_SEED.yaml` | `S-` | 🌱芽 | PJ の芽・アイデア・「いつかやりたい」 |
| **Question** | `PINAKAS_QUESTION.yaml` | `Q-` | ❓ | 調べたいこと・未解決の問い |
| **Wish** | `PINAKAS_WISH.yaml` | `W-` | 🟠WARM | 四半期候補・設計完了→実装待ち |
| **Backlog** | `PINAKAS_BACKLOG.yaml` | `B-` | ❄️COLD | 半年以上先の願望・構想 |
| **Whiteboard** | `PINAKAS_WHITEBOARD.yaml` | `WB-` | 📝NOTES | 論文執筆中の戦略ノート・作業記憶 (本体は別体 .md) |

配置: `10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/pinakas/`

Whiteboard の本体 md は `whiteboards/WB-NNN_*.md` に配置される。YAML は索引のみ。
詳細は下部「Whiteboard ボード仕様」を参照。

## 操作 (4つ)

### 1. post — 項目を追加

```yaml
# PINAKAS_TASK.yaml に追加する例
- id: T-001
  text: "/ero パイプラインが hermeneus_run を経由していない"
  from: "claude-code#2026-03-29-PM"
  date: 2026-03-29
  status: open
  priority: high
  tags: [ccl, bug]
  sprint_ref: S-002  # Sprint ストリームへの紐付け (任意)
```

**v1.1 追加フィールド:**

| フィールド | 対象ボード | 必須 | 説明 |
|:-----------|:-----------|:-----|:-----|
| `sprint_ref` | Task | 任意 | Sprint ストリーム ID (S-001〜S-006) への紐付け |
| `origin` | Seed | 任意 | アイデアの起源 (`session` / `creator` / `incubator` / `backlog`) |

**ルール:**
- `_meta.next_id` を読み、その値で ID を振り、`next_id` をインクリメント
- `_meta.last_updated` を今日の日付に更新
- `from` は `エージェント名#YYYY-MM-DD-AM/PM` 形式
- Creator が手書きする場合は `from: creator#YYYY-MM-DD`

### 2. list — 一覧表示

ボードの `items` を読み、`status: open` (+ `in_progress`) のものを表示。

出力形式:
```
PINAKAS SEED (2 open)
  S-001 [open] Gnosis に論文推薦機能 #gnosis
  S-002 [open] Hyphē 結晶化の自動トリガー #hyphē

PINAKAS TASK (1 open)
  T-001 [open] /ero hermeneus_run 未経由 #ccl #bug — high

PINAKAS QUESTION (1 open)
  Q-001 [open] UniT ablation は HGK に適用可能か #fep #paper
```

### 3. done — 完了 / 回答

- Task: `status: done`、`note` に完了日と結果を記載
- Question: `status: answered`、`answer` に回答を記載
- Seed: `status: adopted` (PJ 化) または `status: dropped` (不採用)

### 4. drop — 不要になった項目を除去

`status: dropped`、`note` に理由を記載。
項目は削除せず残す (履歴として)。

## 振り分けガイド

| 「これは...」 | → ボード |
|:-------------|:---------|
| ふわっとした思いつき、PJ になるかもしれないアイデア | **Seed** |
| 具体的にやるべき作業、バグ、修正依頼 | **Task** |
| 調べないとわからないこと、検証が必要な問い | **Question** |

迷ったら **Seed** に入れる。Seed は最も自由度が高い。

## ライフサイクル

```
Seed (open) → adopted → registry.yaml に PJ 登録
           → dropped  → 理由を note に

Task (open) → in_progress → done
           → dropped

Question (open) → answered (answer に回答)
               → dropped
```

## Boot 統合

`/boot` Phase 6 で、全ボードの `open` 項目数をサマリー表示:

```
PINAKAS: Seed 2 | Task 1 | Question 1
```

`/boot+` では個別項目も展開。

## 競合回避 (並列セッション)

複数セッションが同時に書き込む場合:
1. **Read → Edit** のアトミック操作を徹底 (Read してから Edit)
2. **追記のみ**: 既存項目の変更は原則そのセッション自身が post したものだけ
3. **ID 衝突**: `_meta.next_id` が衝突した場合、後から書いた方が ID を再採番
4. **Syncthing**: ファイル同期で CRDT 的に収束 (YAML の append-only 特性を活用)

## 既存機構との関係

| 機構 | 用途 | Pinakas との違い |
|:-----|:-----|:----------------|
| **Intent-WAL** | 単一セッション内のクラッシュリカバリ | セッション内 (揮発) |
| **Handoff** | セッション終了時の圧縮記憶 | 事後的 (セッション間は /boot で復元) |
| **registry.yaml** | PJ の正式登録 | Seed が育ったら移行先 |
| **backlog.md** | COLD 願望リスト | 長期ビジョン (半年+) |
| **Work Orders** | 管理者向け Gap/WO | 構造化された開発管理 |
| **Pinakas** | セッション中に生まれた付箋 | **即時性** — 思いついた瞬間に貼る |

## ダッシュボード生成

`generate_dashboard.py` を実行すると、3ボードを統合した俯瞰ビュー `PINAKAS_DASHBOARD.md` を生成する。

```bash
python pinakas/generate_dashboard.py
```

含まれる情報:
- 📊 サマリー (全ボードの件数)
- 🎯 Sprint ストリーム × アクティブ Task マトリクス
- 🔥 今日のアクション候補 (open × high)
- 🌱 Seed ボード一覧
- ✅ 直近の完了 Task

## Whiteboard ボード仕様 (v1.3〜)

Whiteboard (WB) は他 5 ボードと異なり、**「索引 YAML + 本体 .md」の二層構造**を持つ。
長文・構造化・状態遷移を持つ戦略ノート (論文執筆の作業記憶層など) を保持する。

### 構造

```
pinakas/
├── PINAKAS_WHITEBOARD.yaml      # 索引 (items フィールドに WB メタデータ)
└── whiteboards/
    ├── WB-001_xxx.md            # 本体 (長文・自由構造)
    └── WB-002_yyy.md
```

YAML 索引は「どの WB が存在するか・状態・最終更新」の high-level view のみ。
実質コンテンツ (戦略原理、梁、停止条件、派生問い等) は本体 md が持つ。

### スキーマ (items フィールド)

| フィールド | 必須 | 型 | 説明 |
|:----------|:----:|:---|:-----|
| `id` | ✓ | str | `WB-NNN` 形式 |
| `title` | ✓ | str | ボード項目のタイトル |
| `path` | ✓ | str | pinakas/ からの相対パス (例: `whiteboards/WB-001_xxx.md`) |
| `target` | — | str | この WB が対象とする論文・プロジェクトのリポ内相対パス |
| `status` | ✓ | enum | `active` / `paused` / `archived` |
| `created` | ✓ | date | YYYY-MM-DD |
| `updated` | ✓ | date | YYYY-MM-DD |
| `source` | — | str | セッション ID 等 |
| `tags` | — | list[str] | タグ |
| `note` | — | str | 短い説明 |

### 既存 Hook との接続 (双方向リンク)

- 本体 md 内の `📋T:` `📋S:` `📋Q:` マーカーは既存 PostToolUse Hook (`pinakas-queue.py`) が
  Edit/Write 検出時に拾い、セッション別キューへ蓄積 → `/bye` で PINAKAS_TASK/SEED/QUESTION.yaml へ merge される
- つまり WB は「派生 Task/Seed/Question の発行源」として機能する
- 逆向きリンクは、Task/Seed/Question 側 item に `related_wb: WB-NNN` を任意で付与することで維持する
- 新マーカー `📋W:` (Whiteboard create) は追加しない。WB 新設は頻度が低いため手動で十分

### 他ボードとの使い分け

- Task/Seed/Question/Wish/Backlog: **短文の付箋**。1 項目 1-3 行
- Whiteboard: **長文の戦略ノート**。論文・大型 PJ の作業記憶。複数セクション・状態遷移を持つ

迷ったら他ボードに書く。WB を新設するのは「会話ベースの構想が揮発すると困る」戦略層だけ。

## 改版履歴

- **v1.3** (2026-04-11): 6 番目のボード Whiteboard を追加。索引 YAML + 本体 md の二層構造
- **v1.2** (2026-04-01): 5 ボード体制 (Wish/Backlog 追加)
- **v1.1**: Sprint 紐付け (`sprint_ref`)、Seed 起源 (`origin`) を追加
- **v1.0**: 初版 (3 ボード: Seed/Task/Question)

## MCP 拡張 (将来)

Phase 2 として Phantázein MCP にエンドポイントを追加予定:
- `phantazein_pinakas(action, board, item)` — CRUD 操作
- Boot Context の `pinakas` 軸として自動配信
