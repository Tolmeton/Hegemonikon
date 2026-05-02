#!/usr/bin/env python3
"""tape ベース PoC — HGK+ データ拡張 (v2)

tape JSONL (WF実行記録) からセッション単位で認知メトリクスを自動計算する。

v2 操作的定義の再定義:
  H(s) := Telos 族 (6族) の使用分布エントロピー
           族 = {Telos, Methodos, Krisis, Diástasis, Orexis, Chronos}
           WF 名 → 族マッピングは CCL 36動詞の定義に基づく
  H(a) := 個別 WF の使用頻度エントロピー (正規化)
  R(s,a) := I(族; WF) 族と WF の相互情報量
  S(B) := WF 実行成功率 (COMPLETE + DIRECT_EXEC) / (COMPLETE + DIRECT_EXEC + FAILED)

根拠: tape は構造化された JSONL で操作的定義の一致度が高い。
      conv はテキストにツール呼出が直接記録されないため不適。
"""
import json
import math
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from dataclasses import dataclass, field

# === WF → 族 (Series) マッピング ===
# 36 動詞 → 6 族 (episteme-entity-map.md 準拠)
WF_TO_SERIES = {
    # Telos (目的) = Flow × Value
    "noe": "Telos", "bou": "Telos", "zet": "Telos",
    "ene": "Telos", "the": "Telos", "ant": "Telos",
    # Methodos (方法) = Flow × Function
    "ske": "Methodos", "sag": "Methodos", "pei": "Methodos",
    "tek": "Methodos", "ere": "Methodos", "agn": "Methodos",
    # Krisis (判断) = Flow × Precision
    "kat": "Krisis", "epo": "Krisis", "pai": "Krisis",
    "dok": "Krisis", "sap": "Krisis", "ski": "Krisis",
    # Diástasis (拡張) = Flow × Scale
    "lys": "Diastasis", "ops": "Diastasis", "akr": "Diastasis",
    "arc": "Diastasis", "prs": "Diastasis", "per": "Diastasis",
    # Orexis (欲求) = Flow × Valence
    "beb": "Orexis", "ele": "Orexis", "kop": "Orexis",
    "dio": "Orexis", "apo": "Orexis", "exe": "Orexis",
    # Chronos (時間) = Flow × Temporality
    "hyp": "Chronos", "prm": "Chronos", "ath": "Chronos",
    "par": "Chronos", "his": "Chronos", "prg": "Chronos",
}

# メタ WF (族に属さないもの) → "MetaWF" にマッピング
META_WFS = {
    "boot", "bye", "rom", "eat", "fit", "hon", "vet",
    "dendron", "basanos", "u", "x", "ax",
}

# CCL マクロ → 解決
CCL_MACROS = {
    "ccl-build", "ccl-chew", "ccl-denoise", "ccl-design",
    "ccl-desktop", "ccl-dig", "ccl-ero", "ccl-exp",
    "ccl-fix", "ccl-gap", "ccl-helm", "ccl-kyc",
    "ccl-learn", "ccl-next", "ccl-noe", "ccl-nous",
    "ccl-plan", "ccl-prd", "ccl-proof", "ccl-query",
    "ccl-read", "ccl-ready", "ccl-rest", "ccl-rpr",
    "ccl-search", "ccl-syn", "ccl-tak", "ccl-vet",
    "ccl-wake", "ccl-weave", "ccl-xrev",
}


def resolve_wf_name(wf: str) -> str:
    """WF 名を正規化 (/noe+ → noe, @ccl-build → ccl-build)"""
    wf = wf.strip()
    # 先頭の / や @ を除去
    if wf.startswith("/") or wf.startswith("@"):
        wf = wf[1:]
    # 修飾子 (+, -, *, >>, _, ~) を除去
    for ch in "+-*_~":
        wf = wf.split(ch)[0]
    # >> 演算子で分割
    wf = wf.split(">>")[0]
    return wf.lower().strip()


def wf_to_series(wf: str) -> str:
    """WF 名 → 族名"""
    name = resolve_wf_name(wf)
    if name in WF_TO_SERIES:
        return WF_TO_SERIES[name]
    if name in META_WFS:
        return "MetaWF"
    if name.startswith("ccl-"):
        return "CCL_Macro"
    # Peras 族
    if name in ("t", "m", "k", "d", "o", "c"):
        return "Peras"
    return "Other"


def shannon_entropy(counts: list[int]) -> float:
    """Shannon entropy H = -Σ p_i log2(p_i)"""
    total = sum(counts)
    if total == 0:
        return 0.0
    probs = [c / total for c in counts if c > 0]
    return -sum(p * math.log2(p) for p in probs)


def normalized_entropy(counts: list[int]) -> float:
    """正規化 Shannon entropy H_norm = H / log2(n)"""
    n = len([c for c in counts if c > 0])
    if n <= 1:
        return 0.0
    h = shannon_entropy(counts)
    return h / math.log2(n)


def mutual_information(joint_counts: dict[tuple, int]) -> float:
    """相互情報量 I(X;Y) = H(X) + H(Y) - H(X,Y)"""
    marginal_x: Counter = Counter()
    marginal_y: Counter = Counter()
    for (x, y), c in joint_counts.items():
        marginal_x[x] += c
        marginal_y[y] += c
    h_x = shannon_entropy(list(marginal_x.values()))
    h_y = shannon_entropy(list(marginal_y.values()))
    h_xy = shannon_entropy(list(joint_counts.values()))
    return max(0.0, h_x + h_y - h_xy)


@dataclass
class SessionMetrics:
    """1セッション (日付単位) の計測結果"""
    session_id: str
    date: str
    wf_counts: Counter = field(default_factory=Counter)
    series_counts: Counter = field(default_factory=Counter)
    success_count: int = 0
    fail_count: int = 0
    total_wf: int = 0

    H_s: float = 0.0   # 族使用分布エントロピー
    H_a: float = 0.0   # WF 使用頻度エントロピー
    R_sa: float = 0.0   # 族×WF 相互情報量
    S_B: float = 0.0    # WF 実行成功率
    k_s: int = 0        # 利用族数
    k_a: int = 0        # 利用 WF 数
    theta_B: float = 0.0


def load_tape_data(tape_dir: Path) -> list[dict]:
    """全 tape JSONL ファイルを読み込み"""
    entries = []
    for tape_file in sorted(tape_dir.glob("tape_*.jsonl")):
        with tape_file.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def group_by_session(entries: list[dict]) -> dict[str, list[dict]]:
    """tape エントリをセッション単位にグループ化

    セッション境界 = 日付 (ts の YYYY-MM-DD)
    """
    sessions = defaultdict(list)
    for e in entries:
        ts = e.get("ts", "")
        date = ts[:10] if ts else "unknown"
        sessions[date].append(e)
    return dict(sessions)


def compute_session_metrics(session_id: str, entries: list[dict]) -> SessionMetrics | None:
    """1セッション分のエントリから Θ(B) メトリクスを計算"""
    wf_counts = Counter()
    series_counts = Counter()
    success_count = 0
    fail_count = 0

    for e in entries:
        wf = e.get("wf", "")
        step = e.get("step", "")
        success = e.get("success")

        if step in ("COMPLETE", "DIRECT_EXEC"):
            wf_name = resolve_wf_name(wf)
            series = wf_to_series(wf)
            wf_counts[wf_name] += 1
            series_counts[series] += 1
            success_count += 1
        elif step == "FAILED":
            fail_count += 1

    total_wf = sum(wf_counts.values())
    if total_wf < 2:
        return None

    date = entries[0].get("ts", "")[:10] if entries else "unknown"

    metrics = SessionMetrics(
        session_id=session_id,
        date=date,
        wf_counts=wf_counts,
        series_counts=series_counts,
        success_count=success_count,
        fail_count=fail_count,
        total_wf=total_wf,
    )

    # H(s): 族分布の正規化エントロピー
    metrics.H_s = normalized_entropy(list(series_counts.values()))
    metrics.k_s = len(series_counts)

    # H(a): WF 使用頻度の正規化エントロピー
    metrics.H_a = normalized_entropy(list(wf_counts.values()))
    metrics.k_a = len(wf_counts)

    # R(s,a): 族×WF の相互情報量
    joint = {}
    for wf_name, count in wf_counts.items():
        series = wf_to_series(wf_name)
        joint[(series, wf_name)] = count
    metrics.R_sa = mutual_information(joint)

    # S(B): 成功率
    total_attempts = success_count + fail_count
    metrics.S_B = success_count / total_attempts if total_attempts > 0 else 0.0

    # Θ(B)
    alpha, beta, gamma = 1.0, 1.0, 1.0
    metrics.theta_B = metrics.S_B * (
        1 + alpha * metrics.H_s + beta * metrics.H_a + gamma * metrics.R_sa
    )

    return metrics


def main():
    parser = argparse.ArgumentParser(description="tape ベース PoC — HGK+ データ拡張")
    parser.add_argument("--tape-dir", type=Path,
                        default=Path(__file__).parent.parent.parent /
                        "30_記憶｜Mneme/01_記録｜Records/g_実行痕跡｜traces",
                        help="tape ディレクトリのパス")
    parser.add_argument("--min-wf", type=int, default=2,
                        help="HGK+ 判定の最小 WF 完了数")
    parser.add_argument("--csv", type=str, default="",
                        help="CSV 出力ファイルパス")
    parser.add_argument("--verbose", action="store_true",
                        help="各セッションの詳細を表示")
    args = parser.parse_args()

    tape_dir = args.tape_dir
    if not tape_dir.exists():
        print(f"❌ ディレクトリが見つかりません: {tape_dir}")
        return

    print(f"📂 tape ディレクトリ: {tape_dir}")

    # tape データの読み込み
    entries = load_tape_data(tape_dir)
    print(f"📊 全エントリ数: {len(entries)}")

    # セッション単位にグループ化
    sessions = group_by_session(entries)
    print(f"📅 セッション数 (日付単位): {len(sessions)}")

    print(f"\n{'='*70}")
    print(f"  tape ベース PoC — HGK+ メトリクス自動計算")
    print(f"{'='*70}\n")

    results: list[SessionMetrics] = []

    for session_id in sorted(sessions.keys()):
        session_entries = sessions[session_id]
        metrics = compute_session_metrics(session_id, session_entries)
        if metrics is None:
            continue
        results.append(metrics)

        if args.verbose:
            print(f"\n  [{session_id}]")
            print(f"    WF 完了: {metrics.total_wf} | "
                  f"族={metrics.k_s} | WF種={metrics.k_a}")
            print(f"    H(s)={metrics.H_s:.3f} | H(a)={metrics.H_a:.3f} | "
                  f"R(s,a)={metrics.R_sa:.3f} | S(B)={metrics.S_B:.3f}")
            print(f"    Θ(B)={metrics.theta_B:.3f}")
            top_wfs = metrics.wf_counts.most_common(5)
            print(f"    Top WFs: {', '.join(f'{w}={c}' for w,c in top_wfs)}")
            top_series = metrics.series_counts.most_common(3)
            print(f"    Top Series: {', '.join(f'{s}={c}' for s,c in top_series)}")

    # === サマリー ===
    print(f"\n{'='*70}")
    print(f"  サマリー")
    print(f"{'='*70}")
    print(f"  全セッション: {len(sessions)}")
    print(f"  HGK+ 判定: {len(results)} セッション (WF≥{args.min_wf})")

    if results:
        h_s_vals = [r.H_s for r in results]
        h_a_vals = [r.H_a for r in results]
        r_sa_vals = [r.R_sa for r in results]
        s_b_vals = [r.S_B for r in results]
        theta_vals = [r.theta_B for r in results]
        k_s_vals = [float(r.k_s) for r in results]
        k_a_vals = [float(r.k_a) for r in results]
        total_wf_vals = [float(r.total_wf) for r in results]

        print(f"\n  n = {len(results)} セッション")
        print(f"\n  {'指標':>10s} {'平均':>8s} {'SD':>8s} {'最小':>8s} {'最大':>8s}")
        print(f"  {'-'*50}")
        for name, vals in [
            ("H(s)", h_s_vals), ("H(a)", h_a_vals),
            ("R(s,a)", r_sa_vals), ("S(B)", s_b_vals),
            ("Θ(B)", theta_vals), ("k_s", k_s_vals),
            ("k_a", k_a_vals), ("n_wf", total_wf_vals),
        ]:
            mean = sum(vals) / len(vals)
            std = (sum((v - mean)**2 for v in vals) / len(vals)) ** 0.5
            print(f"  {name:>10s} {mean:8.3f} {std:8.3f} {min(vals):8.3f} {max(vals):8.3f}")

        # v2 の手動値との比較
        print(f"\n  📊 v2 手動計測値との比較:")
        print(f"  v2 Session 1: H(s)=2.81, H(a)=2.32, R(s,a)=0.67, S(B)=0.94")
        print(f"  v2 Session 2: H(s)=2.65, H(a)=2.18, R(s,a)=0.71, S(B)=0.91")
        mean_Hs = sum(h_s_vals)/len(h_s_vals)
        mean_Ha = sum(h_a_vals)/len(h_a_vals)
        mean_Rsa = sum(r_sa_vals)/len(r_sa_vals)
        mean_SB = sum(s_b_vals)/len(s_b_vals)
        print(f"  tape 自動平均: H(s)={mean_Hs:.2f}, "
              f"H(a)={mean_Ha:.2f}, "
              f"R(s,a)={mean_Rsa:.2f}, "
              f"S(B)={mean_SB:.2f}")

        # 注意点
        print(f"\n  ⚠️ 注意: 操作的定義が異なる")
        print(f"    v2: H(s) = MCP サーバ別ツール分布")
        print(f"    v2 tape: H(s) = Telos 6族の WF 使用分布")
        print(f"    → 直接比較は適切でない。レベルの再定義が必要")

    # CSV 出力
    if args.csv and results:
        import csv
        with open(args.csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'session_id', 'date', 'H_s', 'H_a', 'R_sa', 'S_B', 'theta_B',
                'k_s', 'k_a', 'total_wf', 'success', 'fail',
            ])
            for r in results:
                writer.writerow([
                    r.session_id, r.date,
                    f"{r.H_s:.4f}", f"{r.H_a:.4f}",
                    f"{r.R_sa:.4f}", f"{r.S_B:.4f}", f"{r.theta_B:.4f}",
                    r.k_s, r.k_a, r.total_wf,
                    r.success_count, r.fail_count,
                ])
        print(f"\n  📁 CSV 出力: {args.csv}")


if __name__ == "__main__":
    main()
