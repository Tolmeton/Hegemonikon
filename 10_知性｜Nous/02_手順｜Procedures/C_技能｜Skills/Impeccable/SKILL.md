---
name: Impeccable
description: Design refinement bundle adapted from Anthropic's Impeccable skill set. Use when Tolmetes asks for "Impeccable" or wants UI/UX quality raised through focused design subskills.
---

`Impeccable` is a dispatcher skill. It bundles multiple design-oriented subskills and routes to the smallest useful subset.

## When To Use

Use this skill when Tolmetes explicitly mentions `Impeccable`, or when the task is primarily about:

- raising frontend or UX quality
- sharpening visual direction
- improving onboarding or empty states
- auditing interface quality
- refining copy, motion, theming, responsiveness, or polish

## How To Use

1. Read only the specific subskill files needed from `./skills/`.
2. Prefer 1-2 subskills, not the whole bundle.
3. If the task spans multiple phases, use them in sequence.
4. Preserve the existing product language and design system unless Tolmetes asks for a redesign.

## Recommended Dispatch

- New UI or major redesign:
  Read `./skills/frontend-design/SKILL.md`
- One-time project design context setup:
  Read `./skills/teach-impeccable/SKILL.md`
- Onboarding, empty states, first-run UX:
  Read `./skills/onboard/SKILL.md`
- Interface quality audit without fixing:
  Read `./skills/audit/SKILL.md`
- Final visual refinement:
  Read `./skills/polish/SKILL.md`
- Stronger visual personality:
  Read `./skills/bolder/SKILL.md`
- Calmer / less noisy interface:
  Read `./skills/quieter/SKILL.md`
- Color system and palette work:
  Read `./skills/colorize/SKILL.md`
- Motion and transitions:
  Read `./skills/animate/SKILL.md`
- UX writing and clarity:
  Read `./skills/clarify/SKILL.md`
- Extract or simplify content:
  Read `./skills/extract/SKILL.md` and/or `./skills/distill/SKILL.md`
- Adapt to device / responsive / context:
  Read `./skills/adapt/SKILL.md`
- Hardening edge cases and robustness:
  Read `./skills/harden/SKILL.md`
- Design-system alignment and consistency:
  Read `./skills/normalize/SKILL.md`
- Performance-oriented UI cleanup:
  Read `./skills/optimize/SKILL.md`
- Constructive critique:
  Read `./skills/critique/SKILL.md`
- Delight moments and emotional lift:
  Read `./skills/delight/SKILL.md`

## Default Sequence

When the best path is unclear, prefer this order:

1. `teach-impeccable` once per project, if design context is missing
2. one primary making skill such as `frontend-design`, `onboard`, `colorize`, or `clarify`
3. `audit` or `critique` to inspect
4. `polish` to finish

## Notes

- The bundled subskills live under `./skills/` and are self-contained.
- Keep context small: do not load every subskill up front.
- If an existing house style is already strong, refine it instead of replacing it.
