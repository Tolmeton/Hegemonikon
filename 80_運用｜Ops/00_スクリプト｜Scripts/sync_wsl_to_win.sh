#!/usr/bin/env bash
# PROOF: WSL → Windows ワンショット整理移行スクリプト
# PURPOSE: WSL oikos から Windows へ「意味のあるファイルのみ」を rsync で移行する
#
# 使い方:
#   bash sync_wsl_to_win.sh          # dry-run（何がコピーされるか表示）
#   bash sync_wsl_to_win.sh --apply  # 実行
#
# 前提:
#   - WSL (Debian/Ubuntu) から実行
#   - rsync がインストール済み
#   - Windows 側の宛先ディレクトリが存在する

set -euo pipefail

# ─── 設定 ───────────────────────────────────────
SRC="$HOME/Sync/oikos/"
DST="/mnt/c/Users/makar/Sync/oikos/"
MODE="dry-run"

if [[ "${1:-}" == "--apply" ]]; then
    MODE="apply"
fi

# ─── 除外リスト ─────────────────────────────────
# 環境依存 (OS固有バイナリ)
EXCLUDES=(
    --exclude='.venv/'
    --exclude='.venv-*/'

    # キャッシュ・再生成可能
    --exclude='__pycache__/'
    --exclude='*.pyc'
    --exclude='node_modules/'
    --exclude='.pytest_cache/'
    --exclude='.ruff_cache/'
    --exclude='.playwright-mcp/'

    # Git (.git は Windows 側で git clone する)
    --exclude='.git/'
    --exclude='.gitmodules'

    # LanceDB (デバイス固有。双方向同期と非互換)
    --exclude='*.lance'
    --exclude='lancedb/'

    # Syncthing メタデータ
    --exclude='.stversions/'
    --exclude='.stfolder'
    --exclude='*.sync-conflict-*'
    --exclude='.syncthing.*.tmp'
    --exclude='~syncthing~*'

    # 機密 (手動管理)
    --exclude='.env'
    --exclude='.env.*'
    --exclude='.secrets/'

    # IDE ローカルデータ
    --exclude='.claude/'
    --exclude='.gemini/state.json'
    --exclude='.gemini/antigravity/implicit/'
    --exclude='.gemini/antigravity/logs/'
    --exclude='.gemini/antigravity/installation_id'
    --exclude='.gemini/antigravity/browser_recordings/'
    --exclude='.gemini/antigravity/code_tracker/'

    # ロックファイル
    --exclude='*.lock'

    # macOS ゴミ
    --exclude='__MACOSX/'
    --exclude='.DS_Store'
)

# ─── メイン ──────────────────────────────────────
echo "╔══════════════════════════════════════════╗"
echo "║  WSL → Windows oikos 整理移行           ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  SRC: $SRC"
echo "  DST: $DST"
echo "  MODE: $MODE"
echo ""

# 宛先ディレクトリの存在確認
if [[ ! -d "$DST" ]]; then
    echo "[ERROR] 宛先が存在しません: $DST"
    echo "  Windows 側で mkdir を実行してください"
    exit 1
fi

if [[ "$MODE" == "dry-run" ]]; then
    echo "── dry-run: コピーされるファイル一覧 ──"
    echo ""
    rsync -avhn --stats \
        "${EXCLUDES[@]}" \
        "$SRC" "$DST" 2>&1 | tail -20
    echo ""
    echo "─────────────────────────────────────────"
    echo "実行するには: bash $0 --apply"
else
    echo "── 実行中 ──"
    echo ""
    rsync -avh --progress --stats \
        "${EXCLUDES[@]}" \
        "$SRC" "$DST"
    echo ""
    echo "── 完了 ──"
    echo ""
    echo "次のステップ:"
    echo "  1. Windows Terminal で git clone:"
    echo "     cd C:\\Users\\makar\\Sync\\oikos\\01_ヘゲモニコン｜Hegemonikon"
    echo "     git clone https://github.com/Tolmeton/Hegemonikon.git ."
    echo "     ※ 既にファイルがあるので init + remote add + fetch が安全:"
    echo "       git init"
    echo "       git remote add origin https://github.com/Tolmeton/Hegemonikon.git"
    echo "       git fetch origin"
    echo "       git reset origin/main"
    echo ""
    echo "  2. Windows 側で .venv を再作成:"
    echo "     python -m venv C:\\hgk\\.venv"
    echo "     C:\\hgk\\.venv\\Scripts\\pip install -r C:\\hgk\\requirements.txt"
    echo ""
    echo "  3. 構造整理が完了したら Syncthing を設定"
fi
