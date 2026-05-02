import requests
import time
import argparse
import logging
from pprint import pprint

BASE_URL = "http://127.0.0.1:9696/api"

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_endpoint(name, func, *args, **kwargs):
    logger.info(f"--- Testing {name} ---")
    try:
        r = func(*args, **kwargs)
        logger.info(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            # truncate output if large
            if 'diff' in data and len(data['diff']) > 500:
                data['diff'] = data['diff'][:500] + '... [TRUNCATED]'
            if 'files' in data and len(data['files']) > 5:
                data['files'] = data['files'][:5] + ['... [TRUNCATED]']
            pprint(data)
            return True
        else:
            logger.error(f"Failed: {r.text}")
            return False
    except Exception as e:
        logger.exception(f"Error during {name}: {e}")
        return False

def main():
    test_path = "~/Sync/oikos/_test_rename_e2e.txt"
    test_path_new = "~/Sync/oikos/_test_renamed_e2e.txt"

    # 1. Write file
    test_endpoint("files_write", requests.post, f"{BASE_URL}/files/write", json={
        "path": test_path,
        "content": "Hello, E2E Test!"
    })

    # 2. Read file to verify
    test_endpoint("files_read (before rename)", requests.get, f"{BASE_URL}/files/read", params={
        "path": test_path
    })

    # 3. Rename file
    test_endpoint("files_rename", requests.post, f"{BASE_URL}/files/rename", json={
        "path": test_path,
        "new_path": test_path_new
    })

    # 4. Read renamed file
    test_endpoint("files_read (after rename)", requests.get, f"{BASE_URL}/files/read", params={
        "path": test_path_new
    })

    # 5. Delete file
    test_endpoint("files_delete", requests.post, f"{BASE_URL}/files/delete", json={
        "path": test_path_new
    })

    # 6. Read deleted file (should fail)
    logger.info("--- Testing files_read (expecting 404) ---")
    r = requests.get(f"{BASE_URL}/files/read", params={"path": test_path_new})
    logger.info(f"Status: {r.status_code} (Expected 404/403)")

    # 7. Git status
    test_endpoint("git/status", requests.get, f"{BASE_URL}/git/status", params={
        "repo": "/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
    })

    # 8. Git diff
    test_endpoint("git/diff", requests.get, f"{BASE_URL}/git/diff", params={
        "repo": "/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
    })

if __name__ == "__main__":
    main()
