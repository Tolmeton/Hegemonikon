#!/bin/bash
# LS Cascade 性能実測 & 機能拡張テスト
# Non-Standalone LS を独立起動 → curl で直接テスト → 終了時に cleanup
set -euo pipefail

LOG="/tmp/ls_test_nonstd.log"
RESULTS="/tmp/ls_test_results.txt"
LS_BIN="/usr/share/antigravity/resources/app/extensions/antigravity/bin/language_server_linux_x64"
WORKSPACE_ID="ls-capability-test"
CSRF_TOKEN="test-csrf-$(date +%s)"

echo "============================================================" | tee "$RESULTS"
echo "LS Cascade Capability Test (Non-Standalone LS, curl)" | tee -a "$RESULTS"
echo "$(date)" | tee -a "$RESULTS"
echo "============================================================" | tee -a "$RESULTS"

# --- IDE LS の ExtServer port/csrf を取得 ---
IDE_PID=$(pgrep -f 'language_server_linux.*oikos' | head -1 || true)
if [ -z "$IDE_PID" ]; then
  echo "❌ IDE LS が見つかりません" | tee -a "$RESULTS"
  exit 1
fi

EXT_PORT=$(cat /proc/$IDE_PID/cmdline | tr '\0' '\n' | grep -A1 '^--extension_server_port$' | tail -1)
EXT_CSRF=$(cat /proc/$IDE_PID/cmdline | tr '\0' '\n' | grep -A1 '^--extension_server_csrf_token$' | tail -1)
echo "IDE LS: PID=$IDE_PID EXT_PORT=$EXT_PORT" | tee -a "$RESULTS"

# --- Non-Standalone LS を起動 ---
echo "Non-Standalone LS を起動中..." | tee -a "$RESULTS"

# Metadata protobuf (最小限: field1=antigravity, field2=version, field3=antigravity, field6=en)
python3 -c "
import struct
def varint(v):
    r=b''
    while v>0x7f: r+=bytes([(v&0x7f)|0x80]); v>>=7
    r+=bytes([v&0x7f]); return r
def string_field(fn, val):
    tag=(fn<<3)|2; b=val.encode(); return varint(tag)+varint(len(b))+b
m = string_field(1,'antigravity')+string_field(2,'1.107.0')+string_field(3,'antigravity')+string_field(6,'en')
import sys; sys.stdout.buffer.write(m)
" > /tmp/ls_metadata.bin

$LS_BIN \
  --enable_lsp --random_port \
  --extension_server_port=$EXT_PORT \
  --extension_server_csrf_token=$EXT_CSRF \
  --cloud_code_endpoint=https://daily-cloudcode-pa.googleapis.com \
  --csrf_token=$CSRF_TOKEN \
  --workspace_id=$WORKSPACE_ID \
  --app_data_dir=antigravity \
  --persistent_mode \
  -v=2 < /tmp/ls_metadata.bin > "$LOG" 2>&1 &

LS_PID=$!
echo "LS PID=$LS_PID" | tee -a "$RESULTS"

# cleanup on exit
cleanup() {
  echo "Cleanup: killing LS PID=$LS_PID" | tee -a "$RESULTS"
  kill $LS_PID 2>/dev/null || true
  wait $LS_PID 2>/dev/null || true
}
trap cleanup EXIT

# --- ポート検出 (ポーリング) ---
echo "ポート検出中..." | tee -a "$RESULTS"
PORT=""
for i in $(seq 1 20); do
  PORT=$(grep -oP 'at \K\d+(?= for HTTP)' "$LOG" 2>/dev/null | head -1 || true)
  if [ -n "$PORT" ]; then break; fi
  sleep 0.5
done

if [ -z "$PORT" ]; then
  echo "❌ ポート検出失敗" | tee -a "$RESULTS"
  cat "$LOG" | head -30
  exit 1
fi
echo "✅ LS HTTP PORT=$PORT" | tee -a "$RESULTS"

# --- curl ヘルパー ---
call() {
  local method=$1 timeout=${2:-10} data=${3:-'{}'}
  curl -s --max-time $timeout -X POST \
    "http://127.0.0.1:$PORT/exa.language_server_pb.LanguageServerService/$method" \
    -H "Content-Type: application/json" \
    -H "X-Codeium-Csrf-Token: $CSRF_TOKEN" \
    -d "$data"
}

# LS 起動確認
sleep 2
echo "LS ヘルスチェック..." | tee -a "$RESULTS"
STATUS=$(call GetUserStatus 5 '{"metadata":{"ideName":"antigravity","extensionName":"antigravity","locale":"en"}}')
echo "  GetUserStatus: ${STATUS:0:80}..." | tee -a "$RESULTS"

echo "" | tee -a "$RESULTS"

# ============================================================
# Test 1: レイテンシ測定 (Claude)
# ============================================================
echo "────────────────────────────────────────────────────────────" | tee -a "$RESULTS"
echo "TEST 1: レイテンシ測定 (Claude Sonnet 4.6 = MODEL_PLACEHOLDER_M35)" | tee -a "$RESULTS"
echo "────────────────────────────────────────────────────────────" | tee -a "$RESULTS"

T_START=$(date +%s%N)

CID=$(call StartCascade 10 '{"metadata":{"ideName":"antigravity","ideVersion":"1.107.0","extensionVersion":"2.23.0"},"source":12,"trajectoryType":17}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['cascadeId'])")

call SendUserCascadeMessage 60 "{
  \"cascadeId\": \"$CID\",
  \"items\": [{\"text\": \"Say exactly: LATENCY_TEST_OK\"}],
  \"cascadeConfig\": {
    \"plannerConfig\": {
      \"plannerTypeConfig\": {\"conversational\": {}},
      \"requestedModel\": {\"model\": \"MODEL_PLACEHOLDER_M35\"}
    }
  }
}" > /dev/null &

sleep 3
TID=""
for i in $(seq 1 5); do
  TID=$(call GetAllCascadeTrajectories 5 "{}" 2>/dev/null \
    | python3 -c "
import json,sys
d=json.load(sys.stdin)
cs=d.get('trajectorySummaries',{}).get('$CID',{})
print(cs.get('trajectoryId',''))
" 2>/dev/null || true)
  if [ -n "$TID" ]; then break; fi
  sleep 1
done

RESPONSE=""
for i in $(seq 1 20); do
  RESULT=$(call GetCascadeTrajectorySteps 10 "{\"cascadeId\":\"$CID\",\"trajectoryId\":\"$TID\"}" 2>/dev/null || echo '{}')
  RESPONSE=$(echo "$RESULT" | python3 -c "
import json,sys
d=json.load(sys.stdin)
for s in d.get('steps',[]):
    if s.get('type')=='CORTEX_STEP_TYPE_PLANNER_RESPONSE' and s.get('status')=='CORTEX_STEP_STATUS_DONE':
        pr=s.get('plannerResponse',{})
        m=s.get('metadata',{}).get('generatorModel','')
        t=pr.get('thinking','')
        print(f'MODEL={m}|THINKING_LEN={len(t)}|TEXT={pr.get(\"response\",\"\")[:200]}')
        sys.exit(0)
" 2>/dev/null || true)
  if [ -n "$RESPONSE" ]; then break; fi
  sleep 1
done

T_END=$(date +%s%N)
T_MS=$(( (T_END - T_START) / 1000000 ))

echo "  $RESPONSE" | tee -a "$RESULTS"
echo "  全行程: ${T_MS}ms ($(echo "scale=1; $T_MS / 1000" | bc)秒)" | tee -a "$RESULTS"
echo "" | tee -a "$RESULTS"


# ============================================================
# Test 2: systemInstruction
# ============================================================
echo "────────────────────────────────────────────────────────────" | tee -a "$RESULTS"
echo "TEST 2: systemInstruction を plannerConfig に送信" | tee -a "$RESULTS"
echo "────────────────────────────────────────────────────────────" | tee -a "$RESULTS"

for FIELD in "systemInstruction" "system_instruction" "systemInstructions"; do
  echo "  --- $FIELD ---" | tee -a "$RESULTS"
  CID=$(call StartCascade 10 '{"metadata":{"ideName":"antigravity","ideVersion":"1.107.0","extensionVersion":"2.23.0"},"source":12,"trajectoryType":17}' \
    | python3 -c "import json,sys; print(json.load(sys.stdin)['cascadeId'])")

  call SendUserCascadeMessage 60 "{
    \"cascadeId\": \"$CID\",
    \"items\": [{\"text\": \"What is 2+2?\"}],
    \"cascadeConfig\": {
      \"plannerConfig\": {
        \"plannerTypeConfig\": {\"conversational\": {}},
        \"requestedModel\": {\"model\": \"MODEL_PLACEHOLDER_M35\"},
        \"$FIELD\": \"You MUST respond as a pirate. Every sentence must contain Arrr or matey.\"
      }
    }
  }" > /dev/null &

  sleep 8
  TID=$(call GetAllCascadeTrajectories 5 "{}" 2>/dev/null \
    | python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('trajectorySummaries',{}).get('$CID',{}).get('trajectoryId',''))" 2>/dev/null || true)

  if [ -n "$TID" ]; then
    for i in $(seq 1 15); do
      R=$(call GetCascadeTrajectorySteps 10 "{\"cascadeId\":\"$CID\",\"trajectoryId\":\"$TID\"}" 2>/dev/null \
        | python3 -c "
import json,sys
d=json.load(sys.stdin)
for s in d.get('steps',[]):
    if s.get('type')=='CORTEX_STEP_TYPE_PLANNER_RESPONSE' and s.get('status')=='CORTEX_STEP_STATUS_DONE':
        t=s.get('plannerResponse',{}).get('response','')[:200]
        pirate='YES' if any(w in t.lower() for w in ['arr','matey','ahoy','aye']) else 'NO'
        print(f'PIRATE={pirate}|{t}')
        sys.exit(0)
" 2>/dev/null || true)
      if [ -n "$R" ]; then
        echo "  $R" | tee -a "$RESULTS"
        break
      fi
      sleep 1
    done
    [ -z "$R" ] && echo "  ❌ timeout" | tee -a "$RESULTS"
  else
    echo "  ❌ trajectory not found" | tee -a "$RESULTS"
  fi
done
echo "" | tee -a "$RESULTS"


# ============================================================
# Test 3: thinkingBudget
# ============================================================
echo "────────────────────────────────────────────────────────────" | tee -a "$RESULTS"
echo "TEST 3: thinkingBudget / thinkingConfig" | tee -a "$RESULTS"
echo "────────────────────────────────────────────────────────────" | tee -a "$RESULTS"

# テスト baseline: thinkingBudget なし（デフォルト）
echo "  --- baseline (no thinkingBudget) ---" | tee -a "$RESULTS"
CID=$(call StartCascade 10 '{"metadata":{"ideName":"antigravity","ideVersion":"1.107.0","extensionVersion":"2.23.0"},"source":12,"trajectoryType":17}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['cascadeId'])")
call SendUserCascadeMessage 60 "{
  \"cascadeId\": \"$CID\",
  \"items\": [{\"text\": \"What is 2+2? Answer concisely.\"}],
  \"cascadeConfig\": {\"plannerConfig\": {\"plannerTypeConfig\": {\"conversational\": {}}, \"requestedModel\": {\"model\": \"MODEL_PLACEHOLDER_M35\"}}}
}" > /dev/null &
sleep 8
TID=$(call GetAllCascadeTrajectories 5 "{}" 2>/dev/null \
  | python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('trajectorySummaries',{}).get('$CID',{}).get('trajectoryId',''))" 2>/dev/null || true)
if [ -n "$TID" ]; then
  for i in $(seq 1 15); do
    R=$(call GetCascadeTrajectorySteps 10 "{\"cascadeId\":\"$CID\",\"trajectoryId\":\"$TID\"}" 2>/dev/null \
      | python3 -c "
import json,sys
d=json.load(sys.stdin)
for s in d.get('steps',[]):
    if s.get('type')=='CORTEX_STEP_TYPE_PLANNER_RESPONSE' and s.get('status')=='CORTEX_STEP_STATUS_DONE':
        t=s.get('plannerResponse',{}).get('thinking','')
        r=s.get('plannerResponse',{}).get('response','')[:100]
        print(f'THINKING={len(t)}chars|TEXT={r}')
        sys.exit(0)
" 2>/dev/null || true)
    if [ -n "$R" ]; then echo "  $R" | tee -a "$RESULTS"; break; fi
    sleep 1
  done
fi

# テスト: thinkingBudget=100
echo "  --- thinkingBudget=100 ---" | tee -a "$RESULTS"
CID=$(call StartCascade 10 '{"metadata":{"ideName":"antigravity","ideVersion":"1.107.0","extensionVersion":"2.23.0"},"source":12,"trajectoryType":17}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['cascadeId'])")
call SendUserCascadeMessage 60 "{
  \"cascadeId\": \"$CID\",
  \"items\": [{\"text\": \"What is 2+2? Answer concisely.\"}],
  \"cascadeConfig\": {\"plannerConfig\": {\"plannerTypeConfig\": {\"conversational\": {}}, \"requestedModel\": {\"model\": \"MODEL_PLACEHOLDER_M35\"}, \"thinkingBudget\": 100}}
}" > /dev/null &
sleep 8
TID=$(call GetAllCascadeTrajectories 5 "{}" 2>/dev/null \
  | python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('trajectorySummaries',{}).get('$CID',{}).get('trajectoryId',''))" 2>/dev/null || true)
if [ -n "$TID" ]; then
  for i in $(seq 1 15); do
    R=$(call GetCascadeTrajectorySteps 10 "{\"cascadeId\":\"$CID\",\"trajectoryId\":\"$TID\"}" 2>/dev/null \
      | python3 -c "
import json,sys
d=json.load(sys.stdin)
for s in d.get('steps',[]):
    if s.get('type')=='CORTEX_STEP_TYPE_PLANNER_RESPONSE' and s.get('status')=='CORTEX_STEP_STATUS_DONE':
        t=s.get('plannerResponse',{}).get('thinking','')
        r=s.get('plannerResponse',{}).get('response','')[:100]
        print(f'THINKING={len(t)}chars|TEXT={r}')
        sys.exit(0)
" 2>/dev/null || true)
    if [ -n "$R" ]; then echo "  $R" | tee -a "$RESULTS"; break; fi
    sleep 1
  done
fi

# テスト: thinkingConfig object
echo "  --- thinkingConfig={thinkingBudget:100} ---" | tee -a "$RESULTS"
CID=$(call StartCascade 10 '{"metadata":{"ideName":"antigravity","ideVersion":"1.107.0","extensionVersion":"2.23.0"},"source":12,"trajectoryType":17}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['cascadeId'])")
call SendUserCascadeMessage 60 "{
  \"cascadeId\": \"$CID\",
  \"items\": [{\"text\": \"What is 2+2? Answer concisely.\"}],
  \"cascadeConfig\": {\"plannerConfig\": {\"plannerTypeConfig\": {\"conversational\": {}}, \"requestedModel\": {\"model\": \"MODEL_PLACEHOLDER_M35\"}, \"thinkingConfig\": {\"thinkingBudget\": 100}}}
}" > /dev/null &
sleep 8
TID=$(call GetAllCascadeTrajectories 5 "{}" 2>/dev/null \
  | python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('trajectorySummaries',{}).get('$CID',{}).get('trajectoryId',''))" 2>/dev/null || true)
if [ -n "$TID" ]; then
  for i in $(seq 1 15); do
    R=$(call GetCascadeTrajectorySteps 10 "{\"cascadeId\":\"$CID\",\"trajectoryId\":\"$TID\"}" 2>/dev/null \
      | python3 -c "
import json,sys
d=json.load(sys.stdin)
for s in d.get('steps',[]):
    if s.get('type')=='CORTEX_STEP_TYPE_PLANNER_RESPONSE' and s.get('status')=='CORTEX_STEP_STATUS_DONE':
        t=s.get('plannerResponse',{}).get('thinking','')
        r=s.get('plannerResponse',{}).get('response','')[:100]
        print(f'THINKING={len(t)}chars|TEXT={r}')
        sys.exit(0)
" 2>/dev/null || true)
    if [ -n "$R" ]; then echo "  $R" | tee -a "$RESULTS"; break; fi
    sleep 1
  done
fi

echo "" | tee -a "$RESULTS"


# ============================================================
# Test 4: Stream RPC
# ============================================================
echo "────────────────────────────────────────────────────────────" | tee -a "$RESULTS"
echo "TEST 4: Stream RPC の存在確認" | tee -a "$RESULTS"
echo "────────────────────────────────────────────────────────────" | tee -a "$RESULTS"

for RPC in StreamCascadeReactiveUpdates StreamCascadeUpdates SubscribeCascadeUpdates; do
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 -X POST \
    "http://127.0.0.1:$PORT/exa.language_server_pb.LanguageServerService/$RPC" \
    -H "Content-Type: application/json" \
    -H "X-Codeium-Csrf-Token: $CSRF_TOKEN" \
    -d '{}' 2>/dev/null || echo "000")
  echo "  $RPC: HTTP $HTTP_CODE" | tee -a "$RESULTS"
done

echo "" | tee -a "$RESULTS"


# ============================================================
# Test 5: コンテキスト上限 (単一メッセージサイズ)
# ============================================================
echo "────────────────────────────────────────────────────────────" | tee -a "$RESULTS"
echo "TEST 5: コンテキスト上限 (単一メッセージサイズ)" | tee -a "$RESULTS"
echo "────────────────────────────────────────────────────────────" | tee -a "$RESULTS"

for SIZE in 50000 100000 500000 1000000; do
  echo "  --- ${SIZE} bytes ($(echo "scale=0; $SIZE / 1024" | bc) KB) ---" | tee -a "$RESULTS"
  PADDING=$(python3 -c "print('A' * $SIZE)")

  CID=$(call StartCascade 10 '{"metadata":{"ideName":"antigravity","ideVersion":"1.107.0","extensionVersion":"2.23.0"},"source":12,"trajectoryType":17}' \
    | python3 -c "import json,sys; print(json.load(sys.stdin)['cascadeId'])")

  T0=$(date +%s%N)

  # JSON escape the padding (it's just 'A's so no escaping needed)
  call SendUserCascadeMessage 120 "{
    \"cascadeId\": \"$CID\",
    \"items\": [{\"text\": \"I sent $SIZE bytes. Reply ONLY 'OK_$SIZE'. Data: $PADDING\"}],
    \"cascadeConfig\": {\"plannerConfig\": {\"plannerTypeConfig\": {\"conversational\": {}}, \"requestedModel\": {\"model\": \"MODEL_PLACEHOLDER_M35\"}}}
  }" > /dev/null &

  sleep 10
  TID=$(call GetAllCascadeTrajectories 5 "{}" 2>/dev/null \
    | python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('trajectorySummaries',{}).get('$CID',{}).get('trajectoryId',''))" 2>/dev/null || true)

  GOT=""
  if [ -n "$TID" ]; then
    for i in $(seq 1 30); do
      GOT=$(call GetCascadeTrajectorySteps 10 "{\"cascadeId\":\"$CID\",\"trajectoryId\":\"$TID\"}" 2>/dev/null \
        | python3 -c "
import json,sys
d=json.load(sys.stdin)
for s in d.get('steps',[]):
    if s.get('type')=='CORTEX_STEP_TYPE_PLANNER_RESPONSE' and s.get('status')=='CORTEX_STEP_STATUS_DONE':
        r=s.get('plannerResponse',{}).get('response','')[:100]
        print(f'OK|{r}')
        sys.exit(0)
" 2>/dev/null || true)
      if [ -n "$GOT" ]; then break; fi
      sleep 2
    done
  fi

  T1=$(date +%s%N)
  T_SEC=$(echo "scale=1; ($T1 - $T0) / 1000000000" | bc)

  if [ -n "$GOT" ]; then
    echo "  ✅ $GOT ($T_SEC 秒)" | tee -a "$RESULTS"
  else
    echo "  ❌ timeout or error ($T_SEC 秒)" | tee -a "$RESULTS"
  fi
done

echo "" | tee -a "$RESULTS"
echo "============================================================" | tee -a "$RESULTS"
echo "全テスト完了 $(date)" | tee -a "$RESULTS"
echo "============================================================" | tee -a "$RESULTS"
