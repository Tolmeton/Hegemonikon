# Codex 委託 brief: 梁4 Phase 2 — Estimator 化の完全実装

## 目的

梁4 Phase 1 (2026-04-11, v1.3 → v1.4) で §5.5 line 266-275 の Pattern B 差し替えと line 315 の SWE-bench N=500 成功転換を完了した。Phase 2 では Phase 1 の核を**論文全体で整合**させ、批評の「proxy 逃避」攻撃を構造的に無効化する残り 5 項目を実装する。

## 背景: Phase 1 の成果 (v1.4)

- 局所忘却曲率密度 $\kappa(\theta) := \|d(\Phi T)\|_g^2 = (4/\alpha^2)\|F\|_g^2$ を主定義として導入
- 観測設計依存の理論量 $\Xi_{\text{theory}}(\nu) := \operatorname{Var}_{u \sim \nu}[\kappa(\theta_u)]$ を定式化
- 経験的 $\Xi_{\text{Var}}, \Xi_{\text{Gini}}, \Xi_{\text{CV}}, \Xi_{\text{impl}}$ を estimator/lower-bound estimator として宣言 (詳細は Appendix E に委ねる予定)
- SWE-bench N=500 の「ヌル結果」を Fisher z 変換で予測帯域計算し、**境界条件の成功確認**に昇格

## Phase 2 実装タスク (5 項目)

Phase 1 の成果を論文全体で整合させる。核心的な未実装項目は 5 つ:

### Task 1: Appendix E 新設 — Estimator 仮定の完全詳細 (最優先, 2 時間)

**位置**: Appendix D (ノルム分離) の直後に新規 Appendix として挿入。

**内容**: 梁4 Phase 1 Codex report (`codex_report_liang4_proxy_estimator.md` の §2.1-§2.4) に書かれた各 estimator の完全な定式化を論文本体に移植する。

**構成**:
```
Appendix E. Estimator 化の詳細 — 仮定 H1-H1''' と命題

E.1 共通設定
 - 理論的 target: $\kappa(\theta), \Xi_{\text{theory}}(\nu)$ の復唱 (§5.5 で定義済み)
 - observation unit $u$ の一般的定義

E.2 $\widehat{\Xi}_{\text{Var}}$ — N=416 統制実験 (§5.5 対応)
 - 仮定 H1: 線形観測モデル, i.i.d. ターン, 固定 compression budget, 四次モーメント有限
 - estimator 式: de-noised variance formula (Codex report §2.1)
 - 命題 V: unbiased + consistent の証明スケッチ
 - bias = O(n⁻¹), variance = O(n⁻¹)

E.3 $\widehat{\Xi}_{\text{Gini}}$ — SWE-bench (§5.5/§5.6 対応)
 - 仮定 H1': multiplicative observation model (lognormal), basis alignment
 - estimator 式: Gini inverse formula via Φ⁻¹ (Codex report §2.2)
 - 命題 G: asymptotic unbiasedness + consistency
 - 但し書き: §5.6 Schur-Horn 条件を満たさないとき lower bound のみ

E.4 $\widehat{\Xi}_{\text{CV}}$ — 全保持対照 (§5.5 line 315 対応)
 - 仮定 H1'': lognormal, fixed budget, noise baseline 独立推定
 - estimator 式: log(1 + CV²) の逆写像 (Codex report §2.3)
 - 命題 C: asymptotic unbiasedness + consistency
 - no-forgetting corollary: $\kappa \approx 0 \Rightarrow \widehat{\Xi}_{\text{CV}} \approx 0$

E.5 $\widehat{\Xi}_{\text{impl}}$ — N=229 CCL 式 (§5.5 line 317-340 対応)
 - 仮定 H1''': Bernoulli omission, logit-linear in $\kappa_k$, 6 座標 basis
 - estimator 式: Gini delta method (Codex report §2.4)
 - 命題 I: coordinate-level heterogeneity の consistent estimator
 - basis alignment 破れの場合は lower bound に降格

E.6 推定量間の関係
 - 4 つの estimator はすべて同じ latent $\Xi_{\text{theory}}(\nu)$ を推定するが、観測単位 $u$ (turn vs trajectory vs layer vs coordinate) が異なる
 - basis alignment の有無で full target vs lower bound が決まる
```

**制約**: Appendix E は estimator 仮定と命題の**詳細**を含めよ。各命題は証明スケッチまで書く。§5.5 本体は Appendix E への参照ですむように簡潔に保つ。

### Task 2: $\Xi_{\text{theory}}$ の overload 解消 (line 321/348 改名) (30 分)

Codex Phase 1 report §7 が指摘した **SOURCE anomaly**: 現行草稿で `$\Xi_{\text{theory}}$` が 3 通りの意味で使われている。

| 場所 | 現状 | 意味 | 改名案 |
|:---|:---|:---|:---|
| line 266 | `Var(λ)` (v1.4 で $\Xi_{\text{theory}}(\nu)$ に更新済) | experiment-level target | 維持 (`$\Xi_{\text{theory}}(\nu)$` or `$\Xi_{\text{theory}}^{(\nu)}$`) |
| line 351 (旧 321) | `Gini(p̄_1,...,p̄_6) = 0.271` | coordinate-level theory (均等使用仮定下の Gini) | `$\Xi_{\text{coord,theory}}$` に改名 |
| line 365 (旧 348) | `Gini(spec(Σ))` (定理 5.6.1) | spectral lower bound | `$\Xi_{\text{spec,proj}}$` に改名 |

**手順**:
1. 論文 v1.4 を読み、`$\Xi_\text{theory}$` または `$\Xi_{\text{theory}}$` の全出現箇所を特定 (grep)
2. 各箇所が 3 つのうちどの意味で使われているかを判定
3. 意味ごとに上記の改名規則を適用
4. 置換後も数式の整合性を確認

**注意**: §5.5 line 266 の experiment-level target と混同しないこと。Codex report §7 を参考にせよ。

### Task 3: §5.7-§5.8 の coherence/τ を proxy 語彙から降格 (1 時間)

Codex Phase 1 report §5.2-§5.3 の結論:
- **Chunk coherence** は estimator ではなく fixed-point diagnostic
- **τ** は proxy ではなく experimental knob / instrument variable

**手順**:
1. §5.7-§5.8 を読み、coherence と τ が estimator/proxy として扱われている箇所を特定
2. 各箇所を以下の語彙に置き換え:
   - coherence → 「G∘F 不動点の post-distillation diagnostic」「量的 invariant」
   - τ → 「実験的 knob」「instrument variable」「initial partition parameter」
3. 「coherence が曲率を推定する」のような表現があれば削除し、「coherence は G∘F の不動点構造を診断する」に置き換え
4. 定理 5.8.1 (Coherence Invariance) は保持するが、「$\Xi$ を推定する」意味合いの語彙を除去

**成果物**: §5.7-§5.8 の editing diff (before/after)

### Task 4: §5.6 Schur-Horn equality condition の本文昇格 (30 分)

現行 line 367 (v1.4) は等号条件を「特徴次元が Σ の固有方向と一致するとき (PCA 後)」と 1 行で書いているのみ。Codex Phase 1 report は、この equality condition が **lower-bound estimator** と **full estimator** の境界を決めると指摘している。

**手順**:
1. 定理 5.6.1 の直後に新しい段落「**等号条件の意味**」を追加
2. 以下を明示:
   - basis alignment が principal directions と一致 → $\widehat{\Xi}$ は full target の estimator
   - 一致しない場合 → lower-bound estimator に降格
   - Appendix E.3/E.5 の但し書きとの接続 (Ξ_Gini と Ξ_impl で発生する境界)
3. 実験設計者が $\widehat{\Xi}$ の解釈を決める時の判断基準として使えるように書く

### Task 5: CKA partial closure 化 + OP-I-5 新設 (30 分)

Codex Phase 1 report §5.1 の結論:
- CKA route は partial closure のみ
- Φ 側の proxy は定義可能だが T 側の独立推定が欠けている
- これは **新しい open problem (OP-I-5)** として記録すべき

**手順**:
1. §5.7 の CKA 関連記述を読む (E9/E10 の箇所, line 369 以降)
2. CKA-based Fisher ratio が $\Xi_{\text{theory}}^{\text{proj}}$ の **lower-bound estimator** として partial に定義できることを記述
3. ただし「$\widehat{T}_l$ の独立推定」が欠けていることを明示
4. §9 の open problem 一覧 (line 1115 付近) に **OP-I-5** を追加:
   ```
   Open Problem OP-I-5. Chebyshev 形式 T の layerwise estimator の独立構成。
   現在 CKA route は Φ 側 proxy のみ持ち、d(ΦT) 全体の estimator にはなっていない
   (梁4 Phase 1 report §5.1 参照)。
   ```
5. §10 結論 (iv) や変更履歴にも簡潔に言及

## 注意事項

1. **梁4 Phase 1 の核 (§5.5 line 266-275 の Pattern B 差し替え, line 315 の Fisher z 帯域) は既に実装済み**。これらは触らないこと
2. **$\kappa(\theta) := \|d(\Phi T)\|_g^2$ は主定義**。Codex Phase 1 report §1 が確定した
3. **梁6 Phase B Codex が並行稼働中** (hook auto-delegated)。論文の数値検証スクリプト関連 (§4.5, P5 line 1108, Appendix B, reproducibility package) は触らないこと
4. **Tolmetes は「バイブコーディング」前提**なので、新たな bug 発見は歓迎される

## 参考資料 (この順で読むこと)

1. **梁4 Phase 1 Codex report**: `10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/plans/codex_report_liang4_proxy_estimator.md` — 全 task の数学的詳細を含む
2. **論文 v1.4**: `10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/series/論文I_力としての忘却_草稿.md` — 編集対象
3. **梁5 Codex report**: `10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/plans/codex_report_g_alpha_literature.md` — Option C 採用の根拠 (Ay et al. 2017 引用の文脈)

## 出力形式

同じディレクトリの `codex_report_liang4_phase2_estimator_completion.md` に書き出す。

```markdown
# 梁4 Phase 2 実装報告

## 0. 実装サマリー
<各 Task の完了状況, 論文 v1.4 → v1.5 の diff 統計>

## 1. Task 1: Appendix E 新設
<新 Appendix E の全テキスト (~500-800 行規模)>

## 2. Task 2: Ξ_theory overload 解消
<改名した全箇所の before/after diff>

## 3. Task 3: coherence/τ 降格
<§5.7-§5.8 の editing diff>

## 4. Task 4: Schur-Horn equality condition 昇格
<§5.6 の editing diff>

## 5. Task 5: CKA partial closure + OP-I-5
<§5.7 CKA 箇所の diff + OP-I-5 の新規テキスト>

## 6. 論文本体への反映提案 (総合 diff)
<全編集を統合した統一 diff>

## 7. 残された open problem (梁4 Phase 3 候補)
<もしあれば>
```

## 制約

- **時間**: 3-5 時間
- **編集対象**: 論文 v1.4 本体 (直接編集可、提案ではなく実装)
- **コンフリクト回避**: §4.5, §10, §6.7-§6.8, P5 line 1108, Appendix B は**触らない** (梁5/梁6 Phase A/B の担当範囲)
- **SOURCE 厳格**: line 番号を必ず明示
- **言語**: 日本語
- **数式**: LaTeX 記法 ($...$, $$...$$) を使用

## 補足

- 論文 v1.4 の変更履歴末尾で「梁4 Phase 2 は後続の Codex 委託で処理予定」と明示してある
- Phase 2 完了後の論文は v1.5 になる予定
- 各 Task の実装が完了したら変更履歴を v1.5 として更新し、何を実装したかを追記すること
