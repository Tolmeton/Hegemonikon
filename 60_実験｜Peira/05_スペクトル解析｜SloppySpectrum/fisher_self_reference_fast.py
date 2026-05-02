import numpy as np
import time

def softmax_probs(n, alpha):
    logits = np.linspace(3.0, -3.0, n)
    beta = alpha / 3.0
    raw = np.exp(beta * logits)
    return raw / raw.sum()

def entropy_nats(p):
    return -np.sum(p * np.log(p + 1e-30))

def calc_pr(p):
    return (1.0/p).sum()**2 / np.sum((1.0/p)**2)

print("Starting Fast Grid Search...")
start_time = time.time()

kappa = 0.05
ns = list(range(2, 65))
alphas = np.linspace(0.1, 15.0, 150)

print("\nModel B: Accuracy = gamma * PR")
print(f"{'gamma':>6} {'n*':>5} {'a*':>6} {'PR*':>6} {'minVFE':>8}")
print('-' * 40)

for gamma in [0.01, 0.05, 0.1, 0.2, 0.5]:
    min_vfe = float('inf')
    best_n, best_a, best_pr = 0, 0, 0
    for n in ns:
        for a in alphas:
            p = softmax_probs(n, a)
            pr = calc_pr(p)
            vfe = np.log(n) - entropy_nats(p) - gamma * pr + kappa * n
            if vfe < min_vfe:
                min_vfe = vfe
                best_n, best_a, best_pr = n, a, pr
    print(f"{gamma:>6.2f} {best_n:>5} {best_a:>6.1f} {best_pr:>6.1f} {min_vfe:>8.2f}")

print("\nModel A: Accuracy = gamma * alpha")
print(f"{'gamma':>6} {'n*':>5} {'a*':>6} {"PR":>6} {'minVFE':>8}")
print('-' * 40)

for gamma in [0.1, 0.5, 1.0, 1.5, 2.0]:
    min_vfe = float('inf')
    best_n, best_a, best_pr = 0, 0, 0
    for n in ns:
        for a in alphas:
            p = softmax_probs(n, a)
            vfe = np.log(n) - entropy_nats(p) - gamma * a + kappa * n
            if vfe < min_vfe:
                min_vfe = vfe
                best_n, best_a = n, a
                best_pr = calc_pr(p)
    print(f"{gamma:>6.2f} {best_n:>5} {best_a:>6.1f} {best_pr:>6.1f} {min_vfe:>8.2f}")

print(f"\nDone in {time.time()-start_time:.2f}s")
