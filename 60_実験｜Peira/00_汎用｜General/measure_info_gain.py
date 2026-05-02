import asyncio
import os
import sys

# Setup paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mekhane.anamnesis.vertex_embedder import VertexEmbedder

async def main():
    print("Initializing VertexEmbedder...")
    embedder = VertexEmbedder()
    
    # Representative synthesis texts (simulated)
    text_a = """
    The free energy principle (FEP) is a formal theory originating in neuroscience,
    suggesting that the brain minimizes surprise or uncertainty. It describes a system
    that resists a tendency to disorder by minimizing its variational free energy.
    Active inference is a corollary, where agents act to confirm their prior beliefs.
    """
    
    # Completely identical text
    text_same_a = text_a
    
    # Slight variation (reordered, synonymous)
    text_slight_mod = """
    Originating from neuroscience, the free energy principle (FEP) posits that brains
    work to minimize surprise and uncertainty. Essentially, it models systems that
    fight disorder through minimizing variational free energy. A closely related
    concept is active inference, wherein agents take actions to fulfill prior expectations.
    """
    
    # Moderate variation (adding new info)
    text_mod_gain = text_a + """
    Crucially, FEP uses Markov blankets to statistically separate internal states from
    external states. This boundary allows the internal states to model the external
    world probabilistically.
    """
    
    # Completely unrelated text
    text_unrelated = """
    Transformer models rely on self-attention mechanisms to process sequential data,
    allowing them to capture long-range dependencies effectively. They have become
    the standard architecture for large language models.
    """
    
    print("Measuring novelty (info_gain) = 1 - cosine_similarity...")
    
    try:
        n_same = embedder.novelty(text_a, text_same_a)
        print(f"Identical text (Expected 0.0): {n_same:.4f}")
        
        n_slight = embedder.novelty(text_a, text_slight_mod)
        print(f"Slight modification (Expected low): {n_slight:.4f}")
        
        n_mod = embedder.novelty(text_a, text_mod_gain)
        print(f"Moderate gain (Expected mid): {n_mod:.4f}")
        
        n_unrelated = embedder.novelty(text_a, text_unrelated)
        print(f"Unrelated text (Expected >0.5): {n_unrelated:.4f}")
        
    except Exception as e:
        print(f"Error during measurement: {e}")

if __name__ == "__main__":
    asyncio.run(main())
