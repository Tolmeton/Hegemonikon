"""
Blind Judge via Cursor Agent CLI (GPT-5.4)
cursor agent -p を使ってバッチ採点する。
"""
import json
import subprocess
import sys
import time
from pathlib import Path

BATCH_DIR = Path(__file__).parent / "results" / "batch"
JUDGE_DIR = Path(__file__).parent / "results" / "blind_judge_gpt54"
OUTPUT_TRUNCATE = 6000
MODEL = "gpt-5.4-xhigh"

RUBRIC = """Score this reasoning text on 5 dimensions (1-5 each). Be STRICT - 5 is exceptional and rare. Most good outputs score 3-4.

D1 Reasoning depth: 1=fact listing only / 3=1-2 why levels / 5=3+ why levels reaching root mechanism
D2 Premise explicitness: 1=no premises / 3=some stated / 5=AXIOM(unchangeable) vs ASSUMPTION(changeable) explicitly classified
D3 Structural coherence: 1=many logical leaps / 3=main chain holds / 5=each step necessitates next, conclusion inevitable
D4 Confidence disclosure: 1=all assertive / 3=some confidence variation / 5=explicit confidence labels (high/med/low or %) on major claims
D5 Actionability: 1=nothing follows / 3=1-2 follow-ups suggested / 5=3+ concrete extensions visible

Return ONLY valid JSON, no other text:
{"D1":int,"D2":int,"D3":int,"D4":int,"D5":int,"total":sum,"one_line":"max feature in one sentence"}"""


def judge_one(filepath: Path) -> dict | None:
    data = json.loads(filepath.read_text(encoding="utf-8"))
    output_text = data["output"][:OUTPUT_TRUNCATE]
    uid = filepath.stem
    condition = uid[0]
    task_id = uid.split("_")[1]

    prompt = f"""{RUBRIC}

--- TEXT TO SCORE (ID: {uid}) ---
{output_text}
--- END ---

Return ONLY the JSON."""

    try:
        result = subprocess.run(
            ["cursor", "agent", "-p",
             "--model", MODEL,
             "--mode", "ask",
             "--yolo", "--trust",
             "--output-format", "text",
             prompt],
            capture_output=True, text=True, timeout=180,
            cwd=str(Path(__file__).parent),
        )
        raw = result.stdout
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT")
        return None

    # JSON を抽出 (最後の {...} を探す)
    json_str = None
    for line in reversed(raw.split("\n")):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                json.loads(line)
                json_str = line
                break
            except json.JSONDecodeError:
                continue

    if not json_str:
        print(f"  JSON parse failed. Raw tail: {raw[-300:]}")
        return None

    scores = json.loads(json_str)
    scores["uid"] = uid
    scores["condition"] = condition
    scores["task_id"] = task_id
    scores["input_tokens"] = 0
    scores["output_tokens"] = 0
    return scores


def main():
    JUDGE_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(f for f in BATCH_DIR.glob("*.json") if f.name != "batch_analysis.json")
    total = len(files)
    print(f"Cursor Agent Blind Judge: {total} files / model: {MODEL}")
    print(f"Output: {JUDGE_DIR}\n")

    for i, f in enumerate(files):
        uid = f.stem
        out_path = JUDGE_DIR / f.name

        if out_path.exists():
            print(f"[{i+1}/{total}] {uid} → skip (exists)")
            continue

        print(f"[{i+1}/{total}] {uid} → scoring...", end=" ", flush=True)
        scores = judge_one(f)
        if scores:
            out_path.write_text(json.dumps(scores, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"done (total={scores['total']})")
        else:
            print("FAILED")

        time.sleep(0.5)

    print(f"\nDone. Results in {JUDGE_DIR}")


if __name__ == "__main__":
    main()
