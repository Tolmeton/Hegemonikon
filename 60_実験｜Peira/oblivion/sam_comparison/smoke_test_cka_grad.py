#!/usr/bin/env python3
"""CKA 自動微分可能性スモークテスト (🔴#3 解消)

PURPOSE: CKA(h_l, h_0) の θ に関する勾配が PyTorch autograd で
安全に計算できることを検証する。OA-SAM 実装の前提条件。
"""

import torch
import torch.nn as nn


def linear_cka(X, Y, eps=1e-10):
    """線形 CKA (Kornblith et al. 2019) — autograd 対応"""
    X = X - X.mean(dim=0, keepdim=True)
    Y = Y - Y.mean(dim=0, keepdim=True)
    cross = Y.T @ X
    xx = X.T @ X
    yy = Y.T @ Y
    num = (cross ** 2).sum()
    denom = torch.sqrt((xx ** 2).sum() * (yy ** 2).sum()) + eps
    return num / denom


class MiniNet(nn.Module):
    """テスト用の小さな BatchNorm 付きネットワーク"""
    def __init__(self):
        super().__init__()
        self.block1 = nn.Sequential(nn.Linear(784, 256), nn.BatchNorm1d(256), nn.ReLU())
        self.block2 = nn.Sequential(nn.Linear(256, 128), nn.BatchNorm1d(128), nn.ReLU())
        self.head = nn.Linear(128, 10)

    def forward_with_intermediates(self, x):
        h0 = x
        h1 = self.block1(x)
        h2 = self.block2(h1)
        out = self.head(h2)
        return out, [h0, h1, h2]


def test_basic_differentiability():
    """テスト 1: CKA の基本的微分可能性"""
    print("=== テスト 1: CKA 基本微分 ===")
    X = torch.randn(32, 64, requires_grad=True)
    Y = torch.randn(32, 128, requires_grad=True)
    cka = linear_cka(X, Y)
    cka.backward()
    ok = (X.grad is not None and not torch.isnan(X.grad).any()
          and Y.grad is not None and not torch.isnan(Y.grad).any())
    print(f"  CKA={cka.item():.6f}  grad_ok={ok}")
    return ok


def test_network_gradient():
    """テスト 2: ネットワーク経由の ∂Φ/∂θ"""
    print("=== テスト 2: ネットワーク経由 ∂Φ/∂θ ===")
    model = MiniNet()
    model.train()
    x = torch.randn(32, 784)
    out, ints = model.forward_with_intermediates(x)

    # Φ(l) = 1 - CKA(h_l, h_0)
    h0 = ints[0]
    phis = [1.0 - linear_cka(ints[l], h0) for l in range(1, len(ints))]

    # 離散勾配: ∇_l Φ
    grad_phi = [phis[0]] + [phis[l] - phis[l - 1] for l in range(1, len(phis))]

    # 正則化項 R = Σ (∇_l Φ)²
    reg = sum(g ** 2 for g in grad_phi)

    # CE + λ·R (λ<0 → 引き算)
    criterion = nn.CrossEntropyLoss()
    loss = criterion(out, torch.randint(0, 10, (32,))) - 0.01 * reg
    loss.backward()

    has_grad = all(p.grad is not None for p in model.parameters())
    has_nan = any(torch.isnan(p.grad).any().item() for p in model.parameters() if p.grad is not None)
    max_grad = max(p.grad.abs().max().item() for p in model.parameters() if p.grad is not None)
    print(f"  Φ={[f'{v.item():.4f}' for v in phis]}")
    print(f"  ∇Φ={[f'{g.item():.4f}' for g in grad_phi]}")
    print(f"  has_grad={has_grad}  nan={has_nan}  max_grad={max_grad:.6f}")
    return has_grad and not has_nan


def test_numerical_stability(n_iter=200):
    """テスト 3: 数値安定性 (λ<0 で繰り返し更新)"""
    print(f"=== テスト 3: 数値安定性 ({n_iter} iter) ===")
    model = MiniNet()
    opt = torch.optim.SGD(model.parameters(), lr=0.01, weight_decay=5e-4)
    criterion = nn.CrossEntropyLoss()
    nan_count = 0

    for i in range(n_iter):
        opt.zero_grad()
        model.train()
        x = torch.randn(32, 784)
        out, ints = model.forward_with_intermediates(x)
        h0 = ints[0]
        phis = [1.0 - linear_cka(ints[l], h0) for l in range(1, len(ints))]
        grad_phi = [phis[0]] + [phis[l] - phis[l - 1] for l in range(1, len(phis))]
        reg = sum(g ** 2 for g in grad_phi)
        loss = criterion(out, torch.randint(0, 10, (32,))) - 0.01 * reg
        loss.backward()
        if any(torch.isnan(p.grad).any() for p in model.parameters() if p.grad is not None):
            nan_count += 1
        else:
            opt.step()

    print(f"  NaN 発生: {nan_count}/{n_iter}  最終loss={loss.item():.4f}")
    return nan_count == 0


if __name__ == "__main__":
    results = {
        "basic": test_basic_differentiability(),
        "network": test_network_gradient(),
        "stability": test_numerical_stability(),
    }
    print("\n" + "=" * 40)
    all_pass = all(results.values())
    for name, ok in results.items():
        print(f"  {name}: {'✅ PASS' if ok else '❌ FAIL'}")
    print(f"\n{'✅ CKA 自動微分: 安全に使用可能' if all_pass else '⚠️ 問題検出'}")
