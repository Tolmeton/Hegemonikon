"""SAM / OA-SAM オプティマイザ
PURPOSE: Foret et al. 2021 の SAM + 忘却場正則化
"""
import torch


class SAM(torch.optim.Optimizer):
    """Sharpness-Aware Minimization (Foret et al. 2021)

    用法:
        optimizer = SAM(model.parameters(), base_optimizer_cls=torch.optim.SGD,
                        rho=0.05, lr=0.1, momentum=0.9, weight_decay=5e-4)
        # ステップ 1: 摂動方向の計算
        loss = criterion(model(inputs), targets)
        loss.backward()
        optimizer.first_step(zero_grad=True)
        # ステップ 2: 摂動点での勾配で更新
        loss2 = criterion(model(inputs), targets)
        loss2.backward()
        optimizer.second_step(zero_grad=True)
    """

    def __init__(self, params, base_optimizer_cls, rho=0.05, **kwargs):
        defaults = dict(rho=rho)
        super().__init__(params, defaults)
        self.base_optimizer = base_optimizer_cls(self.param_groups, **kwargs)
        self.param_groups = self.base_optimizer.param_groups

    @torch.no_grad()
    def first_step(self, zero_grad=False):
        """ε = ρ · ∇L / ‖∇L‖ で摂動し、θ → θ + ε"""
        grad_norm = self._grad_norm()
        for group in self.param_groups:
            scale = group["rho"] / (grad_norm + 1e-12)
            for p in group["params"]:
                if p.grad is None:
                    continue
                e_w = p.grad * scale
                p.add_(e_w)  # θ + ε
                self.state[p]["e_w"] = e_w  # 復元用に保存
        if zero_grad:
            self.zero_grad()

    @torch.no_grad()
    def second_step(self, zero_grad=False):
        """θ + ε → θ に復元し、base optimizer で更新"""
        for group in self.param_groups:
            for p in group["params"]:
                if p.grad is None:
                    continue
                p.sub_(self.state[p]["e_w"])  # θ + ε → θ
        self.base_optimizer.step()
        if zero_grad:
            self.zero_grad()

    def _grad_norm(self):
        norms = []
        for group in self.param_groups:
            for p in group["params"]:
                if p.grad is not None:
                    norms.append(p.grad.norm(p=2))
        return torch.stack(norms).norm(p=2) if norms else torch.tensor(0.0)


def create_optimizer(model, cfg):
    """設定辞書から適切なオプティマイザを生成"""
    params = model.parameters()
    base_kw = dict(lr=cfg['lr'], momentum=cfg['momentum'],
                   weight_decay=cfg['weight_decay'])

    if cfg['use_sam']:
        return SAM(params, torch.optim.SGD, rho=cfg['rho'], **base_kw)
    else:
        return torch.optim.SGD(params, **base_kw)
