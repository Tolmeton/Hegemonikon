from __future__ import annotations
# PROOF: mekhane/periskope/models.py
# PURPOSE: periskope モジュールのデータモデル定義 (models)
"""
Periskopē data models.

Shared data structures for the search → synthesis → citation pipeline.
Includes ProgressProtocol for unified progress reporting across mekhane subsystems.
"""


from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Literal, Optional


# ─── Progress Protocol ────────────────────────────────────────────

@dataclass
class ProgressEvent:
    """Unified progress event for all mekhane subsystems.

    Replaces ad-hoc callback signatures:
    - periskope: callback(phase, detail_dict)
    - symploke: callback(batch_num, total, completed)

    All progress reporting uses this single structure.
    """
    phase: str                          # Phase identifier (e.g., "phase_1_start", "batch")
    label: str | None = None            # Human-readable phase name (e.g., "Parallel Search")
    phase_type: Literal["start", "done", "error"] | None = None # Classification of event
    detail: dict[str, Any] = field(default_factory=dict)  # Flexible detail payload
    elapsed: float = 0.0                # Seconds since start
    progress: float | None = None       # 0.0-1.0 completion ratio (optional)

    def __post_init__(self):
        if self.phase_type is None:
            if self.phase.endswith("_start"):
                self.phase_type = "start"
            elif self.phase.endswith("_done") or "complete" in self.phase:
                self.phase_type = "done"

    def summary(self) -> str:
        """One-line summary for logging."""
        display = self.label or self.phase
        parts = [f"[{display}]"]
        if self.progress is not None:
            parts.append(f"{self.progress:.0%}")
        if self.elapsed > 0:
            parts.append(f"{self.elapsed:.1f}s")
        detail_str = ", ".join(f"{k}={v}" for k, v in self.detail.items() if v is not None)
        if detail_str:
            parts.append(detail_str)
        return " ".join(parts)


# Type alias for progress callbacks
ProgressCallback = Callable[[ProgressEvent], None]


# PURPOSE: [L2-auto] SearchSource のクラス定義
class SearchSource(str, Enum):
    """Search source identifiers."""
    SEARXNG = "searxng"
    BRAVE = "brave"
    TAVILY = "tavily"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    GNOSIS = "gnosis"
    SOPHIA = "sophia"
    KAIROS = "kairos"
    PLAYWRIGHT = "playwright"
    ARXIV = "arxiv"
    OPENALEX = "openalex"
    GITHUB = "github"
    GEMINI_SEARCH = "gemini_search"
    STACKOVERFLOW = "stackoverflow"
    REDDIT = "reddit"
    HACKERNEWS = "hackernews"
    VERTEX_SEARCH = "vertex_search"
    VECTOR_SEARCH_ANN = "vector_search_ann"
    GOOGLE_CSE = "google_cse"


# PURPOSE: [L2-auto] TaintLevel のクラス定義
class TaintLevel(str, Enum):
    """N-10 TAINT classification for citations."""
    SOURCE = "SOURCE"       # Directly verified (similarity > 0.8)
    TAINT = "TAINT"         # Partially verified (0.5 < similarity < 0.8)
    FABRICATED = "FABRICATED"  # Not found at source (similarity < 0.5)
    UNCHECKED = "UNCHECKED"   # Not yet verified


# PURPOSE: [L2-auto] SynthModel のクラス定義
class SynthModel(str, Enum):
    """Available synthesis models."""
    GEMINI_FLASH = "gemini-3-flash-preview"
    GEMINI_PRO = "gemini-3.1-pro-preview"
    CLAUDE_SONNET = "claude-sonnet-4-6"    # L2 standard
    CLAUDE_OPUS = "claude-opus-4-6"        # L3 deep
    # Deprecated — use CLAUDE_SONNET/CLAUDE_OPUS instead
    CLAUDE_LS = "claude-ls"
    CLAUDE_CORTEX = "claude-cortex"


# PURPOSE: [L2-auto] SearchResult のクラス定義
@dataclass
class SearchResult:
    """A single search result from any source."""
    source: SearchSource
    title: str
    url: str | None = None
    source_urls: list[str] = field(default_factory=list)  # Layer E: provenance URLs
    content: str = ""
    snippet: str = ""       # Short extract for display
    relevance: float = 0.0  # 0.0-1.0
    timestamp: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    # PURPOSE: [L2-auto] is_internal の関数定義
    @property
    def is_internal(self) -> bool:
        """Whether this result comes from HGK internal knowledge."""
        return self.source in (
            SearchSource.GNOSIS, 
            SearchSource.SOPHIA, 
            SearchSource.KAIROS,
            SearchSource.VECTOR_SEARCH_ANN
        )


# PURPOSE: [L2-auto] Citation のクラス定義
@dataclass
class Citation:
    """A citation linking a claim to its source."""
    claim: str
    source_url: str
    source_title: str = ""
    taint_level: TaintLevel = TaintLevel.UNCHECKED
    similarity: float | None = None
    verified_at: str | None = None
    verification_note: str = ""

    # PURPOSE: [L2-auto] is_trustworthy の関数定義
    @property
    def is_trustworthy(self) -> bool:
        return self.taint_level == TaintLevel.SOURCE


# PURPOSE: [L2-auto] SynthesisResult のクラス定義
@dataclass
class SynthesisResult:
    """Result from a single model's synthesis."""
    model: SynthModel
    content: str
    citations: list[Citation] = field(default_factory=list)
    confidence: float = 0.0
    thinking: str = ""  # Chain-of-thought if available
    token_count: int = 0


# PURPOSE: [L2-auto] DivergenceReport のクラス定義
@dataclass
class DivergenceReport:
    """Report on divergence between multiple model outputs."""
    models_compared: list[SynthModel] = field(default_factory=list)
    agreement_score: float = 0.0  # 0.0-1.0
    divergent_claims: list[str] = field(default_factory=list)
    consensus_claims: list[str] = field(default_factory=list)


# PURPOSE: [L2-auto] PeriskopeConfig のクラス定義
@dataclass
class PeriskopeConfig:
    """Configuration for a Periskopē research session."""
    query: str = ""
    # Search config
    search_sources: list[SearchSource] = field(
        default_factory=lambda: [
            SearchSource.SEARXNG,
            SearchSource.BRAVE,
            SearchSource.TAVILY,
            SearchSource.SEMANTIC_SCHOLAR,
            SearchSource.GNOSIS,
            SearchSource.SOPHIA,
        ]
    )
    max_results_per_source: int = 20
    # Synthesis config
    synth_models: list[SynthModel] = field(
        default_factory=lambda: [SynthModel.GEMINI_FLASH]
    )
    # Citation config
    verify_citations: bool = True
    max_citations_to_verify: int = 10
    # Output config
    output_format: str = "markdown"
    auto_digest: bool = False  # Auto-run /eat- after completion

