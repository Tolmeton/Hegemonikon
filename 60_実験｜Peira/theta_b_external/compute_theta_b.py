#!/usr/bin/env python3
"""
外部データソースから Θ(B) (MB thickness) を計算する統合パイプライン。

Θ(B) := S(B) · (1 + α·H(s) + β·H(a) + γ·R(s,a))

データソース:
  A. MCPToolBench++ (Fan et al., 2025) — 41 MCP カテゴリ × 5 LLM
  B. SPaRK (Bo et al., 2025) — 8ツール × 4条件 (Base/SFT/PPO/SPaRK)
  C. 独自 MCP trajectory — Cortex 経由 (別スクリプト)
  D. Seal-Tools (Wu et al., 2024) — 大規模ツールデータ
  E. HGK+ (内部) — 既存2セッション
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional
import json


# --- Θ(B) の定義 ---

@dataclass
class ThetaComponents:
    """Θ(B) の各コンポーネント"""
    # 基本データ
    system_name: str
    source: str  # データソース名
    
    # Θ(B) コンポーネント
    H_s: float  # sensory entropy (Shannon)
    H_a: float  # active entropy (Shannon)
    R_sa: float  # 相互情報量 (multivariate MI)
    S_B: float  # blanket strength (MB 存在ゲート, 0-1)
    
    # パラメータ
    alpha: float = 0.4  # sensory weight (α = β)
    beta: float = 0.4   # active weight
    gamma: float = 0.2  # redundancy weight (γ = 1 - 2α)
    
    # メタデータ
    k_s: int = 0  # sensory channel 数
    k_a: int = 0  # active channel 数
    confidence: str = "[推定]"  # 確信度ラベル
    notes: str = ""
    
    @property
    def theta(self) -> float:
        """Θ(B) を計算"""
        return self.S_B * (1 + self.alpha * self.H_s 
                          + self.beta * self.H_a 
                          + self.gamma * self.R_sa)
    
    @property
    def theta_max(self) -> float:
        """最大到達可能 Θ(B) (一様分布仮定)"""
        H_s_max = np.log2(self.k_s) if self.k_s > 0 else 0
        H_a_max = np.log2(self.k_a) if self.k_a > 0 else 0
        R_max = min(H_s_max, H_a_max)
        return self.S_B * (1 + self.alpha * H_s_max 
                          + self.beta * H_a_max 
                          + self.gamma * R_max)


def shannon_entropy(probs: list[float]) -> float:
    """Shannon entropy を計算 (bits)"""
    probs = np.array(probs)
    probs = probs[probs > 0]  # log(0) を回避
    return -np.sum(probs * np.log2(probs))


def uniform_entropy(k: int) -> float:
    """k チャネルの一様分布 entropy"""
    return np.log2(k) if k > 0 else 0.0


# --- データソース A: MCPToolBench++ ---

def mcptoolbench_data() -> list[ThetaComponents]:
    """
    MCPToolBench++ (Fan et al., 2025) Table 2 の正確なデータから Θ(B) を計算。
    
    [SOURCE: ar5iv ブラウザ読み取り 2026-03-21]
    6 カテゴリ × 5 LLM の AST/Pass@1 スコア
    
    計算方法:
    H(s): 6 カテゴリの AST スコアを正規化 → Shannon entropy (sensory channel diversity)
           AST = ツール選択の正確さ → 各カテゴリをどれだけ均等に「知覚」しているか
    H(a): 6 カテゴリの Pass@1 スコアを正規化 → Shannon entropy (action diversity)
           Pass@1 = 実行成功率 → 各カテゴリでどれだけ均等に「行動」できるか
    R(s,a): AST と Pass@1 の相関 → 知覚-行動の結合度
    S(B): 全カテゴリで少なくとも一部成功 → S(B) = 1.0
    """
    results = []
    
    # [SOURCE: MCPToolBench++ Table 2, ar5iv 2026-03-21 ブラウザ確認]
    # カテゴリ: Browser, FileSystem, Search, Map, Pay, Finance
    categories = ["Browser", "FileSystem", "Search", "Map", "Pay", "Finance"]
    k_s = len(categories)  # 6 sensory channels (論文に報告されたカテゴリ)
    # 注意: 論文は 41 MCP カテゴリと述べるが、Table 2 は主要6カテゴリのみ掲載
    # 残り 35 カテゴリは Figure 3/4 の棒グラフ内に含まれる
    
    table2 = {
        "Claude-3.7-Sonnet": {
            "AST":    [0.6503, 0.8415, 0.7280, 0.5820, 0.7058, 0.7400],
            "Pass@1": [0.1840, 0.8183, 0.6200, 0.2748, 0.5574, 0.2311],
        },
        "GPT-4o": {
            "AST":    [0.6524, 0.8863, 0.5200, 0.6120, 0.7077, 0.7200],
            "Pass@1": [0.2182, 0.8232, 0.4720, 0.3616, 0.5742, 0.2889],
        },
        "Kimi-K2-Instruct": {
            "AST":    [0.8182, 0.9062, 0.7320, 0.6088, 0.8071, 0.7156],
            "Pass@1": [0.2524, 0.8772, 0.3680, 0.2008, 0.6761, 0.2378],
        },
        "Qwen3-Coder": {
            "AST":    [0.8866, 0.9080, 0.7180, 0.7830, 0.7240, 0.7320],
            "Pass@1": [0.2925, 0.8680, 0.5227, 0.3054, 0.5440, 0.2860],
        },
        "Qwen2.5-Max": {
            "AST":    [0.7262, 0.9419, 0.6280, 0.7372, 0.6684, 0.7511],
            "Pass@1": [0.2749, 0.8871, 0.4600, 0.2272, 0.5277, 0.2556],
        },
    }
    
    for name, scores in table2.items():
        ast = np.array(scores["AST"])
        pass1 = np.array(scores["Pass@1"])
        
        # H(s): AST スコアを正規化して Shannon entropy
        # AST は各カテゴリの「知覚精度」を表す
        ast_norm = ast / ast.sum()
        H_s = shannon_entropy(ast_norm.tolist())
        
        # H(a): Pass@1 スコアを正規化して Shannon entropy
        # Pass@1 は各カテゴリの「行動成功度」を表す
        pass1_norm = pass1 / pass1.sum()
        H_a = shannon_entropy(pass1_norm.tolist())
        
        # R(s,a): AST と Pass@1 の分布間の相互情報量を近似
        # 正規化した joint distribution からの MI 推定
        # 簡易版: 1 - Jensen-Shannon divergence として近似
        m = (ast_norm + pass1_norm) / 2
        jsd = 0.5 * (shannon_entropy(m.tolist()) - 
                     0.5 * shannon_entropy(ast_norm.tolist()) - 
                     0.5 * shannon_entropy(pass1_norm.tolist()))
        # R ∝ (1 - JSD) × min(H_s, H_a)
        # JSD ≈ 0 なら分布が同じ → 高い結合
        R_sa = (1 - jsd) * min(H_s, H_a) * 0.5
        
        # S(B) = 1.0 (全カテゴリで成功あり → MB 存在)
        S_B = 1.0
        
        # メタデータ
        avg_ast = ast.mean()
        avg_pass1 = pass1.mean()
        
        results.append(ThetaComponents(
            system_name=name,
            source="MCPToolBench++ (Fan et al., 2025)",
            H_s=H_s, H_a=H_a, R_sa=R_sa, S_B=S_B,
            k_s=k_s, k_a=k_s,  # 同じ6カテゴリで sensory も active も計測
            confidence="[確信] Table 2 SOURCE データから直接計算",
            notes=f"avg_AST={avg_ast:.3f}, avg_Pass@1={avg_pass1:.3f}",
        ))
    
    return results


# --- データソース B: SPaRK ---

def spark_data() -> list[ThetaComponents]:
    """
    SPaRK (Bo et al., 2025) の tool selection entropy から Θ(B) を計算。
    
    データ源: Fig. 5 + §5.2
    8 ツール + CoT = 9 action 種類
    4 条件: Base / SFT / PPO-no-diversity / SPaRK
    """
    results = []
    
    k_tools = 9   # active channels (8 ツール + CoT)
    k_sensory = 14  # MMLU-Pro の 14 カテゴリ = sensory channels
    
    # SPaRK 4条件のデータ
    # [TAINT: Fig. 5 の目視推定。正確な数値取得にはブラウザ読み取りが必要]
    conditions = {
        "LLaMA-3.1-8B (Base)": {
            "accuracy": 0.224,
            "tool_entropy_estimate": 0.8,
            "h_s_estimate": 2.5,
        },
        "LLaMA-3.1-8B (SFT)": {
            "accuracy": 0.262,
            "tool_entropy_estimate": 1.2,
            "h_s_estimate": 2.8,
        },
        "LLaMA-3.1-8B (PPO)": {
            "accuracy": 0.330,
            "tool_entropy_estimate": 1.8,
            "h_s_estimate": 3.0,
        },
        "LLaMA-3.1-8B (SPaRK)": {
            "accuracy": 0.408,
            "tool_entropy_estimate": 2.8,
            "h_s_estimate": 3.2,
        },
    }
    
    for name, data in conditions.items():
        H_a = data["tool_entropy_estimate"]
        H_s = data["h_s_estimate"]
        R_sa = min(H_s, H_a) * 0.25
        S_B = 1.0 if data["accuracy"] > 0 else 0.0
        
        results.append(ThetaComponents(
            system_name=name,
            source="SPaRK (Bo et al., 2025)",
            H_s=H_s, H_a=H_a, R_sa=R_sa, S_B=S_B,
            k_s=k_sensory, k_a=k_tools,
            confidence="[推定] Fig.5 からの目視推定",
            notes=f"accuracy={data['accuracy']}",
        ))
    
    return results


# --- データソース E: HGK+ (内部データ) ---

def hgk_data() -> list[ThetaComponents]:
    """
    HGK+ の既存セッションデータから Θ(B) を計算。
    データ源: 論文 §5 の Figure 4/5
    """
    results = []
    
    # Session 1: 技術セッション
    results.append(ThetaComponents(
        system_name="HGK+ Session 1 (Technical)",
        source="HGK+ (本論文 §5)",
        H_s=3.17, H_a=2.85, R_sa=1.42, S_B=0.92,
        k_s=9, k_a=45,
        confidence="[確信] 直接計算",
        notes="9 MCP servers, 45+ tools",
    ))
    
    # Session 2: 研究セッション
    results.append(ThetaComponents(
        system_name="HGK+ Session 2 (Research)",
        source="HGK+ (本論文 §5)",
        H_s=2.89, H_a=2.54, R_sa=1.18, S_B=0.88,
        k_s=9, k_a=38,
        confidence="[確信] 直接計算",
        notes="9 MCP servers, 38 tools used",
    ))
    
    return results


# --- 参照点 ---

def biological_reference() -> ThetaComponents:
    """Human (論文 §4.3 の参照値)"""
    return ThetaComponents(
        system_name="Human (reference)",
        source="Literature estimates",
        H_s=4.7, H_a=4.2, R_sa=3.8, S_B=1.0,
        k_s=26, k_a=18,
        confidence="[推定] 文献からの推定",
        notes="5 major senses + sub-modalities",
    )


def vanilla_llm_reference() -> ThetaComponents:
    """Vanilla LLM (ツールなし)"""
    return ThetaComponents(
        system_name="Vanilla LLM (no tools)",
        source="Theoretical minimum",
        H_s=0.0, H_a=0.0, R_sa=0.0, S_B=0.72,
        k_s=1, k_a=1,
        confidence="[確信] 定義上",
        notes="Text-in/text-out only",
    )


# --- 統合 & 出力 ---

def compute_all():
    """全データソースを統合して Θ(B) を計算"""
    all_data = []
    
    # 参照点
    all_data.append(biological_reference())
    all_data.append(vanilla_llm_reference())
    
    # 内部データ
    all_data.extend(hgk_data())
    
    # 外部データ
    all_data.extend(mcptoolbench_data())
    all_data.extend(spark_data())
    
    # 出力
    print("=" * 100)
    print("Θ(B) 計算結果 — 全データソース統合")
    print("=" * 100)
    print(f"{'System':<35} {'Source':<30} {'H(s)':<6} {'H(a)':<6} {'R(s,a)':<7} {'S(B)':<5} {'Θ(B)':<7} {'Conf.'}")
    print("-" * 100)
    
    for d in sorted(all_data, key=lambda x: x.theta, reverse=True):
        print(f"{d.system_name:<35} {d.source[:28]:<30} {d.H_s:<6.2f} {d.H_a:<6.2f} {d.R_sa:<7.2f} {d.S_B:<5.2f} {d.theta:<7.3f} {d.confidence[:30]}")
    
    print(f"\n全データポイント数: n = {len(all_data)}")
    print(f"  参照点: 2 (Human, Vanilla LLM)")
    print(f"  HGK+: 2")
    print(f"  MCPToolBench++: {len(mcptoolbench_data())}")
    print(f"  SPaRK: {len(spark_data())}")
    
    # JSON 出力
    output = []
    for d in sorted(all_data, key=lambda x: x.theta, reverse=True):
        output.append({
            "system": d.system_name,
            "source": d.source,
            "H_s": round(d.H_s, 3),
            "H_a": round(d.H_a, 3),
            "R_sa": round(d.R_sa, 3),
            "S_B": round(d.S_B, 3),
            "theta": round(d.theta, 3),
            "k_s": d.k_s,
            "k_a": d.k_a,
            "confidence": d.confidence,
            "notes": d.notes,
        })
    
    with open("/tmp/theta_b_results.json", "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n結果を /tmp/theta_b_results.json に保存")
    
    return all_data


if __name__ == "__main__":
    compute_all()
