```typos
#prompt rom-6ls-pool-deploy
#syntax: v8
#depth: L2

<:role: ROM — 6アカウント LS プール構築セッションの蒸留 :>

<:goal: LS プール6垢デプロイの全知見を次セッションで即復元可能な形で保存する :>

<:context:
  - [knowledge] 完了: 6アカウント LS プール (systemd 常駐化)
    vault.json: Tolmeton, movement, rairaixoxoxo, makaron, nous, hraiki
    各 LS にアカウント固有 state DB (state_nonstd_{account}.vscdb) を生成
    ラウンドロビンルーティングで Cursor リクエストを分散
    30分ごとにアカウント別トークンリフレッシュ
    合計メモリ: ~1.2GB (GALLERIA 16GB の 7%)

  - [knowledge] 修正ファイル (2ファイル):
    ls_manager.py:
      - NonStandaloneLSManager に account パラメータ追加
      - start() でアカウント固有 state DB を生成・トークン注入
      - ensure_token_fresh() を @staticmethod → インスタンスメソッドに変更
    ls_daemon.py:
      - _load_accounts() で vault.json から6アカウント読込
      - account_assignments[] でラウンドロビン割当
      - ls_daemon.json にアカウント名を記録
      - _loop() のリフレッシュをアカウント別に変更
      - _write_info() を enumerate() に修正 (idx 未定義バグ修正)
      - start()/_load_accounts() の構造分離 (コードが混入していたバグ修正)

  - [knowledge] デプロイ構成 (GALLERIA 100.83.204.102):
    systemd user service: ~/.config/systemd/user/hgk-ls-daemon.service
    LS プロセス: 6つ (各 ~190MB RSS)
    ls_daemon.json: ~/.gemini/antigravity/ls_daemon.json (6エントリ + account フィールド)
    state DB: ~/.config/Antigravity/User/globalStorage/state_nonstd_{account}.vscdb × 6
    旧 IDE LS (PID=2071769): 停止済み
    旧 hgk-ls.service: 停止 + 無効化済み
    check_ls.py: /tmp/check_ls.py (LS 死活 + Quota + メモリ確認)

  - [knowledge] 検証コマンド:
    LS プール状態: ssh 100.83.204.102 "python3 /tmp/check_ls.py"
    systemd: ssh 100.83.204.102 "systemctl --user status hgk-ls-daemon.service"
    ログ: ssh 100.83.204.102 "journalctl --user -u hgk-ls-daemon.service -n 20"

  - [knowledge] 未解決: hgk-hub.service が CancelledError でクラッシュループ
    ochema MCP サーバー自体は active (port 9701)
    hub (port 9700) がクラッシュしているため Cursor → gateway → ochema 経路が不通
    LS プールの直接 HTTP テストは全6LS OK (check_ls.py で検証済み)
    → hub のクラッシュ修復 or hub 迂回 (ochema 直接接続) が次のタスク

  - [knowledge] OAuth 認証パターン (将来のトークン追加用):
    NotePC で oauth_local.py を実行 → ブラウザ認証 → SCP で GALLERIA に転送
    コマンド: python C:\Users\makar\tmp\oauth_local.py {account_name} {email}
    vault 登録は oauth_local.py が自動で vault.json に追記

  - [knowledge] 設計判断の根拠:
    なぜアカウント固有 state DB?: 全 LS が同じ state_nonstd.vscdb を共有すると1トークンしか入らない
    なぜ ensure_token_fresh() をインスタンスメソッドに?: アカウント別リフレッシュに account + db_path が必要
    provision_state_db() は既に account/db_path パラメータを持っていた → 呼び出し側の変更のみ
/context:>
```
