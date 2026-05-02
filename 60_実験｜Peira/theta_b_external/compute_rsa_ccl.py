#!/usr/bin/env python3
"""
R(s,a) 計算: CCL 動詞の FEP 6軸分類に基づく相互情報量

PURPOSE: HGK+ セッション tape データから R(s,a) を計算する。
- tape JSONL から WF 実行履歴を抽出
- 各 WF 名を CCL 動詞に正規化
- 24 動詞を FEP 6修飾座標で多軸分類
- bigram (連続 2 動詞) を構築
- Value 軸 (Internal↔Ambient) の相互情報量 I(S;A) として R(s,a) を計算
- 他の 5 軸でも同様に R を計算 → 6次元結合テンソル

理論的背景:
  R(s,a) = I(S;A) = H(S) + H(A) - H(S,A)
  S = sensory states (Internal: 認識・受容系の動詞)
  A = active states (Ambient: 行為・環境変更系の動詞)
"""

import json
import glob
import os
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path


# ============================================================
# §1. CCL 24動詞の FEP 6軸分類
# ============================================================
# 各動詞を 6 修飾座標で分類 (episteme-entity-map.md に基づく)
# Value:  I=Internal, A=Ambient
# Function: E=Explore, P=Exploit
# Precision: C=Certain, U=Uncertain
# Scale: Mi=Micro, Ma=Macro
# Valence: +=Positive, -=Negative
# Temporality: Pa=Past, Fu=Future

@dataclass
class VerbProfile:
    """CCL 動詞の FEP 6軸プロファイル"""
    name: str           # 動詞名 (e.g., "noe")
    series: str         # 族 (Telos/Methodos/Krisis/Diastasis/Orexis/Chronos)
    # 6 修飾座標 (各座標は -1.0 〜 +1.0 の連続値)
    # -1.0 = 左極 (Internal/Explore/Certain/Micro/Positive/Past)
    # +1.0 = 右極 (Ambient/Exploit/Uncertain/Macro/Negative/Future)
    value: float        # Internal(-1) ↔ Ambient(+1)
    function: float     # Explore(-1) ↔ Exploit(+1)
    precision: float    # Certain(-1) ↔ Uncertain(+1)
    scale: float        # Micro(-1) ↔ Macro(+1)
    valence: float      # Positive(-1) ↔ Negative(+1)
    temporality: float  # Past(-1) ↔ Future(+1)


# 24動詞の FEP 分類
# episteme-entity-map.md から:
#   Telos = Flow × Value: noe(I×E), bou(I×P), zet(A×E), ene(A×P)
#   Methodos = Flow × Function: ske(I×Explore), sag(I×Exploit), pei(A×Explore), tek(A×Exploit)
#   Krisis = Flow × Precision: kat(I×C), epo(I×U), pai(A×C), dok(A×U)
#   Diástasis = Flow × Scale: lys(I×Mi), ops(I×Ma), akr(A×Mi), arc(A×Ma)
#   Orexis = Flow × Valence: beb(I×+), ele(I×-), kop(A×+), dio(A×-)
#   Chronos = Flow × Temporality: hyp(I×Past), prm(I×Future), ath(A×Past), par(A×Future)
#
# 各 Series は Flow × 1修飾座標。各動詞は Internal(I) or Ambient(A) の属性を持つ。
# Value 軸での S/A 分類: I=Sensory, A=Active

VERB_PROFILES = {
    # Telos (目的): Flow × Value
    "noe": VerbProfile("noe", "Telos",    value=-1.0, function=-1.0, precision= 0.0, scale= 0.0, valence= 0.0, temporality= 0.0),
    "bou": VerbProfile("bou", "Telos",    value=-1.0, function= 1.0, precision= 0.0, scale= 0.0, valence= 0.0, temporality= 0.0),
    "zet": VerbProfile("zet", "Telos",    value= 1.0, function=-1.0, precision= 0.0, scale= 0.0, valence= 0.0, temporality= 0.0),
    "ene": VerbProfile("ene", "Telos",    value= 1.0, function= 1.0, precision= 0.0, scale= 0.0, valence= 0.0, temporality= 0.0),
    # Methodos (方法): Flow × Function
    "ske": VerbProfile("ske", "Methodos", value= 0.0, function=-1.0, precision= 0.0, scale= 0.0, valence= 0.0, temporality= 0.0),
    "sag": VerbProfile("sag", "Methodos", value= 0.0, function= 1.0, precision= 0.0, scale= 0.0, valence= 0.0, temporality= 0.0),
    "pei": VerbProfile("pei", "Methodos", value= 0.0, function=-1.0, precision= 0.0, scale= 0.0, valence= 0.0, temporality= 0.0),
    "tek": VerbProfile("tek", "Methodos", value= 0.0, function= 1.0, precision= 0.0, scale= 0.0, valence= 0.0, temporality= 0.0),
    # Krisis (判断): Flow × Precision
    "kat": VerbProfile("kat", "Krisis",   value= 0.0, function= 0.0, precision=-1.0, scale= 0.0, valence= 0.0, temporality= 0.0),
    "epo": VerbProfile("epo", "Krisis",   value= 0.0, function= 0.0, precision= 1.0, scale= 0.0, valence= 0.0, temporality= 0.0),
    "pai": VerbProfile("pai", "Krisis",   value= 0.0, function= 0.0, precision=-1.0, scale= 0.0, valence= 0.0, temporality= 0.0),
    "dok": VerbProfile("dok", "Krisis",   value= 0.0, function= 0.0, precision= 1.0, scale= 0.0, valence= 0.0, temporality= 0.0),
    # Diástasis (拡張): Flow × Scale
    "lys": VerbProfile("lys", "Diastasis",value= 0.0, function= 0.0, precision= 0.0, scale=-1.0, valence= 0.0, temporality= 0.0),
    "ops": VerbProfile("ops", "Diastasis",value= 0.0, function= 0.0, precision= 0.0, scale= 1.0, valence= 0.0, temporality= 0.0),
    "akr": VerbProfile("akr", "Diastasis",value= 0.0, function= 0.0, precision= 0.0, scale=-1.0, valence= 0.0, temporality= 0.0),
    "arc": VerbProfile("arc", "Diastasis",value= 0.0, function= 0.0, precision= 0.0, scale= 1.0, valence= 0.0, temporality= 0.0),
    # Orexis (欲求): Flow × Valence
    "beb": VerbProfile("beb", "Orexis",   value= 0.0, function= 0.0, precision= 0.0, scale= 0.0, valence=-1.0, temporality= 0.0),
    "ele": VerbProfile("ele", "Orexis",   value= 0.0, function= 0.0, precision= 0.0, scale= 0.0, valence= 1.0, temporality= 0.0),
    "kop": VerbProfile("kop", "Orexis",   value= 0.0, function= 0.0, precision= 0.0, scale= 0.0, valence=-1.0, temporality= 0.0),
    "dio": VerbProfile("dio", "Orexis",   value= 0.0, function= 0.0, precision= 0.0, scale= 0.0, valence= 1.0, temporality= 0.0),
    # Chronos (時間): Flow × Temporality
    "hyp": VerbProfile("hyp", "Chronos",  value= 0.0, function= 0.0, precision= 0.0, scale= 0.0, valence= 0.0, temporality=-1.0),
    "prm": VerbProfile("prm", "Chronos",  value= 0.0, function= 0.0, precision= 0.0, scale= 0.0, valence= 0.0, temporality= 1.0),
    "ath": VerbProfile("ath", "Chronos",  value= 0.0, function= 0.0, precision= 0.0, scale= 0.0, valence= 0.0, temporality=-1.0),
    "par": VerbProfile("par", "Chronos",  value= 0.0, function= 0.0, precision= 0.0, scale= 0.0, valence= 0.0, temporality= 1.0),
}

# Telos 族の Value 分類をより精密に:
# noe(認識) = Internal sensory, bou(意志) = Internal active-planning
# zet(探求) = Ambient exploration, ene(実行) = Ambient execution
# ここで I(Internal) → sensory, A(Ambient) → active として FEP を完全に操作化

# 各 Series の動詞を I/A に再分類 (episteme-entity-map の定義通り)
VERB_IA_CLASSIFICATION = {
    # Telos: noe=I, bou=I, zet=A, ene=A
    "noe": "I", "bou": "I", "zet": "A", "ene": "A",
    # Methodos: ske=I(internal explore), sag=I(internal exploit), pei=A, tek=A
    "ske": "I", "sag": "I", "pei": "A", "tek": "A",
    # Krisis: kat=I(internal certain), epo=I(internal uncertain), pai=A, dok=A
    "kat": "I", "epo": "I", "pai": "A", "dok": "A",
    # Diástasis: lys=I, ops=I, akr=A, arc=A
    "lys": "I", "ops": "I", "akr": "A", "arc": "A",
    # Orexis: beb=I, ele=I, kop=A, dio=A
    "beb": "I", "ele": "I", "kop": "A", "dio": "A",
    # Chronos: hyp=I, prm=I, ath=A, par=A
    "hyp": "I", "prm": "I", "ath": "A", "par": "A",
}

# メタ WF (マクロ) → 基底動詞へのマッピング
MACRO_TO_VERB = {
    "@plan": "bou",     # 計画 → 意志
    "@next": "prm",     # 次提案 → 予見
    "@nous": "noe",     # 認識マクロ → 認識
    "@query": "zet",    # 検索 → 探求
    "@learn": "ath",    # 学習 → 省みる
    "@rest": "epo",     # 休息 → 留保
    "@wake": "hyp",     # 目覚め → 想起
    "boot": "hyp",      # 起動 → 想起/初期化
    "bye": "par",       # 終了 → 先制行動/準備
    "ochema": "tek",    # LLM 呼び出し → 適用
    "fit": "kat",       # 適合判定 → 確定
    "rom": "ops",       # 蒸留 → 俯瞰
    "hon": "pai",       # 本気 → 決断
}


# ============================================================
# §2. WF 名の正規化: CCL 式 → 基底動詞列
# ============================================================

def normalize_wf_to_verbs(wf_name: str) -> list[str]:
    """WF 名を単一または複数の基底動詞名に正規化する。

    例:
      "/noe+" → ["noe"]
      "/ske_/noe+" → ["ske", "noe"]
      "@plan" → ["bou"]
      "C:{...}_/pis_/dox-" → [...] (複雑 CCL は内部動詞を抽出)
    """
    verbs = []

    # マクロ名のチェック
    clean = wf_name.lstrip("/")
    if clean in MACRO_TO_VERB:
        return [MACRO_TO_VERB[clean]]

    # @ マクロ
    if wf_name.startswith("@"):
        macro = wf_name.lstrip("@")
        if macro in MACRO_TO_VERB:
            return [MACRO_TO_VERB[macro]]
        # 未知のマクロ → スキップ
        return []

    # ccl- プレフィックスの WF
    if wf_name.startswith("/ccl-"):
        ccl_name = wf_name.replace("/ccl-", "")
        # ccl-plan → bou, ccl-next → prm など
        mapping = {
            "plan": "bou", "next": "prm", "fix": "dio",
            "build": "ene", "read": "noe", "search": "zet",
            "vet": "ele", "dig": "lys", "exp": "pei",
            "proof": "kat", "ready": "ops", "helm": "bou",
        }
        if ccl_name in mapping:
            return [mapping[ccl_name]]

    # 正規表現で /xxx パターンを抽出
    # 深度修飾子 (+/-) を除去し、基底動詞名を取得
    verb_pattern = re.compile(r'/([a-z]{2,4})[\+\-]?')
    matches = verb_pattern.findall(wf_name)

    for m in matches:
        # FEP に存在しない動詞をフィルタ (pis, dox, dia 等の知られた非24動詞)
        if m in VERB_PROFILES:
            verbs.append(m)
        elif m in MACRO_TO_VERB:
            verbs.append(MACRO_TO_VERB[m])

    return verbs if verbs else []


# ============================================================
# §3. Tape データの読み込みとセッション構造化
# ============================================================

def load_tape_sessions(tape_dir: str, merge_by_date: bool = True) -> list[dict]:
    """tape JSONL ファイル群を読み、セッション単位にグループ化する。

    Args:
        tape_dir: tape ディレクトリパス
        merge_by_date: True の場合、同日の tape を1セッションにマージ

    Returns:
        list[dict]: 各セッション = {
            "date": 日付文字列,
            "files": [ファイル名リスト],
            "wf_sequence": [WF 名の時系列],
            "verb_sequence": [正規化された基底動詞の時系列]
        }
    """
    files = sorted(glob.glob(os.path.join(tape_dir, "tape_*.jsonl")))

    # 全 tape を読み込み、タイムスタンプで時系列順にソート
    all_complete = []
    for filepath in files:
        basename = os.path.basename(filepath)
        # 日付抽出: tape_2026-02-19_0155.jsonl → 2026-02-19
        date_match = re.match(r'tape_(\d{4}-\d{2}-\d{2})_', basename)
        date_str = date_match.group(1) if date_match else "unknown"

        with open(filepath, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entry = json.loads(line)
                    if entry.get("step") == "COMPLETE":
                        entry["_date"] = date_str
                        entry["_file"] = basename
                        all_complete.append(entry)

    # タイムスタンプで全体をソート
    all_complete.sort(key=lambda e: e.get("ts", ""))

    if merge_by_date:
        # 日付でグループ化
        date_groups = defaultdict(list)
        for entry in all_complete:
            date_groups[entry["_date"]].append(entry)

        sessions = []
        for date_str in sorted(date_groups.keys()):
            entries = date_groups[date_str]
            wf_sequence = [e.get("wf", "unknown") for e in entries]
            verb_sequence = []
            for wf in wf_sequence:
                verbs = normalize_wf_to_verbs(wf)
                verb_sequence.extend(verbs)

            files_in_date = list(set(e["_file"] for e in entries))
            if verb_sequence:
                sessions.append({
                    "date": date_str,
                    "files": sorted(files_in_date),
                    "n_tapes": len(files_in_date),
                    "wf_sequence": wf_sequence,
                    "verb_sequence": verb_sequence,
                })
        return sessions
    else:
        # 個別 tape をセッションとして扱う (従来の挙動)
        tape_groups = defaultdict(list)
        for entry in all_complete:
            tape_groups[entry["_file"]].append(entry)

        sessions = []
        for fname in sorted(tape_groups.keys()):
            entries = tape_groups[fname]
            wf_sequence = [e.get("wf", "unknown") for e in entries]
            verb_sequence = []
            for wf in wf_sequence:
                verbs = normalize_wf_to_verbs(wf)
                verb_sequence.extend(verbs)
            if verb_sequence:
                sessions.append({
                    "date": entries[0].get("_date", "unknown"),
                    "files": [fname],
                    "n_tapes": 1,
                    "wf_sequence": wf_sequence,
                    "verb_sequence": verb_sequence,
                })
        return sessions


# ============================================================
# §4. R(s,a) 計算: 相互情報量
# ============================================================

def compute_entropy(counts: Counter) -> float:
    """Shannon エントロピー H(X) を計算する。"""
    total = sum(counts.values())
    if total == 0:
        return 0.0
    h = 0.0
    for count in counts.values():
        if count > 0:
            p = count / total
            h -= p * math.log2(p)
    return h


def compute_rsa_bigram(verb_sequences: list[list[str]]) -> dict:
    """bigram ベースで R(s,a) を計算する。

    各 bigram (v_t, v_{t+1}) について:
    - S = I/A 分類 of v_t
    - A = I/A 分類 of v_{t+1}
    - R(s,a) = I(S;A) = H(S) + H(A) - H(S,A)

    Args:
        verb_sequences: セッションごとの動詞時系列

    Returns:
        dict: {
            "R_sa": 相互情報量 (bits),
            "R_sa_normalized": [0,1] 正規化,
            "H_s": H(S),
            "H_a": H(A),
            "H_sa": H(S,A),
            "bigram_count": bigram 数,
            "transition_matrix": 遷移行列,
        }
    """
    # bigram 抽出
    s_counts = Counter()   # sensory (source) の分布
    a_counts = Counter()   # active (target) の分布
    sa_counts = Counter()  # joint 分布

    total_bigrams = 0

    for seq in verb_sequences:
        for i in range(len(seq) - 1):
            v_src = seq[i]
            v_tgt = seq[i + 1]

            # I/A 分類
            src_ia = VERB_IA_CLASSIFICATION.get(v_src)
            tgt_ia = VERB_IA_CLASSIFICATION.get(v_tgt)

            if src_ia is None or tgt_ia is None:
                continue

            s_counts[src_ia] += 1
            a_counts[tgt_ia] += 1
            sa_counts[(src_ia, tgt_ia)] += 1
            total_bigrams += 1

    if total_bigrams == 0:
        return {"R_sa": 0.0, "R_sa_normalized": 0.0, "bigram_count": 0}

    # エントロピー計算
    h_s = compute_entropy(s_counts)
    h_a = compute_entropy(a_counts)
    h_sa = compute_entropy(sa_counts)

    # 相互情報量 I(S;A) = H(S) + H(A) - H(S,A)
    r_sa = h_s + h_a - h_sa

    # 正規化: R_normalized = I(S;A) / min(H(S), H(A))
    # min(H(S), H(A)) が 0 の場合は 0
    max_mi = min(h_s, h_a) if min(h_s, h_a) > 0 else 1.0
    r_sa_normalized = r_sa / max_mi

    # 遷移行列
    transition_matrix = {}
    for (s, a), count in sa_counts.items():
        transition_matrix[f"{s}→{a}"] = count

    return {
        "R_sa": round(r_sa, 4),
        "R_sa_normalized": round(r_sa_normalized, 4),
        "H_s": round(h_s, 4),
        "H_a": round(h_a, 4),
        "H_sa": round(h_sa, 4),
        "bigram_count": total_bigrams,
        "s_distribution": dict(s_counts),
        "a_distribution": dict(a_counts),
        "transition_matrix": transition_matrix,
    }


def compute_rsa_6axis(verb_sequences: list[list[str]]) -> dict:
    """6軸全てで R を計算する。

    各軸で bigram の (source_pole, target_pole) の相互情報量を計算。
    結果: 6次元の結合テンソル。

    Returns:
        dict: 軸名 → R 値
    """
    axes = {
        "Value": lambda v: "I" if VERB_IA_CLASSIFICATION.get(v) == "I" else "A",
        "Function": lambda v: "E" if VERB_PROFILES.get(v, VerbProfile("?", "?", 0,0,0,0,0,0)).function <= 0 else "P",
        "Precision": lambda v: "C" if VERB_PROFILES.get(v, VerbProfile("?", "?", 0,0,0,0,0,0)).precision <= 0 else "U",
        "Scale": lambda v: "Mi" if VERB_PROFILES.get(v, VerbProfile("?", "?", 0,0,0,0,0,0)).scale <= 0 else "Ma",
        "Valence": lambda v: "+" if VERB_PROFILES.get(v, VerbProfile("?", "?", 0,0,0,0,0,0)).valence <= 0 else "-",
        "Temporality": lambda v: "Pa" if VERB_PROFILES.get(v, VerbProfile("?", "?", 0,0,0,0,0,0)).temporality <= 0 else "Fu",
    }

    results = {}
    for axis_name, classifier in axes.items():
        s_counts = Counter()
        a_counts = Counter()
        sa_counts = Counter()
        total = 0

        for seq in verb_sequences:
            for i in range(len(seq) - 1):
                v_src = seq[i]
                v_tgt = seq[i + 1]
                if v_src not in VERB_PROFILES or v_tgt not in VERB_PROFILES:
                    continue
                s_pole = classifier(v_src)
                a_pole = classifier(v_tgt)
                s_counts[s_pole] += 1
                a_counts[a_pole] += 1
                sa_counts[(s_pole, a_pole)] += 1
                total += 1

        if total == 0:
            results[axis_name] = {"R": 0.0, "R_norm": 0.0, "n": 0}
            continue

        h_s = compute_entropy(s_counts)
        h_a = compute_entropy(a_counts)
        h_sa = compute_entropy(sa_counts)
        r = h_s + h_a - h_sa
        max_mi = min(h_s, h_a) if min(h_s, h_a) > 0 else 1.0

        results[axis_name] = {
            "R": round(r, 4),
            "R_norm": round(r / max_mi, 4),
            "n": total,
            "H_s": round(h_s, 4),
            "H_a": round(h_a, 4),
            "transition": dict(sa_counts),
        }

    return results


# ============================================================
# §5. メイン実行
# ============================================================

def main():
    tape_dir = str(
        Path(__file__).resolve().parent.parent.parent
        / "30_記憶｜Mneme"
        / "01_記録｜Records"
        / "g_実行痕跡｜traces"
    )

    print(f"{'='*60}")
    print(f"R(s,a) 計算: CCL 動詞の FEP 6軸分類")
    print(f"{'='*60}")
    print(f"tape ディレクトリ: {tape_dir}")

    # データ読み込み
    sessions = load_tape_sessions(tape_dir)
    print(f"セッション数: {len(sessions)}")

    total_verbs = sum(len(s["verb_sequence"]) for s in sessions)
    print(f"動詞トークン総数: {total_verbs}")

    # 動詞分布
    all_verbs = []
    for s in sessions:
        all_verbs.extend(s["verb_sequence"])
    verb_dist = Counter(all_verbs)
    print(f"\n--- 動詞分布 ---")
    for verb, cnt in verb_dist.most_common():
        ia = VERB_IA_CLASSIFICATION.get(verb, "?")
        series = VERB_PROFILES.get(verb, VerbProfile("?", "?", 0,0,0,0,0,0)).series
        print(f"  /{verb} ({ia}, {series}): {cnt}")

    # I/A 分布
    ia_dist = Counter()
    for v in all_verbs:
        ia = VERB_IA_CLASSIFICATION.get(v, "?")
        ia_dist[ia] += 1
    print(f"\n--- I/A 分布 ---")
    for ia, cnt in ia_dist.most_common():
        pct = cnt / len(all_verbs) * 100
        print(f"  {ia}: {cnt} ({pct:.1f}%)")

    # 全セッション集計 R(s,a)
    all_verb_sequences = [s["verb_sequence"] for s in sessions]
    print(f"\n{'='*60}")
    print(f"§A. R(s,a) — Value 軸 (全セッション集計)")
    print(f"{'='*60}")
    rsa_result = compute_rsa_bigram(all_verb_sequences)
    for k, v in rsa_result.items():
        print(f"  {k}: {v}")

    # セッション別 R(s,a)
    print(f"\n{'='*60}")
    print(f"§B. R(s,a) — セッション別")
    print(f"{'='*60}")
    session_rsa = []
    for s in sessions:
        r = compute_rsa_bigram([s["verb_sequence"]])
        if r["bigram_count"] >= 3:  # 最低 3 bigram
            session_rsa.append({
                "date": s["date"],
                "n_verbs": len(s["verb_sequence"]),
                "n_bigrams": r["bigram_count"],
                "R_sa": r["R_sa"],
                "R_sa_norm": r["R_sa_normalized"],
            })
            print(f"  {s['date']}: verbs={len(s['verb_sequence']):>3}, "
                  f"bigrams={r['bigram_count']:>3}, "
                  f"R(s,a)={r['R_sa']:.4f}, "
                  f"R_norm={r['R_sa_normalized']:.4f}")

    if session_rsa:
        avg_rsa = sum(s["R_sa"] for s in session_rsa) / len(session_rsa)
        avg_norm = sum(s["R_sa_norm"] for s in session_rsa) / len(session_rsa)
        print(f"\n  平均 R(s,a): {avg_rsa:.4f}")
        print(f"  平均 R_norm: {avg_norm:.4f}")
        print(f"  有効セッション数: {len(session_rsa)}")

    # 6軸 R 計算
    print(f"\n{'='*60}")
    print(f"§C. 6軸結合テンソル (全セッション集計)")
    print(f"{'='*60}")
    r6 = compute_rsa_6axis(all_verb_sequences)
    for axis, data in r6.items():
        print(f"  {axis:>12}: R={data['R']:.4f}, R_norm={data['R_norm']:.4f}, n={data['n']}")

    # Series 間遷移行列
    print(f"\n{'='*60}")
    print(f"§D. Series 間遷移行列")
    print(f"{'='*60}")
    series_bigrams = Counter()
    for seq in all_verb_sequences:
        for i in range(len(seq) - 1):
            s_src = VERB_PROFILES.get(seq[i], VerbProfile("?","?",0,0,0,0,0,0)).series
            s_tgt = VERB_PROFILES.get(seq[i+1], VerbProfile("?","?",0,0,0,0,0,0)).series
            if s_src != "?" and s_tgt != "?":
                series_bigrams[(s_src, s_tgt)] += 1

    series_names = ["Telos", "Methodos", "Krisis", "Diastasis", "Orexis", "Chronos"]
    print(f"{'':>12}", end="")
    for s in series_names:
        print(f" {s[:6]:>7}", end="")
    print()
    for src in series_names:
        print(f"{src[:12]:>12}", end="")
        for tgt in series_names:
            cnt = series_bigrams.get((src, tgt), 0)
            print(f" {cnt:>7}", end="")
        print()


if __name__ == "__main__":
    main()
