#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/symploke/ A0→継続する私が必要→boot_integration が担う
"""
Boot Integration - 22軸を統合した /boot 用 API

Axes:
  A. Handoff   B. Sophia/KI   C. Persona   D. PKS
  E. Safety    F. Attractor   G. GPU       H. EPT
  I. Projects  J. Skills      K. Doxa      L. Credit
  M. Explanation Stack  N. Ideas (HGK Gateway)

Theorem Coverage:
  全24動詞 (T1-T4, M1-M4, K1-K4, D1-D4, O1-O4, C1-C4) を
  TheoremAttractor + THEOREM_REGISTRY 経由で Boot 時にアクセス可能。

  SOURCE: axiom_hierarchy.md v4.2 §Poiesis (L320-L361)。
  6族 = Flow × 6修飾座標。4極 = I×{+極}, I×{-極}, A×{+極}, A×{-極}。

  FEP 的理想: このレジストリは Kernel (axiom_hierarchy.md) から
  動的に導出されるべきであり、ハードコードは暫定措置。
  Kernel が変われば THEOREM_REGISTRY も自動的に変わる世界が理想。
  TODO: Kernel YAML / JSON からの動的ロードに移行する。

Usage:
    python boot_integration.py                    # 標準起動
    python boot_integration.py --mode fast        # 高速起動
    python boot_integration.py --mode detailed    # 詳細起動
    python boot_integration.py --postcheck /tmp/boot_report.md --mode detailed  # ポストチェック
"""

from mekhane.paths import MNEME_STATE
import os
import re
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from mekhane.fep.mapping import POIESIS_VERBS

# ── 48 Operations Registry (v5.4 core) ──
# PURPOSE: 57実体体系 (axiom_hierarchy.md v5.4) の全48操作を Boot 時に参照可能にする
# SOURCE: axiom_hierarchy.md §Poiesis — 6族×6極 = 36動詞
_SERIES_COORD = {
    "Value": "T", "Function": "M", "Precision": "K",
    "Scale": "D", "Valence": "O", "Temporality": "C"
}
def _component_to_num(verb):
    # Mapping to numbers 1-6
    if verb.flow_pole == "I":
        return "1" if verb.helmholtz_component.name == "SOLENOIDAL" else "2"
    elif verb.flow_pole == "A":
        return "3" if verb.helmholtz_component.name == "SOLENOIDAL" else "4"
    else: # flow_pole == "S"
        return "5" if verb.helmholtz_component.name == "SOLENOIDAL" else "6"

_POIESIS_SORTED = sorted(POIESIS_VERBS.values(), key=lambda v: (_SERIES_COORD.get(v.coordinate, "X"), _component_to_num(v)))

THEOREM_REGISTRY: dict[str, dict] = {
    f"{_SERIES_COORD.get(v.coordinate, 'X')}{_component_to_num(v)}": {
        "name": v.greek_name,
        "series": _SERIES_COORD.get(v.coordinate, "X"),
        "wf": f"/{v.ccl_name}",
        "level": "d3" if v.coordinate in ["Scale", "Valence"] else "d2",
        "ja": v.japanese_name,
        "pole": f"{v.flow_pole}×{v.helmholtz_component.name[0]}"
    }
    for v in _POIESIS_SORTED
}


# 族メタデータ (Boot サマリー用)
# シリーズコードは各族の Peras WF (/t /m /k /d /o /c) と整合
SERIES_INFO = {
    "T": "Telos (目的)", "M": "Methodos (戦略)", "K": "Krisis (判断)",
    "D": "Diástasis (拡張)", "O": "Orexis (欲求)", "C": "Chronos (時間)",
}



# PURPOSE: Extract Dispatcher dispatch plan from context
def extract_dispatch_info(context: str, gpu_ok: bool = True) -> dict:
    """Extract Dispatcher dispatch plan from context.

    Graceful degradation: returns empty-primary dict on any failure.
    Separated from _run_attractor() for testability (dia+ issue #1).
    """
    dispatch_info = {"primary": "", "alternatives": [], "dispatch_formatted": ""}
    try:
        from mekhane.fep.attractor_dispatcher import AttractorDispatcher
        dispatcher = AttractorDispatcher(force_cpu=not gpu_ok)
        plan = dispatcher.dispatch(context)
        if plan:
            dispatch_info = {
                "primary": plan.primary.workflow,
                "alternatives": [d.workflow for d in plan.alternatives[:3]],
                "dispatch_formatted": dispatcher.format_compact(plan),
            }
    except Exception:  # noqa: BLE001
        pass  # Dispatcher failure should not block boot
    return dispatch_info


# PURPOSE: [L2-auto] _load_projects の関数定義
def _load_projects(project_root: Path) -> dict:
    """Load project registry from nous/projects/registry.yaml.

    Returns:
        dict: {
            "projects": [...],   # 全プロジェクト
            "active": int,
            "dormant": int,
            "total": int,
            "formatted": str     # フォーマット済み出力
        }
    """
    result = {"projects": [], "active": 0, "dormant": 0, "total": 0, "formatted": ""}
    # POMDP Nous 再構築で nous/ → 10_知性｜Nous/, projects/ → 04_企画｜Boulēsis/ に移動
    registry_path = project_root / "10_知性｜Nous" / "04_企画｜Boulēsis" / "00_舵｜Helm" / "registry.yaml"
    if not registry_path.exists():
        return result

    try:
        import yaml
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        projects = data.get("projects", [])
        if not projects:
            return result

        active = [p for p in projects if p.get("status") == "active"]
        dormant = [p for p in projects if p.get("status") == "dormant"]
        archived = [p for p in projects if p.get("status") == "archived"]

        lines = ["📦 **Projects** (registry.yaml)"]
        # Group by category based on path patterns
        categories = {
            "コアランタイム": [],
            "Mekhane モジュール": [],
            "理論・言語基盤": [],
            "研究・概念": [],
            "補助": [],
        }
        for p in projects:
            path = p.get("path", "")
            status = p.get("status", "")
            if status == "archived":
                categories["補助"].append(p)
            elif path.startswith("mekhane/"):
                categories["Mekhane モジュール"].append(p)
            elif path.startswith(".") or p.get("id") in ("kalon", "aristos", "autophonos"):
                categories["研究・概念"].append(p)
            elif p.get("id") in ("ccl", "kernel", "pepsis"):
                categories["理論・言語基盤"].append(p)
            elif p.get("id") in ("hgk",):
                categories["補助"].append(p)
            else:
                categories["コアランタイム"].append(p)

        status_icons = {"active": "🟢", "dormant": "💤", "archived": "🗄️", "planned": "📋"}
        for cat_name, cat_projects in categories.items():
            if not cat_projects:
                continue
            lines.append(f"  [{cat_name}]")
            for p in cat_projects:
                icon = status_icons.get(p.get("status", ""), "❓")
                name = p.get("name", p.get("id", "?"))
                phase = p.get("phase", "")
                summary = p.get("summary", "")
                if len(summary) > 50:
                    summary = summary[:50] + "..."
                line = f"    {icon} {name} [{phase}] — {summary}"
                # entry_point: CLI があれば表示
                ep = p.get("entry_point")
                if ep and isinstance(ep, dict):
                    cli = ep.get("cli", "")
                    if cli:
                        line += f"\n       📎 `{cli}`"
                lines.append(line)
                # usage_trigger: 利用条件を表示
                trigger = p.get("usage_trigger", "")
                if trigger and p.get("status") == "active":
                    lines.append(f"       ⚡ {trigger}")

        lines.append(f"  統計: {len(projects)}件 / Active {len(active)} / Dormant {len(dormant)} / Archived {len(archived)}")

        result = {
            "projects": projects,
            "active": len(active),
            "dormant": len(dormant),
            "total": len(projects),
            "formatted": "\n".join(lines),
        }
    except Exception:  # noqa: BLE001
        pass  # Registry loading failure should not block boot

    return result


# PURPOSE: /boot 起動時に全 Skill を発見し、Agent がコンテキストに取り込めるようにする
def _load_skills(project_root: Path) -> dict:
    """Load all Skills from nous/skills/ for boot preloading.

    Returns:
        dict: {
            "skills": [{name, path, description}, ...],
            "count": int,
            "skill_paths": [str, ...],   # view_file 用の絶対パス一覧
            "formatted": str
        }
    """
    result = {"skills": [], "count": 0, "skill_paths": [], "formatted": ""}
    skills_dir = project_root / "10_知性｜Nous" / "02_手順｜Procedures" / "C_技能｜Skills"
    if not skills_dir.exists():
        return result

    try:
        import yaml  # ループ外で1回だけインポート

        skills = []
        skill_paths = []
        for skill_dir in sorted(skills_dir.iterdir()):
            skill_md = skill_dir / "SKILL.md"
            if not skill_dir.is_dir() or not skill_md.exists():
                continue

            # YAML frontmatter からメタデータのみ抽出
            content = skill_md.read_text(encoding="utf-8")
            name = skill_dir.name
            description = ""
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    try:
                        meta = yaml.safe_load(parts[1])
                        name = meta.get("name", skill_dir.name)
                        description = meta.get("description", "")
                    except Exception:  # noqa: BLE001
                        pass

            abs_path = str(skill_md.resolve())
            skills.append({
                "name": name,
                "dir": skill_dir.name,
                "path": abs_path,
                "description": description,
            })
            skill_paths.append(abs_path)

        if not skills:
            return result

        # 行為可能性のみ出力。全文は Agent が view_file で個別取得する
        # 旧実装: body 全文埋め込み → 872KB → MCP レスポンス超過で boot 失敗
        lines = [f"🧠 **Skills** ({len(skills)}件)"]
        for s in skills:
            desc = f" — {s['description']}" if s['description'] else ""
            lines.append(f"  📖 {s['name']}{desc}")
            lines.append(f"     `{s['path']}`")

        result = {
            "skills": skills,
            "count": len(skills),
            "skill_paths": skill_paths,
            "formatted": "\n".join(lines),
        }
    except Exception:  # noqa: BLE001
        pass  # Skill loading failure should not block boot

    return result


# ── Always-On Boot: 計算軸の定義 ──
# ファイル監視では検知できない「計算由来」の軸。
# TTL ベースの自然 stale でのみ更新される。
_COMPUTED_AXES: set[str] = {
    "attractor",      # GPU/FEP 計算
    "ept",            # DB クエリ (Embedding Performance)
    "proactive_push", # 通知キュー (動的生成)
    "ideas",          # LLM 生成
    "episodic_memory", # DB クエリ (記憶検索)
    "identity",       # LLM 生成
    "bc_violations",  # JSONL ファイル (sympatheia 管轄)
}


# ── Always-On Boot: 軸→監視ディレクトリのマッピング ──
# watchdog がファイル変更を検知した際、変更されたディレクトリから
# 影響を受ける軸キーを特定するために使用する。
# 注: _COMPUTED_AXES は含まれない (ファイル監視では検知不可)。
def _get_axis_dir_map() -> dict[str, list[str]]:
    """軸キー → 監視対象ディレクトリパスのマッピングを返す。"""
    from mekhane.paths import (
        HANDOFF_DIR, ROM_DIR, INCOMING_DIR, MNEME_STATE,
    )
    _project_root = Path(__file__).parent.parent.parent
    _nous = _project_root / "10_知性｜Nous"
    _constraints = _nous / "01_制約｜Constraints"
    _episteme = _nous / "03_知識｜Epistēmē"
    _boulesis = _nous / "04_企画｜Boulēsis"
    return {
        "handoffs": [str(HANDOFF_DIR)],
        "ki": [str(_episteme)],
        "persona": [str(_constraints)],
        "pks": [str(_episteme)],
        "safety": [str(_constraints)],
        "projects": [str(_boulesis)],
        "helm": [str(_boulesis / "00_舵｜Helm")],
        "skills": [str(_nous / "02_手順｜Procedures" / "C_技能｜Skills")],
        "doxa": [str(MNEME_STATE)],
        "feedback": [str(MNEME_STATE)],
        "incoming": [str(INCOMING_DIR)],
        "digestor": [str(INCOMING_DIR)],
        "session_resume": [str(ROM_DIR)],
        "state_space": [str(MNEME_STATE)],
        "wal": [str(ROM_DIR)],
    }


def _dir_to_axes() -> dict[str, list[str]]:
    """監視ディレクトリ → 影響を受ける軸キーの逆引きマッピング。"""
    reverse: dict[str, list[str]] = {}
    for axis, dirs in _get_axis_dir_map().items():
        for d in dirs:
            reverse.setdefault(d, []).append(axis)
    return reverse


# ── Always-On Boot: 全軸名の定義 ──
BOOT_AXIS_KEYS = [
    "handoffs", "ki", "persona", "pks", "safety", "ept",
    "digestor", "attractor", "projects", "helm", "skills",
    "doxa", "feedback", "proactive_push", "ideas",
    "session_resume", "state_space", "episodic_memory",
    "identity", "wal", "incoming", "bc_violations",
]

# デフォルトキャッシュ TTL (秒)
BOOT_CACHE_TTL = 300.0


# PURPOSE: /boot 統合 API: キャッシュ優先で boot context を返す (Always-On Boot)
def get_boot_context(mode: str = "standard", context: Optional[str] = None) -> dict:
    """
    /boot 統合 API — Always-On Boot (キャッシュ優先)。

    1. SQLite キャッシュを読み出す (< 50ms)
    2. キャッシュが空 or 全 stale → _full_boot_load() でフルロード → キャッシュに書込
    3. API の戻り値は従来と完全互換

    Args:
        mode: "fast" (/boot-), "standard" (/boot), "detailed" (/boot+)
        context: 現在のコンテキスト（Handoff の主題など）

    Returns:
        dict: 各軸の結果 + "formatted" キーにフォーマット済み出力
    """
    from mekhane.symploke.phantazein_store import get_store

    try:
        store = get_store()
        cached = store.get_cached_boot_context(mode)
        if cached and not cached.get("all_stale"):
            # キャッシュヒット — 即座に返す
            import logging
            meta = cached.get("_cache_meta", {})
            logging.info(
                "Boot cache HIT: mode=%s, fresh=%d/%d",
                mode, meta.get("fresh", 0), meta.get("total", 0),
            )
            return cached
    except Exception:  # noqa: BLE001
        pass  # キャッシュ失敗時は従来のフルロードにフォールバック

    # キャッシュミス — 従来のフルロードを実行
    result = _full_boot_load(mode, context)

    # キャッシュに書き込む (非ブロッキング: 失敗しても boot は返す)
    try:
        store = get_store()
        for axis_key in BOOT_AXIS_KEYS:
            axis_data = result.get(axis_key)
            if axis_data is not None and isinstance(axis_data, dict):
                formatted = axis_data.get("formatted", "")
                store.update_boot_cache(
                    axis_key=axis_key,
                    mode=mode,
                    data=axis_data,
                    formatted=formatted,
                    ttl_sec=BOOT_CACHE_TTL,
                )
    except Exception:  # noqa: BLE001
        pass  # キャッシュ書込失敗は致命的でない

    return result


# ── Always-On Boot: 軸単位ローダーレジストリ ──
# 各軸キー → (load_function, requires_context) のマッピング。
# refresh_boot_cache が対象軸だけを個別にロードするために使用。
# _full_boot_load からのフルロードは不要になる。
def _get_axis_loaders() -> dict[str, tuple]:
    """軸キー → (ローダー関数, kwarg名リスト) のレジストリを返す。

    遅延 import で循環参照を回避。
    返り値のタプル: (callable, list[str])
      callable: (mode, context, **extra) シグネチャのローダー
      list[str]: 追加キーワード引数の名前 (空ならなし)
    """
    from mekhane.symploke.boot_axes import (
        load_handoffs, load_sophia, load_persona, load_pks,
        load_safety, load_ept, load_digestor, load_attractor,
        load_projects, load_helm, load_skills, load_doxa, load_feedback,
        load_proactive_push, load_ideas, load_state_space,
        load_episodic_memory, load_identity, load_session_resume,
    )
    return {
        "handoffs": (load_handoffs, []),
        "ki": (load_sophia, ["ki_context"]),
        "persona": (load_persona, []),
        "pks": (load_pks, ["ki_context"]),
        "safety": (load_safety, []),
        "ept": (load_ept, []),
        "digestor": (load_digestor, []),
        "attractor": (load_attractor, ["gpu_ok"]),
        "projects": (load_projects, []),
        "helm": (load_helm, []),
        "skills": (load_skills, []),
        "doxa": (load_doxa, []),
        "feedback": (load_feedback, []),
        "proactive_push": (load_proactive_push, []),
        "ideas": (load_ideas, []),
        "session_resume": (load_session_resume, []),
        "state_space": (load_state_space, []),
        "episodic_memory": (load_episodic_memory, []),
        "identity": (load_identity, []),
    }


# PURPOSE: 指定軸のみ再計算してキャッシュを更新する (watchdog から呼ばれる)
def refresh_boot_cache(
    axis_keys: Optional[list[str]] = None,
    mode: str = "standard",
    context: Optional[str] = None,
) -> dict:
    """指定軸のキャッシュを再計算して更新する。

    矛盾 #1 修正: _full_boot_load (全軸) ではなく、
    軸単位ローダーで対象軸だけを個別にロードする。

    Args:
        axis_keys: 再計算する軸キーのリスト。None なら全軸。
        mode: boot モード。
        context: オプショナルなコンテキスト。

    Returns:
        更新結果のサマリー dict。
    """
    import logging
    from mekhane.symploke.phantazein_store import get_store

    if axis_keys is None:
        axis_keys = list(BOOT_AXIS_KEYS)

    loaders = _get_axis_loaders()
    store = get_store()
    updated = 0
    errors: list[str] = []

    for axis_key in axis_keys:
        loader_entry = loaders.get(axis_key)
        if loader_entry is None:
            # wal, incoming, bc_violations は専用ロジック。スキップ
            logging.debug("refresh_boot_cache: %s はレジストリにないのでスキップ", axis_key)
            continue

        load_fn, extra_kwargs = loader_entry
        try:
            # 各ローダーは (mode, context, **extra) シグネチャ
            # extra kwargs は ki_context, gpu_ok など — 簡易フォールバック値を渡す
            kwargs: dict = {}
            if "ki_context" in extra_kwargs:
                kwargs["ki_context"] = context or ""
            if "gpu_ok" in extra_kwargs:
                kwargs["gpu_ok"] = True  # watcher 呼び出し時は GPU チェックを省略

            axis_data = load_fn(mode, context, **kwargs)

            if axis_data is not None and isinstance(axis_data, dict):
                formatted = axis_data.get("formatted", "")
                store.update_boot_cache(
                    axis_key=axis_key,
                    mode=mode,
                    data=axis_data,
                    formatted=formatted,
                    ttl_sec=BOOT_CACHE_TTL,
                )
                updated += 1
        except Exception as e:  # noqa: BLE001
            logging.warning("refresh_boot_cache: %s のロードに失敗: %s", axis_key, e)
            errors.append(f"{axis_key}: {e}")

    return {
        "updated": updated,
        "requested": len(axis_keys),
        "errors": errors,
        "mode": mode,
    }


# ── 軸ロード制御 ──
# PURPOSE: 各軸ロードの例外ハンドリング + タイムアウト定数
# タイムアウト制御は _full_boot_load の ThreadPoolExecutor.future.result() に一元化
# load_sophia / load_attractor は内部に独自タイムアウトを持つ (防御層として維持)
_AXIS_TIMEOUT_PRIOR: float = 15.0  # 軸別タイムアウトの prior (秒)
_HEAVY_AXIS_TIMEOUT_PRIOR: float = 30.0  # 重い軸の prior タイムアウト
_TIMEOUT_BUFFER: float = 1.2  # タイムアウト = p95 × このバッファ
# load_pks は内部 future.result(timeout=10.0) — wave の wait 秒数がこれ未満だと PKS だけ打ち切られる
_MIN_TIMEOUT: float = 12.0  # 最低タイムアウト (どんなに速くてもこれ未満にはしない)
# 信念 (prior): 観測データがない軸のフォールバック分類
# → 十分な観測データがある軸は _classify_axes_adaptive() で posterior に更新される
_HEAVY_AXES_PRIOR: set[str] = {"attractor", "proactive_push", "ept", "episodic_memory", "identity", "ideas"}
# 適応的分類の閾値 prior (観測データから再計算される)
_HEAVY_THRESHOLD_PRIOR: float = _AXIS_TIMEOUT_PRIOR * 0.6  # 9.0s


def _derive_threshold(profiles: dict[str, dict]) -> float:
    """全軸の中央値分布から heavy/light 閾値を適応的に導出する。

    Otsu 的 2クラス分離: 全中央値を昇順ソートし、
    各候補閾値でクラス内分散が最小になる点を選ぶ。
    データが少ない場合は prior にフォールバック。

    自己言及レベル: 閾値が自身の観測データから生まれる。
    """
    medians = [p["median"] for p in profiles.values() if p["count"] >= 2]
    if len(medians) < 3:
        return _HEAVY_THRESHOLD_PRIOR

    sorted_m = sorted(medians)
    best_threshold = _HEAVY_THRESHOLD_PRIOR
    best_score = float("inf")

    for i in range(1, len(sorted_m)):
        lo = sorted_m[:i]
        hi = sorted_m[i:]
        # クラス内分散の重み付き和
        if len(lo) < 1 or len(hi) < 1:
            continue
        mean_lo = sum(lo) / len(lo)
        mean_hi = sum(hi) / len(hi)
        var_lo = sum((x - mean_lo) ** 2 for x in lo) / len(lo)
        var_hi = sum((x - mean_hi) ** 2 for x in hi) / len(hi)
        score = len(lo) * var_lo + len(hi) * var_hi
        if score < best_score:
            best_score = score
            best_threshold = (sorted_m[i - 1] + sorted_m[i]) / 2

    # 最低でも 3.0s、最大で 20.0s に制約
    return max(3.0, min(best_threshold, 20.0))


def _derive_timeouts(profiles: dict[str, dict]) -> tuple[float, float]:
    """過去の p95 からタイムアウトを適応的に導出する。

    自己言及レベル: タイムアウト値が自身の過去パフォーマンスから生まれる。

    Returns:
        (light_timeout, heavy_timeout)
    """
    light_times: list[float] = []
    heavy_times: list[float] = []
    threshold = _derive_threshold(profiles) if profiles else _HEAVY_THRESHOLD_PRIOR

    for name, p in profiles.items():
        if p["count"] < 2:
            continue
        if p["median"] > threshold:
            heavy_times.append(p["p95"])
        else:
            light_times.append(p["p95"])

    def _calc(times: list[float], prior: float) -> float:
        if not times:
            return prior
        p95 = max(times)
        adapted = p95 * _TIMEOUT_BUFFER
        return max(_MIN_TIMEOUT, adapted)

    return _calc(light_times, _AXIS_TIMEOUT_PRIOR), _calc(heavy_times, _HEAVY_AXIS_TIMEOUT_PRIOR)


# ── G∘F 3周目 (L4): 適応的観測窓 ──
_OBS_WINDOW_PRIOR: int = 10  # last_n の prior
_OBS_WINDOW_MIN: int = 5  # 最小観測窓
_OBS_WINDOW_MAX: int = 30  # 最大観測窓
_CV_THRESHOLD: float = 0.3  # CVがこれ以上なら「不安定」


def _derive_observation_windows(profiles: dict[str, dict]) -> dict[str, int]:
    """各軸の変動係数 (CV) に基づいて観測窓幅を適応的に導出する。

    CV 高 (不安定) → 窓を広げて推定を安定化
    CV 低 (安定)   → 窓を狭めて最新トレンドを追従

    自己言及レベル: 「どれだけ過去を見るか」が自身の安定性から生まれる。
    """
    windows: dict[str, int] = {}
    for name, p in profiles.items():
        cv = p.get("cv", 0.0)
        count = p.get("count", 0)
        if count < 2:
            windows[name] = _OBS_WINDOW_PRIOR
            continue

        # CV が高いほど窓を広げる (線形マッピング)
        # cv=0 → _OBS_WINDOW_MIN, cv=_CV_THRESHOLD*2 → _OBS_WINDOW_MAX
        ratio = min(cv / (_CV_THRESHOLD * 2), 1.0)
        window = int(_OBS_WINDOW_MIN + ratio * (_OBS_WINDOW_MAX - _OBS_WINDOW_MIN))
        windows[name] = max(_OBS_WINDOW_MIN, min(window, _OBS_WINDOW_MAX))

    return windows


# ── G∘F 3周目 (L5): N-wave 動的分割 ──
_MAX_WAVES: int = 4  # 最大 wave 数
_SPLIT_VARIANCE_RATIO: float = 0.5  # クラス内分散がクラス間分散のこの割合以上なら分割


def _classify_into_waves(
    axis_names: list[str],
    profiles: dict[str, dict],
    threshold: float,
) -> list[tuple[set[str], float]]:
    """軸を N 個の wave に動的分割する。各 wave にタイムアウトを付与。

    1. まず Otsu 閾値で light/heavy の 2 クラスに分割
    2. 各クラス内で分散が大きければさらに再帰的に分割 (最大 _MAX_WAVES)
    3. 各 wave のタイムアウト = max(p95) × _TIMEOUT_BUFFER

    自己言及レベル: wave の数が自身のタイミング分布から生まれる。

    Returns:
        [(wave_axes, wave_timeout), ...] — 軽い wave から重い wave の順
    """
    import logging

    # 軸を中央値でソートし、データなし軸は prior で分類
    scored: list[tuple[str, float, float]] = []  # (name, median, p95)
    for name in axis_names:
        if name in profiles and profiles[name]["count"] >= 2:
            scored.append((name, profiles[name]["median"], profiles[name]["p95"]))
        elif name in _HEAVY_AXES_PRIOR:
            scored.append((name, _HEAVY_AXIS_TIMEOUT_PRIOR * 0.6, _HEAVY_AXIS_TIMEOUT_PRIOR))
        else:
            scored.append((name, _AXIS_TIMEOUT_PRIOR * 0.3, _AXIS_TIMEOUT_PRIOR))

    if not scored:
        return []

    scored.sort(key=lambda x: x[1])

    def _split_recursive(items: list[tuple[str, float, float]], depth: int) -> list[tuple[set[str], float]]:
        """再帰的に分割。depth は残り分割可能回数。"""
        if not items or depth <= 0 or len(items) < 2:
            names = {n for n, _, _ in items}
            p95_max = max((p for _, _, p in items), default=_AXIS_TIMEOUT_PRIOR)
            timeout = max(_MIN_TIMEOUT, p95_max * _TIMEOUT_BUFFER)
            return [(names, timeout)]

        # Otsu 的に最適分割点を探す
        medians = [m for _, m, _ in items]
        best_idx = 1
        best_score = float("inf")
        for i in range(1, len(medians)):
            lo = medians[:i]
            hi = medians[i:]
            mean_lo = sum(lo) / len(lo)
            mean_hi = sum(hi) / len(hi)
            var = sum((x - mean_lo) ** 2 for x in lo) + sum((x - mean_hi) ** 2 for x in hi)
            if var < best_score:
                best_score = var
                best_idx = i

        # 分割の価値を評価: クラス内分散 vs 全体分散
        total_mean = sum(medians) / len(medians)
        total_var = sum((x - total_mean) ** 2 for x in medians)

        if total_var < 0.01:
            # 全軸ほぼ同じ → 分割不要
            names = {n for n, _, _ in items}
            p95_max = max((p for _, _, p in items), default=_AXIS_TIMEOUT_PRIOR)
            timeout = max(_MIN_TIMEOUT, p95_max * _TIMEOUT_BUFFER)
            return [(names, timeout)]

        if best_score / max(total_var, 1e-9) > _SPLIT_VARIANCE_RATIO:
            # 分割してもクラス内分散が大きい → 改善不十分、分割しない
            names = {n for n, _, _ in items}
            p95_max = max((p for _, _, p in items), default=_AXIS_TIMEOUT_PRIOR)
            timeout = max(_MIN_TIMEOUT, p95_max * _TIMEOUT_BUFFER)
            return [(names, timeout)]

        # 分割
        lo_items = items[:best_idx]
        hi_items = items[best_idx:]
        return _split_recursive(lo_items, depth - 1) + _split_recursive(hi_items, depth - 1)

    # 最大分割回数 = log2(_MAX_WAVES) 回
    max_depth = 0
    w = _MAX_WAVES
    while w > 1:
        max_depth += 1
        w //= 2

    waves = _split_recursive(scored, max_depth)

    if len(waves) > 2:
        logging.info(
            "N-wave 分割: %d waves (軸分布に基づく動的分割)",
            len(waves),
        )

    return waves


def _classify_axes_adaptive(
    axis_names: list[str],
    store=None,
) -> tuple[set[str], dict[str, str], float, float, float]:
    """軸をタイミング履歴に基づいて heavy/light に適応的分類する。

    FEP 知覚推論: prior (_HEAVY_AXES_PRIOR) + likelihood (タイミング履歴) → posterior

    G∘F 2周目: 閾値とタイムアウトも適応的に導出。
    - 閾値: 全軸の中央値分布から Otsu 的 2クラス分離
    - タイムアウト: 各クラスの p95 × buffer (1.2x)

    Returns:
        (heavy_axes, classification_log, threshold, light_timeout, heavy_timeout)
    """
    import logging

    if store is None:
        return (
            _HEAVY_AXES_PRIOR.copy(),
            {n: "prior (no store)" for n in axis_names if n in _HEAVY_AXES_PRIOR},
            _HEAVY_THRESHOLD_PRIOR,
            _AXIS_TIMEOUT_PRIOR,
            _HEAVY_AXIS_TIMEOUT_PRIOR,
        )

    try:
        profiles = store.get_all_axis_profiles(last_n=10)
    except Exception as e:  # noqa: BLE001
        logging.warning("適応的分類: プロファイル取得失敗 (%s) → prior にフォールバック", e)
        return (
            _HEAVY_AXES_PRIOR.copy(),
            {n: "prior (store error)" for n in axis_names if n in _HEAVY_AXES_PRIOR},
            _HEAVY_THRESHOLD_PRIOR,
            _AXIS_TIMEOUT_PRIOR,
            _HEAVY_AXIS_TIMEOUT_PRIOR,
        )

    # ── G∘F 2周目: パラメータの適応的導出 ──
    threshold = _derive_threshold(profiles)
    light_timeout, heavy_timeout = _derive_timeouts(profiles)

    heavy: set[str] = set()
    log: dict[str, str] = {}

    for name in axis_names:
        if name in profiles:
            median = profiles[name]["median"]
            count = profiles[name]["count"]
            if median > threshold:
                heavy.add(name)
                log[name] = f"posterior=heavy (median={median:.2f}s, n={count})"
            else:
                log[name] = f"posterior=light (median={median:.2f}s, n={count})"
        elif name in _HEAVY_AXES_PRIOR:
            heavy.add(name)
            log[name] = "prior=heavy (insufficient data)"
        else:
            log[name] = "prior=light (no data)"

    # prior との差分を報告 (自己観測の効果を可視化)
    prior_only = _HEAVY_AXES_PRIOR - heavy
    posterior_only = heavy - _HEAVY_AXES_PRIOR
    if prior_only or posterior_only:
        logging.info(
            "適応的分類: prior→light に降格=%s, prior→heavy に昇格=%s",
            sorted(prior_only) if prior_only else "なし",
            sorted(posterior_only) if posterior_only else "なし",
        )

    # メタ観測: 閾値とタイムアウトのドリフトを報告
    th_drift = threshold - _HEAVY_THRESHOLD_PRIOR
    lt_drift = light_timeout - _AXIS_TIMEOUT_PRIOR
    ht_drift = heavy_timeout - _HEAVY_AXIS_TIMEOUT_PRIOR
    if abs(th_drift) > 0.5 or abs(lt_drift) > 1.0 or abs(ht_drift) > 1.0:
        logging.info(
            "適応的パラメータ: threshold=%.1fs (Δ%+.1fs), light_timeout=%.1fs (Δ%+.1fs), heavy_timeout=%.1fs (Δ%+.1fs)",
            threshold, th_drift, light_timeout, lt_drift, heavy_timeout, ht_drift,
        )

    return heavy, log, threshold, light_timeout, heavy_timeout


def _safe_load(
    name: str,
    load_fn,
    *args,
    default: Optional[dict] = None,
    **kwargs,
) -> dict:
    """例外ハンドリング付きで軸をロードする。

    タイムアウト制御は呼び出し側 (ThreadPoolExecutor.future.result) が担当。
    この関数は例外のキャッチとデフォルト値フォールバックのみ。
    """
    import logging

    if default is None:
        default = {"formatted": ""}

    try:
        return load_fn(*args, **kwargs)
    except Exception as e:  # noqa: BLE001
        logging.warning("Boot axis '%s' failed: %s", name, e)
        return default


# PURPOSE: 並列フルロード (C: 個別タイムアウト + A: ThreadPoolExecutor 並列化)
def _full_boot_load(mode: str = "standard", context: Optional[str] = None) -> dict:
    """
    全軸を並列ロードして結果を返す。

    Wave 1:  handoffs + GPU preflight (他軸が依存)
    Wave 2A: 軽量軸を並列実行 (15s タイムアウト)
    Wave 2B: 重量軸 (LLM/GPU) を並列実行 (30s タイムアウト)
             fast モードでは 2B をスキップ

    get_boot_context() のキャッシュミス時、および refresh_boot_cache() から呼ばれる。
    """
    import logging
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from mekhane.symploke.boot_axes import (
        gpu_preflight as _gpu_pf,
        load_handoffs, load_sophia, load_persona, load_pks,
        load_safety, load_ept, load_digestor, load_attractor,
        load_projects, load_helm, load_skills, load_doxa, load_feedback,
        load_proactive_push, load_ideas, load_state_space,
        load_episodic_memory, load_identity, load_session_resume,
    )

    # ── Wave 1: handoffs + GPU preflight (依存元) ──
    gpu_ok, gpu_reason = _gpu_pf()
    handoffs_result = _safe_load("handoffs", load_handoffs, mode, context)

    # KI コンテキスト: Handoff 主題からフォールバック
    ki_context = context
    if not ki_context and handoffs_result.get("latest"):
        ki_context = handoffs_result["latest"].metadata.get("primary_task", "")
        if not ki_context:
            ki_context = handoffs_result["latest"].content[:200]

    attractor_context = context or ki_context

    # ── 全タスク定義 (result_key, axis_name, load_fn, args, kwargs) ──
    all_tasks: list[tuple[str, str, object, tuple, dict]] = [
        ("ki", "ki", load_sophia, (mode, context), {"ki_context": ki_context}),
        ("persona", "persona", load_persona, (mode, context), {}),
        ("pks", "pks", load_pks, (mode, context), {"ki_context": ki_context}),
        ("safety", "safety", load_safety, (mode, context), {}),
        ("ept", "ept", load_ept, (mode, context), {}),
        ("digestor", "digestor", load_digestor, (mode, context), {}),
        ("attractor", "attractor", load_attractor, (mode, attractor_context), {"gpu_ok": gpu_ok}),
        ("projects", "projects", load_projects, (mode, context), {}),
        ("helm", "helm", load_helm, (mode, context), {}),
        ("skills", "skills", load_skills, (mode, context), {}),
        ("doxa", "doxa", load_doxa, (mode, context), {}),
        ("feedback", "feedback", load_feedback, (mode, context), {}),
        ("proactive_push", "proactive_push", load_proactive_push, (mode, context), {}),
        ("ideas", "ideas", load_ideas, (mode, context), {}),
        ("session_resume", "session_resume", load_session_resume, (mode, context), {}),
        ("state_space", "state_space", load_state_space, (mode, context), {}),
        ("episodic_memory", "episodic_memory", load_episodic_memory, (mode, context), {}),
        ("identity", "identity", load_identity, (mode, context), {}),
    ]

    # ── 適応的分類 (FEP 知覚推論) ──
    # prior (_HEAVY_AXES_PRIOR) + likelihood (Store のタイミング履歴) → posterior
    try:
        from mekhane.symploke.phantazein_store import get_store
        _store = get_store()
    except Exception:  # noqa: BLE001
        _store = None

    all_axis_names = [n for _, n, _, _, _ in all_tasks]
    heavy_axes, classification_log, adapted_threshold, adapted_light_to, adapted_heavy_to = (
        _classify_axes_adaptive(all_axis_names, _store)
    )

    if classification_log:
        logging.debug("Boot axis classification (threshold=%.1fs): %s", adapted_threshold, classification_log)

    # ── G∘F 3周目: L4 観測窓メタ観測 + L5 N-wave 分割 ──
    try:
        profiles = _store.get_all_axis_profiles() if _store else {}
    except Exception:  # noqa: BLE001
        profiles = {}

    # L4: 適応的観測窓の導出・報告 (次回 boot で last_n を分岐する基盤)
    obs_windows = _derive_observation_windows(profiles)
    if obs_windows:
        varied = {n: w for n, w in obs_windows.items() if w != _OBS_WINDOW_PRIOR}
        if varied:
            logging.info(
                "L4 適応的観測窓: %s",
                ", ".join(f"{n}={w}" for n, w in sorted(varied.items())),
            )

    # L5: N-wave 動的分割
    waves = _classify_into_waves(all_axis_names, profiles, adapted_threshold)

    # wave_axes → tasks マッピング
    task_lookup: dict[str, tuple[str, str, object, tuple, dict]] = {
        n: (k, n, fn, a, kw) for k, n, fn, a, kw in all_tasks
    }

    results: dict[str, dict] = {"handoffs": handoffs_result}
    skipped: list[str] = []
    timed_out: list[str] = []  # タイムアウトした軸名 (分類精度メタ観測用)
    timings: dict[str, float] = {}  # 軸名 → 所要時間

    import time as _time

    def _run_wave(
        tasks: list[tuple[str, str, object, tuple, dict]],
        timeout: float,
        wave_label: str,
    ) -> None:
        """指定タスクを並列実行し results/skipped を更新する。"""
        if not tasks:
            return
        wave_start = _time.monotonic()
        with ThreadPoolExecutor(max_workers=8, thread_name_prefix=f"boot-{wave_label}") as executor:
            future_to_info: dict = {}
            submit_times: dict = {}
            for result_key, axis_name, load_fn, args, kwargs in tasks:
                t0 = _time.monotonic()
                future = executor.submit(_safe_load, axis_name, load_fn, *args, **kwargs)
                future_to_info[future] = (result_key, axis_name)
                submit_times[future] = t0

            from concurrent.futures import wait
            done, not_done = wait(future_to_info.keys(), timeout=timeout)

            # 完了した軸の結果を収集
            for future in done:
                key, axis_name = future_to_info[future]
                elapsed = _time.monotonic() - submit_times[future]
                timings[axis_name] = elapsed
                try:
                    results[key] = future.result()
                except Exception as e:  # noqa: BLE001
                    logging.warning("Boot axis '%s' failed (%.1fs): %s", axis_name, elapsed, e)
                    results[key] = {"formatted": ""}

            # 未完了の軸をスキップ
            for future in not_done:
                key, axis_name = future_to_info[future]
                future.cancel()
                elapsed = _time.monotonic() - submit_times[future]
                timings[axis_name] = elapsed
                timed_out.append(axis_name)
                logging.warning("Boot %s: axis '%s' timed out after %.1fs — skipped", wave_label, axis_name, elapsed)
                results[key] = {"formatted": f"⏱️ {axis_name}: タイムアウト ({timeout:.0f}s)"}
                skipped.append(key)

        wave_elapsed = _time.monotonic() - wave_start
        logging.info("Boot %s: %d axes in %.1fs (timeout=%.0fs, adapted)", wave_label, len(tasks), wave_elapsed, timeout)

    # ── N-wave 実行 (L5: 軽い wave → 重い wave の順) ──
    for wave_idx, (wave_axes, wave_timeout) in enumerate(waves):
        wave_label = f"W{wave_idx + 1}/{len(waves)}"
        wave_tasks = [task_lookup[n] for n in wave_axes if n in task_lookup]

        # fast モード: 最も重い wave (最後) はスキップ
        if mode == "fast" and wave_idx == len(waves) - 1 and len(waves) > 1:
            for result_key, axis_name, _, _, _ in wave_tasks:
                results[result_key] = {"formatted": f"⏩ {axis_name}: fast モードでスキップ"}
                skipped.append(result_key)
            logging.info("Boot %s: %d heavy axes skipped (fast mode)", wave_label, len(wave_tasks))
        else:
            _run_wave(wave_tasks, wave_timeout, wave_label)

    # ── 分類精度のメタ観測 ──
    # 「light wave (= 前半 wave) に分類したのにタイムアウト」= 分類ミス → 次回修正
    if timed_out:
        # light wave = waves[0] (最も軽い)
        light_wave_axes = waves[0][0] if waves else set()
        misclassified = [a for a in timed_out if a in light_wave_axes]
        if misclassified:
            logging.warning(
                "Boot 分類精度: light wave でタイムアウト=%s (→ 次回再分類される)",
                misclassified,
            )

    # ── タイミングログ ──
    if timings:
        sorted_t = sorted(timings.items(), key=lambda x: x[1], reverse=True)
        top5 = sorted_t[:5]
        timing_report = ", ".join(f"{n}={t:.1f}s" for n, t in top5)
        logging.info("Boot timing (top 5): %s", timing_report)

    if skipped:
        logging.info("Boot: %d axes skipped: %s", len(skipped), ", ".join(skipped))

    # ── タイミング永続化 (フィードバックループを閉じる) ──
    if _store and timings:
        import uuid
        boot_id = str(uuid.uuid4())[:8]
        # タイムアウトした軸のステータスを記録
        statuses = {}
        for axis_name in timings:
            if axis_name in [s for s in skipped]:
                statuses[axis_name] = "timeout"
        # fast モードでスキップされた軸 (最後の wave) を記録
        if mode == "fast" and len(waves) > 1:
            last_wave_axes = waves[-1][0]
            for axis_name in last_wave_axes:
                if axis_name not in timings:
                    timings[axis_name] = 0.0
                    statuses[axis_name] = "skipped"
        try:
            _store.record_boot_timings(boot_id, timings, statuses, mode)
            logging.info("Boot feedback loop: timings persisted (boot_id=%s)", boot_id)
        except Exception as e:  # noqa: BLE001
            logging.warning("Boot feedback loop: persistence failed: %s", e)

    # ── WAL 軸 (O) — Intent-WAL 前セッション復元 ──
    wal_result = {"has_wal": False, "formatted": ""}
    if mode != "fast":
        try:
            from mekhane.symploke.intent_wal import IntentWALManager
            wal_mgr = IntentWALManager()
            prev_wal = wal_mgr.load_latest()
            if prev_wal:
                done = sum(1 for e in prev_wal.progress if e.status == "done")
                total = len(prev_wal.progress)
                wal_lines = ["📋 **Intent-WAL** (前セッション)"]
                wal_lines.append(f"   Goal: {prev_wal.session_goal}")
                wal_lines.append(f"   Health: {prev_wal.context_health_level}")
                wal_lines.append(f"   Progress: {done}/{total} steps")
                if prev_wal.blockers:
                    wal_lines.append(f"   ⚠️ Blockers: {', '.join(prev_wal.blockers)}")
                incomplete = [e for e in prev_wal.progress if e.status in ("in_progress", "blocked")]
                if incomplete:
                    wal_lines.append("   未完了:")
                    for e in incomplete[:5]:
                        wal_lines.append(f"     - [{e.status}] {e.action}")
                wal_result = {
                    "has_wal": True,
                    "session_goal": prev_wal.session_goal,
                    "health": prev_wal.context_health_level,
                    "progress_done": done,
                    "progress_total": total,
                    "blockers": prev_wal.blockers,
                    "formatted": "\n".join(wal_lines),
                    "boot_section": wal_mgr.to_boot_section(),
                }
        except Exception:  # noqa: BLE001
            pass  # WAL failure should not block boot

    results["wal"] = wal_result

    # ── 統合フォーマット ──
    lines: list[str] = []
    persona_result = results.get("persona", {})
    ki_result = results.get("ki", {})

    if persona_result.get("formatted"):
        lines.append(persona_result["formatted"])
        lines.append("")

    if handoffs_result.get("latest"):
        from mekhane.symploke.handoff_search import format_boot_output
        lines.append(format_boot_output(handoffs_result, verbose=(mode == "detailed")))
        lines.append("")

    if wal_result.get("formatted"):
        lines.append(wal_result["formatted"])
        lines.append("")

    if ki_result.get("ki_items"):
        from mekhane.symploke.sophia_ingest import format_ki_output
        lines.append(format_ki_output(ki_result))

    for key in ["pks", "safety", "ept", "digestor", "attractor", "projects",
                "helm", "skills", "doxa", "feedback", "proactive_push", "ideas",
                "session_resume", "state_space", "episodic_memory", "identity"]:
        axis_result = results.get(key, {})
        fmt = axis_result.get("formatted", "")
        if fmt:
            lines.append("")
            lines.append(fmt)

    # ── BC違反傾向 (Phase 4.9) ──
    bc_violation_result = {"formatted": ""}
    if mode != "fast":
        try:
            from mekhane.sympatheia.violation_logger import (
                read_all_entries as _read_bc,
                format_boot_summary as _format_bc_boot,
            )
            bc_entries = _read_bc()
            if bc_entries:
                bc_summary = _format_bc_boot(bc_entries)
                bc_violation_result = {"formatted": bc_summary, "count": len(bc_entries)}
                lines.append("")
                lines.append(bc_summary)
        except Exception as e:  # noqa: BLE001
            logging.debug("BC violation loading skipped: %s", e)

    # incoming/ チェック — Digestor 消化候補の通知
    from mekhane.paths import INCOMING_DIR
    incoming_dir = INCOMING_DIR
    incoming_files = sorted(incoming_dir.glob("eat_*.md")) if incoming_dir.exists() else []
    incoming_result = {"count": len(incoming_files), "files": [f.name for f in incoming_files]}
    if incoming_files:
        lines.append("")
        lines.append(f"📥 Digestor: {len(incoming_files)} 件の消化候補待ち")
        for f in incoming_files[:5]:
            lines.append(f"   → {f.name}")
        if len(incoming_files) > 5:
            lines.append(f"   ... +{len(incoming_files) - 5} 件")

    # n8n WF-06: Session Start 通知
    try:
        import urllib.request
        n8n_payload = json.dumps({
            "mode": mode,
            "context": context or "",
            "agent": "Claude",
            "handoff_count": handoffs_result.get("count", 0),
            "ki_count": ki_result.get("count", 0),
        }).encode("utf-8")
        req = urllib.request.Request(
            "http://localhost:5678/webhook/session-start",
            data=n8n_payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5)
        print(" 📡 n8n: session started", file=sys.stderr)
    except Exception:  # noqa: BLE001
        pass  # n8n 未起動でもブートは継続

    results["incoming"] = incoming_result
    results["bc_violations"] = bc_violation_result
    results["formatted"] = "\n".join(lines)

    return results




# PURPOSE: Print formatted boot summary (API priority, local fallback)
def print_boot_summary(mode: str = "standard", context: Optional[str] = None):
    """Print formatted boot summary. Tries API first, falls back to local execution."""
    result = None
    
    # Try fetching boot context via API to prevent local hang and utilize Mother Brain warm cache
    try:
        import urllib.request
        import urllib.parse
        api_base = os.environ.get("HGK_API_BASE", "http://127.0.0.1:9696").rstrip("/")
        # API 既定 max 300s / symploke.get_boot_context の重い軸と整合（12s は空 axes になりやすい）
        url = f"{api_base}/api/symploke/boot-context?mode={mode}&timeout=90"
        if context:
            url += f"&context={urllib.parse.quote(context)}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=max(120.0, 90.0 + 30.0)) as response:
            data = json.loads(response.read().decode("utf-8"))
            result = data.get("axes", {})
            if not result or not result.get("formatted"):
                raise ValueError("Empty or invalid axes data from API")
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ API Server fetch failed ({e}), falling back to local execution...", file=sys.stderr)
        result = get_boot_context(mode=mode, context=context)

    print(result["formatted"])

    # Today's Theorem — underused theorem suggestion
    try:
        from mekhane.fep.theorem_recommender import todays_theorem, usage_summary
        suggestions = todays_theorem(n=2)
        if suggestions:
            print()
            print("💡 **今日の定理提案** (underused theorems)")
            for t in suggestions:
                usage = t["usage_count"]
                print(f"   {t['id']} {t['name']} ({t['command']}) — 使用{usage}回")
                print(f"      {t['prompt']}")
            # Usage summary line
            summary = usage_summary()
            unused_pct = round(summary["unused_count"] / 24 * 100)
            print(f"   📊 未使用: {summary['unused_count']}/24 ({unused_pct}%)")
    except Exception:  # noqa: BLE001
        pass  # Theorem recommender failure should not block boot

    # Summary line
    print()
    print("─" * 50)
    h_count = result["handoffs"]["count"]
    ki_count = result["ki"]["count"]
    sessions = result["persona"].get("sessions", 0)
    pks_count = result.get("pks", {}).get("count", 0)
    safety_errors = result.get("safety", {}).get("errors", 0)
    attractor_series = result.get("attractor", {}).get("series", [])
    attractor_str = "+".join(attractor_series) if attractor_series else "—"
    ept_pct = result.get("ept", {}).get("pct", 0)
    ept_str = f"{ept_pct:.0f}%" if ept_pct > 0 else "—"
    proj_total = result.get("projects", {}).get("total", 0)
    proj_active = result.get("projects", {}).get("active", 0)
    proj_str = f"{proj_active}/{proj_total}" if proj_total > 0 else "—"
    fb_total = result.get("feedback", {}).get("total", 0)
    fb_rate = result.get("feedback", {}).get("accept_rate", 0)
    fb_str = f"{fb_rate:.0%}({fb_total})" if fb_total > 0 else "—"
    print(f"📊 Handoff: {h_count}件 | KI: {ki_count}件 | Sessions: {sessions} | PKS: {pks_count}件 | Safety: {'✅' if safety_errors == 0 else f'⚠️{safety_errors}'} | EPT: {ept_str} | PJ: {proj_str} | Attractor: {attractor_str} | FB: {fb_str}")

    # detailed モード: テンプレートファイル生成
    if mode == "detailed":
        template_path = generate_boot_template(result)
        print(f"\n📝 Boot Report Template: {template_path}", file=sys.stderr)
        print(f"TEMPLATE:{template_path}")


# ============================================================
# テンプレート生成 (A+C) — 環境強制: 穴埋め式テンプレート
# ============================================================

# モード別の最低要件定義
MODE_REQUIREMENTS = {
    "detailed": {
        "handoff_window": "72H",
        "ki_count": 5,
        "min_chars": 3000,
        "required_sections": [
            "Handoff 個別要約",
            "KI 深読み",
            "Self-Profile 摩擦",
            "意味ある瞬間",
            "Phase 詳細",
            "開発中プロジェクト",
            "タスク提案",
        ],
    },
    "standard": {
        "handoff_window": "24H",
        "ki_count": 3,
        "min_chars": 1400,
        "required_sections": [
            "Handoff 個別要約 (3件・各S/A/R)",
            "開発中プロジェクト",
            "Safety",
            "EPT",
            "Doxa",
            "Digestor",
            "Quota",
            "Phantazein 成果物レポート",
            "タスク提案",
        ],
    },
    "fast": {
        "handoff_window": "0",
        "ki_count": 0,
        "min_chars": 0,
        "required_sections": [],
    },
}


# PURPOSE: 環境強制: モード別の穴埋めテンプレートを生成する。
def generate_boot_template(result: dict) -> Path:
    """
    環境強制: モード別の穴埋めテンプレートを生成する。

    <!-- REQUIRED --> マーカー付きセクションは必須。
    <!-- FILL --> マーカーは LLM が記入すべき箇所。
    postcheck で未記入の FILL が検出されると FAIL になる。
    """
    now = datetime.now()
    template_path = Path(f"/tmp/boot_report_{now.strftime('%Y%m%d_%H%M')}.md")

    lines = []
    lines.append(f"# Boot Report — {now.strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("## 必須セクション チェックリスト")
    lines.append("")

    reqs = MODE_REQUIREMENTS.get("detailed", {})
    for section in reqs.get("required_sections", []):
        lines.append(f"- [ ] {section}")
    lines.append("")

    # --- Handoff 個別要約 ---
    lines.append("## Handoff 個別要約")
    lines.append("<!-- REQUIRED: 各 Handoff の S/A/R を1行以上 -->")
    lines.append("")

    handoffs = result.get("handoffs", {})
    related = handoffs.get("related", [])
    latest = handoffs.get("latest")

    all_handoffs = []
    if latest:
        all_handoffs.append(latest)
    if related:
        all_handoffs.extend(related)

    for i, h in enumerate(all_handoffs, 1):
        title = "Unknown"
        if hasattr(h, "metadata"):
            title = h.metadata.get("primary_task", h.metadata.get("title", "Unknown"))
        elif isinstance(h, dict):
            title = h.get("primary_task", h.get("title", "Unknown"))
        lines.append(f"### Handoff {i}: {title}")
        lines.append("")
        lines.append("> 要約: <!-- FILL -->")
        lines.append("")

    # --- KI 深読み ---
    lines.append("## KI 深読み")
    lines.append("<!-- REQUIRED: サマリー引用 + 自分の解釈を記述 -->")
    lines.append("")

    ki_items = result.get("ki", {}).get("ki_items", [])
    for i, ki in enumerate(ki_items[:5], 1):
        name = "Unknown"
        summary = "N/A"
        if hasattr(ki, "metadata"):
            name = ki.metadata.get("ki_name", "Unknown")
            summary = ki.metadata.get("summary", "N/A")
        elif isinstance(ki, dict):
            name = ki.get("ki_name", "Unknown")
            summary = ki.get("summary", "N/A")
        lines.append(f"### KI {i}: {name}")
        lines.append("")
        lines.append(f"> サマリー: {summary[:100]}")
        lines.append("> 解釈: <!-- FILL -->")
        lines.append("")

    # 不足分はプレースホルダー
    for i in range(len(ki_items) + 1, 6):
        lines.append(f"### KI {i}: (session context から選択)")
        lines.append("")
        lines.append("> サマリー: <!-- FILL -->")
        lines.append("> 解釈: <!-- FILL -->")
        lines.append("")

    # --- Self-Profile 摩擦 ---
    lines.append("## Self-Profile 摩擦")
    lines.append("<!-- REQUIRED: ミスパターンとの摩擦を明示 -->")
    lines.append("")
    lines.append("今回のセッションで注意すべきミスパターン: <!-- FILL -->")
    lines.append("")

    # --- 意味ある瞬間 ---
    lines.append("## 意味ある瞬間")
    lines.append("<!-- REQUIRED: 各瞬間に対する自分の解釈を記述 -->")
    lines.append("")
    lines.append("解釈: <!-- FILL -->")
    lines.append("")

    # --- Phase 詳細 ---
    lines.append("## Phase 詳細")
    lines.append("<!-- REQUIRED: 各 Phase の展開された詳細を出力 -->")
    lines.append("")
    for phase in range(7):
        lines.append(f"### Phase {phase}")
        lines.append("")
        lines.append("<!-- FILL -->")
        lines.append("")

    # --- 開発中プロジェクト ---
    lines.append("## 開発中プロジェクト")
    lines.append("<!-- REQUIRED: registry.yaml から読み込んだ PJ 一覧 -->")
    lines.append("")

    projects = result.get("projects", {}).get("projects", [])
    if projects:
        status_icons = {"active": "🟢", "dormant": "💤", "archived": "🗄️", "planned": "📋"}
        active = [p for p in projects if p.get("status") == "active"]
        dormant = [p for p in projects if p.get("status") == "dormant"]
        archived = [p for p in projects if p.get("status") == "archived"]
        # 全PJを表示（status で区別）— dormant/archived を省略しない
        for p in projects:
            icon = status_icons.get(p.get("status", ""), "❓")
            name = p.get("name", p.get("id", "?"))
            phase = p.get("phase", "")
            summary_text = p.get("summary", "")
            lines.append(f"- {icon} **{name}** [{phase}]: {summary_text}")
        lines.append("")
        lines.append(f"統計: Active {len(active)} / Dormant {len(dormant)} / Archived {len(archived)} / Total {len(projects)}")
    else:
        lines.append("<!-- FILL: registry.yaml が見つかりません -->")
    lines.append("")

    # --- タスク提案 ---
    lines.append("## タスク提案")
    lines.append("<!-- REQUIRED: Handoff から抽出したタスク提案 -->")
    lines.append("")
    lines.append("1. <!-- FILL -->")
    lines.append("")

    template_path.write_text("\n".join(lines), encoding="utf-8")
    return template_path


# ============================================================
# ポストチェック (B) — 環境強制: 記入済みレポートの検証
# ============================================================

# PURPOSE: 記入済み boot report を検証する。
def postcheck_boot_report(report_path: str, mode: str = "detailed") -> dict:
    """
    記入済み boot report を検証する。

    Returns:
        dict: {
            "passed": bool,
            "checks": [{"name": str, "passed": bool, "detail": str}],
            "formatted": str
        }
    """
    path = Path(report_path)
    if not path.exists():
        return {
            "passed": False,
            "checks": [{"name": "file_exists", "passed": False, "detail": f"File not found: {report_path}"}],
            "formatted": f"❌ Boot Report Validation: FAIL\n  ❌ File not found: {report_path}",
        }

    content = path.read_text(encoding="utf-8")
    reqs = MODE_REQUIREMENTS.get(mode, MODE_REQUIREMENTS["standard"])
    checks = []

    # Check 1: <!-- FILL --> の残存数
    fill_count = content.count("<!-- FILL -->")
    checks.append({
        "name": "unfilled_sections",
        "passed": fill_count == 0,
        "detail": f"{'No' if fill_count == 0 else fill_count} unfilled sections"
            + ("" if fill_count == 0 else f" remaining (<!-- FILL --> found {fill_count}x)"),
    })

    # Check 2: REQUIRED セクション数
    required_count = content.count("<!-- REQUIRED")
    expected = len(reqs.get("required_sections", []))
    checks.append({
        "name": "required_sections",
        "passed": required_count >= expected,
        "detail": f"Required sections: {required_count}/{expected}",
    })

    # Check 3: 総文字数
    min_chars = reqs.get("min_chars", 0)
    char_count = len(content)
    checks.append({
        "name": "content_length",
        "passed": char_count >= min_chars,
        "detail": f"Content length: {char_count} chars"
            + (f" (≥ {min_chars})" if char_count >= min_chars else f" (< {min_chars}, need {min_chars - char_count} more)"),
    })

    # Check 4: Handoff 引用数 (### Handoff N: の数)
    handoff_refs = len(re.findall(r"^### Handoff \d+:", content, re.MULTILINE))
    # postcheck は独立関数なので get_boot_context の結果にアクセスできない
    # Handoff 存在を静的にチェック: 最低1件あれば OK
    expected_h = 1 if mode == "detailed" else 0
    checks.append({
        "name": "handoff_references",
        "passed": handoff_refs >= expected_h,
        "detail": f"Handoff references: {handoff_refs}"
            + (f" (≥ {expected_h})" if handoff_refs >= expected_h else f" (< {expected_h})"),
    })

    # Check 5: チェックリスト完了率
    unchecked = content.count("- [ ]")
    checked = content.count("- [x]")
    total_checks = unchecked + checked
    all_checked = unchecked == 0 and total_checks > 0
    checks.append({
        "name": "checklist_completion",
        "passed": all_checked,
        "detail": f"Checklist: {checked}/{total_checks} completed"
            + ("" if all_checked else f" ({unchecked} remaining)"),
    })
    # Check 6: Intent-WAL 空チェック (Plan Object 案D — 環境強制)
    # /boot- (fast) では省略可、/boot, /boot+ では必須
    if mode != "fast":
        has_intent_wal = bool(re.search(
            r"intent_wal:|session_goal:", content, re.IGNORECASE
        ))
        # WAL が存在する場合、session_goal がプレースホルダーのままでないか確認
        wal_filled = has_intent_wal and not bool(re.search(
            r'session_goal:\s*["\']?\{', content
        ))
        checks.append({
            "name": "intent_wal",
            "passed": wal_filled,
            "detail": "Intent-WAL: "
                + ("✅ declared" if wal_filled else "❌ missing or unfilled")
                + (" (required for /boot and /boot+)" if not wal_filled else ""),
        })

    # Drift = 1 - ε (失われた文脈の量)
    # ε precision: Handoff への言及 + Self-Profile 参照 + 意味ある瞬間の記述
    # BS-3b fix: FILL 残存率で ε を割り引く
    #   テンプレート見出しに "Handoff" 等が含まれるため、
    #   記入前でもパターンマッチが成立してしまう問題を解消
    adjunction_indicators = {
        "handoff_context": bool(re.search(r"(?:引き継ぎ|handoff|Handoff|前回)", content, re.IGNORECASE)),
        "self_profile_ref": bool(re.search(r"(?:self.profile|ミスパターン|能力境界|Self-Profile)", content, re.IGNORECASE)),
        "meaningful_moment": bool(re.search(r"(?:意味ある瞬間|印象的|感動|発見)", content, re.IGNORECASE)),
        "task_continuity": bool(re.search(r"(?:前回の続き|継続|再開|残タスク)", content, re.IGNORECASE)),
    }
    epsilon_count = sum(adjunction_indicators.values())
    epsilon_raw = epsilon_count / len(adjunction_indicators)

    # BS-3b: FILL 残存ペナルティ (dia+ TH-005)
    # 未記入セクションが多い → テンプレート見出しのマッチは信頼できない
    fill_remaining = content.count("<!-- FILL -->")
    if fill_remaining > 0:
        # fill_ratio = 記入完了率 (0.0 = 全未記入, 1.0 = 全記入)
        # 推定: テンプレートは ~25 FILL マーカーを含む (detailed mode)
        estimated_total_fills = max(fill_remaining, 25)
        fill_ratio = 1.0 - (fill_remaining / estimated_total_fills)
        epsilon_precision = epsilon_raw * fill_ratio
    else:
        epsilon_precision = epsilon_raw

    drift = 1.0 - epsilon_precision
    checks.append({
        "name": "adjunction_metrics",
        "passed": True,  # Informational only, never blocks
        "detail": f"Adjunction L⊣R: ε={epsilon_precision:.0%}, Drift={drift:.0%}"
            + (f" (fill_penalty: {fill_remaining} FILL remaining)" if fill_remaining > 0 else "")
            + f" ({', '.join(k for k, v in adjunction_indicators.items() if v)})"
            if epsilon_count > 0
            else f"Adjunction L⊣R: ε=0%, Drift=100% (no context restoration detected)",
    })

    # 結果集計
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    all_passed = all(c["passed"] for c in checks)

    # フォーマット
    status = "PASS" if all_passed else "FAIL"
    icon = "✅" if all_passed else "❌"
    lines = [f"{icon} Boot Report Validation: {status} ({passed_count}/{total} checks)"]
    for c in checks:
        ci = "✅" if c["passed"] else "❌"
        lines.append(f"  {ci} {c['detail']}")

    return {
        "passed": all_passed,
        "checks": checks,
        "formatted": "\n".join(lines),
    }


# PURPOSE: main の処理
def main():
    # .env ロード — HGK_ROOT の .env から環境変数を注入
    try:
        from mekhane.paths import ensure_env
        ensure_env()
    except ImportError:
        pass  # mekhane.paths not available — rely on system env vars

    parser = argparse.ArgumentParser(description="Boot integration API")
    parser.add_argument(
        "--mode",
        choices=["fast", "standard", "detailed"],
        default="standard",
        help="Boot mode",
    )
    parser.add_argument("--context", type=str, help="Context for search")
    parser.add_argument(
        "--postcheck",
        type=str,
        metavar="REPORT_PATH",
        help="Post-check a completed boot report file",
    )
    args = parser.parse_args()

    import warnings

    warnings.filterwarnings("ignore")

    # ポストチェックモード
    if args.postcheck:
        result = postcheck_boot_report(args.postcheck, mode=args.mode)
        print(result["formatted"])
        sys.exit(0 if result["passed"] else 1)

    # 通常ブートモード
    print(f"⏳ Boot Mode: {args.mode}", file=sys.stderr)

    try:
        print_boot_summary(mode=args.mode, context=args.context)
    except KeyboardInterrupt:
        print("\n⚠️ Boot sequence interrupted.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print(f"\n❌ Boot sequence failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

