from __future__ import annotations
# PROOF: mekhane/periskope/cognition/context_compressor.py
# PURPOSE: periskope モジュールの context_compressor
"""
Context Compressor — LS-inspired checkpoint summarization for dialectic context.

Reverse-engineered from Antigravity Language Server's context management:
  - Recent messages: kept verbatim
  - Old messages: compressed into structured summaries (checkpoints)
  - Budget: dynamic, based on task complexity (here: research depth)

Applied to DialecticEngine's inter-engine communication:
  - Recent opponent findings: kept verbatim for accurate reasoning
  - Old findings: compressed via LLM into a compact summary
  - Budget: depth-aware (L1: 5K, L2: 20K, L3: 40K chars)

```
┌───────────────────────────────────────────────────┐
│  [Checkpoint Summary]  ← compressed old findings  │
│  ─────────────────────                             │
│  [Verbatim iter N-1]   ← recent, full text         │
│  [Verbatim iter N]     ← most recent, full text    │
└───────────────────────────────────────────────────┘
```
"""


import logging
from dataclasses import dataclass, field
from mekhane.ochema.model_defaults import FLASH

logger = logging.getLogger(__name__)


# Depth-aware context budgets (chars)
CONTEXT_BUDGET = {
    1: 5_000,     # L1 Quick: 1-2 iters, small context
    2: 20_000,    # L2 Standard: 3-5 iters
    3: 40_000,    # L3 Deep: 5-10 iters, large context
}

# How many recent entries to keep verbatim (never compress)
VERBATIM_WINDOW = {
    1: 2,     # L1: keep last 2 entries
    2: 4,     # L2: keep last 4 entries
    3: 6,     # L3: keep last 6 entries
}


@dataclass
class ContextEntry:
    """One entry in the dialectic context buffer."""

    iteration: int
    source: str  # "thesis" or "antithesis"
    text: str
    is_checkpoint: bool = False  # True if this is a compressed summary

    @property
    def char_count(self) -> int:
        return len(self.text)


@dataclass
class DialecticContextBuffer:
    """LS-pattern context manager for inter-engine communication.

    Maintains a rolling buffer of opponent findings with:
      - Depth-aware budget limits
      - Automatic checkpoint compression when budget is exceeded
      - Recent entries kept verbatim, old entries compressed

    Usage:
        buf = DialecticContextBuffer(depth=2)
        buf.append(1, "antithesis", "Finding: X is contradicted by Y...")
        buf.append(2, "antithesis", "Finding: Z supports alternative...")
        context_str = buf.render()  # Get current context for reasoning
        await buf.compress_if_needed()  # Compress old entries if over budget
    """

    depth: int = 2
    entries: list[ContextEntry] = field(default_factory=list)
    _checkpoint_text: str = ""  # Compressed summary of old entries

    @property
    def budget(self) -> int:
        """Current context budget in chars."""
        return CONTEXT_BUDGET.get(self.depth, 20_000)

    @property
    def verbatim_window(self) -> int:
        """Number of recent entries to keep verbatim."""
        return VERBATIM_WINDOW.get(self.depth, 4)

    @property
    def total_chars(self) -> int:
        """Total chars in buffer (checkpoint + entries)."""
        return len(self._checkpoint_text) + sum(e.char_count for e in self.entries)

    @property
    def is_over_budget(self) -> bool:
        return self.total_chars > self.budget

    def append(self, iteration: int, source: str, text: str) -> None:
        """Add a new entry to the buffer."""
        if not text or len(text.strip()) < 10:
            return
        self.entries.append(ContextEntry(
            iteration=iteration,
            source=source,
            text=text,
        ))
        logger.debug(
            "DialecticContext: append iter=%d src=%s chars=%d total=%d/%d",
            iteration, source, len(text), self.total_chars, self.budget,
        )

    async def compress_if_needed(self) -> bool:
        """Compress old entries if over budget. Returns True if compression occurred.

        Pattern (LS reverse-engineering):
          1. Split entries into [old | recent] by verbatim_window
          2. Summarize old entries + existing checkpoint via LLM
          3. Replace old entries with new checkpoint
          4. Keep recent entries verbatim
        """
        if not self.is_over_budget:
            return False

        if len(self.entries) <= self.verbatim_window:
            # Can't compress — all entries are in the verbatim window.
            # Truncate the oldest entries as a last resort.
            self._truncate_oldest()
            return True

        # Split: old entries to compress, recent to keep
        split_idx = len(self.entries) - self.verbatim_window
        old_entries = self.entries[:split_idx]
        recent_entries = self.entries[split_idx:]

        # Build text to compress
        compress_input = self._build_compress_input(old_entries)

        # LLM compression
        try:
            compressed = await self._llm_compress(compress_input)
            if compressed:
                # Validation: check if conflict markers are preserved
                if "CONFLICT" not in compressed and "⚔️" not in compressed:
                    logger.warning(
                        "DialecticContext: LLM compression omitted CONFLICT markers. "
                        "Potential information loss during compression."
                    )
                
                self._checkpoint_text = compressed
                self.entries = recent_entries
                logger.info(
                    "DialecticContext: compressed %d old entries → %d chars checkpoint. "
                    "Keeping %d recent. Total: %d/%d",
                    len(old_entries), len(compressed),
                    len(recent_entries), self.total_chars, self.budget,
                )
                return True
        except Exception as e:  # noqa: BLE001
            logger.warning("DialecticContext compression failed: %s", e)

        # Fallback: truncate oldest entries
        self._truncate_oldest()
        return True

    def _build_compress_input(self, old_entries: list[ContextEntry]) -> str:
        """Build input for LLM compression."""
        parts = []
        if self._checkpoint_text:
            parts.append(f"[Previous Checkpoint]\n{self._checkpoint_text}")
        for entry in old_entries:
            parts.append(
                f"[Iter {entry.iteration} / {entry.source}]\n{entry.text}"
            )
        return "\n\n---\n\n".join(parts)

    async def _llm_compress(self, text: str) -> str | None:
        """Compress text via LLM (LS-style checkpoint summarization)."""
        from mekhane.periskope.cognition._llm import llm_ask

        prompt = (
            "You are compressing research context for an ongoing dialectical analysis.\n"
            "Summarize the following opponent findings into a compact checkpoint.\n\n"
            "Rules:\n"
            "- Preserve ALL factual claims and counter-evidence\n"
            "- Preserve source attributions (URLs, paper names)\n"
            "- Extract and SEPARATELY LIST all points of conflict/disagreement\n"
            "- Format conflicts as: '⚔️ CONFLICT: [thesis claim] vs [counter-evidence]'\n"
            "- Remove redundancy and verbose explanations\n"
            "- Keep the summary under 40% of the original length\n"
            "- Format as bullet points grouped by theme\n"
            "- End with a '## Conflicts' section listing all ⚔️ items\n\n"
            f"--- INPUT ({len(text)} chars) ---\n{text}\n\n"
            "--- COMPRESSED CHECKPOINT ---\n"
        )
        return await llm_ask(
            prompt,
            model=FLASH,
            max_tokens=1024,
        )

    def _truncate_oldest(self) -> None:
        """Last-resort truncation: remove oldest entries until under budget."""
        while self.is_over_budget and len(self.entries) > 1:
            removed = self.entries.pop(0)
            logger.debug(
                "DialecticContext: truncated iter=%d (%d chars)",
                removed.iteration, removed.char_count,
            )

    def render(self) -> str:
        """Render the full context string for injection into reasoning.

        Output format mirrors LS checkpoint structure:
          [CHECKPOINT] compressed old findings
          ---
          [RECENT] verbatim recent findings
        """
        parts = []
        if self._checkpoint_text:
            parts.append(
                f"## Opponent Findings (Compressed Checkpoint)\n\n{self._checkpoint_text}"
            )
        if self.entries:
            recent_parts = []
            for entry in self.entries:
                recent_parts.append(
                    f"### Iter {entry.iteration} [{entry.source}]\n{entry.text}"
                )
            parts.append(
                "## Recent Opponent Findings\n\n" + "\n\n".join(recent_parts)
            )
        return "\n\n---\n\n".join(parts) if parts else ""

    def clear(self) -> None:
        """Reset buffer."""
        self.entries.clear()
        self._checkpoint_text = ""

    def stats(self) -> dict:
        """Return buffer statistics."""
        return {
            "total_chars": self.total_chars,
            "budget": self.budget,
            "utilization": f"{self.total_chars / self.budget:.0%}" if self.budget > 0 else "N/A",
            "entries": len(self.entries),
            "has_checkpoint": bool(self._checkpoint_text),
            "checkpoint_chars": len(self._checkpoint_text),
            "over_budget": self.is_over_budget,
        }
