from __future__ import annotations
# PROOF: [L2/Dendron] <- mekhane/dendron/circulation_detector.py
"""
PROOF: [L2/Dendron] このファイルは存在しなければならない

existence_theorem.md §6 → 循環的存在理由を検出する必要がある
  → コード依存グラフから SCC を抽出し孤立循環を判定する
  → circulation_detector.py が担う

Q.E.D.

---

Circulation Detector — Q-Series 循環検出の Dendron 実装

PURPOSE: Python コードベースの **import レベルの** 依存グラフを構築し、
  循環的依存 (SCC) を検出・分類する。
  注: コールグラフ・データフロー・動的依存は対象外 (Level 0 検出器)。

理論的基盤:
  - existence_theorem.md §6: Q-Series 循環検出
  - circulation_theorem.md §4.1: K₆ 上の二重テンソル場
  - 循環 ≠ 因果 (P₁ /kat 2026-03-15)

設計原理:
  - SCC ≈ Q-series のアナロジー (import レベルの循環パターン)
    注: 座標間テンソル Q_{ij} との正式な関手は未定義
  - 孤立判定: h^X = 0 (existence_theorem 3軸中 第1軸のみ)
    注: ΔF(X), d(X, Fix) は未実装
  - 循環 ≠ 悪。「孤立した循環」のみを除去候補として報告
"""


import ast
import logging
import math
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# --- 存在定理 §1.2 統合判定ビットフラグ (Phase 4) ---
# PURPOSE: 複合的な存在理由の欠如を表現する (例: REDUNDANT | UNSTABLE)
EX_HEALTHY  = 0x00  # 全軸健全
EX_ISOLATED = 0x01  # yoneda_score == 0 (接続なし)
EX_FRAGILE  = 0x02  # yoneda_tier == "fragile" (脆弱な接続)
EX_REDUNDANT = 0x04  # stiffness ≤ 0 (除去で改善)
EX_UNSTABLE = 0x08  # kalon_gf_distance > 0.8 (G∘F で大幅に刈り込める)


# PURPOSE: 1つの SCC の分類結果を構造化し、3軸存在判定を可能にする
@dataclass
class CirculationResult:
    """1つの循環 (SCC) の分類結果.

    存在定理 (existence_theorem.md §1) の3軸:
      - Yoneda 軸: h^X — 接続の豊かさ
      - VFE 軸: ΔF(X) — 除去インパクト (stiffness)
      - Kalon 軸: d(X, Fix) — 不動点距離
    """

    members: list[str]  # SCC に含まれるモジュールパス
    size: int  # SCC のサイズ
    external_in: int  # SCC 外から SCC 内への参照数 (h^{SCC})
    external_out: int  # SCC 内から SCC 外への参照数
    is_isolated: bool  # 孤立循環か (external_in == 0)
    verdict: str  # "isolated" | "connected" | "self"
    # --- §2 Yoneda 軸: 接続性 (existence_theorem §2) ---
    yoneda_score: int = 0  # |h^X| = external_in (接続の豊かさ)
    yoneda_diversity: float = 0.0  # 参照元の多様性 (0.0〜1.0)
    yoneda_tier: str = ""  # Phase 1: "orphan" / "fragile" / "robust"
    yoneda_package_diversity: float = 0.0  # Phase 1: パッケージレベル多様性
    # --- §3 VFE 軸: 除去インパクト (existence_theorem §3.3 stiffness) ---
    accuracy_loss: float = 0.0  # SCC 除去で壊れる依存の割合 (Accuracy 寄与)
    complexity_cost: float = 0.0  # SCC が追加する複雑さの割合 (Complexity 寄与)
    stiffness: float = 0.0  # accuracy_loss - complexity_cost (ΔF の符号)
    removal_broken_paths: int = 0  # Phase 2: SCC 除去で到達不能になるペア数
    removal_cascade: int = 0  # Phase 2: SCC 除去後に孤立するノード数
    stiffness_normalized: float = 0.0  # Phase 2: stiffness / log2(size + 1)
    # --- §4 Kalon 軸: 不動点距離 (existence_theorem §4) ---
    kalon_distance: float = 0.0  # 1 - internal_density (0=不動点, 1=不安定)
    kalon_gf_distance: float = 0.0  # Phase 3: |SCC - Fix(G∘F)| / |SCC|
    kalon_gf_iterations: int = 0  # Phase 3: 不動点到達までの反復回数
    kalon_cohesion: float = 0.0  # Phase 3: min(入次数,出次数) の平均 / (n-1)
    # --- 統合判定 ---
    existence_verdict: str = ""  # 3軸統合の存在判定
    existence_flags: int = 0  # Phase 4: ビットフラグ (EX_ISOLATED 等)


# PURPOSE: 循環検出パイプラインの全結果を集約し、Markdown レポート生成を可能にする
@dataclass
class CirculationReport:
    """循環検出の全体レポート."""

    total_modules: int
    total_edges: int
    sccs: list[CirculationResult]
    isolated_count: int
    connected_count: int

    @property
    def has_issues(self) -> bool:
        """除去候補 (孤立循環) が存在するか."""
        return self.isolated_count > 0

    # PURPOSE: Markdown レポートを生成する (Phase 1-4 深化版)
    def to_markdown(self) -> str:
        """Markdown 形式のレポートを生成."""
        lines = [
            "# 🔄 循環検出レポート (Q-Series)",
            "",
            f"- 総モジュール数: {self.total_modules}",
            f"- 総依存エッジ数: {self.total_edges}",
            f"- 循環グループ (SCC): {len(self.sccs)}",
            f"  - 孤立循環 (除去候補): {self.isolated_count}",
            f"  - 接続循環 (正当): {self.connected_count}",
            "",
        ]

        if not self.sccs:
            lines.append("✅ 循環的依存は検出されませんでした。")
            return "\n".join(lines)

        # 3軸統合テーブル (全 SCC を存在判定順に表示)
        sorted_sccs = sorted(
            self.sccs,
            key=lambda s: (0 if "❌" in s.existence_verdict else 1, -s.size),
        )

        lines.append("## 存在定理 3軸判定")
        lines.append("")
        lines.append(
            "| # | サイズ | メンバー "
            "| Tier "
            "| h^X | Div "
            "| Stiff "
            "| GF距離 "
            "| 存在判定 |"
        )
        lines.append(
            "|---:|---:|:---"
            "|:---"
            "|---:|---:"
            "|---:"
            "|---:"
            "|:---|"
        )
        for i, scc in enumerate(sorted_sccs, 1):
            members_str = ", ".join(
                Path(m).stem for m in scc.members[:5]
            )
            if len(scc.members) > 5:
                members_str += f" (+{len(scc.members) - 5})"
            lines.append(
                f"| {i} | {scc.size} | {members_str} "
                f"| {scc.yoneda_tier} "
                f"| {scc.yoneda_score} | {scc.yoneda_diversity:.2f} "
                f"| {scc.stiffness:+.4f} "
                f"| {scc.kalon_gf_distance:.2f} "
                f"| {scc.existence_verdict} |"
            )
        lines.append("")

        # 詳細セクション (除去影響・結束度・ビットフラグ)
        has_details = any(
            scc.removal_broken_paths > 0
            or scc.removal_cascade > 0
            or scc.existence_flags != EX_HEALTHY
            for scc in sorted_sccs
        )
        if has_details:
            lines.append("### 詳細メトリクス")
            lines.append("")
            lines.append(
                "| # | Broken Paths | Cascade "
                "| Stiff(norm) "
                "| GF反復 | 結束度 "
                "| Flags |"
            )
            lines.append(
                "|---:|---:|---:"
                "|---:"
                "|---:|---:"
                "|:---|"
            )
            for i, scc in enumerate(sorted_sccs, 1):
                # ビットフラグを人間可読に変換
                flag_names = []
                if scc.existence_flags & EX_ISOLATED:
                    flag_names.append("ISOLATED")
                if scc.existence_flags & EX_FRAGILE:
                    flag_names.append("FRAGILE")
                if scc.existence_flags & EX_REDUNDANT:
                    flag_names.append("REDUNDANT")
                if scc.existence_flags & EX_UNSTABLE:
                    flag_names.append("UNSTABLE")
                flags_str = " | ".join(flag_names) if flag_names else "HEALTHY"

                lines.append(
                    f"| {i} | {scc.removal_broken_paths} | {scc.removal_cascade} "
                    f"| {scc.stiffness_normalized:+.4f} "
                    f"| {scc.kalon_gf_iterations} | {scc.kalon_cohesion:.2f} "
                    f"| {flags_str} |"
                )
            lines.append("")

        lines.append("> **3軸判定基準** (existence_theorem.md §1.2):")
        lines.append("> - h^X = 0 → ❌ 孤立 (接続なし)")
        lines.append("> - stiffness ≤ 0 → ❌ 冗長 (除去で改善)")
        lines.append("> - GF距離 > 0.8 → ⚠️ 不安定 (G∘F で大幅刈込可能)")
        lines.append("> - 全軸健全 → ✅ 存在理由あり")
        lines.append(">")
        lines.append("> 循環 ≠ 因果。相互依存は即座に悪ではない。")

        return "\n".join(lines)


# PURPOSE: Python AST から import 文を抽出する
def extract_imports(filepath: Path) -> list[str]:
    """Python ファイルから import しているモジュール名を抽出.

    Args:
        filepath: 対象の .py ファイル

    Returns:
        import しているモジュール名のリスト
    """
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError, OSError) as e:
        logger.debug(f"[CirculationDetector] パース失敗: {filepath}: {e}")
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return imports


# PURPOSE: モジュール名をファイルパスに解決する
def resolve_module_to_path(
    module_name: str,
    source_file: Path,
    root: Path,
    known_modules: dict[str, Path],
) -> Optional[Path]:
    """Python モジュール名をファイルパスに解決.

    Args:
        module_name: import 対象のモジュール名 (e.g. "mekhane.dendron.checker")
        source_file: import 元のファイル
        root: プロジェクトルート
        known_modules: モジュール名 → ファイルパスのマップ

    Returns:
        解決されたファイルパス (見つからない場合は None)
    """
    # 完全一致
    if module_name in known_modules:
        return known_modules[module_name]

    # 親モジュールマッチ (mekhane.dendron.checker → mekhane.dendron)
    parts = module_name.split(".")
    for i in range(len(parts), 0, -1):
        prefix = ".".join(parts[:i])
        if prefix in known_modules:
            return known_modules[prefix]

    return None


# PURPOSE: 依存グラフを構築するクラス
class DependencyGraph:
    """Python コードベースの import 依存グラフ.

    有向グラフ G = (V, E) を構築:
      V = Python モジュール (ファイル)
      E = import 関係 (A が B を import → A→B)
    """

    # PURPOSE: 初期化
    def __init__(self):
        self.nodes: set[str] = set()  # ファイルパス (文字列)
        self.edges: dict[str, set[str]] = defaultdict(set)  # src → {dst}
        self.reverse_edges: dict[str, set[str]] = defaultdict(set)  # dst → {src}
        self._module_map: dict[str, Path] = {}  # モジュール名 → パス

    # PURPOSE: モジュールを走査してノードマップを構築する (Phase 1)
    def scan_modules(self, root: Path, package_prefix: str = "") -> list[Path]:
        """ディレクトリをスキャンしてモジュールマップを構築 (原子的 Phase 1).

        build() の Phase 1 のみを独立実行。エッジ解決は resolve_edges() で行う。

        Args:
            root: スキャンするルートディレクトリ
            package_prefix: パッケージの接頭辞 (e.g. "mekhane")

        Returns:
            検出された Python ファイルのリスト
        """
        if not root.exists():
            logger.warning(f"[DependencyGraph] ディレクトリが見つからない: {root}")
            return []

        py_files = [
            f
            for f in root.rglob("*.py")
            if "__pycache__" not in str(f)
            and ".venv" not in str(f)
        ]

        for f in py_files:
            rel = f.relative_to(root)
            # ファイルパスをモジュール名に変換
            parts = list(rel.parts)
            if parts[-1] == "__init__.py":
                parts = parts[:-1]
            else:
                parts[-1] = parts[-1].replace(".py", "")

            if package_prefix:
                module_name = package_prefix + "." + ".".join(parts)
            else:
                module_name = ".".join(parts)

            self._module_map[module_name] = f
            node_key = str(f)
            self.nodes.add(node_key)

        return py_files

    # PURPOSE: import 関係を解決してエッジを構築する (Phase 2)
    def resolve_edges(self, py_files: list[Path], root: Path) -> int:
        """モジュール間の import 関係を解決してエッジを構築 (原子的 Phase 2).

        scan_modules() でモジュールマップが構築済みであること。

        Args:
            py_files: scan_modules() が返した Python ファイルのリスト
            root: プロジェクトルート

        Returns:
            検出されたエッジ数
        """
        for f in py_files:
            node_key = str(f)
            imports = extract_imports(f)

            for imp in imports:
                target = resolve_module_to_path(
                    imp, f, root, self._module_map
                )
                if target is not None:
                    target_key = str(target)
                    if target_key in self.nodes and target_key != node_key:
                        self.edges[node_key].add(target_key)
                        self.reverse_edges[target_key].add(node_key)

        total_edges = sum(len(e) for e in self.edges.values())
        logger.info(
            f"[DependencyGraph] エッジ解決完了: {total_edges} エッジ"
        )
        return total_edges

    # PURPOSE: スキャンとエッジ解決を一括で実行する便利メソッド
    def build(self, root: Path, package_prefix: str = "") -> int:
        """ディレクトリ内の Python ファイルをスキャンしてグラフを構築.

        scan_modules() + resolve_edges() の一括実行。後方互換性のために維持。

        Args:
            root: スキャンするルートディレクトリ
            package_prefix: パッケージの接頭辞 (e.g. "mekhane")

        Returns:
            検出されたモジュール数
        """
        py_files = self.scan_modules(root, package_prefix)
        if not py_files:
            return 0
        self.resolve_edges(py_files, root)
        logger.info(
            f"[DependencyGraph] グラフ構築完了: "
            f"{len(self.nodes)} モジュール, {self.edge_count} エッジ"
        )
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        """総エッジ数."""
        return sum(len(e) for e in self.edges.values())


# PURPOSE: Tarjan のアルゴリズムで強連結成分を抽出する
def find_sccs(graph: DependencyGraph) -> list[list[str]]:
    """Tarjan のアルゴリズムで強連結成分 (SCC) を抽出.

    サイズ 2 以上の SCC のみ返す (サイズ 1 = 自己循環なし = 非循環)。

    Args:
        graph: 依存グラフ

    Returns:
        SCC のリスト (各 SCC はノードのリスト)
    """
    index_counter = [0]
    stack: list[str] = []
    lowlink: dict[str, int] = {}
    index: dict[str, int] = {}
    on_stack: set[str] = set()
    sccs: list[list[str]] = []

    def strongconnect(v: str) -> None:
        index[v] = index_counter[0]
        lowlink[v] = index_counter[0]
        index_counter[0] += 1
        stack.append(v)
        on_stack.add(v)

        for w in graph.edges.get(v, set()):
            if w not in index:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w in on_stack:
                lowlink[v] = min(lowlink[v], index[w])

        # v がルートなら SCC をポップ
        if lowlink[v] == index[v]:
            scc: list[str] = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                scc.append(w)
                if w == v:
                    break
            if len(scc) >= 2:
                sccs.append(scc)

    for v in graph.nodes:
        if v not in index:
            strongconnect(v)

    return sccs


# PURPOSE: G∘F 反復で SCC の不動点を求める (CKDF §5.2, Phase 3)
def _compute_gf_fixpoint(
    scc_set: set[str],
    edges: dict[str, set[str]],
    reverse_edges: dict[str, set[str]],
) -> tuple[set[str], int]:
    """G∘F 反復で SCC 内の不動点 (循環の核) を求める.

    F (発散): SCC 内の各ノードの到達可能範囲 (= 次のステップに必要)
    G (収束): SCC 内で入次数=0 のノードを除去 (循環に不要)

    反復: 全体 → 刈り込み → ... → Fix (もう刈れない)
    計算量: O(N²) = P (CKDF §5.2: 有限束なら最大 N 回)

    Args:
        scc_set: SCC に含まれるノード集合
        edges: 順方向エッジ
        reverse_edges: 逆方向エッジ

    Returns:
        (不動点ノード集合, 反復回数)
    """
    current = set(scc_set)
    iterations = 0

    while True:
        # G (収束): 現在の部分グラフ内で入次数=0 のノードを除去
        # 入次数=0 = 循環に寄与しない末端ノード
        to_remove: set[str] = set()
        for node in current:
            # 現在の部分グラフ内での入次数
            in_degree = sum(
                1 for src in reverse_edges.get(node, set())
                if src in current
            )
            if in_degree == 0:
                to_remove.add(node)

        if not to_remove:
            # 不動点到達: もう刈り込めない
            break

        current -= to_remove
        iterations += 1

        if not current:
            # 全て刈り込まれた (循環が存在しない退化ケース)
            break

    return current, iterations


# PURPOSE: SCC 除去による到達性への影響を計算する (Phase 2)
def _compute_removal_impact(
    graph: DependencyGraph, scc_set: set[str]
) -> tuple[int, int]:
    """SCC を仮想除去し、残存グラフの到達性を計算.

    Args:
        graph: 依存グラフ
        scc_set: SCC に含まれるノード集合

    Returns:
        (broken_paths: 到達不能になるペア数, cascade: 孤立するノード数)
    """
    # SCC 除去後のノード集合
    remaining_nodes = graph.nodes - scc_set
    if not remaining_nodes:
        return 0, 0

    # SCC 除去後のエッジで到達性を計算
    # 各ノードから BFS で到達可能なノードを数える
    def bfs_reachable(start: str) -> set[str]:
        visited: set[str] = set()
        queue = deque([start])
        visited.add(start)
        while queue:
            node = queue.popleft()
            for dst in graph.edges.get(node, set()):
                if dst in remaining_nodes and dst not in visited:
                    visited.add(dst)
                    queue.append(dst)
        return visited

    # SCC 除去後に孤立するノード (入次数も出次数もゼロ)
    cascade_count = 0
    for node in remaining_nodes:
        in_deg = sum(
            1 for src in graph.reverse_edges.get(node, set())
            if src in remaining_nodes
        )
        out_deg = sum(
            1 for dst in graph.edges.get(node, set())
            if dst in remaining_nodes
        )
        if in_deg == 0 and out_deg == 0:
            cascade_count += 1

    # 元のグラフでの到達可能ペア (SCC ノードを含む) vs 除去後
    # 効率のため: SCC に隣接するノードからのみ BFS を実行
    # SCC を経由するパスが壊れたペアを推定
    adjacent_nodes: set[str] = set()
    for member in scc_set:
        for src in graph.reverse_edges.get(member, set()):
            if src in remaining_nodes:
                adjacent_nodes.add(src)
        for dst in graph.edges.get(member, set()):
            if dst in remaining_nodes:
                adjacent_nodes.add(dst)

    # SCC 経由のパスが壊れるケース:
    # 「SCC に入力するノード」から「SCC から出力するノード」への到達が
    # SCC 除去後に不可能になるペアを数える
    scc_inputs: set[str] = set()  # SCC に向かうノード
    scc_outputs: set[str] = set()  # SCC から出てくる先のノード
    for member in scc_set:
        for src in graph.reverse_edges.get(member, set()):
            if src in remaining_nodes:
                scc_inputs.add(src)
        for dst in graph.edges.get(member, set()):
            if dst in remaining_nodes:
                scc_outputs.add(dst)

    if not scc_inputs or not scc_outputs:
        return 0, cascade_count

    # SCC 除去後: 各 input から各 output に到達可能か
    broken_paths = 0
    reachability_cache: dict[str, set[str]] = {}
    for src in scc_inputs:
        if src not in reachability_cache:
            reachability_cache[src] = bfs_reachable(src)
        for dst in scc_outputs:
            if dst not in reachability_cache[src]:
                broken_paths += 1

    return broken_paths, cascade_count


# PURPOSE: SCC を分類する (孤立/接続) — 3軸深化版
def classify_sccs(
    graph: DependencyGraph, sccs: list[list[str]]
) -> list[CirculationResult]:
    """各 SCC を孤立/接続に分類し、3軸 + 深化メトリクスで判定.

    Phase 1: Yoneda 品質ティア (orphan/fragile/robust)
    Phase 2: VFE 除去シミュレーション (broken_paths, cascade)
    Phase 3: Kalon G∘F 反復不動点距離 (CKDF §5.2)
    Phase 4: 統合ビットフラグ

    Args:
        graph: 依存グラフ
        sccs: SCC のリスト

    Returns:
        分類結果のリスト
    """
    results = []

    for scc in sccs:
        scc_set = set(scc)
        external_in = 0
        external_out = 0

        for member in scc:
            # SCC 外から member への参照
            for src in graph.reverse_edges.get(member, set()):
                if src not in scc_set:
                    external_in += 1

            # member から SCC 外への参照
            for dst in graph.edges.get(member, set()):
                if dst not in scc_set:
                    external_out += 1

        # --- §3 VFE 軸: stiffness (existence_theorem §3.3) ---
        # Accuracy 寄与: SCC 外から SCC への依存数 / 全エッジ数
        #   → SCC を除去すると壊れる「外部からの参照」の割合
        total_edges = graph.edge_count
        if total_edges > 0:
            accuracy_loss = external_in / total_edges
        else:
            accuracy_loss = 0.0

        # Complexity 寄与: SCC 内部エッジ数 / 全エッジ数
        #   → SCC が系に追加している複雑さの割合
        internal_edges = 0
        for member in scc:
            for dst in graph.edges.get(member, set()):
                if dst in scc_set:
                    internal_edges += 1
        if total_edges > 0:
            complexity_cost = internal_edges / total_edges
        else:
            complexity_cost = 0.0

        # stiffness = accuracy_loss - complexity_cost
        #   > 0: 取り除くと系がより多く壊れる (存在理由あり)
        #   ≤ 0: 取り除いても問題ない or むしろ改善 (冗長)
        stiffness = accuracy_loss - complexity_cost

        # --- §2 Yoneda 軸: 接続性 (existence_theorem §2) ---
        # |h^X| = external_in (SCC に入ってくる射の総数)
        yoneda_score = external_in

        # Diversity(h^X) = |参照元の一意ノード集合| / |全ノード数|
        # 同一モジュールからの複数参照より、多様なモジュールからの参照の方が頑健
        referrer_set: set[str] = set()
        for member in scc:
            for src in graph.reverse_edges.get(member, set()):
                if src not in scc_set:
                    referrer_set.add(src)
        total_nodes = len(graph.nodes)
        if total_nodes > 0:
            yoneda_diversity = len(referrer_set) / total_nodes
        else:
            yoneda_diversity = 0.0

        # Phase 1: Yoneda 品質ティア (existence_theorem §2.2)
        # orphan: |h^X| = 0 — 誰からも参照されない孤島
        # fragile: |h^X| = 1-2 — 少数の依存元、消滅リスクあり
        # robust: |h^X| ≥ 3 — kalon.typos §2 の最小閉構造条件 D≥3 と整合
        if yoneda_score == 0:
            yoneda_tier = "orphan"
        elif yoneda_score <= 2:
            yoneda_tier = "fragile"
        else:
            yoneda_tier = "robust"

        # Phase 1: パッケージレベル多様性
        # 参照元のトップレベルディレクトリ (パッケージ) の多様性
        referrer_packages: set[str] = set()
        all_packages: set[str] = set()
        for node in graph.nodes:
            parts = Path(node).parts
            if parts:
                all_packages.add(parts[0])
        for src in referrer_set:
            parts = Path(src).parts
            if parts:
                referrer_packages.add(parts[0])
        if all_packages:
            yoneda_package_diversity = len(referrer_packages) / len(all_packages)
        else:
            yoneda_package_diversity = 0.0

        # --- §4 Kalon 軸: 不動点距離 (existence_theorem §4) ---
        # 旧メトリク (後方互換): d(SCC, Fix) ≈ 1 - internal_density
        n = len(scc)
        max_internal = n * (n - 1)  # 完全有向グラフのエッジ数
        if max_internal > 0:
            kalon_distance = 1.0 - (internal_edges / max_internal)
        else:
            kalon_distance = 0.0  # サイズ1は自明

        # Phase 3: G∘F 反復不動点距離 (CKDF §5.2)
        # Fix(G∘F)|_{SCC} — SCC 内で「刈り込めないコア」を求める
        fixpoint, gf_iterations = _compute_gf_fixpoint(
            scc_set, graph.edges, graph.reverse_edges
        )
        if n > 0:
            kalon_gf_distance = 1.0 - (len(fixpoint) / n)
        else:
            kalon_gf_distance = 0.0

        # Phase 3: 内部結束度
        # 各ノードの min(入次数, 出次数) の平均 / (n-1)
        # = 循環への寄与度。1.0 に近いほど全員が密に循環に関与
        if n > 1:
            cohesion_sum = 0.0
            for member in scc:
                in_deg = sum(
                    1 for src in graph.reverse_edges.get(member, set())
                    if src in scc_set
                )
                out_deg = sum(
                    1 for dst in graph.edges.get(member, set())
                    if dst in scc_set
                )
                cohesion_sum += min(in_deg, out_deg)
            kalon_cohesion = cohesion_sum / (n * (n - 1))
        else:
            kalon_cohesion = 1.0

        # Phase 2: VFE 除去シミュレーション
        removal_broken_paths, removal_cascade = _compute_removal_impact(
            graph, scc_set
        )

        # Phase 2: サイズ補正 stiffness
        if n > 0:
            stiffness_normalized = stiffness / math.log2(n + 1)
        else:
            stiffness_normalized = 0.0

        # --- 統合判定 ---
        is_isolated = external_in == 0

        if len(scc) == 1:
            verdict = "self"
        elif is_isolated:
            verdict = "isolated"
        else:
            verdict = "connected"

        # Phase 4: ビットフラグ (existence_theorem §1.2)
        flags = EX_HEALTHY
        if yoneda_score == 0:
            flags |= EX_ISOLATED
        if yoneda_tier == "fragile":
            flags |= EX_FRAGILE
        if stiffness <= 0:
            flags |= EX_REDUNDANT
        if kalon_gf_distance > 0.8:
            flags |= EX_UNSTABLE

        # 3軸統合の存在判定 (後方互換: 文字列 verdict 維持)
        if yoneda_score == 0:
            existence_verdict = "❌ 孤立"
        elif stiffness <= 0:
            existence_verdict = "❌ 冗長"
        elif kalon_gf_distance > 0.8:
            existence_verdict = "⚠️ 不安定"
        else:
            existence_verdict = "✅ 存在理由あり"

        results.append(
            CirculationResult(
                members=sorted(scc),
                size=len(scc),
                external_in=external_in,
                external_out=external_out,
                is_isolated=is_isolated,
                verdict=verdict,
                yoneda_score=yoneda_score,
                yoneda_diversity=round(yoneda_diversity, 4),
                yoneda_tier=yoneda_tier,
                yoneda_package_diversity=round(yoneda_package_diversity, 4),
                accuracy_loss=round(accuracy_loss, 4),
                complexity_cost=round(complexity_cost, 4),
                stiffness=round(stiffness, 4),
                removal_broken_paths=removal_broken_paths,
                removal_cascade=removal_cascade,
                stiffness_normalized=round(stiffness_normalized, 4),
                kalon_distance=round(kalon_distance, 4),
                kalon_gf_distance=round(kalon_gf_distance, 4),
                kalon_gf_iterations=gf_iterations,
                kalon_cohesion=round(kalon_cohesion, 4),
                existence_verdict=existence_verdict,
                existence_flags=flags,
            )
        )

    # 孤立を先に、サイズ降順
    results.sort(key=lambda r: (-int(r.is_isolated), -r.size))
    return results


# PURPOSE: 循環検出の全パイプラインを実行する
def detect_circulation(
    root: Path,
    package_prefix: str = "",
) -> CirculationReport:
    """循環検出の全パイプラインを実行.

    1. 依存グラフ構築
    2. Tarjan で SCC 抽出
    3. 孤立/接続に分類
    4. レポート生成

    Args:
        root: スキャンするルートディレクトリ
        package_prefix: パッケージ接頭辞

    Returns:
        CirculationReport
    """
    # 1. グラフ構築
    graph = DependencyGraph()
    graph.build(root, package_prefix)

    # 2. SCC 抽出
    sccs = find_sccs(graph)

    # 3. 分類
    classified = classify_sccs(graph, sccs)

    isolated_count = sum(1 for r in classified if r.is_isolated)
    connected_count = sum(1 for r in classified if not r.is_isolated)

    return CirculationReport(
        total_modules=len(graph.nodes),
        total_edges=graph.edge_count,
        sccs=classified,
        isolated_count=isolated_count,
        connected_count=connected_count,
    )


# PURPOSE: CLI エントリーポイント
def main():
    """CLI エントリーポイント."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Q-Series 循環検出 — Python コードの循環的依存を検出"
    )
    parser.add_argument(
        "path",
        type=Path,
        help="スキャンするディレクトリ",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="",
        help="パッケージ接頭辞 (e.g. mekhane)",
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    report = detect_circulation(args.path, args.prefix)
    print(report.to_markdown())

    sys.exit(1 if report.has_issues else 0)


if __name__ == "__main__":
    main()
