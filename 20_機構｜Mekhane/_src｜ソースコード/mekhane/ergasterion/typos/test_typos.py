# PROOF: [L2/インフラ] <- mekhane/ergasterion/typos/test_typos.py S2→プロンプト言語が必要→test_typos が担う
#!/usr/bin/env python3
"""
typos Unit Tests
======================

Test suite for typos parser and integration.

Usage:
    python test_typos.py
"""

import sys
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from typos import PromptLangParser, ParseError, validate_file


# PURPOSE: Test cases for PromptLangParser
class TestPromptLangParser(unittest.TestCase):
    """Test cases for PromptLangParser."""

    # PURPOSE: Test parsing a minimal prompt with only required fields
    def test_minimal_prompt(self):
        """Test parsing a minimal prompt with only required fields."""
        content = """#prompt test-minimal

@role:
  Test role

@goal:
  input -> output
"""
        parser = PromptLangParser(content)
        prompt = parser.parse()

        self.assertEqual(prompt.name, "test-minimal")
        self.assertEqual(prompt.blocks.get("@role"), "Test role")
        self.assertEqual(prompt.blocks.get("@goal"), "input -> output")

    # PURPOSE: Test parsing a prompt with all fields
    def test_full_prompt(self):
        """Test parsing a prompt with all fields."""
        content = """#prompt test-full

@role:
  Full test role

@goal:
  complex input -> structured output

@constraints:
  - Constraint one
  - Constraint two

@tools:
  - search_web: Search the web
  - read_file: Read files

@resources:
  - kb: file:///path/to/kb

@format:
  ```json
  {"key": "value"}
  ```

@examples:
  - input: "test input"
    output: "test output"
"""
        parser = PromptLangParser(content)
        prompt = parser.parse()

        self.assertEqual(prompt.name, "test-full")
        self.assertEqual(prompt.blocks.get("@role"), "Full test role")
        self.assertEqual(prompt.blocks.get("@goal"), "complex input -> structured output")
        self.assertEqual(len(prompt.blocks.get("@constraints", [])), 2)
        self.assertEqual(prompt.blocks.get("@constraints", [])[0], "Constraint one")
        self.assertEqual(len(prompt.blocks.get("@tools", [])), 2)
        self.assertIn("search_web", prompt.blocks.get("@tools", []))
        self.assertEqual(len(prompt.blocks.get("@resources", {})), 1)
        self.assertIn("kb", prompt.blocks.get("@resources", {}))
        self.assertEqual(prompt.blocks.get("@resources", {})["kb"], "file:///path/to/kb")
        self.assertIn("json", prompt.blocks.get("@format", ""))
        self.assertEqual(len(prompt.blocks.get("@examples", [])), 1)
        self.assertEqual(prompt.blocks.get("@examples", [])[0]["input"], '"test input"')

    # PURPOSE: Test that missing header raises error
    def test_missing_header(self):
        """Test that missing header raises error."""
        content = """@role:
  Test role
"""
        parser = PromptLangParser(content)
        with self.assertRaises(ParseError):
            parser.parse()

    # PURPOSE: Test expanding prompt to natural language
    def test_expand(self):
        """Test expanding prompt to natural language."""
        content = """#prompt test-expand

@role:
  Expert assistant

@goal:
  question -> answer
"""
        parser = PromptLangParser(content)
        prompt = parser.parse()
        expanded = prompt.expand()

        self.assertIn("Expert assistant", expanded)
        self.assertIn("question -> answer", expanded)

    # PURPOSE: Test JSON serialization
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

    # PURPOSE: Test parsing prompt with no constraints
    def test_empty_constraints(self):
        """Test parsing prompt with no constraints."""
        content = """#prompt test-no-constraints

@role:
  Simple role

@goal:
  in -> out
"""
        parser = PromptLangParser(content)
        prompt = parser.parse()

        self.assertEqual(prompt.blocks.get("@constraints", []), [])

    # PURPOSE: Test parsing multi-line goal
    def test_multiline_goal(self):
        """Test parsing multi-line goal."""
        content = """#prompt test-multiline

@role:
  Multiline test

@goal:
  complex input with
  multiple lines -> output
"""
        parser = PromptLangParser(content)
        prompt = parser.parse()

        self.assertIn("complex input with", prompt.blocks.get("@goal", ""))
        self.assertIn("multiple lines", prompt.blocks.get("@goal", ""))


# PURPOSE: Test cases for validation
class TestValidation(unittest.TestCase):
    """Test cases for validation."""

    # PURPOSE: Test validating a valid prompt
    def test_valid_file(self):
        """Test validating a valid prompt."""
        content = """#prompt valid
#syntax: v8

<:role: Valid role :>
<:goal: valid -> pass :>
<:constraints:
  - Add at least one constraint to pass new validation rules
:>
"""
        # Create temp file
        temp_path = Path(__file__).parent / "staging" / "_test_valid.prompt"
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path.write_text(content, encoding="utf-8")

        try:
            valid, msg = validate_file(str(temp_path))
            self.assertTrue(valid)
            self.assertEqual(msg, "Validation passed.")
        finally:
            temp_path.unlink(missing_ok=True)

    # PURPOSE: Test validation fails with missing role
    def test_missing_role(self):
        """Test validation fails with missing role."""
        content = """#prompt missing-role

@goal:
  test -> fail
"""
        temp_path = Path(__file__).parent / "staging" / "_test_missing_role.prompt"
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path.write_text(content, encoding="utf-8")

        try:
            valid, msg = validate_file(str(temp_path))
            self.assertFalse(valid)
            self.assertIn("@role", msg)
        finally:
            temp_path.unlink(missing_ok=True)


# PURPOSE: Integration tests for typos_integrate.py
class TestIntegration(unittest.TestCase):
    """Integration tests for typos_integrate.py."""

    # PURPOSE: Test that generate creates a file in staging
    def test_generate_creates_file(self):
        """Test that generate creates a file in staging."""
        from typos_integrate import generate_prompt

        filepath, prompt = generate_prompt(
            slug="_test-gen",
            role="Test role",
            goal="test -> pass",
            constraints=["Test constraint"],
        )

        try:
            self.assertTrue(filepath.exists())
            self.assertEqual(prompt.blocks.get("@role"), "Test role")
            self.assertEqual(len(prompt.blocks.get("@constraints", [])), 1)
        finally:
            filepath.unlink(missing_ok=True)

    # PURPOSE: Test listing prompts in staging
    def test_list_prompts(self):
        """Test listing prompts in staging."""
        from typos_integrate import list_prompts

        prompts = list_prompts()
        # Should return a list (may be empty or have items)
        self.assertIsInstance(prompts, list)


# PURPOSE: Test cases for v2.1 @extends and @mixin features
class TestExtendsAndMixin(unittest.TestCase):
    """Test cases for v2.1 @extends and @mixin features."""

    # PURPOSE: Test basic template inheritance
    def test_basic_extends(self):
        """Test basic template inheritance."""
        from typos import parse_all, resolve

        content = """#prompt base_spec
@role:
  Base role

@goal:
  Base goal

@constraints:
  - Base constraint

#prompt child_spec
@extends: base_spec
@goal:
  Child goal

@constraints:
  - Child constraint
"""
        result = parse_all(content)
        child = result.get_prompt("child_spec")
        resolved = resolve(child, result)

        self.assertEqual(resolved.blocks.get("@role"), "Base role")  # inherited
        self.assertEqual(resolved.blocks.get("@goal"), "Child goal")  # overridden
        self.assertEqual(len(resolved.blocks.get("@constraints", [])), 2)  # concatenated
        self.assertIn("Base constraint", resolved.blocks.get("@constraints", []))
        self.assertIn("Child constraint", resolved.blocks.get("@constraints", []))

    # PURPOSE: Test mixin composition
    def test_mixin_composition(self):
        """Test mixin composition."""
        from typos import parse_all, resolve

        content = """#mixin json_output
@format:
  type: json

@constraints:
  - Output must be valid JSON

#prompt my_prompt
@mixin: [json_output]
@role:
  JSON generator
@goal:
  Generate JSON
"""
        result = parse_all(content)
        prompt = result.get_prompt("my_prompt")
        resolved = resolve(prompt, result)

        self.assertEqual(resolved.blocks.get("@role"), "JSON generator")
        self.assertIn("type: json", resolved.blocks.get("@format", ""))
        self.assertIn("Output must be valid JSON", resolved.blocks.get("@constraints", []))

    # PURPOSE: Test multiple mixin composition (left to right)
    def test_multiple_mixins(self):
        """Test multiple mixin composition (left to right)."""
        from typos import parse_all, resolve

        content = """#mixin mixin_a
@constraints:
  - Constraint A

#mixin mixin_b
@constraints:
  - Constraint B

#prompt multi_mixin
@mixin: [mixin_a, mixin_b]
@role:
  Multi mixin role
@goal:
  Test
@constraints:
  - Constraint C
"""
        result = parse_all(content)
        prompt = result.get_prompt("multi_mixin")
        resolved = resolve(prompt, result)

        # Should have constraints from both mixins + self
        self.assertEqual(len(resolved.blocks.get("@constraints", [])), 3)

    # PURPOSE: Test extends combined with mixin
    def test_extends_with_mixin(self):
        """Test extends combined with mixin."""
        from typos import parse_all, resolve

        content = """#mixin common_format
@format:
  markdown

#prompt parent
@role:
  Parent role
@goal:
  Parent goal

#prompt child
@extends: parent
@mixin: [common_format]
@constraints:
  - Child constraint
"""
        result = parse_all(content)
        child = result.get_prompt("child")
        resolved = resolve(child, result)

        self.assertEqual(resolved.blocks.get("@role"), "Parent role")
        self.assertEqual(resolved.blocks.get("@goal"), "Parent goal")
        self.assertIn("markdown", resolved.blocks.get("@format", ""))

    # PURPOSE: Test that circular references raise error
    def test_circular_reference_detection(self):
        """Test that circular references raise error."""
        from typos import parse_all, resolve, CircularReferenceError

        content = """#prompt a
@extends: b
@role:
  A
@goal:
  A

#prompt b
@extends: a
@role:
  B
@goal:
  B
"""
        result = parse_all(content)
        prompt_a = result.get_prompt("a")

        with self.assertRaises(CircularReferenceError):
            resolve(prompt_a, result)

    # PURPOSE: Test that undefined references raise error
    def test_undefined_reference(self):
        """Test that undefined references raise error."""
        from typos import (
            parse_all,
            resolve,
            ReferenceError as PromptReferenceError,
        )

        content = """#prompt child
@extends: nonexistent
@role:
  Child
@goal:
  Child
"""
        result = parse_all(content)
        child = result.get_prompt("child")

        with self.assertRaises(PromptReferenceError):
            resolve(child, result)

    # PURPOSE: Test parsing multiple prompts in one file
    def test_parse_all_multiple_prompts(self):
        """Test parsing multiple prompts in one file."""
        from typos import parse_all

        content = """#prompt first
@role:
  First role
@goal:
  First goal

#prompt second
@role:
  Second role
@goal:
  Second goal
"""
        result = parse_all(content)

        self.assertEqual(len(result.prompts), 2)
        self.assertIn("first", result.prompts)
        self.assertIn("second", result.prompts)

    # PURPOSE: Test that dict fields use child priority
    def test_dict_merge_child_priority(self):
        """Test that dict fields use child priority."""
        from typos import parse_all, resolve

        content = """#prompt parent
@role:
  Parent
@goal:
  Parent
@tools:
  - search: Parent search
  - read: Parent read

#prompt child
@extends: parent
@tools:
  - search: Child search overrides
"""
        result = parse_all(content)
        child = result.get_prompt("child")
        resolved = resolve(child, result)

        # Child's search should override parent's
        self.assertEqual(resolved.blocks.get("@tools", {})["search"], "Child search overrides")
        # Parent's read should be inherited
        self.assertEqual(resolved.blocks.get("@tools", {})["read"], "Parent read")

    # PURPOSE: Test that already resolved prompts are returned as-is
    def test_already_resolved_prompt(self):
        """Test that already resolved prompts are returned as-is."""
        from typos import parse_all, resolve

        content = """#prompt simple
@role:
  Simple
@goal:
  Simple
"""
        result = parse_all(content)
        prompt = result.get_prompt("simple")

        resolved1 = resolve(prompt, result)
        resolved2 = resolve(resolved1, result)  # Should return same object

        self.assertTrue(resolved2._resolved)


# PURPOSE: Test cases for v7.0 description act directives (24 acts)
class TestV7Directives(unittest.TestCase):
    """Test cases for v7.0 description act directives."""

    # PURPOSE: Test parsing v7.0 directives into blocks dict
    def test_v7_parse_basic(self):
        """Test parsing v7.0 directives into blocks dict."""
        from typos import V7_DIRECTIVES

        content = """#prompt v7_test

@role:
  Analyst

@intent:
  Understand motivation

@rationale:
  Evidence-based reasoning

@detail:
  Full specification
"""
        parser = PromptLangParser(content)
        prompt = parser.parse()

        self.assertEqual(prompt.name, "v7_test")
        self.assertEqual(prompt.blocks.get("@role"), "Analyst")
        # @role is now also in blocks, so 4 total
        self.assertEqual(len(prompt.blocks), 4)
        self.assertIn("@intent", prompt.blocks)
        self.assertIn("@rationale", prompt.blocks)
        self.assertIn("@detail", prompt.blocks)
        self.assertEqual(prompt.blocks["@intent"], "Understand motivation")

    # PURPOSE: Test all 24 directives are in V7_DIRECTIVES
    def test_v7_directive_count(self):
        """Test that V7_DIRECTIVES contains 24 directives."""
        from typos import V7_DIRECTIVES
        self.assertEqual(len(V7_DIRECTIVES), 24)

    # PURPOSE: Test v7.0 directives compile correctly
    def test_v7_compile(self):
        """Test v7.0 directives appear in compiled output."""
        content = """#prompt v7_compile

@role:
  Expert

@spec:
  JSON format with strict schema

@fact:
  Zaslavsky et al. (2018)

@assume:
  Language universals hold
"""
        parser = PromptLangParser(content)
        prompt = parser.parse()
        compiled = prompt.compile(format="markdown")

        self.assertIn("## Spec", compiled)
        self.assertIn("JSON format with strict schema", compiled)
        self.assertIn("## Fact", compiled)
        self.assertIn("## Assume", compiled)

    # PURPOSE: Test v7.0 directives expand correctly
    def test_v7_expand(self):
        """Test v7.0 directives appear in expanded output."""
        content = """#prompt v7_expand

@role:
  Researcher

@focus:
  Accuracy and latency

@schema:
  {type: object}
"""
        parser = PromptLangParser(content)
        prompt = parser.parse()
        expanded = prompt.expand()

        self.assertIn("Focus:", expanded)
        self.assertIn("Accuracy and latency", expanded)
        self.assertIn("Schema:", expanded)

    # PURPOSE: Test legacy directives (@goal, @format, @context) are NOT duplicated in blocks
    def test_v7_legacy_not_duplicated(self):
        """Test legacy directives are handled by legacy parser, not blocks."""
        content = """#prompt v7_legacy

@role:
  Test

@goal:
  This is a legacy goal

@format:
  markdown output
"""
        parser = PromptLangParser(content)
        prompt = parser.parse()

        # All directives are now stored in blocks, accessed via properties
        self.assertEqual(prompt.blocks.get("@goal"), "This is a legacy goal")
        self.assertEqual(prompt.blocks.get("@format"), "markdown output")
        self.assertIn("@goal", prompt.blocks)
        self.assertIn("@format", prompt.blocks)

    # PURPOSE: Test v7.0 blocks in to_dict output
    def test_v7_to_dict(self):
        """Test v7.0 blocks appear in to_dict output."""
        content = """#prompt v7_dict

@role:
  Test

@data:
  Rate-Distortion results
"""
        parser = PromptLangParser(content)
        prompt = parser.parse()
        d = prompt.to_dict()

        self.assertIn("blocks", d)
        self.assertEqual(d["blocks"]["@data"], "Rate-Distortion results")

    # PURPOSE: Test v7.0 blocks with extends inheritance
    def test_v7_extends_blocks(self):
        """Test v7.0 blocks are inherited via extends."""
        from typos import parse_all, resolve

        content = """#prompt parent
@role:
  Parent

@intent:
  Parent intent

@fact:
  Parent fact

#prompt child
@extends: parent
@intent:
  Child intent override
"""
        result = parse_all(content)
        child = result.get_prompt("child")
        resolved = resolve(child, result)

        # Child's @intent should override parent's
        self.assertEqual(resolved.blocks["@intent"], "Child intent override")
        # Parent's @fact should be inherited
        self.assertEqual(resolved.blocks["@fact"], "Parent fact")


class TestV71LayeredArchitecture(unittest.TestCase):
    """Test cases for v7.1 layered architecture."""

    V71_CONTENT = """\
#prompt layered_test

## Why

@intent:
  Verify hypothesis

@goal:
  Find refutation conditions

## When

@fact:
  Zaslavsky proved optimality

@assume:
  Universality holds

---

fact.confidence: 95%
fact.source: PNAS2018
assume.falsifiable: true

fact -> assert
context, intent -> goal
"""

    def test_family_scope(self):
        """Test L1: ## family scope parsing."""
        p = PromptLangParser(self.V71_CONTENT)
        r = p.parse()
        self.assertIn("why", r.family_scope)
        self.assertIn("@intent", r.family_scope["why"])
        self.assertIn("@goal", r.family_scope["why"])
        self.assertIn("when", r.family_scope)
        self.assertIn("@fact", r.family_scope["when"])
        self.assertIn("@assume", r.family_scope["when"])

    def test_block_meta(self):
        """Test L3: metadata parsing after ---."""
        p = PromptLangParser(self.V71_CONTENT)
        r = p.parse()
        self.assertEqual(r.block_meta["fact.confidence"], "95%")
        self.assertEqual(r.block_meta["fact.source"], "PNAS2018")
        self.assertEqual(r.block_meta["assume.falsifiable"], "true")

    def test_block_relations(self):
        """Test L4: relation parsing after ---."""
        p = PromptLangParser(self.V71_CONTENT)
        r = p.parse()
        self.assertEqual(len(r.block_relations), 2)
        self.assertEqual(r.block_relations[0], (["fact"], "->", ["assert"]))
        self.assertEqual(r.block_relations[1], (["context", "intent"], "->", ["goal"]))

    def test_compile_view_mode(self):
        """Test compile produces View Mode with family grouping."""
        p = PromptLangParser(self.V71_CONTENT)
        r = p.parse()
        compiled = r.compile(format="markdown")
        self.assertIn("## Why", compiled)
        self.assertIn("## When", compiled)
        self.assertIn("confidence: 95%", compiled)

    def test_backward_compat_flat(self):
        """Test v7.0 flat mode still works without ## or ---."""
        content = "#prompt flat\n\n@intent:\n  Just a test\n\n@fact:\n  Some fact\n"
        p = PromptLangParser(content)
        r = p.parse()
        compiled = r.compile(format="markdown")
        self.assertIn("## Intent", compiled)
        self.assertIn("## Fact", compiled)
        self.assertEqual(r.family_scope, {})
        self.assertEqual(r.block_meta, {})
        self.assertEqual(r.block_relations, [])

    def test_to_dict_includes_v71(self):
        """Test v7.1 fields appear in to_dict."""
        p = PromptLangParser(self.V71_CONTENT)
        r = p.parse()
        d = r.to_dict()
        self.assertIn("family_scope", d)
        self.assertIn("block_meta", d)
        self.assertIn("block_relations", d)


if __name__ == "__main__":
    # Run tests with verbosity
    unittest.main(verbosity=2)
