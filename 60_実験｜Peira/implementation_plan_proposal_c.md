# Implementation Plan: Proposal C (Math Static Analysis)

## Objective
Implement an AST-based batch static analysis script to verify the consistency and dimensional accuracy of mathematical formulas (Category Theory, FEP, Information Geometry) scattered across Hegemonikon internal papers (Paper I-XI) and `.typos` files.

## Scope
- Target Files: 
  - `10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/paper_*.md`
  - `*.typos` files across the repository.
- Script Location: `60_実験｜Peira/00_汎用｜General/math_analyzer.py`
- Features:
  1. Parse mathematical blocks (`$$...$$` and `$...$`).
  2. Parse Adjunctions (`⊣`).
  3. Static Analysis checks:
     - Adjunction direction checks (ensure Left adjoint is on the left, Right adjoint on the right, matching known pairs).
     - Simple type checking for FEP variables (e.g., checking if integral ranges or dimensions match).
  4. Generate a summary report of formulas and warnings.

## Steps
1. Create `math_analyzer.py`.
2. Implement file crawling logic.
3. Implement Regex-based AST extraction for math.
4. Implement consistency checks.
5. Run the script and verify output.
