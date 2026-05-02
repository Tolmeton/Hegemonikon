#!/usr/bin/env python3
# PROOF: [L2/Basanos] <- mekhane/basanos/ Verify-on-Edit パターン
"""
Verify-on-Edit — ファイル変更後の自動テスト発見・実行

SWE-bench Verified で 22% → 38% の改善を実証したパターンの HGK 実装。
import グラフ解析で変更モジュールに依存するテストだけを正確に特定し、
スコープ済みテストのみを実行する。

Phase 1: L0 静的解析 (既存 basanos_scan) — オプション
Phase 2: import グラフ解析 — AST で import 逆引き
Phase 3: collect-only — pytest ドライランでテスト件数確認
Phase 4: pytest 実行 — スコープ済みテストのみ
Phase 5: Lēthē Hint — 新関数名を抽出し mneme search scope=code への委譲を示唆
"""

import ast
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from mekhane.paths import HGK_ROOT


# =============================================================================
# Data Classes
# =============================================================================


# PURPOSE: テスト収集結果を表すデータクラス
@dataclass
class CollectResult:
    """pytest --collect-only の結果。"""

    count: int = 0
    test_ids: list[str] = field(default_factory=list)
    skipped_reason: str | None = None


# PURPOSE: テスト実行結果を表すデータクラス
@dataclass
class VerifyResult:
    """pytest 実行結果。"""

    passed: bool = False
    total: int = 0
    failed: int = 0
    errors: int = 0
    output: str = ""
    test_files: list[str] = field(default_factory=list)
    skipped_reason: str | None = None


# =============================================================================
# Import Graph Builder
# =============================================================================

# PURPOSE: テストファイル群の import 文を AST パースし、モジュール→テストの逆引き辞書を構築
def build_import_graph(
    source_root: Path,
    test_dirs: list[Path] | None = None,
    changed_files: list[str] | None = None,
    max_depth: int = 2,
) -> dict[str, list[Path]]:
    """テストファイルの import を AST パースし、逆引き辞書を構築する。

    推移的追跡: テストが import する非テストモジュールの import も
    再帰的に解決し、間接依存を検出する。

    Returns:
        dict[str, list[Path]]: モジュール名 → テストファイルリスト
    """
    if test_dirs is None:
        test_dirs = _discover_test_dirs(source_root)

    # Step 1: テストファイルの直接 import を収集
    direct_graph: dict[str, list[Path]] = {}
    test_imports: dict[Path, set[str]] = {}  # テストファイル → 直接 import 集合

    for test_dir in test_dirs:
        if not test_dir.exists():
            continue
        for test_file in _glob_test_files(test_dir):
            try:
                modules = _extract_imports(test_file)
            except Exception:  # noqa: BLE001
                continue
            test_imports[test_file] = set(modules)
            for mod in modules:
                if mod not in direct_graph:
                    direct_graph[mod] = []
                if test_file not in direct_graph[mod]:
                    direct_graph[mod].append(test_file)

    # Step 2: 非テストモジュールの import を再帰的に解決 (推移的クロージャ, 深さ制限付き)
    module_deps = _build_module_dependency_map(source_root, changed_files=changed_files)
    transitive_graph: dict[str, list[Path]] = dict(direct_graph)

    from collections import deque

    for test_file, imported_mods in test_imports.items():
        # BFS で推移的に到達可能なモジュールを計算 (深さ制限付き)
        visited: set[str] = set()
        queue: deque[tuple[str, int]] = deque((mod, 0) for mod in imported_mods)
        while queue:
            mod, depth = queue.popleft()
            if mod in visited:
                continue
            visited.add(mod)
            # 深さ制限を超えたら展開しない (ただし現在のモジュールは登録する)
            if depth < max_depth and mod in module_deps:
                for dep in module_deps[mod]:
                    if dep not in visited:
                        queue.append((dep, depth + 1))
        # visited にある全モジュールに対して、このテストを逆引き登録
        for mod in visited:
            if mod not in transitive_graph:
                transitive_graph[mod] = []
            if test_file not in transitive_graph[mod]:
                transitive_graph[mod].append(test_file)

    return transitive_graph


# PURPOSE: 非テストモジュールの依存関係マップを構築する (推移的追跡用)
def _build_module_dependency_map(
    source_root: Path,
    changed_files: list[str] | None = None,
) -> dict[str, set[str]]:
    """ソースルート以下の .py ファイルから import を抽出し、
    モジュール名 → 依存モジュール集合 のマップを構築する。

    テストファイルは除外 (テスト間の依存は不要)。
    mekhane パッケージ内の import のみを追跡する。

    性能最適化: changed_files が指定された場合、変更ファイルの
    トップレベルパッケージ配下のみをスキャンする (878ファイル → 数十ファイル)。
    """
    # スキャン対象ディレクトリを決定
    scan_dirs: list[Path] = []
    if changed_files:
        seen_packages: set[str] = set()
        for fpath_str in changed_files:
            fpath = Path(fpath_str)
            try:
                rel = fpath.resolve().relative_to(source_root.resolve())
            except ValueError:
                continue
            # トップレベルパッケージ (mekhane, hermeneus 等)
            if rel.parts:
                top_pkg = rel.parts[0]
                if top_pkg not in seen_packages:
                    seen_packages.add(top_pkg)
                    pkg_dir = source_root / top_pkg
                    if pkg_dir.is_dir():
                        scan_dirs.append(pkg_dir)

    if not scan_dirs:
        # フォールバック: 全体をスキャン (小規模プロジェクト用)
        scan_dirs = [source_root]

    deps: dict[str, set[str]] = {}
    for scan_dir in scan_dirs:
        for py_file in scan_dir.rglob("*.py"):
            # テストファイル/隠しディレクトリはスキップ
            if py_file.name.startswith("test_") or py_file.name.endswith("_test.py"):
                continue
            if any(part.startswith(".") for part in py_file.parts):
                continue

            mod_name = _path_to_module(py_file, source_root)
            if not mod_name:
                continue

            try:
                imports = _extract_imports(py_file)
            except Exception:  # noqa: BLE001
                continue

            # mekhane/hermeneus パッケージ内の import のみを追跡
            internal = {m for m in imports if m.startswith(("mekhane.", "hermeneus."))}
            if internal:
                deps[mod_name] = internal

    return deps


# PURPOSE: テストディレクトリからテストファイルを glob する (test_*.py + *_test.py)
def _glob_test_files(test_dir: Path) -> list[Path]:
    """test_*.py と *_test.py の両方を探す。"""
    files = set()
    files.update(test_dir.glob("test_*.py"))
    files.update(test_dir.glob("*_test.py"))
    return sorted(files)


# PURPOSE: Python ファイルから import 文を AST で抽出する
def _extract_imports(filepath: Path) -> list[str]:
    """AST で import / from...import 文からモジュール名を抽出する。"""
    source = filepath.read_text("utf-8", errors="replace")
    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError:
        return []

    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.append(node.module)
                # import されている名前も結合して追加 (関数かもしれないが無害)
                for alias in node.names:
                    modules.append(f"{node.module}.{alias.name}")
                # 親モジュールも追加 (mekhane.foo.bar → mekhane.foo も)
                parts = node.module.split(".")
                for i in range(1, len(parts)):
                    modules.append(".".join(parts[:i]))

    return list(set(modules))


# PURPOSE: ソースルート以下の tests/ ディレクトリを自動発見する
def _discover_test_dirs(source_root: Path) -> list[Path]:
    """source_root 以下の tests/ ディレクトリを発見する。"""
    dirs = []
    for p in source_root.rglob("tests"):
        if p.is_dir() and not any(part.startswith(".") for part in p.parts):
            dirs.append(p)
    return sorted(dirs)


# =============================================================================
# Related Test Finder
# =============================================================================


# PURPOSE: 変更ファイルから関連テストを import グラフで特定する
def find_related_tests(
    changed_files: list[str],
    source_root: Path,
    import_graph: dict[str, list[Path]] | None = None,
) -> list[Path]:
    """変更ファイルに関連するテストを特定する。

    戦略:
      1. import グラフから依存テストを逆引き
      2. 変更ファイル自体がテストならそのまま含める
      3. グラフに見つからない場合、パス推定にフォールバック

    Returns:
        テストファイルのパスリスト (重複なし)
    """
    if import_graph is None:
        import_graph = build_import_graph(source_root)

    found: set[Path] = set()

    for fpath_str in changed_files:
        fpath = Path(fpath_str)

        # 変更ファイル自体がテストファイルの場合
        if fpath.name.startswith("test_") or fpath.name.endswith("_test.py"):
            if fpath.exists() and fpath.suffix == ".py":
                found.add(fpath)
            continue

        # conftest.py が変更された場合: そのディレクトリ + 子ディレクトリの全テストを対象
        if fpath.name == "conftest.py":
            conftest_dir = fpath.parent
            if conftest_dir.exists():
                for tf in _glob_test_files(conftest_dir):
                    found.add(tf)
                # 子ディレクトリの tests/ も
                for sub_tests in conftest_dir.rglob("tests"):
                    if sub_tests.is_dir():
                        for tf in _glob_test_files(sub_tests):
                            found.add(tf)
            continue

        # .py 以外は skip
        if fpath.suffix != ".py":
            continue

        # モジュール名に変換して import グラフで逆引き
        module_name = _path_to_module(fpath, source_root)
        if module_name:
            # 完全一致のみ — 部分一致は過剰にテストを拾うため廃止
            if module_name in import_graph:
                found.update(import_graph[module_name])

        # フォールバック: パス推定
        if not any(t for t in found if str(fpath.stem) in t.name):
            fallback = _path_based_discovery(fpath, source_root)
            found.update(fallback)

    return sorted(found)


# PURPOSE: ファイルパスからPythonモジュール名に変換する
def _path_to_module(filepath: Path, source_root: Path) -> str | None:
    """ファイルパスをモジュール名に変換する。

    例: source_root/mekhane/foo/bar.py → mekhane.foo.bar
    """
    try:
        rel = filepath.resolve().relative_to(source_root.resolve())
    except ValueError:
        return None

    parts = list(rel.parts)
    if parts and parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]  # .py 除去

    # __init__ は省略
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]

    if not parts:
        return None

    return ".".join(parts)


# PURPOSE: パス推定によるテスト発見のフォールバック
def _path_based_discovery(filepath: Path, source_root: Path) -> list[Path]:
    """import グラフで見つからない場合のフォールバック。

    パス推定パターン:
      mekhane/foo/bar.py → mekhane/foo/tests/test_bar.py
      mekhane/foo/bar.py → tests/test_bar.py
    """
    found = []
    test_name = f"test_{filepath.stem}.py"

    # パターン1: 同ディレクトリの tests/ 下
    sibling_test = filepath.parent / "tests" / test_name
    if sibling_test.exists():
        found.append(sibling_test)

    # パターン2: ソースルート直下の tests/
    root_test = source_root / "tests" / test_name
    if root_test.exists():
        found.append(root_test)

    # パターン3: ソースルート直下の tests_root/
    root_test2 = source_root / "tests_root" / test_name
    if root_test2.exists():
        found.append(root_test2)

    return found


# =============================================================================
# Test Collection (Dry Run)
# =============================================================================


# PURPOSE: pytest --collect-only でテスト件数を事前確認する
def collect_tests(
    test_paths: list[Path],
    python_exec: str | None = None,
    max_tests: int = 100,
) -> CollectResult:
    """pytest --collect-only でテスト件数を事前確認する。

    0件 → 即終了
    max_tests 超 → スキップして警告
    """
    if not test_paths:
        return CollectResult(count=0, skipped_reason="テスト対象なし")

    if python_exec is None:
        python_exec = sys.executable

    str_paths = [str(p) for p in test_paths if p.exists()]
    if not str_paths:
        return CollectResult(count=0, skipped_reason="テストファイルが存在しない")

    try:
        proc = subprocess.run(
            [python_exec, "-m", "pytest", "--collect-only", "-q", "--no-header"]
            + str_paths,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        return CollectResult(count=0, skipped_reason="collect-only タイムアウト (15秒)")
    except FileNotFoundError:
        return CollectResult(count=0, skipped_reason=f"Python 実行ファイルが見つからない: {python_exec}")

    # 出力からテスト ID を抽出
    test_ids = []
    for line in proc.stdout.strip().split("\n"):
        line = line.strip()
        if line and "::" in line and not line.startswith(("=", "-", "no tests")):
            test_ids.append(line)

    count = len(test_ids)

    if count > max_tests:
        return CollectResult(
            count=count,
            test_ids=test_ids[:10],  # 先頭10件のみ
            skipped_reason=f"テスト数 {count} > 上限 {max_tests}。スコープを絞ってください",
        )

    return CollectResult(count=count, test_ids=test_ids)


# =============================================================================
# Test Runner
# =============================================================================


# PURPOSE: スコープ済みテストを pytest で実行する
def run_tests(
    test_paths: list[Path],
    python_exec: str | None = None,
) -> VerifyResult:
    """pytest を subprocess で実行する。

    前提: test_paths は collect_tests でスコープ済み。
    """
    if not test_paths:
        return VerifyResult(passed=True, skipped_reason="テスト対象なし")

    if python_exec is None:
        python_exec = sys.executable

    str_paths = [str(p) for p in test_paths if p.exists()]
    if not str_paths:
        return VerifyResult(passed=True, skipped_reason="テストファイルが存在しない")

    try:
        proc = subprocess.run(
            [python_exec, "-m", "pytest", "--tb=short", "-q", "--no-header"]
            + str_paths,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return VerifyResult(
            passed=False,
            output=f"Python 実行ファイルが見つからない: {python_exec}",
        )

    output = proc.stdout + proc.stderr

    # pytest 終了コードで判定
    passed = proc.returncode == 0

    # 結果行をパース: "X passed, Y failed, Z errors" etc
    total, failed, errors = 0, 0, 0
    for line in output.split("\n"):
        line = line.strip()
        if "passed" in line or "failed" in line or "error" in line:
            import re

            m_passed = re.search(r"(\d+) passed", line)
            m_failed = re.search(r"(\d+) failed", line)
            m_errors = re.search(r"(\d+) error", line)
            if m_passed:
                total += int(m_passed.group(1))
            if m_failed:
                failed = int(m_failed.group(1))
                total += failed
            if m_errors:
                errors = int(m_errors.group(1))
                total += errors

    return VerifyResult(
        passed=passed,
        total=total,
        failed=failed,
        errors=errors,
        output=output[-2000:] if len(output) > 2000 else output,  # 末尾2000文字
        test_files=str_paths,
    )


# =============================================================================
# Orchestrator
# =============================================================================


# PURPOSE: Verify-on-Edit のフルパイプラインを実行するオーケストレータ
def verify_on_edit(
    changed_files: list[str],
    source_root: Path | None = None,
    include_basanos: bool = True,
    max_tests: int = 100,
    python_exec: str | None = None,
) -> dict:
    """Verify-on-Edit のフルパイプラインを実行する。

    Returns:
        {
            "basanos": {"issues": int, "details": [...]},  # include_basanos=True の場合
            "test_discovery": {"found": int, "test_files": [...]},
            "collection": {"count": int, "skipped_reason": ...},
            "execution": VerifyResult のダンプ,
            "verdict": "PASS" | "FAIL" | "SKIP" | "NO_TESTS",
            "lethe_hint": {...}  # Lēthē 軽量ヒント (新関数名 + mneme 委譲示唆)
        }
    """
    if source_root is None:
        source_root = _infer_source_root(changed_files)

    result: dict = {
        "basanos": None,
        "test_discovery": None,
        "collection": None,
        "execution": None,
        "lethe_hint": None,
        "verdict": "NO_TESTS",
    }

    # Phase 1: L0 Basanos (optional)
    if include_basanos:
        basanos_issues = _run_basanos(changed_files)
        result["basanos"] = basanos_issues

    # Phase 2: import グラフ解析
    import_graph = build_import_graph(source_root, changed_files=changed_files)
    related_tests = find_related_tests(changed_files, source_root, import_graph)
    result["test_discovery"] = {
        "found": len(related_tests),
        "test_files": [str(t) for t in related_tests],
    }

    if not related_tests:
        result["verdict"] = "NO_TESTS"
        return result

    # Phase 3: collect-only
    collect = collect_tests(related_tests, python_exec=python_exec, max_tests=max_tests)
    result["collection"] = {
        "count": collect.count,
        "test_ids": collect.test_ids[:10],
        "skipped_reason": collect.skipped_reason,
    }

    if collect.skipped_reason:
        result["verdict"] = "SKIP"
        return result

    if collect.count == 0:
        result["verdict"] = "NO_TESTS"
        return result

    # Phase 4: pytest 実行
    verify = run_tests(related_tests, python_exec=python_exec)
    result["execution"] = {
        "passed": verify.passed,
        "total": verify.total,
        "failed": verify.failed,
        "errors": verify.errors,
        "output": verify.output,
        "test_files": verify.test_files,
    }

    result["verdict"] = "PASS" if verify.passed else "FAIL"

    # Phase 5: Lēthē Hint (軽量 — 重い検索は mneme に委譲)
    result["lethe_hint"] = _lethe_hint(changed_files)

    return result


# PURPOSE: 変更ファイルから新関数名を軽量抽出し、mneme search への委譲を示唆する
def _lethe_hint(changed_files: list[str]) -> dict | None:
    """Lēthē 軽量ヒント — 重い検索は mneme に委譲。

    変更ファイルの関数名を AST から高速抽出するのみ。
    574MB のインデックスロードは行わない。
    Agent (Claude) がこのヒントを見て mneme search scope=code を
    自発的に呼ぶことで、R1 (完全一致) + 43d (類似) の相補検索が実行される。
    """
    func_names: list[dict] = []

    for fpath_str in changed_files:
        fpath = Path(fpath_str)
        if not fpath.exists() or fpath.suffix != ".py":
            continue

        try:
            source = fpath.read_text("utf-8", errors="replace")
            tree = ast.parse(source)
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_names.append({
                    "name": node.name,
                    "file": str(fpath.name),
                    "line": node.lineno,
                })

    if not func_names:
        return None

    return {
        "functions": func_names,
        "count": len(func_names),
        "hint": "mneme search scope=code code_mode=similar で構造類似チェックを推奨",
    }


# PURPOSE: 変更ファイルに対して L0 Basanos 静的解析を実行する
def _run_basanos(changed_files: list[str]) -> dict:
    """L0 Basanos 静的解析。"""
    try:
        from mekhane.basanos.ai_auditor import AIAuditor

        auditor = AIAuditor(strict=False)
        all_issues = []
        for fpath_str in changed_files:
            fpath = Path(fpath_str)
            if fpath.exists() and fpath.suffix == ".py":
                try:
                    result = auditor.audit_file(fpath)
                    all_issues.extend(
                        {
                            "file": str(fpath.name),
                            "line": i.line,
                            "code": i.code,
                            "severity": i.severity.value if hasattr(i.severity, "value") else str(i.severity),
                            "message": i.message,
                        }
                        for i in result.issues
                    )
                except Exception:  # noqa: BLE001
                    pass

        return {"issues": len(all_issues), "details": all_issues[:20]}
    except ImportError:
        return {"issues": -1, "details": ["Basanos module not available"]}


# PURPOSE: 変更ファイルからソースルートを推定する
def _infer_source_root(changed_files: list[str]) -> Path:
    """変更ファイルのパスからソースルートを推定する。"""
    for fpath_str in changed_files:
        fpath = Path(fpath_str).resolve()
        parts = fpath.parts
        for i, part in enumerate(parts):
            if part == "mekhane":
                return Path(*parts[: i])  # mekhane の親ディレクトリ
    # フォールバック
    hgk = HGK_ROOT
    return hgk / "20_機構｜Mekhane" / "_src｜ソースコード"


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import json

    if len(sys.argv) < 2:
        print("Usage: verify_on_edit.py <file1> [file2] ...")
        sys.exit(1)

    files = sys.argv[1:]
    result = verify_on_edit(files)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
