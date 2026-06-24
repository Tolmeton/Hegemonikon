# Contributing to Hegemonikon

Hegemonikon is a deductive system: every component descends from a single axiom, so the parts hold together only as long as that coherence is protected. Contributions are welcome, but this is **not** a project that merges broadly and shallowly. The kernel is treated as load-bearing.

Two principles govern everything here:

- **SOURCE discipline.** Claims are backed by a source — a file, a line, a result, a citation. Inference and memory are kept separate from established fact. A contribution that asserts without a source is incomplete.
- **Propositions over rhetoric.** Changes are argued from structure, not from tone or popularity. Refutation is welcome; deference is not the goal.

## Contribution ladder

Contributions are accepted by rung. Lower rungs are easy to accept; higher rungs require correspondingly more.

| Rung | Contribution | What it must satisfy |
|:--|:--|:--|
| **L1** | Docs: typo, broken link, added source | Source-backed, no change of meaning |
| **L2** | Example / witness: a before→after or failure-prevention case | Public-safe, with reproduction conditions |
| **L3** | A thin wrapper or entry point over existing constructs | Does not change any kernel proposition |
| **L4** | Improvement to the meaning or phases of an operation | Source/inference separated, a rejection ledger, a test or witness |
| **L5** | A proposal touching the core (FEP, category theory, the operation set) | **Not merged directly** — opened as an issue / RFC / argument first |

The kernel (`kernel/`) is the axiomatic core. Changes to it are L5 by definition: propose, argue, and let the proposal survive scrutiny before any merge is considered.

## How to propose

1. **Open an issue first** for anything beyond L1–L2. State the problem, the source, and an observable acceptance condition.
2. One issue = one problem + one artifact + one close condition. Do not bundle unrelated changes.
3. For L5 (kernel) proposals, frame the change as an argument: what proposition changes, what derivation supports it, what it costs.

## What will not be accepted

- Changes that quietly narrow a proposition for the sake of being "safe" or "conventional."
- Contributions that depend on or expose private state (local paths, credentials, unreviewed runtime detail).
- Reframing Hegemonikon as an ordinary prompt pack or agent framework — that erases the system's claim rather than improving it.

## License

By contributing, you agree that your contributions are licensed under the project's [MIT License](LICENSE).
