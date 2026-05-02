# PROOF: mekhane/anamnesis/tests/test_chunker.py
# PURPOSE: anamnesis モジュールの chunker に対するテスト
import pytest
from mekhane.anamnesis.chunker import MarkdownChunker

class TestMarkdownChunker:

    def test_chunk_empty_text(self):
        chunker = MarkdownChunker()
        chunks = chunker.chunk("", source_id="test_id")
        assert len(chunks) == 0

    def test_chunk_no_headers(self):
        chunker = MarkdownChunker(max_chars=100)
        text = "This is a simple text without any headers. It should be treated as a single section."
        chunks = chunker.chunk(text, source_id="doc1", title="Doc Title")
        assert len(chunks) == 1
        assert chunks[0]["parent_id"] == "doc1"
        assert chunks[0]["section_title"] == ""
        assert "[Doc Title]" in chunks[0]["text"]
        assert "This is a simple text" in chunks[0]["text"]

    def test_chunk_with_headers(self):
        chunker = MarkdownChunker()
        text = """# Main Title

Introduction text goes here.

## Section 1
This is the first section.

### Sub-section 1.1
This is a subsection.

## Section 2
This is the second section."""
        
        chunks = chunker.chunk(text, source_id="doc2", title="Main Doc")
        
        assert len(chunks) == 4
        
        # Introduction
        assert chunks[0]["section_title"] == "Introduction"
        assert "[Main Doc > Introduction]" in chunks[0]["text"]
        
        # Section 1
        assert chunks[1]["section_title"] == "Section 1"
        assert "[Main Doc > Section 1]" in chunks[1]["text"]
        assert "This is the first section." in chunks[1]["text"]
        
        # Sub-section 1.1
        assert chunks[2]["section_title"] == "Sub-section 1.1"
        assert "This is a subsection." in chunks[2]["text"]

        # Section 2
        assert chunks[3]["section_title"] == "Section 2"
        assert "This is the second section." in chunks[3]["text"]

    def test_chunk_length_split(self):
        # Small max_chars to force splitting within a section
        chunker = MarkdownChunker(max_chars=50, overlap=10)
        text = "## Long Section\n" + "A" * 60 + "\n\n" + "B" * 60
        
        chunks = chunker.chunk(text, source_id="doc3")
        
        # Section should be split into multiple chunks
        assert len(chunks) > 1
        assert chunks[0]["section_title"] == "Long Section"
        assert chunks[1]["section_title"] == "Long Section"
        
        # verify parent key preservation
        assert chunks[0]["parent_id"] == "doc3"
        assert chunks[1]["parent_id"] == "doc3"
        assert chunks[0]["id"] != chunks[1]["id"]
