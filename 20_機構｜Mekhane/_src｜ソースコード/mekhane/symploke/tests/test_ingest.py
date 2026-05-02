# PROOF: [L3/テスト] <- mekhane/symploke/tests/test_ingest.py 対象モジュールが存在→検証が必要→test_ingest が担う
"""
Tests for Kairos and Sophia ingest scripts
"""

import pytest
import tempfile
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


# PURPOSE: Tests for kairos_ingest.py
class TestKairosIngest:
    """Tests for kairos_ingest.py"""

    # PURPOSE: Test parsing of Handoff v2 YAML + Markdown format
    def test_parse_handoff_v2_format(self):
        """Test parsing of Handoff v2 YAML + Markdown format"""
        from mekhane.symploke.kairos_ingest import parse_handoff

        # Create temp handoff file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("""---
session_handoff:
  version: "2.0"
  timestamp: "2026-01-27T16:50:00+09:00"
  session_id: "test-session"
---

## 🔄 Hegemonikón Session Handoff v2

**主題**: Test task description

This is the summary content.
""")
            f.flush()
            temp_path = Path(f.name)

        try:
            doc = parse_handoff(temp_path)
            assert doc is not None
            assert doc.id.startswith("handoff-")
            assert "Test task description" in doc.metadata.get("primary_task", "")
        finally:
            temp_path.unlink()

    # PURPOSE: Test parsing handoff without YAML metadata
    def test_parse_handoff_missing_yaml(self):
        """Test parsing handoff without YAML metadata"""
        from mekhane.symploke.kairos_ingest import parse_handoff

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Simple handoff\n\nJust some content.")
            f.flush()
            temp_path = Path(f.name)

        try:
            doc = parse_handoff(temp_path)
            # Should still create a document with content
            assert doc is not None
            assert "Simple handoff" in doc.content
        finally:
            temp_path.unlink()

    # PURPOSE: Test that handoff files are returned sorted by date
    def test_get_handoff_files_sorted(self):
        """Test that handoff files are returned sorted by date"""
        from mekhane.symploke import kairos_ingest as ki

        # This test uses actual session directory
        files = ki.get_handoff_files()

        # Should return list (may be empty if no handoffs)
        assert isinstance(files, list)

        # If files exist, check they're sorted in reverse order (newest first)
        if len(files) > 1:
            for i in range(len(files) - 1):
                assert ki._extract_date_from_filename(files[i]) >= ki._extract_date_from_filename(files[i + 1])

    # PURPOSE: Test recursive monthly directories + .typos support for handoffs
    def test_get_handoff_files_recurses_and_supports_typos(self, monkeypatch, tmp_path):
        """Monthly subdirectories and .typos files should be included in newest-first order."""
        from mekhane.symploke import kairos_ingest as ki

        root_md = tmp_path / "handoff_2026-04-09_2346.md"
        monthly_dir = tmp_path / "2026-04"
        monthly_dir.mkdir()
        nested_typos = monthly_dir / "handoff_2026-04-10_2307.typos"

        root_md.write_text("# old", encoding="utf-8")
        nested_typos.write_text("# new", encoding="utf-8")

        monkeypatch.setattr(ki, "HANDOFF_DIR", tmp_path)

        files = ki.get_handoff_files()

        assert files == [nested_typos, root_md]


# PURPOSE: Tests for sophia_ingest.py
class TestSophiaIngest:
    """Tests for sophia_ingest.py"""

    # PURPOSE: Test parsing KI directory with metadata.json
    def test_parse_ki_with_metadata(self):
        """Test parsing KI directory with metadata.json"""
        from mekhane.symploke.sophia_ingest import parse_ki_directory

        # Create temp KI directory
        with tempfile.TemporaryDirectory() as tmpdir:
            ki_path = Path(tmpdir)

            # Create metadata.json
            import json

            metadata = {"name": "Test KI", "summary": "This is a test knowledge item"}
            (ki_path / "metadata.json").write_text(json.dumps(metadata))

            # Create artifacts directory with a file
            artifacts_dir = ki_path / "artifacts"
            artifacts_dir.mkdir()
            (artifacts_dir / "overview.md").write_text("# Overview\n\nTest content.")

            docs = parse_ki_directory(ki_path)

            assert len(docs) == 1
            assert docs[0].id.startswith("ki-")
            assert "Test KI" in docs[0].content
            assert docs[0].metadata.get("ki_name") == "Test KI"

    # PURPOSE: Test parsing KI with only metadata, no artifacts
    def test_parse_ki_without_artifacts(self):
        """Test parsing KI with only metadata, no artifacts"""
        from mekhane.symploke.sophia_ingest import parse_ki_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            ki_path = Path(tmpdir)

            import json

            metadata = {
                "name": "Summary Only KI",
                "summary": "Just a summary, no artifacts",
            }
            (ki_path / "metadata.json").write_text(json.dumps(metadata))

            docs = parse_ki_directory(ki_path)

            # Should create doc from summary even without artifacts
            assert len(docs) == 1
            assert "Summary Only KI" in docs[0].content

    # PURPOSE: Test parsing KI without metadata.json
    def test_parse_ki_missing_metadata(self):
        """Test parsing KI without metadata.json"""
        from mekhane.symploke.sophia_ingest import parse_ki_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            ki_path = Path(tmpdir)
            # No metadata.json

            docs = parse_ki_directory(ki_path)

            # Should return empty list
            assert docs == []

    # PURPOSE: Test parsing KI with nested artifact directories (rglob)
    def test_parse_ki_nested_artifacts(self):
        """Test parsing KI with nested artifact directories (rglob)"""
        from mekhane.symploke.sophia_ingest import parse_ki_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            ki_path = Path(tmpdir)

            import json

            metadata = {"name": "Nested KI", "summary": "KI with nested subdirectories"}
            (ki_path / "metadata.json").write_text(json.dumps(metadata))

            # Create nested artifact structure
            artifacts_dir = ki_path / "artifacts"
            artifacts_dir.mkdir()
            (artifacts_dir / "overview.md").write_text("# Overview")

            # Create subdirectory with more artifacts
            subdir = artifacts_dir / "implementation"
            subdir.mkdir()
            (subdir / "details.md").write_text("# Implementation Details")
            (subdir / "guide.md").write_text("# Guide")

            # Deeper nesting
            deep = subdir / "examples"
            deep.mkdir()
            (deep / "example1.md").write_text("# Example 1")

            docs = parse_ki_directory(ki_path)

            # Should find all 4 .md files via rglob
            assert len(docs) == 4

            # Check doc IDs include subdirectory paths
            doc_ids = [d.id for d in docs]
            assert any("implementation-details" in id for id in doc_ids)
            assert any("implementation-examples-example1" in id for id in doc_ids)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
