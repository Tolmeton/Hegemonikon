# T-039 Diagnostic Isomer Error Analysis

## SOURCE
- input: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/.claude/worktrees/serene-clarke/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_diagnostic.jsonl`
- scorer: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/pinakas/T-038_phase_c_diag_codebert_proxy_2026-05-01.py`
- rows: `288`
- threshold: `0.5`

## Confusion Matrix
Labels are `[0=diag_isomer, 1=diag_blindspot]`.

| true\pred | 0 | 1 |
|:---|---:|---:|
| 0 | 166 | 27 |
| 1 | 0 | 95 |

## Error Taxonomy
| class | count | interpretation |
|:---|---:|:---|
| test_scaffold_overlap | 17 | Both sides look like tests/assertion scaffolds; surface role overwhelms deeper CCL separation. |
| unicode_docstring_surface | 5 | Docstring/comment language surface may dominate representation. |
| generic_structural_surface_overlap | 3 | No single simple surface cause; requires local inspection. |
| cli_parser_long_surface | 2 | Large CLI/parser boilerplate creates broad structural similarity noise. |

## Highest-Score False Positives
These are `diag_isomer` pairs incorrectly classified as `diag_blindspot`.

| idx | score | class | ccl_sim | 49d_cos | codebert_cos | func_a | func_b |
|---:|---:|:---|---:|---:|---:|:---|:---|
| 23 | 1.000 | test_scaffold_overlap | 0.000 | 0.861 | 0.987 | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\ccl\tests\test_output_schema.py::test_optional_fields_none` | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\ergasterion\tekhne\tests\test_pipeline.py::test_defaults` |
| 9 | 0.999 | test_scaffold_overlap | 0.000 | 0.929 | 0.954 | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\fep\tests\test_eukairia_detector.py::test_all_windows_exist` | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\tests\test_fep_config.py::test_default_values` |
| 4 | 0.999 | test_scaffold_overlap | 0.000 | 0.873 | 0.986 | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\pks\tests\test_pks_v2.py::test_infer_context_returns_series` | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\ergasterion\tekhne\tests\test_pipeline.py::test_defaults` |
| 19 | 0.995 | cli_parser_long_surface | 0.000 | 0.861 | 0.972 | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\ergasterion\typos\test_typos.py::test_to_json` | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\hermeneus\src\cli.py::create_parser` |
| 100 | 0.993 | test_scaffold_overlap | 0.010 | 0.940 | 0.984 | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\dendron\tests\test_ept.py::test_ept_stats_in_check_result` | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\ergasterion\tekhne\tests\test_pipeline.py::test_defaults` |
| 2 | 0.986 | test_scaffold_overlap | 0.000 | 0.889 | 0.970 | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\anamnesis\tests\test_chunker_nucleator.py::test_creation_full` | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\fep\tests\test_tekhne_registry.py::test_all_categories_exist` |
| 12 | 0.970 | generic_structural_surface_overlap | 0.000 | 0.886 | 0.960 | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\ergasterion\tekhne\deep_engine.py::__init__` | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\periskope\tests\test_rerank.py::_make_engine` |
| 112 | 0.966 | test_scaffold_overlap | 0.012 | 0.862 | 0.968 | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\symploke\tests\test_phantasia_gap2.py::test_record_dissolve_defaults` | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\tests\test_phantazein_indexer.py::test_handoff_upsert` |
| 1 | 0.953 | test_scaffold_overlap | 0.000 | 0.889 | 0.964 | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\anamnesis\tests\test_chunker_nucleator.py::test_creation_full` | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\fep\tests\test_energeia_executor.py::test_all_phases_exist` |
| 111 | 0.947 | test_scaffold_overlap | 0.012 | 0.905 | 0.973 | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\fep\ergon\tests\__init__.py::test_ordering` | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\fep\tests\test_credit_assignment.py::test_feedback_summary` |
| 130 | 0.943 | test_scaffold_overlap | 0.016 | 0.890 | 0.965 | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\symploke\tests\test_generate_prompt.py::test_specialist_identity_preserved` | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\api\tests\test_synteleia_api.py::test_audit_response_structure` |
| 31 | 0.915 | test_scaffold_overlap | 0.000 | 0.862 | 0.968 | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\dendron\tests\test_ept.py::test_ept_stats_in_check_result` | `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\fep\tests\test_tekhne_registry.py::test_all_categories_exist` |

## Lowest-Score False Negatives
These are `diag_blindspot` pairs incorrectly classified as `diag_isomer`.

| idx | score | class | ccl_sim | 49d_cos | codebert_cos | func_a | func_b |
|---:|---:|:---|---:|---:|---:|:---|:---|
| N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

## Local Excerpts For Top False Positives

### FP idx 23 — score 1.000 — test_scaffold_overlap
- func_a: `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\ccl\tests\test_output_schema.py::test_optional_fields_none`
- func_b: `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\ergasterion\tekhne\tests\test_pipeline.py::test_defaults`

```python
def test_optional_fields_none(self, valid_output):
        """Verify optional fields none behavior."""
        assert valid_output.oscillations is None
        assert valid_output.merges is None
        assert valid_output.metas is None
        assert valid_output.factorials is None
```

```python
def test_defaults(self):
        cfg = PipelineConfig()
        assert cfg.model == "gemini-2.0-flash"
        assert cfg.use_async is True
        assert cfg.max_concurrency == 5
        assert cfg.use_cache is True
        assert cfg.top_n == 20
        assert cfg.report_format == "markdown"
        assert cfg.domains is None
        assert cfg.axes is None
```

### FP idx 9 — score 0.999 — test_scaffold_overlap
- func_a: `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\fep\tests\test_eukairia_detector.py::test_all_windows_exist`
- func_b: `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\tests\test_fep_config.py::test_default_values`

```python
def test_all_windows_exist(self):
        """Verify all windows exist behavior."""
        assert OpportunityWindow.WIDE.value == "wide"
        assert OpportunityWindow.NARROW.value == "narrow"
        assert OpportunityWindow.CLOSING.value == "closing"
```

```python
def test_default_values(self):
        """Default values match literature."""
        params = FEPParameters()

        # A matrix (pymdp Tutorial 2 range: 0.7-0.9)
        assert params.A.high_reliability == 0.85
        assert params.A.low_reliability == 0.15

        # B matrix
        assert params.B.deterministic == 1.0
        assert params.B.observe_clarifies == 0.8

        # C vector (Gijsen et al. 2022)
        assert params.C.high_positive == 2.5
        assert params.C.high_negative == -2.0

        # D
...
```

### FP idx 4 — score 0.999 — test_scaffold_overlap
- func_a: `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\pks\tests\test_pks_v2.py::test_infer_context_returns_series`
- func_b: `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\ergasterion\tekhne\tests\test_pipeline.py::test_defaults`

```python
def test_infer_context_returns_series(self, bridge):
        """Verify infer context returns series behavior."""
        ctx = bridge.infer_context("アーキテクチャを設計する")
        assert ctx.series in ("O", "S", "H", "P", "K", "A")
        assert ctx.similarity > 0
        assert ctx.oscillation in ("clear", "positive", "negative")
```

```python
def test_defaults(self):
        cfg = PipelineConfig()
        assert cfg.model == "gemini-2.0-flash"
        assert cfg.use_async is True
        assert cfg.max_concurrency == 5
        assert cfg.use_cache is True
        assert cfg.top_n == 20
        assert cfg.report_format == "markdown"
        assert cfg.domains is None
        assert cfg.axes is None
```

### FP idx 19 — score 0.995 — cli_parser_long_surface
- func_a: `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\ergasterion\typos\test_typos.py::test_to_json`
- func_b: `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\hermeneus\src\cli.py::create_parser`

```python
def test_to_json(self):
        """Test JSON serialization."""
        content = """#prompt test-json

@role:
  JSON test

@goal:
  test -> pass
"""
        parser = PromptLangParser(content)
        prompt = parser.parse()
        json_str = prompt.to_json()

        self.assertIn('"name": "test-json"', json_str)
        self.assertIn('"@role": "JSON test"', json_str)
```

```python
def create_parser() -> argparse.ArgumentParser:
    """CLI パーサーを作成"""
    parser = argparse.ArgumentParser(
        prog="hermeneus",
        description="Hermēneus — CCL 実行保証コンパイラ",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  hermeneus compile "/noe+ ~> V[] < 0.3"
  hermeneus execute "/noe+" --context "プロジェクト分析"
  hermeneus verify "/ene+" --rounds 3
  hermeneus audit --period 7
"""
    )
    
    parser.add_argument(
        "--version", "-v",
        action="versio
...
```

### FP idx 100 — score 0.993 — test_scaffold_overlap
- func_a: `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\dendron\tests\test_ept.py::test_ept_stats_in_check_result`
- func_b: `C:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード\mekhane\ergasterion\tekhne\tests\test_pipeline.py::test_defaults`

```python
def test_ept_stats_in_check_result(self, ept_checker, tmp_project):
        """CheckResult に EPT 統計が含まれる"""
        root = tmp_project({
            "module.py": "# PROOF: [L1/コア]\ndef foo():\n    return 1\n",
        })
        result = ept_checker.check(root)
        assert result.total_structure_checks >= 0
        assert result.total_function_nf_checks >= 0
        assert result.total_verification_checks >= 0
        assert result.structure_ok >= 0
        assert result.function_nf_ok >= 0
        assert result
...
```

```python
def test_defaults(self):
        cfg = PipelineConfig()
        assert cfg.model == "gemini-2.0-flash"
        assert cfg.use_async is True
        assert cfg.max_concurrency == 5
        assert cfg.use_cache is True
        assert cfg.top_n == 20
        assert cfg.report_format == "markdown"
        assert cfg.domains is None
        assert cfg.axes is None
```

## Judgment
- The strict component split leaves 27 false positives and 0 false negatives at threshold 0.5.
- The remaining failure mode is asymmetric: the probe over-promotes some high-surface-overlap isomers, but does not miss blindspots in this run.
- This supports Q-007 G5 as `L3 candidate`, while L4 stays blocked until false-positive isomers are reduced or explained by a stronger negative-control design.
