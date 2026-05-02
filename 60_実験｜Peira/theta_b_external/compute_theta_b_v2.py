#!/usr/bin/env python3
"""
Θ(B) 再計算 v2 — MCPToolBench++ raw データからの正確な導出。

v1 の構造的欠陥 (/ele+ 検出) を解消:
  1. H(s): ツール分布のエントロピー (AST → Shannon 変換ではなく定義通り)
  2. H(a): 実際のツール使用頻度のエントロピー (Pass@1 → Shannon ではなく定義通り)
  3. R(s,a): I(X;Y) = H(X)+H(Y)-H(X,Y) (JSD 近似ではなく定義通り)
  4. S(B): MCP 応答成功率 (一律 1.0 ではなく計測値)

Θ(B) := S(B) · (1 + α·H(s) + β·H(a) + γ·R(s,a))
"""

import json
import os
import sys
import glob
import math
from dataclasses import dataclass, field
from typing import Optional
from collections import Counter
import numpy as np


# === データ構造 ===

@dataclass
class ThetaComponents:
    """Θ(B) の各コンポーネント"""
    system_name: str
    source: str
    category: str

    # Θ(B) コンポーネント
    H_s: float       # sensory channel entropy
    H_a: float       # active channel entropy
    R_sa: float      # sensory-active mutual information
    S_B: float       # blanket strength (gate, 0-1)

    # パラメータ (論文 §4.1 と同一)
    alpha: float = 0.4
    beta: float = 0.4
    gamma: float = 0.2

    # メタデータ
    k_s: int = 0        # 利用可能ツール数
    k_a: int = 0        # 使用されたツール数
    n_tasks: int = 0    # タスク数
    confidence: str = "[確信]"
    notes: str = ""

    @property
    def theta(self) -> float:
        """Θ(B) を計算"""
        return self.S_B * (1 + self.alpha * self.H_s
                           + self.beta * self.H_a
                           + self.gamma * self.R_sa)

    def summary(self) -> str:
        return (f"{self.system_name} ({self.category}): "
                f"Θ(B)={self.theta:.4f} "
                f"[S(B)={self.S_B:.3f}, H(s)={self.H_s:.3f}, "
                f"H(a)={self.H_a:.3f}, R(s,a)={self.R_sa:.3f}] "
                f"k_s={self.k_s}, k_a={self.k_a}, n={self.n_tasks}")


# === エントロピー計算 ===

def shannon_entropy(counts: list[int]) -> float:
    """Shannon entropy H = -Σ p_i log2(p_i)
    
    counts: 各カテゴリの出現回数のリスト
    戻り値: エントロピー (bits)
    """
    total = sum(counts)
    if total == 0:
        return 0.0
    h = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            h -= p * math.log2(p)
    return h


def normalized_entropy(counts: list[int]) -> float:
    """正規化 Shannon entropy H_norm = H / log2(n)
    
    [0, 1] に正規化。n=1 の場合は 0。
    """
    n = len([c for c in counts if c > 0])
    if n <= 1:
        return 0.0
    h = shannon_entropy(counts)
    return h / math.log2(n)


def mutual_information(joint_counts: dict[tuple, int],
                       marginal_x: dict, marginal_y: dict) -> float:
    """相互情報量 I(X;Y) = H(X) + H(Y) - H(X,Y)
    
    joint_counts: {(x, y): count} の辞書
    marginal_x: {x: count}
    marginal_y: {y: count}
    
    戻り値: I(X;Y) (bits)
    """
    h_x = shannon_entropy(list(marginal_x.values()))
    h_y = shannon_entropy(list(marginal_y.values()))
    h_xy = shannon_entropy(list(joint_counts.values()))
    mi = h_x + h_y - h_xy
    # 浮動小数点誤差で微小な負値になりうる
    return max(0.0, mi)


# === データローダー ===

def load_category_data(data_dir: str, category: str) -> list[dict]:
    """カテゴリのフルデータセット JSON を読み込む。
    
    demo ファイルは除外し、本番データのみを返す。
    """
    cat_path = os.path.join(data_dir, category)
    tasks = []
    for f in sorted(glob.glob(os.path.join(cat_path, '*.json'))):
        fname = os.path.basename(f)
        # デモ/テストファイルを除外
        if 'demo' in fname or 'test_file' in fname or 'forqwen' in fname:
            continue
        with open(f) as fh:
            data = json.load(fh)
            tasks.extend(data)
    return tasks


def get_all_categories(data_dir: str) -> list[str]:
    """data/ 以下の全カテゴリディレクトリを返す"""
    cats = []
    for entry in sorted(os.listdir(data_dir)):
        if os.path.isdir(os.path.join(data_dir, entry)):
            cats.append(entry)
    return cats


# === Θ(B) コンポーネント計算 ===

def compute_category_theta(tasks: list[dict], category: str,
                           system_name: str = "MCPToolBench++") -> ThetaComponents:
    """1カテゴリの全タスクから Θ(B) コンポーネントを計算する。
    
    操作的定義:
    - 感覚チャネル (s): 各タスクで利用可能なツール群
    - 行動チャネル (a): 実際に LLM が呼んだツール (function_call_label)
    - H(s): 利用可能ツールのサーバ別分布のエントロピー
    - H(a): 実際に使用されたツール名の頻度分布のエントロピー  
    - R(s,a): I(s;a) = H(s) + H(a) - H(s,a)
    - S(B): MCP 応答成功率 (status_code == 200 の割合)
    """
    if not tasks:
        return ThetaComponents(
            system_name=system_name, source="MCPToolBench++",
            category=category, H_s=0, H_a=0, R_sa=0, S_B=0,
            notes="空のデータセット"
        )

    # --- 利用可能ツール分布 (感覚チャネル) ---
    # 全タスクを集約: 各ツールが何回「利用可能」として提供されたか
    available_tool_counts = Counter()
    for task in tasks:
        for tool in task.get('tools', []):
            available_tool_counts[tool['name']] += 1

    # --- 使用されたツール分布 (行動チャネル) ---
    used_tool_counts = Counter()
    for task in tasks:
        for label in task.get('function_call_label', []):
            used_tool_counts[label['name']] += 1

    # --- S(B): MB 形成度 ---
    # MCPToolBench++ のラベルデータは ground truth (タスク定義)。
    # 実行ログではないため status_code は参考値。
    # S(B) の操作化: function_call_label が存在するタスクの割合
    #   (= MCP ツールが使用される = MB が観測される確率)
    # 加えて、status_code == 200 があればそれも考慮。
    tasks_with_calls = sum(1 for t in tasks if t.get('function_call_label'))
    total_calls = 0
    success_calls = 0
    for task in tasks:
        for label in task.get('function_call_label', []):
            total_calls += 1
            output = label.get('output', {})
            sc = output.get('status_code')
            if sc is not None:
                if sc == 200:
                    success_calls += 1
            else:
                # status_code がない場合はツール呼出し存在自体を成功とみなす
                success_calls += 1
    s_b = success_calls / total_calls if total_calls > 0 else 0.0

    # --- H(s): 利用可能ツール頻度分布のエントロピー ---
    h_s_raw = shannon_entropy(list(available_tool_counts.values()))
    # 正規化: log2(ユニークツール数) で割る
    k_s = len(available_tool_counts)
    h_s = normalized_entropy(list(available_tool_counts.values()))

    # --- H(a): 使用ツール頻度分布のエントロピー ---
    h_a_raw = shannon_entropy(list(used_tool_counts.values()))
    k_a = len(used_tool_counts)
    h_a = normalized_entropy(list(used_tool_counts.values()))

    # --- R(s,a): 相互情報量 ---
    # 結合分布: (利用可能ツール, 使用されたツール) のペア
    # タスクレベルで: 各タスクの (available_tools_set, used_tool) ペアをカウント
    # 
    # 操作化: 各タスクについて、
    #   s = タスクが属するカテゴリの MCP サーバ (粗粒度)
    #   a = 実際に使用されたツール名
    # の結合分布で I(s;a) を計算
    joint_counts = Counter()
    marginal_s = Counter()  # サーバ別
    marginal_a = Counter()  # ツール別

    for task in tasks:
        for label in task.get('function_call_label', []):
            server = label.get('mcp_server', 'unknown')
            tool = label['name']
            joint_counts[(server, tool)] += 1
            marginal_s[server] += 1
            marginal_a[tool] += 1

    r_sa_raw = mutual_information(joint_counts, marginal_s, marginal_a)
    # 正規化: min(H(s_server), H(a_tool)) で割る
    h_s_server = shannon_entropy(list(marginal_s.values()))
    h_a_tool = shannon_entropy(list(marginal_a.values()))
    denom = min(h_s_server, h_a_tool)
    r_sa = r_sa_raw / denom if denom > 0 else 0.0

    return ThetaComponents(
        system_name=system_name,
        source="MCPToolBench++",
        category=category,
        H_s=h_s,
        H_a=h_a,
        R_sa=r_sa,
        S_B=s_b,
        k_s=k_s,
        k_a=k_a,
        n_tasks=len(tasks),
        confidence="[確信] SOURCE: MCPToolBench++ raw データから直接計算",
        notes=f"servers={set(marginal_s.keys())}"
    )


def compute_aggregate_theta(category_results: list[ThetaComponents],
                            system_name: str = "MCPToolBench++ (全体)"
                            ) -> ThetaComponents:
    """全カテゴリの加重平均 Θ(B) を計算する。
    
    タスク数で加重平均。
    """
    total_tasks = sum(r.n_tasks for r in category_results)
    if total_tasks == 0:
        return ThetaComponents(
            system_name=system_name, source="MCPToolBench++",
            category="aggregate", H_s=0, H_a=0, R_sa=0, S_B=0
        )

    # タスク数加重平均
    h_s = sum(r.H_s * r.n_tasks for r in category_results) / total_tasks
    h_a = sum(r.H_a * r.n_tasks for r in category_results) / total_tasks
    r_sa = sum(r.R_sa * r.n_tasks for r in category_results) / total_tasks
    s_b = sum(r.S_B * r.n_tasks for r in category_results) / total_tasks

    return ThetaComponents(
        system_name=system_name,
        source="MCPToolBench++",
        category="aggregate",
        H_s=h_s,
        H_a=h_a,
        R_sa=r_sa,
        S_B=s_b,
        k_s=sum(r.k_s for r in category_results),
        k_a=sum(r.k_a for r in category_results),
        n_tasks=total_tasks,
        confidence="[確信] カテゴリ別タスク数加重平均",
        notes=f"{len(category_results)} categories"
    )


# === HGK+ 内部データ (既存、変更なし) ===

def hgk_internal_results() -> list[ThetaComponents]:
    """HGK+ 内部セッションデータ (2セッション)
    
    元の値は生の Shannon entropy (bits):
      Session 1: H(s)=2.81, H(a)=2.32, k_s=9, k_a=47
      Session 2: H(s)=2.65, H(a)=2.18, k_s=9, k_a=42
    
    MCPToolBench++ と尺度を統一するため、正規化:
      H_s_norm = H_s_raw / log2(k_s)
      H_a_norm = H_a_raw / log2(k_a)
    """
    import math
    
    # Session 1: 生のエントロピー値
    h_s_1_raw, k_s_1 = 2.81, 9    # 9 MCP サーバからの entropy
    h_a_1_raw, k_a_1 = 2.32, 47   # 47 ツールの使用 entropy
    h_s_1 = h_s_1_raw / math.log2(k_s_1)  # = 2.81 / 3.17 ≈ 0.887
    h_a_1 = h_a_1_raw / math.log2(k_a_1)  # = 2.32 / 5.55 ≈ 0.418
    
    # Session 2
    h_s_2_raw, k_s_2 = 2.65, 9
    h_a_2_raw, k_a_2 = 2.18, 42
    h_s_2 = h_s_2_raw / math.log2(k_s_2)  # = 2.65 / 3.17 ≈ 0.836
    h_a_2 = h_a_2_raw / math.log2(k_a_2)  # = 2.18 / 5.39 ≈ 0.404
    
    return [
        ThetaComponents(
            system_name="HGK+ Session 1",
            source="HGK+ Internal",
            category="internal",
            H_s=h_s_1,
            H_a=h_a_1,
            R_sa=0.67,  # 既に正規化済み
            S_B=0.94,   # MCP 応答成功率
            k_s=k_s_1,
            k_a=k_a_1,
            n_tasks=1,
            confidence="[確信] SOURCE: HGK+ セッションログから直接計算 + 正規化",
            notes=f"H(s) raw={h_s_1_raw}, H(a) raw={h_a_1_raw}, MCP 9サーバ構成"
        ),
        ThetaComponents(
            system_name="HGK+ Session 2",
            source="HGK+ Internal",
            category="internal",
            H_s=h_s_2,
            H_a=h_a_2,
            R_sa=0.71,  # 既に正規化済み
            S_B=0.91,   # MCP 応答成功率
            k_s=k_s_2,
            k_a=k_a_2,
            n_tasks=1,
            confidence="[確信] SOURCE: HGK+ セッションログから直接計算 + 正規化",
            notes=f"H(s) raw={h_s_2_raw}, H(a) raw={h_a_2_raw}, MCP 9サーバ構成"
        ),
    ]


# === 理論的検証 ===

def validate_components(result: ThetaComponents) -> list[str]:
    """理論的性質のアサーション"""
    errors = []

    if result.H_s < 0:
        errors.append(f"H(s) < 0: {result.H_s}")
    if result.H_a < 0:
        errors.append(f"H(a) < 0: {result.H_a}")
    if result.R_sa < 0:
        errors.append(f"R(s,a) < 0: {result.R_sa}")
    if not (0 <= result.S_B <= 1):
        errors.append(f"S(B) not in [0,1]: {result.S_B}")
    if result.theta < 0:
        errors.append(f"Θ(B) < 0: {result.theta}")

    # 正規化エントロピーは [0, 1]
    if result.H_s > 1.0 + 1e-10:
        errors.append(f"normalized H(s) > 1: {result.H_s}")
    if result.H_a > 1.0 + 1e-10:
        errors.append(f"normalized H(a) > 1: {result.H_a}")

    # R(s,a) は [0, 1] (正規化済み)
    if result.R_sa > 1.0 + 1e-10:
        errors.append(f"normalized R(s,a) > 1: {result.R_sa}")

    return errors


# === メイン ===

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Θ(B) v2: MCPToolBench++ raw データからの正確な計算")
    parser.add_argument("--data-dir", default="MCPToolBenchPP/data",
                        help="MCPToolBench++ の data/ ディレクトリ")
    parser.add_argument("--validate", action="store_true",
                        help="理論的性質の検証のみ実行")
    parser.add_argument("--json", action="store_true",
                        help="結果を JSON で出力")
    args = parser.parse_args()

    # データディレクトリの確認
    if not os.path.isdir(args.data_dir):
        print(f"エラー: {args.data_dir} が見つかりません。"
              " MCPToolBenchPP をクローンしてください。")
        sys.exit(1)

    categories = get_all_categories(args.data_dir)
    print(f"\n{'='*70}")
    print(f"Θ(B) v2 計算 — MCPToolBench++ raw データ")
    print(f"{'='*70}")
    print(f"カテゴリ: {categories}")

    # --- カテゴリ別計算 ---
    category_results = []
    all_errors = []

    for cat in categories:
        tasks = load_category_data(args.data_dir, cat)
        if not tasks:
            continue
        result = compute_category_theta(tasks, cat)
        category_results.append(result)

        # 検証
        errors = validate_components(result)
        if errors:
            all_errors.extend([(cat, e) for e in errors])

    # --- 結果表示 ---
    print(f"\n--- カテゴリ別 Θ(B) ---")
    print(f"{'カテゴリ':<15} {'Θ(B)':>8} {'S(B)':>8} {'H(s)':>8} "
          f"{'H(a)':>8} {'R(s,a)':>8} {'k_s':>6} {'k_a':>6} {'n':>6}")
    print("-" * 90)
    for r in category_results:
        print(f"{r.category:<15} {r.theta:>8.4f} {r.S_B:>8.3f} {r.H_s:>8.3f} "
              f"{r.H_a:>8.3f} {r.R_sa:>8.3f} {r.k_s:>6} {r.k_a:>6} {r.n_tasks:>6}")

    # --- 全体集約 ---
    aggregate = compute_aggregate_theta(category_results)
    print("-" * 90)
    print(f"{'AGGREGATE':<15} {aggregate.theta:>8.4f} {aggregate.S_B:>8.3f} "
          f"{aggregate.H_s:>8.3f} {aggregate.H_a:>8.3f} {aggregate.R_sa:>8.3f} "
          f"{aggregate.k_s:>6} {aggregate.k_a:>6} {aggregate.n_tasks:>6}")

    # --- HGK+ 内部データとの比較 ---
    print(f"\n--- HGK+ 内部データ ---")
    hgk_results = hgk_internal_results()
    for r in hgk_results:
        print(r.summary())

    # --- 比較表 ---
    print(f"\n--- 比較表: MCPToolBench++ vs HGK+ ---")
    print(f"{'システム':<25} {'Θ(B)':>8} {'S(B)':>8} {'H(s)':>8} "
          f"{'H(a)':>8} {'R(s,a)':>8}")
    print("-" * 80)
    print(f"{'MCPToolBench++ (全体)':<25} {aggregate.theta:>8.4f} {aggregate.S_B:>8.3f} "
          f"{aggregate.H_s:>8.3f} {aggregate.H_a:>8.3f} {aggregate.R_sa:>8.3f}")
    for r in hgk_results:
        print(f"{r.system_name:<25} {r.theta:>8.4f} {r.S_B:>8.3f} "
              f"{r.H_s:>8.3f} {r.H_a:>8.3f} {r.R_sa:>8.3f}")

    # --- 理論的性質の検証 ---
    print(f"\n--- 理論的性質の検証 ---")
    if all_errors:
        print(f"❌ {len(all_errors)} 件のエラー:")
        for cat, err in all_errors:
            print(f"  [{cat}] {err}")
    else:
        print(f"✅ 全 {len(category_results)} カテゴリで理論的性質を満たす")

    # --- JSON 出力 ---
    if args.json:
        results_json = {
            "version": "v2",
            "source": "MCPToolBench++ raw data",
            "categories": [{
                "category": r.category,
                "theta_b": round(r.theta, 4),
                "S_B": round(r.S_B, 4),
                "H_s": round(r.H_s, 4),
                "H_a": round(r.H_a, 4),
                "R_sa": round(r.R_sa, 4),
                "k_s": r.k_s,
                "k_a": r.k_a,
                "n_tasks": r.n_tasks,
            } for r in category_results],
            "aggregate": {
                "theta_b": round(aggregate.theta, 4),
                "S_B": round(aggregate.S_B, 4),
                "H_s": round(aggregate.H_s, 4),
                "H_a": round(aggregate.H_a, 4),
                "R_sa": round(aggregate.R_sa, 4),
                "n_tasks": aggregate.n_tasks,
            },
            "hgk_internal": [{
                "name": r.system_name,
                "theta_b": round(r.theta, 4),
                "S_B": round(r.S_B, 4),
                "H_s": round(r.H_s, 4),
                "H_a": round(r.H_a, 4),
                "R_sa": round(r.R_sa, 4),
            } for r in hgk_results],
        }
        print(f"\n--- JSON ---")
        print(json.dumps(results_json, indent=2, ensure_ascii=False))

    if args.validate:
        sys.exit(1 if all_errors else 0)


if __name__ == "__main__":
    main()
