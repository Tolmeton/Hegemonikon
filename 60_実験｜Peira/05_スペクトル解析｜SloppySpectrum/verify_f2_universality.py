#!/usr/bin/env python3
import sys
import numpy as np

# ROOT パスを通して mekhane モジュールを読めるようにする
import os
import sys
sys.path.insert(0, os.path.expanduser("~/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード"))

from mekhane.symploke.motherbrain_store import MotherbrainStore
from mekhane.symploke.embedder_factory import get_embed_fn

def main():
    print("=== E1: FEP Universality Test ===")
    store = MotherbrainStore()
    axes = store.load_field_axes()
    if not axes:
        print("No field axes found in DB. Running classification to generate them...")
        from mekhane.anamnesis.fisher_field import FisherField
        from mekhane.symploke.field_classifier import FieldClassifier
        import logging
        logging.basicConfig(level=logging.INFO)
        
        fisher = FisherField()
        axes = fisher.compute_axes(k_neighbors=10)
        classifier = FieldClassifier(fisher)
        results = classifier.classify_all(axes)
        axes_id = store.save_field_axes(axes)
        store.save_classifications_batch(results, axes_id)
        axes = store.load_field_axes()
        if not axes:
            print("Error: Still no field axes after running classification.")
            sys.exit(1)
            
    # axes_dict returns a dict, but we need the FieldAxes object or just its arrays
    # Ah, wait, store.get_latest_field_axes() returns a dict, not the FieldAxes object directly.
    # We should reconstruct or use the dict. Actually, `eigenvectors` is stored as bytes or list?
    # Let me check how get_latest_field_axes returns it.

    eigenvectors = axes.eigenvectors # shape (k, 3072)
    eigenvalues = axes.eigenvalues
    k = axes.k

    print(f"Loaded {k} eigenvectors.")
    print("\n[1] Sloppy Spectrum (log10 of eigenvalues):")
    log_vals = np.log10(np.maximum(eigenvalues, 1e-10))
    for i, v in enumerate(log_vals):
        print(f"  Axis {i}: {v:.3f}")

    # Words to test (7 HGK coordinates + opposites)
    pairs = {
        "Value (Internal ↔ Ambient)": ("Internal, subjective, inner thought, model", "Ambient, objective, external environment, perception"),
        "Function (Explore ↔ Exploit)": ("Explore, discovery, seeking new information, epistemic", "Exploit, use known information, pragmatic, execution"),
        "Precision (Certain ↔ Uncertain)": ("Certain, precise, formal, rigid, reliable", "Uncertain, vague, ambiguous, heuristic, sloppy"),
        "Scale (Micro ↔ Macro)": ("Micro, detail, local, specific, granular", "Macro, global, overview, holistic, general"),
        "Valence (Positive ↔ Negative)": ("Positive, success, match, alignment, good", "Negative, failure, mismatch, error, bad"),
        "Temporality (Past ↔ Future)": ("Past, memory, history, retroactive", "Future, prediction, planning, anticipation"),
        "Flow (Passive ↔ Active)": ("Passive, observation, receiving, stagnant", "Active, action, generation, dynamic")
    }

    print("\n[2] Embedding Coordinate Keywords...")
    embed_fn = get_embed_fn()
    
    results = {}
    for coord_name, (p1, p2) in pairs.items():
        # Get embeddings
        emb1 = embed_fn(p1)
        emb2 = embed_fn(p2)
        
        # Calculate semantic direction vector
        dir_vec = emb2 - emb1
        norm = np.linalg.norm(dir_vec)
        if norm > 1e-10:
            dir_vec = dir_vec / norm
        
        # Project onto eigenvectors
        # eigenvectors shape is (k, 3072), dir_vec is (3072,)
        # result is (k,)
        sims = eigenvectors.T @ dir_vec
        
        # Find best aligning axis
        best_k = np.argmax(np.abs(sims))
        max_sim = sims[best_k]
        
        # Second best for context
        sorted_indices = np.argsort(np.abs(sims))[::-1]
        second_k = sorted_indices[1]
        second_sim = sims[second_k]
        
        results[coord_name] = {
            "best": (best_k, max_sim),
            "second": (second_k, second_sim),
            "all_sims": sims
        }

    print("\n[3] Coordinate Alignment Results:")
    for coord_name, data in results.items():
        best_k, max_sim = data["best"]
        second_k, second_sim = data["second"]
        print(f"{coord_name}:")
        print(f"  -> Best Alignment: Axis {best_k} (sim: {max_sim:.3f})")
        print(f"  -> Next Alignment: Axis {second_k} (sim: {second_sim:.3f})")

    # Overall analysis
    print("\n[4] Axis Coverage:")
    axis_hits = {i: 0 for i in range(k)}
    for data in results.values():
        axis_hits[data["best"][0]] += 1
    
    for i in range(k):
        print(f"  Axis {i}: {axis_hits[i]} top coordinate hits")

if __name__ == "__main__":
    main()
