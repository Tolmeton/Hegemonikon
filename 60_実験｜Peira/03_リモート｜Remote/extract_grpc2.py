import sys
import os
import time
import subprocess
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mekhane.ochema.ls_manager import NonStandaloneLSManager
from mekhane.ochema.antigravity_client import AntigravityClient

def run_and_dump():
    mgr = NonStandaloneLSManager(workspace_id='dump_test_2')
    is_running = True
    try:
        info = mgr.start()
        print(f"LS Started: pid={info.pid}")
        client = AntigravityClient(ls_info=info)
        unique_str = "HACK_PAYLOAD_XYZ_987654321_END"
        
        def spam_req():
            while is_running:
                try:
                    # Send continuously
                    client.ask(unique_str)
                except:
                    pass
                time.sleep(0.1)
                
        t = threading.Thread(target=spam_req)
        t.start()
        
        # Give it enough time to be fully in LS memory
        time.sleep(2.0)
        
        print(f"Dumping memory of PID {info.pid}...")
        subprocess.run(['sudo', 'gcore', '-o', '/tmp/ls_core_2', str(info.pid)], check=True)
        print("Dump complete.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        is_running = False
        mgr.stop()

if __name__ == '__main__':
    run_and_dump()
