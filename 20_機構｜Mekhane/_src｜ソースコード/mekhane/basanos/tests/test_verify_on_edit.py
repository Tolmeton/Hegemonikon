# PROOF: mekhane/basanos/tests/test_verify_on_edit.py
# PURPOSE: basanos モジュールの verify_on_edit に対するテスト
import pytest
from pathlib import Path
from mekhane.basanos.verify_on_edit import (
    _path_to_module,
    _extract_imports,
    build_import_graph,
    find_related_tests,
)

def test_path_to_module(tmp_path):
    source_root = tmp_path
    f1 = tmp_path / "mekhane" / "foo" / "bar.py"
    f1.parent.mkdir(parents=True)
    f1.touch()
    
    assert _path_to_module(f1, source_root) == "mekhane.foo.bar"
    
    f2 = tmp_path / "mekhane" / "foo" / "__init__.py"
    f2.touch()
    assert _path_to_module(f2, source_root) == "mekhane.foo"

def test_extract_imports(tmp_path):
    f = tmp_path / "test_extract.py"
    f.write_text("import os\nfrom mekhane.foo import bar\nfrom mekhane.baz import qux\n")
    imports = _extract_imports(f)
    assert set(imports) == {"os", "mekhane", "mekhane.foo", "mekhane.foo.bar", "mekhane.baz", "mekhane.baz.qux"}

def test_build_import_graph_and_find_related(tmp_path):
    source_root = tmp_path
    
    # Core module (変更する対象)
    core_dir = source_root / "mekhane" / "core"
    core_dir.mkdir(parents=True)
    (core_dir / "target.py").write_text("def do_something(): pass\n")
    
    # Helper module (Core に依存)
    helper_dir = source_root / "mekhane" / "helper"
    helper_dir.mkdir(parents=True)
    (helper_dir / "util.py").write_text("from mekhane.core.target import do_something\n")
    
    # Tests directory
    test_dir = source_root / "mekhane" / "tests"
    test_dir.mkdir(parents=True)
    
    # 直接 Core をテストするファイル
    test_file_direct = test_dir / "test_target.py"
    test_file_direct.write_text("from mekhane.core.target import do_something\n")
    
    # Helper をテストするが、間接的に Core に依存するファイル
    test_file_indirect = test_dir / "test_util.py"
    test_file_indirect.write_text("from mekhane.helper.util import something_else\n")
    
    test_dirs = [test_dir]
    graph = build_import_graph(source_root, test_dirs)
    
    changed = [str(core_dir / "target.py")]
    related = find_related_tests(changed, source_root, graph)
    
    related_names = [r.name for r in related]
    
    # 推移的依存の解決により、両方のテストが発見されることを検証
    assert "test_target.py" in related_names
    assert "test_util.py" in related_names

def test_find_related_conftest_changed(tmp_path):
    source_root = tmp_path
    test_dir = source_root / "mekhane" / "tests"
    test_dir.mkdir(parents=True)
    
    conftest = test_dir / "conftest.py"
    conftest.touch()
    
    t1 = test_dir / "test_1.py"
    t1.touch()
    
    t2 = test_dir / "2_test.py"  # *_test.py パターンのカバー
    t2.touch()
    
    related = find_related_tests([str(conftest)], source_root, import_graph={})
    
    related_names = [r.name for r in related]
    assert "test_1.py" in related_names
    assert "2_test.py" in related_names
