"""
介入実験: 選択的忘却定理 v3 の検証

v3 核心予測: |∇_t Θ| > 0 → P > P(∇_t Θ = 0)

設計原理:
  - 総情報予算を固定 (例: 50%) し、配分のみを操作
  - 3戦略: U(均等), G(勾配), S(二値)
  - P = LLM が生成したパッチの正解パッチとの一致度

データ: nebius/SWE-agent-trajectories (成功 trajectory のみ)
LLM: Gemini 3.1 Pro via ochema (round-robin)

使い方:
  python intervention_experiment.py --n_per_strategy 5 --budget 0.5 --output /tmp/intervention_pilot.json
"""
import json
import numpy as np
import argparse
import sys
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional


# --- 定数 ---
BUDGET_DEFAULT = 0.5  # 情報保持率 (0.5 = 50% 保持)


# --- データ構造 ---
@dataclass
class TrajectoryEntry:
    """trajectory の1エントリ"""
    role: str       # system / user / ai
    text: str       # テキスト内容
    turn_idx: int   # turn 番号 (0始まり)
    char_len: int   # 文字数


@dataclass
class MaskedContext:
    """操作後の context"""
    system_prompt: str
    issue_text: str
    turns: list  # [{role, text, original_len, masked_len}]
    strategy: str
    budget: float
    actual_retention: float  # 実際の保持率
    grad_theta: list  # 各 turn の Θ(t)
    total_original_chars: int
    total_masked_chars: int


# --- trajectory パーサー ---
def _extract_text(entry: dict) -> str:
    """エントリからテキストを抽出。text/content/message の順に探索。"""
    text = entry.get("text", "") or entry.get("content", "") or entry.get("message", "") or ""
    # リスト形式の場合
    if isinstance(text, list):
        text = " ".join(
            item.get("text", str(item)) if isinstance(item, dict) else str(item)
            for item in text
        )
    if not isinstance(text, str):
        text = str(text) if text else ""
    return text


def parse_trajectory(raw_traj: list) -> tuple:
    """
    trajectory を system_prompt, issue_text, turns に分離。
    
    SWE-agent の role 構造:
      - system: システムプロンプト
      - user: 最初の1つ = issue text
      - user/tool: observation (環境からの入力)
      - ai/assistant: action (エージェントの出力)
    
    Returns:
        system_prompt: str
        issue_text: str  
        turns: list of TrajectoryEntry
    """
    system_prompt = ""
    issue_text = ""
    turns = []
    found_first_user = False
    
    for i, entry in enumerate(raw_traj):
        if not isinstance(entry, dict):
            continue
        role = entry.get("role", "")
        text = _extract_text(entry)
        
        if role == "system":
            system_prompt = text
        elif role == "user" and not found_first_user:
            # 最初の user メッセージ = issue text
            issue_text = text
            found_first_user = True
        elif role in ("user", "tool", "ai", "assistant"):
            # observation (user/tool) と action (ai/assistant) を交互に収集
            normalized_role = "ai" if role in ("ai", "assistant") else "user"
            turns.append(TrajectoryEntry(
                role=normalized_role, text=text, turn_idx=len(turns), char_len=len(text)
            ))
    
    return system_prompt, issue_text, turns


# --- 3戦略の実装 ---
def apply_strategy_U(turns: list, budget: float) -> list:
    """
    戦略 U (均等): 各 turn を一律 budget 比率で截断。
    ∇_t Θ = 0 (真のゼロ)
    """
    masked = []
    for t in turns:
        keep_len = max(1, int(t.char_len * budget))
        masked_text = t.text[:keep_len]
        if keep_len < t.char_len:
            masked_text += "... [truncated]"
        masked.append({
            "role": t.role,
            "text": masked_text,
            "original_len": t.char_len,
            "masked_len": len(masked_text),
        })
    return masked


def apply_strategy_G(turns: list, budget: float) -> list:
    """
    戦略 G (勾配): 新しい turn ほど多く保持。古い turn は少なく。
    総保持文字数は U と同一。
    ∇_t Θ = 一定正 (線形勾配)
    """
    n = len(turns)
    if n == 0:
        return []
    
    # 線形重み: 新しい turn ほど大きい (0.2 → 1.8)
    # 正規化して総量 = budget × 総文字数 になるように
    weights = np.linspace(0.2, 1.8, n)
    
    # 各 turn の理想的保持文字数を計算
    total_chars = sum(t.char_len for t in turns)
    target_total = int(total_chars * budget)
    
    # 重み × 文字数 で配分
    raw_alloc = np.array([w * t.char_len for w, t in zip(weights, turns)])
    raw_sum = raw_alloc.sum()
    if raw_sum > 0:
        alloc = (raw_alloc / raw_sum * target_total).astype(int)
    else:
        alloc = np.ones(n, dtype=int)
    
    # 各 turn の上限 = 元の文字数
    alloc = np.minimum(alloc, [t.char_len for t in turns])
    alloc = np.maximum(alloc, 1)
    
    masked = []
    for t, keep_len in zip(turns, alloc):
        masked_text = t.text[:keep_len]
        if keep_len < t.char_len:
            masked_text += "... [truncated]"
        masked.append({
            "role": t.role,
            "text": masked_text,
            "original_len": t.char_len,
            "masked_len": len(masked_text),
        })
    return masked


def apply_strategy_S(turns: list, budget: float) -> list:
    """
    戦略 S (二値): budget 割合の turn を完全保持、残りを完全除去。
    総保持文字数は U と同一 (近似)。
    ∇_t Θ = デルタ関数 (保持/除去の境界で跳躍)
    
    除去する turn は均等間隔で選ぶ (偏りを排除)。
    """
    n = len(turns)
    if n == 0:
        return []
    
    total_chars = sum(t.char_len for t in turns)
    target_total = int(total_chars * budget)
    
    # 文字数順にソートして、大きい turn から保持するとバランスが偏る
    # → 等間隔サンプリングで保持 turn を選ぶ
    # budget=0.5 なら半分の turn を保持
    n_keep = max(1, int(n * budget))
    
    # 等間隔で保持する turn のインデックスを計算
    keep_indices = set(np.linspace(0, n - 1, n_keep, dtype=int).tolist())
    
    masked = []
    for i, t in enumerate(turns):
        if i in keep_indices:
            masked.append({
                "role": t.role,
                "text": t.text,  # 完全保持
                "original_len": t.char_len,
                "masked_len": t.char_len,
            })
        else:
            # 完全除去だが、存在したことは示す
            placeholder = f"[Turn {i}: {t.role}, {t.char_len} chars removed]"
            masked.append({
                "role": t.role,
                "text": placeholder,
                "original_len": t.char_len,
                "masked_len": len(placeholder),
            })
    return masked


def apply_strategy(turns: list, strategy: str, budget: float) -> MaskedContext:
    """戦略を適用し MaskedContext を返す。"""
    if strategy == "U":
        masked_turns = apply_strategy_U(turns, budget)
    elif strategy == "G":
        masked_turns = apply_strategy_G(turns, budget)
    elif strategy == "S":
        masked_turns = apply_strategy_S(turns, budget)
    else:
        raise ValueError(f"不明な戦略: {strategy}")
    
    total_original = sum(m["original_len"] for m in masked_turns)
    total_masked = sum(m["masked_len"] for m in masked_turns)
    
    # Θ(t) = 1 - masked_len / original_len (忘却率)
    grad_theta = []
    for m in masked_turns:
        if m["original_len"] > 0:
            theta = 1.0 - m["masked_len"] / m["original_len"]
        else:
            theta = 0.0
        grad_theta.append(theta)
    
    return MaskedContext(
        system_prompt="",
        issue_text="",
        turns=masked_turns,
        strategy=strategy,
        budget=budget,
        actual_retention=total_masked / total_original if total_original > 0 else 0,
        grad_theta=grad_theta,
        total_original_chars=total_original,
        total_masked_chars=total_masked,
    )


# --- プロンプト構築 ---
def build_prompt(issue_text: str, masked_ctx: MaskedContext, gold_patch: str) -> str:
    """
    LLM に渡すプロンプトを構築する。
    
    タスク: 操作された context から最終パッチを生成。
    """
    # context を文字列化
    history_lines = []
    for m in masked_ctx.turns:
        role_label = "Agent" if m["role"] == "ai" else "Environment"
        history_lines.append(f"[{role_label}]\n{m['text']}")
    
    history_text = "\n\n---\n\n".join(history_lines)
    
    prompt = f"""あなたはソフトウェアバグ修正の専門家です。
以下の GitHub issue と、そのデバッグ作業の記録を読んで、最終的な修正パッチを生成してください。

## Issue
{issue_text[:3000]}

## デバッグ作業記録
{history_text}

## タスク
上記の作業記録に基づいて、この issue を修正する diff パッチを生成してください。
unified diff 形式で出力してください。
ファイルパスを含めてください。
"""
    return prompt


# --- P (パッチ一致度) の計算 ---
def compute_patch_similarity(generated: str, gold: str) -> dict:
    """
    生成パッチと正解パッチの一致度を計算。
    
    Returns:
        file_match: bool — 正しいファイルを特定したか
        line_overlap: float — 編集行の重複率 (Jaccard)
        exact_match: bool — 文字列完全一致
    """
    # ファイルパスの抽出
    import re
    
    def extract_files(text):
        """diff からファイルパスを抽出"""
        files = set()
        for line in text.split("\n"):
            for prefix in ("--- a/", "+++ b/", "--- ", "+++ "):
                if line.startswith(prefix):
                    path = line[len(prefix):].strip()
                    if path and path != "/dev/null":
                        # パスの正規化
                        path = path.lstrip("a/").lstrip("b/")
                        files.add(path)
        return files
    
    def extract_changed_lines(text):
        """diff から変更行 (+/-) を抽出"""
        lines = set()
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped.startswith("+") and not stripped.startswith("+++"):
                lines.add(stripped[1:].strip())
            elif stripped.startswith("-") and not stripped.startswith("---"):
                lines.add(stripped[1:].strip())
        return lines
    
    gold_files = extract_files(gold)
    gen_files = extract_files(generated)
    
    gold_lines = extract_changed_lines(gold)
    gen_lines = extract_changed_lines(generated)
    
    # ファイル一致
    file_match = bool(gold_files & gen_files) if gold_files else False
    
    # 行の Jaccard 類似度
    if gold_lines and gen_lines:
        intersection = gold_lines & gen_lines
        union = gold_lines | gen_lines
        line_overlap = len(intersection) / len(union)
    else:
        line_overlap = 0.0
    
    # 完全一致
    exact_match = generated.strip() == gold.strip()
    
    return {
        "file_match": file_match,
        "line_overlap": line_overlap,
        "exact_match": exact_match,
        "n_gold_files": len(gold_files),
        "n_gen_files": len(gen_files),
        "n_gold_lines": len(gold_lines),
        "n_gen_lines": len(gen_lines),
    }


# --- ∇_t Θ の計算 ---
def compute_grad_theta(theta_list: list) -> dict:
    """Θ(t) から ∇_t Θ の統計を計算。"""
    if len(theta_list) < 2:
        return {"mean_abs_grad": 0.0, "std_grad": 0.0, "max_abs_grad": 0.0}
    
    arr = np.array(theta_list)
    grad = np.diff(arr)
    
    return {
        "mean_abs_grad": float(np.mean(np.abs(grad))),
        "std_grad": float(np.std(grad)),
        "max_abs_grad": float(np.max(np.abs(grad))),
        "mean_theta": float(np.mean(arr)),
        "std_theta": float(np.std(arr)),
    }


# --- メイン実験ループ ---
def run_experiment(
    n_per_strategy: int = 5,
    budget: float = BUDGET_DEFAULT,
    output_path: Optional[str] = None,
    seed: int = 42,
    dry_run: bool = False,
):
    """
    介入実験を実行。
    
    Args:
        n_per_strategy: 各戦略あたりの trajectory 数
        budget: 情報保持率
        output_path: 結果 JSON の出力先
        seed: 乱数シード
        dry_run: True なら LLM 呼出をスキップ (context 操作のみ検証)
    """
    try:
        from datasets import load_dataset
    except ImportError:
        print("❌ datasets ライブラリが未インストール")
        sys.exit(1)
    
    np.random.seed(seed)
    strategies = ["U", "G", "S"]
    
    print(f"📥 nebius/SWE-agent-trajectories をロード中...")
    ds = load_dataset("nebius/SWE-agent-trajectories", split="train", streaming=True)
    
    # 成功 trajectory のみ収集
    print(f"🔍 成功 trajectory を {n_per_strategy} 件収集中...")
    success_examples = []
    
    for example in ds:
        if len(success_examples) >= n_per_strategy:
            break
        if example.get("target", False):
            traj = example.get("trajectory", [])
            if isinstance(traj, str):
                traj = json.loads(traj)
            if len(traj) >= 6:  # 最低限のターン数
                success_examples.append(example)
                if len(success_examples) % 10 == 0:
                    print(f"  収集: {len(success_examples)}/{n_per_strategy}")
    
    print(f"✅ {len(success_examples)} 件の成功 trajectory を収集")
    
    if len(success_examples) < 3:
        print("❌ 成功 trajectory が不十分 (成功率が低い)")
        return
    
    # 各 trajectory × 各戦略で実験
    all_results = []
    total_calls = 0
    
    for ex_idx, example in enumerate(success_examples):
        traj = example.get("trajectory", [])
        if isinstance(traj, str):
            traj = json.loads(traj)
        
        system_prompt, issue_text, turns = parse_trajectory(traj)
        gold_patch = example.get("patch", "")
        instance_id = example.get("instance_id", f"unknown_{ex_idx}")
        
        if not turns or not gold_patch:
            continue
        
        for strategy in strategies:
            # context 操作
            masked_ctx = apply_strategy(turns, strategy, budget)
            
            # ∇_t Θ 計算
            grad_stats = compute_grad_theta(masked_ctx.grad_theta)
            
            # プロンプト構築
            prompt = build_prompt(issue_text, masked_ctx, gold_patch)
            
            if dry_run:
                # LLM 呼出をスキップ
                generated_patch = "[DRY RUN — no LLM call]"
                p_metrics = {"file_match": False, "line_overlap": 0.0, "exact_match": False}
            else:
                # ochema 経由で Gemini 3.1 Pro を呼出
                # ※ MCP ツールは直接呼べないので、ここでは placeholder
                # 実際の実行時は ochema ask を使う
                generated_patch = call_llm(prompt)
                p_metrics = compute_patch_similarity(generated_patch, gold_patch)
            
            result = {
                "instance_id": instance_id,
                "strategy": strategy,
                "budget": budget,
                "n_turns": len(turns),
                "actual_retention": masked_ctx.actual_retention,
                "total_original_chars": masked_ctx.total_original_chars,
                "total_masked_chars": masked_ctx.total_masked_chars,
                **grad_stats,
                **p_metrics,
                "prompt_len": len(prompt),
            }
            all_results.append(result)
            total_calls += 1
        
        if (ex_idx + 1) % 5 == 0:
            print(f"  進捗: {ex_idx + 1}/{len(success_examples)} trajectories "
                  f"({total_calls} LLM calls)")
    
    print(f"\n✅ 実験完了: {total_calls} calls")
    
    # 結果分析
    analyze_results(all_results)
    
    # 保存
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                "experiment": "intervention_v3",
                "n_per_strategy": n_per_strategy,
                "budget": budget,
                "dry_run": dry_run,
                "total_calls": total_calls,
                "results": all_results,
            }, f, indent=2, ensure_ascii=False)
        print(f"💾 結果を {output_path} に保存")


def call_llm(prompt: str) -> str:
    """
    LLM を呼出してパッチを生成。
    
    この関数は MCP (ochema) から呼ばれる場合は使わない。
    スタンドアロン実行時のみ使用。
    """
    # スタンドアロン実行時: Gemini API を直接呼出
    # MCP 経由時: この関数は呼ばれず、Claude が ochema ask を使う
    raise NotImplementedError(
        "call_llm() はスタンドアロンモードでは未実装。\n"
        "Claude 経由で ochema ask を使って実行してください。"
    )


def analyze_results(results: list):
    """結果を統計分析。"""
    from scipy import stats
    
    if not results:
        print("結果なし")
        return
    
    print(f"\n{'='*60}")
    print(f"介入実験結果 (N={len(results)})")
    print(f"{'='*60}")
    
    strategies = ["U", "G", "S"]
    
    # 戦略別の基本統計
    for s in strategies:
        s_results = [r for r in results if r["strategy"] == s]
        if not s_results:
            continue
        
        file_matches = [r["file_match"] for r in s_results]
        line_overlaps = [r["line_overlap"] for r in s_results]
        retentions = [r["actual_retention"] for r in s_results]
        mean_abs_grads = [r["mean_abs_grad"] for r in s_results]
        
        print(f"\n📊 戦略 {s} (N={len(s_results)}):")
        print(f"  ファイル特定率: {sum(file_matches)}/{len(file_matches)} "
              f"({100*sum(file_matches)/len(file_matches):.1f}%)")
        print(f"  行重複率 (mean): {np.mean(line_overlaps):.4f}")
        print(f"  実際の保持率: {np.mean(retentions):.4f}")
        print(f"  |∇_t Θ| (mean): {np.mean(mean_abs_grads):.4f}")
    
    # 戦略間比較: U vs G
    u_data = [r["line_overlap"] for r in results if r["strategy"] == "U"]
    g_data = [r["line_overlap"] for r in results if r["strategy"] == "G"]
    s_data = [r["line_overlap"] for r in results if r["strategy"] == "S"]
    
    if len(u_data) > 1 and len(g_data) > 1:
        # 対応ありt検定 (同じ trajectory に対する異なる戦略)
        t_ug, p_ug = stats.ttest_rel(u_data, g_data)
        d_ug = (np.mean(g_data) - np.mean(u_data)) / np.sqrt(
            (np.var(u_data) + np.var(g_data)) / 2 + 1e-10)
        print(f"\n🔬 U vs G (v3 核心テスト: ∇_t Θ = 0 vs > 0):")
        print(f"  G - U = {np.mean(g_data) - np.mean(u_data):+.4f}")
        print(f"  paired t = {t_ug:.3f}, p = {p_ug:.4e}")
        print(f"  Cohen's d = {d_ug:.3f}")
        
        sig = "✅ v3 支持" if np.mean(g_data) > np.mean(u_data) and p_ug < 0.05 \
            else "❌ v3 棄却" if np.mean(g_data) < np.mean(u_data) and p_ug < 0.05 \
            else "❓ 有意差なし"
        print(f"  判定: {sig}")
    
    if len(u_data) > 1 and len(s_data) > 1:
        t_us, p_us = stats.ttest_rel(u_data, s_data)
        print(f"\n🔬 U vs S (∇_t Θ = 0 vs δ関数):")
        print(f"  S - U = {np.mean(s_data) - np.mean(u_data):+.4f}")
        print(f"  paired t = {t_us:.3f}, p = {p_us:.4e}")
    
    # 分散の比較 (Levene 検定)
    if len(u_data) > 2 and len(g_data) > 2:
        lev_stat, lev_p = stats.levene(u_data, g_data)
        print(f"\n📊 Var(P) 比較 (Levene 検定):")
        print(f"  Var(P_U) = {np.var(u_data):.4f}")
        print(f"  Var(P_G) = {np.var(g_data):.4f}")
        print(f"  Var(P_S) = {np.var(s_data):.4f}")
        print(f"  Levene U vs G: stat={lev_stat:.3f}, p={lev_p:.4e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="選択的忘却定理 v3 介入実験")
    parser.add_argument("--n_per_strategy", type=int, default=5,
                        help="各戦略あたりの trajectory 数")
    parser.add_argument("--budget", type=float, default=BUDGET_DEFAULT,
                        help="情報保持率 (0-1)")
    parser.add_argument("--output", default=None, help="結果 JSON の出力先")
    parser.add_argument("--seed", type=int, default=42, help="乱数シード")
    parser.add_argument("--dry_run", action="store_true",
                        help="LLM 呼出をスキップして context 操作のみ検証")
    
    args = parser.parse_args()
    run_experiment(args.n_per_strategy, args.budget, args.output, args.seed, args.dry_run)
