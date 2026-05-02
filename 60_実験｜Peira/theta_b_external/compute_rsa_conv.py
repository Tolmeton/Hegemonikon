#!/usr/bin/env python3
"""
R(s,a) 全認知活動版 — conv/ セッションログから CCL 動詞シーケンスを抽出し計算。

Phase 2: tape のみではなく、セッション対話ログ全体から認知活動を抽出する。
- CCL 動詞 (/noe, /ele, /boot, etc.) は Value 軸 (I/A) で分類
- ツール呼び出し (view_file, run_command, etc.) も Sensory/Active に分類
- 全認知活動のシーケンスから bigram を構築し R(s,a) を計算
"""
import re
import os
import sys
import math
import glob
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# === 24 CCL 動詞の FEP Value 軸分類 ===
# I (Internal) = 感覚的/認識的 = Sensory
# A (Ambient) = 行動的/環境変更 = Active
VERB_VALUE = {
    # Telos 族
    "noe": "I", "bou": "I", "zet": "A", "ene": "A",
    # Methodos 族
    "ske": "I", "sag": "I", "pei": "A", "tek": "A",
    # Krisis 族
    "kat": "I", "epo": "I", "pai": "A", "dok": "A",
    # Diástasis 族
    "lys": "I", "ops": "I", "akr": "A", "arc": "A",
    # Orexis 族
    "beb": "I", "ele": "I", "kop": "A", "dio": "A",
    # Chronos 族
    "hyp": "I", "prm": "I", "ath": "A", "par": "A",
}

# セッション管理 WF も分類
SESSION_VERBS = {
    "boot": "I",  # ブート = 文脈認識 (Sensory)
    "bye": "A",   # 終了 = 成果物生成 (Active)
    "fit": "I",   # フィット判定 = 品質評価 (Sensory)
    "rom": "A",   # ROM焼付け = 永続化 (Active)
    "hon": "I",   # 本気モード = メタ認知 (Sensory)
}

# ツール呼び出しの S/A 分類
TOOL_VALUE = {
    # Sensory (情報取得) — Antigravity 形式
    "view_file": "I", "list_dir": "I", "grep_search": "I",
    "find_by_name": "I", "search_web": "I", "read_url": "I",
    "Searched": "I",
    # Active (環境変更) — Antigravity 形式
    "write_to_file": "A", "replace_file_content": "A",
    "multi_replace": "A", "run_command": "A",
    "Created": "A", "Modified": "A", "Deleted": "A",
    "browser_subagent": "A", "generate_image": "A",
    # Sensory (情報取得) — Claude Code 形式
    "Read": "I", "Grep": "I", "Glob": "I",
    "WebFetch": "I", "WebSearch": "I", "ToolSearch": "I",
    # Active (環境変更) — Claude Code 形式
    "Write": "A", "Edit": "A", "MultiEdit": "A",
    "Bash": "A", "Agent": "A", "Skill": "A",
    "TodoWrite": "A", "NotebookEdit": "A",
}

# 全動詞辞書を統合
ALL_VERBS = {**VERB_VALUE, **SESSION_VERBS}

# === 正規表現パターン ===
# CCL 動詞パターン
CCL_VERBS = "|".join(sorted(ALL_VERBS.keys(), key=len, reverse=True))
CCL_PAT = re.compile(rf"/({CCL_VERBS})[\+\-]?\b")

# ツール呼び出しパターン
TOOL_NAMES = "|".join(sorted(TOOL_VALUE.keys(), key=len, reverse=True))
TOOL_PAT = re.compile(rf"\b({TOOL_NAMES})\b")

# ターン境界パターン
TURN_PAT = re.compile(r"^##\s+(👤\s*User|🤖\s*Claude)", re.MULTILINE)


@dataclass
class CognitiveEvent:
    """認知イベント"""
    kind: str       # "ccl" or "tool"
    name: str       # 動詞名 or ツール名
    value: str      # "I" or "A"
    line: int = 0   # 行番号(デバッグ用)


@dataclass
class SessionData:
    """セッションデータ"""
    filename: str
    date: str
    title: str
    events: list = field(default_factory=list)
    msg_count: int = 0


def extract_events(content: str) -> list:
    """テキストから認知イベントのシーケンスを抽出する。

    CCL動詞とツール呼び出しを行順に抽出。
    重複除去: 同一行内で同一イベントが複数出現する場合は1回のみカウント。
    """
    events = []
    seen_in_line = set()

    for line_no, line in enumerate(content.split("\n"), 1):
        seen_in_line.clear()

        # CCL 動詞を抽出
        for m in CCL_PAT.finditer(line):
            verb = m.group(1).lower()
            key = ("ccl", verb)
            if key not in seen_in_line and verb in ALL_VERBS:
                events.append(CognitiveEvent(
                    kind="ccl", name=verb,
                    value=ALL_VERBS[verb], line=line_no
                ))
                seen_in_line.add(key)

        # ツール呼び出しを抽出
        for m in TOOL_PAT.finditer(line):
            tool = m.group(1)
            key = ("tool", tool)
            if key not in seen_in_line and tool in TOOL_VALUE:
                events.append(CognitiveEvent(
                    kind="tool", name=tool,
                    value=TOOL_VALUE[tool], line=line_no
                ))
                seen_in_line.add(key)

    return events


def load_conv_sessions(conv_dir: str) -> list:
    """conv/ ディレクトリからセッションをロードする"""
    pattern = os.path.join(conv_dir, "*.md")
    files = sorted(glob.glob(pattern))
    sessions = []

    date_pat = re.compile(r"(\d{4}-\d{2}-\d{2})")
    msg_pat = re.compile(r"\*\*メッセージ数\*\*:\s*(\d+)")

    for filepath in files:
        basename = os.path.basename(filepath)

        # 日付を抽出
        m = date_pat.match(basename)
        date = m.group(1) if m else "unknown"

        # タイトルを抽出 (日付とconv番号を除去)
        title = re.sub(r"^\d{4}-\d{2}-\d{2}_conv_\d+_", "", basename)
        title = title.replace(".md", "")

        try:
            with open(filepath, encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue

        # メッセージ数を抽出
        mm = msg_pat.search(content[:500])
        msg_count = int(mm.group(1)) if mm else 0

        # 認知イベントを抽出
        events = extract_events(content)

        if events:  # イベントがあるセッションのみ
            sessions.append(SessionData(
                filename=basename,
                date=date,
                title=title,
                events=events,
                msg_count=msg_count,
            ))

    return sessions


def load_claude_code_sessions(jsonl_dir: str) -> list:
    """Claude Code .jsonl セッションログからセッションをロードする"""
    import json as _json

    pattern = os.path.join(jsonl_dir, "*.jsonl")
    files = sorted(glob.glob(pattern))
    sessions = []

    for filepath in files:
        basename = os.path.basename(filepath)
        events = []
        first_ts = "unknown"

        try:
            with open(filepath, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    try:
                        d = _json.loads(line)
                    except _json.JSONDecodeError:
                        continue

                    dtype = d.get("type", "")

                    # timestamp 取得 (最初のもの)
                    if first_ts == "unknown":
                        ts = d.get("timestamp", "")
                        if ts and len(ts) >= 10:
                            first_ts = ts[:10]

                    # assistant メッセージからツール呼出と CCL 動詞を抽出
                    if dtype == "assistant":
                        msg = d.get("message", {})
                        content = msg.get("content", [])
                        if not isinstance(content, list):
                            continue
                        for block in content:
                            if not isinstance(block, dict):
                                continue
                            if block.get("type") == "tool_use":
                                tool_name = block.get("name", "")
                                # MCP ツールを汎用分類
                                value = TOOL_VALUE.get(tool_name)
                                if value is None and tool_name.startswith("mcp__"):
                                    low = tool_name.lower()
                                    if any(k in low for k in ("search", "observe", "check", "graph", "query", "read", "list", "get")):
                                        value = "I"
                                    else:
                                        value = "A"
                                if value:
                                    events.append(CognitiveEvent(kind="tool", name=tool_name, value=value))
                            elif block.get("type") == "text":
                                text = block.get("text", "")
                                for m in CCL_PAT.finditer(text):
                                    verb = m.group(1).lower()
                                    if verb in ALL_VERBS:
                                        events.append(CognitiveEvent(kind="ccl", name=verb, value=ALL_VERBS[verb]))

                    # user メッセージから CCL 動詞を抽出
                    elif dtype == "user":
                        msg = d.get("message", {})
                        content = msg.get("content", [])
                        if isinstance(content, str):
                            content = [{"type": "text", "text": content}]
                        if not isinstance(content, list):
                            continue
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text = block.get("text", "")
                                for m in CCL_PAT.finditer(text):
                                    verb = m.group(1).lower()
                                    if verb in ALL_VERBS:
                                        events.append(CognitiveEvent(kind="ccl", name=verb, value=ALL_VERBS[verb]))

        except Exception:
            continue

        if events:
            sessions.append(SessionData(
                filename=basename,
                date=first_ts,
                title=basename.replace(".jsonl", ""),
                events=events,
            ))

    return sessions


def compute_entropy(counts: Counter) -> float:
    """Shannon エントロピー (bits)"""
    total = sum(counts.values())
    if total == 0:
        return 0.0
    h = 0.0
    for c in counts.values():
        if c > 0:
            p = c / total
            h -= p * math.log2(p)
    return h


def compute_rsa_from_events(events: list) -> dict:
    """イベントシーケンスから R(s,a) = I(S;A) を計算する。

    bigram (連続する2イベント) の Value 軸遷移から相互情報量を計算。
    """
    if len(events) < 2:
        return {"rsa": 0.0, "rsa_norm": 0.0, "bigrams": 0,
                "transitions": Counter(), "s_counts": Counter(), "a_counts": Counter()}

    # bigram を構築
    transitions = Counter()  # (前のValue, 後のValue) のカウント
    s_counts = Counter()     # 前のイベントの Value カウント
    a_counts = Counter()     # 後のイベントの Value カウント

    for i in range(len(events) - 1):
        s = events[i].value   # 前 (sensory role)
        a = events[i + 1].value  # 後 (active role)
        transitions[(s, a)] += 1
        s_counts[s] += 1
        a_counts[a] += 1

    n_bigrams = sum(transitions.values())
    if n_bigrams == 0:
        return {"rsa": 0.0, "rsa_norm": 0.0, "bigrams": 0,
                "transitions": transitions, "s_counts": s_counts, "a_counts": a_counts}

    # H(S), H(A), H(S,A) を計算
    h_s = compute_entropy(s_counts)
    h_a = compute_entropy(a_counts)
    h_sa = compute_entropy(transitions)

    # I(S;A) = H(S) + H(A) - H(S,A)
    rsa = max(0.0, h_s + h_a - h_sa)

    # 正規化: R_norm = I / min(H(S), H(A))
    h_min = min(h_s, h_a) if min(h_s, h_a) > 0 else 1.0
    rsa_norm = rsa / h_min

    return {
        "rsa": rsa,
        "rsa_norm": rsa_norm,
        "bigrams": n_bigrams,
        "h_s": h_s,
        "h_a": h_a,
        "h_sa": h_sa,
        "transitions": transitions,
        "s_counts": s_counts,
        "a_counts": a_counts,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="R(s,a) 全認知活動版")
    parser.add_argument("conv_dir", nargs="?",
                        default="/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/"
                                "30_記憶｜Mneme/01_記録｜Records/b_対話｜sessions/conv",
                        help="conv/*.md ディレクトリ")
    parser.add_argument("--jsonl", default=os.path.expanduser(
                        "~/.claude/projects/-home-makaron8426-Sync-oikos-01--------Hegemonikon"),
                        help="Claude Code .jsonl ディレクトリ")
    parser.add_argument("--all", action="store_true",
                        help="conv/ と .jsonl の両方を統合")
    parser.add_argument("--jsonl-only", action="store_true",
                        help=".jsonl のみ使用")
    args = parser.parse_args()

    print(f"=== R(s,a) 全認知活動版 (v8) ===")

    sessions = []
    if args.jsonl_only:
        print(f"データソース: {args.jsonl} (Claude Code .jsonl)")
        sessions = load_claude_code_sessions(args.jsonl)
    elif args.all:
        print(f"データソース [conv]: {args.conv_dir}")
        print(f"データソース [jsonl]: {args.jsonl}")
        s_conv = load_conv_sessions(args.conv_dir)
        s_jsonl = load_claude_code_sessions(args.jsonl)
        print(f"  conv セッション: {len(s_conv)}")
        print(f"  jsonl セッション: {len(s_jsonl)}")
        sessions = s_conv + s_jsonl
    else:
        print(f"データソース: {args.conv_dir}")
        sessions = load_conv_sessions(args.conv_dir)

    print()
    print(f"セッション数: {len(sessions)}")

    if not sessions:
        print("セッションが見つかりません")
        return

    # === 全体集計 ===
    all_events = []
    for s in sessions:
        all_events.extend(s.events)

    print(f"認知イベント総数: {len(all_events)}")
    print()

    # イベント種類の分布
    ccl_events = [e for e in all_events if e.kind == "ccl"]
    tool_events = [e for e in all_events if e.kind == "tool"]
    print(f"CCL 動詞イベント: {len(ccl_events)}")
    print(f"ツールイベント: {len(tool_events)}")
    print()

    # CCL 動詞の上位
    ccl_counter = Counter(e.name for e in ccl_events)
    print("CCL 動詞分布 (上位15):")
    for verb, cnt in ccl_counter.most_common(15):
        v = ALL_VERBS.get(verb, "?")
        print(f"  /{verb:5} ({v}): {cnt:>5}")

    # ツールの上位
    tool_counter = Counter(e.name for e in tool_events)
    print("\nツール分布 (上位10):")
    for tool, cnt in tool_counter.most_common(10):
        v = TOOL_VALUE.get(tool, "?")
        print(f"  {tool:25} ({v}): {cnt:>5}")

    # Value 軸の分布
    value_counter = Counter(e.value for e in all_events)
    total = sum(value_counter.values())
    print(f"\nValue 軸分布:")
    for v in ["I", "A"]:
        c = value_counter.get(v, 0)
        print(f"  {v} ({'Sensory/Internal' if v == 'I' else 'Active/Ambient'}): "
              f"{c:>5} ({100*c/total:.1f}%)")

    # === 全体 R(s,a) ===
    print("\n" + "=" * 50)
    print("=== 全体 R(s,a) (全セッション集約) ===")
    result = compute_rsa_from_events(all_events)
    print(f"  bigram 数: {result['bigrams']}")
    print(f"  H(S): {result.get('h_s', 0):.4f} bits")
    print(f"  H(A): {result.get('h_a', 0):.4f} bits")
    print(f"  H(S,A): {result.get('h_sa', 0):.4f} bits")
    print(f"  R(s,a) = I(S;A): {result['rsa']:.4f} bits")
    print(f"  R_norm: {result['rsa_norm']:.4f}")
    print()

    # 遷移行列
    print("  遷移行列 (Value 軸):")
    print(f"  {'':5} {'→I':>6} {'→A':>6}")
    for s_val in ["I", "A"]:
        row = []
        for a_val in ["I", "A"]:
            row.append(result["transitions"].get((s_val, a_val), 0))
        total_row = sum(row)
        pcts = [f"{100*r/total_row:.0f}%" if total_row > 0 else "0%" for r in row]
        print(f"  {s_val:5} {row[0]:>6} {row[1]:>6}  ({pcts[0]}/{pcts[1]})")

    # === セッション別 R(s,a) ===
    print("\n" + "=" * 50)
    print("=== セッション別 R(s,a) (上位20) ===")
    session_results = []
    for s in sessions:
        r = compute_rsa_from_events(s.events)
        r["session"] = s
        session_results.append(r)

    # R(s,a) > 0 のセッションのみ、降順
    active = [r for r in session_results if r["rsa"] > 0 and r["bigrams"] >= 10]
    active.sort(key=lambda x: x["rsa"], reverse=True)

    for r in active[:20]:
        s = r["session"]
        print(f"  R={r['rsa']:.4f} norm={r['rsa_norm']:.4f} "
              f"n={r['bigrams']:>4} {s.date} {s.title[:40]}")

    # 統計
    all_rsa = [r["rsa"] for r in session_results if r["bigrams"] >= 10]
    if all_rsa:
        mean_rsa = sum(all_rsa) / len(all_rsa)
        sorted_rsa = sorted(all_rsa)
        median_rsa = sorted_rsa[len(sorted_rsa) // 2]
        print(f"\n  セッション数 (≥10 bigrams): {len(all_rsa)}")
        print(f"  平均 R(s,a): {mean_rsa:.4f}")
        print(f"  中央値 R(s,a): {median_rsa:.4f}")
        print(f"  最大 R(s,a): {max(all_rsa):.4f}")
        print(f"  最小 R(s,a): {min(all_rsa):.4f}")

    # === 日付別集計 ===
    print("\n" + "=" * 50)
    print("=== 日付別 R(s,a) ===")
    by_date = defaultdict(list)
    for s in sessions:
        by_date[s.date].extend(s.events)

    date_results = []
    for date in sorted(by_date.keys()):
        events = by_date[date]
        r = compute_rsa_from_events(events)
        if r["bigrams"] >= 5:
            date_results.append((date, r))
            print(f"  {date}: R={r['rsa']:.4f} norm={r['rsa_norm']:.4f} "
                  f"n={r['bigrams']:>5} events={len(events)}")

    # === サマリー ===
    print("\n" + "=" * 50)
    print("=== サマリー ===")
    print(f"全セッション: {len(sessions)}")
    print(f"全認知イベント: {len(all_events)}")
    print(f"全 bigrams: {result['bigrams']}")
    print(f"R(s,a) [全体集約]: {result['rsa']:.4f} bits")
    print(f"R(s,a) [正規化]: {result['rsa_norm']:.4f}")
    if all_rsa:
        print(f"R(s,a) [セッション平均]: {mean_rsa:.4f}")
        print(f"R(s,a) [セッション中央値]: {median_rsa:.4f}")


if __name__ == "__main__":
    main()
