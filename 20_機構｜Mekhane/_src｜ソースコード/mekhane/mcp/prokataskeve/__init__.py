#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/prokataskeve/ V-001 前処理パイプライン
"""
Prokataskeuē (προκατασκευή) — Pre-processing Pipeline Package

FEP Derivation: 24 Poiesis full scan → 18 pre-processing functions → 8 modules.
Depth Synchronization: d_pre ≤ d_main (Precision Saturation Inequality).

Modules (8-module reduction from 18 conceptual functions):
  - intent_classifier:    classify_intent + extract_goal + match_template
  - query_transformer:    rewrite_query + diversify_query
  - input_analyzer:       normalize + extract_entities + extract_certain + detect_ambiguity
  - context_resolver:     resolve_references + integrate_context + recall_past
  - consistency_checker:  detect_contradiction + suggest_fix
  - hypothesis_generator: generate_hyde
  - pattern_injector:     inject_few_shot
  - predictor:            predict_next + prefetch
"""

try:
    # Tier 2+ — 8-module package structure
    from mekhane.mcp.prokataskeve.models import (
        AmbiguitySpan, CertainSpan, ContextSummary, Contradiction,
        Depth, Domain, Entity, EntityType, FewShotExample,
        FixSuggestion, GoalExtraction, IntentClassification, IntentType,
        PastResult, PreprocessResult, TemplateMatch,
    )
    from mekhane.mcp.prokataskeve.input_analyzer import (
        detect_ambiguity, extract_certain, extract_entities, normalize,
    )
    from mekhane.mcp.prokataskeve.intent_classifier import (
        classify_intent, extract_goal, match_template,
    )
    from mekhane.mcp.prokataskeve.query_transformer import (
        diversify_query, rewrite_query,
    )
    from mekhane.mcp.prokataskeve.context_resolver import (
        integrate_context, recall_past, resolve_references,
    )
    from mekhane.mcp.prokataskeve.consistency_checker import (
        detect_contradiction, suggest_fix,
    )
    from mekhane.mcp.prokataskeve.hypothesis_generator import generate_hyde
    from mekhane.mcp.prokataskeve.pattern_injector import inject_few_shot
    from mekhane.mcp.prokataskeve.predictor import predict_next, prefetch
    from mekhane.mcp.prokataskeve.pipeline import PreprocessPipeline

except (ImportError, ModuleNotFoundError):
    # Tier 1 fallback — single-file implementation (prokataskeve.py)
    # Python resolves package over file, so we use importlib to load the .py directly
    import importlib.util as _ilu
    from pathlib import Path as _Path
    _single_file = _Path(__file__).parent.parent / "prokataskeve.py"
    if _single_file.exists():
        _spec = _ilu.spec_from_file_location(
            "mekhane.mcp._prokataskeve_single", str(_single_file),
        )
        _mod = _ilu.module_from_spec(_spec)  # type: ignore[arg-type]
        _spec.loader.exec_module(_mod)  # type: ignore[union-attr]

        # Re-export everything from the single file
        from mekhane.mcp._prokataskeve_single import *  # noqa: F403, F401
        # Explicit names for type checkers
        Depth = _mod.Depth  # type: ignore[misc]
        PreprocessPipeline = _mod.PreprocessPipeline  # type: ignore[misc]
        normalize = _mod.normalize  # type: ignore[misc]
        Entity = _mod.Entity  # type: ignore[misc]
        EntityType = _mod.EntityType  # type: ignore[misc]
        IntentType = _mod.IntentType  # type: ignore[misc]
        IntentClassification = _mod.IntentClassification  # type: ignore[misc]
        Domain = _mod.Domain  # type: ignore[misc]
        CertainSpan = _mod.CertainSpan  # type: ignore[misc]
        extract_entities = _mod.extract_entities  # type: ignore[misc]
        extract_certain = _mod.extract_certain  # type: ignore[misc]
        classify_intent = _mod.classify_intent  # type: ignore[misc]
        PreprocessResult = _mod.PreprocessResult  # type: ignore[misc]
    else:
        raise

__all__ = [
    # Models
    "AmbiguitySpan", "CertainSpan", "ContextSummary", "Contradiction",
    "Depth", "Domain", "Entity", "EntityType", "FewShotExample",
    "FixSuggestion", "GoalExtraction", "IntentClassification", "IntentType",
    "PastResult", "PreprocessResult", "TemplateMatch",
    # Functions (18)
    "normalize", "extract_entities", "extract_certain",       # L0 (3)
    "classify_intent", "resolve_references", "rewrite_query",  # L1 (3)
    "extract_goal", "match_template", "diversify_query",       # L2 (6)
    "detect_ambiguity", "integrate_context", "inject_few_shot",
    "recall_past", "detect_contradiction", "suggest_fix",      # L3 (4)
    "generate_hyde",
    "predict_next", "prefetch",                                # L4 (2)
    # Pipeline
    "PreprocessPipeline",
]

