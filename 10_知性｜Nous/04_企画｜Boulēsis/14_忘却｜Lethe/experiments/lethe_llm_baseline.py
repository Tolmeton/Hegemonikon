#!/usr/bin/env python3
"""Lēthē LLM Zero-Shot Baseline — CCL 構造類似度の LLM 判定実験。

Force is Oblivion / Hegemonikón Research (Lēthē)

目的: Phase C の QLoRA 微調整モデル (ρ≈0.96) に対する LLM zero-shot ベースラインを確立する。
  Gemini CLI を gemini_bridge 経由で呼び出し、CCL ペアの構造的類似度を 0.0-1.0 で判定。

接続:
  - gemini_bridge.run_gemini() → Gemini CLI → 6垢ローテーション
  - phase_c_condition_A.jsonl → CCL テキストペア (条件 A: CCL のみ)
  - phase_c_v3.py と同一メトリクス (Spearman ρ, Accuracy, F1)

Usage:
  SRC="20_機構｜Mekhane/_src｜ソースコード"
  # Quick test (最初の 10 ペア)
  python lethe_llm_baseline.py --quick

  # Full run (全ペア)
  python lethe_llm_baseline.py --data phase_c_condition_A_full.jsonl

  # 特定モデル指定
  python lethe_llm_baseline.py --quick --model gemini-2.5-flash
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

import numpy as np

_SCRIPT_DIR = Path(__file__).parent

# gemini_bridge は mekhane パッケージ内。PYTHONPATH に追加
_SRC_DIR = Path(__file__).resolve().parents[4] / "20_機構｜Mekhane" / "_src｜ソースコード"
sys.path.insert(0, str(_SRC_DIR))

from mekhane.ochema.gemini_bridge import run_gemini  # noqa: E402


# ---------------------------------------------------------------------------
# Multi-backend LLM dispatch
# ---------------------------------------------------------------------------

def _find_cli(name: str, known_paths: list[str] | None = None) -> str:
    """CLI バイナリのフルパスを解決。"""
    path = shutil.which(name)
    if path:
        return path
    for p in (known_paths or []):
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return name  # fallback: PATH に任せる


_CODEX_PATH = _find_cli("codex", [
    os.path.expanduser("~/.antigravity/extensions/.e7159d27-f7c2-4a65-b37d-66dccee915dc/bin/linux-x86_64/codex"),
])
_CURSOR_PATH = _find_cli("cursor", ["/usr/bin/cursor"])
_CLAUDE_PATH = _find_cli("claude", [os.path.expanduser("~/.local/bin/claude")])


def _run_codex(prompt: str, *, timeout: int = 120, **_kw) -> dict:
    """Codex CLI (GPT-5.4) で実行。

    v0.118.0 workaround: 非ASCII CWD が HTTP ヘッダーに入り WebSocket 接続失敗するため
    -C /tmp で ASCII パスを強制。-o で最終メッセージのみ抽出。
    """
    import subprocess as sp
    import tempfile
    t0 = time.time()
    out_fd, out_path = tempfile.mkstemp(suffix=".txt", prefix="codex_")
    os.close(out_fd)
    try:
        result = sp.run(
            [_CODEX_PATH, "exec",
             "-C", "/tmp", "--skip-git-repo-check",
             "--full-auto", "-o", out_path, "-"],
            input=prompt,
            capture_output=True, text=True, timeout=timeout,
        )
        elapsed = round(time.time() - t0, 1)
        answer = ""
        if os.path.isfile(out_path):
            with open(out_path) as f:
                answer = f.read().strip()
        if result.returncode == 0 and answer:
            return {"status": "ok", "output": answer,
                    "elapsed_s": elapsed, "account": "codex"}
        return {"status": "error", "error": result.stderr[:200],
                "elapsed_s": elapsed, "account": "codex"}
    except sp.TimeoutExpired:
        return {"status": "error", "error": f"timeout ({timeout}s)",
                "elapsed_s": timeout, "account": "codex"}
    finally:
        if os.path.isfile(out_path):
            os.unlink(out_path)


def _run_claude(prompt: str, *, timeout: int = 120, **_kw) -> dict:
    """Claude Code CLI (Opus 4.6) で実行。"""
    import subprocess as sp
    t0 = time.time()
    try:
        result = sp.run(
            [_CLAUDE_PATH, "-p", prompt, "--allowedTools", ""],
            capture_output=True, text=True, timeout=timeout,
        )
        elapsed = round(time.time() - t0, 1)
        if result.returncode == 0 and result.stdout.strip():
            return {"status": "ok", "output": result.stdout.strip(),
                    "elapsed_s": elapsed, "account": "claude"}
        return {"status": "error", "error": result.stderr[:200],
                "elapsed_s": elapsed, "account": "claude"}
    except sp.TimeoutExpired:
        return {"status": "error", "error": f"timeout ({timeout}s)",
                "elapsed_s": timeout, "account": "claude"}


def _run_cursor(prompt: str, *, timeout: int = 120, **_kw) -> dict:
    """Cursor Agent (Composer 2) で実行。"""
    import subprocess as sp
    t0 = time.time()
    try:
        result = sp.run(
            [_CURSOR_PATH, "agent", "-p", prompt],
            capture_output=True, text=True, timeout=timeout,
        )
        elapsed = round(time.time() - t0, 1)
        if result.returncode == 0 and result.stdout.strip():
            return {"status": "ok", "output": result.stdout.strip(),
                    "elapsed_s": elapsed, "account": "cursor"}
        return {"status": "error", "error": result.stderr[:200],
                "elapsed_s": elapsed, "account": "cursor"}
    except sp.TimeoutExpired:
        return {"status": "error", "error": f"timeout ({timeout}s)",
                "elapsed_s": timeout, "account": "cursor"}


def _run_gemini_wrapper(prompt: str, *, model: str = "", sandbox: bool = False,
                        timeout: int = 120, **_kw) -> dict:
    """Gemini bridge wrapper (デフォルト)。"""
    return run_gemini(
        prompt, model=model, sandbox=sandbox,
        timeout=timeout, max_retries=3, rotate_before=True,
    )


_BACKENDS = {
    "gemini": _run_gemini_wrapper,
    "codex": _run_codex,
    "claude": _run_claude,
    "cursor": _run_cursor,
}


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

_SYSTEM_PROMPTS = {
    "ccl": """\
あなたは CCL (Cognitive Command Language) の構造解析エキスパートです。
CCL は認知操作を記述する形式言語で、以下の演算子を使います:
  >> = 射 (構造的変換)
  * = 融合 (精度加重統合)
  % = 展開 (テンソル積)
  ~ = 振動 (動的往復)
  V:{} = 検証ゲート
  F:[] = 反復
  I:[] = 条件分岐
  # = 内部状態変数
  ¥ = 外部入力変数

2つの CCL 式の「構造的類似度」を判定してください。
表面的な文字列の一致ではなく、計算グラフの構造（演算子の配置、ネスト、データフロー）を比較してください。""",
    "code": """\
あなたはソースコードの構造解析エキスパートです。

2つのコードスニペットの「構造的類似度」を判定してください。
表面的な文字列の一致ではなく、計算構造（制御フロー、データフロー、関数呼出パターン、テストパターン）を比較してください。""",
    "mixed": """\
あなたはソースコードと CCL (Cognitive Command Language) の構造解析エキスパートです。
各テキストにはソースコード (### Code) と CCL 式 (### CCL) が含まれます。
CCL の主要演算子: >> (射), * (融合), % (展開), ~ (振動), V:{} (検証), F:[] (反復), # (内部状態), ¥ (外部入力)

2つのテキストの「構造的類似度」を判定してください。
コードの計算構造と CCL の演算子構造の両方を考慮してください。""",
}

_PAIR_PROMPT_TEMPLATE = """\
{system}

---
テキスト A: {text_a}

テキスト B: {text_b}
---

この2つのテキストの構造的類似度を 0.0（完全に異なる）から 1.0（構造的に同一）の数値で答えてください。
数値のみを1行で出力してください（例: 0.72）。"""


def build_prompt(text_a: str, text_b: str, *, mode: str = "ccl") -> str:
    """ペア判定プロンプトを構築。"""
    system = _SYSTEM_PROMPTS.get(mode, _SYSTEM_PROMPTS["ccl"])
    max_len = 500 if mode == "ccl" else 800
    return _PAIR_PROMPT_TEMPLATE.format(
        system=system,
        text_a=text_a[:max_len],
        text_b=text_b[:max_len],
    )


def parse_score(output: str) -> float | None:
    """Gemini 出力から 0.0-1.0 の数値を抽出。"""
    if not output:
        return None
    # 出力から数値を探す (最初に見つかった 0.XX or 1.0 or 0.X パターン)
    match = re.search(r"\b([01](?:\.\d+)?)\b", output)
    if match:
        val = float(match.group(1))
        if 0.0 <= val <= 1.0:
            return val
    return None


# ---------------------------------------------------------------------------
# Experiment runner
# ---------------------------------------------------------------------------

def run_experiment(
    data_path: Path,
    *,
    model: str = "",
    max_pairs: int = 0,
    timeout: int = 60,
    sandbox: bool = False,
    prompt_mode: str = "ccl",
    backend: str = "gemini",
) -> dict:
    """LLM でペアの構造類似度を判定し、メトリクスを計算。

    Args:
        data_path: JSONL データパス
        model: モデル名 (gemini backend のみ)
        max_pairs: 最大ペア数 (0=全件)
        timeout: 各呼出しのタイムアウト秒
        sandbox: True=--sandbox (gemini のみ)
        prompt_mode: ccl / code / mixed
        backend: gemini / codex / claude

    Returns:
        dict: 実験結果 (metrics + per-pair results)
    """
    # データ読込
    records = []
    with open(data_path, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))

    if max_pairs > 0 and max_pairs < len(records):
        # 層化サンプリング: 正例・負例を均等に取得
        rng = np.random.RandomState(42)
        pos = [r for r in records if r["label"] == 1]
        neg = [r for r in records if r["label"] == 0]
        half = max_pairs // 2
        rng.shuffle(pos)
        rng.shuffle(neg)
        records = pos[:half] + neg[:max_pairs - half]
        rng.shuffle(records)

    llm_fn = _BACKENDS.get(backend, _run_gemini_wrapper)
    print(f"[lethe] {len(records)} pairs from {data_path.name}")
    print(f"[lethe] backend={backend}, model={model or 'default'}, prompt_mode={prompt_mode}")

    results = []
    parse_failures = 0
    start_time = time.time()

    for i, rec in enumerate(records):
        prompt = build_prompt(rec["text_a"], rec["text_b"], mode=prompt_mode)
        resp = llm_fn(prompt, model=model, sandbox=sandbox, timeout=timeout)

        pred_score = None
        if resp["status"] == "ok":
            pred_score = parse_score(resp["output"])

        if pred_score is None:
            parse_failures += 1

        results.append({
            "index": i,
            "label": rec["label"],
            "cosine_49d": rec.get("cosine_49d"),
            "ccl_edit_dist": rec.get("ccl_edit_dist"),
            "pred_score": pred_score,
            "raw_output": resp.get("output", "")[:200] if resp["status"] == "ok" else None,
            "status": resp["status"],
            "account": resp.get("account"),
            "elapsed_s": resp.get("elapsed_s"),
        })

        status_char = "✓" if pred_score is not None else "✗"
        score_str = f"{pred_score:.2f}" if pred_score is not None else "N/A"
        print(f"  [{i+1}/{len(records)}] {status_char} score={score_str} label={rec['label']} ({resp.get('elapsed_s', '?')}s)")

    elapsed_total = time.time() - start_time

    # --- メトリクス計算 ---
    valid_results = [r for r in results if r["pred_score"] is not None]
    metrics: dict = {
        "total_pairs": len(records),
        "valid_pairs": len(valid_results),
        "parse_failures": parse_failures,
        "elapsed_s": round(elapsed_total, 1),
    }

    if len(valid_results) >= 5:
        pred_scores = np.array([r["pred_score"] for r in valid_results])
        true_cosine = np.array([r["cosine_49d"] for r in valid_results])
        true_binary = np.array([r["label"] for r in valid_results])

        # Spearman ρ (numpy-only — scipy が Python 3.13 で壊れるため)
        def _rankdata(x: np.ndarray) -> np.ndarray:
            """Simple rank (no ties handling — sufficient for this use case)."""
            order = x.argsort()
            ranks = np.empty_like(order, dtype=float)
            ranks[order] = np.arange(1, len(x) + 1, dtype=float)
            return ranks

        def _spearmanr(a: np.ndarray, b: np.ndarray) -> float:
            ra, rb = _rankdata(a), _rankdata(b)
            n = len(a)
            d = ra - rb
            return float(1 - 6 * np.sum(d ** 2) / (n * (n ** 2 - 1)))

        rho = _spearmanr(pred_scores, true_cosine)
        metrics["spearman_rho"] = round(rho, 4)

        # Binary accuracy & F1 (threshold 0.5)
        pred_binary = (pred_scores >= 0.5).astype(int)
        acc = float(np.mean(pred_binary == true_binary))
        tp = int(np.sum((pred_binary == 1) & (true_binary == 1)))
        fp = int(np.sum((pred_binary == 1) & (true_binary == 0)))
        fn = int(np.sum((pred_binary == 0) & (true_binary == 1)))
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        metrics["accuracy"] = round(acc, 4)
        metrics["f1"] = round(f1, 4)
        metrics["precision"] = round(precision, 4)
        metrics["recall"] = round(recall, 4)

    return {
        "experiment": "lethe_llm_baseline",
        "data": data_path.name,
        "backend": backend,
        "model": model or "default",
        "prompt_mode": prompt_mode,
        "metrics": metrics,
        "results": results,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lēthē LLM Zero-Shot Baseline — CCL 構造類似度判定",
    )
    parser.add_argument(
        "--data", default="phase_c_condition_A.jsonl",
        help="JSONL データファイル (デフォルト: condition A)",
    )
    parser.add_argument("-m", "--model", default="", help="Gemini モデル名")
    parser.add_argument("--quick", action="store_true", help="Quick test (10 pairs)")
    parser.add_argument("-n", "--max-pairs", type=int, default=0, help="最大ペア数")
    parser.add_argument("--timeout", type=int, default=120, help="各呼出しタイムアウト秒")
    parser.add_argument("--sandbox", action="store_true", help="--sandbox モード (Docker, 遅い)")
    parser.add_argument(
        "--prompt-mode", choices=["ccl", "code", "mixed"], default="ccl",
        help="プロンプトモード: ccl (条件A), code (条件D), mixed (条件B)",
    )
    parser.add_argument(
        "--backend", choices=["gemini", "codex", "claude", "cursor"], default="gemini",
        help="LLM バックエンド: gemini / codex (GPT-5.4) / claude (Opus 4.6) / cursor (Composer 2)",
    )
    parser.add_argument("-o", "--output", default="", help="結果出力先 (JSON)")
    args = parser.parse_args()

    data_path = _SCRIPT_DIR / args.data
    if not data_path.exists():
        print(f"Error: {data_path} not found", file=sys.stderr)
        sys.exit(1)

    max_pairs = args.max_pairs
    if args.quick:
        max_pairs = 10

    result = run_experiment(
        data_path,
        model=args.model,
        max_pairs=max_pairs,
        timeout=args.timeout,
        sandbox=args.sandbox,
        prompt_mode=args.prompt_mode,
        backend=args.backend,
    )

    # 結果出力
    output_path = args.output
    if not output_path:
        output_path = f"lethe_llm_baseline_{result['model']}.json"
    output_path = _SCRIPT_DIR / output_path

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"[lethe] Results saved to {output_path.name}")
    print(f"[lethe] Metrics:")
    for k, v in result["metrics"].items():
        print(f"  {k}: {v}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
