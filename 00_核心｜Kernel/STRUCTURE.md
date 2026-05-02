# Hegemonikón 構造図 (STRUCTURE.md) v5.0

> **目的**: Hegemonikón の全体像を把握するための地図
> **体系**: PARA v5.0 — FEP カテゴリ対応の番号化ディレクトリ
> **更新日**: 2026-03-11

---

## 命名規則

```
NN_日本語名｜EnglishName/
│
├── NN = 番号 (00-92)  … 認知的負荷を下げるソート
├── 日本語名           … Creator 向け意味 (L2)
├── ｜                 … 全角パイプ (区切り)
└── EnglishName        … 英語名 (L3: grep/import 用)
```

**例外**: `_src｜ソースコード/` — Python import 互換のためアンダースコア接頭辞。番号不可。

---

## トップレベル構造

```
01_ヘゲモニコン｜Hegemonikon/
├── 00_核心｜Kernel/          # 公理・定理・不変真理
├── 10_知性｜Nous/            # 制約・手順・知識・企画・素材
├── 20_機構｜Mekhane/         # 実装コード + モジュール別ドキュメント
├── 30_記憶｜Mneme/           # 記憶・引き継ぎ・セッション履歴・論文DB
├── 40_作品｜Poiema/          # HGK 産出物（自作アプリケーション）
├── 50_外部｜External/        # 外部 OSS 依存（git submodule）
├── 60_実験｜Peira/           # 実験・プロトタイプ・検証
├── 80_運用｜Ops/             # スクリプト・開発ツール・配備
└── 90_保管庫｜Archive/       # アーカイブ
```

---

## 詳細構造

### 00_核心｜Kernel — 不変の公理体系

| ファイル | 内容 |
|:---------|:-----|
| ARCHITECTURE.md | 技術構造の全体像 |
| STRUCTURE.md | 本文書 |
| README.md | 32実体体系と設計思想 |
| PROOF.md | 存在証明 |
| AGENTS.md | AI エージェント向けガイド |
| LICENSE | MIT |

---

### 10_知性｜Nous — AI 制御層

```
10_知性｜Nous/
├── 01_制約｜Constraints/         # 行動制約 (Kernel, Hóros, CCL, Standards)
├── 02_手順｜Procedures/          # WF・スキル・CCL マクロ・テンプレート
├── 03_知識｜Epistēmē/           # 知識定義 (Docs, KI, Kalon)
├── 04_企画｜Boulēsis/            # プロジェクト企画 (Helm + サブPJ)
├── 05_素材｜Hylē/               # 素材・データ・テンプレート
└── 09_保管｜Archeia/             # Nous 内アーカイブ
```

#### 04_企画｜Boulēsis 配下

```
04_企画｜Boulēsis/
├── 00_舵｜Helm/                  # プロジェクト管理ハブ (registry, vision)
├── 16_CCL｜CCL/01_意味論｜Semantikē/ # CCL 圏論的意味論 (旧 01_美論｜Kalon)
├── 02_解釈｜Hermeneus/           # CCL コンパイラ開発フェーズ
├── 03_市場｜Agora/               # FM連携・フリーランス
├── 04_随伴｜OssAdjoint/          # OSS 随伴関手マッピング
├── 05_自律｜Autophonos/          # 自律提案システム
├── 06_信念｜Doxa/                # 研究ジャーナル (DX-nnn)
├── 09_能動｜Ergon/               # 能動的推論
├── 10_統合｜GWSIntegration/      # GWS 統合
└── 11_肌理｜Hyphē/              # Hyphē 理論基盤 (CKDF/chunk公理)
```

---

### 20_機構｜Mekhane — 実行基盤

```
20_機構｜Mekhane/
├── _src｜ソースコード/           # ★ Python パッケージ実体
│   ├── mekhane/                  #   コア (27 modules)
│   ├── hermeneus/                #   CCL コンパイラ
│   └── tests/                    #   テスト
│
│  【モジュール別ドキュメント — コードと 1:1 対応】
├── 00_概要｜Overview/            # アーキテクチャ全体図
├── 01_MCP｜MCP/                  # MCP サーバー群 (8 server)
├── 02_車体｜Ochema/              # Language Server
├── 03_解釈｜Hermeneus/           # CCL コンパイラ設計・仕様
├── 04_共感｜Sympatheia/          # 自律神経系
├── 05_樹｜Dendron/               # 存在証明
├── 06_観察｜Periskope/           # 研究エンジン
├── 07_試金石｜Basanos/           # 品質評議
├── 08_最適化｜Aristos/           # ルーティング最適化
├── 09_編組｜Symploke/            # 統合 (/boot 等)
├── 10_想起｜Anamnesis/           # 記憶・検索
├── 11_完遂｜Synteleia/           # 完了処理
├── 12_制作｜Poiema/              # 出力生成
├── 13_FEP｜FEP/                  # 自由エネルギー原理エンジン
└── 14_分類｜Taxis/               # 分類
```

> **設計原則**: ドキュメントは番号ディレクトリ、コードは `_src/`。
> 「Dendron のドキュメントはどこ？」→ `05_樹｜Dendron/`。考える余地なし。

---

### 30_記憶｜Mneme — 長期記憶

```
30_記憶｜Mneme/
├── 01_記録｜Records/             # セッション履歴・Handoff・成果物
│   ├── a_引継｜handoff/           #   セッション引き継ぎ
│   ├── b_対話_sessions/          #   対話ログ
│   ├── c_ROM｜rom/               #   ROM (コンテキスト蒸留)
│   ├── d_成果｜artifacts/        #   出力成果物
│   ├── f_ログ｜logs/             #   実行ログ
│   └── g_実行痕跡｜traces/       #   実行トレース
│
├── 02_索引｜Index/               # ベクトル索引 (pkl)
├── 03_素材｜Materials/           # WF 出力・素材
├── 04_知識｜Gnosis/              # 論文DB・学術データ
│   ├── 00_知識基盤｜KnowledgeBase/  # LanceDB
│   ├── 01_文献｜Literature/         # 論文・記事
│   ├── 02_プロンプト｜Prompts/      # テンプレート
│   └── 03_記録｜Records/            # 研究記録
│
└── 05_状態｜State/               # ランタイム状態・セッション
    ├── A_違反｜Violations/       #   BC 違反ログ
    ├── B_キャッシュ｜Cache/      #   キャッシュ
    ├── C_ログ｜Logs/             #   サービスログ
    ├── F_セッション｜Sessions/   #   セッション状態
    ├── F_ランタイム｜Runtime/    #   ランタイム状態
    ├── G_合成ログ｜SynteleiaLogs/ # 合成ログ
    └── H_ワークフロー｜Workflows/ # WF 状態
```

---

### 40_作品｜Poiema — HGK 産出物

```
40_作品｜Poiema/
└── (HGK 自作アプリケーション)
```

> **注**: コード実体は `20_機構/_src/` に集約。
> hgk (デスクトップ UI), synergeia (マルチエージェント), pepsis (消化) 等。
> 40_作品/ にはドキュメント・設計文書を配置する。

---

### 50_外部｜External — 外部 OSS

```
50_外部｜External/
├── Bytebot/                      # デスクトップ自動化 (外部 OSS)
└── openclaw/                     # ドキュメント生成 (外部 OSS)
```

> **区別**: HGK の産出物 (40_作品) と外部依存 (50_外部) は MECE 分離。

---

### 60_実験｜Peira — 実験・テスト

```
60_実験｜Peira/
├── 00_汎用｜General/            # 汎用実験
├── 01_検証｜Verification/       # 検証
├── 02_テスト｜Tests/            # テストデータ
├── 03_リモート｜Remote/         # リモート関連
├── 04_知覚PoC｜PerceptionPoc/   # 知覚 PoC
├── 05_スペクトル解析｜SloppySpectrum/ # スペクトル解析
└── 50_自律研究｜Autoresearch/   # 自律研究
```

---

### 80_運用｜Ops — 運用・スクリプト

```
80_運用｜Ops/
├── _src｜ソースコード/           # スクリプト実体
├── 00_スクリプト｜Scripts/       # 運用スクリプト
├── 01_開発ツール｜Devtools/      # 開発ツール
├── 04_配備｜Deploy/              # デプロイ構成
├── 05_設定｜Config/              # 設定ファイル
└── 06_文書｜Docs/                # 運用ドキュメント
```

---

### 90_保管庫｜Archive — アーカイブ

```
90_保管庫｜Archive/
├── 00_スクリプト｜Scripts/       # 旧スクリプト
├── 01_設計｜Designs/             # 旧設計文書
├── 02_アセット｜Assets/          # 旧アセット
├── 03_テキストミラー｜TextMirror/ # テキストミラー
├── 05_出力｜Output/              # 過去の出力
├── 06_スキル｜Skills/            # 旧スキル
├── 07_ワークフロー｜Workflows/   # 旧ワークフロー
├── 20_Mekhane_legacy/            # Mekhane 旧構造
├── 30_Mneme_Archive/             # Mneme 旧アーカイブ
├── 30_Records_legacy/            # Records 旧構造
├── 80_Infrastructure/            # 旧インフラ
├── A_旧規則｜ArchivedRules/      # 旧ルール
├── B_旧技能｜SkillsArchive/      # 旧技能
├── C_旧手順｜WorkflowsArchive/   # 旧手順
└── D_旧公理構造｜AxiomsLegacy/   # 旧公理構造
```

---

## FEP カテゴリ対応

| # | ディレクトリ | FEP 段階 | カテゴリ論的役割 |
|:--|:------------|:---------|:----------------|
| 00 | Kernel | μ (内部モデル) | 終対象 — 不変の公理 |
| 10 | Nous | π (policy) | 関手 — 記憶を行動に変換 |
| 20 | Mekhane | α (action) | 射 — 計算の実行 |
| 30 | Mneme | o (observation) | 対象 — 記憶の構造 |
| 40 | Poiema | ε (effector) | 余射 — 外部への出力 |
| 50 | External | s (sensory) | 余対象 — 外部からの入力 |
| 60 | Peira | γ (generative) | 自然変換 — 仮説検証 |
| 80 | Ops | — | 補助 — インフラ |
| 90 | Archive | — | 補助 — 保管 |

---

*Hegemonikón STRUCTURE v5.0 — MECE 対応 (2026-03-11)*
