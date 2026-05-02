# PROOF: [L2/インフラ] <- mekhane/dendron/__main__.py
"""
Dendron package entry point.

Enables: python -m mekhane.dendron check [PATH]
"""

from .cli import main

if __name__ == "__main__":
    main()
