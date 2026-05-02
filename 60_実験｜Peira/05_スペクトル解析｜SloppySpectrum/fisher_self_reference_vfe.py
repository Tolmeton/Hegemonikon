#!/usr/bin/env python3
import numpy as np
from scipy.optimize import minimize_scalar

def entropy_nats(n, alpha):
    if alpha < 1e-6:
        return np.log(n)
    langevin = 1.0 / np.tanh(alpha) - 1.0 / alpha
    h_cont = np.log(2.0 * np.sinh(alpha) / alpha) - alpha * langevin
    return h_cont + np.log(n)

def pr_continuous(n, alpha):
    if alpha < 1e-6:
        return n
    return n * (np.tanh(alpha) / alpha)

def optimize_n(gamma, model_type, max_n=100, kappa=0.01):
    best_n = None
    best_a = None
    min_vfe = float('inf')
    
    for n in range(2, max_n + 1):
        def obj(a):
            comp = np.log(n) - entropy_nats(n, a)
            if model_type == 'PR':
                acc = gamma * pr_continuous(n, a)
            else:
                acc = gamma * a
            return comp - acc + kappa * n

        res = minimize_scalar(obj, bounds=(0.01, 30.0), method='bounded')
        if res.success and res.fun < min_vfe:
            min_vfe = res.fun
            best_n = n
            best_a = res.x
            
    return best_n, best_a, min_vfe

print("=" * 60)
print("自己参照的 VFE の不動点探索 (scipy.optimize 版)")
print("=" * 60)

print("\n[Model B] Accuracy = γ * PR (有効次元の確保がゲイン)")
print("κ = 0.01 (リソース維持コスト)")
print(f"{'γ':>6} | {'n*':>5} | {'α*':>7} | {'PR*':>7} | {'H*(bits)':>9} | {'VFE':>8}")
print("-" * 55)

for gamma in [0.01, 0.05, 0.1, 0.15, 0.2, 0.3]:
    n, a, vfe = optimize_n(gamma, 'PR', kappa=0.01)
    if n:
        pr = pr_continuous(n, a)
        h = entropy_nats(n, a) / np.log(2)
        print(f"{gamma:>6.2f} | {n:>5} | {a:>7.2f} | {pr:>7.2f} | {h:>9.2f} | {vfe:>8.2f}")

print("\n[Model A] Accuracy = γ * α (確信度自体がゲイン)")
print("κ = 0.01 (リソース維持コスト)")
print(f"{'γ':>6} | {'n*':>5} | {'α*':>7} | {'PR*':>7} | {'H*(bits)':>9} | {'VFE':>8}")
print("-" * 55)

for gamma in [0.1, 0.5, 1.0, 1.5, 2.0]:
    n, a, vfe = optimize_n(gamma, 'ALPHA', kappa=0.01)
    if n:
        pr = pr_continuous(n, a)
        h = entropy_nats(n, a) / np.log(2)
        print(f"{gamma:>6.2f} | {n:>5} | {a:>7.2f} | {pr:>7.2f} | {h:>9.2f} | {vfe:>8.2f}")
