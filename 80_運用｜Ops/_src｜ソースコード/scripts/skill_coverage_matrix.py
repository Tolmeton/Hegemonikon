#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path
from mekhane.peira.theorem_activity import generate_report, THEOREM_WORKFLOWS

SKILL_DIR = Path("nous/skills")

def get_skill_line_count(wf_id: str) -> int:
    """SKILL.md の行数を取得 (存在しない場合は0)"""
    # WF_TO_SKILL mapping (from macro_executor)
    WF_TO_SKILL = {
        "noe": "V01", "bou": "V02", "zet": "V03", "ene": "V04",
        "ske": "V05", "sag": "V06", "pei": "V07", "tek": "V08",
        "kat": "V09", "epo": "V10", "pai": "V11", "dok": "V12",
        "lys": "V13", "ops": "V14", "akr": "V15", "arc": "V16",
        "beb": "V17", "ele": "V18", "kop": "V19", "dio": "V20",
        "hyp": "V21", "prm": "V22", "ath": "V23", "par": "V24",
    }
    skill_id = WF_TO_SKILL.get(wf_id)
    if not skill_id:
        return 0
        
    for skill_path in SKILL_DIR.rglob("SKILL.md"):
        if skill_path.parent.name.startswith(skill_id.lower()) or skill_path.parent.name.startswith(skill_id):
            with open(skill_path, 'r') as f:
                return sum(1 for line in f)
    return 0

def main():
    # 発生頻度データを json で取得
    report_json = generate_report(as_json=True)
    report_data = json.loads(report_json)
    
    matrix = []
    for th in report_data["theorems"]:
        wf_id = th["id"]
        count = th["count"]
        lines = get_skill_line_count(wf_id)
        
        # Priority logic: 
        # High priority = High usage count AND Low line count (< 800)
        priority = 0
        if lines < 800:
            priority = count * (800 - lines) / 800
            
        matrix.append({
            "wf_id": wf_id,
            "label": th["label"],
            "count": count,
            "lines": lines,
            "priority": priority
        })
        
    matrix.sort(key=lambda x: x["priority"], reverse=True)
    
    print("| WF | 定理名 | 発動回数 | SKILL.md 行数 | 優先度スコア |")
    print("|:---|:-------|---------:|--------------:|----------:|")
    for item in matrix:
        status = "⚠️ 薄い" if item["lines"] < 800 else "✅ 充足"
        if item["lines"] == 0:
            status = "❌ 未作成"
        print(f"| `/{item['wf_id']}` | {item['label']} | {item['count']}回 | {item['lines']}行 ({status}) | {item['priority']:.1f} |")

if __name__ == "__main__":
    main()
