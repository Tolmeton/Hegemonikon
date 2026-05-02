import asyncio
from hermeneus.src.macro_executor import MacroExecutor

def run():
    executor = MacroExecutor()
    # 意図的に environment を破壊する
    executor.walker.environment = None
    try:
        executor.execute("/boe+", context="testing")
        print("Success (should NOT happen if fully integrated)")
    except Exception as e:
        print(f"Failed as expected: {e}")

if __name__ == "__main__":
    run()
