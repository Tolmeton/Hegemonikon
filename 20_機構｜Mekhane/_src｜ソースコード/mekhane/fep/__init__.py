# PROOF: [L2/インフラ] <- mekhane/fep/__init__.py
"""
PROOF: [L2/インフラ] このファイルは存在しなければならない

A0 → fep/ は FEP 実装を持つ
   → モジュールには公開インターフェイスが必要
   → __init__.py が担う

Q.E.D.

---

Hegemonikón FEP Module

Active Inference implementation based on pymdp for cognitive processes.

PERFORMANCE NOTE (2026-03-10):
    Previously this file eagerly imported 20+ submodules at top level,
    causing ~2s delay on first `import mekhane.fep.anything`.
    Now uses __getattr__ lazy loading — each symbol is imported only
    when first accessed. This eliminates the eager import chain penalty
    during boot and other scenarios where only specific submodules are needed.
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Lazy Import Registry
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Maps public symbol name → (submodule_name, actual_name_in_module)
# When __getattr__ is called for a symbol, it imports only that submodule.

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {}


def _register(module: str, *names: str) -> None:
    """Register symbols for lazy import from a submodule."""
    for name in names:
        _LAZY_IMPORTS[name] = (module, name)


# --- Core ---
_register("fep_agent", "HegemonikónFEPAgent")

_register("state_spaces",
    "PHANTASIA_STATES", "ASSENT_STATES", "HORME_STATES", "OBSERVATION_MODALITIES",
)

_register("encoding",
    "encode_input", "encode_structured_input", "decode_observation",
    "encode_noesis_output", "encode_boulesis_output", "generate_fep_feedback_markdown",
    "auto_encode_noesis", "format_learning_progress",
    "get_x_series_recommendations", "X_SERIES_MATRIX", "X_SERIES_REPRESENTATIVE_PATHS",
)

_register("persistence",
    "save_A", "load_A", "A_exists", "LEARNED_A_PATH",
)

_register("fep_bridge",
    "noesis_analyze", "boulesis_analyze", "full_inference_cycle",
    "NoesisResult", "BoulesisResult",
)

_register("llm_evaluator",
    "encode_input_with_confidence", "hierarchical_evaluate",
    "evaluate_and_infer", "EvaluationResult", "GEMINI_AVAILABLE",
)

_register("config",
    "FEPParameters", "load_parameters", "get_default_params", "reload_params",
)

# --- Theorem Evaluators ---

_register("telos_checker",
    "AlignmentStatus", "TelосResult", "check_alignment",
    "format_telos_markdown", "encode_telos_observation",
)

_register("tekhne_registry",
    "TechniqueQuadrant", "ActionCategory", "Technique", "TekhnēRegistry",
    "STANDARD_TECHNIQUES", "get_registry", "search_techniques", "format_registry_markdown",
)

_register("energeia_executor",
    "ExecutionPhase", "ExecutionStatus", "ExecutionContext", "ExecutionResult",
    "EnergеiaExecutor", "format_execution_markdown", "encode_execution_observation",
)

_register("chronos_evaluator",
    "TimeScale", "CertaintyLevel", "SlackLevel", "ChronosResult",
    "evaluate_time", "format_chronos_markdown", "encode_chronos_observation",
)

_register("eukairia_detector",
    "OpportunityWindow", "OpportunityScale", "OpportunityDecision",
    "OpportunityContext", "EukairiaResult",
    "detect_opportunity", "format_eukairia_markdown", "encode_eukairia_observation",
)

_register("perigraphe_engine",
    "KhoraDerivative", "ScopeScale", "KhoraResult",
    "HodosDerivative", "HodosResult", "TrokhiaDerivative", "TrokhiaResult",
    "define_scope", "define_path", "define_trajectory",
    "format_khora_markdown", "format_hodos_markdown", "format_trokhia_markdown",
    "encode_perigraphe_observation",
)

_register("horme_evaluator",
    "PropatheiaDerivative", "PropatheiaResult",
    "PistisDerivative", "PistisResult",
    "OrexisDerivative", "OrexisResult",
    "evaluate_propatheia", "evaluate_pistis", "evaluate_orexis",
    "format_propatheia_markdown", "format_pistis_markdown", "format_orexis_markdown",
    "encode_horme_observation",
)

_register("akribeia_evaluator",
    "PathosDerivative", "PathosResult",
    "GnomeDerivative", "GnomeResult",
    "EpistemeDerivative", "EpistemeResult",
    "evaluate_pathos", "extract_gnome", "evaluate_episteme",
    "format_pathos_markdown", "format_gnome_markdown", "format_episteme_markdown",
    "encode_akribeia_observation",
)

_register("zetesis_inquirer",
    "ZetesisDerivative", "QuestionType", "ZetesisResult",
    "inquire", "format_zetesis_markdown", "encode_zetesis_observation",
)

_register("schema_analyzer",
    "MetronDerivative", "ScaleLevel", "MetronResult",
    "StathmosDerivative", "CriterionPriority", "StathmosResult",
    "PraxisDerivative", "PraxisResult",
    "analyze_scale", "define_criteria", "plan_praxis",
    "format_metron_markdown", "format_stathmos_markdown", "format_praxis_markdown",
    "encode_schema_observation",
)

_register("doxa_persistence",
    "DoxaDerivative", "BeliefStrength", "Belief", "DoxaResult", "DoxaStore",
    "get_store", "format_doxa_markdown", "encode_doxa_observation",
)

_register("sophia_researcher",
    "SophiaDerivative", "ResearchDepth", "ResearchQuery", "SophiaResult",
    "research", "format_sophia_markdown", "encode_sophia_observation",
)

_register("krisis_judge",
    "KrisisDerivative", "VerdictType", "Objection", "KrisisResult",
    "judge", "epochē", "format_krisis_markdown", "encode_krisis_observation",
)

_register("fisher_metric",
    "FisherMetricAnalyzer", "ParameterBlock", "FlowBlock",
    "POMDPStatistic", "STATISTIC_COORDINATE_MAP",
    "BlockDiagonalizationResult", "RankVerificationResult",
    "ProductDecompositionProof", "ProductDecompositionResult", "DecompositionEvidence",
)

# --- Proof modules (DX-014) ---
_register("flow_proof", "run_flow_uniqueness_proof")
_register("d1_proof", "run_d1_uniqueness_proof")
_register("scale_proof", "run_scale_uniqueness_proof")
_register("temporality_proof", "run_temporality_uniqueness_proof")
_register("valence_proof", "run_valence_uniqueness_proof")
_register("independence_proof", "run_independence_proof")

# --- Ergon (Active Inference: a→μ channel) ---
_register("ergon.types",
    "SafetyClass", "SourceLabel", "Confidence",
    "Plan", "Task", "ExecutionResult", "ErgonBeliefUpdate",
)

_register("ergon.classifier",
    "classify_tool", "requires_confirmation", "BOUNDARY_TOOL_DEFAULTS",
)

_register("ergon.functors",
    "source_label_rule", "forgetting_rate",
    "compute_prediction_error", "triangle_identity_check",
)

_register("ergon.protocols",
    "BeliefChannelProtocol",
    "ergon_to_channel", "phi7_to_channel", "compare_channels",
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# __getattr__ — Lazy Loading Engine
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def __getattr__(name: str):
    """Lazy import: only load a submodule when one of its symbols is first accessed."""
    if name in _LAZY_IMPORTS:
        module_name, attr_name = _LAZY_IMPORTS[name]
        import importlib
        mod = importlib.import_module(f".{module_name}", __name__)
        value = getattr(mod, attr_name)
        # Cache on module to avoid repeated __getattr__ calls
        globals()[name] = value
        return value
    raise AttributeError(f"module 'mekhane.fep' has no attribute {name!r}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# __all__
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
__all__ = list(_LAZY_IMPORTS.keys())
