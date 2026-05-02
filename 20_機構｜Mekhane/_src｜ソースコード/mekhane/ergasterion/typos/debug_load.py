# PROOF: mekhane/ergasterion/typos/debug_load.py
# PURPOSE: ergasterion モジュールの debug_load
from typos_integrate import generate_prompt, load_prompt
import json
import time

slug = f"integration_test_adapter_{int(time.time())}"
role = "Tester"
goal = "Verify adapter"

filepath, _ = generate_prompt(slug, role, goal)
print(f"Generated file: {filepath}")

data = load_prompt(filepath)
print(json.dumps(data["parsed"], indent=2))
