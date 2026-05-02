import logging
import time
logging.basicConfig(level=logging.DEBUG)
print("1. import start")
from hermeneus.src.macro_executor import execute_macro
print("2. execute_macro start")
start = time.time()
res = execute_macro("/noe-", "test")
print("3. execute_macro end, took", time.time() - start)
print(res.summary())
