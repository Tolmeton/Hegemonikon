#!/usr/bin/env python3
# PROOF: mekhane/symploke/tests/test_sophia_ingest_brain.py
# PURPOSE: symploke モジュールの sophia_ingest_brain に対するテスト
"""Tests for sophia_ingest brain session parsing."""

import sys
import tempfile
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mekhane.symploke.sophia_ingest import (
    parse_brain_session,
    parse_ki_directory,
    get_all_documents,
    DEFAULT_KNOWLEDGE_DIRS,
)


# ── parse_brain_session テスト ──────────────────────────────

class TestParseBrainSession:
    """brain セッションのパーステスト。"""

    # PURPOSE: .md ファイルから Document を正しく生成するか
    def test_basic_parsing(self):
        """セッション内の .md ファイルが Document に変換されるか。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "abcd1234-5678-9012-3456-789012345678"
            session_dir.mkdir()

            # テスト用 .md ファイルを作成
            (session_dir / "task.md").write_text("# Boot 拡張タスク\n\n- [ ] 実装\n", encoding="utf-8")
            (session_dir / "implementation_plan.md").write_text("# 実装計画\n\n## 変更点\n", encoding="utf-8")

            docs = parse_brain_session(session_dir)

            assert len(docs) == 2, f"Expected 2 docs, got {len(docs)}"
            ids = {d.id for d in docs}
            assert "brain-abcd1234-task" in ids
            assert "brain-abcd1234-implementation_plan" in ids

    # PURPOSE: .system_generated/ 配下のファイルが除外されるか
    def test_excludes_system_generated(self):
        """直下の .md のみパースし、サブディレクトリは無視。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "abcd1234-session"
            session_dir.mkdir()

            # 直下の .md
            (session_dir / "task.md").write_text("# タスク\n", encoding="utf-8")

            # .system_generated/ 配下 (除外されるべき)
            sys_gen = session_dir / ".system_generated" / "logs"
            sys_gen.mkdir(parents=True)
            (sys_gen / "overview.md").write_text("ログ内容\n", encoding="utf-8")

            docs = parse_brain_session(session_dir)

            assert len(docs) == 1, f"Expected 1 doc (excluding .system_generated), got {len(docs)}"
            assert docs[0].id == "brain-abcd1234-task"

    # PURPOSE: 空の .md ファイルがスキップされるか
    def test_skips_empty_files(self):
        """空ファイルはスキップ。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "abcd1234-session"
            session_dir.mkdir()

            (session_dir / "empty.md").write_text("", encoding="utf-8")
            (session_dir / "whitespace.md").write_text("   \n\n  ", encoding="utf-8")
            (session_dir / "real.md").write_text("# 実際のコンテンツ\n", encoding="utf-8")

            docs = parse_brain_session(session_dir)

            assert len(docs) == 1, f"Expected 1 doc (skipping empty), got {len(docs)}"

    # PURPOSE: metadata にセッション情報が含まれるか
    def test_metadata_fields(self):
        """metadata に type, session_id, artifact, ki_name が含まれるか。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "abcd1234-5678-9012-3456-789012345678"
            session_dir.mkdir()

            (session_dir / "walkthrough.md").write_text("# ウォークスルー\n\n変更内容\n", encoding="utf-8")

            docs = parse_brain_session(session_dir)

            assert len(docs) == 1
            meta = docs[0].metadata
            assert meta["type"] == "brain_artifact"
            assert meta["session_id"] == "abcd1234-5678-9012-3456-789012345678"
            assert meta["artifact"] == "walkthrough.md"
            assert "Session abcd1234" in meta["ki_name"]
            assert "ウォークスルー" in meta["ki_name"]

    # PURPOSE: タイトル抽出が正しく動作するか
    def test_title_extraction(self):
        """# で始まる行からタイトルを抽出。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / "abcd1234-session"
            session_dir.mkdir()

            # # がある場合
            (session_dir / "plan.md").write_text("# Boot 拡張計画\n\n詳細\n", encoding="utf-8")
            # # がない場合 (ファイル名がフォールバック)
            (session_dir / "notes.md").write_text("メモ内容\n", encoding="utf-8")

            docs = parse_brain_session(session_dir)
            doc_map = {d.metadata["artifact"]: d for d in docs}

            # # がある → タイトル抽出
            assert "Boot 拡張計画" in doc_map["plan.md"].metadata["ki_name"]
            # # がない → ファイル名
            assert "notes" in doc_map["notes.md"].metadata["ki_name"]


# ── DEFAULT_KNOWLEDGE_DIRS テスト ──────────────────────────

class TestDefaultKnowledgeDirs:
    """DEFAULT_KNOWLEDGE_DIRS の設定テスト。"""

    # PURPOSE: brain ディレクトリが含まれるか
    def test_brain_dir_included(self):
        """DEFAULT_KNOWLEDGE_DIRS に brain パスが含まれる。"""
        brain_paths = [d for d in DEFAULT_KNOWLEDGE_DIRS if "brain" in str(d)]
        assert len(brain_paths) >= 1, "brain directory not found in DEFAULT_KNOWLEDGE_DIRS"

    # PURPOSE: knowledge ディレクトリが含まれるか
    def test_knowledge_dir_included(self):
        """DEFAULT_KNOWLEDGE_DIRS に knowledge パスが含まれる。"""
        ki_paths = [d for d in DEFAULT_KNOWLEDGE_DIRS if "knowledge" in str(d)]
        assert len(ki_paths) >= 1, "knowledge directory not found in DEFAULT_KNOWLEDGE_DIRS"


# ── get_all_documents テスト ──────────────────────────────

class TestGetAllDocuments:
    """get_all_documents の統合テスト。"""

    # PURPOSE: 実ディレクトリで呼び出してエラーが出ないか
    def test_no_crash(self):
        """実環境で get_all_documents() がクラッシュしない。"""
        try:
            docs = get_all_documents()
            assert isinstance(docs, list)
            # brain が 103 セッションあるので 0 件ではないはず
            print(f"  Found {len(docs)} documents total")
        except Exception as e:
            assert False, f"get_all_documents() crashed: {e}"

    # PURPOSE: 返却された Document が正しい型を持つか
    def test_document_types(self):
        """全 Document の type が knowledge_item か brain_artifact。"""
        docs = get_all_documents()
        valid_types = {"knowledge_item", "brain_artifact"}
        for doc in docs:
            doc_type = doc.metadata.get("type", "")
            assert doc_type in valid_types, f"Invalid type '{doc_type}' in doc {doc.id}"


# ── テストランナー ──────────────────────────────────────

def run_tests():
    """全テストを実行してレポートする。"""
    import traceback

    test_classes = [TestParseBrainSession, TestDefaultKnowledgeDirs, TestGetAllDocuments]
    passed = 0
    failed = 0
    errors = []

    for cls in test_classes:
        print(f"\n{'='*60}")
        print(f"  {cls.__name__}")
        print(f"{'='*60}")
        instance = cls()
        for method_name in sorted(dir(instance)):
            if not method_name.startswith("test_"):
                continue
            method = getattr(instance, method_name)
            try:
                method()
                print(f"  ✅ {method_name}")
                passed += 1
            except Exception as e:
                print(f"  ❌ {method_name}: {e}")
                errors.append((f"{cls.__name__}.{method_name}", traceback.format_exc()))
                failed += 1

    print(f"\n{'='*60}")
    print(f"  Results: {passed} passed, {failed} failed")
    print(f"{'='*60}")

    if errors:
        print("\nErrors:")
        for name, tb in errors:
            print(f"\n--- {name} ---")
            print(tb)

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
