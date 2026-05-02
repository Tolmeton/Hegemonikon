#!/bin/bash
export LOG_FILE=/tmp/grpc_server.log
python3 /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/experiments/grpc_generic_server.py 36989 > $LOG_FILE 2>&1 &
SERVER_PID=$!
sleep 1
echo "Starting Language Server..."
/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/bin/language_server_linux_x64 \
    --extension_server_port=36989 \
    --minloglevel=0 \
    --v=1 &
LS_PID=$!
sleep 5
echo "Killing Language Server..."
kill $LS_PID
echo "Killing gRPC Server..."
kill $SERVER_PID
cat $LOG_FILE
