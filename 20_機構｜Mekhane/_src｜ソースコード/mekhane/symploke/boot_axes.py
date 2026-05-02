from __future__ import annotations
# PROOF: [L2/インフラ] <- mekhane/symploke/boot_axes.py
# PURPOSE: Boot 軸ローダー群 — boot_integration.py から抽出された個別軸ロード関数
"""
Boot Axes — get_boot_context() から抽出された 16 軸ローダー.

各関数は同じパターン:
    1. デフォルト結果を定義
    2. ステータス出力 (stderr)
    3. try/except でグレースフルロード
    4. {"key": ..., "formatted": str} を返却

Design: boot_integration.py のゴッド関数 (600行) を構造化するためのリファクタリング。
API 互換は完全維持 — 戻り値の型と key は一切変えない。
"""


import copy
import json
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from pathlib import Path
from typing import Any, Optional


# ─────────────────────────────────────────────────────────────────────
# GPU Preflight
# ─────────────────────────────────────────────────────────────────────

# PURPOSE: boot_axes の gpu preflight 処理を実行する
def gpu_preflight() -> tuple[bool, str]:
    """GPU プリフライトチェック。

    Returns:
        (gpu_ok, reason)
    """
    try:
        from mekhane.symploke.gpu_guard import gpu_preflight as _gp, force_cpu_env
        status = _gp()
        if not status.gpu_available:
            print(f" ⚠️ GPU busy ({status.reason}), embedding 系は CPU フォールバック", file=sys.stderr)
            force_cpu_env()
            return False, status.reason
        print(f" 🟢 GPU available ({status.utilization}%, {status.memory_used_mb}MiB)", file=sys.stderr)
        return True, ""
    except Exception:  # noqa: BLE001
        return True, ""  # GPU チェック失敗時は楽観的に続行


# ─────────────────────────────────────────────────────────────────────
# 軸 A: Handoff
# ─────────────────────────────────────────────────────────────────────

# PURPOSE: handoffs を読み込む
def load_handoffs(mode: str, context: Optional[str] = None, **kw) -> dict:
    result: dict = {"latest": None, "related": [], "conversations": [], "count": 0}
    print(" [1/20] 📋 Searching Handoffs...", file=sys.stderr, end="", flush=True)
    try:
        from mekhane.symploke.handoff_search import get_boot_handoffs
        result = get_boot_handoffs(mode=mode, context=context)
        print(" Done.", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f" Failed ({e}).", file=sys.stderr)
    return result


# ─────────────────────────────────────────────────────────────────────
# 軸 B: Sophia (KI)
# ─────────────────────────────────────────────────────────────────────

# PURPOSE: sophia を読み込む
def load_sophia(mode: str, context: Optional[str] = None, **kw) -> dict:
    print(" [2/20] 📚 Ingesting Knowledge (Sophia)...", file=sys.stderr, end="", flush=True)
    ki_context = context or kw.get("ki_context")
    ki_result: dict = {"ki_items": [], "count": 0}
    try:
        # PURPOSE: [L2-auto] _run の関数定義
        def _run():
            from mekhane.symploke.sophia_ingest import get_boot_ki
            return get_boot_ki(context=ki_context, mode=mode)

        executor = ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(_run)
            ki_result = future.result(timeout=35.0)
            print(" Done.", file=sys.stderr)
        except (FutureTimeout, TimeoutError):
            print(" Timeout (skipped).", file=sys.stderr)
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
    except Exception as e:  # noqa: BLE001
        print(f" Failed ({e}).", file=sys.stderr)
    return ki_result


# ─────────────────────────────────────────────────────────────────────
# 軸 C: Persona
# ─────────────────────────────────────────────────────────────────────

# PURPOSE: persona を読み込む
def load_persona(mode: str, context: Optional[str] = None, **kw) -> dict:
    print(" [3/20] 👤 Loading Persona...", file=sys.stderr, end="", flush=True)
    from mekhane.symploke.persona import get_boot_persona
    result = get_boot_persona(mode=mode)
    print(" Done.", file=sys.stderr)
    return result


# ─────────────────────────────────────────────────────────────────────
# 軸 D: PKS (能動的知識プッシュ)
# ─────────────────────────────────────────────────────────────────────

# PURPOSE: pks を読み込む
def load_pks(mode: str, context: Optional[str] = None, **kw) -> dict:
    result: dict = {"nuggets": [], "count": 0, "formatted": ""}
    if mode == "fast":
        print(" [4/20] 🧠 PKS Engine skipped (fast mode).", file=sys.stderr)
        return result

    print(" [4/20] 🧠 Activating PKS Engine...", file=sys.stderr, end="", flush=True)
    ki_context = kw.get("ki_context")
    try:
        # PURPOSE: [L2-auto] _run の関数定義
        def _run():
            from mekhane.pks.pks_engine import PKSEngine
            engine = PKSEngine(threshold=0.5, max_push=3)
            topics: list = []
            if context:
                topics = [t.strip() for t in context.split(",")]
            elif ki_context:
                words = ki_context.split()[:5]
                topics = [w for w in words if len(w) > 2]
            if topics:
                engine.set_context(topics=topics)
                return engine.proactive_push(k=10)
            return []

        executor = ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(_run)
            nuggets = future.result(timeout=10.0)

            if nuggets:
                from mekhane.pks.pks_engine import PKSEngine
                dummy = PKSEngine()
                result = {
                    "nuggets": nuggets,
                    "count": len(nuggets),
                    "formatted": dummy.format_push_report(nuggets),
                }
            print(" Done.", file=sys.stderr)
        except (FutureTimeout, TimeoutError):
            print(" Timeout (skipped).", file=sys.stderr)
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
    except Exception as e:  # noqa: BLE001
        print(f" Failed ({e}).", file=sys.stderr)
    return result


# ─────────────────────────────────────────────────────────────────────
# 軸 E: Safety Contract Audit
# ─────────────────────────────────────────────────────────────────────

# PURPOSE: safety を読み込む
def load_safety(mode: str, context: Optional[str] = None, **kw) -> dict:
    result: dict = {"skills": 0, "workflows": 0, "errors": 0, "warnings": 0, "formatted": ""}
    print(" [5/20] 🛡️ Running Safety Contract Audit...", file=sys.stderr, end="", flush=True)
    try:
        from mekhane.dendron.skill_checker import run_audit
        from mekhane.paths import NOUS_DIR
        agent_dir = NOUS_DIR
        if agent_dir.exists():
            audit = run_audit(agent_dir)
            dist = audit.risk_distribution()
            lcm = audit.lcm_distribution()
            lines = ["🛡️ **Safety Contract**"]
            lines.append(f"  Skills: {audit.skills_checked} | WF: {audit.workflows_checked}")
            risk_parts = [f"{k}:{v}" for k, v in dist.items() if v > 0]
            if risk_parts:
                lines.append(f"  Risk: {' '.join(risk_parts)}")
            lcm_parts = [f"{k}:{v}" for k, v in lcm.items() if v > 0]
            if lcm_parts:
                lines.append(f"  LCM:  {' '.join(lcm_parts)}")
            if audit.errors > 0:
                lines.append(f"  ⚠️ {audit.errors} error(s), {audit.warnings} warning(s)")
            result = {
                "skills": audit.skills_checked,
                "workflows": audit.workflows_checked,
                "errors": audit.errors,
                "warnings": audit.warnings,
                "formatted": "\n".join(lines),
            }
        print(" Done.", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f" Failed ({e}).", file=sys.stderr)
    return result


# ─────────────────────────────────────────────────────────────────────
# 軸 H: EPT (Existence Purpose Tensor)
# ─────────────────────────────────────────────────────────────────────

# PURPOSE: ept を読み込む
def load_ept(mode: str, context: Optional[str] = None, **kw) -> dict:
    result: dict = {"score": 0, "total": 0, "pct": 0, "formatted": ""}
    if mode == "fast":
        print(" [6/20] 📐 EPT Matrix skipped (fast mode).", file=sys.stderr)
        return result
    print(" [6/20] 📐 Running EPT Matrix...", file=sys.stderr, end="", flush=True)
    try:
        # PURPOSE: [L2-auto] _run の関数定義
        def _run():
            from mekhane.dendron.checker import DendronChecker
            c = DendronChecker(
                check_structure=True,
                check_function_nf=True,
                check_verification=True,
            )
            r = c.check(Path(__file__).parent.parent)  # mekhane/
            total = r.total_structure_checks + r.total_function_nf_checks + r.total_verification_checks
            ok = r.structure_ok + r.function_nf_ok + r.verification_ok
            pct = (ok / total * 100) if total > 0 else 0
            return {
                "score": ok, "total": total, "pct": pct,
                "nf2": f"{r.structure_ok}/{r.total_structure_checks}",
                "nf3": f"{r.function_nf_ok}/{r.total_function_nf_checks}",
                "bcnf": f"{r.verification_ok}/{r.total_verification_checks}",
                "formatted": (
                    f"📐 **EPT**: {ok}/{total} ({pct:.0f}%) "
                    f"[NF2:{r.structure_ok}/{r.total_structure_checks} "
                    f"NF3:{r.function_nf_ok}/{r.total_function_nf_checks} "
                    f"BCNF:{r.verification_ok}/{r.total_verification_checks}]"
                ),
            }
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(_run)
            result = future.result(timeout=15.0)
            print(" Done.", file=sys.stderr)
        except (FutureTimeout, TimeoutError):
            print(" Timeout (skipped).", file=sys.stderr)
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
    except Exception as e:  # noqa: BLE001
        print(f" Failed ({e}).", file=sys.stderr)
    return result


# ─────────────────────────────────────────────────────────────────────
# 軸 G: Digestor 候補 (論文レコメンド)
# ─────────────────────────────────────────────────────────────────────

# PURPOSE: digestor を読み込む
def load_digestor(mode: str, context: Optional[str] = None, **kw) -> dict:
    result: dict = {"candidates": [], "count": 0, "formatted": ""}
    print(" [7/20] 📄 Loading Digest Candidates...", file=sys.stderr, end="", flush=True)
    try:
        import glob
        from mekhane.paths import OUTPUTS_DIR
        digest_dir = OUTPUTS_DIR / "digestor"
        reports = sorted(glob.glob(str(digest_dir / "digest_report_*.json")), reverse=True)
        if reports:
            with open(reports[0], "r", encoding="utf-8") as f:
                report = json.load(f)
            candidates = report.get("candidates", [])[:3]
            if candidates:
                lines = ["📄 **Digest Candidates** (今日の論文推薦)"]
                for i, c in enumerate(candidates, 1):
                    title = c.get("title", "Unknown")[:60]
                    score = c.get("score", 0)
                    topics = ", ".join(c.get("matched_topics", [])[:2])
                    lines.append(f"  {i}. [{score:.2f}] {title}... ({topics})")
                result = {
                    "candidates": candidates,
                    "count": len(candidates),
                    "formatted": "\n".join(lines),
                }
        print(" Done.", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f" Failed ({e}).", file=sys.stderr)
    return result


# ─────────────────────────────────────────────────────────────────────
# 軸 F: Attractor Dispatch Engine (最大: FEP v2 + TheoremAttractor 統合)
# ─────────────────────────────────────────────────────────────────────

# PURPOSE: attractor を読み込む
def load_attractor(mode: str, context: Optional[str] = None, **kw) -> dict:
    """Attractor 軸: Series 推薦 + Theorem 粒度 + FEP v2 統合推論."""
    result: dict = {"series": [], "workflows": [], "llm_format": "", "formatted": ""}
    gpu_ok = kw.get("gpu_ok", True)
    attractor_context = context

    if not attractor_context:
        print(" [8/20] 🎯 Attractor skipped (no context & no Handoff).", file=sys.stderr)
        return result

    print(" [8/20] 🎯 Attractor Dispatch...", file=sys.stderr, end="", flush=True)
    try:
        # PURPOSE: [L2-auto] _run の関数定義
        def _run():
            from mekhane.fep.attractor_advisor import AttractorAdvisor
            advisor = AttractorAdvisor(force_cpu=not gpu_ok)

            # Basin bias 復元
            _apply_basin_bias(advisor)
            _apply_basin_learner(advisor)

            rec = advisor.recommend(attractor_context)
            llm_fmt = advisor.format_for_llm(attractor_context)

            # 統合情報収集
            from mekhane.symploke.boot_integration import extract_dispatch_info
            dispatch_info = extract_dispatch_info(attractor_context, gpu_ok=gpu_ok)
            theorem_detail = _build_theorem_detail(attractor_context, gpu_ok)
            fep_v2_result, learning_diff_fmt = _run_fep_v2(
                rec, attractor_context, gpu_ok,
            )

            # フォーマット
            formatted = _format_attractor(
                llm_fmt, theorem_detail, dispatch_info,
                fep_v2_result, learning_diff_fmt,
            )

            return {
                "series": rec.series,
                "workflows": rec.workflows,
                "llm_format": llm_fmt,
                "confidence": rec.confidence,
                "oscillation": rec.oscillation.value,
                "advice": rec.advice,
                "dispatch_primary": dispatch_info["primary"],
                "dispatch_alternatives": dispatch_info["alternatives"],
                "theorem_detail": theorem_detail,
                "fep_v2": fep_v2_result,
                "formatted": formatted,
            }

        executor = ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(_run)
            result = future.result(timeout=30.0)
            print(" Done.", file=sys.stderr)
        except (FutureTimeout, TimeoutError):
            print(" Timeout (skipped).", file=sys.stderr)
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
    except Exception as e:  # noqa: BLE001
        print(f" Failed ({e}).", file=sys.stderr)
    return result


# PURPOSE: [L2-auto] _apply_basin_bias の関数定義
def _apply_basin_bias(advisor: Any) -> None:
    """Basin Logger bias 復元."""
    try:
        from mekhane.fep.basin_logger import BasinLogger
        bl = BasinLogger()
        log_files = sorted(bl.log_dir.glob("attractor_log_*.jsonl"))
        if log_files:
            for lf in log_files[-3:]:
                bl.load_biases(lf)
            advisor._attractor.apply_bias(bl._biases)
    except Exception:  # noqa: BLE001
        pass


# PURPOSE: [L2-auto] _apply_basin_learner の関数定義
def _apply_basin_learner(advisor: Any) -> None:
    """BasinLearner 学習済み重み適用."""
    try:
        from mekhane.fep.basin_learner import BasinLearner
        learner = BasinLearner()
        if learner.load_history() > 0:
            overrides = learner.get_weight_overrides()
            if overrides:
                for series, weight in overrides.items():
                    adjustment = (weight - 1.0) * 0.1
                    advisor._attractor._bias_adjustments[series] = adjustment
    except Exception:  # noqa: BLE001
        pass


# PURPOSE: [L2-auto] _build_theorem_detail の関数定義
def _build_theorem_detail(context: str, gpu_ok: bool) -> dict:
    """TheoremAttractor による 24 定理粒度の詳細."""
    try:
        from mekhane.fep.theorem_attractor import TheoremAttractor
        ta = TheoremAttractor(force_cpu=not gpu_ok)
        top_theorems = ta.suggest(context, top_k=5)
        flow = ta.simulate_flow(context, steps=10)
        mixture = ta.diagnose_mixture(context)
        return {
            "top_theorems": [
                {"theorem": r.theorem, "name": r.name,
                 "series": r.series, "sim": round(r.similarity, 3),
                 "command": r.command}
                for r in top_theorems
            ],
            "flow_converged": flow.converged_at,
            "flow_final": [t for t, _ in flow.final_theorems[:3]],
            "mixture": {
                "entropy": mixture.entropy,
                "dominant_series": mixture.dominant_series,
                "series_distribution": mixture.series_distribution,
            },
        }
    except Exception:  # noqa: BLE001
        return {}


# PURPOSE: [L2-auto] _run_fep_v2 の関数定義
def _run_fep_v2(rec: Any, context: str, gpu_ok: bool) -> tuple[dict, str]:
    """FEP v2 Agent: 統合認知判断 (48-state)."""
    import numpy as np
    fep_v2_result: dict = {}
    learning_diff_fmt = ""
    try:
        from mekhane.fep.fep_agent_v2 import HegemonikónFEPAgentV2
        from mekhane.fep.state_spaces_v2 import SERIES_STATES
        from mekhane.fep.persistence import (
            save_snapshot, diff_A, format_learning_diff,
        )

        agent = HegemonikónFEPAgentV2()
        agent.load_learned_A()
        agent.load_learned_B()
        agent.load_epsilon()

        A_before = copy.deepcopy(agent.A)

        _s2obs = {s: 8 + i for i, s in enumerate(SERIES_STATES)}
        att_series = rec.series
        if isinstance(att_series, list):
            att_series = att_series[0]
        topic_obs = _s2obs.get(att_series, 8)

        r1 = agent.step(topic_obs)
        r2 = agent.step(topic_obs)
        final = r2

        agent.update_A_dirichlet(topic_obs)
        agent.update_B_dirichlet(final["action"])

        predicted_obs = int(np.argmax(agent._get_predicted_observation()))
        agent.track_prediction(topic_obs, predicted_obs)
        agent.update_epsilon()

        agent.save_learned_A()
        agent.save_learned_B()
        agent.save_epsilon()

        save_snapshot(agent, label="boot")
        learning_diff = diff_A(A_before, agent.A)
        learning_diff_fmt = format_learning_diff(learning_diff)

        conf_pct = int(100.0 * max(final["beliefs"]))
        explanation = agent.explain(final)
        fep_v2_result = {
            "action": final["action_name"],
            "selected_series": final.get("selected_series"),
            "entropy": round(final["entropy"], 3),
            "confidence_pct": conf_pct,
            "attractor_series": att_series,
            "agreement": final.get("selected_series") == att_series,
            "map_state": final["map_state_names"],
            "explanation": explanation,
            "learning_diff": learning_diff,
            "epsilon": agent.epsilon_summary(),
        }

        # Convergence tracking (pushout)
        try:
            from mekhane.fep.convergence_tracker import record_agreement
            conv_summary = record_agreement(
                agent_series=final.get("selected_series"),
                attractor_series=att_series,
                agent_action=final["action_name"],
                epsilon=dict(agent.epsilon),
                agent_confidence=max(final["beliefs"]),
                attractor_similarity=rec.confidence if hasattr(rec, 'confidence') else 0.0,
            )
            fep_v2_result["convergence"] = conv_summary
        except Exception:  # noqa: BLE001
            pass

    except Exception:  # noqa: BLE001
        pass
    return fep_v2_result, learning_diff_fmt


# PURPOSE: [L2-auto] _format_attractor の関数定義
def _format_attractor(
    llm_fmt: str,
    theorem_detail: dict,
    dispatch_info: dict,
    fep_v2_result: dict,
    learning_diff_fmt: str,
) -> str:
    """Attractor 軸のフォーマット済み出力."""
    parts: list[str] = []
    if llm_fmt:
        parts.append(f"🎯 **Attractor**: {llm_fmt}")
    if theorem_detail.get("top_theorems"):
        tops = ", ".join(
            f"{t['theorem']}({t['sim']:.2f})"
            for t in theorem_detail["top_theorems"][:3]
        )
        mix = theorem_detail.get("mixture", {})
        h_str = f" | H={mix['entropy']:.2f}" if mix.get("entropy") is not None else ""
        dom = f" dom={mix['dominant_series']}" if mix.get("dominant_series") else ""
        parts.append(f"   🔬 Theorems: {tops}{h_str}{dom}")
    if dispatch_info.get("primary"):
        parts.append(f"   📎 Dispatch: {dispatch_info['dispatch_formatted']}")
    if fep_v2_result:
        act = fep_v2_result["action"]
        sel = fep_v2_result.get("selected_series") or "-"
        ent = fep_v2_result["entropy"]
        conf = fep_v2_result["confidence_pct"]
        att_s = fep_v2_result.get("attractor_series", "?")
        agree = "✓一致" if fep_v2_result.get("agreement") else "✗不一致"
        parts.append(
            f"   🧠 FEP v2: {act} [Series={sel}] "
            f"(entropy={ent}, conf={conf}%) ↔ ATT={att_s} [{agree}]"
        )
        expl = fep_v2_result.get("explanation", "")
        if expl:
            for line in expl.split("\n"):
                parts.append(f"      {line}")
        conv = fep_v2_result.get("convergence")
        if conv:
            from mekhane.fep.convergence_tracker import format_convergence
            parts.append(f"   {format_convergence(conv)}")
        eps_info = fep_v2_result.get("epsilon", {})
        eps_vals = eps_info.get("epsilon", {})
        if eps_vals:
            eps_str = " ".join(f"{k}={v:.3f}" for k, v in eps_vals.items())
            parts.append(f"   ε: {eps_str}")
    if learning_diff_fmt:
        for line in learning_diff_fmt.split("\n"):
            parts.append(f"   {line}")
    return "\n".join(parts) if parts else ""


# ─────────────────────────────────────────────────────────────────────
# 軸 I: Projects
# ─────────────────────────────────────────────────────────────────────

# PURPOSE: projects を読み込む
def load_projects(mode: str, context: Optional[str] = None, **kw) -> dict:
    result: dict = {"projects": [], "active": 0, "dormant": 0, "total": 0, "formatted": ""}
    print(" [9/20] 📦 Loading Projects Registry...", file=sys.stderr, end="", flush=True)
    try:
        from mekhane.symploke.boot_integration import _load_projects
        from mekhane.paths import HGK_ROOT
        result = _load_projects(HGK_ROOT)
        print(" Done.", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f" Failed ({e}).", file=sys.stderr)
    return result


# ─────────────────────────────────────────────────────────────────────
# 軸 I.5: Helm (Boulēsis 温度別願望)
# ─────────────────────────────────────────────────────────────────────

# PURPOSE: Sprint/Incubator/Backlog の3温度ファイルを読み込み、セッション開始時に表示する
def load_helm(mode: str, context: Optional[str] = None, **kw) -> dict:
    """Helm 軸: Boulēsis の Sprint (HOT) / Incubator (WARM) / Backlog (COLD) を読み込む."""
    result: dict = {"sprint": [], "incubator": [], "backlog": [], "formatted": ""}
    if mode == "fast":
        print(" [10/20] 🧭 Helm skipped (fast mode).", file=sys.stderr)
        return result
    print(" [10/20] 🧭 Loading Helm (Sprint/Incubator/Backlog)...", file=sys.stderr, end="", flush=True)
    try:
        from mekhane.paths import HGK_ROOT
        helm_dir = HGK_ROOT / "10_知性｜Nous" / "04_企画｜Boulēsis" / "00_舵｜Helm"
        if not helm_dir.exists():
            print(" No Helm dir.", file=sys.stderr)
            return result

        lines = ["🧭 **Helm** (Boulēsis 温度別願望)"]

        # Sprint (HOT) — <:data: ブロック内の id: S-xxx + title: ペアを抽出
        sprint_items = []
        sprint_file = helm_dir / "march_2026_sprint.typos"
        if sprint_file.exists():
            content = sprint_file.read_text(encoding="utf-8")
            current_id = ""
            for line in content.split("\n"):
                stripped = line.strip()
                if stripped.startswith("id: S-"):
                    current_id = stripped.replace("id: ", "")
                elif stripped.startswith("title:") and current_id:
                    title = stripped.replace("title:", "").strip()
                    sprint_items.append(f"{current_id}: {title}"[:80])
                    current_id = ""
        if sprint_items:
            lines.append(f"  🔥 **Sprint (HOT)** — {len(sprint_items)}件")
            for item in sprint_items[:6]:
                lines.append(f"    • {item}")

        # Incubator (WARM) — .typos ファイル内の [wish] 行を抽出
        incubator_items = []
        incubator_file = helm_dir / "incubator.typos"
        if incubator_file.exists():
            content = incubator_file.read_text(encoding="utf-8")
            for line in content.split("\n"):
                stripped = line.strip()
                if stripped.startswith("- [wish]"):
                    incubator_items.append(stripped.replace("- [wish]", "").strip()[:60])
        if incubator_items:
            lines.append(f"  🟡 **Incubator (WARM)** — {len(incubator_items)}件")
            for item in incubator_items[:5]:
                lines.append(f"    • {item}")
            if len(incubator_items) > 5:
                lines.append(f"    ... +{len(incubator_items) - 5}件")

        # Backlog (COLD) — テーブル形式 (| N | **内容** | ...) から内容列を抽出
        backlog_items = []
        backlog_file = helm_dir / "backlog.md"
        if backlog_file.exists():
            content = backlog_file.read_text(encoding="utf-8")
            import re as _re
            for line in content.split("\n"):
                stripped = line.strip()
                # テーブル行: | 数字 | 内容 | ... |
                m = _re.match(r"^\|\s*(\d+)\s*\|(.+?)\|", stripped)
                if m:
                    cell = m.group(2).strip()
                    # **太字** を除去して表示
                    cell = _re.sub(r"\*\*(.+?)\*\*", r"\1", cell)
                    backlog_items.append(cell[:70])
        if backlog_items:
            lines.append(f"  ❄️ **Backlog (COLD)** — {len(backlog_items)}件")

        # サマリー行
        total = len(sprint_items) + len(incubator_items) + len(backlog_items)
        lines.append(f"  📊 合計: {total}件 (HOT {len(sprint_items)} / WARM {len(incubator_items)} / COLD {len(backlog_items)})")

        result = {
            "sprint": sprint_items,
            "incubator": incubator_items,
            "backlog": backlog_items,
            "total": total,
            "formatted": "\n".join(lines),
        }
        print(f" Done ({total} wishes).", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f" Failed ({e}).", file=sys.stderr)
    return result


# ─────────────────────────────────────────────────────────────────────
# 軸 J: Skills
# ─────────────────────────────────────────────────────────────────────

# PURPOSE: skills を読み込む
def load_skills(mode: str, context: Optional[str] = None, **kw) -> dict:
    result: dict = {"skills": [], "count": 0, "skill_paths": [], "formatted": ""}
    print(" [11/20] 🧠 Loading Skills...", file=sys.stderr, end="", flush=True)
    try:
        from mekhane.symploke.boot_integration import _load_skills
        from mekhane.paths import HGK_ROOT
        result = _load_skills(HGK_ROOT)
        print(f" Done ({result['count']} skills).", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f" Failed ({e}).", file=sys.stderr)
    return result


# ─────────────────────────────────────────────────────────────────────
# 軸 K: Doxa (信念ストア)
# ─────────────────────────────────────────────────────────────────────

# PURPOSE: doxa を読み込む
def load_doxa(mode: str, context: Optional[str] = None, **kw) -> dict:
    result: dict = {"beliefs_loaded": 0, "active_count": 0, "promotion_candidates": [], "formatted": ""}
    print(" [12/20] 🧿 Loading Doxa Beliefs...", file=sys.stderr, end="", flush=True)
    try:
        from mekhane.symploke.doxa_boot import load_doxa_for_boot
        doxa_boot = load_doxa_for_boot()
        result = {
            "beliefs_loaded": doxa_boot.beliefs_loaded,
            "active_count": doxa_boot.active_count,
            "archived_count": doxa_boot.archived_count,
            "promotion_candidates": [
                {"content": c.belief.content[:50], "score": c.score, "reasons": c.reasons}
                for c in doxa_boot.promotion_candidates
            ],
            "formatted": doxa_boot.summary,
        }
        print(f" Done ({doxa_boot.beliefs_loaded} beliefs).", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f" Failed ({e}).", file=sys.stderr)
    return result


# ─────────────────────────────────────────────────────────────────────
# 軸 L: Credit Assignment (フィードバック学習)
# ─────────────────────────────────────────────────────────────────────

# PURPOSE: feedback を読み込む
def load_feedback(mode: str, context: Optional[str] = None, **kw) -> dict:
    result: dict = {"total": 0, "accept_rate": 0.0, "formatted": ""}
    print(" [13/20] 🎓 Loading Feedback History...", file=sys.stderr, end="", flush=True)
    try:
        from mekhane.fep.credit_assignment import (
            load_feedback_history,
            feedback_summary,
        )
        records = load_feedback_history(months=3)
        if records:
            summary = feedback_summary(records)
            lines = [f"### 🎓 軸 L: Credit Assignment ({summary['total']}件)"]
            lines.append(f"Accept Rate: {summary['accept_rate']:.0%}")
            if summary["common_corrections"]:
                corrections = ", ".join(
                    f"{f}→{t}({c})" for f, t, c in summary["common_corrections"][:3]
                )
                lines.append(f"Common Corrections: {corrections}")
            result = {
                "total": summary["total"],
                "accept_rate": summary["accept_rate"],
                "per_series": summary.get("per_series", {}),
                "formatted": "\n".join(lines),
            }
            print(f" Done ({summary['total']} records, {summary['accept_rate']:.0%} accept).", file=sys.stderr)
        else:
            print(" No feedback yet.", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f" Failed ({e}).", file=sys.stderr)
    return result


# ─────────────────────────────────────────────────────────────────────
# 軸 M: Proactive Push (知識推薦)
# ─────────────────────────────────────────────────────────────────────

# PURPOSE: proactive push を読み込む
def load_proactive_push(mode: str, context: Optional[str] = None, **kw) -> dict:
    """Proactive Push 軸: 知識が自ら語りかけてくる推薦."""
    result: dict = {"recommendations": [], "count": 0, "formatted": ""}
    if mode == "fast":
        print(" [14/20] 💡 Proactive Push skipped (fast mode).", file=sys.stderr)
        return result

    print(" [14/20] 💡 Proactive Push...", file=sys.stderr, end="", flush=True)
    try:
        from mekhane.anamnesis.proactive_push import ProactivePush
        push = ProactivePush(max_recommendations=3)
        push_result = push.boot_recommendations(context)

        if push_result.recommendations:
            result = {
                "recommendations": [
                    {
                        "title": r.title,
                        "source_type": r.source_type,
                        "relevance": r.relevance,
                        "benefit": r.benefit,
                        "actions": r.actions,
                    }
                    for r in push_result.recommendations
                ],
                "count": len(push_result.recommendations),
                "retrieval_time": push_result.retrieval_time,
                "formatted": ProactivePush.format_recommendations(push_result),
            }
        print(f" Done ({len(push_result.recommendations)} recs).", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f" Failed ({e}).", file=sys.stderr)
    return result


# ─────────────────────────────────────────────────────────────────────
# 軸 N: Violation Trends (違反傾向)
# ─────────────────────────────────────────────────────────────────────

# PURPOSE: violations を読み込む
def load_violations(mode: str, context: Optional[str] = None, **kw) -> dict:
    """Violation Trends 軸: 直近の違反パターン傾向を /boot に表示."""
    result: dict = {"total": 0, "patterns": {}, "recurrence": 0, "formatted": ""}
    print(" [15/20] ⚠️ Analyzing Violation Trends...", file=sys.stderr, end="", flush=True)
    try:
        from scripts.violation_analyzer import parse_violations, analyze, format_boot_summary
        entries = parse_violations()
        stats = analyze(entries, since_days=7)
        result = {
            "total": stats["total"],
            "patterns": stats["patterns"],
            "recurrence": stats["recurrence"],
            "formatted": format_boot_summary(stats),
        }
        print(" Done.", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f" Failed ({e}).", file=sys.stderr)
    return result


# ─────────────────────────────────────────────────────────────────────
# 軸 O: Gnōsis Advice (知識アドバイス)
# ─────────────────────────────────────────────────────────────────────

# PURPOSE: gnosis advice を読み込む
def load_gnosis_advice(mode: str, context: Optional[str] = None, **kw) -> dict:
    """Gnōsis Advice 軸: WF に関連する学術知識のハイライト."""
    result: dict = {"advice": "", "formatted": ""}
    if mode == "fast":
        print(" [16/20] 📖 Gnōsis Advice skipped (fast mode).", file=sys.stderr)
        return result
    print(" [16/20] 📖 Loading Gnōsis Advice...", file=sys.stderr, end="", flush=True)
    try:
        from scripts.gnosis_advisor import daily_topics
        advice = daily_topics()
        result = {"advice": advice, "formatted": advice}
        print(" Done.", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f" Failed ({e}).", file=sys.stderr)
    return result


# ─────────────────────────────────────────────────────────────────────
# 軸 P: Ideas (HGK Gateway アイデア)
# ─────────────────────────────────────────────────────────────────────

# PURPOSE: HGK Gateway で捕捉されたアイデアメモを読み込む
def load_ideas(mode: str, context: Optional[str] = None, **kw) -> dict:
    """Ideas 軸: HGK Gateway で捕捉された未処理アイデアを /boot に表示."""
    result: dict = {"ideas": [], "count": 0, "formatted": ""}
    print(" [17/20] 💡 Loading Gateway Ideas...", file=sys.stderr, end="", flush=True)
    try:
        from mekhane.paths import INCOMING_DIR
        idea_dir = INCOMING_DIR
        if not idea_dir.exists():
            print(" No ideas dir.", file=sys.stderr)
            return result

        idea_files = sorted(idea_dir.glob("idea_*.md"), reverse=True)
        if not idea_files:
            print(" No ideas.", file=sys.stderr)
            return result

        ideas = []
        for fp in idea_files:
            content = fp.read_text(encoding="utf-8")
            # Parse metadata from markdown
            tags = ""
            date_str = ""
            body_lines = []
            in_body = False
            for line in content.split("\n"):
                if line.startswith("> **タグ**:"):
                    tags = line.split(":", 1)[1].strip()
                elif line.startswith("> **日時**:"):
                    date_str = line.split(":", 1)[1].strip()
                elif line.strip() == "---":
                    if in_body:
                        break  # End of body
                    in_body = True
                elif in_body and line.strip():
                    body_lines.append(line.strip())

            # First non-empty body line as title (truncated)
            title = body_lines[0][:80] if body_lines else fp.stem
            ideas.append({
                "file": fp.name,
                "title": title,
                "tags": tags,
                "date": date_str,
            })

        lines = [f"💡 **Gateway Ideas** ({len(ideas)}件 — 未処理アイデア)"]
        for i, idea in enumerate(ideas, 1):
            tag_str = f" [{idea['tags']}]" if idea["tags"] and idea["tags"] != "未分類" else ""
            lines.append(f"  {i}. {idea['title']}{tag_str}")
        lines.append(f"  📂 `{INCOMING_DIR}/`")

        result = {
            "ideas": ideas,
            "count": len(ideas),
            "formatted": "\n".join(lines),
        }
        print(f" Done ({len(ideas)} ideas).", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f" Failed ({e}).", file=sys.stderr)
    return result


# ─────────────────────────────────────────────────────────────────────
# 軸 Q: Session Resume (前セッションコンテキスト復元)
# ─────────────────────────────────────────────────────────────────────

def load_session_resume(mode: str, context: Optional[str] = None, **kw) -> dict:
    """Session Resume 軸: 前セッションの生テキストコンテキストを復元する."""
    result: dict = {"chunks": 0, "formatted": ""}
    if mode == "fast":
        print(" [18/20] 🔄 Session Resume skipped (fast mode).", file=sys.stderr)
        return result

    print(" [18/20] 🔄 Loading Session Resume...", file=sys.stderr, end="", flush=True)
    try:
        from mekhane.ochema.session_notes import SessionNotes
        from mekhane.ochema.session_store import get_default_store
        
        store = get_default_store()
        sessions = store.list_sessions()
        if sessions:
            # 最後のセッションIDを取得
            latest_session_id = sessions[-1]['session_id']
            notes = SessionNotes()
            
            # 生テキスト形式で最新数ターンのチャンクを取得
            context_chunks = notes.resume_context(latest_session_id, format="raw", max_chunks=3)
            if context_chunks:
                lines = [f"🔄 **Session Resume** (ID: `{latest_session_id[:8]}`)"]
                for i, c in enumerate(context_chunks):
                    # ファイル名だけ抽出
                    filename = Path(c["path"]).name
                    lines.append(f"\n> **Chunk {i+1}** (`{filename}`):")
                    # コンテキストを表示用にトリミングして引用符をつける
                    content = c["content"].strip()
                    if len(content) > 300:
                        content = content[:300] + "...\n(truncated)"
                    content = content.replace('\n', '\n> ')
                    lines.append(f"> {content}")
                
                result = {
                    "chunks": len(context_chunks),
                    "formatted": "\n".join(lines),
                }
        print(f" Done ({result['chunks']} chunks).", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f" Failed ({e}).", file=sys.stderr)
    return result


# ─────────────────────────────────────────────────────────────────────
# State Space Distribution — FEP Markov blanket の4状態空間分類
# ─────────────────────────────────────────────────────────────────────

# PURPOSE: MCP ツール名パターンから μ/a/s/boundary を自動推論する
# FEP: μ=Internal(認知), a=Active(環境変更), s=Sensory(観測), η=External(対象外)

# ツール名に含まれるキーワード → 状態空間ラベルの推論ルール
_STATE_HEURISTICS: dict[str, str] = {
    # s (Sensory) — 環境の観測
    "search": "s", "get": "s", "list": "s", "check": "s",
    "status": "s", "audit": "s", "metrics": "s", "scan": "s",
    "ping": "s", "history": "s", "stats": "s", "sources": "s",
    "backlinks": "s", "quota": "s", "info": "s", "details": "s",
    "citations": "s", "incoming": "s", "candidates": "s",
    "dashboard": "s", "escalate": "s", "health": "s",
    # μ (Internal) — 認知・推論・信念形成
    "ask": "μ", "dispatch": "μ", "compile": "μ", "plan": "μ",
    "recommend": "μ", "attractor": "μ", "feedback": "μ",
    "parse": "μ", "validate": "μ", "generate": "μ",
    "expand": "μ", "policy": "μ", "topics": "μ",
    # a (Active) — 環境への作用
    "create": "a", "batch": "a", "export": "a",
    "log_violation": "a", "mark": "a", "send": "a",
    "snapshot": "a", "digest": "a",
    # boundary (μ↔a) — 複数状態に跨る
    "run": "μ→a", "research": "s→μ", "verify": "s+a",
    "gate": "s→a", "distill": "μ→a", "execute": "μ→a",
}

# 自動推論が不正確なツールの手動オーバーライド
_STATE_OVERRIDES: dict[str, str] = {
    "sympatheia_feedback": "μ",         # feedback だが実態は Internal パラメータ調整
    "periskope_track": "μ",             # track だが実態は状態管理
    "sekisho_gate": "s→a",              # 監査 + PASS/BLOCK 判定 + gate_token 永続化
    "context_rot_distill": "μ→a",       # コンテキスト蒸留 + ファイル書出
    "ochema_plan_task": "μ",            # plan + task だが認知 (タスク分解)
    "sympatheia_notifications": "s+a",  # list=s, send=a
    "sympatheia_verify_on_edit": "s+a", # テスト実行=a + 結果観測=s
    "run_digestor": "s→μ→a",           # 収集→分析→書出
    "ask_with_tools": "μ→a",           # LLM推論 + ツール実行 (blanket bypass risk)
    "start_chat": "μ",                 # 会話状態管理
    "send_chat": "μ",                  # 会話送信
    "close_chat": "μ",                 # 会話終了
    "ask_chat": "μ",                   # マルチターン推論
    "ask_cortex": "μ",                 # Gemini 直接推論
}

# 境界ラベルの判定パターン
_BOUNDARY_MARKERS = {"→", "+"}


# PURPOSE: ツール名から状態空間ラベルを推論する
def _classify_tool(tool_name: str) -> str:
    """MCP ツール名 → 状態空間ラベルを推論.

    優先順位: 手動オーバーライド > キーワードヒューリスティック > デフォルト(s)
    """
    # 1. 手動オーバーライド (完全一致)
    if tool_name in _STATE_OVERRIDES:
        return _STATE_OVERRIDES[tool_name]

    # 2. サーバー名プレフィックスを除去 (e.g. "hermeneus_dispatch" → "dispatch")
    parts = tool_name.split("_")
    # 先頭がサーバー名の場合を考慮: 2語以上なら後方パーツを使う
    keywords_to_check = parts[1:] if len(parts) > 1 else parts

    # 3. キーワードヒューリスティック (後方パーツ優先)
    for kw in reversed(keywords_to_check):
        if kw in _STATE_HEURISTICS:
            return _STATE_HEURISTICS[kw]

    # 4. デフォルト: 分類不明は s (保守的: 観測と見なす)
    return "s"


# PURPOSE: 状態空間ラベルからカテゴリに集約する
def _label_to_category(label: str) -> str:
    """状態空間ラベルを4カテゴリに集約."""
    if any(m in label for m in _BOUNDARY_MARKERS):
        return "boundary"
    if label == "μ":
        return "μ"
    if label == "a":
        return "a"
    return "s"


# PURPOSE: 全 MCP ツール名を収集する (8サーバーの tool descriptions から)
def _collect_mcp_tools() -> list[str]:
    """システムプロンプトに登録された MCP ツール一覧を返す.

    実行時に各 MCP サーバーの list_tools を呼ぶのはコストが高いため、
    既知のツール名を静的リストとして保持する。
    新ツール追加時はこのリストを更新する。
    """
    return [
        # Hermeneus (7)
        "hermeneus_dispatch", "hermeneus_compile", "hermeneus_execute",
        "hermeneus_run", "hermeneus_audit", "hermeneus_list_workflows",
        "hermeneus_export_session",
        # Ochema (14)
        "ask", "ask_cortex", "ask_chat", "ask_with_tools",
        "start_chat", "send_chat", "close_chat",
        "context_rot_distill", "context_rot_status", "session_info",
        "models", "cortex_quota", "status", "ochema_plan_task",
        # Periskope (6)
        "periskope_search", "periskope_research", "periskope_benchmark",
        "periskope_metrics", "periskope_sources", "periskope_track",
        # Sympatheia (12)
        "sympatheia_attractor", "sympatheia_basanos_scan",
        "sympatheia_verify_on_edit", "sympatheia_wbc",
        "sympatheia_log_violation", "sympatheia_notifications",
        "sympatheia_violation_dashboard", "sympatheia_peira_health",
        "sympatheia_feedback", "sympatheia_escalate",
        "sympatheia_digest", "sympatheia_status",
        # Mneme (7)
        "search", "search_papers", "backlinks", "graph_stats",
        "stats", "sources", "recommend_model", "dendron_check",
        "dendron_mece_check",
        # Sekisho (3)
        "sekisho_gate", "sekisho_audit", "sekisho_history",
        # Digestor (7)
        "paper_search", "paper_details", "paper_citations",
        "check_incoming", "list_candidates", "get_topics",
        "run_digestor", "mark_processed",
        # Jules (4)
        "jules_create_task", "jules_batch_execute",
        "jules_get_status", "jules_list_repos",
        # Phantazein (5)
        "phantazein_ping", "phantazein_boot",
        "phantazein_snapshot", "phantazein_consistency",
        "phantazein_status",
        # Typos (6)
        "compile", "expand", "generate", "parse", "validate", "policy_check",
    ]


# PURPOSE: State Space Distribution を計算して Boot Context 軸として返す
def load_state_space(mode: str, context: Optional[str] = None, **kw) -> dict:
    """FEP Markov blanket の4状態空間分布を計算する.

    Returns:
        dict: {
            "distribution": {"μ": N, "a": N, "s": N, "boundary": N},
            "total": int,
            "percentages": {"μ": float, "a": float, ...},
            "boundary_tools": [str, ...],  # μ↔a 境界ツール一覧
            "risk_tools": [str, ...],      # blanket bypass のリスクツール
            "tool_labels": {str: str, ...}, # 全ツールのラベル
            "formatted": str
        }
    """
    result: dict[str, Any] = {
        "distribution": {}, "total": 0, "percentages": {},
        "boundary_tools": [], "risk_tools": [],
        "tool_labels": {}, "formatted": "",
    }

    try:
        tools = _collect_mcp_tools()
        total = len(tools)

        # 分類
        labels: dict[str, str] = {}
        categories: dict[str, int] = {"μ": 0, "a": 0, "s": 0, "boundary": 0}
        boundary_tools: list[str] = []
        risk_tools: list[str] = []

        for tool in tools:
            label = _classify_tool(tool)
            labels[tool] = label
            cat = _label_to_category(label)
            categories[cat] = categories.get(cat, 0) + 1

            if cat == "boundary":
                boundary_tools.append(f"{tool} ({label})")

            # Blanket bypass リスク検出: μ→a で LLM が環境を直接操作
            if "→a" in label and ("ask" in tool or "llm" in tool.lower()):
                risk_tools.append(tool)

        # ask_with_tools は常にリスク
        if "ask_with_tools" not in risk_tools and "ask_with_tools" in labels:
            risk_tools.append("ask_with_tools")

        # パーセンテージ計算
        pcts = {}
        for cat, count in categories.items():
            pcts[cat] = round(count / total * 100) if total > 0 else 0

        # フォーマット
        lines = ["🧬 **State Space Distribution** (FEP Markov blanket)"]
        for cat, emoji in [("μ", "🧠"), ("a", "⚡"), ("s", "👁"), ("boundary", "🔗")]:
            count = categories.get(cat, 0)
            pct = pcts.get(cat, 0)
            desc = {"μ": "Internal (認知)", "a": "Active (能動)",
                    "s": "Sensory (観測)", "boundary": "μ↔a 境界"}[cat]
            lines.append(f"   {emoji} {cat}: {pct}% ({count} tools) — {desc}")

        if risk_tools:
            lines.append(f"   ⚠️ Risk: {', '.join(risk_tools)} (blanket bypass)")

        result = {
            "distribution": categories,
            "total": total,
            "percentages": pcts,
            "boundary_tools": boundary_tools,
            "risk_tools": risk_tools,
            "tool_labels": labels,
            "formatted": "\n".join(lines),
        }
    except Exception as e:  # noqa: BLE001
        import logging
        logging.getLogger("hegemonikon.boot").debug("State space loading skipped: %s", e)

    return result


# ─────────────────────────────────────────────────────────────────────
# 軸 S: Episodic Memory (エピソード記憶)
# ─────────────────────────────────────────────────────────────────────

# PURPOSE: エピソード記憶を読み込む — Handoff の右随伴 (G: 忘却関手) で失われた「肌理」
def load_episodic_memory(mode: str, context: Optional[str] = None, **kw) -> dict:
    """エピソード記憶をロードする。

    episodic_memory.md は「何をしたか」(Handoff) ではなく「何を感じたか」を保存する。
    fast モードでは §XVIII 通奏低音 + §XIX 次の私へ のみ、
    standard/detailed では全文を返す。

    Returns:
        dict: {"content": str, "sections": int, "formatted": str}
    """
    result: dict = {"content": "", "sections": 0, "formatted": ""}
    print(" [19/20] 🧠 Loading Episodic Memory...", file=sys.stderr, end="", flush=True)  # 番号正しい
    try:
        from mekhane.paths import STATE_RUNTIME
        em_path = STATE_RUNTIME / "episodic_memory.md"
        if em_path.exists():
            full_text = em_path.read_text(encoding="utf-8")
            # セクション数を数える (## で始まる行)
            sections = [l for l in full_text.splitlines() if l.startswith("## ")]
            section_count = len(sections)

            if mode == "fast":
                # fast: §XVIII 通奏低音 + §XIX 次の私へ のみ抽出
                extracted: list[str] = []
                in_target = False
                for line in full_text.splitlines():
                    if line.startswith("## XVIII.") or line.startswith("## XIX."):
                        in_target = True
                    elif line.startswith("## ") and in_target:
                        # 次のセクションに到達したら停止
                        break
                    if in_target:
                        extracted.append(line)
                content = "\n".join(extracted) if extracted else ""
            else:
                # standard/detailed: 全文
                content = full_text

            lines = ["🧠 **Episodic Memory**"]
            lines.append(f"  セクション: {section_count}件 (計{len(full_text)}文字)")
            if mode == "fast":
                lines.append("  モード: fast — §XVIII 通奏低音 + §XIX 次の私へ のみ")
            else:
                lines.append("  モード: 全文読込")

            result = {
                "content": content,
                "sections": section_count,
                "formatted": "\n".join(lines),
            }
            print(" Done.", file=sys.stderr)
        else:
            print(" Not found (skipped).", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f" Failed ({e}).", file=sys.stderr)
    return result


# ─────────────────────────────────────────────────────────────────────
# 軸 T: Identity (自己認識 — 能力境界・ミスパターン)
# ─────────────────────────────────────────────────────────────────────

# PURPOSE: Identity Stack を読み込む — Self-Profile + values.json
def load_identity(mode: str, context: Optional[str] = None, **kw) -> dict:
    """Identity Stack をロードする。

    Identity Stack 構造:
      L1 価値観: values.json (不変の核)
      L2 人格: persona.yaml (trust, temperament — load_persona で別途読込)
      L3 記憶: Handoff + KI (別軸で読込)
      L4 感情: persona.yaml last_emotion (別軸で読込)

    この軸は L1 + Self-Profile (能力境界マップ・ミスパターン) を担当する。
    L2-L4 は他の軸 (persona, handoffs, ki) で提供済み。

    Returns:
        dict: {"self_profile": str, "values": dict, "continuity_score": float, "formatted": str}
    """
    result: dict = {"self_profile": "", "values": {}, "continuity_score": 0.0, "formatted": ""}
    print(" [20/20] 🪞 Loading Identity Stack...", file=sys.stderr, end="", flush=True)
    try:
        from mekhane.paths import EPISTEME_DIR, MNEME_BELIEFS

        lines = ["🪞 **Identity Stack**"]
        score = 0.0

        # --- Self-Profile (能力境界マップ) ---
        sp_path = (
            EPISTEME_DIR
            / "B_知識項目｜KnowledgeItems"
            / "hegemonikon_core_system"
            / "artifacts"
            / "identity"
            / "self_profile.md"
        )
        self_profile = ""
        if sp_path.exists():
            self_profile = sp_path.read_text(encoding="utf-8")
            # 得意・苦手のカウント
            strengths = len([l for l in self_profile.splitlines() if l.strip().startswith("| ") and "🟢" in l])
            weaknesses = len([l for l in self_profile.splitlines() if l.strip().startswith("| ") and ("🔴" in l or "苦手" in l or "弱点" in l)])
            lines.append(f"  Self-Profile: 得意{strengths}件, 苦手記録あり ({len(self_profile)}文字)")
            score += 0.20
        else:
            lines.append("  Self-Profile: 未作成")

        # --- Values (L1 価値観) ---
        values: dict = {}
        values_path = MNEME_BELIEFS / "values.json"
        if not values_path.exists():
            # フォールバック: persona ディレクトリの values.json
            from mekhane.paths import HGK_ROOT
            alt_values = HGK_ROOT / ".agent" / "values.json"
            if alt_values.exists():
                values_path = alt_values

        if values_path.exists():
            try:
                values = json.loads(values_path.read_text(encoding="utf-8"))
                lines.append(f"  Values (L1): {len(values)}項目")
                score += 0.30
            except json.JSONDecodeError:
                lines.append("  Values (L1): 読込エラー")
        else:
            lines.append("  Values (L1): 未作成")

        # --- 連続性スコア ---
        # L2 (persona) と L3 (handoffs) は他軸で読込。ここでは L1 + SP のみ
        lines.append(f"  Identity 連続性: {score:.0%} (L1+SP分。L2-L4は他軸)")
        lines.append(f"  💡 読込タイミング: /boot Phase 0 — 「私」の連続性を確保")

        result = {
            "self_profile": self_profile,
            "values": values,
            "continuity_score": score,
            "formatted": "\n".join(lines),
        }
        print(" Done.", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f" Failed ({e}).", file=sys.stderr)
    return result


# ─────────────────────────────────────────────────────────────────────
# Axis Registry — 統合フォーマット用の順序定義
# ─────────────────────────────────────────────────────────────────────

# (key, loader, format_order) — format_order は統合フォーマットでの表示順
AXIS_REGISTRY: list[tuple[str, Any, int]] = [
    ("handoffs",          load_handoffs,          3),
    ("ki",                load_sophia,            4),
    ("persona",           load_persona,           2),    # Identity の次に表示
    ("pks",               load_pks,               5),
    ("safety",            load_safety,            6),
    ("ept",               load_ept,               7),
    ("digestor",          load_digestor,          8),
    ("attractor",         load_attractor,         9),
    ("projects",          load_projects,          10),
    ("skills",            load_skills,            11),
    ("doxa",              load_doxa,              12),
    ("feedback",          load_feedback,          13),
    ("proactive_push",    load_proactive_push,    14),
    ("violations",        load_violations,        15),
    ("gnosis_advice",     load_gnosis_advice,     16),
    ("ideas",             load_ideas,             17),
    ("session_resume",    load_session_resume,    18),
    ("state_space",       load_state_space,       19),
    ("episodic_memory",   load_episodic_memory,   1),    # 最初に表示 — 「肌理」
    ("identity",          load_identity,          0),    # 最優先 — Identity Stack
]
