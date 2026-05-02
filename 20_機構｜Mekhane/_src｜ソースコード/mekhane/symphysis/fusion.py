from __future__ import annotations
"""
CCL-IR × Dendron 融合モジュール — Phase 0.5 (43d + import graph 統合)

PURPOSE: 二つの忘却関手 (U_ccl × U_purpose) の出力を
  同一の FusionEntry に統合し、「自由の検出」を可能にする。

理論的背景 (VISION v0.3.0 §1.6-1.8):
  自由 = 独立して存在する同型射 (参照で接続されていない)
  融合 = G_purpose ∘ F_search : Code → Kalon
  Fix(G∘F) = 全ての同型が参照で接続 = 最小表現
  検出: Lēthē (43d cosine) × import graph の交差分析

PROOF:
  VISION: Symphysis/Lethe_dendron/VISION.md (v0.3.0)
  DEPENDS: mekhane.symploke.code_ingest, mekhane.dendron.purpose_infer
"""


import ast
import json
import multiprocessing
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterator

from mekhane.symploke.code_ingest import python_to_ccl, ccl_feature_vector
from mekhane.dendron.purpose_infer import infer_purpose


# --- データ構造 ---

@dataclass
class FusionEntry:
    """構造と存在の統合エントリ (Phase 0: 軽量版)

    VISION.md §2.3 の FusionEntry から Phase 0 に必要な
    フィールドのみを抽出。 embedding や EPT は Phase 2+ で追加。

    直交性の二軸:
      ccl_expr  — U_ccl (構造的忘却) の出力
      purpose   — U_purpose (存在的忘却) の出力
    """

    # Level 0: 名前 (識別用)
    filepath: str
    name: str
    lineno: int
    class_name: str = ""

    # Level 1: 構造 (U_ccl の出力)
    ccl_expr: str = ""
    ccl_features_43d: list = field(default_factory=list)  # 43d 構造特徴量

    # Level 2: 存在 (U_purpose の出力)
    purpose: str = ""
    purpose_source: str = ""  # "manual" | "inferred" | "docstring"

    # 参照グラフ (§1.7: 射 h の有無を判定するための情報)
    imports: list = field(default_factory=list)  # このファイルの import 一覧

    @property
    def qualified_name(self) -> str:
        """完全修飾名"""
        if self.class_name:
            return f"{self.class_name}.{self.name}"
        return self.name

    @property
    def short_location(self) -> str:
        """短縮ロケーション"""
        return f"{Path(self.filepath).name}:{self.qualified_name}"

    def to_dict(self) -> dict:
        """シリアライズ"""
        d = asdict(self)
        # numpy array は list に変換済み (field 定義で list)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> FusionEntry:
        """辞書から復元"""
        return cls(**{k: v for k, v in d.items()
                      if k in cls.__dataclass_fields__})


# --- スキャナー ---

# デフォルト除外ディレクトリ
DEFAULT_EXCLUDES = frozenset({
    "__pycache__", ".git", ".venv", "venv", "node_modules",
    "90_保管庫｜Archive", ".system_generated", "dist", "build",
})

# python_to_ccl のタイムアウト秒数
# code_ingest.py の _stmt_to_ccl で walrus operator 修正済み (2026-03-20):
#   旧: [_stmt_to_ccl(s) for s in body if _stmt_to_ccl(s)]  → 2回呼出し → O(2^n)
#   新: [c for s in body if (c := _stmt_to_ccl(s))]          → 1回呼出し → O(n)
# multiprocessing 分離は防御的安全策として残す。
_CCL_TIMEOUT_SECONDS = 5
_MAX_IF_DEPTH = 30  # walrus 修正後は線形。30段でも <2秒


def _measure_if_depth(node: ast.AST, current: int = 0) -> int:
    """AST ノードの if/elif ネスト深度を測定 (O(n) で安価)"""
    max_depth = current
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.If):
            d = _measure_if_depth(child, current + 1)
            max_depth = max(max_depth, d)
        else:
            d = _measure_if_depth(child, current)
            max_depth = max(max_depth, d)
    return max_depth


def _ccl_worker(source_code: str, func_name: str, queue: multiprocessing.Queue) -> None:
    """別プロセスで python_to_ccl を実行するワーカー"""
    try:
        tree = ast.parse(source_code)
        # 指定された関数名のノードを探す
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == func_name and node.lineno:
                    result = python_to_ccl(node)
                    queue.put(result if result != "_" else None)
                    return
        queue.put(None)
    except Exception:  # noqa: BLE001
        queue.put(None)


def _safe_python_to_ccl(
    node: ast.FunctionDef,
    source_code: str,
) -> str | None:
    """python_to_ccl を安全に呼ぶ (事前深度チェック + プロセス分離)

    2段階の保護:
    1. AST の if/elif 深度チェック (O(n), 即完了) → 深すぎたらスキップ
    2. multiprocessing.Process でタイムアウト付き実行 → ハングしたら kill
    """
    # 事前チェック: if/elif の深さが閾値を超えたらスキップ
    if _measure_if_depth(node) > _MAX_IF_DEPTH:
        return None

    queue = multiprocessing.Queue()
    p = multiprocessing.Process(
        target=_ccl_worker,
        args=(source_code, node.name, queue),
    )
    p.start()
    p.join(timeout=_CCL_TIMEOUT_SECONDS)

    if p.is_alive():
        p.kill()
        p.join(timeout=1)
        return None

    try:
        return queue.get_nowait()
    except Exception:  # noqa: BLE001
        return None


def _extract_purpose(
    node: ast.FunctionDef,
    lines: list[str],
    class_name: str,
) -> tuple[str, str]:
    """PURPOSE を抽出 (手書き優先 → 推定フォールバック)

    Returns:
        (purpose_text, source) where source is "manual"|"inferred"|"docstring"
    """
    # 1. 手書き PURPOSE コメントを探す
    if node.lineno >= 2:
        prev_line = lines[node.lineno - 2].strip()
        if prev_line.startswith("# PURPOSE:"):
            return prev_line[len("# PURPOSE:"):].strip(), "manual"

    # 2. 推定 (infer_purpose)
    docstring = ast.get_docstring(node)
    node_type = "method" if class_name else "function"
    inferred = infer_purpose(node.name, node_type, docstring)
    source = "docstring" if docstring and inferred else "inferred"
    return inferred, source


def _extract_imports(tree: ast.AST) -> list[str]:
    """ファイルの import 一覧を抽出 (§1.7: 射 h の有無判定用)"""
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}")
    return imports


def scan_file(filepath: Path) -> Iterator[FusionEntry]:
    """単一ファイルをスキャンし FusionEntry を生成"""
    try:
        source = filepath.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError):
        return

    lines = source.splitlines()
    # ファイル単位の import 一覧 (全関数で共有)
    file_imports = _extract_imports(tree)

    def _process_node(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        class_name: str = "",
    ) -> FusionEntry | None:
        """AST ノードから FusionEntry を構築"""
        # 5行未満の自明な関数は除外
        end = node.end_lineno or node.lineno
        if (end - node.lineno + 1) < 5:
            return None

        # ダンダーメソッド除外 (__init__ は残す)
        if (node.name.startswith("__") and node.name.endswith("__")
                and node.name != "__init__"):
            return None

        # U_ccl: 構造的忘却
        ccl_expr = _safe_python_to_ccl(node, source)
        if ccl_expr is None:
            return None

        # 43d 構造特徴量 (Phase 0.5)
        try:
            features = ccl_feature_vector(node)
        except Exception:  # noqa: BLE001
            features = []

        # U_purpose: 存在的忘却
        purpose, purpose_source = _extract_purpose(node, lines, class_name)

        return FusionEntry(
            filepath=str(filepath),
            name=node.name,
            lineno=node.lineno,
            class_name=class_name,
            ccl_expr=" ".join(ccl_expr.split()),  # 正規化
            ccl_features_43d=features,
            purpose=purpose,
            purpose_source=purpose_source,
            imports=file_imports,
        )

    # トップレベル関数
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            entry = _process_node(node)
            if entry:
                yield entry
        elif isinstance(node, ast.ClassDef):
            for item in ast.iter_child_nodes(node):
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    entry = _process_node(item, class_name=node.name)
                    if entry:
                        yield entry


def scan_codebase(
    scan_dirs: list[Path],
    exclude_dirs: frozenset[str] = DEFAULT_EXCLUDES,
    verbose: bool = False,
) -> list[FusionEntry]:
    """コードベースをスキャンし FusionEntry のリストを生成"""
    entries: list[FusionEntry] = []

    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            if verbose:
                print(f"  ⚠️ {scan_dir} が存在しません、スキップ")
            continue

        for py_file in sorted(scan_dir.rglob("*.py")):
            if set(py_file.parts) & exclude_dirs:
                continue
            entries.extend(scan_file(py_file))

    return entries


# --- 直交性分析 ---

@dataclass
class OrthogonalityResult:
    """直交性分析の結果

    直交性スコア = (cat_a + cat_b) / (cat_a + cat_b + cat_c)
      1.0 = 完全直交 (冗長なし)
      0.0 = 完全重複 (CCL と PURPOSE が結合)
    """
    total: int = 0
    unique_ccl: int = 0
    unique_purpose: int = 0

    # カテゴリ集計
    cat_a_count: int = 0  # 同一CCL × 異なるPURPOSE
    cat_b_count: int = 0  # 同一PURPOSE × 異なるCCL
    cat_c_count: int = 0  # 真の冗長 (同一CCL × 同一PURPOSE)

    # 詳細 (上位のみ)
    cat_a_groups: list = field(default_factory=list)
    cat_b_groups: list = field(default_factory=list)
    cat_c_groups: list = field(default_factory=list)

    @property
    def score(self) -> float:
        """直交性スコア"""
        denom = self.cat_a_count + self.cat_b_count + self.cat_c_count
        return (self.cat_a_count + self.cat_b_count) / denom if denom > 0 else 1.0


def analyze_orthogonality(
    entries: list[FusionEntry],
    max_detail_groups: int = 10,
) -> OrthogonalityResult:
    """直交性を分析

    Args:
        entries: FusionEntry のリスト
        max_detail_groups: 詳細を保持するグループの最大数
    """
    # CCL でグループ化
    ccl_groups: dict[str, list[FusionEntry]] = defaultdict(list)
    for e in entries:
        ccl_groups[e.ccl_expr].append(e)

    # PURPOSE でグループ化
    purpose_groups: dict[str, list[FusionEntry]] = defaultdict(list)
    for e in entries:
        purpose_groups[e.purpose].append(e)

    result = OrthogonalityResult(
        total=len(entries),
        unique_ccl=len(ccl_groups),
        unique_purpose=len(purpose_groups),
    )

    # カテゴリ A: 同一CCL × 異なるPURPOSE
    for ccl, group in ccl_groups.items():
        purposes = set(e.purpose for e in group)
        if len(group) >= 2 and len(purposes) >= 2:
            result.cat_a_count += len(group)
            if len(result.cat_a_groups) < max_detail_groups:
                result.cat_a_groups.append({
                    "ccl": ccl[:100],
                    "members": [e.short_location for e in group[:5]],
                    "purposes": list(purposes)[:5],
                })

    # カテゴリ B: 同一PURPOSE × 異なるCCL
    for purpose, group in purpose_groups.items():
        ccls = set(e.ccl_expr for e in group)
        if len(group) >= 2 and len(ccls) >= 2:
            result.cat_b_count += len(group)
            if len(result.cat_b_groups) < max_detail_groups:
                result.cat_b_groups.append({
                    "purpose": purpose[:100],
                    "members": [e.short_location for e in group[:5]],
                })

    # カテゴリ C: 真の冗長 (同一CCL × 同一PURPOSE)
    for ccl, group in ccl_groups.items():
        if len(group) < 2:
            continue
        purpose_sub: dict[str, list[FusionEntry]] = defaultdict(list)
        for e in group:
            purpose_sub[e.purpose].append(e)
        for purpose, subgroup in purpose_sub.items():
            if len(subgroup) >= 2:
                result.cat_c_count += len(subgroup)
                if len(result.cat_c_groups) < max_detail_groups:
                    result.cat_c_groups.append({
                        "ccl": ccl[:80],
                        "purpose": purpose[:60],
                        "members": [e.short_location for e in subgroup],
                    })

    return result


# --- 自由の検出 (VISION v0.3.0 §1.6-1.8) ---

# 53d ベクトルの分類階級 (SOURCE: code_ingest.py L563-852)
# 各次元群は異なる「忘却の深度」に対応する
TAXONOMIC_LEVELS: dict[str, tuple[int, int]] = {
    # 基本形状 — 「界」レベル: 全てのコードが共有する基本量
    "basic":    (0, 6),     # nt, n_seq, n_block, n_call, n_builtin, n_method
    # 制御構造 — 「門」レベル: 手筋 (guard-return 等) の基本要素
    "control":  (6, 13),    # if/for/while/try/with フラグ + カウント
    # データ型 — 「綱」レベル: 扱うデータの種類
    "datatype": (13, 18),   # str, num, nil+bool, pred, n_yen
    # 構造パターン — 「目」レベル: 合成の仕方
    "pattern":  (18, 29),   # mx, seq_density, product, dual, union, and, hash, mb_ratio, type_annot, guard, product_density
    # AST 詳細 — 「科」レベル: Python 固有の構文パターン
    "ast":      (29, 45),   # ListComp...Starred (16d)
    # 型分布 — 「属」レベル: S/T/P/M の割合
    "typedist": (45, 49),   # S率, T率, P率, M率
    # 型フロー — 「種」レベル: 計算の流れパターン (最も細かい差異)
    "typeflow": (49, 53),   # seq_len, max_T_run, S→T遷移, T→S遷移
}


def zscore_normalize(entries: list[FusionEntry]) -> None:
    """全エントリの ccl_features_43d を Z-score 正規化する (in-place)。

    各次元の mean/std を計算し、(x - mean) / std に変換。
    std=0 の死次元は 0 に設定。
    正規化により、スケールの異なる次元間の比較が公平になる。
    """
    valid = [e for e in entries if e.ccl_features_43d and len(e.ccl_features_43d) >= 43]
    if not valid:
        return

    n_dims = len(valid[0].ccl_features_43d)
    n = len(valid)

    # 各次元の mean/std を計算
    means = [0.0] * n_dims
    for e in valid:
        for d in range(n_dims):
            means[d] += e.ccl_features_43d[d]
    means = [m / n for m in means]

    stds = [0.0] * n_dims
    for e in valid:
        for d in range(n_dims):
            stds[d] += (e.ccl_features_43d[d] - means[d]) ** 2
    stds = [(s / n) ** 0.5 for s in stds]

    # 正規化 (std=0 → 0 に設定)
    for e in valid:
        e.ccl_features_43d = [
            (e.ccl_features_43d[d] - means[d]) / stds[d] if stds[d] > 0 else 0.0
            for d in range(n_dims)
        ]


def _cosine_similarity(a: list[float], b: list[float],
                        dim_range: tuple[int, int] | None = None) -> float:
    """コサイン類似度を計算。dim_range で次元のスライスを指定可能。"""
    if not a or not b:
        return 0.0
    if dim_range:
        start, end = dim_range
        a = a[start:end]
        b = b[start:end]
    if len(a) != len(b) or len(a) == 0:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _files_share_import(entry_a: FusionEntry, entry_b: FusionEntry) -> bool:
    """二つのエントリのファイルが import graph で接続されているか判定

    §1.7: 射 h の存在 = A のファイルが B のモジュールを import している、またはその逆。
    """
    stem_a = Path(entry_a.filepath).stem
    stem_b = Path(entry_b.filepath).stem
    for imp in entry_a.imports:
        if stem_b in imp:
            return True
    for imp in entry_b.imports:
        if stem_a in imp:
            return True
    return False


def _purpose_similarity(a: str, b: str) -> float:
    """PURPOSE テキストの Jaccard 類似度 (単語ベース、軽量)"""
    if not a or not b:
        return 0.0
    # 日本語対応: スペースで分割 (docstring は英語混在が多い)
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union) if union else 0.0


@dataclass
class FreedomResult:
    """二軸自由検出の結果 (VISION v0.3.0 §2.1)

    四象限:
      🔴 構造≈同型 + PURPOSE≈同一 + 独立 → リファクタリング候補 (真の冗長)
      ⚠️ 構造≈同型 + PURPOSE異         → 正当な分離
      🟡 構造≠同型 + PURPOSE≈同一       → 代替実装検討
      ✅ 構造≠同型 + PURPOSE異           → 独立 (問題なし)
    """
    level: str = "all"               # 構造比較の分類階級
    total_pairs_checked: int = 0

    # 四象限カウント
    red_count: int = 0               # 🔴 構造同型 + PURPOSE同一 + 独立 (= 真の自由)
    warn_count: int = 0              # ⚠️ 構造同型 + PURPOSE異
    yellow_count: int = 0            # 🟡 構造異 + PURPOSE同一 (構造閾値以下)
    green_count: int = 0             # ✅ 独立

    # 接続判定
    connected_count: int = 0         # 構造同型だが参照接続あり (= symlink)

    # 詳細
    red_pairs: list = field(default_factory=list)     # 🔴 リファクタリング候補
    warn_pairs: list = field(default_factory=list)    # ⚠️ 正当分離
    connected_pairs: list = field(default_factory=list)  # 接続済み

    @property
    def freedom_ratio(self) -> float:
        """真の自由率 = 🔴 / (🔴 + 接続済み)。低いほど kalon に近い"""
        denom = self.red_count + self.connected_count
        return self.red_count / denom if denom > 0 else 0.0

    @property
    def structural_similar(self) -> int:
        """構造的に類似なペアの総数"""
        return self.red_count + self.warn_count + self.connected_count


def analyze_freedom(
    entries: list[FusionEntry],
    cosine_threshold: float = 0.95,
    purpose_threshold: float = 0.3,
    level: str = "pattern",
    max_detail_pairs: int = 20,
) -> FreedomResult:
    """二軸の自由を検出する (VISION v0.3.0 §1.6-1.8, §2.1)
    # [OPTIMIZED] O(N^2) ループの事前計算とベクトル化
    """
    dim_range = TAXONOMIC_LEVELS.get(level)
    valid = [e for e in entries if e.ccl_features_43d and len(e.ccl_features_43d) >= 43]
    n = len(valid)

    result = FreedomResult(level=level)
    if n < 2:
        return result

    # --- 1. 事前計算 ---
    try:
        import numpy as np
        A = np.array([e.ccl_features_43d for e in valid], dtype=np.float32)
        if dim_range:
            start, end = dim_range
            A = A[:, start:end]
        norms = np.linalg.norm(A, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        A_norm = A / norms
        sim_matrix = A_norm @ A_norm.T
        use_np = True
    except ImportError:
        use_np = False

    purpose_words = [set(e.purpose.lower().split()) if e.purpose else set() for e in valid]
    stems = [Path(e.filepath).stem for e in valid]

    for i in range(n):
        for j in range(i + 1, n):
            result.total_pairs_checked += 1

            # --- 2. 構造軸 (cosine) ---
            if use_np:
                cos = float(sim_matrix[i, j])
            else:
                cos = _cosine_similarity(
                    valid[i].ccl_features_43d, valid[j].ccl_features_43d,
                    dim_range=dim_range,
                )
            
            struct_similar = cos >= cosine_threshold

            # 構造が同型でない場合は早期リターン (99% のペアをスキップ)
            if not struct_similar:
                continue

            # --- 3. 存在軸 (Jaccard) ---
            wa, wb = purpose_words[i], purpose_words[j]
            if wa and wb:
                psim = len(wa & wb) / len(wa | wb)
            else:
                psim = 0.0
                
            purpose_similar = psim >= purpose_threshold

            if struct_similar and purpose_similar:
                # 構造同型 + PURPOSE同一 → 接続チェック
                connected = False
                if valid[i].filepath == valid[j].filepath:
                    connected = True
                else:
                    sa, sb = stems[i], stems[j]
                    if any(sb in imp for imp in valid[i].imports) or any(sa in imp for imp in valid[j].imports):
                        connected = True
                
                if connected:
                    result.connected_count += 1
                    if len(result.connected_pairs) < max_detail_pairs:
                        result.connected_pairs.append({
                            "a": valid[i].short_location,
                            "b": valid[j].short_location,
                            "cos": round(cos, 4),
                            "psim": round(psim, 3),
                            "verdict": "symlink (正当)",
                        })
                else:
                    # 🔴 真の冗長
                    result.red_count += 1
                    if len(result.red_pairs) < max_detail_pairs:
                        result.red_pairs.append({
                            "a": valid[i].short_location,
                            "b": valid[j].short_location,
                            "cos": round(cos, 4),
                            "psim": round(psim, 3),
                            "purpose_a": valid[i].purpose[:60],
                            "purpose_b": valid[j].purpose[:60],
                            "verdict": "🔴 copy (真の冗長)",
                        })
            elif struct_similar and not purpose_similar:
                # ⚠️ 正当な分離
                result.warn_count += 1
                if len(result.warn_pairs) < max_detail_pairs:
                    result.warn_pairs.append({
                        "a": valid[i].short_location,
                        "b": valid[j].short_location,
                        "cos": round(cos, 4),
                        "psim": round(psim, 3),
                        "verdict": "⚠️ 正当分離",
                    })

    return result


# --- 階級別自由の検出 (分類階級モデル) ---

# PURPOSE: 49d ベクトルの分類階級定義
# 📖 参照: code_ingest.py L979-998 (ccl_feature_vector 49d)
#   ccl_features: 29d (dim 0-28)
#   ccl_structural_counts: 12d (dim 29-40)
#   ccl_type_features: 8d (dim 41-48)
# 全体 cosine は「ゲノム比較」= ゴリラ ≈ 人間 (95%)。
# 階級別 cosine で「種レベルの差異」を検出する。
TAXONOMIC_RANKS: dict[str, tuple[int, int]] = {
    # ccl_features (29d) の分解
    "scale":    (0, 4),     # 基本形状 — nt, n_seq, n_assign, n_block
    "call":     (4, 9),     # 呼出パターン — n_call, n_builtin, n_method, n_var, n_uvar
    "control":  (9, 16),    # 制御構造 — if/for/while/try/with フラグ + カウント
    "data":     (16, 22),   # データ型 — str, num, nil+bool, pred, return, def
    "derived":  (22, 29),   # 派生指標 — arity, arsum, max_depth, seq_density, var_reuse + 追加2d
    # ccl_structural_counts (12d)
    "ast":      (29, 41),   # 構造カウント — comp, dcomp, scomp, gen, except, raise 等
    # ccl_type_features (8d) — Aletheia n=2
    "typeflow": (41, 49),   # 型フロー — S/T/P/M 分布 + フローメトリクス
}


@dataclass
class HierarchicalFreedomResult:
    """階級別「自由」検出の結果

    分類階級モデル: 51d ベクトルを7階級に分割し、
    各階級ごとに cosine similarity を測定する。

    全体 cosine = ゲノム比較 (ゴリラ ≈ 人間)
    階級別 cosine = 種レベル比較 (ゴリラ ≠ 人間)
    """
    total_pairs_checked: int = 0
    # 各階級の同型ペア数
    rank_similar: dict = field(default_factory=dict)  # {rank: count}
    # 全階級で同型かつ独立 (最もリファクタリング優先度が高い)
    full_independent: int = 0
    # 特定階級で同型かつ独立
    rank_independent: dict = field(default_factory=dict)  # {rank: count}
    # 詳細: 独立同型ペア (階級別スコア付き)
    independent_pairs: list = field(default_factory=list)

    @property
    def summary(self) -> dict:
        """階級別のサマリー"""
        return {
            "total_pairs": self.total_pairs_checked,
            "全階級一致かつ独立": self.full_independent,
            "階級別同型数": self.rank_similar,
            "階級別独立数": self.rank_independent,
        }


def _cosine_subvector(
    a: list[float], b: list[float], start: int, end: int,
) -> float:
    """サブベクトル (a[start:end], b[start:end]) の cosine similarity"""
    if end > len(a) or end > len(b):
        return 0.0
    sub_a = a[start:end]
    sub_b = b[start:end]
    dot = sum(x * y for x, y in zip(sub_a, sub_b))
    norm_a = sum(x * x for x in sub_a) ** 0.5
    norm_b = sum(x * x for x in sub_b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def analyze_freedom_hierarchical(
    entries: list[FusionEntry],
    rank_thresholds: dict[str, float] | None = None,
    target_ranks: list[str] | None = None,
    max_detail_pairs: int = 20,
) -> HierarchicalFreedomResult:
    """階級別「自由」を検出する
    # [OPTIMIZED] 類似度行列の事前計算とベクトル化
    """
    default_thresholds = {
        "scale":    0.85,
        "call":     0.88,
        "control":  0.90,
        "data":     0.88,
        "derived":  0.90,
        "ast":      0.92,
        "typeflow": 0.93,
    }
    thresholds = {**default_thresholds, **(rank_thresholds or {})}
    ranks_to_check = target_ranks or list(TAXONOMIC_RANKS.keys())

    valid = [e for e in entries if e.ccl_features_43d and len(e.ccl_features_43d) >= 49]
    n = len(valid)

    result = HierarchicalFreedomResult(
        rank_similar={r: 0 for r in ranks_to_check},
        rank_independent={r: 0 for r in ranks_to_check},
    )

    if n < 2:
        return result

    # --- 1. 事前計算 ---
    try:
        import numpy as np
        A = np.array([e.ccl_features_43d for e in valid], dtype=np.float32)
        rank_sims = {}
        for rank in ranks_to_check:
            start, end = TAXONOMIC_RANKS[rank]
            sub_A = A[:, start:end]
            norms = np.linalg.norm(sub_A, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            sub_A_norm = sub_A / norms
            rank_sims[rank] = sub_A_norm @ sub_A_norm.T
        use_np = True
    except ImportError:
        use_np = False

    stems = [Path(e.filepath).stem for e in valid]

    # --- 2. O(N^2) ループ ---
    for i in range(n):
        for j in range(i + 1, n):
            result.total_pairs_checked += 1

            rank_scores: dict[str, float] = {}
            matches: dict[str, bool] = {}

            # 各階級の cosine
            for rank in ranks_to_check:
                if use_np:
                    cos = float(rank_sims[rank][i, j])
                else:
                    start, end = TAXONOMIC_RANKS[rank]
                    cos = _cosine_subvector(valid[i].ccl_features_43d, valid[j].ccl_features_43d, start, end)
                
                rank_scores[rank] = cos
                is_match = cos >= thresholds.get(rank, 0.9)
                matches[rank] = is_match
                if is_match:
                    result.rank_similar[rank] += 1

            all_match = all(matches.values())

            # どの階級でも同型でない場合、独立性や詳細記録は不要
            has_any_match = any(matches.values())
            if not has_any_match:
                continue

            # 独立性判定
            connected = False
            if valid[i].filepath == valid[j].filepath:
                connected = True
            else:
                sa, sb = stems[i], stems[j]
                if any(sb in imp for imp in valid[i].imports) or any(sa in imp for imp in valid[j].imports):
                    connected = True

            if not connected:
                if all_match:
                    result.full_independent += 1

                for rank in ranks_to_check:
                    if matches[rank]:
                        result.rank_independent[rank] += 1

                typeflow_match = matches.get("typeflow", False)
                if typeflow_match and len(result.independent_pairs) < max_detail_pairs:
                    result.independent_pairs.append({
                        "a": valid[i].short_location,
                        "b": valid[j].short_location,
                        "rank_scores": {k: round(v, 4) for k, v in rank_scores.items()},
                        "全階級一致": all_match,
                        "purpose_a": valid[i].purpose[:60],
                        "purpose_b": valid[j].purpose[:60],
                    })

    return result


# --- I/O ---

def save_index(entries: list[FusionEntry], path: Path) -> None:
    """融合インデックスを JSONL で保存"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")


def load_index(path: Path) -> list[FusionEntry]:
    """融合インデックスを JSONL から読み込み"""
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entries.append(FusionEntry.from_dict(json.loads(line)))
    return entries
