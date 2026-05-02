import sys
import traceback

try:
    import hermeneus.src.executor
    print("Success")
except Exception as e:
    print(f"Exception: {type(e).__name__}: {e}")
    traceback.print_exc()

