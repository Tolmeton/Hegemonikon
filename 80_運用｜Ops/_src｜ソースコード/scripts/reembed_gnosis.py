"""
⚠️ DEPRECATED — FAISS 移行完了により削除。

旧: LanceDB 1024d (BGE-M3) → 768d (Vertex AI text-embedding-004) の移行スクリプト。
後継: reindex_gnosis.py (FAISS バックエンド対応)

このスクリプトは LanceDB 時代のワンショット移行ツールであり、
FAISS 移行後は不要。再インデックスが必要な場合は reindex_gnosis.py を使用。
"""

import sys


def main():
    print("⚠️  reembed_gnosis.py は DEPRECATED です。")
    print("    代わりに reindex_gnosis.py を使用してください。")
    sys.exit(1)


if __name__ == "__main__":
    main()
