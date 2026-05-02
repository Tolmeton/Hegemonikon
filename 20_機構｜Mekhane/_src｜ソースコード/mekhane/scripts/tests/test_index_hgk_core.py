# PROOF: mekhane/scripts/tests/test_index_hgk_core.py
# PURPOSE: hgk_core index script のローカルロジック回帰を検証する

from pathlib import Path
from unittest.mock import MagicMock

from mekhane.anamnesis.chunker import MarkdownChunker
from mekhane.scripts.index_hgk_core import build_heading_path, build_records, diff_states


def test_build_heading_path_keeps_document_title():
    assert build_heading_path("Kernel 公理", "定義") == "Kernel 公理 > 定義"
    assert build_heading_path("Kernel 公理", "Introduction") == "Kernel 公理"


def test_diff_states_detects_changed_and_removed():
    previous = {
        "/a.md": {"mtime": 1.0, "size": 10},
        "/b.md": {"mtime": 1.0, "size": 20},
    }
    current = {
        "/a.md": {"mtime": 2.0, "size": 10},
        "/c.md": {"mtime": 1.0, "size": 30},
    }

    changed, removed = diff_states(previous, current)

    assert changed == ["/a.md", "/c.md"]
    assert removed == ["/b.md"]


def test_build_records_preserves_source_metadata(tmp_path: Path):
    source = tmp_path / "kernel.md"
    source.write_text("# Kernel\n\n## 定義\n\n忘却は構造の脱落である。", encoding="utf-8")

    chunker = MarkdownChunker(max_chars=2000, overlap=200)
    embedder = MagicMock()
    embedder.embed_batch.return_value = [[0.1, 0.2, 0.3]]

    records, chunk_counts = build_records([source], chunker, embedder)

    assert chunk_counts[str(source.resolve())] == 1
    assert len(records) == 1
    assert records[0]["source_path"] == str(source.resolve())
    assert records[0]["doc_id"] == str(source.resolve())
    assert records[0]["heading_path"] == "Kernel > 定義"
    assert records[0]["chunk_type"] == "hgk_core"
