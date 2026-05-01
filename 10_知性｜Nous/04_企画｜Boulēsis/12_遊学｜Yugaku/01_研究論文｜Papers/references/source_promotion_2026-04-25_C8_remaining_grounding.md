# C8 remaining grounding SOURCE promotion — 2026-04-25

対象: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/LLMに身体はあるか_存在証明版_v0.1_日本語.md`

目的: C8 の未照合 SOURCE を潰し、`direct grounding / mediated referential grounding / circumvention / image-density question` の型分類を外部原典で支える。

## Promotion Table

| ID | 原典 | local SOURCE | 判定 |
|:---|:---|:---|:---|
| P6 | Bender & Koller, *Climbing towards NLU*, ACL 2020 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/_sources/Bender_Koller_2020_Climbing_Towards_NLU.pdf` / `.txt` | SOURCE |
| P7 | Kiela, Bulat, Vero, & Clark, *Virtual Embodiment*, arXiv:1610.07432 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/_sources/Kiela_2016_Virtual_Embodiment.pdf` / `.txt` | SOURCE |
| P8 | Kim et al., *OpenVLA*, arXiv:2406.09246v3 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/_sources/Kim_2024_OpenVLA.pdf` / `.txt` | SOURCE |
| P9 | Wu et al., *The Mechanistic Emergence of Symbol Grounding in Language Models*, arXiv:2510.13796v2 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/_sources/Mechanistic_Emergence_Symbol_Grounding_2510.13796.pdf` / `.txt` | SOURCE |

## P6 — Bender & Koller (2020)

SOURCE anchor:

- Abstract and §1 define the objection: a system trained only on form has no route to meaning.
- §3 defines meaning as relation between linguistic form and communicative intent.
- §5 gives the Octopus Test: the octopus sees only form and eventually diverges when communicative intent is needed.
- §9 concedes that grounding data or interaction data can add signals beyond form.

本文への効き:

- C8 に対する最強の古典的攻撃 SOURCE。  
- 本稿の応答は、「form-only から human meaning が出る」ではなく、「form-only でない operating LLM / tool-using LLM / interaction-bearing system では $F_B$ の像が空と断定できない」へ置くべき。
- §3.2-§3.3 の Bender & Koller 段落は SOURCE 化済み。§7.3 に octopus 直接引用を足すかは文量判断。

## P7 — Kiela et al. (2016)

SOURCE anchor:

- Title/source confirms `Virtual Embodiment` の著者は Kiela, Bulat, Vero, & Clark。meta に残っていた `Botta & Vijayaraghavan (2016)` は典拠名として不一致。
- §1 proposes virtual embodiment as a long-term AI strategy.
- §2 frames virtual worlds as a way to ground semantics through interaction with an environment.
- The paper gives a hierarchy of virtual embodied manifestations from basic world interaction to multi-objective, communicative planning.

本文への効き:

- `virtual embodiment` は physical direct grounding と mediated/text-only grounding の中間 SOURCE。
- C8 の direct grounding を human phenomenology に閉じない根拠として使える。
- 現本文には未投入。投入するなら §7.3 table に `Virtual embodiment` 行を足す。

## P8 — Kim et al. (2024) OpenVLA

SOURCE anchor:

- Abstract states OpenVLA is a 7B open-source vision-language-action model trained on 970k real-world robot demonstrations.
- §3 describes mapping image observation and language instruction to robot action tokens.
- §5 evaluates multiple robot embodiments and language-conditioned manipulation tasks.
- Appendix task descriptions include explicit language grounding tasks where the robot must select the target object named by the instruction.

本文への効き:

- §7.3 table の `Embodied AI / VLA` 行を SOURCE 化する。
- `H(s), H(a)` 増加の実装例として妥当。ただし direct grounding の哲学的完成ではなく、vision/action channel 増加の工学的 SOURCE。
- 既存参考文献行は存在する。

## P9 — Wu et al. (2025)

SOURCE anchor:

- Abstract states symbol grounding can emerge in language models and that the work traces loci/mechanisms through mechanistic and causal analysis.
- §4-§5 define grounding information gain and behavioral tests.
- §7 identifies middle-layer gather/aggregate attention heads as mechanistic pathways.
- Causal interventions on those heads affect grounding behavior, supporting a structural-probing reading.

本文への効き:

- §7.3 table の `Mechanistic emergence of grounding` 行を SOURCE 化する。
- 本稿の `F_B` structural probing と image-density question に直接つながる。
- 本文 table に `(Wu et al., 2025)` を追加し、参考文献へ追加済み。

## Integration Decisions

| 論点 | 判定 |
|:---|:---|
| `Botta & Vijayaraghavan (2016)` | SOURCE 名として確認不能。`Kiela et al. (2016) Virtual Embodiment` に置換する。 |
| Bender & Koller octopus | SOURCE 取得済み。本文 §7.3 へ直接追加するかは文量判断。 |
| OpenVLA | 既存 table/ref を支える SOURCE として確定。 |
| Mechanistic emergence | table/ref へ反映済み。 |

## Remaining Editorial Choice

未照合 SOURCE は消えた。残るのは SOURCE 不足ではなく、本文へどこまで入れるかの編集判断である。

- §7.3 に Bender & Koller の Octopus Test を 1 文で入れるか。
- §7.3 table に `Virtual embodiment (Kiela et al., 2016)` 行を追加するか。
- `Embodied AI / VLA` 行を OpenVLA 単独ではなく `Virtual embodiment / VLA` に分けるか。
