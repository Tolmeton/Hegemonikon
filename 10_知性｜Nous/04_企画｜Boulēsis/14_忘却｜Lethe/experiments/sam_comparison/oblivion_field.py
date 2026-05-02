"""忘却場 Φ(l) の CKA ベース計算
PURPOSE: Paper I §6.8 の OA-SAM 正則化項を実装
"""
import torch
import torch.nn.functional as F


def linear_cka(X, Y, eps=1e-10):
    """線形 CKA (Kornblith et al. 2019) — autograd 対応"""
    X = X - X.mean(0, keepdim=True)
    Y = Y - Y.mean(0, keepdim=True)
    cross = Y.T @ X
    xx = X.T @ X
    yy = Y.T @ Y
    num = (cross ** 2).sum()
    denom = torch.sqrt((xx ** 2).sum() * (yy ** 2).sum()) + eps
    return num / denom


class OblivionField:
    """CKA ベースの忘却場 Φ(l) = 1 - CKA(h_l, h_0)"""

    def __init__(self, model, hook_names=None,
                 ema_beta=0.99, lam_base=0.01, lam_sign=-1):
        self.model = model
        self.ema_beta = ema_beta
        self.lam_base = lam_base
        self.lam_sign = lam_sign
        self.hook_names = hook_names or ['layer1', 'layer2', 'layer3', 'layer4']
        self.activations = {}
        self.hooks = []
        self.phi_ema = None
        self._register()

    def _register(self):
        named = dict(self.model.named_modules())
        for n in self.hook_names:
            h = named[n].register_forward_hook(self._hook(n))
            self.hooks.append(h)

    def _hook(self, name):
        def fn(mod, inp, out):
            if out.dim() == 4:
                self.activations[name] = F.adaptive_avg_pool2d(out, 1).flatten(1)
            else:
                self.activations[name] = out
        return fn

    def compute_reg(self, inputs):
        """R = lam_sign * lam_base * Σ(∇_l Φ)². model(inputs) 呼出後に使う。"""
        h0 = inputs.flatten(1)
        phis = []
        for n in self.hook_names:
            if n in self.activations:
                phis.append(1.0 - linear_cka(self.activations[n], h0))
        if len(phis) < 2:
            return torch.tensor(0.0, device=inputs.device, requires_grad=True)
        gp = [phis[0]] + [phis[i] - phis[i-1] for i in range(1, len(phis))]
        reg = sum(g ** 2 for g in gp)
        with torch.no_grad():
            cur = [p.item() for p in phis]
            if self.phi_ema is None:
                self.phi_ema = cur
            else:
                self.phi_ema = [self.ema_beta*e + (1-self.ema_beta)*c
                                for e, c in zip(self.phi_ema, cur)]
        return self.lam_sign * self.lam_base * reg

    @torch.no_grad()
    def get_profiles(self, inputs):
        """分析用: CKA, ∇Φ, Φ プロファイル"""
        self.model.eval()
        self.model(inputs)
        h0 = inputs.flatten(1)
        phi = []
        for n in self.hook_names:
            if n in self.activations:
                phi.append(1.0 - linear_cka(self.activations[n], h0).item())
        cka = [1.0 - p for p in phi]
        gp = [phi[0]] + [phi[i]-phi[i-1] for i in range(1, len(phi))]
        return cka, gp, phi

    def remove(self):
        for h in self.hooks:
            h.remove()
