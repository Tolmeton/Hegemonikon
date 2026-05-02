#!/usr/bin/env bash
# agq-check — Antigravity Quota Checker v3
# Language Server の内部 API から全モデルの quota 情報を取得する
#
# 使い方:
#   ./agq-check.sh                       # デフォルト (hegemonikon workspace)
#   ./agq-check.sh filemaker             # 他のワークスペース
#   ./agq-check.sh --raw                 # JSON 生データ
#   ./agq-check.sh --json                # jq フォーマット済み
#   ./agq-check.sh --snapshot boot       # BOOT 時スナップショット保存
#   ./agq-check.sh --snapshot bye        # BYE 時スナップショット保存
#   ./agq-check.sh --delta               # BOOT→BYE デルタ計算
#
# 依存: curl, jq, ps, grep, ss
#
# 起源: 2026-02-12 AntigravityQuotaWatcher ソースコード解析
# API: /exa.language_server_pb.LanguageServerService/GetUserStatus

set -euo pipefail

# --- 引数解析 ---
RAW_MODE=false
JSON_MODE=false
SNAPSHOT_PHASE=""
DELTA_MODE=false
WS_FILTER="oikos"
SNAPSHOT_DIR="/tmp"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --raw) RAW_MODE=true; shift ;;
    --json) JSON_MODE=true; shift ;;
    --snapshot)
      SNAPSHOT_PHASE="$2"
      shift 2 ;;
    --delta) DELTA_MODE=true; shift ;;
    --help|-h)
      echo "Usage: agq-check.sh [workspace] [--raw|--json|--snapshot boot|bye|--delta]"
      exit 0 ;;
    *) WS_FILTER="$1"; shift ;;
  esac
done

# --- Delta モード: スナップショット間の差分を計算 ---
if $DELTA_MODE; then
  BOOT_FILE="$SNAPSHOT_DIR/agq_boot.json"
  BYE_FILE="$SNAPSHOT_DIR/agq_bye.json"
  if [[ ! -f "$BOOT_FILE" ]]; then
    echo "❌ Boot スナップショットが見つかりません: $BOOT_FILE" >&2
    exit 1
  fi
  if [[ ! -f "$BYE_FILE" ]]; then
    echo "❌ Bye スナップショットが見つかりません: $BYE_FILE" >&2
    exit 1
  fi
  BOOT_PC=$(jq -r '.pc' "$BOOT_FILE")
  BOOT_FC=$(jq -r '.fc' "$BOOT_FILE")
  BOOT_TS=$(jq -r '.timestamp' "$BOOT_FILE")
  BYE_PC=$(jq -r '.pc' "$BYE_FILE")
  BYE_FC=$(jq -r '.fc' "$BYE_FILE")
  BYE_TS=$(jq -r '.timestamp' "$BYE_FILE")
  DELTA_PC=$((BOOT_PC - BYE_PC))
  DELTA_FC=$((BOOT_FC - BYE_FC))
  BOOT_CLAUDE=$(jq -r '.claude_opus_pct' "$BOOT_FILE")
  BYE_CLAUDE=$(jq -r '.claude_opus_pct' "$BYE_FILE")
  DELTA_CLAUDE=$(echo "$BOOT_CLAUDE - $BYE_CLAUDE" | bc 2>/dev/null || echo "?")
  echo "┌─────────────────────────────────────────────────┐"
  echo "│ 📊 Session Metrics (BOOT→BYE)"
  echo "├─────────────────────────────────────────────────┤"
  echo "│ 🕐 Boot: $BOOT_TS"
  echo "│ 🕐 Bye:  $BYE_TS"
  echo "├─────────────────────────────────────────────────┤"
  printf "│ 💳 Prompt Credits: %s → %s (Δ -%s)\n" "$BOOT_PC" "$BYE_PC" "$DELTA_PC"
  printf "│ 🌊 Flow Credits:   %s → %s (Δ -%s)\n" "$BOOT_FC" "$BYE_FC" "$DELTA_FC"
  printf "│ 🧠 Claude Opus:    %s%% → %s%% (Δ -%s%%)\n" "$BOOT_CLAUDE" "$BYE_CLAUDE" "$DELTA_CLAUDE"
  echo "└─────────────────────────────────────────────────┘"
  exit 0
fi

# --- Step 1: ls_daemon.json から接続情報を取得 ---
# IDE LS は gRPC API に応答しないため、ls_daemon (Docker/ローカル) のみを使用する
DAEMON_JSON="${LS_DAEMON_INFO_PATH:-$HOME/.gemini/antigravity/ls_daemon.json}"

if [[ ! -f "$DAEMON_JSON" ]]; then
  echo "❌ ls_daemon.json が見つかりません: $DAEMON_JSON" >&2
  echo "   ls_daemon が起動しているか確認してください: systemctl status ls-daemon" >&2
  exit 1
fi

# JSON から全エントリを読み取り、順に試行する
NUM_ENTRIES=$(jq 'length' "$DAEMON_JSON" 2>/dev/null || echo 0)

if [[ "$NUM_ENTRIES" -eq 0 ]]; then
  echo "❌ ls_daemon.json にエントリがありません" >&2
  exit 1
fi

# --- Step 2: 各エントリに対して GetUserStatus を試行 ---
JSON=""
for i in $(seq 0 $((NUM_ENTRIES - 1))); do
  PORT=$(jq -r ".[$i].port" "$DAEMON_JSON")
  CSRF=$(jq -r ".[$i].csrf" "$DAEMON_JSON")
  IS_HTTPS=$(jq -r ".[$i].is_https // false" "$DAEMON_JSON")
  SOURCE=$(jq -r ".[$i].source // \"unknown\"" "$DAEMON_JSON")

  if [[ "$IS_HTTPS" == "true" ]]; then
    PROTO="https"
    CURL_OPTS="-sk"
  else
    PROTO="http"
    CURL_OPTS="-s"
  fi

  result=$(curl $CURL_OPTS --max-time 3 -X POST \
    -H "Content-Type: application/json" \
    -H "X-Codeium-Csrf-Token: $CSRF" \
    -H "Connect-Protocol-Version: 1" \
    -d '{"metadata":{"ideName":"antigravity","extensionName":"antigravity","locale":"en"}}' \
    "$PROTO://127.0.0.1:$PORT/exa.language_server_pb.LanguageServerService/GetUserStatus" 2>/dev/null || true)

  if [[ -n "$result" && "$result" == *"userStatus"* ]]; then
    JSON="$result"
    break
  fi
done

if [[ -z "$JSON" ]]; then
  echo "❌ ls_daemon.json の全エントリ ($NUM_ENTRIES 件) で Quota 取得に失敗しました" >&2
  echo "   ls_daemon プロセスが生きているか確認してください" >&2
  exit 1
fi

# --- Step 3: スナップショット保存 or 表示 ---
if [[ -n "$SNAPSHOT_PHASE" ]]; then
  PC=$(echo "$JSON" | jq -r '.userStatus.planStatus.availablePromptCredits // 0')
  FC=$(echo "$JSON" | jq -r '.userStatus.planStatus.availableFlowCredits // 0')
  CLAUDE_PCT=$(echo "$JSON" | jq -r '
    [.userStatus.cascadeModelConfigData.clientModelConfigs[]
     | select(.label | test("Claude Opus"))
     | (.quotaInfo.remainingFraction // 0) * 100 | round] | first // 0')
  SNAP_FILE="$SNAPSHOT_DIR/agq_${SNAPSHOT_PHASE}.json"
  jq -n \
    --arg ts "$(date -Iseconds)" \
    --argjson pc "$PC" \
    --argjson fc "$FC" \
    --argjson claude "$CLAUDE_PCT" \
    --arg phase "$SNAPSHOT_PHASE" \
    '{timestamp: $ts, phase: $phase, pc: $pc, fc: $fc, claude_opus_pct: $claude}' \
    > "$SNAP_FILE"
  echo "📸 Snapshot saved: $SNAP_FILE (PC=$PC, FC=$FC, Claude=$CLAUDE_PCT%)"
  exit 0
fi

if $RAW_MODE; then
  echo "$JSON"
  exit 0
fi

if $JSON_MODE; then
  echo "$JSON" | jq '.'
  exit 0
fi

# jq 存在チェック
if ! command -v jq &>/dev/null; then
  echo "⚠️  jq がインストールされていません。--raw モードで表示します。"
  echo "$JSON"
  exit 0
fi

NAME=$(echo "$JSON" | jq -r '.userStatus.name // "unknown"')
PLAN=$(echo "$JSON" | jq -r '.userStatus.userTier.name // "unknown"')
PC=$(echo "$JSON" | jq -r '.userStatus.planStatus.availablePromptCredits // 0')
MPC=$(echo "$JSON" | jq -r '.userStatus.planStatus.planInfo.monthlyPromptCredits // 0')
FC=$(echo "$JSON" | jq -r '.userStatus.planStatus.availableFlowCredits // 0')
MFC=$(echo "$JSON" | jq -r '.userStatus.planStatus.planInfo.monthlyFlowCredits // 0')

echo "┌─────────────────────────────────────────────────┐"
echo "│ ⚡ Antigravity Quota — $NAME"
echo "│ 📋 Plan: $PLAN"
echo "├─────────────────────────────────────────────────┤"
printf "│ 💳 Prompt Credits: %s / %s\n" "$PC" "$MPC"
printf "│ 🌊 Flow Credits:   %s / %s\n" "$FC" "$MFC"
echo "├─────────────────────────────────────────────────┤"

echo "$JSON" | jq -r '
  .userStatus.cascadeModelConfigData.clientModelConfigs[]
  | select(.quotaInfo)
  | {label, frac: (.quotaInfo.remainingFraction // 0), reset: .quotaInfo.resetTime}
  | "│ \(if .frac >= 0.8 then "🟢" elif .frac >= 0.4 then "🟡" elif .frac >= 0.1 then "🟠" else "🔴" end) \(.label): \(.frac * 100 | round)%  ↻ \(.reset[11:16])"
'

echo "└─────────────────────────────────────────────────┘"
echo "📅 $(date '+%Y-%m-%d %H:%M:%S')"
