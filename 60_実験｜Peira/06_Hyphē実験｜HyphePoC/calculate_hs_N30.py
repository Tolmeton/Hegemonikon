#!/usr/bin/env python3
"""H(s) メトリクス計算と 3条件分類スクリプト。

N=30 セッション実データから MCP tool usage を抽出し、H(s) (entropy) を計算。
セッションを VANILLA, PARTIAL, HGK+ に分類し、§5.2 のデータテーブルを出力する。
"""

import os
import sys
import re
import math
import random
from pathlib import Path
from collections import defaultdict

HGK = os.path.expanduser("~/Sync/oikos/01_ヘゲモニコン｜Hegemonikon")
sys.path.insert(0, os.path.join(HGK, "20_機構｜Mekhane/_src｜ソースコード"))
sys.path.insert(0, os.path.join(HGK, "60_実験｜Peira/06_Hyphē実験｜HyphePoC"))

from hyphe_chunker import Step

# カスタムパーサー (run_ensemble_e2e_N30.py と同様)
_STEP_PATTERN = re.compile(r"^## 🤖 (?:Claude|Assistant|Gemini Code Assist)", re.MULTILINE)

def parse_session_custom(text: str) -> list[Step]:
    splits = _STEP_PATTERN.split(text)
    steps = []
    for i, block in enumerate(splits[1:], start=0):
        block = re.sub(r"^\s*\([^)]*\)\s*\n*", "", block).strip()
        if not block:
            continue
        tools = re.findall(r"🔧 `([^`]+)`", block)
        steps.append(Step(index=i, text=block, tools=tools))
    return steps

def load_real_sessions(n_sessions: int) -> list[list[Step]]:
    sessions_dir = Path(HGK) / "30_記憶｜Mneme/01_記録｜Records/b_対話｜sessions"
    all_files = sorted(list(sessions_dir.rglob("*.md")))
    
    random.seed(42)  # 再現性のため run_ensemble_e2e_N30.py と同じseed
    random.shuffle(all_files)
    
    valid_sessions = []
    for path in all_files:
        try:
            text = path.read_text(encoding="utf-8")
            steps = parse_session_custom(text)
            if len(steps) >= 8:
                valid_sessions.append(steps)
            if len(valid_sessions) >= n_sessions:
                break
        except Exception as e:
            pass
            
    return valid_sessions

# 対象 MCP サーバー一覧 (§5.2 に記載のもの)
KNOWN_MCP_SERVERS = {
    "hermeneus", "periskope", "mneme", "ochema", 
    "sympatheia", "sekisho", "digestor", "jules", "typos", "phantazein"
}

def extract_mcp_servers(tools: list[str]) -> list[str]:
    """ツール名から MCP サーバー名を抽出。"""
    servers = []
    for tool in tools:
        if tool.startswith("mcp_"):
            parts = tool.split("_")
            if len(parts) >= 2:
                server = parts[1]
                if server in KNOWN_MCP_SERVERS:
                    servers.append(server)
        elif tool.startswith("periskope_"):
            servers.append("periskope")
        elif tool.startswith("sympatheia_"):
            servers.append("sympatheia")
        elif tool.startswith("sekisho_"):
            servers.append("sekisho")
        # 他にもプレフィックスがあれば追加可能
    return servers

def compute_hs(server_counts: dict) -> float:
    """H(s) = Shannon entropy を計算。"""
    total = sum(server_counts.values())
    if total == 0:
        return 0.0
    
    hs = 0.0
    for count in server_counts.values():
        p = count / total
        hs -= p * math.log2(p)
    return hs

def main():
    N_TARGET = 30
    sessions = load_real_sessions(N_TARGET)
    
    # 統計用リスト
    vanilla_stats = []
    partial_stats = []
    hgk_stats = []
    
    for i, steps in enumerate(sessions):
        # セッションレベルの集計
        session_servers = defaultdict(int)
        total_mcp_calls = 0
        
        for step in steps:
            servers = extract_mcp_servers(step.tools)
            for server in servers:
                session_servers[server] += 1
                total_mcp_calls += 1
                
        # n_distinct_servers = len(session_servers)
        n_distinct_servers = len(session_servers)
        hs = compute_hs(session_servers)
        
        stat = {
            "hs": hs,
            "calls": total_mcp_calls,
            "servers": n_distinct_servers,
        }
        
        # 3条件分類
        if total_mcp_calls == 0:
            vanilla_stats.append(stat)
        elif total_mcp_calls <= 4:
            partial_stats.append(stat)
        else:
            hgk_stats.append(stat)
            
    def summarize(stats: list[dict], name: str):
        n = len(stats)
        if n == 0:
            return f"| {name} | {n} | - | - | - | - |"
        
        mean_hs = sum(s["hs"] for s in stats) / n
        std_hs = math.sqrt(sum((s["hs"] - mean_hs)**2 for s in stats) / n) if n > 1 else 0.0
        mean_calls = sum(s["calls"] for s in stats) / n
        mean_servers = sum(s["servers"] for s in stats) / n
        
        return f"| {name} | {n} | {mean_hs:.3f} | {std_hs:.3f} | {mean_calls:.1f} | {mean_servers:.1f} |"
        
    print("### 5.2 H(s) Measurement Results (N=30)")
    print("| Condition | n | H(s) mean | H(s) std | Calls mean | Servers mean |")
    print("|:----------|---:|----------:|---------:|-----------:|-------------:|")
    print(summarize(vanilla_stats, "VANILLA"))
    print(summarize(partial_stats, "PARTIAL"))
    print(summarize(hgk_stats, "HGK+"))

if __name__ == "__main__":
    main()
