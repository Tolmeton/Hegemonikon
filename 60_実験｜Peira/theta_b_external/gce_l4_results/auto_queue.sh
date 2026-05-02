#!/bin/bash
echo "Starting auto queue..."
date

echo "Waiting for T-034 (PID 2563) to finish..."
while kill -0 2563 2>/dev/null; do sleep 60; done
echo "T-034 finished at $(date)"

echo "Starting T-058 (Gemma4 Phase B2)..."
nohup python3 /home/makaron8426/nonlinear_probe.py --model gemma4 --dataset /home/makaron8426/dataset_v3.json --cache-dir /home/makaron8426/.hidden_cache > /home/makaron8426/phase_b2_gemma4_run.log 2>&1 &
PID_T058=$!
echo "T-058 started with PID $PID_T058 at $(date)"

echo "Waiting for T-008 (PID 13075) to finish..."
while kill -0 13075 2>/dev/null; do sleep 60; done
echo "T-008 finished at $(date)"

echo "Waiting for T-058 (PID $PID_T058) to finish..."
while kill -0 $PID_T058 2>/dev/null; do sleep 60; done
echo "T-058 finished at $(date)"

echo "All tasks finished. Shutting down VM in 1 minute..."
sleep 60
sudo shutdown -h now
