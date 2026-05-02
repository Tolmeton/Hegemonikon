#!/usr/bin/env python3
# PROOF: [L2/実験] <- 60_実験｜Peira/07_CCL-PL A0→Phase B検証→LLM hidden stateとCCL構造の相関
"""
Phase B: Structural Probe — LLM は暗黙の U_ccl を持つか？

VISION.md §12.4 Phase B:
  既存 LLM の中間層 hidden state が CCL 構造的類似度と相関するか検証。
  CCL を明示的 ground truth として組み込み、層別の Spearman ρ を測定。

パイプライン:
  1. P3a データ (35ペア) を取得
  2. 各コードスニペットに python_to_ccl() → CCL 文字列を生成
  3. CCL 間の正規化 Levenshtein 距離を計算 (連続 ground truth)
  4. LLM の各層 hidden state を抽出
  5. 層別に cosine(hidden_a, hidden_b) を計算
  6. バイナリ検定 (Mann-Whitney U) + 連続相関 (Spearman ρ) で分析

Usage:
  python structural_probe.py --dry-run                 # データ確認のみ
  python structural_probe.py --model codebert           # M1: CPU
  python structural_probe.py --model codellama --bits 4 # M2: RTX 2070S
  python structural_probe.py --model llama3 --bits 4    # M3: RTX 2070S
  python structural_probe.py --compare                  # 全モデル結果比較
"""

# PURPOSE: Phase B Structural Probe 実験ハーネス

import sys
import os
import ast
import json
import argparse
import textwrap
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

# パス設定
_SCRIPT_DIR = Path(__file__).parent
_HGK_ROOT = _SCRIPT_DIR.parent.parent.parent.parent.parent
_MEKHANE_SRC = _HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"
sys.path.insert(0, str(_MEKHANE_SRC))
sys.path.insert(0, str(_SCRIPT_DIR))

try:
    from mekhane.symploke.code_ingest import python_to_ccl
except ImportError:
    def python_to_ccl(node) -> str:
        import ast
        ops = []
        for n in ast.walk(node):
            if isinstance(n, ast.For): ops.append("F")
            elif isinstance(n, ast.While): ops.append("W")
            elif isinstance(n, ast.If): ops.append("I")
            elif isinstance(n, ast.Return): ops.append("R")
            elif isinstance(n, ast.Call): ops.append("C")
        return " >> ".join(ops) if ops else "_" 

# P3a ベンチマークデータの再利用
try:
    from p3_benchmark import create_benchmark_pairs, StructuralPair
except ImportError:
    create_benchmark_pairs = None
    StructuralPair = None


# ============================================================
# Phase 1: データ準備 + CCL ground truth 計算
# ============================================================

# PURPOSE: 正規化 Levenshtein 距離を計算
def normalized_levenshtein(s1: str, s2: str) -> float:
    """正規化 Levenshtein 距離 (0=同一, 1=完全不一致)。"""
    if s1 == s2:
        return 0.0
    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 1.0

    # DP テーブル (2行で十分)
    prev = list(range(len2 + 1))
    curr = [0] * (len2 + 1)
    for i in range(1, len1 + 1):
        curr[0] = i
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            curr[j] = min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost)
        prev, curr = curr, prev

    return prev[len2] / max(len1, len2)


# ============================================================
# 交絡因子計測関数 (C2-C6)
# ============================================================

# PURPOSE: トークン重複率 (C2) — bag-of-tokens Jaccard
def token_overlap_jaccard(code_a: str, code_b: str) -> float:
    """2つのコード文字列のトークン (空白分割) の Jaccard 係数。"""
    tokens_a = set(code_a.split())
    tokens_b = set(code_b.split())
    if not tokens_a and not tokens_b:
        return 1.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union) if union else 0.0


# PURPOSE: 識別子重複率 (C3) — AST Name ノードの Jaccard
def identifier_overlap_jaccard(code_a: str, code_b: str) -> float:
    """2つのコード文字列内の識別子 (変数名・関数名) の Jaccard 係数。"""
    def _extract_identifiers(code: str) -> set:
        try:
            tree = ast.parse(textwrap.dedent(code))
        except SyntaxError:
            return set()
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.FunctionDef):
                names.add(node.name)
            elif isinstance(node, ast.arg):
                names.add(node.arg)
        return names

    ids_a = _extract_identifiers(code_a)
    ids_b = _extract_identifiers(code_b)
    if not ids_a and not ids_b:
        return 1.0
    union = ids_a | ids_b
    return len(ids_a & ids_b) / len(union) if union else 0.0


# PURPOSE: ASTノード数類似度 (C5)
def ast_node_count_similarity(code_a: str, code_b: str) -> float:
    """ASTノード数の類似度。1 - |n_a - n_b| / max(n_a, n_b)。"""
    def _count_nodes(code: str) -> int:
        try:
            tree = ast.parse(textwrap.dedent(code))
            return sum(1 for _ in ast.walk(tree))
        except SyntaxError:
            return 0

    n_a = _count_nodes(code_a)
    n_b = _count_nodes(code_b)
    max_n = max(n_a, n_b)
    if max_n == 0:
        return 1.0
    return 1.0 - abs(n_a - n_b) / max_n


# PURPOSE: インデント深度類似度 (C6)
def indent_depth_similarity(code_a: str, code_b: str) -> float:
    """最大インデント深度の類似度。"""
    def _max_indent(code: str) -> int:
        max_d = 0
        for line in code.splitlines():
            stripped = line.lstrip()
            if stripped:  # 空行除外
                indent = len(line) - len(stripped)
                max_d = max(max_d, indent // 4)  # 4スペース=1レベル
        return max_d

    d_a = _max_indent(code_a)
    d_b = _max_indent(code_b)
    max_d = max(d_a, d_b)
    if max_d == 0:
        return 1.0
    return 1.0 - abs(d_a - d_b) / max_d


# PURPOSE: コメントと docstring を除去 (C4 実験用)
def strip_comments_and_docstrings(code: str) -> str:
    """コメント (#) と docstring を除去した骨格コードを返す。"""
    import io
    import tokenize
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(code).readline))
    except tokenize.TokenError:
        return code  # フォールバック: そのまま返す

    # コメントと文字列トークンを除外して再構成
    result_tokens = []
    for tok in tokens:
        if tok.type == tokenize.COMMENT:
            continue
        if tok.type == tokenize.STRING:
            # docstring 判定: 文の最初の式がstring literalならdocstring
            # 簡易版: 3重クォートで始まるものは除去
            if tok.string.startswith('"""') or tok.string.startswith("'''"):
                continue
        result_tokens.append(tok)

    try:
        return tokenize.untokenize(result_tokens)
    except ValueError:
        return code


# PURPOSE: 多変量偏相関 (全交絡因子同時制御)
def multivariate_partial_correlation(
    x: np.ndarray, y: np.ndarray, z_matrix: np.ndarray
) -> float:
    """x と y の偏相関 (z_matrix の全列を制御変数として)。

    線形回帰の残差の相関として計算 (Pearson)。
    Args:
        x: (n,) ターゲット変数 (hidden cos)
        y: (n,) 応答変数 (CCL similarity)
        z_matrix: (n, k) 制御変数行列 (k 個の交絡因子)
    Returns:
        偏相関係数
    """
    from numpy.linalg import lstsq

    # x から z の影響を除去
    z_aug = np.column_stack([z_matrix, np.ones(len(x))])  # バイアス項追加
    beta_x, _, _, _ = lstsq(z_aug, x, rcond=None)
    resid_x = x - z_aug @ beta_x

    # y から z の影響を除去
    beta_y, _, _, _ = lstsq(z_aug, y, rcond=None)
    resid_y = y - z_aug @ beta_y

    # 残差の相関
    if np.std(resid_x) == 0 or np.std(resid_y) == 0:
        return 0.0
    return float(np.corrcoef(resid_x, resid_y)[0, 1])


# PURPOSE: コードスニペットから CCL 文字列を抽出
def code_to_ccl(code: str) -> str:
    """コード文字列 → python_to_ccl() で CCL 構造式に変換。"""
    try:
        tree = ast.parse(textwrap.dedent(code))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return python_to_ccl(node)
        return "_"
    except SyntaxError:
        return "_"


@dataclass
class ProbeDataPoint:
    """1ペアの全計測データ。"""
    pair_id: str
    pattern: str
    is_positive: bool             # 正例 (同構造) か負例 (異構造) か
    ccl_a: str = ""               # コード A の CCL
    ccl_b: str = ""               # コード B の CCL
    ccl_distance: float = 0.0     # CCL 正規化編集距離 (0=同一)
    ccl_similarity: float = 1.0   # 1 - ccl_distance
    layer_cosines: list = field(default_factory=list)  # 各層の cosine
    code_len_a: int = 0           # コード A の文字数
    code_len_b: int = 0           # コード B の文字数
    length_similarity: float = 0.0  # 1 - |len_a - len_b| / max(len_a, len_b)
    ast_distance: float = 0.0     # AST 構造距離 (P3b 用, CCL 非依存)
    code_a: str = ""              # コード A のソース (P3b 用)
    code_b: str = ""              # コード B のソース (P3b 用)
    # --- 交絡因子 (C2-C6) ---
    token_overlap: float = 0.0    # C2: トークン重複率 (Jaccard)
    identifier_overlap: float = 0.0  # C3: 識別子重複率 (Jaccard)
    ast_node_similarity: float = 0.0  # C5: ASTノード数類似度
    indent_similarity: float = 0.0    # C6: インデント深度類似度
    # コメント除去後 hidden state (C4 実験用)
    layer_cosines_nocomment: list = field(default_factory=list)


# PURPOSE: P3a ペアを ProbeDataPoint に変換
def prepare_data(max_pairs: int = 0) -> list[ProbeDataPoint]:
    """P3a の35ペアを ProbeDataPoint に変換し、CCL を計算。"""
    raw_pairs = create_benchmark_pairs()

    # 正例 (P01-P20) と負例 (N01-N15) を分離
    data = []
    for pair in raw_pairs:
        is_positive = pair.pair_id.startswith("P")
        ccl_a = code_to_ccl(pair.func_a_source)
        ccl_b = code_to_ccl(pair.func_b_source)
        dist = normalized_levenshtein(ccl_a, ccl_b)

        # コード長の計算
        len_a = len(pair.func_a_source)
        len_b = len(pair.func_b_source)
        max_len = max(len_a, len_b)
        len_sim = 1.0 - abs(len_a - len_b) / max_len if max_len > 0 else 1.0

        dp = ProbeDataPoint(
            pair_id=pair.pair_id,
            pattern=pair.pattern,
            is_positive=is_positive,
            ccl_a=ccl_a,
            ccl_b=ccl_b,
            ccl_distance=dist,
            ccl_similarity=1.0 - dist,
            code_len_a=len_a,
            code_len_b=len_b,
            length_similarity=len_sim,
        )
        data.append(dp)

    if max_pairs > 0:
        data = data[:max_pairs]

    return data


# PURPOSE: P3b 実世界関数からペアを生成 (3ゾーン層化サンプリング)
def prepare_data_p3b(
    target_dir: str = "",
    max_pairs: int = 60,
    max_functions: int = 100,
    seed: int = 42,
) -> list[ProbeDataPoint]:
    """P3b の実世界関数から3ゾーン層化サンプリングでペアを生成。

    実世界コードの AST 距離は 0.6-0.7 に集中するため、ランダムでは正例が出ない。
    3ゾーン層化サンプリングで対処:
      near (AST < 0.5): 正例候補 — 構造的に類似
      mid  (0.5 ≤ AST ≤ 0.7): 中間ペア — 部分的類似
      far  (AST > 0.7): 負例候補 — 構造的に異質
    各ゾーンから max_pairs // 3 ペアを均等サンプリング。
    ゾーン不足時は mid で補填 (最も豊富な層)。
    """
    import random
    from itertools import combinations

    # P3b の extract_functions を import
    from p3b_benchmark import (
        extract_functions, ast_structural_distance, ccl_edit_distance,
        FunctionInfo,
    )

    # ターゲットディレクトリ
    if target_dir:
        target_root = Path(target_dir)
    else:
        target_root = _HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"

    print(f"📂 P3b データソース: {target_root}")
    functions = extract_functions(target_root, max_functions=max_functions, seed=seed)
    print(f"  抽出関数数: {len(functions)}")

    if len(functions) < 2:
        print("⚠️ 関数が2つ未満。ペア生成不可。")
        return []

    # --- Phase 1: 全ペアの AST 距離を事前計算し3ゾーンに分類 ---
    all_indices = list(combinations(range(len(functions)), 2))
    print(f"  📊 全 {len(all_indices)} ペアの AST 距離を計算中...")

    near_pool = []   # AST < 0.5 (正例候補)
    mid_pool = []    # 0.5 ≤ AST ≤ 0.7 (中間)
    far_pool = []    # AST > 0.7 (負例候補)

    for i, j in all_indices:
        fa, fb = functions[i], functions[j]
        ast_dist = ast_structural_distance(fa, fb)
        entry = (i, j, ast_dist)
        if ast_dist < 0.5:
            near_pool.append(entry)
        elif ast_dist <= 0.7:
            mid_pool.append(entry)
        else:
            far_pool.append(entry)

    print(f"  ゾーン分布: near(AST<0.5)={len(near_pool)}, "
          f"mid(0.5-0.7)={len(mid_pool)}, far(>0.7)={len(far_pool)}")

    # --- Phase 2: 3ゾーン層化サンプリング ---
    random.seed(seed)
    per_zone = max_pairs // 3

    def _sample(pool: list, n: int) -> list:
        """ゾーンから n ペアをサンプリング。不足時は全数。"""
        return list(pool) if len(pool) <= n else random.sample(pool, n)

    sampled_near = _sample(near_pool, per_zone)
    sampled_mid = _sample(mid_pool, per_zone)
    sampled_far = _sample(far_pool, per_zone)

    # 不足分を mid で補填 (最も豊富な層)
    total = len(sampled_near) + len(sampled_mid) + len(sampled_far)
    shortfall = max_pairs - total
    if shortfall > 0:
        remaining_mid = [p for p in mid_pool if p not in sampled_mid]
        extra = _sample(remaining_mid, shortfall)
        sampled_mid.extend(extra)

    sampled = sampled_near + sampled_mid + sampled_far
    random.shuffle(sampled)  # ゾーン順序のバイアスを除去

    n_pos = sum(1 for _, _, d in sampled if d < 0.5)
    print(f"  サンプリング: near={len(sampled_near)}, mid={len(sampled_mid)}, "
          f"far={len(sampled_far)}, 計={len(sampled)} (正例={n_pos})")

    # --- Phase 3: ProbeDataPoint に変換 ---
    data = []
    for idx, (i, j, ast_dist) in enumerate(sampled):
        fa, fb = functions[i], functions[j]

        # CCL ground truth
        ccl_a = fa.ccl
        ccl_b = fb.ccl
        ccl_dist = normalized_levenshtein(ccl_a, ccl_b)

        # 正例/負例の二値分類
        is_positive = ast_dist < 0.5

        # コード長
        len_a = len(fa.source)
        len_b = len(fb.source)
        max_len = max(len_a, len_b)
        len_sim = 1.0 - abs(len_a - len_b) / max_len if max_len > 0 else 1.0

        # 交絡因子 (C2-C6)
        c2_tok = token_overlap_jaccard(fa.source, fb.source)
        c3_ident = identifier_overlap_jaccard(fa.source, fb.source)
        c5_ast_n = ast_node_count_similarity(fa.source, fb.source)
        c6_indent = indent_depth_similarity(fa.source, fb.source)

        pair_id = f"R{idx + 1:03d}"  # R = Real-world
        dp = ProbeDataPoint(
            pair_id=pair_id,
            pattern=f"{fa.name}×{fb.name}",
            is_positive=is_positive,
            ccl_a=ccl_a,
            ccl_b=ccl_b,
            ccl_distance=ccl_dist,
            ccl_similarity=1.0 - ccl_dist,
            code_len_a=len_a,
            code_len_b=len_b,
            length_similarity=len_sim,
            ast_distance=ast_dist,
            code_a=fa.source,
            code_b=fb.source,
            token_overlap=c2_tok,
            identifier_overlap=c3_ident,
            ast_node_similarity=c5_ast_n,
            indent_similarity=c6_indent,
        )
        data.append(dp)

    return data


# ============================================================
# Phase 2: モデルロード
# ============================================================

# モデル設定マップ
MODEL_CONFIGS = {
    "codebert": {
        "hf_name": "microsoft/codebert-base",
        "type": "encoder",
        "default_bits": 32,  # 125M → 量子化不要
    },
    "codellama": {
        "hf_name": "codellama/CodeLlama-7b-hf",
        "type": "decoder",
        "default_bits": 4,
    },
    "codellama-13b": {
        "hf_name": "codellama/CodeLlama-13b-hf",
        "type": "decoder",
        "default_bits": 4,
    },
    "mistral": {
        "hf_name": "mistralai/Mistral-7B-v0.3",
        "type": "decoder",
        "default_bits": 4,
    },
    "gemma4": {
        "hf_name": "google/gemma-4-E4B",
        "type": "multimodal",
        "default_bits": 4,
    },
    "gemma4-31b": {
        "hf_name": "google/gemma-4-31B",
        "type": "multimodal",
        "default_bits": 4,
    },
}


# PURPOSE: HuggingFace モデルをロード (量子化対応)
def load_model(model_key: str, bits: int = 0):
    """モデルとトークナイザーをロード。

    Args:
        model_key: MODEL_CONFIGS のキー
        bits: 量子化ビット数 (0=デフォルト, 4=4bit, 8=8bit)
    """
    import torch
    from transformers import AutoModel, AutoTokenizer, AutoModelForCausalLM

    config = MODEL_CONFIGS[model_key]
    hf_name = config["hf_name"]
    model_type = config["type"]
    bits = bits or config["default_bits"]

    print(f"📦 モデルロード: {hf_name} ({bits}bit)")

    tokenizer = AutoTokenizer.from_pretrained(hf_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    kwargs = {}

    if bits == 4:
        from transformers import BitsAndBytesConfig
        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
        )
        kwargs["device_map"] = "auto"
        # GPU VRAM に応じて max_memory を動的設定
        if torch.cuda.is_available():
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            kwargs["max_memory"] = {0: f"{int(vram_gb * 0.85)}GiB", "cpu": "4GiB"}
        else:
            kwargs["max_memory"] = {0: "7GiB", "cpu": "1GiB"}
        kwargs["torch_dtype"] = torch.float16
    elif bits == 8:
        from transformers import BitsAndBytesConfig
        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_8bit=True,
            llm_int8_enable_fp32_cpu_offload=True,
        )
        kwargs["device_map"] = "auto"
        kwargs["max_memory"] = {0: "6GiB", "cpu": "24GiB"}
    else:
        kwargs["torch_dtype"] = torch.float32

    # TPU (XLA) 検出
    _use_tpu = False
    try:
        import torch_xla.core.xla_model as xm
        _xla_dev = xm.xla_device()
        _use_tpu = True
        print(f"  🟢 TPU 検出: {_xla_dev}")
        # TPU では bitsandbytes 不要。bf16 で直接ロード
        kwargs.pop("quantization_config", None)
        kwargs.pop("device_map", None)
        kwargs.pop("max_memory", None)
        kwargs["torch_dtype"] = torch.bfloat16
    except (ImportError, RuntimeError):
        pass

    if model_type == "encoder":
        model = AutoModel.from_pretrained(hf_name, **kwargs)
    elif model_type == "multimodal":
        # Gemma4 等のマルチモーダルモデル: テキストデコーダのみ抽出
        from transformers import AutoModelForImageTextToText
        _full = AutoModelForImageTextToText.from_pretrained(hf_name, **kwargs)
        model = _full.model.language_model
        del _full
    else:
        model = AutoModelForCausalLM.from_pretrained(hf_name, **kwargs)

    model.config.output_hidden_states = True
    model.eval()

    # デバイス配置
    if _use_tpu:
        device = _xla_dev
        model = model.to(device)
    elif "device_map" not in kwargs:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = model.to(device)
    else:
        device = next(model.parameters()).device

    n_layers = model.config.num_hidden_layers
    print(f"  ✅ ロード完了: {n_layers} 層, device={device}")

    return model, tokenizer, device, n_layers


# ============================================================
# Phase 3: Hidden State 抽出
# ============================================================

# PURPOSE: 1つのコードスニペットの全層 hidden state を抽出
def extract_hidden_states(
    code: str, model, tokenizer, device, max_length: int = 512
) -> list[np.ndarray]:
    """各層の mean-pooled hidden state (numpy array) を返す。

    Returns:
        list[np.ndarray] — (n_layers + 1) 個。[0]=embedding層, [1..n]=各Transformer層
    """
    import torch

    inputs = tokenizer(
        code, return_tensors="pt", truncation=True,
        max_length=max_length, padding=True,
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    # hidden_states: tuple of (batch=1, seq_len, hidden_dim) × (n_layers + 1)
    hidden_states = outputs.hidden_states

    # 各層の mean pooling (attention mask を考慮)
    mask = inputs["attention_mask"].unsqueeze(-1).float()  # (1, seq_len, 1)
    pooled = []
    for layer_hs in hidden_states:
        # layer_hs: (1, seq_len, hidden_dim)
        masked = layer_hs * mask
        mean_vec = masked.sum(dim=1) / mask.sum(dim=1)  # (1, hidden_dim)
        pooled.append(mean_vec[0].cpu().float().numpy())

    return pooled


# ============================================================
# Phase 4: 分析
# ============================================================

# PURPOSE: cosine 類似度
def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """2つのベクトルの cosine 類似度。"""
    dot = np.dot(a, b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    if norm == 0:
        return 0.0
    return float(dot / norm)


# PURPOSE: 全分析を実行
def analyze_results(data: list[ProbeDataPoint], n_layers: int, model_key: str) -> dict:
    """層別の Mann-Whitney U + Spearman ρ を計算。"""
    from scipy import stats

    positive = [d for d in data if d.is_positive]
    negative = [d for d in data if not d.is_positive]

    results = {
        "model": model_key,
        "n_positive": len(positive),
        "n_negative": len(negative),
        "layers": [],
    }

    print(f"\n{'='*70}")
    print(f"  分析結果: {model_key} ({n_layers} 層)")
    print(f"  正例={len(positive)}, 負例={len(negative)}")
    print(f"{'='*70}")
    print(f"{'層':>4} | {'正例cos平均':>10} | {'負例cos平均':>10} | {'gap':>8} | {'MW-U p':>10} | {'Spearman ρ':>10} | {'ρ p値':>10}")
    print(f"{'-'*4}-+-{'-'*10}-+-{'-'*10}-+-{'-'*8}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}")

    best_rho = -1.0
    best_rho_layer = -1

    for layer_idx in range(n_layers + 1):
        pos_cos = [d.layer_cosines[layer_idx] for d in positive]
        neg_cos = [d.layer_cosines[layer_idx] for d in negative]

        pos_mean = np.mean(pos_cos)
        neg_mean = np.mean(neg_cos)
        gap = pos_mean - neg_mean

        # Mann-Whitney U 検定 (正例 cos > 負例 cos)
        try:
            mw_stat, mw_p = stats.mannwhitneyu(pos_cos, neg_cos, alternative="greater")
        except Exception:
            mw_p = 1.0

        # Spearman ρ (hidden_cos vs ccl_similarity)
        all_cosines = [d.layer_cosines[layer_idx] for d in data]
        all_ccl_sim = [d.ccl_similarity for d in data]
        try:
            rho, rho_p = stats.spearmanr(all_cosines, all_ccl_sim)
        except Exception:
            rho, rho_p = 0.0, 1.0

        if rho > best_rho:
            best_rho = rho
            best_rho_layer = layer_idx

        sig_mw = "✅" if mw_p < 0.05 else "  "
        sig_rho = "✅" if rho_p < 0.05 and rho > 0 else "  "

        print(f"{layer_idx:4d} | {pos_mean:10.4f} | {neg_mean:10.4f} | {gap:+8.4f} | {mw_p:10.4f} {sig_mw} | {rho:10.4f} {sig_rho} | {rho_p:10.4f}")

        results["layers"].append({
            "layer": layer_idx,
            "pos_cos_mean": float(pos_mean),
            "neg_cos_mean": float(neg_mean),
            "gap": float(gap),
            "mannwhitney_p": float(mw_p),
            "spearman_rho": float(rho),
            "spearman_p": float(rho_p),
        })

    # ペアごとの生データ保存 (偏相関分析用)
    per_pair = []
    for d in data:
        entry = {
            "pair_id": d.pair_id,
            "is_positive": d.is_positive,
            "ccl_similarity": d.ccl_similarity,
            "length_similarity": d.length_similarity,
            "code_len_a": d.code_len_a,
            "code_len_b": d.code_len_b,
            "layer_cosines": d.layer_cosines,
        }
        per_pair.append(entry)
    results["per_pair"] = per_pair

    # 仮説判定
    print(f"\n{'='*70}")
    print("  仮説判定")
    print(f"{'='*70}")

    any_sig_mw = any(l["mannwhitney_p"] < 0.05 for l in results["layers"])
    h_b1 = "✅ 支持" if any_sig_mw else "❌ 不支持"
    print(f"  H_B1 (暗黙の U_ccl): {h_b1}")
    results["H_B1"] = any_sig_mw

    # H_B2: gap が深い層ほど大きい
    gaps = [l["gap"] for l in results["layers"]]
    layer_indices = list(range(len(gaps)))
    try:
        rho_depth, _ = stats.spearmanr(layer_indices, gaps)
    except Exception:
        rho_depth = 0.0
    h_b2 = "✅ 支持" if rho_depth > 0 else "❌ 不支持"
    print(f"  H_B2 (深層で構造抽出): {h_b2} (ρ={rho_depth:.3f})")
    results["H_B2"] = rho_depth > 0
    results["H_B2_rho"] = float(rho_depth)

    # H_B3: 中間層の正例 cos > 0.7
    mid_layer = n_layers // 2
    mid_pos_cos = results["layers"][mid_layer]["pos_cos_mean"]
    h_b3 = "✅ 支持" if mid_pos_cos > 0.7 else "❌ 不支持"
    print(f"  H_B3 (中間層 cos > 0.7): {h_b3} (Layer {mid_layer}: {mid_pos_cos:.4f})")
    results["H_B3"] = mid_pos_cos > 0.7

    # H_B5: Spearman ρ > 0.5
    h_b5 = "✅ 支持" if best_rho > 0.5 else "❌ 不支持"
    print(f"  H_B5 (CCL ↔ hidden ρ > 0.5): {h_b5} (max ρ={best_rho:.4f} @ Layer {best_rho_layer})")
    results["H_B5"] = best_rho > 0.5
    results["best_rho"] = float(best_rho)
    results["best_rho_layer"] = best_rho_layer

    # ============================================================
    # 偏相関分析: コード長の影響を除去 (従来互換)
    # ============================================================
    print(f"\n{'='*70}")
    print("  偏相関分析 (コード長制御)")
    print(f"{'='*70}")

    length_sims = [d.length_similarity for d in data]
    ccl_sims = [d.ccl_similarity for d in data]

    # コード長 vs CCL の相関
    rho_len_ccl, _ = stats.spearmanr(length_sims, ccl_sims)
    print(f"  r(コード長, CCL) = {rho_len_ccl:.4f}")
    results["rho_length_ccl"] = float(rho_len_ccl)

    # 各層で偏相関を計算 (コード長のみ — 従来互換)
    from scipy.stats import rankdata
    print(f"\n{'層':>4} | {'raw ρ':>8} | {'偏ρ (長さ除去)':>14} | {'r(cos,長さ)':>12}")
    print(f"{'-'*4}-+-{'-'*8}-+-{'-'*14}-+-{'-'*12}")

    best_partial = -1.0
    best_partial_layer = -1

    for layer_idx in range(n_layers + 1):
        all_cosines = [d.layer_cosines[layer_idx] for d in data]

        r_x = rankdata(all_cosines)
        r_y = rankdata(ccl_sims)
        r_z = rankdata(length_sims)

        r_xy = np.corrcoef(r_x, r_y)[0, 1]
        r_xz = np.corrcoef(r_x, r_z)[0, 1]
        r_yz = np.corrcoef(r_y, r_z)[0, 1]

        denom = math.sqrt((1 - r_xz**2) * (1 - r_yz**2))
        partial_rho = (r_xy - r_xz * r_yz) / denom if denom > 0 else 0.0

        if partial_rho > best_partial:
            best_partial = partial_rho
            best_partial_layer = layer_idx

        print(f"{layer_idx:4d} | {r_xy:8.4f} | {partial_rho:14.4f} | {r_xz:12.4f}")

        results["layers"][layer_idx]["partial_rho"] = float(partial_rho)
        results["layers"][layer_idx]["r_cos_length"] = float(r_xz)

    results["best_partial_rho"] = float(best_partial)
    results["best_partial_layer"] = best_partial_layer

    print(f"\n  📊 max 偏 ρ = {best_partial:.4f} @ Layer {best_partial_layer}")
    print(f"     (raw ρ = {best_rho:.4f} @ Layer {best_rho_layer})")
    reduction = best_rho - best_partial
    pct = (reduction / best_rho * 100) if best_rho > 0 else 0
    print(f"     コード長による説明率: {pct:.1f}% (Δρ = {reduction:+.4f})")

    if best_partial > 0.3:
        print(f"  ✅ コード長を除去してもなお ρ={best_partial:.3f} の相関 → 構造理解の証拠")
    elif best_partial > 0.1:
        print(f"  ⚠️ コード長を除去すると ρ={best_partial:.3f} に低下 → 限定的な構造理解")
    else:
        print(f"  ❌ コード長を除去すると ρ={best_partial:.3f} → 構造理解は幻想")

    # ============================================================
    # 多変量偏相関: 全交絡因子 (C1-C6) を同時制御
    # ============================================================
    # 交絡因子が計測済みか確認 (P3b データのみ)
    has_confounds = any(d.token_overlap > 0 or d.identifier_overlap > 0 for d in data)
    if has_confounds:
        print(f"\n{'='*70}")
        print("  多変量偏相関 (全交絡因子同時制御)")
        print(f"{'='*70}")

        # 交絡因子間の相関マトリクス
        confound_names = ["C1:コード長", "C2:トークン重複", "C3:識別子重複", "C5:ASTノード数", "C6:インデント"]
        c1 = np.array(length_sims)
        c2 = np.array([d.token_overlap for d in data])
        c3 = np.array([d.identifier_overlap for d in data])
        c5 = np.array([d.ast_node_similarity for d in data])
        c6 = np.array([d.indent_similarity for d in data])
        confound_matrix = np.column_stack([c1, c2, c3, c5, c6])

        # 各交絡因子の統計
        print(f"\n  交絡因子統計:")
        for i, name in enumerate(confound_names):
            vals = confound_matrix[:, i]
            r_ccl, _ = stats.spearmanr(vals, ccl_sims)
            print(f"    {name}: mean={np.mean(vals):.3f}, std={np.std(vals):.3f}, r(CCL)={r_ccl:.3f}")

        # 交絡因子間の相関
        print(f"\n  交絡因子間相関:")
        print(f"{'':>17}", end="")
        for name in confound_names:
            print(f" | {name[:6]:>6}", end="")
        print()
        for i, name_i in enumerate(confound_names):
            print(f"  {name_i:>15}", end="")
            for j in range(len(confound_names)):
                r, _ = stats.spearmanr(confound_matrix[:, i], confound_matrix[:, j])
                print(f" | {r:6.3f}", end="")
            print()

        # 層別の多変量偏相関
        y_rank = rankdata(ccl_sims)
        z_rank = np.column_stack([rankdata(confound_matrix[:, i]) for i in range(confound_matrix.shape[1])])

        print(f"\n{'層':>4} | {'raw ρ':>8} | {'偏ρ(長さのみ)':>12} | {'偏ρ(全C除去)':>12} | {'Δ':>8}")
        print(f"{'-'*4}-+-{'-'*8}-+-{'-'*12}-+-{'-'*12}-+-{'-'*8}")

        best_mv_partial = -1.0
        best_mv_layer = -1

        for layer_idx in range(n_layers + 1):
            all_cosines = [d.layer_cosines[layer_idx] for d in data]
            x_rank = rankdata(all_cosines)

            # 多変量偏相関 (全交絡因子同時制御)
            mv_partial = multivariate_partial_correlation(x_rank, y_rank, z_rank)

            # 従来の1変数偏相関 (比較用)
            single_partial = results["layers"][layer_idx].get("partial_rho", 0.0)
            raw_rho = results["layers"][layer_idx].get("spearman_rho", 0.0)
            delta = mv_partial - single_partial

            if mv_partial > best_mv_partial:
                best_mv_partial = mv_partial
                best_mv_layer = layer_idx

            print(f"{layer_idx:4d} | {raw_rho:8.4f} | {single_partial:12.4f} | {mv_partial:12.4f} | {delta:+8.4f}")

            results["layers"][layer_idx]["mv_partial_rho"] = float(mv_partial)

        results["best_mv_partial_rho"] = float(best_mv_partial)
        results["best_mv_partial_layer"] = best_mv_layer

        print(f"\n  📊 max 多変量偏ρ = {best_mv_partial:.4f} @ Layer {best_mv_layer}")
        print(f"     (コード長のみ偏ρ = {best_partial:.4f} @ Layer {best_partial_layer})")
        mv_reduction = best_partial - best_mv_partial
        print(f"     追加交絡因子による説明率: {mv_reduction:+.4f}")

        if best_mv_partial > 0.2:
            print(f"  ✅ 全交絡因子を除去してもρ={best_mv_partial:.3f} → 純粋な構造理解の証拠")
        elif best_mv_partial > 0.1:
            print(f"  ⚠️ 全交絡因子を除去するとρ={best_mv_partial:.3f} → 弱い構造理解")
        else:
            print(f"  ❌ 全交絡因子を除去するとρ={best_mv_partial:.3f} → 構造理解は幻想")

    # ペアごとの生データに交絡因子を追加
    for i, entry in enumerate(results.get("per_pair", [])):
        d = data[i]
        entry["token_overlap"] = d.token_overlap
        entry["identifier_overlap"] = d.identifier_overlap
        entry["ast_node_similarity"] = d.ast_node_similarity
        entry["indent_similarity"] = d.indent_similarity

    return results


# ============================================================
# Phase 5: 出力 + 比較
# ============================================================

# PURPOSE: numpy 型を JSON シリアライズ可能にするエンコーダ
class _NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


# PURPOSE: 結果を JSON に保存
def save_results(results: dict, model_key: str, data_source: str = "p3a"):
    """結果を JSON ファイルに保存。"""
    suffix = f"_{data_source}" if data_source != "p3a" else ""
    out_path = _SCRIPT_DIR / f"phase_b_{model_key}{suffix}.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, cls=_NumpyEncoder)
    print(f"\n💾 結果保存: {out_path}")


# PURPOSE: 複数モデルの結果を比較
def compare_models():
    """保存済みの全モデル結果を読み込んで比較。"""
    from scipy import stats

    results = {}
    for key in MODEL_CONFIGS:
        path = _SCRIPT_DIR / f"phase_b_{key}.json"
        if path.exists():
            with open(path) as f:
                results[key] = json.load(f)

    if len(results) < 2:
        print(f"⚠️ 比較には2モデル以上の結果が必要 (現在: {len(results)})")
        return

    print(f"\n{'='*70}")
    print("  多モデル比較")
    print(f"{'='*70}")
    print(f"{'モデル':>12} | {'best ρ':>8} | {'best layer':>10} | {'H_B1':>6} | {'H_B5':>6}")
    print(f"{'-'*12}-+-{'-'*8}-+-{'-'*10}-+-{'-'*6}-+-{'-'*6}")

    for key, res in results.items():
        h1 = "✅" if res.get("H_B1") else "❌"
        h5 = "✅" if res.get("H_B5") else "❌"
        print(f"{key:>12} | {res.get('best_rho', 0):.4f}   | {res.get('best_rho_layer', -1):>10} | {h1:>6} | {h5:>6}")

    # H_B4: CodeLlama > Llama3
    if "codellama" in results and "llama3" in results:
        rho_cl = results["codellama"].get("best_rho", 0)
        rho_l3 = results["llama3"].get("best_rho", 0)
        h_b4 = "✅ 支持" if rho_cl > rho_l3 else "❌ 不支持"
        print(f"\n  H_B4 (コード訓練効果): {h_b4}")
        print(f"    CodeLlama ρ={rho_cl:.4f} vs Llama3 ρ={rho_l3:.4f}")


# ============================================================
# メイン
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Phase B: Structural Probe")
    parser.add_argument("--model", choices=list(MODEL_CONFIGS.keys()),
                        default="codebert", help="使用モデル")
    parser.add_argument("--bits", type=int, default=0,
                        help="量子化ビット数 (0=デフォルト, 4, 8)")
    parser.add_argument("--max-pairs", type=int, default=0,
                        help="使用ペア数の上限 (0=全ペア, P3b デフォルト=50)")
    parser.add_argument("--max-length", type=int, default=512,
                        help="トークン最大長")
    parser.add_argument("--dry-run", action="store_true",
                        help="データ確認のみ (モデルロードなし)")
    parser.add_argument("--compare", action="store_true",
                        help="保存済み結果の多モデル比較")
    parser.add_argument("--data", choices=["p3a", "p3b"],
                        default="p3a", help="データソース (p3a=合成35ペア, p3b=実世界)")
    parser.add_argument("--target-dir", type=str, default="",
                        help="P3b 用: 対象ディレクトリ (デフォルト=mekhane/)")
    parser.add_argument("--max-functions", type=int, default=0,
                        help="P3b 用: 抽出関数数の上限 (0=デフォルト100)")
    args = parser.parse_args()

    # 比較モード
    if args.compare:
        compare_models()
        return

    # Phase 1: データ準備
    print("=" * 70)
    print("  Phase B: Structural Probe")
    print(f"  LLM は暗黙の U_ccl (Code→CCL 忘却関手) を持つか？ [data={args.data}]")
    print("=" * 70)

    if args.data == "p3b":
        max_p = args.max_pairs if args.max_pairs > 0 else 60
        max_f = args.max_functions if args.max_functions > 0 else 100
        data = prepare_data_p3b(
            target_dir=args.target_dir,
            max_pairs=max_p,
            max_functions=max_f,
        )
    else:
        data = prepare_data(max_pairs=args.max_pairs)

    positive = [d for d in data if d.is_positive]
    negative = [d for d in data if not d.is_positive]

    print(f"\n📊 データ: {len(data)} ペア (正例={len(positive)}, 負例={len(negative)})")

    if args.data == "p3b":
        # P3b: AST 距離も表示
        print(f"\n{'ID':>5} | {'種別':>4} | {'AST距離':>7} | {'CCL距離':>7} | {'CCL A (先頭40文字)':40} | {'CCL B (先頭40文字)':40}")
        print(f"{'-'*5}-+-{'-'*4}-+-{'-'*7}-+-{'-'*7}-+-{'-'*40}-+-{'-'*40}")
        for d in data:
            label = "正例" if d.is_positive else "負例"
            print(f"{d.pair_id:>5} | {label:>4} | {d.ast_distance:7.3f} | {d.ccl_distance:7.3f} | {d.ccl_a[:40]:40} | {d.ccl_b[:40]:40}")
    else:
        print(f"\n{'ID':>5} | {'種別':>4} | {'CCL距離':>7} | {'CCL A (先頭50文字)':50} | {'CCL B (先頭50文字)':50}")
        print(f"{'-'*5}-+-{'-'*4}-+-{'-'*7}-+-{'-'*50}-+-{'-'*50}")
        for d in data:
            label = "正例" if d.is_positive else "負例"
            print(f"{d.pair_id:>5} | {label:>4} | {d.ccl_distance:7.3f} | {d.ccl_a[:50]:50} | {d.ccl_b[:50]:50}")

    # CCL ground truth の統計
    pos_dists = [d.ccl_distance for d in positive]
    neg_dists = [d.ccl_distance for d in negative]
    print(f"\n📐 CCL 距離統計:")
    print(f"  正例: 平均={np.mean(pos_dists):.3f}, 中央値={np.median(pos_dists):.3f}")
    print(f"  負例: 平均={np.mean(neg_dists):.3f}, 中央値={np.median(neg_dists):.3f}")

    if args.data == "p3b":
        ast_dists = [d.ast_distance for d in data]
        print(f"\n📐 AST 距離統計:")
        print(f"  全体: 平均={np.mean(ast_dists):.3f}, 中央値={np.median(ast_dists):.3f}, min={min(ast_dists):.3f}, max={max(ast_dists):.3f}")
        # CCL 距離と AST 距離の相関 (ground truth の独立性確認)
        from scipy import stats as _stats
        rho_gt, p_gt = _stats.spearmanr([d.ccl_distance for d in data], ast_dists)
        print(f"  ρ(CCL距離, AST距離) = {rho_gt:.4f} (p={p_gt:.4e}) — ground truth 間の相関")

    if args.dry_run:
        print("\n🏁 dry-run 完了。モデルロードは省略。")
        return

    # Phase 2: モデルロード
    model, tokenizer, device, n_layers = load_model(args.model, args.bits)

    # Phase 3: Hidden State 抽出 + cosine 計算
    print(f"\n🔬 Hidden State 抽出中 ({len(data)} ペア × 2 スニペット)...")
    for i, dp in enumerate(data):
        # P3b: コードは ProbeDataPoint に直接保持
        if dp.code_a and dp.code_b:
            code_a = dp.code_a
            code_b = dp.code_b
        else:
            # P3a: キャッシュ経由で取得
            code_a = _get_code_for_pair(dp.pair_id, "a")
            code_b = _get_code_for_pair(dp.pair_id, "b")

        hs_a = extract_hidden_states(code_a, model, tokenizer, device, args.max_length)
        hs_b = extract_hidden_states(code_b, model, tokenizer, device, args.max_length)

        dp.layer_cosines = [
            cosine_similarity(hs_a[l], hs_b[l])
            for l in range(n_layers + 1)
        ]

        if (i + 1) % 10 == 0 or i == len(data) - 1:
            print(f"  進捗: {i + 1}/{len(data)}")

    # Phase 4: 分析
    results = analyze_results(data, n_layers, args.model)

    # P3b 追加分析: AST 距離との相関
    if args.data == "p3b":
        from scipy import stats as _stats
        print(f"\n{'='*70}")
        print("  P3b 追加分析: hidden cos vs AST 距離")
        print(f"{'='*70}")
        ast_dists_inv = [1.0 - d.ast_distance for d in data]  # 距離→類似度に変換
        print(f"{'層':>4} | {'ρ(cos, ASTsim)':>14} | {'p値':>10}")
        print(f"{'-'*4}-+-{'-'*14}-+-{'-'*10}")
        best_ast_rho = -1.0
        best_ast_layer = -1
        for layer_idx in range(n_layers + 1):
            all_cosines = [d.layer_cosines[layer_idx] for d in data]
            rho, p = _stats.spearmanr(all_cosines, ast_dists_inv)
            if rho > best_ast_rho:
                best_ast_rho = rho
                best_ast_layer = layer_idx
            sig = "✅" if p < 0.05 and rho > 0 else "  "
            print(f"{layer_idx:4d} | {rho:14.4f} | {p:10.4f} {sig}")
        results["best_ast_rho"] = float(best_ast_rho)
        results["best_ast_rho_layer"] = best_ast_layer
        print(f"\n  📊 max ρ(cos, ASTsim) = {best_ast_rho:.4f} @ Layer {best_ast_layer}")

    # Phase 5: 保存
    save_results(results, args.model, data_source=args.data)


# PURPOSE: pair_id からソースコードを再取得するヘルパー
_PAIR_CACHE: dict = {}


def _get_code_for_pair(pair_id: str, side: str) -> str:
    """P3a の pair_id に対応するソースコードを取得。

    Args:
        pair_id: "P01", "N05" など
        side: "a" or "b"
    """
    global _PAIR_CACHE
    if not _PAIR_CACHE:
        for p in create_benchmark_pairs():
            _PAIR_CACHE[p.pair_id] = p

    pair = _PAIR_CACHE.get(pair_id)
    if pair is None:
        return ""
    return pair.func_a_source if side == "a" else pair.func_b_source


if __name__ == "__main__":
    main()
