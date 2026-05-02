import os
import sys
from pathlib import Path

# /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/.env
env_path = Path(__file__).parent.parent.parent.parent / ".env"

try:
    from dotenv import load_dotenv
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass
