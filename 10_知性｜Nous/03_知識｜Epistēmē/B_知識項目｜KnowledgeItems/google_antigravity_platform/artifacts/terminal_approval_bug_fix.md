# Antigravity IDE ターミナル毎回承認バグ — 調査・修正記録

**日付**: 2026-03-11
**ステータス**: ✅ 解決済み
**影響バージョン**: Antigravity v1.107.0 (IDE 1.20.5)

## 症状

- Settings → Agent → Terminal Execution → "Always Proceed" に設定しても、毎回 Run/Reject ダイアログが表示される
- `SafeToAutoRun=true` フラグを送っても無効
- IDE 再起動後も改善しない

## 根本原因

`run_command` ステップレンダラーに `useEffect` フックが欠落。

```javascript
// 存在するコード (ドロップダウン変更時のみ発火):
onChange = useCallback(_ => {
  setPolicy(_), _ === EAGER && confirm(true)
}, [])

// 欠落しているコード (マウント時に保存済みポリシーをチェックすべき):
useEffect(() => {
  if (policy === EAGER && !secureMode) confirm(true)
}, [])
```

→ ドロップダウンを手動変更した **その瞬間のコマンド** だけ自動承認されるが、新コマンドステップのマウント時にポリシーが参照されない。

## DB 内の設定保存状態 (調査結果)

| 保存場所 | キー | 値 | 意味 |
|----------|------|-----|------|
| `state.vscdb` → `antigravityUnifiedStateSync.agentPreferences` | `terminalAutoExecutionPolicySentinelKey` | protobuf varint **3** | EAGER (Always run) ✅ |
| `state.vscdb` → `antigravityUnifiedStateSync.overrideStore` | `secureModeEnabledSentinelKey` | protobuf varint **0** | Secure Mode OFF ✅ |
| `storage.json` | `hasTerminalAutoExecutionPolicyMigrated` | `true` | 移行済みフラグ |

→ 設定は正しく永続化されているが、UI レンダラーがマウント時に読み出さない。

## DB の構造メモ

- `state.vscdb` は SQLite DB、テーブル `ItemTable(key TEXT, value BLOB)` の KV ストア
- 設定値は protobuf エンコード → base64 でシリアライズ
- IDE 実行中はファイルロック → コピーして読み取り
- 全 811 行のキーが存在

## 修正方法

### better-antigravity パッチャー (コミュニティ製)

- **GitHub**: https://github.com/Kanezal/better-antigravity
- **Extension**: Open VSX で "Better Antigravity" を検索
- **CLI**: `npx better-antigravity auto-run`

パッチ対象ファイル:
1. `workbench.desktop.main.js` (+42 bytes)
2. `jetskiAgent` 内の対応ファイル (+42 bytes)

```bash
# 適用
npx better-antigravity auto-run

# 状態確認
npx better-antigravity auto-run --check

# 元に戻す
npx better-antigravity auto-run --revert
```

### ⚠️ 注意事項

- **Antigravity アップデート後にパッチが消える** → 再適用が必要
- パッチ適用後は IDE 再起動が必要
- バックアップは自動作成される

## 調査経路

1. `storage.json` 確認 → 移行フラグのみ、実値なし
2. `state.vscdb` SQLite 解析 → `cached.terminalAutoExecutionPolicy` キーが不在と判明
3. `unifiedStateSync.agentPreferences` の protobuf デコード → varint 3 (EAGER) 保存済み確認
4. ソースコード (`workbench.desktop.main.js`) 解析 → `useEffect` 欠落を特定
5. 外部検索 → 既知の広範なバグ + コミュニティパッチャー発見
6. `npx better-antigravity auto-run --check` → `NOT PATCHED (patchable)` 確認
7. パッチ適用 → `SafeToAutoRun=true` で承認なし実行を検証 ✅
