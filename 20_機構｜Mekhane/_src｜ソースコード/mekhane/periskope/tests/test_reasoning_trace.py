# PROOF: mekhane/periskope/tests/test_reasoning_trace.py
# PURPOSE: periskope モジュールの reasoning_trace に対するテスト
import pytest
from mekhane.periskope.cognition.reasoning_trace import (
    ReasoningStep,
    ReasoningTrace,
    _extract_section,
    _parse_analysis,
)

class TestReasoningTrace:
    @pytest.mark.parametrize(
        "text, header, expected_return",
        [
            # Normal well-formatted
            ("## LEARNED\n- A\n- B\n## NEXT", "LEARNED", ["A", "B"]),
            # LLM variations
            ("**LEARNED:**\n- Fact 1\n\n**GAPS:**", "LEARNED", ["Fact 1"]),
            ("LEARNED:\n- Fact 2\n", "LEARNED", ["Fact 2"]),
            ("learned:\n- Fact 3", "LEARNED", ["Fact 3"]),
            ("## Learned:\n* Fact 4\n* Fact 5", "LEARNED", ["Fact 4", "Fact 5"]),
            # Empty variations
            ("## LEARNED\nNONE\n## NEXT", "LEARNED", []),
            ("## LEARNED\nNone.\n", "LEARNED", []),
            ("## LEARNED\nnone\n", "LEARNED", []),
            # Missing header
            ("## GAPS\n- X", "LEARNED", []),
        ],
    )
    def test_extract_section(self, text: str, header: str, expected_return: list):
        """Test the regex-based section extraction with various LLM formatting quirks."""
        result = _extract_section(text, header)
        assert result == expected_return

    def test_parse_analysis_full(self):
        """Test full parsing of a well-formed LLM response."""
        llm_response = """
## LEARNED
- Fact A
- Fact B

## CONTRADICTIONS
- Disagreement X

## GAPS
- Missing Y
- Missing Z

## NEXT
- Query 1
- Query 2

## CONFIDENCE
85%
"""
        step = _parse_analysis(llm_response, iteration=2)
        assert step.iteration == 2
        assert step.learned == ["Fact A", "Fact B"]
        assert step.contradictions == ["Disagreement X"]
        assert step.gaps == ["Missing Y", "Missing Z"]
        assert step.next_queries == ["Query 1", "Query 2"]
        assert step.confidence == 0.85

    def test_parse_analysis_learned_nonzero(self):
        """Regression test for the learned=0 issue.

        If the LEARNED section contains valid bullet points, len(step.learned) must be > 0.
        """
        llm_response = """
Here is my analysis:

**LEARNED:**
- The Free Energy Principle states that organisms minimize surprise.
- Active inference is a corollary of FEP.

**CONTRADICTIONS:**
None found so far.

**GAPS:**
- Mathematical formulation details.

**NEXT:**
- "free energy principle mathematical formulation"

**CONFIDENCE:**
70%
"""
        step = _parse_analysis(llm_response, iteration=1)
        assert len(step.learned) == 2, "Failed to parse LEARNED section correctly"
        assert step.learned[0].startswith("The Free Energy Principle")
        assert len(step.contradictions) == 0
        assert len(step.gaps) == 1
        assert len(step.next_queries) == 1
        assert step.confidence == 0.7

    def test_reasoning_trace_cumulative(self):
        """Test that cumulative_knowledge correctly aggregates across steps."""
        trace = ReasoningTrace(query="test query")

        trace.steps.append(ReasoningStep(
            iteration=1,
            learned=["Fact 1", "Fact 2"],
            contradictions=[],
            gaps=["Gap A"],
            next_queries=["Q1"],
            confidence=0.5
        ))
        
        trace.steps.append(ReasoningStep(
            iteration=2,
            learned=["Fact 3"],
            contradictions=["Contradiction X"],
            gaps=["Gap B"],
            next_queries=["Q2"],
            confidence=0.8
        ))

        # Test latest properties
        assert trace.latest_confidence == 0.8
        assert trace.open_questions == ["Gap B"]

        # Test cumulative methods
        all_learned = trace.cumulative_knowledge
        assert "Fact 1" in all_learned
        assert "Fact 3" in all_learned
        assert "Contradiction X" in all_learned

    def test_reasoning_trace_format_report(self):
        """Test the markdown formatting of the trace for the final report."""
        trace = ReasoningTrace(query="test formatting")
        trace.steps.append(ReasoningStep(
            iteration=1,
            learned=["Initial fact"],
            contradictions=[],
            gaps=["Unknown thing"],
            next_queries=["q1"],
            confidence=0.4
        ))
        trace.steps.append(ReasoningStep(
            iteration=2,
            learned=["Final fact"],
            contradictions=["Conflict Y"],
            gaps=[],
            next_queries=[],
            confidence=0.9
        ))

        md = trace.format_for_report()
        assert "## Reasoning Trace" in md
        assert "Initial fact" in md
        assert "Final fact" in md
        assert "Conflict Y" in md
        assert "**Confidence:** 40%" in md
        assert "**Confidence:** 90%" in md
