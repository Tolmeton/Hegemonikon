# PROOF: [L1/テスト] <- mekhane/basanos/tests/test_quality_gate.py
"""SequentialQualityGate のテスト。"""

from mekhane.basanos.jules_feedback import GateResult, SequentialQualityGate


class TestSequentialQualityGate:
    """直列品質関門のユニットテスト。"""

    def _make_diff(self, files: list[str]) -> str:
        """テスト用の最小 git diff テキストを生成。"""
        lines = []
        for f in files:
            lines.append(f"diff --git a/{f} b/{f}")
            lines.append(f"--- a/{f}")
            lines.append(f"+++ b/{f}")
            lines.append("@@ -1 +1 @@")
            lines.append("-old")
            lines.append("+new")
        return "\n".join(lines)

    def test_empty_diff_fails_stage1(self):
        gate = SequentialQualityGate()
        results = gate.run(diff="", spec={"planned_files": ["foo.py"]})
        assert len(results) == 1
        assert results[0].stage == "spec_compliance"
        assert results[0].passed is False
        assert any(i["code"] == "SPEC-001" for i in results[0].issues)

    def test_stage1_pass_proceeds_to_stage2(self):
        gate = SequentialQualityGate()
        diff = self._make_diff(["mekhane/foo.py"])
        results = gate.run(
            diff=diff,
            spec={"planned_files": ["mekhane/foo.py"]},
            changed_files=[],  # no real files → Stage 2 will have 0 issues
        )
        assert len(results) == 2
        assert results[0].stage == "spec_compliance"
        assert results[0].passed is True
        assert results[1].stage == "code_quality"

    def test_stage1_fail_blocks_stage2(self):
        gate = SequentialQualityGate()
        # diff is empty → SPEC-001 error → blocks Stage 2
        results = gate.run(diff="  ", spec={})
        assert len(results) == 1
        assert results[0].stage == "spec_compliance"
        assert results[0].passed is False

    def test_spec_missing_file_is_warning(self):
        gate = SequentialQualityGate()
        diff = self._make_diff(["a.py"])
        results = gate.run(
            diff=diff,
            spec={"planned_files": ["a.py", "b.py"]},
        )
        # Stage 1 should pass (warning, not error) but flag missing
        assert results[0].passed is True
        warnings = [i for i in results[0].issues if i["code"] == "SPEC-002"]
        assert len(warnings) == 1
        assert "b.py" in warnings[0]["message"]

    def test_unexpected_file_is_info(self):
        gate = SequentialQualityGate()
        diff = self._make_diff(["a.py", "surprise.py"])
        results = gate.run(
            diff=diff,
            spec={"planned_files": ["a.py"]},
        )
        assert results[0].passed is True
        infos = [i for i in results[0].issues if i["code"] == "SPEC-003"]
        assert len(infos) == 1
        assert "surprise.py" in infos[0]["message"]

    def test_no_spec_passes_stage1(self):
        gate = SequentialQualityGate()
        diff = self._make_diff(["anything.py"])
        results = gate.run(diff=diff, spec={})
        assert results[0].passed is True
        assert len(results[0].issues) == 0

    def test_extract_files_from_diff(self):
        diff = (
            "diff --git a/foo.py b/foo.py\n"
            "--- a/foo.py\n"
            "+++ b/foo.py\n"
            "@@ -1 +1 @@\n"
            "diff --git a/bar.py b/bar.py\n"
            "+++ b/bar.py\n"
        )
        files = SequentialQualityGate._extract_files_from_diff(diff)
        assert files == ["foo.py", "bar.py"]

    def test_format_results(self):
        results = [
            GateResult(stage="spec_compliance", passed=True, issues=[]),
            GateResult(
                stage="code_quality",
                passed=False,
                issues=[{"code": "L0", "message": "test", "severity": "error"}],
            ),
        ]
        text = SequentialQualityGate.format_results(results)
        assert "Stage 1" in text
        assert "Stage 2" in text
        assert "Gate blocked" in text

    def test_planned_deletion_missing(self):
        gate = SequentialQualityGate()
        diff = self._make_diff(["a.py"])
        results = gate.run(
            diff=diff,
            spec={"planned_files": ["a.py"], "planned_deletions": ["old.py"]},
        )
        assert results[0].passed is True  # warning only
        warnings = [i for i in results[0].issues if i["code"] == "SPEC-004"]
        assert len(warnings) == 1


class TestBasanosL0Integration:
    """_run_basanos_l0 の結合テスト (実ファイル使用)。"""

    def test_syntax_error_detected(self, tmp_path):
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("def foo(\n", encoding="utf-8")
        issues = SequentialQualityGate._run_basanos_l0([str(bad_file)])
        assert len(issues) == 1
        assert issues[0]["code"] == "L0-SYNTAX"
        assert issues[0]["severity"] == "error"

    def test_valid_python_no_issues(self, tmp_path):
        good_file = tmp_path / "good.py"
        good_file.write_text("x = 1\n", encoding="utf-8")
        issues = SequentialQualityGate._run_basanos_l0([str(good_file)])
        assert issues == []

    def test_nonexistent_file_skipped(self):
        issues = SequentialQualityGate._run_basanos_l0(["/nonexistent/foo.py"])
        assert issues == []

    def test_non_py_file_skipped(self, tmp_path):
        md_file = tmp_path / "readme.md"
        md_file.write_text("# Hello\n", encoding="utf-8")
        issues = SequentialQualityGate._run_basanos_l0([str(md_file)])
        assert issues == []


class TestDendronIntegration:
    """_run_dendron_check の結合テスト (実ファイル + 実 DendronChecker)。"""

    def test_missing_proof_detected(self, tmp_path):
        """PROOF ヘッダーなしのファイル → DENDRON-PROOF warning。"""
        no_proof = tmp_path / "no_proof.py"
        no_proof.write_text("def hello():\n    pass\n", encoding="utf-8")
        issues = SequentialQualityGate._run_dendron_check([str(no_proof)])
        proof_issues = [i for i in issues if i["code"] == "DENDRON-PROOF"]
        assert len(proof_issues) == 1
        assert "PROOF" in proof_issues[0]["message"]

    def test_valid_proof_no_issue(self, tmp_path):
        """PROOF ヘッダーあり + PURPOSE あり → PROOF issue なし。"""
        good_file = tmp_path / "good.py"
        good_file.write_text(
            '# PROOF: [L2/テスト] <- test\n'
            '# PURPOSE: テスト用\n'
            'def hello():\n'
            '    pass\n',
            encoding="utf-8",
        )
        issues = SequentialQualityGate._run_dendron_check([str(good_file)])
        proof_issues = [i for i in issues if i["code"] == "DENDRON-PROOF"]
        assert proof_issues == []

    def test_missing_purpose_detected(self, tmp_path):
        """PURPOSE なしの public 関数 → DENDRON-PURPOSE warning。"""
        no_purpose = tmp_path / "no_purpose.py"
        no_purpose.write_text(
            '# PROOF: [L2/テスト] <- test\n'
            'def public_func():\n'
            '    pass\n',
            encoding="utf-8",
        )
        issues = SequentialQualityGate._run_dendron_check([str(no_purpose)])
        purpose_issues = [i for i in issues if i["code"] == "DENDRON-PURPOSE"]
        assert len(purpose_issues) == 1
        assert "public_func" in purpose_issues[0]["message"]


class TestFullPipelineIntegration:
    """Stage 1 → Stage 2 の完全結合テスト。"""

    def _make_diff(self, files: list[str]) -> str:
        lines = []
        for f in files:
            lines.extend([
                f"diff --git a/{f} b/{f}",
                f"--- a/{f}",
                f"+++ b/{f}",
                "@@ -1 +1 @@",
                "-old",
                "+new",
            ])
        return "\n".join(lines)

    def test_syntax_error_blocks_quality(self, tmp_path):
        """構文エラーのファイル → Stage 2 で L0-SYNTAX error → gate blocked。"""
        bad = tmp_path / "bad.py"
        bad.write_text("def broken(\n", encoding="utf-8")
        gate = SequentialQualityGate()
        results = gate.run(
            diff=self._make_diff(["bad.py"]),
            spec={"planned_files": ["bad.py"]},
            changed_files=[str(bad)],
        )
        assert len(results) == 2
        assert results[0].passed is True  # Stage 1 OK
        assert results[1].passed is False  # Stage 2 blocked by syntax error
        assert any(i["code"] == "L0-SYNTAX" for i in results[1].issues)

    def test_clean_file_passes_both_stages(self, tmp_path):
        """PROOF + PURPOSE 完備のファイル → 両ステージ通過。"""
        good = tmp_path / "good.py"
        good.write_text(
            '# PROOF: [L2/テスト] <- test\n'
            '# PURPOSE: テスト\n'
            'def foo() -> None:\n'
            '    pass\n',
            encoding="utf-8",
        )
        gate = SequentialQualityGate()
        results = gate.run(
            diff=self._make_diff(["good.py"]),
            spec={"planned_files": ["good.py"]},
            changed_files=[str(good)],
        )
        assert len(results) == 2
        assert results[0].passed is True
        assert results[1].passed is True

