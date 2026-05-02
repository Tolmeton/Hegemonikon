"""Optional activation snapshot helpers for Lethe SAM comparison."""
import os

import torch


PROFILE_INTERVAL = 20
REPRESENTATION_KIND = 'adaptive_avg_pool2d_flatten'


def should_record_profile(epoch, interval=PROFILE_INTERVAL):
    return epoch == 1 or epoch % interval == 0


def expected_profile_epochs(total_epochs, interval=PROFILE_INTERVAL):
    return [
        epoch
        for epoch in range(1, total_epochs + 1)
        if should_record_profile(epoch, interval=interval)
    ]


def resolve_snapshot_dir(out_dir, snapshot_dir=None):
    path = snapshot_dir or os.path.join(out_dir, 'activation_snapshots')
    return os.path.abspath(path)


def save_activation_snapshot(snapshot, labels, method, seed, epoch, snapshot_dir, max_samples=None):
    os.makedirs(snapshot_dir, exist_ok=True)

    inputs = snapshot['inputs']
    representations = snapshot['representations']
    labels = labels.detach().cpu()

    if max_samples is not None:
        inputs = inputs[:max_samples]
        labels = labels[:max_samples]
        representations = {
            name: tensor[:max_samples]
            for name, tensor in representations.items()
        }

    inputs = inputs.contiguous()
    labels = labels.contiguous()
    representations = {
        name: tensor.contiguous()
        for name, tensor in representations.items()
    }

    path = os.path.join(snapshot_dir, f'{method}_seed{seed}_ep{epoch:03d}.pt')
    payload = {
        'method': method,
        'seed': seed,
        'epoch': epoch,
        'representation_kind': REPRESENTATION_KIND,
        'inputs': inputs,
        'labels': labels,
        'representations': representations,
    }
    torch.save(payload, path)

    return {
        'epoch': epoch,
        'path': os.path.abspath(path),
        'sample_count': int(inputs.shape[0]),
        'input_shape': list(inputs.shape),
        'representation_kind': REPRESENTATION_KIND,
        'layers': {
            name: list(tensor.shape)
            for name, tensor in representations.items()
        },
    }


def has_required_snapshots(data, expected_epochs):
    entries = data.get('activation_snapshots') or []
    by_epoch = {
        entry.get('epoch'): entry
        for entry in entries
        if isinstance(entry, dict)
    }
    for epoch in expected_profile_epochs(expected_epochs):
        entry = by_epoch.get(epoch)
        if not entry:
            return False
        path = entry.get('path')
        if not path or not os.path.exists(path):
            return False
    return True
