"""Schema helpers for the Phase alpha wiki layer."""

from __future__ import annotations

from datetime import datetime

import yaml
from pydantic import BaseModel, Field

__all__ = ["WikiPage"]


def _split_front_matter(text: str) -> tuple[dict, str]:
    """Split Markdown text into YAML front matter and body."""
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        raise ValueError("Markdown text is missing YAML front matter")

    lines = normalized.split("\n")
    closing_index = None
    for index in range(1, len(lines)):
        if lines[index] == "---":
            closing_index = index
            break
    if closing_index is None:
        raise ValueError("Markdown text has unterminated YAML front matter")

    front_matter = "\n".join(lines[1:closing_index])
    body = "\n".join(lines[closing_index + 1 :]).lstrip("\n")
    metadata = yaml.safe_load(front_matter) or {}
    if not isinstance(metadata, dict):
        raise ValueError("YAML front matter must decode to a mapping")
    return metadata, body


def _parse_body(body: str) -> tuple[str, list[str]]:
    """Extract representative text and member bullets from the body."""
    normalized = body.replace("\r\n", "\n").strip()
    if not normalized:
        return "", []

    heading = "\n## Members\n"
    if heading in f"\n{normalized}\n":
        representative_text, members_block = normalized.split("## Members", 1)
        representative_text = representative_text.rstrip()
        members = [
            line[2:].strip()
            for line in members_block.strip().splitlines()
            if line.strip().startswith("- ")
        ]
        return representative_text, members

    return normalized, []


class WikiPage(BaseModel):
    """Minimal persisted wiki page for the Phantasia field lint layer."""

    cluster_id: str
    members: list[str]
    source_types: list[str]
    representative_text: str
    title: str
    created_at: datetime
    last_updated: datetime
    in_degree: int = 0
    out_degree: int = 0
    tags: list[str] = Field(default_factory=list)

    def to_markdown(self) -> str:
        """Serialize the page into YAML front matter plus a compact body."""
        metadata = self.model_dump(
            mode="json",
            exclude={"members", "representative_text"},
        )
        front_matter = yaml.safe_dump(
            metadata,
            allow_unicode=True,
            sort_keys=False,
        ).strip()
        members_block = "\n".join(f"- {member}" for member in self.members)
        return (
            f"---\n{front_matter}\n---\n"
            f"{self.representative_text}\n\n## Members\n{members_block}\n"
        )

    @classmethod
    def from_markdown(cls, text: str) -> "WikiPage":
        """Deserialize a page from Markdown with YAML front matter."""
        metadata: dict
        body: str

        try:
            import frontmatter
        except ImportError:
            metadata, body = _split_front_matter(text)
        else:
            post = frontmatter.loads(text)
            metadata = dict(post.metadata)
            body = post.content

        representative_text, members = _parse_body(body)
        payload = dict(metadata)
        payload["representative_text"] = representative_text
        payload["members"] = members
        return cls.model_validate(payload)
