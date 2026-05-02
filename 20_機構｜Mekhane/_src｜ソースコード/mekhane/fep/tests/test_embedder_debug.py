# PROOF: mekhane/fep/tests/test_embedder_debug.py
# PURPOSE: fep モジュールの embedder_debug に対するテスト
import sys
import numpy as np
sys.path.insert(0, '.')
from mekhane.fep.tests.conftest import MockEmbedder
import mekhane.anamnesis.vertex_embedder
mekhane.anamnesis.vertex_embedder.VertexEmbedder = MockEmbedder
from mekhane.fep.attractor_dispatcher import AttractorDispatcher
try:
    import mekhane.fep.attractor_advisor
    mekhane.fep.attractor_advisor.AttractorAdvisor._retrieve_gnosis = lambda self, q, top_k=2: []
except: pass
from mekhane.fep.theorem_attractor import THEOREM_KEYS

if __name__ == "__main__":
    dispatcher = AttractorDispatcher()
    adv = dispatcher._advisor
    sa = adv._attractor

    vec = MockEmbedder().embed("How should we design the architecture and implementation plan?")
    vec = np.array(vec, dtype=np.float32)

    sa._ensure_initialized()
    print("\n--- DISTANCES ---")
    for i, key in enumerate(sa._proto_keys):
        # Depending on GPU/CPU mode, _proto_tensor might be a PyTorch tensor, need fallback
        tensor_val = sa._proto_tensor[i]
        if hasattr(tensor_val, "cpu"):
            tensor_val = tensor_val.cpu().numpy()

        dist = np.linalg.norm(vec - tensor_val)
        if dist < 1.0:
            print(f"Index {i:2d} ({key}): {dist:.4f}")

    plan = dispatcher.dispatch("How should we design the architecture and implementation plan?")
    print("\n--- RESULT ---")
    if plan and plan.primary:
        print("SERIES IS:", plan.primary.series)
        print("WORKFLOW IS:", plan.primary.workflow)
    else:
        print("No primary result returned")

