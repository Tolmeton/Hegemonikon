# PROOF: mekhane/ergasterion/typos/debug_validate.py
# PURPOSE: ergasterion モジュールの debug_validate
from typos_integrate import generate_prompt
from typos import validate_file
import time

slug = f"integration_test_adapter_{int(time.time())}"
role = "Tester"
goal = "Verify adapter"

filepath, _ = generate_prompt(slug, role, goal)
valid, msg = validate_file(str(filepath))
print(f"valid: {valid}, msg: {msg}")
