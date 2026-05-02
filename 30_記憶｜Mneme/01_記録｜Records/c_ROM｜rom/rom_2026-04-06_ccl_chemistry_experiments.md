---
rom_id: rom_2026-04-06_ccl_chemistry_experiments
session_id: context_continuation_ae12f7be
created_at: 2026-04-06
rom_type: distilled
reliability: High
topics: [ccl-features, chemistry-analogy, structural-formula, tensor3, topology, functional-groups, data-driven, road-B, phase-c-v3, SAM, GCE-L4]
exec_summary: |
  CCL 特徴量の化学的同型を展開・実験・批判。3回の実験 (tensor3, v1, v2) で
  道 B (構造式特徴量) の方向性を確認しつつ、同型の根本的誤り (原子≠演算子) を発見。
  次は §8.2 修正 + データ駆動の官能基発見。SAM/v3 は GCE L4 で並行稼働中。
---

# CCL 化学実験と同型批判 — 道 B v1-v2 + §8 展開

## [DECISION] 原子と結合の定義を修正する

旧 (§8.2 初版): 演算子 (>>, *, |) = 原子。**これは誤り。**
新: **原子 = 意味トークン (fn, #, ¥, .method, pred, CTRL)**。**結合 = 演算子 (>>, *, |, &)**。

理由: 化学の原子は「それ自体で安定に存在できる最小単位」。`>>` は原子と原子を繋ぐ結合であって、それ自体では意味を持たない。

## [DECISION] 官能基はデータ駆動で発見する

§8.8 のテンプレート事前定義は prior への過信 (N-01/B1 違反)。
代わりに:
1. 11768 CCL テキストから全長さ 3-7 の部分列を抽出
2. 出現頻度 ≥ 50 の部分列を候補
3. Recall@k の差で弁別力を検定
4. 弁別力のある部分列 = データ駆動の「官能基」

## [DISCOVERY] 3回の実験結果

### tensor3 (2026-04-05)
- 22d 演繹核 → 453d テンソル積: best R@1=2.8% (49d=6.2% に未達)
- Z-score 前処理で 3次項が復活 (var: 0→974)。R@10 で +4.8pp
- **結論**: テンソル積 = 分子式の複雑化。構造式ではない

### 構造式 v1 (2026-04-06)
- 演算子 n-gram (bigram) + 手設計構造特徴量 (22d)
- 全条件で 49d 劣化: S3=4.4%, S4=4.2%, S5=3.2% (< S0=6.2%)
- **原因**: >> が 43549 回出現し n-gram を支配。次元の呪い
- **結論**: ミクロすぎる特徴量はノイズとして有効信号を希釈

### 構造式 v2 (2026-04-06)
- TF-IDF n-gram + トポロジー特徴量 (26d) + MI 特徴選択
- **S4 (49d+topo=75d) が R@10 で 49d を +4.8pp 超え (29.4%)**
- R@1 は未超え (5.0% vs 6.2%)
- TF-IDF は逆効果 (レア n-gram に過剰フォーカス → 縮退)
- MI proxy 特徴選択も失敗 (TF-IDF の高分散に騙された)
- **結論**: トポロジー特徴量は「群同定」に有効。方向性は正しい

## [DISCOVERY] §8 化学同型の批判的検査結果

| セクション | 判定 | 問題 |
|:----------|:-----|:-----|
| §8.1 素粒子 | ❌ 削除 | カテゴリ誤り。CCL トークンは互いを構成しない |
| §8.2 周期表 | 🔴 書直し | 原子≠演算子。原子=意味トークン、結合=演算子 |
| §8.3 結合 | 🟡 拡張 | 結合エネルギー・配位数・結合角の概念が欠如 |
| §8.4 官能基 | 🔴 方法変更 | 事前定義→データ駆動。9種は出発点としてのみ |
| §8.5 分子特性 | 🟡 深化 | 情報フロー解析が必要。表面的すぎる |
| §8.6 反応 | 🟢 後回し | Phase C (2分子間操作) で初めて必要 |

## [DISCOVERY] Tolmetes の 2 つの核心指摘

1. **粒度**: 現在のトポロジー特徴量はアミノ酸レベル。タンパク質 (機能するモジュール) が必要
2. **特性**: 原子にも分子にも固有の特性がある。特性の概念が完全に欠落していた

## [CONTEXT] GCE L4 の稼働状況

- **Phase C v3**: PID 30886。E1/E2/E4 修正済み。4/8 回収予定 (T-060)
- **SAM Phase 1**: PID 31550。SGD 5seeds のうち 4 完了、最後の seed が進行中。その後 SAM/OA-SAM/反転制御の 15 runs が残る。全体完了は ~4/7 (T-062)
- VRAM 同居: 9GB/23GB で安定

## [CONTEXT] 成果物

- 理論文書: `11_肌理｜Hyphē/chemistry_of_ccl_features.md` (§1-§8)
- 実験スクリプト:
  - `14_忘却｜Lethe/experiments/tensor3_experiment.py`
  - `14_忘却｜Lethe/experiments/structural_formula_experiment.py` (v1)
  - `14_忘却｜Lethe/experiments/structural_formula_v2.py` (v2)
- Pinakas: T-062 (SAM), T-063 (tensor3 FB), T-064~T-068 (別セッション追加)

## 次のアクション

1. §8.2 修正 (原子=意味トークン、結合=演算子)
2. データ駆動の官能基発見スクリプト (頻出部分列 → 弁別力検定)
3. 発見された官能基の特性計算
4. v3 実験スクリプト (1-3 が固まってから)

<!-- ROM_GUIDE
primary_use: CCL 特徴量設計の次セッション継続時。化学同型の現在地と批判結果の把握
retrieval_keywords: CCL features, chemistry analogy, structural formula, functional groups, data-driven, topology, tensor product, 49d, road B, R@1, R@10
expiry: permanent
-->
