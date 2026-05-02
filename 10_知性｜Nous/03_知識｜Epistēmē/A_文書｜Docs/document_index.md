```typos
#prompt hgk-document-index
#syntax: v8
#depth: L2

<:role: HGK ドキュメント目録 (マスターインデックス)。全ドキュメントの所在地図。:>

<:goal: 「どこに何があるか」を1ファイルで俯瞰できる統一インデックスを提供する :>

<:context:
  - [knowledge] 対象: _src/ (ソースコード), 50_外部/, 90_保管庫/, .stversions/, 30_記憶/ (バルク) は除外
  - [knowledge] 生成日: 2026-03-17
  - [knowledge] 合計: 約1060件 (構造的文書のみ)
/context:>
```

# HGK ドキュメント目録 v1.0

> **スコープ**: 構造的文書のみ。ソースコード (`_src/`)、外部OSS (`50_外部/`)、アーカイブ (`90_保管庫/`)、セッション記録 (`30_記憶/`) のバルクデータは除外。
>
> **凡例**: 📐 = 公理/定義、📋 = 手順/WF、📑 = 知識/分析、🗂️ = 企画/計画、🔬 = 実験、🔧 = 運用

---

## 00_核心｜Kernel (101 件)

> **POMDP**: P(s) 不変 — 削除すると体系が瓦解する公理

### 📐 A_公理｜Axioms — 体系の根幹

#### ルートファイル (体系核)

| ファイル | 概要 |
|:---------|:-----|
| `SACRED_TRUTH.md` | 不変真理。全体系の頂点 |
| `system_manifest.md` | 32実体体系 (1+7+24) の一覧 |
| `axiom_hierarchy.md` | 公理階層と座標系の定義 |
| `kalon.md` | 美の操作的定義: Fix(G∘F) 不動点 |
| `constructive_cognition.md` | 構成的認知の理論 |
| `formal_derivation_v4.md` | 体系の形式的導出 v4 |
| `cognitive_axioms.md` | 認知公理の集合 |
| `taxis.md` | 分類理論 (G_{ij} 均衡的結合) |
| `circulation_taxis.md` | 循環分類 (ω_{ij} 非均衡的循環) |
| `circulation_theorem.md` | 循環定理 |
| `trigonon.md` | 三角構造 (bridge/anchor) |
| `aletheia.md` | 真理の随伴的定義 |
| `weak_2_category.md` | 弱2圏構造 |
| `fep_as_natural_transformation.md` | FEP を自然変換として定式化 |
| `L4_helmholtz_bicat_dream.md` | L4 Helmholtz BiCat 構想 |
| `proof_levels.md` | 証明の深度レベル定義 |
| `fep_epistemic_status.md` | FEP の認識論的地位 |
| `linkage_hyphe.md` | Hyphē との接続 |
| `problem_E_m_connection.md` | E-m 接続問題 |

#### A_構成｜Constitution (13 件)

開発憲法。00〜07 の章立て + INTRODUCTION + _index。

| ファイル | 概要 |
|:---------|:-----|
| `_index.md` | 構成の目次 |
| `INTRODUCTION.md` | 憲法序論 |
| `00_orchestration.md` | オーケストレーション原則 |
| `01_environment.md` | 環境設定原則 |
| `02_logic.md` | 論理原則 |
| `03_security.md` | セキュリティ原則 |
| `04_lifecycle.md` | ライフサイクル原則 |
| `05_meta_cognition.md` | メタ認知原則 |
| `06_style.md` | スタイル原則 |
| `07_implementation.md` | 実装原則 |
| `tests/test_suite.md` | テストスイート |

#### B_根拠｜Evidence (6 件)

体系の根拠となる証拠・形式導出。Jules による分析含む。

#### C_知識｜Knowledge (21 件)

FEP 関連論文の消化物 + Doxa (DX-007, DX-008)。

| 主要ファイル | 概要 |
|:-------------|:-----|
| `a-mathematical-walkthrough-...` | FEP の数学的ウォークスルー |
| `an-active-inference-implementation-...` | 能動推論の phototaxis 実装 |
| `deconstructing-deep-active-inference*.md` | Deep Active Inference の分解 (2件) |
| `doxa/DX-007_series_as_attractors/` | Series をアトラクターとして解釈 |
| `doxa/DX-008_multilingual_reasoning/` | 多言語推論パターン |

#### D_メタ｜Meta (16 件)

体系の自己反省的分析。外部レビュー結果含む。

| 主要ファイル | 概要 |
|:-------------|:-----|
| `analysis_prior_preferences_C_*.md` | 事前選好のC分析 |
| `analysis_scale_hierarchy_necessity_*.md` | Scale 階層の必要性分析 |
| `analysis_semidirect_6x1_formal_*.md` | 半直積 6×1 形式的分析 |
| `analysis_valence_formalization_*.md` | Valence 形式化分析 |
| `cognitive_distortion_universality.md` | 認知歪みの普遍性 |
| `cognitive_novelty_analysis.md` | 認知的新規性分析 |
| `completeness_minimality_proof.md` | 完全性・最小性証明 |
| `type_theory_formalization_vision.md` | 型理論形式化ビジョン |
| `external_review_results/` | 外部レビュー結果 (2件) |
| `hgk_review_guide.md` | HGK レビューガイド |

#### E_パターン｜Patterns (2 件)

Peras の収束/発散パターン。

#### F_CEP｜CEP (6 件)

CCL Enhancement Proposals (CEP-000〜CEP-003 + INDEX)。

#### H_混合｜Mixins (7 件)

TYPOS Mixin 定義 (caching, retry, timing, tracing, validation)。

### トップレベルファイル

| ファイル | 概要 |
|:---------|:-----|
| `README.md` | GitHub 向け README (クイックスタート+体系概要) |
| `STRUCTURE.md` | ディレクトリ構造+命名規則 |
| `AGENTS.md` | AI エージェント向けガイド |
| `ARCHITECTURE.md` | システムアーキテクチャ |

---

## 10_知性｜Nous (830 件)

> **POMDP**: μ (内部状態) — 可変 prior, 手順, 知識, 計画

### 01_制約｜Constraints (12 件)

P(s) 可変 — バージョン管理下の行動規範。

| サブ帯 | 件数 | 概要 |
|:-------|-----:|:-----|
| `B_核｜Kernel/` | 3 | Kernel 公理の操作的制約。Constitution INTRODUCTION + 07_implementation |
| `E_CCL｜CCL/` | 8 | CCL 言語仕様: `ccl_language.md`, `operators.md`, `ccl_macro_reference.md`, `wf_classification.md`, `CCL_FREEZE.md` |

### 02_手順｜Procedures (368 件)

P(o|s) — 世界に働きかけるメカニズム。

| サブ帯 | 件数 | 概要 |
|:-------|-----:|:-----|
| `A_手順｜Workflows/` | 44+ | WF 定義: 24動詞 WF + CCL マクロ WF + Peras WF + Domain WF + ユーティリティ (boot, bye, eat, fit, basanos, vet) |
| `B_WFモジュール｜WFModules/` | 119 | WF の構成部品 (Boot, Bou, Zet, Ene, Mek, Dia+ 等 15モジュール) |
| `C_技能｜Skills/` | 167 | 動詞別スキル: V01-V24 + U汎用 + X-series。各 SKILL.md + scripts/ |
| `D_マクロ｜Macros/` | 6 | CCL マクロ定義 |
| `F_雛形｜Templates/` | 10 | テンプレート集 |
| `G_CCL｜CCL/` | 12 | CCL 言語仕様の手続き的側面 |
| `H_基準｜Standards/` | 7 | 品質基準・命名規則 |

### 03_知識｜Epistēmē (192 件)

Q(s|o) — 確定した信念。

| サブ帯 | 件数 | 概要 |
|:-------|-----:|:-----|
| `A_文書｜Docs/` | 23 | 確定分析文書: HGK_BC_Quick_Reference, Session_Lifecycle, System_Structure, Tool_Cheatsheet, WF_Cheatsheet, KERNEL_PRACTICE_GUIDE, doctrine, diffusion_cognition, search_cognition 等 |
| `A_知識項目｜KI/` + `A_知識索引/` | 2 | 知識索引 (v8_syntax_reference, numpy_blob_storage_pattern) |
| `B_知識項目｜KnowledgeItems/` | 123 | KI 集積: filemaker_official_docs, google_antigravity_platform, claude_model_intelligence, clustering_as_constraint 等 |
| `E_美論｜Kalon/` | 37 | Kalon 理論の確定信念: 圏論/群論/FEP/微積分/表現論/力学系 deep examination + doxa |
| ルート散在 | 5 | typos_current_state, gemini_rules_scoping, wf_evaluation_axes 等 |

### 04_企画｜Boulēsis (257 件)

G(π) — まだ実行していない行動方針。

| サブ帯 | 件数 | 概要 |
|:-------|-----:|:-----|
| `00_舵｜Helm/` | 25 | プロジェクト管理ハブ: INDEX, AMBITION, ARSENAL, backlog, vision/, specs/ (IMPL_SPEC_*, UI_REQUIREMENTS, SERVER_ARCHITECTURE) |
| `16_CCL｜CCL/01_意味論｜Semantikē/` | 37 | Semantikē (旧 Kalon) 理論開発: docs/ (8 deep examination) + doxa/ (仮説群) |
| `02_解釈｜Hermeneus/` | 11 | Hermēneus 開発計画 |
| `03_市場｜Agora/` | 63 | 遊学エッセイ・知的活動記録 |
| `04_随伴｜OssAdjoint/` | 32 | OSS 随伴戦略 |
| `05_自律｜Autophonos/` | 3 | 自律研究プログラム |
| `06_信念｜Doxa/` | 23 | 仮説・信念 |
| `07_行為可能性｜Euporia/` | 5 | 行為可能性分析 |
| `08_形式導出｜FormalDerivation/` | 1 | 形式導出プロジェクト |
| `09_能動｜Ergon/` | 15 | 能動的プロジェクト |
| `10_統合｜GWSIntegration/` | 5 | Google Workspace 統合 |
| `11_肌理｜Hyphē/` | 7 | Hyphē 理論基盤 (CKDF/chunk公理/NP回避) |
| `12_遊学｜Yugaku/` | 33 | 遊学エッセイシリーズ |

---

## 20_機構｜Mekhane (19 件 docs)

> **POMDP**: a (action) — コードの設計文書。ソースコードは `_src/` に配置 (本目録対象外)。

| 帯 | 概要 |
|:---|:-----|
| `00_概要｜Overview/` | アーキテクチャ全体図 |
| `01_MCP｜MCP/` | MCP サーバー設計 |
| `02_車体｜Ochema/` | Language Server ブリッジ |
| `03_解釈｜Hermeneus/` | CCL パーサー/実行エンジン |
| `04_共感｜Sympatheia/` | 自律神経系 |
| `05_樹｜Dendron/` | PROOF 存在証明チェッカー |
| `06_観察｜Periskope/` | Deep Research エンジン |
| `07_試金石｜Basanos/` | MCP Gateway |
| `08_最適化｜Aristos/` | GA 最適化 (未実装) |
| `09_編組｜Symploke/` | Boot 統合 (15軸) |
| `10_想起｜Anamnesis/` | 記憶 (LanceDB) |
| `11_完遂｜Synteleia/` | 6視点アンサンブル |
| `12_制作｜Poiema/` | 成果物生成 |
| `13_FEP｜FEP/` | FEP エンジン |
| `14_分類｜Taxis/` | 分類・射の提案 |
| `15_HGK｜HGK/` | Tauri デスクトップアプリ |
| `16_消化｜Pepsis/` | 設計哲学消化 |
| `17_協調｜Synergeia/` | マルチエージェント |

---

## 40_作品｜Poiema (2 件)

> **FEP**: 能動推論の行為 (a) が産む成果物。

| ファイル | 概要 |
|:---------|:-----|
| `README.md` | プロジェクト索引ポータル (HGK, Synergeia, Pepsis, Aristos, Bytebot, Hyphē) |
| `README_organon.md` | Organon ツールキット参照 |

---

## 60_実験｜Peira (89 件)

> **EFE**: epistemic value — 不確実性を能動的に減らす実験群。

| サブ帯 | 件数 | 概要 |
|:-------|-----:|:-----|
| `00_汎用｜General/` | 50+ | ベンチマーク, PoC, 遊学エッセイ草稿 (doxa/agora/ に E1-E9) |
| `01_検証｜Verification/` | 1 | 体系整合性チェック |
| `02_テスト｜Tests/` | 1 | 自動化テスト |
| `03_リモート｜Remote/` | 3 | リモート環境 (GPU, LS) |
| `04_知覚PoC｜PerceptionPoc/` | 1 | OmniParser/WindowsAgent PoC |
| `05_スペクトル解析/` | 3 | Fisher 情報量/VFE 理論検証 |
| `06_Hyphē実験/` | 4 | Hyphē チャンカー PoC + 分析 |
| `07_非平衡認知実験/` | 1 | 非平衡認知 |
| `08_関手忠実性/` | 19 | D4 関手忠実性検証 (EXPERIMENT_DESIGN, TRANSFORMER_EDUCATION, gold_standard, corpus/) |

---

## 80_運用｜Ops (19 件)

> **EFE**: H (恒常性) — システムを安定状態に保つ。

| サブ帯 | 件数 | 概要 |
|:-------|-----:|:-----|
| `00_スクリプト｜Scripts/` | 2 | 自動化スクリプト README + PROOF |
| `01_開発ツール｜Devtools/` | 1 | 開発ツール README |
| `04_配備｜Deploy/` | 7 | systemd/K8s/Docker + 行動仕様分析 (Anthropic ComputerUse, Mariner, Operator) |
| `05_設定｜Config/` | 1 | 設定管理 README |
| `06_文書｜Docs/` | 8 | 運用手順: hgk-zero-setup, git-multi-machine, Periskopē運用 (README, depth_mapping, templates) |

---

## 除外対象 (参考)

| ディレクトリ | 除外理由 | 推定件数 |
|:-------------|:---------|:---------|
| `30_記憶｜Mneme/` | セッション記録・handoff・ROM 等のバルクデータ | ~3750 |
| `_src｜ソースコード/` | ソースコード (.py/.ts/.rs) | 多数 |
| `50_外部｜External/` | 外部 OSS フォーク | 多数 |
| `90_保管庫｜Archive/` | 廃止された旧体系ファイル | 多数 |
| `.stversions/` | Syncthing バージョン管理 | ~6350 |

---

## クロスリファレンス: 既存インデックス系ファイルとの関係

| ファイル | 本目録との関係 |
|:---------|:---------------|
| [STRUCTURE.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/00_核心｜Kernel/STRUCTURE.md) | 本目録の上位互換。STRUCTURE はディレクトリ構造+命名規則、本目録は全ファイルの所在 |
| [INDEX.md (Helm)](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/INDEX.md) | 機能 × 文書のクロスリファレンス。本目録はパス順、あちらは機能順 |
| [comprehensive_catalog.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/mcp/hegemonikon_core_system/artifacts/workflows/comprehensive_catalog.md) | WF カタログ。本目録の `02_手順` セクションの WF 部分と対応 |
| 各 `README.md` (10件) | 各ディレクトリの POMDP 分類。本目録は横断的にファイルを列挙 |

---

*HGK Document Index v1.0 — 2026-03-17*
*スコープ: 構造的文書 約1060件 (除外: _src, 50_外部, 90_保管庫, 30_記憶バルク, .stversions)*
