# PROOF: [L2/インフラ] <- hermeneus/src/__main__.py Hermēneus エントリーポイント
"""
Hermēneus __main__.py

python -m hermeneus 対応
"""

from .cli import main
import sys

if __name__ == "__main__":
    sys.exit(main())
