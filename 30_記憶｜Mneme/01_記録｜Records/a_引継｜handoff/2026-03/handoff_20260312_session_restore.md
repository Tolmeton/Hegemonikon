# Handoff: Antigravity IDE セッション復元調査

- **日時**: 2026-03-12 19:30–20:02
- **状態**: 🔴 復元不可 (IDE 本体の制約)
- **残タスク**: Google バグ報告のみ

---

## S — 状況

PC 再起動後、Antigravity IDE の全セッション履歴が消失。IDE 自体がセッションを立ち上げられなくなった。再インストールで新規セッションは動作するが、過去セッション (約74件) は UI に表示されない。

## B — 背景

前セッションで `restore_v4.py` による `state.vscdb` 直接操作を試みたが、IDE の protobuf 検証に拒否された。ロールバック後、別アプローチとして IDE の内部構造解析に転換。

## A — 分析結果

### IDE セッション管理アーキテクチャ (確定)

| レイヤー | 格納場所 | 内容 |
|---|---|---|
| ワークスペース登録 | `sidebarWorkspaces` (ローカル DB) | URI リストのみ。conversation ID なし |
| セッション一覧 | **Google サーバー** | `GetCascadeTrajectory` API で取得 |
| メタデータキャッシュ | `trajectorySummaries` (ローカル DB) | サーバーからのキャッシュ |
| データ本体 | `conversations/*.pb` (ローカル) | **暗号化**キャッシュ |

### 重要な発見

1. **`agentSessions` サービス初期化失敗**
   - Developer Console: `ERR [createInstance] xoe depends on UNKNOWN service agentSessions.`
   - IDE の DI 機構でセッション管理サービスが未登録
   - これが根本原因の可能性 (確度 70%)

2. **ローカル操作不可の理由**
   - `.pb` は暗号化 → 読めない
   - `sidebarWorkspaces` は workspace URI のみ → conversation がない
   - `trajectorySummaries` はキャッシュ → サーバー次第
   - IDE は `makeRequest("GetCascadeTrajectory")` でサーバーに問い合わせる

### 試行履歴

| 手法 | 結果 |
|---|---|
| `restore_v4.py` (protobuf 再構築→DB注入) | IDE が拒否、全データ不可読 → ロールバック |
| `sidebarWorkspaces` 解析 | conversation ID は格納されていない |
| `trajectorySummaries` 解析 | サーバーキャッシュに過ぎない |
| IDE ソース解析 (`jetskiAgent/main.js`) | `GetCascadeTrajectory` API 確認 |
| Developer Console 調査 | `agentSessions` サービス初期化失敗を発見 |

## R — 推奨

1. **`.pb` ファイルを保全** — IDE バグ修正で復活する可能性あり
2. **`brain/` アーティファクトを活用** — 全て暗号化されておらず読める
3. **Google にバグ報告** — `agentSessions` サービス初期化失敗ログを添付
4. **IDE アップデートを待つ** — サーバーにデータが残っていれば自動復元の可能性

---

## 関連ファイル

- `C:\Users\makar\AppData\Local\Temp\decode_f2.py` — sidebarWorkspaces F2 デコード
- `C:\Users\makar\AppData\Local\Temp\search_backend.py` — jetskiAgent セッション管理検索
- `C:\Users\makar\AppData\Local\Temp\check_settings.py` — agentPreferences 確認
