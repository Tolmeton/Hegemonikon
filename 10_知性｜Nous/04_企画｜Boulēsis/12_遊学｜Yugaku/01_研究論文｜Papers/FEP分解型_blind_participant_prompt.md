# FEP 分解型 blind participant prompt

このファイルは、盲検列挙者へ渡す clean prompt である。
下の `PROMPT` ブロックだけを渡す。評価基準、内部分類表、認知アーキテクチャ側の語彙は渡さない。

```text
You are an independent theoretical analyst. Your task is to inspect the standard Free Energy Principle and active inference literature and list the mathematically or operationally distinct decompositions, contrasts, or parameter splits that appear in that literature.

Use only the Free Energy Principle, active inference, variational inference, Markov blankets, expected free energy, precision weighting, hierarchical generative models, interoceptive inference, and related standard literature. Do not use any requester-specific framework or taxonomy beyond the FEP and active inference literature.

Please produce:

1. A table of distinct decompositions or contrasts.
2. For each item, include:
   - a short label you assign,
   - the mathematical object, dynamical structure, boundary structure, policy quantity, parameter, or model class being decomposed,
   - the contrast or opposition involved,
   - the literature anchor or source family,
   - whether the item is algebraic, boundary-based, action/inference-based, policy-functional, precision-related, hierarchical or scale-related, temporal, interoceptive or affective, or another category,
   - your confidence level: high, medium, or low,
   - whether it appears to be an independent decomposition, a derived bridge, an internal parameter, or a domain-specific extension.

3. After the table, synthesize the abstract dimensions suggested by these decompositions. Do not map them to any named architecture or pre-existing taxonomy.
4. Explicitly list any missing or weak dimensions. Mark uncertainty rather than forcing a fit.
5. Do not invent citations. If you are unsure of a source, write "source uncertain" and explain why.
```

## 使用記録

| 日付 | 渡した相手 / モデル | 返答保存先 | contamination check |
|:---|:---|:---|:---|
| 2026-05-01 | Gemini CLI default / Gemini CLI flash / Claude bare | 返答なし。実行ログ: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEP分解型_blind_execution_log_2026-05-01.md` | blind evidence としては不採用。Gemini は capacity exhaustion、Claude は auth failure。 |
| 2026-05-01 | Gemini API `gemini-3.1-flash-lite-preview` | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/blind_outputs/gemini_gemini-3.1-flash-lite-preview_20260501T132107Z.md` | 禁止語直接混入なし。改訂 rubric verdict は Weak pass。 |
