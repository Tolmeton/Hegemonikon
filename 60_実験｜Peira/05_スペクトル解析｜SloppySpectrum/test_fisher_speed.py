import os
import sys
import time

# PYTHONPATH を設定するためのパス追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from mekhane.anamnesis.fisher_field import FisherField

def main():
    print("=== Direct Test ===")
    fisher = FisherField()
    
    # 1. get_all_embeddings の速度
    t0 = time.time()
    embeddings, metadata = fisher.get_all_embeddings()
    t1 = time.time()
    print(f"get_all_embeddings: {len(embeddings)} items in {t1 - t0:.2f}s")
    
    if len(embeddings) == 0:
        print("No embeddings found, exiting.")
        return

    # 2. compute_fisher_matrix の速度
    k = min(10, len(embeddings) - 1)
    if k >= 2:
        t0 = time.time()
        G = fisher.compute_fisher_matrix(embeddings, k=k)
        t1 = time.time()
        print(f"compute_fisher_matrix: G.shape={G.shape} in {t1 - t0:.2f}s")
        
        # 3. eigen_decompose の速度
        t0 = time.time()
        axes = fisher.eigen_decompose(G, k_max=10)
        t1 = time.time()
        print(f"eigen_decompose: axes.k={axes.k} in {t1 - t0:.2f}s")
    
if __name__ == "__main__":
    main()
