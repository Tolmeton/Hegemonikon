#!/usr/bin/env python3
"""E2 圧縮実験 — 13B TPU SPMD 最適化版 (バッチ処理 + 固定長パディング)
CodeLlama-13B を bfloat16 で 4 TPU チップに SPMD シャーディングして推論。
速度問題 (mark_step() の過剰呼び出しによる XLA 同期) をバッチ処理で解決。
"""
import json, os, sys, time, random
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional

# === SPMD 初期化 (最初に呼ぶ必要がある) ===
import torch_xla.runtime as xr
xr.use_spmd()

import torch
import torch_xla.core.xla_model as xm
import torch_xla.distributed.spmd as xs
from torch_xla.distributed.spmd import Mesh

# === データクラス ===
@dataclass
class ProbeDataPoint:
    code_a: str
    code_b: str
    pattern: str = ""
    is_positive: bool = True
    ccl_a: str = ""
    ccl_b: str = ""
    ccl_similarity: float = 0.0
    ast_distance: float = 0.0
    hidden_sim: float = 0.0
    layer_sims: list = field(default_factory=list)

# === 5条件のプロンプト生成 ===
def make_bare_prompt(code: str) -> str:
    """C0: コードのみ"""
    return code

def make_verbal_cot_prompt(code: str) -> str:
    """C1: 自然言語 CoT"""
    return f"""以下のPythonコードの構造を分析してください。
まず、関数名と引数を特定し、制御フローを追跡し、
データの変換パターンを理解してください。

```python
{code}
```

上記のコードの構造的な特徴を説明してください。"""

def make_bullet_prompt(code: str) -> str:
    """C2: 箇条書き構造"""
    return f"""コード構造の要約:
- 関数定義とパラメータ
- 制御フロー (条件分岐、ループ)
- データ変換パターン
- 戻り値の型と構造

```python
{code}
```"""

def make_structured_prompt(code: str) -> str:
    """C3: タグ付き構造"""
    return f"""[FUNC] 関数分析
[PARAMS] パラメータ一覧
[FLOW] 制御フロー
[TRANSFORM] データ変換
[RETURN] 戻り値

```python
{code}
```"""

def code_to_ccl(code: str) -> str:
    """C4: 簡易 CCL 変換"""
    import ast as ast_mod
    try:
        tree = ast_mod.parse(code)
    except:
        return f"/ene[code]"
    
    parts = []
    for node in ast_mod.walk(tree):
        if isinstance(node, ast_mod.FunctionDef):
            params = [a.arg for a in node.args.args]
            parts.append(f"/ene[fn:{node.name}({','.join(params)})]")
        elif isinstance(node, ast_mod.If):
            parts.append("/dok[if]")
        elif isinstance(node, ast_mod.For):
            parts.append("/pei[for]")
        elif isinstance(node, ast_mod.While):
            parts.append("/pei[while]")
        elif isinstance(node, ast_mod.Return):
            parts.append("/kat[return]")
        elif isinstance(node, ast_mod.Assign):
            parts.append("/tek[assign]")
        elif isinstance(node, ast_mod.ListComp):
            parts.append("/sag[listcomp]")
        elif isinstance(node, ast_mod.DictComp):
            parts.append("/sag[dictcomp]")
        elif isinstance(node, ast_mod.Try):
            parts.append("/dok[try]")
        elif isinstance(node, ast_mod.Raise):
            parts.append("/dio[raise]")
        elif isinstance(node, ast_mod.Assert):
            parts.append("/ele[assert]")
    
    return "_".join(parts) if parts else "/ene[code]"

def make_ccl_prompt(code: str) -> str:
    """C4: CCL 変換"""
    ccl = code_to_ccl(code)
    return f"{ccl}\n\n```python\n{code}\n```"

CONDITION_MAP = {
    "C0": ("bare", make_bare_prompt),
    "C1": ("verbal_cot", make_verbal_cot_prompt),
    "C2": ("bullet", make_bullet_prompt),
    "C3": ("structured", make_structured_prompt),
    "C4": ("ccl", make_ccl_prompt),
}

# === SPMD シャーディング ===
def create_mesh():
    """4 TPU チップの 1D メッシュを作成"""
    num_devices = xr.global_runtime_device_count()
    print(f"  TPU デバイス数: {num_devices}")
    device_ids = list(range(num_devices))
    mesh = Mesh(device_ids, (num_devices,), ('mp',))
    return mesh

def apply_llama_sharding(model, mesh):
    """Llama モデルのパラメータに SPMD シャーディングを適用"""
    sharded_count = 0
    replicated_count = 0
    
    for name, param in model.named_parameters():
        if param.dim() < 2:
            replicated_count += 1
            continue
        
        if any(k in name for k in ['q_proj', 'k_proj', 'v_proj', 'gate_proj', 'up_proj']):
            xs.mark_sharding(param, mesh, ('mp', None))
            sharded_count += 1
        elif any(k in name for k in ['o_proj', 'down_proj']):
            xs.mark_sharding(param, mesh, (None, 'mp'))
            sharded_count += 1
        elif 'embed_tokens' in name or 'lm_head' in name:
            xs.mark_sharding(param, mesh, (None, 'mp'))
            sharded_count += 1
        else:
            replicated_count += 1
    
    print(f"  シャーディング: {sharded_count} パラメータ分散, {replicated_count} レプリケート")

# === モデルロード (TPU SPMD) ===
def load_model_spmd(model_name: str, mesh):
    """モデルを bfloat16 で TPU に SPMD ロード"""
    from transformers import AutoTokenizer, AutoModelForCausalLM
    
    print(f"  モデルロード: {model_name} (bfloat16, SPMD)")
    t0 = time.time()
    
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    # Set padding side to left or right? Defaults to right. Right is fine for sequence representations using attention mask mean.
    
    device = xm.xla_device()
    print(f"  XLA デバイス: {device}")
    
    print(f"  CPU にモデルをロード中...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map=None,
        trust_remote_code=True,
        output_hidden_states=True,
    )
    
    print(f"  XLA Virtual Device に移動中...")
    model = model.to(device)
    
    print(f"  Megatron-style シャーディングを適用中...")
    apply_llama_sharding(model, mesh)
    
    model.eval()
    dt = time.time() - t0
    print(f"  ロード完了 ({dt:.0f}秒)")
    
    return model, tokenizer, device

# === Hidden State バッチ抽出 ===
def extract_hidden_states_batched(model, tokenizer, texts: List[str], device, max_length: int = 512):
    """テキストのリストから全層の hidden state をバッチ抽出 (固定長パディング)"""
    inputs = tokenizer(
        texts,
        return_tensors="pt",
        truncation=True,
        max_length=max_length,
        padding="max_length"
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True)
    
    hidden_states = outputs.hidden_states
    mask = inputs["attention_mask"].unsqueeze(-1).float()  # (batch, seq, 1)
    
    layer_means = []
    for hs in hidden_states:
        # パディング部分を無視して平均プーリング
        masked = hs * mask
        mean_hs = masked.sum(dim=1) / (mask.sum(dim=1) + 1e-9) # (batch, hidden_dim)
        
        # .cpu().numpy() でグラフ実行のトリガーになるが、これはまとめているため1バッチにつき1回だけ発生
        layer_means.append(mean_hs.float().cpu().numpy())
    
    return layer_means

# === 相関計算 (バッチ処理) ===
def compute_rho_batched(pairs: List[ProbeDataPoint], model, tokenizer, device, 
                condition_code: str, condition_name: str, prompt_fn, n_layers: int,
                batch_size: int = 16):
    """1条件の全層 ρ をバッチ処理で計算"""
    from scipy.stats import spearmanr
    
    n = len(pairs)
    ccl_sims = np.array([p.ccl_similarity for p in pairs])
    
    # 全件のプロンプトを事前生成
    prompts_a = [prompt_fn(p.code_a) for p in pairs]
    prompts_b = [prompt_fn(p.code_b) for p in pairs]
    
    layer_cosines = [[] for _ in range(n_layers)]
    
    t0 = time.time()
    for i in range(0, n, batch_size):
        batch_a = prompts_a[i:i+batch_size]
        batch_b = prompts_b[i:i+batch_size]
        
        hs_a = extract_hidden_states_batched(model, tokenizer, batch_a, device)
        hs_b = extract_hidden_states_batched(model, tokenizer, batch_b, device)
        
        actual_layers = min(len(hs_a), len(hs_b), n_layers)
        
        for layer_idx in range(actual_layers):
            for b in range(len(batch_a)):
                vec_a = hs_a[layer_idx][b]
                vec_b = hs_b[layer_idx][b]
                cos = float(np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b) + 1e-10))
                layer_cosines[layer_idx].append(cos)
        
        # 不要なグラフをクリア (batch抽出内で同期的 .cpu().numpy() により暗黙的にmark_stepされるが明示が安全)
        xm.mark_step()
        
        dt = time.time() - t0
        processed = min(i + batch_size, n)
        speed = (dt / processed) if processed > 0 else 0
        print(f"  Processed {processed:>3d}/{n} pairs ({(speed):.1f} s/pair) ...")
    
    # 各層の ρ を計算
    layer_rhos = []
    for layer_idx in range(n_layers):
        if len(layer_cosines[layer_idx]) >= 3:
            rho, _ = spearmanr(ccl_sims[:len(layer_cosines[layer_idx])], layer_cosines[layer_idx])
            layer_rhos.append(float(rho) if not np.isnan(rho) else 0.0)
        else:
            layer_rhos.append(0.0)
    
    # 偏相関 (AST distance を制御)
    ast_dists = np.array([p.ast_distance for p in pairs])
    partial_rhos = []
    for layer_idx in range(n_layers):
        if len(layer_cosines[layer_idx]) >= 5:
            cos_arr = np.array(layer_cosines[layer_idx])
            n_pts = len(cos_arr)
            try:
                r_xy, _ = spearmanr(ccl_sims[:n_pts], cos_arr)
                r_xz, _ = spearmanr(ccl_sims[:n_pts], ast_dists[:n_pts])
                r_yz, _ = spearmanr(cos_arr, ast_dists[:n_pts])
                partial = (r_xy - r_xz * r_yz) / (
                    np.sqrt(1 - r_xz**2) * np.sqrt(1 - r_yz**2) + 1e-10
                )
                partial_rhos.append(float(partial) if not np.isnan(partial) else 0.0)
            except:
                partial_rhos.append(0.0)
        else:
            partial_rhos.append(0.0)
    
    best_rho = max(layer_rhos) if layer_rhos else 0.0
    best_layer = int(np.argmax(layer_rhos)) if layer_rhos else 0
    best_partial = max(partial_rhos) if partial_rhos else 0.0
    best_partial_layer = int(np.argmax(partial_rhos)) if partial_rhos else 0
    
    print(f"\n  📊 {condition_code}: best ρ={best_rho:.4f} (L{best_layer}), 偏ρ={best_partial:.4f} (L{best_partial_layer})")
    
    return {
        "condition": condition_name,
        "best_rho": best_rho,
        "best_rho_layer": best_layer,
        "best_partial_rho": best_partial,
        "best_partial_rho_layer": best_partial_layer,
        "layer_rhos": layer_rhos,
        "partial_rhos": partial_rhos,
        "n_pairs": n,
    }

# === メイン ===
def main():
    import argparse
    parser = argparse.ArgumentParser(description="E2 13B TPU SPMD 圧縮実験 (最適化版)")
    parser.add_argument("--dataset-file", default="dataset_v3.json")
    parser.add_argument("--n-pairs", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--model", default="codellama/CodeLlama-13b-hf")
    parser.add_argument("--start-condition", type=int, default=0, help="開始条件 (0=C0)")
    parser.add_argument("--batch-size", type=int, default=16, help="TPUバッチサイズ")
    args = parser.parse_args()
    
    random.seed(args.seed)
    np.random.seed(args.seed)
    
    print(f"\n{'='*60}")
    print(f"  E2 形式的圧縮度 × Probing ρ (13B TPU SPMD Optimized)")
    print(f"  モデル: {args.model}")
    print(f"  データセット: {args.dataset_file}")
    print(f"  n={args.n_pairs}, seed={args.seed}, batch_size={args.batch_size}")
    print(f"{'='*60}")
    
    mesh = create_mesh()
    
    print(f"\n  データ読み込み: {args.dataset_file}")
    with open(args.dataset_file) as f:
        dataset = json.load(f)
    
    all_pairs = dataset if isinstance(dataset, list) else dataset.get("pairs", [])
    print(f"  全ペア数: {len(all_pairs)}")
    
    if len(all_pairs) > args.n_pairs:
        selected = random.sample(all_pairs, args.n_pairs)
    else:
        selected = all_pairs
    
    pairs = []
    for item in selected:
        p = ProbeDataPoint(
            code_a=item.get("func_a_source", item.get("code_a", "")),
            code_b=item.get("func_b_source", item.get("code_b", "")),
            pattern=item.get("pattern", ""),
            is_positive=item.get("is_positive", True),
            ccl_a=item.get("ccl_a", ""),
            ccl_b=item.get("ccl_b", ""),
            ccl_similarity=float(item.get("ccl_similarity", 0)),
            ast_distance=1.0 - float(item.get("ast_similarity", 0)),
        )
        pairs.append(p)
    
    print(f"  選択ペア数: {len(pairs)}")
    
    model, tokenizer, device = load_model_spmd(args.model, mesh)
    
    n_layers = model.config.num_hidden_layers + 1
    print(f"  層数: {n_layers}")
    
    results = {"model": args.model, "n_pairs": len(pairs), "batch_size": args.batch_size, "conditions": {}}
    t_start = time.time()
    
    ckpt_dir = "checkpoints_13b"
    os.makedirs(ckpt_dir, exist_ok=True)
    
    for idx, (code, (name, fn)) in enumerate(CONDITION_MAP.items()):
        if idx < args.start_condition:
            ckpt_path = os.path.join(ckpt_dir, f"ckpt_level_{idx}.json")
            if os.path.exists(ckpt_path):
                print(f"\n  ⏭️ {code} スキップ (チェックポイント復元)")
                with open(ckpt_path) as f:
                    results["conditions"][code] = json.load(f)
                continue
        
        print(f"\n{'='*60}")
        print(f"  条件 {code} ({name}) — {idx+1}/5")
        print(f"{'='*60}")
        
        cond_result = compute_rho_batched(pairs, model, tokenizer, device, code, name, fn, n_layers, batch_size=args.batch_size)
        results["conditions"][code] = cond_result
        
        ckpt_path = os.path.join(ckpt_dir, f"ckpt_level_{idx}.json")
        with open(ckpt_path, "w") as f:
            json.dump(cond_result, f, indent=2)
        print(f"  💾 チェックポイント保存: {ckpt_path}")
    
    elapsed = time.time() - t_start
    print(f"\n{'='*60}")
    print(f"  用量反応分析")
    print(f"{'='*60}")
    print(f"\n  {'条件':<16s} | {'best ρ':>8s} | {'Layer':>5s} | {'偏ρ':>8s} | {'n':>5s}")
    print(f"  {'-'*16}+{'-'*10}+{'-'*7}+{'-'*10}+{'-'*6}")
    
    rhos = []
    for code in ["C0", "C1", "C2", "C3", "C4"]:
        c = results["conditions"][code]
        print(f"  {code} {c['condition']:<12s} | {c['best_rho']:>8.4f} | L{c['best_rho_layer']:>2d} |  {c['best_partial_rho']:>8.4f} | {c['n_pairs']:>5d}")
        rhos.append(c["best_rho"])
    
    from scipy.stats import spearmanr as sp_corr
    from scipy.stats import linregress
    x = np.arange(5)
    sp_rho, sp_p = sp_corr(x, rhos)
    slope, intercept, r, lr_p, se = linregress(x, rhos)
    
    print(f"\n  📈 Spearman 傾向: ρ={sp_rho:.4f}, p={sp_p:.4f}")
    print(f"  📉 線形回帰: slope={slope:.4f}, R²={r**2:.4f}, p={lr_p:.4f}")
    
    results["elapsed_seconds"] = elapsed
    results["hypotheses"] = {
        "H1_monotonic": {
            "rho": float(sp_rho),
            "p": float(sp_p),
            "supported": sp_p < 0.05,
        }
    }
    
    out_file = f"compression_13b_v3_{len(pairs)}_opt.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 結果保存: {out_file} ({elapsed:.0f}s)")

if __name__ == "__main__":
    main()
