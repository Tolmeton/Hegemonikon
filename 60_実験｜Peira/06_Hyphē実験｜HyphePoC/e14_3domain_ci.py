#!/usr/bin/env python3
"""
E14: 3-Domain Coherence Invariance -結晶化モデルの普遍性検証

PURPOSE:
  linkage_crystallization.md: 結晶化は Linkage に限らない -3ドメイン共通。
  T-003: Cognition (WF depth) と Description (granularity) で CI が成立するか実験。

  本実験は同一 chunker (G∘F) インフラを3種の異なるコンテンツに適用し、
  Coherence Invariance (coherence τ-不変性) がコンテンツタイプに依存しない
  ことを示す。

DOMAINS:
  | Domain      | Data Source              | "Session" definition     |
  |-------------|--------------------------|--------------------------|
  | Linkage     | embedding_cache.pkl      | Session transcript (13)  |
  | Cognition   | Handoff files            | Handoff = 認知操作記録   |
  | Description | Paper drafts + spec docs | Structured document      |

HYPOTHESIS:
  C̄(Fix(G∘F; τ)) ≈ const ∀τ ∈ (τ_min, τ_max) for ALL 3 domains.
  If CI holds universally, it proves crystallization is a property of
  G∘F (the operator) rather than the content it operates on.

SOURCE: PINAKAS_TASK T-003, linkage_crystallization.md §3ドメイン共通モデル
"""

import io
import json
import os
import pickle
import re
import sys
from pathlib import Path

# Force UTF-8 stdout on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import numpy as np

HGK_ROOT = Path.home() / "Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
POC_DIR = HGK_ROOT / "60_実験｜Peira/06_Hyphē実験｜HyphePoC"
HANDOFF_DIR = HGK_ROOT / "30_記憶｜Mneme/01_記録｜Records/a_引継｜handoff"
DRAFTS_DIR = HGK_ROOT / "10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts"
KERNEL_DIR = HGK_ROOT / "00_核心｜Kernel/A_公理｜Axioms"

sys.path.insert(0, str(POC_DIR))
sys.path.insert(0, str(HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"))

from hyphe_chunker import chunk_session, Step


# ── Phase 0: Embedding ──────────────────────────────────────────────

_ST_MODEL = None


def get_st_model():
    """sentence-transformers モデルをシングルトンでロード。"""
    global _ST_MODEL
    if _ST_MODEL is None:
        from sentence_transformers import SentenceTransformer
        _ST_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        print(f"  Loaded model: all-MiniLM-L6-v2 (dim={_ST_MODEL.get_sentence_embedding_dimension()})")
    return _ST_MODEL


def get_embeddings(texts: list[str], batch_size: int = 128) -> np.ndarray:
    """ローカル sentence-transformers で embedding を取得。API キー不要。"""
    model = get_st_model()
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        if i == 0 or (i // batch_size) % 5 == 0:
            print(f"  Embedding batch {i // batch_size + 1}/"
                  f"{(len(texts) - 1) // batch_size + 1} ({len(batch)} texts)...")
        embs = model.encode(batch, show_progress_bar=False, normalize_embeddings=True)
        all_embeddings.append(embs)

    return np.vstack(all_embeddings)


# ── Phase 1: Data Collection ────────────────────────────────────────

def split_into_paragraphs(text: str, min_chars: int = 80) -> list[str]:
    """テキストを段落に分割。短すぎる段落は直前に結合。"""
    # Markdown headers, blank lines で分割
    raw_paras = re.split(r'\n\s*\n|\n(?=#{1,4}\s)', text)
    paras = []
    for p in raw_paras:
        p = p.strip()
        if not p:
            continue
        # 表のヘッダ行、区切り線、短いメタデータ行はスキップ
        if re.match(r'^[\-\|:=\s]+$', p):
            continue
        if re.match(r'^\*.*\*$', p) and len(p) < 60:
            continue
        if p.startswith('```'):
            continue
        if paras and len(paras[-1]) < min_chars:
            paras[-1] += "\n" + p
        else:
            paras.append(p)
    # 最後の段落が短い場合も結合
    if len(paras) > 1 and len(paras[-1]) < min_chars:
        paras[-2] += "\n" + paras[-1]
        paras.pop()
    return paras


def load_linkage_sessions():
    """既存 embedding_cache.pkl からステップテキストを読み込み、
    同一 embedding モデル (all-MiniLM-L6-v2) で再 embed する。
    公正比較のため全ドメインで同じモデルを使用。"""
    with open(POC_DIR / "embedding_cache.pkl", "rb") as f:
        cache = pickle.load(f)
    results = json.load(open(POC_DIR / "results.json", encoding="utf-8"))

    sessions = []
    for r in results:
        sid = r["session_id"]
        if sid not in cache:
            continue
        sess = cache[sid]
        steps_raw = sess.get("steps", [])
        steps = []
        texts = []
        for i, s in enumerate(steps_raw):
            if isinstance(s, Step):
                steps.append(s)
                texts.append(s.text)
            elif isinstance(s, str):
                steps.append(Step(index=i, text=s))
                texts.append(s)
            elif hasattr(s, "text"):
                steps.append(Step(index=i, text=s.text))
                texts.append(s.text)
            else:
                steps.append(Step(index=i, text=str(s)))
                texts.append(str(s))
        if len(steps) >= 5:
            sessions.append({
                "steps": steps, "texts": texts,
                "id": f"link_{sid}", "domain": "Linkage",
            })
    return sessions


def collect_cognition_data() -> list[dict]:
    """Handoff ファイルを認知操作のシーケンスとして収集。

    各 Handoff = 1 "session" = S/B/A/R 段落のシーケンス。
    認知操作 (判断, 評価, 計画) の記録なので Cognition ドメインに対応。
    """
    sessions = []
    handoff_files = sorted(HANDOFF_DIR.glob("handoff_*.md"))

    for hf in handoff_files:
        try:
            text = hf.read_text(encoding="utf-8")
        except Exception:
            continue

        paras = split_into_paragraphs(text)
        if len(paras) < 5:
            continue

        steps = [Step(index=i, text=p) for i, p in enumerate(paras)]
        sessions.append({
            "steps": steps,
            "texts": [p for p in paras],
            "id": f"cog_{hf.stem}",
            "domain": "Cognition",
        })

    return sessions


def collect_description_data() -> list[dict]:
    """構造化文書 (Paper drafts, specs) を Description ドメインとして収集。

    長い文書は複数の "session" に分割 (200段落ごと)。
    各段落 = 1 step。指示/記述の粒度がコントロールパラメータ。
    """
    sessions = []

    # Paper drafts
    doc_files = list(DRAFTS_DIR.glob("paper_*_draft.md"))
    doc_files += list(DRAFTS_DIR.glob("essay_*.md"))
    doc_files += list(DRAFTS_DIR.glob("*忘却*.md"))
    doc_files += list(DRAFTS_DIR.glob("*完全性*.md"))

    # Kernel spec docs
    for spec in KERNEL_DIR.glob("*.md"):
        if spec.stat().st_size > 5000:  # 大きい仕様書のみ
            doc_files.append(spec)

    # 企画系 linkage docs
    linkage_dir = HGK_ROOT / "10_知性｜Nous/04_企画｜Boulēsis/11_肌理｜Hyphē"
    for ld in linkage_dir.glob("*.md"):
        if ld.stat().st_size > 3000:
            doc_files.append(ld)

    for df in doc_files:
        try:
            text = df.read_text(encoding="utf-8")
        except Exception:
            continue

        paras = split_into_paragraphs(text)
        if len(paras) < 5:
            continue

        # 長い文書は分割 (max 100 paras per session)
        for chunk_start in range(0, len(paras), 100):
            chunk = paras[chunk_start:chunk_start + 100]
            if len(chunk) < 5:
                continue
            suffix = f"_p{chunk_start}" if chunk_start > 0 else ""
            steps = [Step(index=i, text=p) for i, p in enumerate(chunk)]
            sessions.append({
                "steps": steps,
                "texts": chunk,
                "id": f"desc_{df.stem}{suffix}",
                "domain": "Description",
            })

    return sessions


# ── Phase 2: Embedding & Caching ────────────────────────────────────

CACHE_PATH = POC_DIR / "e14_embedding_cache.pkl"


def embed_sessions(sessions: list[dict]) -> list[dict]:
    """未 embedding のセッションに embedding を付与する。キャッシュを使用。"""
    # Load existing cache
    cache = {}
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "rb") as f:
            cache = pickle.load(f)

    to_embed = []
    for s in sessions:
        if s["id"] in cache:
            s["embs"] = cache[s["id"]]
        elif "embs" not in s:
            to_embed.append(s)

    if to_embed:
        print(f"\n  Need to embed {len(to_embed)} sessions "
              f"({sum(len(s['texts']) for s in to_embed)} texts total)")

        # Batch all texts together for efficiency
        all_texts = []
        text_map = []  # (session_idx, step_idx)
        for si, s in enumerate(to_embed):
            for ti, t in enumerate(s["texts"]):
                all_texts.append(t)
                text_map.append((si, ti))

        all_embs = get_embeddings(all_texts)

        # Distribute back
        for si, s in enumerate(to_embed):
            n_steps = len(s["texts"])
            start = sum(len(to_embed[j]["texts"]) for j in range(si))
            s["embs"] = all_embs[start:start + n_steps]
            cache[s["id"]] = s["embs"]

        # Save cache
        with open(CACHE_PATH, "wb") as f:
            pickle.dump(cache, f)
        print(f"  Cache saved: {CACHE_PATH} ({len(cache)} sessions)")

    return sessions


# ── Phase 3: τ Sweep ────────────────────────────────────────────────

def run_tau_sweep_domain(sessions: list[dict], tau_values: list[float],
                          domain_name: str) -> dict:
    """1ドメインの全セッションに対して τ sweep を実行。"""
    results = {}

    for ti, tau in enumerate(tau_values):
        if ti % 10 == 0:
            print(f"    {domain_name} tau={tau:.2f} ({ti+1}/{len(tau_values)})", flush=True)
        tau_key = f"{tau:.3f}"
        session_metrics = []

        for s in sessions:
            steps = s["steps"]
            embs = s["embs"]

            if len(steps) < 3 or len(embs) < 3:
                continue

            try:
                result = chunk_session(
                    steps, embs, tau=tau, min_steps=2, max_iterations=10,
                    sim_mode="pairwise",
                )
                coherences = [c.coherence for c in result.chunks]

                session_metrics.append({
                    "sid": s["id"],
                    "num_chunks": len(result.chunks),
                    "mean_coherence": float(np.mean(coherences)) if coherences else 0.0,
                    "std_coherence": float(np.std(coherences)) if coherences else 0.0,
                    "converged": result.converged,
                    "iterations": result.iterations,
                })
            except Exception as e:
                continue

        if session_metrics:
            coherences_all = [m["mean_coherence"] for m in session_metrics]
            results[tau_key] = {
                "tau": tau,
                "domain": domain_name,
                "n_sessions": len(session_metrics),
                "mean_num_chunks": float(np.mean([m["num_chunks"] for m in session_metrics])),
                "std_num_chunks": float(np.std([m["num_chunks"] for m in session_metrics])),
                "mean_coherence": float(np.mean(coherences_all)),
                "std_coherence": float(np.std(coherences_all)),
                "ci_range": float(max(coherences_all) - min(coherences_all)),
                "convergence_rate": float(np.mean([m["converged"] for m in session_metrics])),
            }

    return results


# ── Phase 4: CI Analysis ────────────────────────────────────────────

def analyze_ci(domain_results: dict, domain_name: str) -> dict:
    """ドメインの CI 統計を計算。"""
    if not domain_results:
        return {"domain": domain_name, "ci_holds": False, "reason": "no data"}

    taus = sorted(domain_results.keys())
    coherences = [domain_results[t]["mean_coherence"] for t in taus]
    n_chunks_list = [domain_results[t]["mean_num_chunks"] for t in taus]

    # CI metric: coherence の変動係数 (CV)
    c_mean = np.mean(coherences)
    c_std = np.std(coherences)
    cv = c_std / c_mean if c_mean > 0 else float('inf')

    # τ > 0.60 の structured 領域のみで CI を測定 (undifferentiated 領域を除外)
    structured_taus = [t for t in taus if domain_results[t]["tau"] > 0.60]
    if structured_taus:
        struct_coherences = [domain_results[t]["mean_coherence"] for t in structured_taus]
        struct_cv = np.std(struct_coherences) / np.mean(struct_coherences)
        struct_range = max(struct_coherences) - min(struct_coherences)
    else:
        struct_cv = float('inf')
        struct_range = float('inf')

    # chunk 数の変動幅 (CI の前提: chunk 数は大きく変動するのに coherence は不変)
    chunk_ratio = max(n_chunks_list) / max(min(n_chunks_list), 0.1)

    # CI 判定: CV < 2% (Linkage での実績: ±0.7%)
    ci_holds = struct_cv < 0.02

    return {
        "domain": domain_name,
        "ci_holds": ci_holds,
        "coherence_mean": float(c_mean),
        "coherence_std": float(c_std),
        "cv_full": float(cv),
        "cv_structured": float(struct_cv),
        "coherence_range_structured": float(struct_range),
        "chunk_ratio": float(chunk_ratio),
        "n_tau_points": len(taus),
        "n_structured_points": len(structured_taus),
    }


# ── Phase 5: Main ───────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("E14: 3-Domain Coherence Invariance -結晶化モデルの普遍性検証")
    print("=" * 70)

    # ── Data Collection ──
    print("\n[Phase 1] Data Collection")

    # Domain 1: Linkage (existing)
    print("  Loading Linkage sessions (embedding_cache.pkl)...")
    linkage_sessions = load_linkage_sessions()
    print(f"  Linkage: {len(linkage_sessions)} sessions, "
          f"{sum(len(s['steps']) for s in linkage_sessions)} steps")

    # Domain 2: Cognition (Handoffs)
    print("  Collecting Cognition data (Handoffs)...")
    cognition_sessions = collect_cognition_data()
    # Sample for tractable computation (240 sessions x 46 tau = too slow)
    MAX_SESSIONS = 20
    if len(cognition_sessions) > MAX_SESSIONS:
        np.random.seed(42)
        # Prefer longer sessions (more steps = more meaningful chunks)
        cognition_sessions.sort(key=lambda s: len(s["steps"]), reverse=True)
        cognition_sessions = cognition_sessions[:MAX_SESSIONS]
    print(f"  Cognition: {len(cognition_sessions)} sessions, "
          f"{sum(len(s['steps']) for s in cognition_sessions)} steps")

    # Domain 3: Description (Papers + specs)
    print("  Collecting Description data (Papers + specs)...")
    description_sessions = collect_description_data()
    if len(description_sessions) > MAX_SESSIONS:
        description_sessions.sort(key=lambda s: len(s["steps"]), reverse=True)
        description_sessions = description_sessions[:MAX_SESSIONS]
    print(f"  Description: {len(description_sessions)} sessions, "
          f"{sum(len(s['steps']) for s in description_sessions)} steps")

    # ── Embedding ──
    print("\n[Phase 2] Embedding (all-MiniLM-L6-v2, local)")
    linkage_sessions = embed_sessions(linkage_sessions)
    cognition_sessions = embed_sessions(cognition_sessions)
    description_sessions = embed_sessions(description_sessions)

    # ── τ Sweep ──
    tau_values = [round(0.50 + i * 0.01, 3) for i in range(46)]
    print(f"\n[Phase 3] τ Sweep: {tau_values[0]}~{tau_values[-1]} ({len(tau_values)} points)")

    print(f"\n  --- Linkage ({len(linkage_sessions)} sessions) ---")
    linkage_results = run_tau_sweep_domain(linkage_sessions, tau_values, "Linkage")

    print(f"  --- Cognition ({len(cognition_sessions)} sessions) ---")
    cognition_results = run_tau_sweep_domain(cognition_sessions, tau_values, "Cognition")

    print(f"  --- Description ({len(description_sessions)} sessions) ---")
    description_results = run_tau_sweep_domain(description_sessions, tau_values, "Description")

    # ── Results ──
    print("\n[Phase 4] Coherence Invariance Analysis")
    print(f"\n{'Domain':>12} | {'τ':>6} | {'chunks':>7} | {'coherence':>10} | {'std':>8}")
    print("-" * 55)

    all_domain_results = {
        "Linkage": linkage_results,
        "Cognition": cognition_results,
        "Description": description_results,
    }

    for domain_name, dr in all_domain_results.items():
        for tau_key in sorted(dr.keys()):
            r = dr[tau_key]
            if r["tau"] in [0.50, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]:
                print(f"{domain_name:>12} | {r['tau']:6.3f} | {r['mean_num_chunks']:7.1f} | "
                      f"{r['mean_coherence']:10.4f} | {r['std_coherence']:8.4f}")
        print("-" * 55)

    # ── CI Comparison ──
    print("\n[Phase 5] Cross-Domain CI Comparison")
    print(f"\n{'Domain':>12} | {'CI?':>4} | {'C̄':>8} | {'CV(struct)':>10} | "
          f"{'range':>8} | {'chunk ratio':>11}")
    print("-" * 70)

    ci_results = {}
    for domain_name, dr in all_domain_results.items():
        ci = analyze_ci(dr, domain_name)
        ci_results[domain_name] = ci
        status = "✅" if ci["ci_holds"] else "❌"
        print(f"{domain_name:>12} | {status:>4} | {ci['coherence_mean']:8.4f} | "
              f"{ci['cv_structured']:10.4f} | {ci['coherence_range_structured']:8.4f} | "
              f"{ci['chunk_ratio']:11.1f}x")

    # ── Isomorphism test ──
    print("\n[Phase 6] 3-Domain Isomorphism Test")
    domains_with_ci = [d for d, ci in ci_results.items() if ci["ci_holds"]]
    if len(domains_with_ci) == 3:
        print("  ✅ CI holds in ALL 3 domains → 結晶化モデルの普遍性が確認された")
        print("  → Coherence Invariance は G∘F (演算子) の性質であり、")
        print("    コンテンツタイプに依存しない")
    elif len(domains_with_ci) >= 2:
        print(f"  🟡 CI holds in {len(domains_with_ci)}/3 domains: {domains_with_ci}")
        failed = [d for d in ci_results if d not in domains_with_ci]
        for d in failed:
            ci = ci_results[d]
            print(f"    ❌ {d}: CV={ci['cv_structured']:.4f}, range={ci['coherence_range_structured']:.4f}")
    else:
        print(f"  ❌ CI holds in only {len(domains_with_ci)}/3 domains")

    # ── Save ──
    output = {
        "experiment": "e14_3domain_ci",
        "hypothesis": "CI holds universally across 3 content domains",
        "domains": {
            "Linkage": {
                "n_sessions": len(linkage_sessions),
                "n_steps": sum(len(s["steps"]) for s in linkage_sessions),
                "tau_sweep": linkage_results,
                "ci_analysis": ci_results.get("Linkage"),
            },
            "Cognition": {
                "n_sessions": len(cognition_sessions),
                "n_steps": sum(len(s["steps"]) for s in cognition_sessions),
                "tau_sweep": cognition_results,
                "ci_analysis": ci_results.get("Cognition"),
            },
            "Description": {
                "n_sessions": len(description_sessions),
                "n_steps": sum(len(s["steps"]) for s in description_sessions),
                "tau_sweep": description_results,
                "ci_analysis": ci_results.get("Description"),
            },
        },
        "cross_domain": {
            "domains_with_ci": domains_with_ci,
            "isomorphism_confirmed": len(domains_with_ci) == 3,
        },
    }

    # Convert numpy/bool types for JSON serialization
    def json_safe(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    out_path = POC_DIR / "e14_3domain_ci_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=json_safe)
    print(f"\n  Results saved: {out_path}")


if __name__ == "__main__":
    main()
