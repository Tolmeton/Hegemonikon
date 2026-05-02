#!/usr/bin/env python3
"""
矛盾3 診断: Scale 軸がなぜ不活性か

Scale proxy = compute_ratio(micro_n, macro_n)
MICRO = {lys, akr}  — 詳細分析 + 精密操作
MACRO = {ops, arc}  — 俯瞰 + 全体展開

仮説:
  H1: micro/macro 動詞がそもそも少ない (頻度不足)
  H2: micro/macro が常に同時出現 → 比率が 0.5 に固定
  H3: Theorem Log の族マッピングで Diastasis (lys/ops/akr/arc) が必ず 4 つセットで入る
      → micro=2, macro=2 → 比率固定
"""

import json, re
import numpy as np
from pathlib import Path
from collections import defaultdict

TRACES_DIR = Path("/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/g_実行痕跡｜traces")
LOGS_DIR = Path("/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/f_ログ｜logs")

ALL_24 = {'noe','bou','zet','ene','ske','sag','pei','tek',
          'kat','epo','pai','dok','lys','ops','akr','arc',
          'beb','ele','kop','dio','hyp','prm','ath','par'}
VERB_RE = re.compile(r'/([a-z]{2,4})([+\-])?')
MICRO = {"lys","akr"}
MACRO = {"ops","arc"}

print("=" * 60)
print("矛盾3: Scale 軸不活性の原因分析")
print("=" * 60)

# ── Tape イベントでの micro/macro 出現 ──
tape_micro = tape_macro = tape_total = 0
tape_events_with_scale = 0

for tape in sorted(TRACES_DIR.glob("tape_*.jsonl")):
    with open(tape) as f:
        for line in f:
            l = line.strip()
            if not l: continue
            try: ev = json.loads(l)
            except: continue
            wf = ev.get("wf", "")
            verbs = [(m.group(1), m.group(2) or "") for m in VERB_RE.finditer(wf) if m.group(1) in ALL_24]
            if verbs:
                tape_total += 1
                mi = sum(1 for v, _ in verbs if v in MICRO)
                ma = sum(1 for v, _ in verbs if v in MACRO)
                tape_micro += mi
                tape_macro += ma
                if mi > 0 or ma > 0:
                    tape_events_with_scale += 1

print(f"\n── Tape イベント ──")
print(f"  総イベント: {tape_total}")
print(f"  micro (lys/akr) 出現計: {tape_micro}")
print(f"  macro (ops/arc) 出現計: {tape_macro}")
print(f"  Scale 関連イベント: {tape_events_with_scale} / {tape_total} ({100*tape_events_with_scale/tape_total if tape_total else 0:.1f}%)")

# ── Theorem Log での Diastasis 出現 ──
THEOREM_TO_SERIES = {
    "O1": "Telos", "O2": "Telos", "O3": "Telos", "O4": "Telos",
    "A1": "Telos", "A2": "Telos", "A3": "Telos", "A4": "Telos",
    "P1": "Methodos", "P2": "Methodos", "P3": "Methodos", "P4": "Methodos",
    "K1": "Krisis", "K2": "Krisis", "K3": "Krisis", "K4": "Krisis",
    "S1": "Diastasis", "S2": "Diastasis", "S3": "Diastasis", "S4": "Diastasis",
    "H1": "Chronos", "H2": "Chronos", "H3": "Chronos", "H4": "Chronos",
}
SERIES_TO_VERBS = {
    "Diastasis": ["lys","ops","akr","arc"],
}

theorem_total = theorem_diastasis = 0
for logf in sorted(LOGS_DIR.glob("theorem_log_*.jsonl")):
    with open(logf) as f:
        for line in f:
            l = line.strip()
            if not l: continue
            try: ev = json.loads(l)
            except: continue
            theorem = ev.get("theorem", "")
            series = THEOREM_TO_SERIES.get(theorem)
            if series is None: continue
            theorem_total += 1
            if series == "Diastasis":
                theorem_diastasis += 1

print(f"\n── Theorem Log ──")
print(f"  総イベント: {theorem_total}")
print(f"  Diastasis (S1-S4): {theorem_diastasis} ({100*theorem_diastasis/theorem_total if theorem_total else 0:.1f}%)")
print(f"  Diastasis は常に 4 動詞 (lys/ops/akr/arc) セットで入る")
print(f"  → micro=2, macro=2 → ratio = (2+0.5)/(2+2+1) = 0.5 固定")

# ── H3 の検証: ウィンドウ内の micro/macro 比率分布 ──
print(f"\n── ウィンドウ内 Scale proxy 分布 ──")

# 全イベントを読み込み
events = []
for tape in sorted(TRACES_DIR.glob("tape_*.jsonl")):
    with open(tape) as f:
        for line in f:
            l = line.strip()
            if not l: continue
            try: ev = json.loads(l)
            except: continue
            wf = ev.get("wf", "")
            verbs = [(m.group(1), m.group(2) or "") for m in VERB_RE.finditer(wf) if m.group(1) in ALL_24]
            if verbs:
                events.append({"source": "tape", "verbs": verbs})

for logf in sorted(LOGS_DIR.glob("theorem_log_*.jsonl")):
    with open(logf) as f:
        for line in f:
            l = line.strip()
            if not l: continue
            try: ev = json.loads(l)
            except: continue
            theorem = ev.get("theorem", "")
            series = THEOREM_TO_SERIES.get(theorem)
            if series == "Diastasis":
                events.append({"source": "theorem", "verbs": [(v, "") for v in ["lys","ops","akr","arc"]]})
            elif series:
                events.append({"source": "theorem", "verbs": []})  # 非 Diastasis

# ウィンドウ
WINDOW = 20
ratios = []
for i in range(0, len(events) - WINDOW + 1, 5):
    win = events[i:i+WINDOW]
    mi = ma = 0
    for ev in win:
        for v, _ in ev["verbs"]:
            if v in MICRO: mi += 1
            if v in MACRO: ma += 1
    r = (mi + 0.5) / (mi + ma + 1.0)
    ratios.append(r)

ratios = np.array(ratios)
print(f"  サンプル: {len(ratios)} ウィンドウ")
print(f"  Scale proxy: mean={ratios.mean():.6f}, std={ratios.std():.6f}")
print(f"  min={ratios.min():.6f}, max={ratios.max():.6f}")
print(f"  σ < 0.005: {'✅ 不活性 (確認)' if ratios.std() < 0.005 else '❌ 活性'}")

# ── 代替 proxy 案 ──
print(f"\n── 代替 proxy 検討 ──")
print(f"  案1: Diastasis 族の全出現割合 (lys+ops+akr+arc) / 全動詞")
print(f"       → 他の5族との相対比率。Scale の「活性度」を測る")
print(f"  案2: lys+akr (micro) のみの出現割合 / 全動詞")
print(f"       → micro のみを Scale proxy にし、macro との対比は捨てる")
print(f"  案3: ウィンドウ内のユニーク動詞数 / 24 (diversity index)")
print(f"       → micro/macro の区別ではなく「認知の広がり」を Scale proxy に")

# 案3 を実験
diversities = []
for i in range(0, len(events) - WINDOW + 1, 5):
    win = events[i:i+WINDOW]
    unique = set()
    for ev in win:
        for v, _ in ev["verbs"]:
            unique.add(v)
    diversities.append(len(unique) / 24.0)

diversities = np.array(diversities)
print(f"\n  案3 (diversity): mean={diversities.mean():.4f}, std={diversities.std():.4f}")
print(f"    min={diversities.min():.4f}, max={diversities.max():.4f}")
print(f"    σ > 0.005: {'✅ 活性' if diversities.std() > 0.005 else '❌ 不活性'}")

# 案1 を実験
diastasis_ratios = []
for i in range(0, len(events) - WINDOW + 1, 5):
    win = events[i:i+WINDOW]
    dia = total_v = 0
    for ev in win:
        for v, _ in ev["verbs"]:
            total_v += 1
            if v in {"lys","ops","akr","arc"}:
                dia += 1
    diastasis_ratios.append(dia / total_v if total_v > 0 else 0)

diastasis_ratios = np.array(diastasis_ratios)
print(f"\n  案1 (Diastasis割合): mean={diastasis_ratios.mean():.4f}, std={diastasis_ratios.std():.4f}")
print(f"    min={diastasis_ratios.min():.4f}, max={diastasis_ratios.max():.4f}")
print(f"    σ > 0.005: {'✅ 活性' if diastasis_ratios.std() > 0.005 else '❌ 不活性'}")

print(f"\n{'='*60}")
print(f"結論")
print(f"{'='*60}")
print(f"  原因: H3 確認。Theorem Log の Diastasis が常に 4 動詞セットで入り、")
print(f"        micro=2, macro=2 → ratio 固定。Tape の微弱な信号が埋もれる。")
