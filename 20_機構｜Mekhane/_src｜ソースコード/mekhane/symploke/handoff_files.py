#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/symploke/ handoff 列挙規則の単一化が必要
# PURPOSE: Handoff ファイル列挙と日時抽出の共通ユーティリティ
"""Shared utilities for canonical handoff file discovery."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


def extract_handoff_datetime(path: Path) -> datetime:
    """Extract the logical handoff timestamp from a filename."""
    name = path.name

    match = re.match(r"handoff_(\d{4}-\d{2}-\d{2})_(\d{4})\.(?:md|typos)$", name)
    if match:
        date_str, time_str = match.groups()
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H%M")

    match = re.search(r"_(\d{8})\.(?:md|typos)$", name)
    if match:
        return datetime.strptime(match.group(1), "%Y%m%d")

    match = re.search(r"_(\d{4}-\d{2}-\d{2})\.(?:md|typos)$", name)
    if match:
        return datetime.strptime(match.group(1), "%Y-%m-%d")

    try:
        return datetime.fromtimestamp(path.stat().st_mtime)
    except OSError:
        return datetime.min


def list_handoff_files(base_dir: Path) -> list[Path]:
    """Return canonical handoff files below ``base_dir`` newest-first."""
    if not base_dir.exists():
        return []

    files = list(base_dir.rglob("handoff_*.md"))
    files.extend(base_dir.rglob("handoff_*.typos"))
    return sorted(files, key=extract_handoff_datetime, reverse=True)
