#!/usr/bin/env python3
"""Phase 1 統一訓練スクリプト
SGD / SAM / OA-SAM (λ<0) / 反転制御 (λ>0) の4条件
ResNet-18 × CIFAR-10 × 200 epochs × 5 seeds
"""
import argparse, json, os, time
import torch, torch.nn as nn
import torchvision, torchvision.transforms as T
from torch.utils.data import DataLoader
from configs import PHASE1
from optimizers import create_optimizer
from oblivion_field import OblivionField


def cifar10_resnet18():
    """CIFAR-10 用 ResNet-18 (conv1 修正, maxpool 削除)"""
    m = torchvision.models.resnet18(num_classes=10)
    m.conv1 = nn.Conv2d(3, 64, 3, 1, 1, bias=False)
    m.maxpool = nn.Identity()
    return m


def get_loaders(bs=128):
    """CIFAR-10 DataLoader (train + test)"""
    tr = T.Compose([T.RandomCrop(32, 4), T.RandomHorizontalFlip(), T.ToTensor(),
                     T.Normalize((0.4914,0.4822,0.4465),(0.2023,0.1994,0.2010))])
    te = T.Compose([T.ToTensor(),
                     T.Normalize((0.4914,0.4822,0.4465),(0.2023,0.1994,0.2010))])
    train_ds = torchvision.datasets.CIFAR10('./data', True, tr, download=True)
    test_ds = torchvision.datasets.CIFAR10('./data', False, te, download=True)
    return (DataLoader(train_ds, bs, shuffle=True, num_workers=2, pin_memory=True),
            DataLoader(test_ds, bs, shuffle=False, num_workers=2, pin_memory=True))


def train_one(method, cfg, seed, device, out_dir):
    """1条件 × 1seed を訓練"""
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    epochs = cfg['epochs']

    model = cifar10_resnet18().to(device)
    optimizer = create_optimizer(model, cfg)
    base_opt = optimizer.base_optimizer if hasattr(optimizer, 'base_optimizer') else optimizer
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(base_opt, T_max=epochs)
    criterion = nn.CrossEntropyLoss()
    train_ld, test_ld = get_loaders(cfg['batch_size'])

    # 忘却場: 常に生成 (CKA profiling 用)。正則化項は lam_base > 0 のときだけ loss に加算
    field = OblivionField(model, lam_base=cfg.get('lam_base', 0), lam_sign=cfg.get('lam_sign', 0))
    use_reg = cfg.get('lam_base', 0) > 0  # 正則化を loss に加算するか

    metrics = {'method': method, 'seed': seed, 'cfg': {k: v for k, v in cfg.items() if k != 'label'},
               'train_loss': [], 'test_acc': [], 'profiles': []}
    t0 = time.time()

    for ep in range(epochs):
        # --- Train ---
        model.train()
        ep_loss = 0.0
        for x, y in train_ld:
            x, y = x.to(device), y.to(device)
            if hasattr(optimizer, 'first_step'):
                # SAM 2段階
                out = model(x)
                loss = criterion(out, y)
                if use_reg:
                    loss = loss + field.compute_reg(x)
                loss.backward()
                optimizer.first_step(zero_grad=True)
                out2 = model(x)
                loss2 = criterion(out2, y)
                if use_reg:
                    loss2 = loss2 + field.compute_reg(x)
                loss2.backward()
                optimizer.second_step(zero_grad=True)
                ep_loss += loss.item()
            else:
                optimizer.zero_grad()
                out = model(x)
                loss = criterion(out, y)
                if use_reg:
                    loss = loss + field.compute_reg(x)
                loss.backward()
                optimizer.step()
                ep_loss += loss.item()
        scheduler.step()

        # --- Test ---
        model.eval()
        correct = total = 0
        with torch.no_grad():
            for x, y in test_ld:
                x, y = x.to(device), y.to(device)
                pred = model(x).argmax(1)
                correct += (pred == y).sum().item()
                total += y.size(0)
        acc = 100.0 * correct / total
        avg_loss = ep_loss / len(train_ld)
        metrics['train_loss'].append(round(avg_loss, 5))
        metrics['test_acc'].append(round(acc, 2))

        # CKA プロファイル (20 epoch ごと) — 全条件で記録
        if (ep + 1) % 20 == 0 or ep == 0:
            batch_x = next(iter(test_ld))[0].to(device)
            cka_p, gp, phi_p = field.get_profiles(batch_x)
            metrics['profiles'].append({
                'epoch': ep + 1,
                'cka': [round(v, 4) for v in cka_p],
                'grad_phi': [round(v, 4) for v in gp],
                'phi': [round(v, 4) for v in phi_p],
            })

        if (ep + 1) % 10 == 0:
            elapsed = time.time() - t0
            print(f"  [{method}] ep={ep+1:3d}/{epochs} loss={avg_loss:.4f} "
                  f"acc={acc:.2f}% ({elapsed:.0f}s)")

    if field:
        field.remove()

    # 保存
    path = os.path.join(out_dir, f'{method}_seed{seed}.json')
    with open(path, 'w') as f:
        json.dump(metrics, f)
    print(f"  → {path} ({time.time()-t0:.0f}s)")
    return metrics


def main():
    ap = argparse.ArgumentParser(description='Phase 1: SAM comparison')
    ap.add_argument('--methods', nargs='+', default=list(PHASE1.keys()),
                    choices=list(PHASE1.keys()), help='実行する手法')
    ap.add_argument('--seeds', type=int, nargs='+', default=[42])
    ap.add_argument('--epochs', type=int, default=None, help='上書き epoch 数')
    ap.add_argument('--out', default='results', help='出力ディレクトリ')
    ap.add_argument('--smoke', action='store_true', help='1 epoch スモークテスト')
    args = ap.parse_args()

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Device: {device}")
    os.makedirs(args.out, exist_ok=True)

    for method in args.methods:
        cfg = PHASE1[method].copy()
        if args.epochs is not None:
            cfg['epochs'] = args.epochs
        if args.smoke:
            cfg['epochs'] = 1
        for seed in args.seeds:
            print(f"\n{'='*50}")
            print(f"Method: {cfg['label']}  seed={seed}  epochs={cfg['epochs']}")
            print('='*50)
            train_one(method, cfg, seed, device, args.out)


if __name__ == '__main__':
    main()
