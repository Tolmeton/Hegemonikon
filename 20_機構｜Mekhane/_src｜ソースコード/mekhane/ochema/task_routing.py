from __future__ import annotations

from dataclasses import dataclass
import re

DEFAULT_TASK_CLASS = "operator"
TASK_CLASSES = (
    "coding",
    "analysis",
    "operator",
    "multimodal_heavy",
    "final_review",
)

_TASK_CLASS_ALIASES = {
    "coding": "coding",
    "code": "coding",
    "implement": "coding",
    "implementation": "coding",
    "worker": "coding",
    "mechanic": "coding",
    "analysis": "analysis",
    "analyze": "analysis",
    "review": "analysis",
    "reviewer": "analysis",
    "plan_review": "analysis",
    "math": "analysis",
    "science": "analysis",
    "operator": "operator",
    "ops": "operator",
    "default": "operator",
    "general": "operator",
    "computer_use": "operator",
    "multimodal_heavy": "multimodal_heavy",
    "multimodal": "multimodal_heavy",
    "researcher": "multimodal_heavy",
    "research": "multimodal_heavy",
    "heavy_docs": "multimodal_heavy",
    "docs": "multimodal_heavy",
    "document": "multimodal_heavy",
    "documents": "multimodal_heavy",
    "gemini": "multimodal_heavy",
    "final_review": "final_review",
    "final": "final_review",
    "final_review_only": "final_review",
}

_EXPLICIT_TASK_CLASS_RE = re.compile(
    r"(?:task[_ -]?class|task[_ -]?type)\s*[:=]\s*([a-z_ -]+)",
    re.IGNORECASE,
)

_MULTIMODAL_MARKERS = (
    "multimodal",
    "audio",
    "video",
    "pdf",
    "document scan",
    "document review",
    "large document",
    "long document",
    "report",
    "mcp",
    "researcher",
    "research task",
    "文書",
    "資料",
    "音声",
    "動画",
    "レポート",
    "走査",
)

_CODING_MARKERS = (
    "implement",
    "implementation",
    "write code",
    "patch",
    "refactor",
    "fix",
    "bug",
    "worker",
    "mechanic",
    "tekhne",
    "dokimasia",
    "作業者",
    "検証者",
    "実装",
    "修正",
    "バグ",
    "コード",
)

_ANALYSIS_MARKERS = (
    "analysis",
    "analyze",
    "review",
    "reviewer",
    "plan review",
    "math",
    "science",
    "proof",
    "reasoning",
    "explorer",
    "skeptic",
    "レビュー",
    "分析",
    "計画レビュー",
    "数学",
    "科学",
    "証明",
)

_OPERATOR_MARKERS = (
    "operator",
    "computer use",
    "navigate",
    "browser",
    "click",
    "fill",
    "open page",
    "shell",
    "terminal",
    "操作",
    "ブラウザ",
    "クリック",
    "入力",
    "端末",
)


@dataclass(frozen=True)
class TaskRoute:
    task_class: str
    route: str
    tool: str | None = None
    model: str | None = None
    effort: str | None = None

    @property
    def bridge_model(self) -> str | None:
        if not self.model:
            return None
        if self.effort and self.route == "cli_agent":
            return f"{self.model}:{self.effort}"
        return self.model


TASK_POLICY: dict[str, TaskRoute] = {
    "coding": TaskRoute(
        task_class="coding",
        route="cli_agent",
        tool="codex",
        model="gpt-5.3-codex",
        effort="high",
    ),
    "analysis": TaskRoute(
        task_class="analysis",
        route="cli_agent",
        tool="copilot",
        model="gpt-5.4",
        effort="xhigh",
    ),
    "operator": TaskRoute(
        task_class="operator",
        route="cli_agent",
        tool="copilot",
        model="gpt-5.4",
        effort="high",
    ),
    "multimodal_heavy": TaskRoute(
        task_class="multimodal_heavy",
        route="gemini_cli",
        model="gemini-3.1-pro",
    ),
    "final_review": TaskRoute(
        task_class="final_review",
        route="anthropic_passthrough",
        model="claude-opus",
    ),
}


def normalize_task_class(value: str | None, default: str = DEFAULT_TASK_CLASS) -> str:
    if value is None:
        return default
    token = value.strip().lower().replace("-", "_").replace(" ", "_")
    return _TASK_CLASS_ALIASES.get(token, default)


def infer_task_class(
    prompt: str | None,
    *,
    default_task_class: str | None = None,
) -> str:
    default = normalize_task_class(default_task_class, DEFAULT_TASK_CLASS)
    if not prompt:
        return default

    match = _EXPLICIT_TASK_CLASS_RE.search(prompt)
    if match:
        explicit = normalize_task_class(match.group(1), "")
        if explicit:
            return explicit

    lowered = prompt.lower()
    if any(marker in lowered for marker in _MULTIMODAL_MARKERS):
        return "multimodal_heavy"
    if any(marker in lowered for marker in _CODING_MARKERS):
        return "coding"
    if any(marker in lowered for marker in _ANALYSIS_MARKERS):
        return "analysis"
    if any(marker in lowered for marker in _OPERATOR_MARKERS):
        return "operator"
    return default


def resolve_task_route(task_class: str) -> TaskRoute:
    normalized = normalize_task_class(task_class, DEFAULT_TASK_CLASS)
    return TASK_POLICY[normalized]


def resolve_cli_task_route(
    prompt: str | None,
    *,
    default_task_class: str | None = None,
) -> TaskRoute:
    task_class = infer_task_class(prompt, default_task_class=default_task_class)
    return resolve_task_route(task_class)
