from __future__ import annotations
# -*- coding: utf-8 -*-
# PROOF: Phantazein Reporter — IDE セッションレポートの動的生成
"""
PURPOSE: artifact_deep_analysis_ide_sessions レポートを Store のデータから動的に生成する。
v4 の構造 (§0-§7) を再現し、Markdown 文字列を返す。

依存: phantazein_store.py (get_session_cross_ref, get_session_timeline 等)
"""

import math
import re
import statistics
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from mekhane.symploke.phantazein_store import PhantazeinStore, get_store

# 除外ファイル名 (標準アーティファクト)
STANDARD_FILES = {
    "task.md",
    "implementation_plan.md",
    "walkthrough.md",
    ".metadata.json",
    ".resolved",
}

# 除外拡張子
EXCLUDED_EXTENSIONS = {".png", ".webp", ".jpg", ".jpeg", ".gif", ".json"}


def _ts_to_date(ts: float) -> str:
    """Unix timestamp を YYYY-MM-DD に変換する"""
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


def _ts_to_datetime(ts: float) -> str:
    """Unix timestamp を MM-DD HH:MM に変換する"""
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%m-%d %H:%M")


def _is_custom_artifact(filename: str) -> bool:
    """ファイルがカスタムアーティファクトかどうかを判定する"""
    if filename in STANDARD_FILES:
        return False
    ext = Path(filename).suffix.lower()
    if ext in EXCLUDED_EXTENSIONS:
        return False
    if not filename.endswith(".md"):
        return False
    return True


# MECE カテゴリ定義 — v5.0 互換 + Hyphē §8 Nucleator ルールベース版
# FEP 3操作に対応する macro 分類 (理論/実装/運用/戦略/監査/設計)
MECE_CATEGORIES = {
    "A": ("理論・公理検証", ["theory", "axiom", "kalon", "fep", "noe", "stoichei", "poiesis", "hyphe", "linkage"]),
    "B": ("コード実装", ["implement", "code", "refactor", "fix", "bug", "test", "migration"]),
    "C": ("品質評価・監査", ["quality", "audit", "review", "vet", "basanos", "dendron"]),
    "D": ("パイプライン設計", ["pipeline", "design", "architecture", "plan", "prd", "spec"]),
    "E": ("論文消化", ["paper", "digest", "eat", "gnosis", "survey", "literature"]),
    "F": ("UI/UX", ["ui", "ux", "frontend", "dashboard", "design_mockup"]),
    "G": ("インフラ", ["infra", "deploy", "server", "mcp", "ssh", "syncthing", "network"]),
    "H": ("メタ分析", ["meta", "analysis", "deep_analysis", "cross", "trend"]),
    "I": ("統合分析", ["synthesis", "integration", "boot", "report"]),
    "J": ("Hyphē/結晶化", ["hyphē", "crystal", "nucleat", "chunk", "field"]),
    "K": ("インフラ診断", ["crash_analysis", "crash", "diagnosis", "outage", "recovery", "health"]),
    "L": ("戦略・ビジョン", ["wish_vision", "strategy", "vision", "wish", "helm", "roadmap", "goal"]),
    "M": ("品質監査", ["self_audit", "rebuttal", "kalon_self", "assessment", "category_a", "stoicheia_coordinate"]),
    "N": ("システム設計", ["nous", "trinity", "batch_prompt", "ccl_nous"]),
}


# キーワード長の降順でソートしたルールリスト (長いキーワードを優先)
# 例: "kalon_self" (M) が "kalon" (A) より先にマッチする
_SORTED_RULES: list[tuple[str, str, str]] = sorted(
    [
        (code, label, kw)
        for code, (label, keywords) in MECE_CATEGORIES.items()
        for kw in keywords
    ],
    key=lambda x: -len(x[2]),
)


def _classify_artifact(filename: str, artifact_type: str = "") -> str:
    """アーティファクトを MECE カテゴリに分類する (Nucleator ルールベース版)

    キーワード長の降順でマッチするため、より具体的なキーワードが優先される。
    例: "kalon_self_audit" は M (品質監査) にマッチし、A (理論) にはマッチしない。

    Args:
        filename: ファイル名
        artifact_type: Store の artifact_type (theory, analysis, etc.)
    Returns:
        カテゴリコード (A-N) + ラベル。未分類なら "Z: その他"
    """
    name_lower = Path(filename).stem.lower()
    type_lower = (artifact_type or "").lower()
    combined = f"{name_lower} {type_lower}"

    # 長いキーワード優先でマッチ
    for code, label, kw in _SORTED_RULES:
        if kw in combined:
            return f"{code}: {label}"

    return "Z: その他"


# ── GAP-4: Handoff 品質スコアリング ──────────────────────────────

# 必須セクションヘッダー (SBAR 形式 — 部分一致で判定)
# 実データに準拠: handoff_2026-03-14_0930 (S/B/A/R), handoff_2026-03-15_2339 (📋/📊/✅/📌)
_HANDOFF_REQUIRED_SECTIONS = [
    ("状況", "📋"),       # Situation
    ("背景", "📊"),       # Background
    ("評価", "✅"),       # Assessment
    ("推奨", "📌"),       # Recommendation
]

# H(q) 品質段階の閾値 (L(c) と同構造)
HQ_THRESHOLDS = {
    "kalon": 0.75,   # ◎
    "ok": 0.50,      # ◯
    "improve": 0.30,  # △
    # < 0.30 → ✗
}

# 重み
HQ_WEIGHTS = {
    "struct": 0.30,
    "density": 0.25,
    "link": 0.20,
    "size": 0.15,
    "fresh": 0.10,
}


def _hq_grade(hq: float) -> str:
    """H(q) 値から品質段階を返す。"""
    if hq >= HQ_THRESHOLDS["kalon"]:
        return "◎"
    elif hq >= HQ_THRESHOLDS["ok"]:
        return "◯"
    elif hq >= HQ_THRESHOLDS["improve"]:
        return "△"
    return "✗"


def _score_handoff_struct(content: str) -> float:
    """構造完全性: 必須セクションの存在率 (0.0–1.0)。"""
    if not content:
        return 0.0
    content_lower = content.lower()
    found = 0
    for text_marker, emoji_marker in _HANDOFF_REQUIRED_SECTIONS:
        if text_marker.lower() in content_lower or emoji_marker in content:
            found += 1
    return found / len(_HANDOFF_REQUIRED_SECTIONS)


def _score_handoff_size(size_bytes: int) -> float:
    """サイズ適正: 2KB-8KB が最適帯。"""
    if size_bytes < 500:
        return 0.0
    elif size_bytes < 2000:
        return 0.5
    elif size_bytes <= 8000:
        return 1.0
    elif size_bytes <= 15000:
        return 0.7
    return 0.4


def _score_handoff_link(
    session_id: str | None,
    session_ids: set[str],
) -> float:
    """セッション紐づけスコア。"""
    if session_id and session_id in session_ids:
        return 1.0
    elif session_id:
        return 0.5  # ID はあるが session テーブルにない
    return 0.0


def _score_handoff_fresh(
    handoff_version: str | None,
    created_at: str | None = None,
) -> float:
    """鮮度スコア: handoff_version + 作成日からの経過日数。

    - version あり + 7日以内: 1.0
    - version あり + 30日以内: 0.8
    - version あり + 古い: 0.6
    - version なし: 0.3
    - version なし + 古い: 0.1
    """
    import datetime as _dt

    days = None
    if created_at:
        try:
            # Store は REAL (Unix timestamp) を返す場合がある
            if isinstance(created_at, (int, float)):
                dt = _dt.datetime.fromtimestamp(created_at, tz=_dt.timezone.utc)
            else:
                # "2026-03-15" or "2026-03-15T09:30:00" 形式
                dt = _dt.datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
            days = (_dt.datetime.now(_dt.timezone.utc) - dt).days
        except (ValueError, TypeError, OSError):
            days = None

    if handoff_version:
        if days is not None:
            if days <= 7:
                return 1.0
            elif days <= 30:
                return 0.8
            else:
                return 0.6
        return 0.8  # version あり、日付不明
    else:
        if days is not None and days > 30:
            return 0.1
        return 0.3


# 番号付きリスト検出 ("1." 〜 "999." 等)
_RE_ORDERED_LIST = re.compile(r"^\d+\.\s")
# チェックリスト検出 ("- [x]", "- [ ]")
_RE_CHECKLIST = re.compile(r"^-\s+\[.\]")


def _score_handoff_density(content: str) -> float:
    """内容密度: 情報要素 (テーブル行/箇条書き/コードブロック/チェックリスト) の比率。"""
    if not content:
        return 0.0
    lines = content.splitlines()
    total = len(lines) or 1
    info_elements = 0
    in_code_block = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            info_elements += 1
        elif stripped.startswith("|") and "|" in stripped[1:]:
            info_elements += 1  # テーブル行
        elif stripped.startswith(("- ", "* ")):
            info_elements += 1  # 箇条書き
        elif _RE_ORDERED_LIST.match(stripped):
            info_elements += 1  # 番号付きリスト (10. 以上も対応)
        elif _RE_CHECKLIST.match(stripped):
            info_elements += 1  # チェックリスト
    return min(1.0, info_elements / (total * 0.5))


def _score_handoff_quality(
    handoff: dict,
    session_ids: set[str],
    content: str | None = None,
) -> dict:
    """Handoff の品質を5軸でスコア化する。

    Args:
        handoff: Store から取得した handoff dict。
        session_ids: 既知の IDE session ID の集合。
        content: Handoff ファイルの内容 (None なら struct/density は中立 0.5)。

    Returns:
        {"struct": float, "size": float, "link": float,
         "fresh": float, "density": float, "total": float,
         "grade": str, "content_available": bool}
    """
    sid = handoff.get("session_id", "") or ""
    version = handoff.get("handoff_version", "") or ""
    size = handoff.get("size_bytes", 0) or 0
    created_at = handoff.get("created_at", "") or ""
    content_available = content is not None

    # 各軸スコア
    struct = _score_handoff_struct(content) if content_available else 0.5
    size_score = _score_handoff_size(size)
    link = _score_handoff_link(sid, session_ids)
    fresh = _score_handoff_fresh(version, created_at)
    density = _score_handoff_density(content) if content_available else 0.5

    # 重み付き合計
    total = (
        HQ_WEIGHTS["struct"] * struct
        + HQ_WEIGHTS["size"] * size_score
        + HQ_WEIGHTS["link"] * link
        + HQ_WEIGHTS["fresh"] * fresh
        + HQ_WEIGHTS["density"] * density
    )

    return {
        "struct": round(struct, 2),
        "size": round(size_score, 2),
        "link": round(link, 2),
        "fresh": round(fresh, 2),
        "density": round(density, 2),
        "total": round(total, 2),
        "grade": _hq_grade(total),
        "content_available": content_available,
    }


# L(c) 品質段階の閾値
LC_THRESHOLDS = {
    "kalon": 0.2,    # ◎ Kalon: Fix(G∘F) の近傍
    "ok": 0.4,       # ◯ 許容: 改善余地あり
    "improve": 0.6,  # △ 要改善: G (蒸留) が必要
    # > 0.6 → ✗ 違和感: 大幅な蒸留必要
}

# artifact_type → EFE 基本スコア
EFE_TYPE_SCORES = {
    "implementation_plan": 0.8,  # 行動を生む
    "task": 0.7,                 # 構造化された計画
    "walkthrough": 0.5,          # 記録だが再利用限定
    "other": 0.4,
}

# λ₁:λ₂ 比率 (Drift:EFE)
LC_LAMBDA_1 = 0.5  # Drift 重み
LC_LAMBDA_2 = 0.5  # EFE 重み


def _compute_drift_approx(
    artifact: dict, median_size: int,
) -> float:
    """Drift の近似値を計算する (embedding なし版の共通ロジック)。

    E-1 修正: _compute_lc_approx と _compute_lc_with_embedder で共通利用。

    Args:
        artifact: アーティファクト辞書 (size_bytes, mece_category, summary)。
        median_size: 全アーティファクトの中央値サイズ。
    Returns:
        drift 値 (0.0=不動点, 1.0=高ドリフト)。
    """
    size = artifact.get("size_bytes", 0) or 1
    median = max(median_size, 1)
    mece_cat = artifact.get("mece_category", "Z: その他")
    summary = artifact.get("summary", "") or ""

    # サイズの中央値からの対数乖離
    size_ratio = size / median
    size_penalty = abs(math.log2(max(size_ratio, 0.01))) * 0.15
    # MECE Z ペナルティ (分類不能 = 構造的に不安定)
    z_penalty = 0.2 if mece_cat.startswith("Z") else 0.0
    # summary 欠如ペナルティ (メタデータ欠如 = 構造不安定)
    summary_penalty = 0.15 if len(summary) == 0 else (-0.05 if len(summary) > 200 else 0.0)
    return min(1.0, size_penalty + z_penalty + summary_penalty)


def _compute_efe(
    artifact: dict, median_size: int, session_has_handoff: bool,
) -> float:
    """EFE (Expected Free Energy) の近似値を計算する。

    Args:
        artifact: アーティファクト辞書 (artifact_type, size_bytes)。
        median_size: 全アーティファクトの中央値サイズ。
        session_has_handoff: Handoff を持つセッションか。
    Returns:
        EFE 値 (0.0=展開不能, 1.0=最大展開)。
    """
    atype = artifact.get("artifact_type", "other")
    size = artifact.get("size_bytes", 0) or 1
    median = max(median_size, 1)

    efe_base = EFE_TYPE_SCORES.get(atype, 0.4)
    efe_size_bonus = 0.1 if size > median else 0.0
    efe_handoff_bonus = 0.1 if session_has_handoff else 0.0
    return min(1.0, efe_base + efe_size_bonus + efe_handoff_bonus)


def _lc_grade(lc: float) -> str:
    """L(c) 値から品質段階を返す。"""
    if lc <= LC_THRESHOLDS["kalon"]:
        return "◎"
    elif lc <= LC_THRESHOLDS["ok"]:
        return "◯"
    elif lc <= LC_THRESHOLDS["improve"]:
        return "△"
    return "✗"


def _compute_lc_approx(
    artifact: dict, median_size: int, session_has_handoff: bool
) -> dict:
    """L(c) 近似スコアを計算する (embedding なし版)

    Hyphē §3.6: L(c) = λ₁ · ‖G∘F(c) - c‖² + λ₂ · (-EFE(c))
    Drift を情報密度で、EFE を構造的メタデータで代替する。

    Args:
        artifact: アーティファクト辞書 (filename, size_bytes, artifact_type, mece_category, summary)
        median_size: 全アーティファクトの中央値サイズ
        session_has_handoff: セッションが Handoff を持つか
    Returns:
        {"drift": float, "efe": float, "lc": float, "grade": str}
    """
    drift = _compute_drift_approx(artifact, median_size)
    efe = _compute_efe(artifact, median_size, session_has_handoff)

    lc = LC_LAMBDA_1 * drift + LC_LAMBDA_2 * (1.0 - efe)
    lc = round(min(1.0, max(0.0, lc)), 3)

    return {"drift": round(drift, 3), "efe": round(efe, 3), "lc": lc, "grade": _lc_grade(lc)}


def _compute_drift_embedding(
    summaries: list[str],
    embedder: "EmbedderMixin",
    min_summaries: int = 3,
    min_summary_len: int = 30,
) -> list[float]:
    """全 summary の embedding 重心からのコサイン距離を Drift として計算する。

    Hyphē §3.6: Drift = ‖G∘F(c) - c‖² の近似。
    G∘F(c) ≈ 重心 (全 summary の平均 embedding)。
    距離 = 1 - cosine_sim(embed(summary), centroid)。

    Args:
        summaries: 全アーティファクトの summary リスト (空文字含む)。
        embedder: EmbedderMixin を実装したオブジェクト。
        min_summaries: embedding 計算に必要な最小 summary 数。
        min_summary_len: 有効な summary と判定する最小文字数。
    Returns:
        各 summary に対応する drift 値のリスト。
        summary が短い場合は -1.0 (フォールバック指示)。
        有効な summary が min_summaries 未満なら空リスト (全体フォールバック)。
    """
    # 有効な summary のインデックスを特定
    valid_indices = [i for i, s in enumerate(summaries) if len(s) >= min_summary_len]
    if len(valid_indices) < min_summaries:
        return []  # embedding 不十分 → 全体フォールバック

    # 有効な summary のみ embed
    valid_texts = [summaries[i] for i in valid_indices]
    try:
        vecs = embedder.embed_batch(valid_texts)
    except Exception:  # noqa: BLE001
        return []  # embedding 失敗 → フォールバック

    if not vecs or not vecs[0]:
        return []

    # 重心を計算
    dim = len(vecs[0])
    n = len(vecs)
    centroid = [sum(vecs[j][d] for j in range(n)) / n for d in range(dim)]

    # 重心のノルム
    norm_c = sum(x * x for x in centroid) ** 0.5
    if norm_c == 0:
        return []

    # 各有効 summary のドリフト
    valid_drifts = {}
    for idx, v in zip(valid_indices, vecs):
        dot = sum(a * b for a, b in zip(v, centroid))
        norm_v = sum(x * x for x in v) ** 0.5
        cos_sim = dot / (norm_v * norm_c) if norm_v > 0 else 0
        valid_drifts[idx] = round(1.0 - max(0.0, min(1.0, cos_sim)), 3)

    # 全 summary に対応する結果を構築 (無効 = -1.0 でフォールバック指示)
    return [valid_drifts.get(i, -1.0) for i in range(len(summaries))]


def _compute_lc_with_embedder(
    artifact: dict,
    median_size: int,
    session_has_handoff: bool,
    embedding_drift: float,
) -> dict:
    """embedding ベースの Drift を使って L(c) を計算する。

    EFE は既存のルールベース版を維持。
    Drift のみ embedding 値に置換。ただし embedding_drift が -1.0 の場合は
    既存の近似ペナルティも加算する。

    Args:
        artifact: アーティファクト辞書。
        median_size: 全アーティファクトのサイズ中央値。
        session_has_handoff: Handoff を持つセッションか。
        embedding_drift: embedding ベースのドリフト値 (-1.0 = フォールバック)。
    Returns:
        {"drift": float, "efe": float, "lc": float, "grade": str, "drift_source": str}
    """
    mece_cat = artifact.get("mece_category", "Z: その他")

    # Drift: embedding 値を使用。-1.0 の場合は共通近似関数にフォールバック
    if embedding_drift >= 0:
        drift = embedding_drift
        # MECE Z ペナルティは embedding 版でも適用
        if mece_cat.startswith("Z"):
            drift = min(1.0, drift + 0.1)
        drift_source = "embedding"
    else:
        # E-1 修正: 共通関数を使用 (DRY)
        drift = _compute_drift_approx(artifact, median_size)
        drift_source = "approx"

    # EFE: 共通関数を使用 (E-1 修正)
    efe = _compute_efe(artifact, median_size, session_has_handoff)

    # L(c)
    lc = LC_LAMBDA_1 * drift + LC_LAMBDA_2 * (1.0 - efe)
    lc = round(min(1.0, max(0.0, lc)), 3)

    return {
        "drift": round(drift, 3), "efe": round(efe, 3),
        "lc": lc, "grade": _lc_grade(lc), "drift_source": drift_source,
    }



# ── GAP-5: トレンド分析の統計的検定 ─────────────────────────


def _trend_slope(
    xs: list[float], ys: list[float]
) -> dict | None:
    """OLS 線形回帰 (標準ライブラリのみ)。

    Returns:
        {"slope": float, "intercept": float, "r_squared": float} or None
    """
    n = len(xs)
    if n < 2 or len(ys) != n:
        return None
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n

    ss_xy = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(xs, ys))
    ss_xx = sum((xi - x_mean) ** 2 for xi in xs)
    ss_yy = sum((yi - y_mean) ** 2 for yi in ys)

    if ss_xx == 0:
        return {"slope": 0.0, "intercept": y_mean, "r_squared": 0.0}

    slope = ss_xy / ss_xx
    intercept = y_mean - slope * x_mean
    r_squared = (ss_xy ** 2) / (ss_xx * ss_yy) if ss_yy > 0 else 0.0

    return {
        "slope": round(slope, 4),
        "intercept": round(intercept, 4),
        "r_squared": round(r_squared, 4),
    }


def _trend_mann_kendall(ys: list[float]) -> dict | None:
    """Mann-Kendall 傾向検定 (ノンパラメトリック)。

    正規近似 (N≥8)。N<3 は None を返す。
    Returns:
        {"S": int, "z": float, "p": float,
         "direction": "increasing"|"decreasing"|"no_trend"}
    """
    n = len(ys)
    if n < 3:
        return None

    # S 統計量の計算
    s = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            diff = ys[j] - ys[i]
            if diff > 0:
                s += 1
            elif diff < 0:
                s -= 1

    # 分散 (タイ補正なし簡易版)
    var_s = n * (n - 1) * (2 * n + 5) / 18.0

    # Z 統計量
    if s > 0:
        z = (s - 1) / math.sqrt(var_s) if var_s > 0 else 0.0
    elif s < 0:
        z = (s + 1) / math.sqrt(var_s) if var_s > 0 else 0.0
    else:
        z = 0.0

    # p 値 (正規近似 — erfc で両側検定)
    p = math.erfc(abs(z) / math.sqrt(2))

    # 傾向判定
    if p < 0.05:
        direction = "increasing" if s > 0 else "decreasing"
    else:
        direction = "no_trend"

    return {
        "S": s,
        "z": round(z, 4),
        "p": round(p, 4),
        "direction": direction,
    }


def _trend_change_point(ys: list[float]) -> dict | None:
    """単一変化点検出 (CUSUM ベース)。

    時系列を前半/後半に分割し、平均差が最大となる分割点を検出する。
    Returns:
        {"index": int, "before_mean": float, "after_mean": float,
         "magnitude": float} or None
    """
    n = len(ys)
    if n < 4:
        return None

    total_mean = sum(ys) / n
    best_idx = -1
    best_stat = 0.0

    # CUSUM 走査: 各分割点での平均差を評価
    for k in range(2, n - 1):
        before = ys[:k]
        after = ys[k:]
        before_mean = sum(before) / len(before)
        after_mean = sum(after) / len(after)
        # 効果量: 平均差の絶対値
        stat = abs(after_mean - before_mean)
        if stat > best_stat:
            best_stat = stat
            best_idx = k

    if best_idx < 0 or best_stat < 0.5:
        return None  # 閾値未満は報告しない

    before_mean = sum(ys[:best_idx]) / best_idx
    after_mean = sum(ys[best_idx:]) / (n - best_idx)

    return {
        "index": best_idx,
        "before_mean": round(before_mean, 2),
        "after_mean": round(after_mean, 2),
        "magnitude": round(best_stat, 2),
    }


def _trend_summary(timeline: list[dict]) -> str:
    """timeline データから統計サマリの Markdown を生成。"""
    sorted_tl = sorted(timeline, key=lambda d: d.get("day", ""))
    ys = [d.get("session_count", 0) for d in sorted_tl]
    xs = list(range(len(ys)))

    if len(ys) < 2:
        return "\n### 4-3. 統計サマリ\n\nデータ点が不足しています (2日以上必要)。\n"

    lines = [
        "",
        "### 4-3. 統計サマリ\n",
        "| 指標 | 値 | 解釈 |",
        "|:-----|:---|:-----|",
    ]

    # OLS 回帰
    ols = _trend_slope(xs, ys)
    if ols:
        slope_dir = "📈 増加" if ols["slope"] > 0.1 else "📉 減少" if ols["slope"] < -0.1 else "→ 横ばい"
        r2_qual = "強い" if ols["r_squared"] > 0.7 else "中程度" if ols["r_squared"] > 0.3 else "弱い"
        lines.append(
            f"| 線形傾き | {ols['slope']:+.2f} セッション/日 (R²={ols['r_squared']:.2f}) | {slope_dir} ({r2_qual}相関) |"
        )

    # Mann-Kendall
    mk = _trend_mann_kendall(ys)
    if mk:
        sig = f"p={mk['p']:.3f}" + (" ✓" if mk["p"] < 0.05 else "")
        dir_label = {"increasing": "有意な増加傾向", "decreasing": "有意な減少傾向", "no_trend": "有意な傾向なし"}
        lines.append(
            f"| Mann-Kendall | S={mk['S']}, z={mk['z']:.2f}, {sig} | {dir_label.get(mk['direction'], mk['direction'])} |"
        )

    # 変化点
    cp = _trend_change_point(ys)
    if cp:
        day_label = sorted_tl[cp["index"]].get("day", f"Day {cp['index']}")
        lines.append(
            f"| 変化点 | {day_label} (Δ={cp['magnitude']:.1f}) | "
            f"前半平均 {cp['before_mean']:.1f} → 後半平均 {cp['after_mean']:.1f} |"
        )

    # 基本統計量
    if ys:
        lines.extend([
            f"| 日数 | {len(ys)} 日 | — |",
            f"| セッション数合計 | {sum(ys)} | — |",
            f"| 日平均 | {sum(ys)/len(ys):.1f} | — |",
            f"| 最大 | {max(ys)} | — |",
            f"| 中央値 | {statistics.median(ys):.1f} | — |",
        ])

    return "\n".join(lines)

class PhantazeinReporter:
    """IDE セッションレポートの動的生成エンジン"""

    # PURPOSE: Store からデータを取得し、v4 構造のレポートを生成する

    def __init__(
        self,
        store: Optional[PhantazeinStore] = None,
        embedder: Optional["EmbedderMixin"] = None,
    ):
        self._store = store or get_store()
        # E-7 修正: embedder の型安全性チェック
        if embedder is not None and not hasattr(embedder, "embed_batch"):
            import warnings
            warnings.warn(
                f"embedder {type(embedder).__name__} に embed_batch メソッドがありません。"
                " embedding は無効化されます。",
                stacklevel=2,
            )
            embedder = None
        self._embedder = embedder

    def generate_report(
        self, days: int = 30, output_path: str = "", compact: bool = False
    ) -> str:
        """レポートを生成し、Markdown 文字列を返す。

        Args:
            days: 何日分のデータを対象にするか
            output_path: 非空ならファイルに書き出す
            compact: True なら MCP 応答制限対応の短縮版を生成
        Returns:
            生成された Markdown 文字列
        """
        # データ取得 (compact 時は不要なクエリを省略)
        cross_ref = self._store.get_session_cross_ref(limit=200, days=days)
        handoffs = self._store.get_recent_handoff_summaries(limit=100)
        timeline = [] if compact else self._store.get_session_timeline(days=days)
        roms = [] if compact else self._store.get_roms(limit=100)

        # カスタムアーティファクトの分離
        sessions_with_custom = []
        all_custom_artifacts = []
        sessions_standard_only = 0
        sessions_no_md = 0

        for session in cross_ref:
            customs = [
                a for a in session.get("artifacts", [])
                if _is_custom_artifact(a.get("filename", ""))
            ]
            if customs:
                sessions_with_custom.append({
                    **session,
                    "custom_artifacts": customs,
                })
                all_custom_artifacts.extend(customs)
            elif session.get("artifacts"):
                sessions_standard_only += 1
            else:
                sessions_no_md += 1

        # MECE 分類を付与
        for a in all_custom_artifacts:
            a["mece_category"] = _classify_artifact(
                a.get("filename", ""), a.get("artifact_type", "")
            )

        # L(c) 近似スコアを算出
        # E-2 修正: statistics.median を使用 (デフォルト 1000 = 平均的な .md ファイルサイズ)
        sizes = [a.get("size_bytes", 0) for a in all_custom_artifacts if a.get("size_bytes", 0) > 0]
        median_size = int(statistics.median(sizes)) if sizes else 1000

        # Handoff を持つセッションの ID セット
        handoff_session_ids = {h.get("session_id", "") for h in handoffs if h.get("session_id")}

        # Embedding ベース Drift を事前計算 (Embedder 有りの場合)
        embedding_drifts: list[float] = []
        if self._embedder:
            summaries = [a.get("summary", "") or "" for a in all_custom_artifacts]
            embedding_drifts = _compute_drift_embedding(summaries, self._embedder)

        for i, a in enumerate(all_custom_artifacts):
            sid = a.get("session_id", "")
            has_handoff = sid in handoff_session_ids
            # E-6 修正: embedding_drifts の長さガード
            if embedding_drifts and len(embedding_drifts) == len(all_custom_artifacts):
                # embedding 版
                a["lc_scores"] = _compute_lc_with_embedder(
                    a, median_size, has_handoff, embedding_drifts[i],
                )
            else:
                # 近似版 (フォールバック)
                a["lc_scores"] = _compute_lc_approx(a, median_size, has_handoff)

        # セクション生成
        # L(c) 値を事前計算 (compact/full 共通。重複排除)
        all_lc = [a.get("lc_scores", {}).get("lc", 0.5) for a in all_custom_artifacts]

        if compact:
            # コンパクトモード: MCP 応答制限対応
            # §0 サマリー + §2 MECE(テーブル) + §3 L(c)分布 + §7 メタ観察
            sections = [
                self._render_header(len(cross_ref), len(sessions_with_custom), len(all_custom_artifacts)),
                self._render_summary(
                    len(cross_ref),
                    len(sessions_with_custom),
                    len(all_custom_artifacts),
                    sessions_standard_only,
                    sessions_no_md,
                ),
                self._render_mece_compact(all_custom_artifacts),
                self._render_quality_compact(all_custom_artifacts, all_lc),
                self._render_meta_compact(all_custom_artifacts, all_lc),
            ]
        else:
            sections = [
                self._render_header(len(cross_ref), len(sessions_with_custom), len(all_custom_artifacts)),
                self._render_summary(
                    len(cross_ref),
                    len(sessions_with_custom),
                    len(all_custom_artifacts),
                    sessions_standard_only,
                    sessions_no_md,
                ),
                self._render_session_table(sessions_with_custom),
                self._render_rom_links(roms, sessions_with_custom),
                self._render_handoff_links(handoffs, sessions_with_custom),
                self._render_mece(all_custom_artifacts),
                self._render_quality(all_custom_artifacts, sessions_with_custom),
                self._render_trends(timeline, cross_ref),
                self._render_projects(sessions_with_custom),
                self._render_crosscut(all_custom_artifacts),
                self._render_meta(all_custom_artifacts),
            ]

        report = "\n\n---\n\n".join(sections)

        if output_path:
            Path(output_path).write_text(report, encoding="utf-8")

        return report

    def _render_header(
        self,
        total_sessions: int,
        custom_sessions: int,
        custom_count: int,
    ) -> str:
        """§ヘッダー"""
        today = datetime.now().strftime("%Y-%m-%d")
        return (
            f"# IDE セッション カスタムアーティファクト 深層分析レポート (自動生成)\n\n"
            f"> **対象**: `.gemini/antigravity/brain/` 配下 "
            f"{total_sessions}セッション → **{custom_sessions}セッション**に"
            f"**{custom_count}件**のカスタムアーティファクト\n"
            f"> **生成日**: {today} (Phantazein Reporter 自動生成)\n"
            f"> **配置**: `30_記憶｜Mneme/01_記録｜Records/d_成果物｜artifacts/`"
        )

    def _render_summary(
        self,
        total: int,
        custom_sessions: int,
        custom_count: int,
        standard_only: int,
        no_md: int,
    ) -> str:
        """§0 集計サマリー"""
        return (
            f"## 0. 集計サマリー\n\n"
            f"| 項目 | 件数 |\n"
            f"|:-----|:-----|\n"
            f"| 総セッション数 | {total} |\n"
            f"| カスタムF有りセッション | **{custom_sessions}** |\n"
            f"| カスタムF総数 | **{custom_count}** |\n"
            f"| 標準ファイルのみ | {standard_only} |\n"
            f"| .md なし | {no_md} |\n\n"
            f"**除外基準**: `task.md`, `implementation_plan.md`, `walkthrough.md`, "
            f"`.metadata.json`, `.resolved`, 画像ファイル"
        )

    def _render_session_table(self, sessions: list[dict]) -> str:
        """§1 セッション一覧"""
        lines = [
            "## 1. セッション × 関連資産 対応表\n",
            "### 1-1. セッション一覧 (作成日順)\n",
            "| セッション | 作成日時 | 件数 | 主要アーティファクト |",
            "|:-----------|:---------|:-----|:-------------------|",
        ]
        # 作成日時でソート
        sorted_sessions = sorted(sessions, key=lambda s: s.get("created_at", 0))
        for s in sorted_sessions:
            sid = s.get("id", "")[:8]
            created = _ts_to_datetime(s.get("created_at", 0))
            customs = s.get("custom_artifacts", [])
            count = len(customs)
            names = ", ".join(
                Path(a.get("filename", "")).stem for a in customs[:3]
            )
            if count > 3:
                names += f" (+{count - 3}件)"
            lines.append(f"| `{sid}` | {created} | {count} | {names} |")

        return "\n".join(lines)

    def _render_rom_links(self, roms: list[dict], sessions: list[dict]) -> str:
        """§1-2 ROM 紐づけ"""
        session_ids = {s.get("id", "") for s in sessions}
        lines = [
            "### 1-2. ROM 紐づけ (session_id マッチ)\n",
            "| ROM ファイル | マッチ先 |",
            "|:-------------|:---------|",
        ]
        matched = 0
        unmatched_roms = []
        for r in roms:
            fname = r.get("filename", "")
            sid = r.get("session_id", "")
            if sid and sid in session_ids:
                lines.append(f"| `{fname}` | **`{sid[:8]}`** ✓ |")
                matched += 1
            else:
                unmatched_roms.append(fname)

        if unmatched_roms:
            lines.append(f"\n**対象外 ROM** ({len(unmatched_roms)}件: 別セッション由来):")
            for u in unmatched_roms[:5]:
                lines.append(f"- `{u}`")
            if len(unmatched_roms) > 5:
                lines.append(f"- ... (+{len(unmatched_roms) - 5}件)")

        return "\n".join(lines)

    def _render_handoff_links(self, handoffs: list[dict], sessions: list[dict]) -> str:
        """§1-3 Handoff 紐づけ + 品質スコア (GAP-4)"""
        session_ids = {s.get("id", "") for s in sessions}
        # 全 IDE session の ID セット (品質スコアの link 判定用)
        all_session_ids = session_ids
        lines = [
            "### 1-3. Handoff 紐づけ + 品質\n",
            "> ✓=ID一致, ≈=日時近傍マッチ / H(q)=品質スコア\n",
            "| Handoff | 内容 | マッチ先 | H(q) | 段階 |",
            "|:--------|:-----|:---------|:-----|:-----|",
        ]
        matched_id = 0
        matched_dt = 0
        unmatched = 0
        hq_scores: list[float] = []
        grade_counts: dict[str, int] = {"◎": 0, "◯": 0, "△": 0, "✗": 0}

        for h in handoffs:
            fname = h.get("filename", "")
            title = h.get("title", "") or fname
            sid = h.get("session_id", "")
            if sid and sid in session_ids:
                match_label = f"**`{sid[:8]}`** ✓"
                matched_id += 1
            else:
                # 日時フォールバック: created_at で最も近いセッションを探す
                created_at = h.get("created_at")
                closest = None
                if created_at:
                    try:
                        closest = self._store.find_closest_session(created_at)
                    except Exception:  # noqa: BLE001
                        closest = None
                if closest and closest in session_ids:
                    match_label = f"**`{closest[:8]}`** ≈"
                    matched_dt += 1
                else:
                    match_label = "—"
                    unmatched += 1

            # Handoff ファイルの内容を読み取り (filepath があれば)
            content = None
            filepath = h.get("filepath", "")
            if filepath:
                try:
                    with open(filepath, encoding="utf-8") as f:
                        content = f.read()
                except (OSError, UnicodeDecodeError):
                    content = None

            # 品質スコア算出
            hq = _score_handoff_quality(h, all_session_ids, content)
            hq_scores.append(hq["total"])
            grade_counts[hq["grade"]] = grade_counts.get(hq["grade"], 0) + 1

            lines.append(
                f"| `{fname}` | {title[:50]} | {match_label} | {hq['total']:.2f} | {hq['grade']} |"
            )

        # マッチ統計 + 品質統計
        total = len(handoffs) or 1
        avg_hq = sum(hq_scores) / len(hq_scores) if hq_scores else 0.0
        lines.append(
            f"\n**紐づけ統計**: ID一致 {matched_id} / 日時 {matched_dt} / 未マッチ {unmatched} "
            f"(計 {len(handoffs)}, 率 {(matched_id + matched_dt) * 100 // total}%)"
        )
        lines.append(
            f"**品質統計**: 平均 H(q)={avg_hq:.2f} "
            f"(◎{grade_counts['◎']} / ◯{grade_counts['◯']} / △{grade_counts['△']} / ✗{grade_counts['✗']})"
        )

        return "\n".join(lines)

    def _render_mece(self, artifacts: list[dict]) -> str:
        """§2 MECE カテゴリ分類 (Nucleator ルールベース版)"""
        # カテゴリ別集計
        by_cat: dict[str, list[dict]] = defaultdict(list)
        for a in artifacts:
            cat = a.get("mece_category", "Z: その他")
            by_cat[cat].append(a)

        lines = [
            "## 2. MECE カテゴリ分類\n",
            "> Hyphē §8 Nucleator のルールベース版。"
            "ファイル名 + artifact_type のキーワードマッチで分類。\n",
            "### 2-1. カテゴリ別分布\n",
            "| カテゴリ | 件数 | 比率 | 総バイト |",
            "|:---------|:-----|:-----|:---------|",
        ]
        total = len(artifacts) or 1
        for cat in sorted(by_cat.keys()):
            items = by_cat[cat]
            count = len(items)
            pct = count * 100 // total
            total_bytes = sum(a.get("size_bytes", 0) for a in items)
            lines.append(f"| {cat} | {count} | {pct}% | {total_bytes:,} |")

        # カテゴリ別内訳 (件数 >= 2 のカテゴリのみ)
        lines.extend(["", "### 2-2. カテゴリ別内訳\n"])
        for cat in sorted(by_cat.keys()):
            items = by_cat[cat]
            if len(items) < 2:
                continue
            lines.append(f"**{cat}** ({len(items)}件):")
            for a in sorted(items, key=lambda x: x.get("size_bytes", 0), reverse=True):
                name = Path(a.get("filename", "")).stem
                size = a.get("size_bytes", 0)
                lines.append(f"- `{name}` ({size:,} bytes)")
            lines.append("")

        return "\n".join(lines)

    def _render_quality(
        self, artifacts: list[dict], sessions: list[dict]
    ) -> str:
        """§3 品質評価 (Phase 3.0: L(c) 近似スコア統合)"""
        lines = [
            "## 3. 品質評価\n",
            "### 3-0. 品質段階定義 (Hyphē §3.6 L(c) 近似)\n",
            "| 段階 | 記号 | L(c) 範囲 | 定義 |",
            "|:-----|:-----|:----------|:-----|",
            "| **Kalon** | ◎ | ≤ 0.2 | Fix(G∘F) — 発散と収束の不動点 |",
            "| **許容** | ◯ | 0.2-0.4 | 改善余地あるが実用的 |",
            "| **要改善** | △ | 0.4-0.6 | G (蒸留) が必要 |",
            "| **違和感** | ✗ | > 0.6 | 大幅な蒸留必要 |",
            "",
            "> L(c) = 0.5·Drift + 0.5·(1-EFE)。"
            "Drift=サイズ中央値からの乖離、EFE=タイプスコア+Handoff連携。\n",
        ]

        # §3-1 定量指標
        lines.append("### 3-1. 定量指標\n")
        total_bytes = sum(a.get("size_bytes", 0) for a in artifacts)
        lines.append(
            f"**全{len(artifacts)}件の総バイト数**: {total_bytes:,} bytes (≈{total_bytes // 1024} KB)\n"
        )

        # アーティファクトタイプ別集計
        by_type: dict[str, list[dict]] = defaultdict(list)
        for a in artifacts:
            atype = a.get("artifact_type", "other")
            by_type[atype].append(a)

        lines.extend([
            "| カテゴリ | 件数 | 総バイト | 平均 | 最大 |",
            "|:---------|:-----|:---------|:-----|:-----|",
        ])
        for atype, items in sorted(by_type.items(), key=lambda x: -sum(i.get("size_bytes", 0) for i in x[1])):
            count = len(items)
            total = sum(i.get("size_bytes", 0) for i in items)
            avg = total // count if count else 0
            max_item = max(items, key=lambda i: i.get("size_bytes", 0))
            max_name = Path(max_item.get("filename", "")).stem
            max_size = max_item.get("size_bytes", 0)
            lines.append(
                f"| {atype} | {count} | {total:,} | {avg:,} | {max_size:,} ({max_name}) |"
            )

        # §3-1.5 L(c) 品質分布
        grade_counts: dict[str, int] = defaultdict(int)
        grade_lcs: dict[str, list[float]] = defaultdict(list)
        for a in artifacts:
            scores = a.get("lc_scores", {})
            grade = scores.get("grade", "?")
            lc_val = scores.get("lc", 0.5)
            grade_counts[grade] += 1
            grade_lcs[grade].append(lc_val)

        lines.extend([
            "",
            "### 3-1.5. L(c) 品質分布\n",
            "| 段階 | 件数 | 比率 | 平均 L(c) |",
            "|:-----|:-----|:-----|:----------|",
        ])
        total_count = len(artifacts) or 1
        for grade_sym in ["◎", "◯", "△", "✗"]:
            cnt = grade_counts.get(grade_sym, 0)
            pct = cnt * 100 // total_count
            avg_lc = sum(grade_lcs.get(grade_sym, [0])) / max(cnt, 1)
            lines.append(f"| {grade_sym} | {cnt} | {pct}% | {avg_lc:.3f} |")

        # 全体平均
        all_lc = [a.get("lc_scores", {}).get("lc", 0.5) for a in artifacts]
        avg_all = sum(all_lc) / max(len(all_lc), 1)
        lines.append(f"\n**全体平均 L(c)**: {avg_all:.3f}")

        # §3-2 個別品質評価 (Top 10) — L(c) 列追加
        sorted_arts = sorted(artifacts, key=lambda a: a.get("size_bytes", 0), reverse=True)
        lines.extend([
            "",
            "### 3-2. 個別アーティファクト (Top 10 by size)\n",
            "| # | アーティファクト | バイト | タイプ | L(c) | 段階 | セッション |",
            "|:--|:----------------|:-------|:-------|:-----|:-----|:-----------|",
        ])
        for i, a in enumerate(sorted_arts[:10], 1):
            name = Path(a.get("filename", "")).stem
            size = a.get("size_bytes", 0)
            atype = a.get("artifact_type", "other")
            scores = a.get("lc_scores", {})
            lc_val = scores.get("lc", 0.5)
            grade = scores.get("grade", "?")
            sid = a.get("session_id", "")[:8]
            lines.append(f"| {i} | `{name}` | {size:,} | {atype} | {lc_val:.3f} | {grade} | `{sid}` |")

        # §3-3 セッション品質マトリクス (Top 10)
        sorted_sessions = sorted(
            sessions,
            key=lambda s: sum(a.get("size_bytes", 0) for a in s.get("custom_artifacts", [])),
            reverse=True,
        )
        lines.extend([
            "",
            "### 3-3. セッション別品質マトリクス (Top 10)\n",
            "| # | セッション | 件数 | 総バイト | タイトル |",
            "|:--|:-----------|:-----|:---------|:---------|",
        ])
        for i, s in enumerate(sorted_sessions[:10], 1):
            sid = s.get("id", "")[:8]
            customs = s.get("custom_artifacts", [])
            count = len(customs)
            total = sum(a.get("size_bytes", 0) for a in customs)
            title = s.get("title", "")[:40]
            lines.append(f"| {i} | `{sid}` | {count} | {total:,} | {title} |")

        return "\n".join(lines)


    def _render_trends(self, timeline: list[dict], cross_ref: list[dict]) -> str:
        """§4 トレンド分析"""
        lines = [
            "## 4. トレンド分析\n",
            "### 4-1. 時系列パターン\n",
            "```",
        ]
        for day in sorted(timeline, key=lambda d: d.get("day", "")):
            date = day.get("day", "")
            count = day.get("session_count", 0)
            arts = day.get("total_artifacts", 0) or 0
            bar = "█" * min(count * 2, 40)
            lines.append(f"{date} {bar:<40} {count}セッション / {arts}件")

        lines.append("```")

        # 日別テーマ分布
        by_day: dict[str, list[dict]] = defaultdict(list)
        for s in cross_ref:
            day = _ts_to_date(s.get("created_at", 0))
            by_day[day].append(s)

        lines.extend([
            "",
            "### 4-2. 日別セッション数\n",
            "| 日付 | セッション数 | タイトル例 |",
            "|:-----|:----------:|:-----------|",
        ])
        for day in sorted(by_day.keys()):
            sessions = by_day[day]
            count = len(sessions)
            titles = ", ".join(
                s.get("title", "")[:20] for s in sessions[:3]
            )
            if count > 3:
                titles += f" (+{count - 3}件)"
            lines.append(f"| {day} | {count} | {titles} |")

        # §4-3 統計サマリ (GAP-5)
        lines.append(_trend_summary(timeline))

        return "\n".join(lines)

    def _render_projects(self, sessions: list[dict]) -> str:
        """§5 PJ 紐づけ"""
        pj_map: dict[str, list[str]] = defaultdict(list)
        for s in sessions:
            for p in s.get("projects", []):
                pid = p.get("project_id", "") or p.get("name", "")
                for a in s.get("custom_artifacts", []):
                    pj_map[pid].append(Path(a.get("filename", "")).stem)

        lines = [
            "## 5. PJ 紐づけ\n",
            "| PJ | アーティファクト | 件数 |",
            "|:---|:----------------|:-----|",
        ]
        for pid in sorted(pj_map.keys(), key=lambda k: -len(pj_map[k])):
            arts = pj_map[pid]
            names = ", ".join(arts[:5])
            if len(arts) > 5:
                names += f" (+{len(arts) - 5}件)"
            lines.append(f"| `{pid}` | {names} | {len(arts)} |")

        if not pj_map:
            lines.append("| (紐づけなし) | — | 0 |")

        return "\n".join(lines)

    def _render_crosscut(self, artifacts: list[dict]) -> str:
        """§6 クロスカット分析"""
        lines = [
            "## 6. クロスカット分析\n",
            "### 6-1. サイズ分布\n",
        ]

        sizes = [a.get("size_bytes", 0) for a in artifacts if a.get("size_bytes", 0) > 0]
        if sizes:
            avg = sum(sizes) // len(sizes)
            median = sorted(sizes)[len(sizes) // 2]
            lines.extend([
                f"- 平均: {avg:,} bytes",
                f"- 中央値: {median:,} bytes",
                f"- 最大: {max(sizes):,} bytes",
                f"- 最小: {min(sizes):,} bytes",
            ])

        # タイプ別比率
        type_counts: dict[str, int] = defaultdict(int)
        for a in artifacts:
            type_counts[a.get("artifact_type", "other")] += 1

        lines.extend([
            "",
            "### 6-2. タイプ別比率\n",
            "| タイプ | 件数 | 比率 |",
            "|:-------|:-----|:-----|",
        ])
        total = len(artifacts) or 1
        for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
            pct = c * 100 // total
            lines.append(f"| {t} | {c} | {pct}% |")

        return "\n".join(lines)

    def _render_meta(self, artifacts: list[dict]) -> str:
        """§7 メタ観察 — G (蒸留) の出力

        L(c) スコアに基づき、Kalon アーティファクトの列挙と
        改善が必要なアーティファクトへの提案を行う。
        """
        lines = [
            "## 7. メタ観察 (G 蒸留)\n",
            "> Hyphē §3.6 L(c) に基づく品質の蒸留。"
            "◎ Kalon = Fix(G∘F) の近傍、✗ = 大幅な蒸留必要。\n",
        ]

        # ◎ Kalon 一覧
        kalons = [
            a for a in artifacts
            if a.get("lc_scores", {}).get("grade") == "◎"
        ]
        lines.append(f"### 7-1. ◎ Kalon アーティファクト ({len(kalons)}件)\n")
        if kalons:
            for a in sorted(kalons, key=lambda x: x.get("lc_scores", {}).get("lc", 1)):
                name = Path(a.get("filename", "")).stem
                lc_val = a.get("lc_scores", {}).get("lc", 0)
                cat = a.get("mece_category", "Z")
                lines.append(f"- `{name}` (L={lc_val:.3f}, {cat})")
        else:
            lines.append("(◎ 該当なし — 閾値 ≤ 0.2 を満たすアーティファクトがない)")

        # ✗ 改善候補一覧
        poor = [
            a for a in artifacts
            if a.get("lc_scores", {}).get("grade") == "✗"
        ]
        lines.extend(["", f"### 7-2. ✗ 改善候補 ({len(poor)}件)\n"])
        if poor:
            for a in sorted(poor, key=lambda x: x.get("lc_scores", {}).get("lc", 0), reverse=True):
                name = Path(a.get("filename", "")).stem
                scores = a.get("lc_scores", {})
                lc_val = scores.get("lc", 0)
                drift = scores.get("drift", 0)
                efe = scores.get("efe", 0)
                # 改善提案: Drift が高い → リファクタ、EFE が低い → 再利用性向上
                if drift > 0.5:
                    suggestion = "→ サイズを蒸留 (G を適用)"
                elif efe < 0.3:
                    suggestion = "→ 展開可能性を向上 (implementation_plan 化)"
                else:
                    suggestion = "→ 分類の見直し (MECE カテゴリ Z)"
                lines.append(f"- `{name}` (L={lc_val:.3f}, D={drift:.2f}, E={efe:.2f}) {suggestion}")
        else:
            lines.append("(✗ 該当なし)")

        # 全体サマリ
        all_lc = [a.get("lc_scores", {}).get("lc", 0.5) for a in artifacts]
        avg = sum(all_lc) / max(len(all_lc), 1)
        lines.extend([
            "",
            "### 7-3. 全体サマリ\n",
            f"- 全体平均 L(c): **{avg:.3f}**",
            f"- ◎ Kalon 率: **{len(kalons) * 100 // max(len(artifacts), 1)}%**",
            f"- ✗ 率: **{len(poor) * 100 // max(len(artifacts), 1)}%**",
        ])

        if avg <= 0.3:
            lines.append("- 💎 全体的に高品質。G∘F サイクルが機能している。")
        elif avg <= 0.5:
            lines.append("- 🔧 改善余地あり。△ アーティファクトの蒸留を優先。")
        else:
            lines.append("- ⚠️ 品質低下の兆候。分類体系と蒸留プロセスの再検討を推奨。")

        return "\n".join(lines)


    def _render_mece_compact(self, artifacts: list[dict]) -> str:
        """§2 MECE カテゴリ分類 (コンパクト版 — テーブルのみ)"""
        by_cat: dict[str, list[dict]] = defaultdict(list)
        for a in artifacts:
            cat = a.get("mece_category", "Z: その他")
            by_cat[cat].append(a)

        lines = [
            "## 2. MECE カテゴリ分類 (compact)\n",
            "| カテゴリ | 件数 | 比率 |",
            "|:---------|:-----|:-----|",
        ]
        total = len(artifacts) or 1
        for cat in sorted(by_cat.keys()):
            items = by_cat[cat]
            count = len(items)
            pct = count * 100 // total
            lines.append(f"| {cat} | {count} | {pct}% |")

        return "\n".join(lines)

    def _render_quality_compact(self, artifacts: list[dict], all_lc: list[float] | None = None) -> str:
        """§3 品質 L(c) 分布 (コンパクト版)

        Args:
            artifacts: アーティファクト一覧
            all_lc: 事前計算済み L(c) 値リスト (省略時は再計算)
        """
        grade_counts: dict[str, int] = defaultdict(int)
        grade_lcs: dict[str, list[float]] = defaultdict(list)
        for a in artifacts:
            scores = a.get("lc_scores", {})
            grade = scores.get("grade", "?")
            lc_val = scores.get("lc", 0.5)
            grade_counts[grade] += 1
            grade_lcs[grade].append(lc_val)

        lines = [
            "## 3. L(c) 品質分布 (compact)\n",
            "| 段階 | 件数 | 比率 | 平均 L(c) |",
            "|:-----|:-----|:-----|:----------|",
        ]
        total_count = len(artifacts) or 1
        for grade_sym in ["◎", "◯", "△", "✗"]:
            cnt = grade_counts.get(grade_sym, 0)
            pct = cnt * 100 // total_count
            avg_lc = sum(grade_lcs.get(grade_sym, [0])) / max(cnt, 1)
            lines.append(f"| {grade_sym} | {cnt} | {pct}% | {avg_lc:.3f} |")

        if all_lc is None:
            all_lc = [a.get("lc_scores", {}).get("lc", 0.5) for a in artifacts]
        avg_all = sum(all_lc) / max(len(all_lc), 1)
        lines.append(f"\n**全体平均 L(c)**: {avg_all:.3f}")

        return "\n".join(lines)

    def _render_meta_compact(self, artifacts: list[dict], all_lc: list[float] | None = None) -> str:
        """§7 メタ観察 (コンパクト版 — 全体サマリのみ)

        Args:
            artifacts: アーティファクト一覧
            all_lc: 事前計算済み L(c) 値リスト (省略時は再計算)
        """
        if all_lc is None:
            all_lc = [a.get("lc_scores", {}).get("lc", 0.5) for a in artifacts]
        avg = sum(all_lc) / max(len(all_lc), 1)
        kalons = [a for a in artifacts if a.get("lc_scores", {}).get("grade") == "◎"]
        poor = [a for a in artifacts if a.get("lc_scores", {}).get("grade") == "✗"]

        lines = [
            "## 7. メタ観察 (compact)\n",
            f"- 全体平均 L(c): **{avg:.3f}**",
            f"- ◎ Kalon 率: **{len(kalons) * 100 // max(len(artifacts), 1)}%** ({len(kalons)}件)",
            f"- ✗ 率: **{len(poor) * 100 // max(len(artifacts), 1)}%** ({len(poor)}件)",
        ]

        if avg <= 0.3:
            lines.append("- 💎 全体的に高品質。")
        elif avg <= 0.5:
            lines.append("- 🔧 改善余地あり。△ アーティファクトの蒸留を優先。")
        else:
            lines.append("- ⚠️ 品質低下の兆候。分類体系の再検討を推奨。")

        # ✗ 候補 (上位3件のみ)
        if poor:
            lines.append("\n**✗ 改善候補 (Top 3)**:")
            for a in sorted(poor, key=lambda x: x.get("lc_scores", {}).get("lc", 0), reverse=True)[:3]:
                name = Path(a.get("filename", "")).stem
                lc_val = a.get("lc_scores", {}).get("lc", 0)
                lines.append(f"- `{name}` (L={lc_val:.3f})")

        return "\n".join(lines)


def generate_report(
    days: int = 30,
    output_path: str = "",
    store: Optional[PhantazeinStore] = None,
    compact: bool = False,
) -> str:
    """公開API: レポートを生成する

    Args:
        days: 対象日数 (デフォルト30日)
        output_path: 出力先パス (空ならファイル出力しない)
        store: 既存の Store インスタンス (テスト用)
        compact: True なら MCP 応答制限対応の短縮版
    Returns:
        生成された Markdown 文字列
    """
    reporter = PhantazeinReporter(store=store)
    return reporter.generate_report(days=days, output_path=output_path, compact=compact)
