import json
import glob
from pathlib import Path

traj_files = glob.glob("C:/Users/makar/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/experiments/experiments/evaluation/verified/20240402_sweagent_gpt4/trajs/*.traj")

out_file = "C:/Users/makar/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/experiments/swebench_verified_real_traj.jsonl"

with open(out_file, "w") as f_out:
    for tf in traj_files:
        instance_id = Path(tf).stem
        with open(tf, "r", encoding="utf-8") as f_in:
            data = json.load(f_in)
        
        trajectory = data.get("trajectory", []) if isinstance(data, dict) else data
        
        record = {
            "instance_id": instance_id,
            "trajectory": trajectory
        }
        f_out.write(json.dumps(record) + "\n")
