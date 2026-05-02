from __future__ import annotations
# PROOF: [L1/FEP] <- mekhane/fep/e2e_loop.py
# PURPOSE: Active Inference の E2E ループを統合実行する
"""
FEP E2E Loop — 動く認知体の証明

全 FEP コンポーネントを統合し、閉じた Active Inference ループを実行する。

## 構造

               入力
              ╱    ╲
        FEP Agent   Attractor
        (act/obs)   (Series/WF)
              ╲    ╱
             統合判断
                ↓
          Dispatch + Cone
                ↓
              学習 (A-matrix)
                ↓
            次サイクルへ

## 使用例

    from mekhane.fep.e2e_loop import run_loop
    results = run_loop("なぜこのプロジェクトは存在するのか", cycles=2)
    print(results.summary)
"""


import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# =============================================================================
# Data Classes
# =============================================================================


# PURPOSE: 1サイクルの E2E 結果
@dataclass
class CycleResult:
    """1サイクルの E2E 結果"""
    cycle: int
    # Encoding
    observation: tuple[int, int, int]
    obs_decoded: Dict[str, str]
    # FEP inference
    fep_action: str = "act"  # "act" or "observe"
    fep_entropy: float = 0.0
    fep_confidence: float = 0.0
    fep_raw: Dict[str, Any] = field(default_factory=dict)
    # Attractor / Dispatch
    dispatch_wf: Optional[str] = None
    dispatch_series: Optional[str] = None
    dispatch_reason: Optional[str] = None
    dispatch_oscillation: Optional[str] = None
    dispatch_alternatives: List[str] = field(default_factory=list)
    # Cone
    cone_apex: Optional[str] = None
    cone_dispersion: Optional[float] = None
    cone_method: Optional[str] = None
    # ConeAdvice + DevilAttack
    advice_action: Optional[str] = None
    advice_wf: Optional[str] = None
    advice_trace: Optional[str] = None  # ES: DecisionTrace repr
    advice_format: Optional[str] = None  # ES: format_advice_for_llm output
    devil_severity: Optional[float] = None
    devil_summary: Optional[str] = None
    # Learning
    a_matrix_updated: bool = False
    should_epoche: bool = False
    # Helmholtz Bridge (P3)
    helmholtz_is_gradient: Optional[bool] = None
    helmholtz_coordinate: Optional[str] = None
    helmholtz_score: Optional[float] = None


# PURPOSE: E2E ループの全サイクル結果
@dataclass
class E2EResult:
    """E2E ループの全サイクル結果"""
    input_text: str
    cycles: List[CycleResult]
    learning_proof: Optional[str] = None

    # PURPOSE: 人間向けサマリー
    @property
    def summary(self) -> str:
        """人間向けサマリー"""
        lines = [
            f"═══ FEP E2E Loop: {len(self.cycles)} cycle(s) ═══",
            f"Input: {self.input_text[:60]}",
        ]
        for c in self.cycles:
            meta = "🔴 observe" if c.fep_action == "observe" else "🟢 act"
            wf = c.dispatch_wf or "(none)"
            lines.append(
                f"  Cycle {c.cycle}: {meta} → {wf} "
                f"(entropy={c.fep_entropy:.2f}, conf={c.fep_confidence:.0%})"
            )
        if self.learning_proof:
            lines.append(f"📈 Learning: {self.learning_proof}")
        return "\n".join(lines)


# =============================================================================
# Core Loop
# =============================================================================


# PURPOSE: FEP E2E ループを実行する。
def run_loop(
    user_input: str,
    *,
    cycles: int = 2,
    a_matrix_path: Optional[str] = None,
    force_cpu: bool = False,
) -> E2EResult:
    """FEP E2E ループを実行する。

    Helmholtz Bridge (P3): verb_helmholtz_context() により、
    各 dispatch の WF に対して Γ/Q コンテキストを自動注入。

    Active Inference の完全なサイクルを指定回数実行し、
    学習によるA行列の改善を証明する。

    Args:
        user_input: 自然言語入力
        cycles: 実行サイクル数 (default: 2 — 学習証明のため)
        a_matrix_path: A行列の保存先 (None=一時ファイル)
        force_cpu: Attractor の CPU 強制
    """
    # Lazy imports (heavy dependencies)
    from mekhane.fep.encoding import (
        encode_input,
        decode_observation,
        run_fep_with_learning,
    )
    from mekhane.fep.attractor_dispatcher import AttractorDispatcher
    from mekhane.fep.cone_builder import converge
    from mekhane.fep.category import Series
    from mekhane.fep.cone_consumer import advise, devil_attack, format_advice_for_llm

    # 一時ファイルでA行列を管理 (テスト時のクリーン性)
    if a_matrix_path is None:
        _tmp = tempfile.NamedTemporaryFile(suffix="_e2e_A.npy", delete=False)
        a_matrix_path = _tmp.name
        _tmp.close()
        Path(a_matrix_path).unlink(missing_ok=True)  # 空の状態から開始

    try:
        dispatcher = AttractorDispatcher(force_cpu=force_cpu)
    except (FileNotFoundError, OSError, ImportError):
        dispatcher = None
    results: List[CycleResult] = []

    for i in range(cycles):
        cycle = CycleResult(cycle=i, observation=(0, 0, 0), obs_decoded={})

        # ── Step 1: Encode ──
        obs = encode_input(user_input)
        cycle.observation = obs
        cycle.obs_decoded = decode_observation(obs)

        # ── Step 2: Parallel Judgment ──

        # 2a. FEP Agent (meta-level: act or observe?)
        fep_result = run_fep_with_learning(
            obs, a_matrix_path=a_matrix_path, learning_rate=50.0,
        )
        cycle.fep_action = fep_result.get("action_name", "act")
        cycle.fep_entropy = fep_result.get("entropy", 0.0)
        cycle.fep_confidence = 1.0 - min(fep_result.get("entropy", 0.0) / 3.0, 1.0)
        cycle.fep_raw = fep_result
        cycle.a_matrix_updated = True
        cycle.should_epoche = fep_result.get("should_epoche", False)

        # 2b. Attractor (content-level: which WF?)
        plan = None
        if dispatcher is not None:
            try:
                plan = dispatcher.dispatch(user_input)
            except (FileNotFoundError, OSError) as e:
                # Embedding model unavailable (CI/test env)
                plan = None

        if plan is not None:
            cycle.dispatch_wf = plan.primary.workflow
            cycle.dispatch_series = plan.primary.series
            cycle.dispatch_reason = plan.primary.reason
            cycle.dispatch_oscillation = plan.oscillation.value if hasattr(plan.oscillation, 'value') else str(plan.oscillation)
            cycle.dispatch_alternatives = [
                d.workflow for d in plan.alternatives
            ]

            # ── Helmholtz Bridge: inject Γ/Q context ──
            try:
                from mekhane.fep.mapping import verb_helmholtz_context
                wf_name = plan.primary.workflow or ""
                # WF 名から CCL 動詞を抽出 (e.g., "/noe+" → "noe")
                ccl_verb = wf_name.strip("/").rstrip("+- ")
                h_ctx = verb_helmholtz_context(ccl_verb)
                if h_ctx is not None:
                    cycle.helmholtz_is_gradient = h_ctx.is_gradient
                    cycle.helmholtz_coordinate = h_ctx.coordinate
                    cycle.helmholtz_score = h_ctx.helmholtz_score
            except ImportError:
                pass  # mapping module not available

        # ── Step 3: Meta-judgment integration ──
        # FEP says "observe" → suppress dispatch (don't act)
        if cycle.fep_action == "observe" and plan is not None:
            cycle.dispatch_reason = (
                f"[SUPPRESSED by FEP: observe mode] {cycle.dispatch_reason}"
            )

        # ── Step 4: Cone (simulated WF output) ──
        if plan is not None and cycle.fep_action != "observe":
            simulated_cone = _simulate_cone(plan.primary.series, user_input)
            cycle.cone_apex = simulated_cone.get("apex")
            cycle.cone_dispersion = simulated_cone.get("dispersion")
            cycle.cone_method = simulated_cone.get("method")

            # ── Step 4b: ConeAdvice + DevilAttack ──
            try:
                series_enum = Series[plan.primary.series]
                outputs = simulated_cone.get("outputs", {})
                cone = converge(series_enum, outputs)
                advice = advise(cone)
                cycle.advice_action = advice.action
                cycle.advice_wf = advice.suggested_wf
                # ES: preserve trace
                if advice.trace:
                    cycle.advice_trace = repr(advice.trace)
                cycle.advice_format = format_advice_for_llm(advice)
                if cone.needs_devil:
                    attack = devil_attack(cone)
                    cycle.devil_severity = attack.severity
                    cycle.devil_summary = attack.attack_summary
            except Exception:  # noqa: BLE001
                pass  # cone_consumer is best-effort

        results.append(cycle)

    # ── Learning proof ──
    learning_proof = None
    if len(results) >= 2:
        e0 = results[0].fep_entropy
        e1 = results[-1].fep_entropy
        if e0 > 0:
            change = ((e1 - e0) / e0) * 100
            if e1 < e0:
                learning_proof = (
                    f"エントロピー減少: {e0:.3f} → {e1:.3f} "
                    f"({change:+.1f}%) — モデルの確信度が向上"
                )
            elif e1 == e0:
                learning_proof = (
                    f"エントロピー安定: {e0:.3f} → {e1:.3f} — "
                    f"1サイクル目から安定 (十分なデータで変化が期待される)"
                )
            else:
                learning_proof = (
                    f"エントロピー増加: {e0:.3f} → {e1:.3f} "
                    f"({change:+.1f}%) — 探索フェーズ"
                )

    return E2EResult(
        input_text=user_input,
        cycles=results,
        learning_proof=learning_proof,
    )


# =============================================================================
# Simulated Cone
# =============================================================================


_SERIES_THEOREMS = {
    "O": ["O1", "O2", "O3", "O4"],
    "S": ["S1", "S2", "S3", "S4"],
    "H": ["H1", "H2", "H3", "H4"],
    "P": ["P1", "P2", "P3", "P4"],
    "K": ["K1", "K2", "K3", "K4"],
    "A": ["A1", "A2", "A3", "A4"],
}

_THEOREM_TEMPLATES = {
    "O1": "この問いの本質は「{topic}」の根源的な意味にある",
    "O2": "目標: {topic} を明確化し、優先順位を決定する",
    "O3": "問うべきは「なぜ {topic} なのか」ではなく「何を見落としているか」",
    "O4": "実行計画: {topic} に対し段階的にアプローチする",
    "S1": "スケール: {topic} は Micro/Meso/Macro のどの粒度か",
    "S2": "手法: {topic} には以下の方法論が適用可能",
    "S3": "基準: {topic} の成功基準を定量化する",
    "S4": "実践: {topic} の価値は実行されることで初めて発揮される",
    "H1": "直感的反応: {topic} に対する初期感情は肯定的",
    "H2": "確信度: {topic} について 70% の確信がある",
    "H3": "欲求: {topic} を追求する動機は十分に強い",
    "H4": "信念: {topic} は Hegemonikón の方向性と一致する",
    "P1": "スコープ: {topic} の境界を定義する",
    "P2": "経路: {topic} への到達パスを設計する",
    "P3": "軌道: {topic} の進捗サイクルを定義する",
    "P4": "技法: {topic} に最適な技法を選択する",
    "K1": "タイミング: 今は {topic} に取り組む好機か",
    "K2": "期限: {topic} の時間制約を評価する",
    "K3": "目的: {topic} の究極的な目的を問い直す",
    "K4": "知恵: {topic} に関する先行研究を参照する",
    "A1": "感情: {topic} に対する感情的反応を評価する",
    "A2": "判断: {topic} を批判的に評価する",
    "A3": "格言: {topic} から抽出される原則は何か",
    "A4": "知識: {topic} に関する確立された知識を確認する",
}


# PURPOSE: [L2-auto] _simulate_cone の関数定義
def _simulate_cone(series: str, user_input: str) -> Dict[str, Any]:
    """Build a Cone using real workflow infrastructure.

    Uses workflow_runner to select derivatives, then
    cone_builder.converge() for real C0-C3 Cone construction.
    Falls back to template simulation if imports fail.

    Architecture:
        Series → 4 theorems → workflow_runner.run_workflow() per theorem
        → WFContext stores outputs → cone_builder.converge() → Cone
    """
    try:
        from mekhane.fep.cone_builder import converge
        from mekhane.fep.category import Series
        from mekhane.symploke.workflow_runner import run_workflow
    except ImportError:
        return _simulate_cone_fallback(series, user_input)

    theorems = _SERIES_THEOREMS.get(series, [])
    if not theorems:
        return {"apex": "(unknown series)", "dispersion": 0.0, "method": "n/a"}

    topic = user_input[:100]

    # Run workflow_runner for each theorem in the series
    outputs: Dict[str, str] = {}
    pw: Dict[str, float] = {}
    for t in theorems:
        try:
            result = run_workflow(t, topic)
            # Use derivative description as the "output" of this theorem
            outputs[t] = (
                f"[{result.derivative}] {result.description}"
                if result.description
                else f"[{result.derivative}] {result.rationale}"
            )
            pw[t] = result.confidence - 0.5  # Normalize to [-0.5, 0.5]
        except Exception:  # noqa: BLE001
            # Graceful fallback per-theorem
            template = _THEOREM_TEMPLATES.get(t, "{topic} に関する分析")
            outputs[t] = template.format(topic=topic[:30])

    # Build real Cone via converge() C0-C3
    try:
        series_enum = Series[series] if hasattr(Series, series) else Series.Tel
        cone = converge(
            series=series_enum,
            outputs=outputs,
            pw=pw if any(v != 0 for v in pw.values()) else None,
            context=topic,
        )
        return {
            "apex": cone.apex,
            "dispersion": cone.dispersion,
            "method": cone.resolution_method,
            "outputs": outputs,
            "cone": cone,
        }
    except Exception:  # noqa: BLE001
        # Fallback: partial result without Cone object
        from mekhane.fep.cone_builder import compute_dispersion, resolve_method
        dispersion = compute_dispersion(outputs)
        method = resolve_method(dispersion)
        return {
            "apex": outputs.get(theorems[0], ""),
            "dispersion": dispersion,
            "method": method,
            "outputs": outputs,
        }


# PURPOSE: [L2-auto] _simulate_cone_fallback の関数定義
def _simulate_cone_fallback(series: str, user_input: str) -> Dict[str, Any]:
    """Original simulation fallback when imports are unavailable."""
    theorems = _SERIES_THEOREMS.get(series, ["T1", "T2", "T3", "T4"])
    topic = user_input[:30]
    outputs = {}
    for t in theorems:
        template = _THEOREM_TEMPLATES.get(t, "{topic} に関する分析")
        outputs[t] = template.format(topic=topic)

    try:
        from mekhane.fep.cone_builder import compute_dispersion, resolve_method
        dispersion = compute_dispersion(outputs)
        method = resolve_method(dispersion)
    except ImportError:
        dispersion = 0.0
        method = "n/a"

    return {
        "apex": outputs.get(theorems[0], ""),
        "dispersion": dispersion,
        "method": method,
        "outputs": outputs,
    }



# =============================================================================
# V2 Loop: Unified 48-state judgment
# =============================================================================

# Series → topic observation index mapping
_SERIES_TO_TOPIC_OBS = {"O": 8, "S": 9, "H": 10, "P": 11, "K": 12, "A": 13}


# PURPOSE: 1サイクルの E2E v2 結果 — 統合判断
@dataclass
class CycleResultV2:
    """1サイクルの E2E v2 結果 — 統合判断"""
    cycle: int
    # Encoding
    observation: tuple[int, int, int] = (0, 0, 0)
    obs_decoded: Dict[str, str] = field(default_factory=dict)
    # Attractor recommendation (input to agent)
    attractor_series: Optional[str] = None
    attractor_wf: Optional[str] = None
    # Unified FEP v2 judgment
    action_name: str = "observe"
    selected_series: Optional[str] = None
    fep_entropy: float = 0.0
    fep_confidence: float = 0.0
    map_state: Dict[str, str] = field(default_factory=dict)
    fep_raw: Dict[str, Any] = field(default_factory=dict)
    # Cone
    cone_apex: Optional[str] = None
    cone_dispersion: Optional[float] = None
    cone_method: Optional[str] = None
    # ConeAdvice + ES
    advice_action: Optional[str] = None
    advice_wf: Optional[str] = None
    advice_trace: Optional[str] = None  # ES: DecisionTrace repr
    advice_format: Optional[str] = None  # ES: format_advice_for_llm output
    # Learning
    a_matrix_updated: bool = False
    # Helmholtz Bridge (P3)
    helmholtz_is_gradient: Optional[bool] = None
    helmholtz_coordinate: Optional[str] = None
    helmholtz_score: Optional[float] = None


# PURPOSE: E2E v2 ループの全サイクル結果
@dataclass
class E2EResultV2:
    """E2E v2 ループの全サイクル結果"""
    input_text: str
    cycles: List[CycleResultV2]
    learning_proof: Optional[str] = None

    # PURPOSE: summary の処理
    @property
    def summary(self) -> str:
        lines = [
            f"═══ FEP E2E Loop v2 (48-state): {len(self.cycles)} cycle(s) ═══",
            f"Input: {self.input_text[:60]}",
        ]
        for c in self.cycles:
            if c.action_name == "observe":
                action = "🔴 observe"
            else:
                action = f"🟢 {c.action_name}"
            series = c.selected_series or "-"
            lines.append(
                f"  Cycle {c.cycle}: {action} [Series={series}] "
                f"(entropy={c.fep_entropy:.2f}, conf={c.fep_confidence:.0%})"
            )
        if self.learning_proof:
            lines.append(f"📈 Learning: {self.learning_proof}")
        return "\n".join(lines)


# PURPOSE: FEP E2E ループ v2 — 統合 48-state モデル。
def run_loop_v2(
    user_input: str,
    *,
    cycles: int = 2,
    a_matrix_path: Optional[str] = None,
    force_cpu: bool = False,
) -> E2EResultV2:
    """FEP E2E ループ v2 — 統合 48-state モデル。

    v1 との違い:
    - FEP Agent が Series を内部で選択する (並列→統合)
    - Attractor は observation provider (判断者→情報提供者)
    - 行動 = observe / act_T / act_M / act_K / act_D / act_O / act_C

    Args:
        user_input: 自然言語入力
        cycles: 実行サイクル数 (default: 2)
        a_matrix_path: A行列の保存先 (None=一時ファイル)
        force_cpu: Attractor の CPU 強制
    """
    from mekhane.fep.encoding import encode_input, decode_observation
    from mekhane.fep.fep_agent_v2 import HegemonikónFEPAgentV2

    # Attractor (optional — provides topic observation)
    dispatcher = None
    try:
        from mekhane.fep.attractor_dispatcher import AttractorDispatcher
        dispatcher = AttractorDispatcher(force_cpu=force_cpu)
    except (FileNotFoundError, OSError, ImportError):
        pass

    # A行列パス
    if a_matrix_path is None:
        _tmp = tempfile.NamedTemporaryFile(suffix="_e2e_v2_A.npy", delete=False)
        a_matrix_path = _tmp.name
        _tmp.close()
        Path(a_matrix_path).unlink(missing_ok=True)

    # Agent (persistent across cycles)
    agent = HegemonikónFEPAgentV2()
    agent.load_learned_A(a_matrix_path)
    agent.load_epsilon()  # Meta-ε 復元

    results: List[CycleResultV2] = []

    for i in range(cycles):
        cycle = CycleResultV2(cycle=i)

        # ── Step 1: Encode text → (context, urgency, confidence) ──
        obs = encode_input(user_input)
        cycle.observation = obs
        cycle.obs_decoded = decode_observation(obs)

        # ── Step 2: Get Attractor recommendation → topic observation ──
        topic_obs_idx = 8  # default: O (neutral fallback)
        if dispatcher is not None:
            try:
                plan = dispatcher.dispatch(user_input)
                if plan is not None:
                    cycle.attractor_series = plan.primary.series
                    cycle.attractor_wf = plan.primary.workflow
                    topic_obs_idx = _SERIES_TO_TOPIC_OBS.get(
                        plan.primary.series, 8
                    )

                    # ── Helmholtz Bridge (P4): inject Γ/Q context ──
                    try:
                        from mekhane.fep.mapping import verb_helmholtz_context
                        wf_name = plan.primary.workflow or ""
                        ccl_verb = wf_name.strip("/").rstrip("+- ")
                        h_ctx = verb_helmholtz_context(ccl_verb)
                        if h_ctx is not None:
                            cycle.helmholtz_is_gradient = h_ctx.is_gradient
                            cycle.helmholtz_coordinate = h_ctx.coordinate
                            cycle.helmholtz_score = h_ctx.helmholtz_score
                    except ImportError:
                        pass  # mapping module not available

            except (FileNotFoundError, OSError):
                pass

        # ── Step 3: Build flat observation for v2 agent ──
        # Layout: context(2) + urgency(3) + confidence(3) + topic(6) = 14
        # We pick the dominant observation index
        # Use topic as the primary observation for Series selection
        flat_obs = topic_obs_idx

        # ── Step 4: Unified judgment (infer + act) ──
        result = agent.step(observation=flat_obs)

        cycle.action_name = result["action_name"]
        cycle.selected_series = result.get("selected_series")
        cycle.fep_entropy = result["entropy"]
        cycle.fep_confidence = 1.0 - min(result["entropy"] / 4.0, 1.0)
        cycle.map_state = result["map_state_names"]
        cycle.fep_raw = result

        # ── Step 5: Learn ──
        agent.update_A_dirichlet(observation=flat_obs)
        cycle.a_matrix_updated = True

        # ── Step 5b: Feedback Bridge — A行列 → Attractor bias ──
        # A行列の topic 精度を Attractor の similarity bias に注入
        # これにより cycle N の学習が cycle N+1 の Series 感度に反映される
        if dispatcher is not None:
            try:
                from mekhane.fep.fep_attractor_bridge import apply_fep_bias_to_attractor
                biases = apply_fep_bias_to_attractor(
                    agent, dispatcher._advisor._attractor,
                )
                cycle.fep_raw["feedback_bias"] = biases
            except Exception:  # noqa: BLE001
                pass  # feedback is best-effort

        # ── Step 6: Cone + ConeAdvice (if acting) ──
        if cycle.selected_series is not None:
            simulated_cone = _simulate_cone(cycle.selected_series, user_input)
            cycle.cone_apex = simulated_cone.get("apex")
            cycle.cone_dispersion = simulated_cone.get("dispersion")
            cycle.cone_method = simulated_cone.get("method")

            # ES: ConeAdvice + Explanation Stack
            try:
                from mekhane.fep.cone_consumer import advise, format_advice_for_llm
                from mekhane.fep.cone_builder import converge as _converge
                from mekhane.fep.category import Series as SeriesEnum
                cone_obj = simulated_cone.get("cone")
                if cone_obj is None:
                    series_enum = SeriesEnum[cycle.selected_series]
                    cone_obj = _converge(series_enum, simulated_cone.get("outputs", {}))
                advice = advise(cone_obj)
                cycle.advice_action = advice.action
                cycle.advice_wf = advice.suggested_wf
                if advice.trace:
                    cycle.advice_trace = repr(advice.trace)
                cycle.advice_format = format_advice_for_llm(advice)
            except Exception:  # noqa: BLE001
                pass  # ES is best-effort

        results.append(cycle)

    # Save A matrix
    import os
    os.makedirs(os.path.dirname(a_matrix_path), exist_ok=True)
    agent.save_learned_A(a_matrix_path)
    agent.save_epsilon()  # Meta-ε 永続化

    # ES: Persist last cycle's trace for boot Axis M
    last_es = next(
        (c for c in reversed(results) if c.advice_format),
        None,
    )
    if last_es:
        try:
            import json as _json
            from mekhane.paths import LOGS_DIR
            es_log_dir = LOGS_DIR
            os.makedirs(es_log_dir, exist_ok=True)
            from datetime import datetime as _dt
            es_path = es_log_dir / f"es_trace_{_dt.now().strftime('%Y%m%d_%H%M%S')}.json"
            es_payload = {
                "advice": {
                    "action": last_es.advice_action,
                    "format_llm": last_es.advice_format,
                },
                "cycle": last_es.cycle,
            }
            with open(es_path, "w") as f:
                _json.dump(es_payload, f, ensure_ascii=False, indent=2)
        except Exception:  # noqa: BLE001
            pass  # ES persistence is best-effort

    # Learning proof
    learning_proof = None
    if len(results) >= 2:
        e0 = results[0].fep_entropy
        e1 = results[-1].fep_entropy
        if e0 > 0:
            change = ((e1 - e0) / e0) * 100
            if e1 < e0:
                learning_proof = (
                    f"エントロピー減少: {e0:.3f} → {e1:.3f} "
                    f"({change:+.1f}%) — モデルの確信度が向上"
                )
            elif e1 == e0:
                learning_proof = (
                    f"エントロピー安定: {e0:.3f} → {e1:.3f}"
                )
            else:
                learning_proof = (
                    f"エントロピー増加: {e0:.3f} → {e1:.3f} "
                    f"({change:+.1f}%) — 探索フェーズ"
                )

    return E2EResultV2(
        input_text=user_input,
        cycles=results,
        learning_proof=learning_proof,
    )

