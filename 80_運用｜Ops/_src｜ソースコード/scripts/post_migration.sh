#!/bin/bash
# Gnōsis post-migration: セッション再インデックス + FTS 再構築
# handoff-index 完了後に実行される
set -e

cd ~/oikos/01_ヘゲモニコン｜Hegemonikon
export PYTHONPATH=.

echo "=== [1/3] ROM Index ==="
.venv/bin/python -u mekhane/anamnesis/cli.py rom-index 2>&1 | tee -a /tmp/gnosis_reindex.log

echo "=== [2/3] Build FTS Index ==="
.venv/bin/python -u mekhane/anamnesis/cli.py build-fts 2>&1 | tee -a /tmp/gnosis_reindex.log

echo "=== [3/3] Quick Search Test ==="
.venv/bin/python -u mekhane/anamnesis/cli.py search "Free Energy Principle" --limit 3 2>&1 | tee -a /tmp/gnosis_reindex.log

echo "=== DONE ==="
date
