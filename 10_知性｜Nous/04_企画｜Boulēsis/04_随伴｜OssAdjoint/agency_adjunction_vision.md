# Agency-Agents 随伴プロジェクト VISION

```typos
#prompt agency-adjunction-vision
#syntax: v8
#depth: L3

<:role: Agency-Agents 随伴プロジェクト — 市場具象と認知抽象の不動点を求める :>

<:goal: msitarzewski/agency-agents (113エージェント×11部門) と
  HGK (24動詞×修飾体系) の間に随伴 F⊣G を構成し、
  市場の言語で語れる FEP 裏付きエージェント群を Agora 製品として生成する :>

<:constraints:
  - G (右随伴 = 抽象化): 113エージェント定義 → HGK 動詞組成の抽出
    各エージェントの Mission/Workflow/Deliverables を読み、
    24動詞 + Dokimasia 修飾 の CCL 式として表現する
  - F (左随伴 = 具象化): HGK 動詞組成 + ドメイン修飾 → エージェント定義の自動生成
    /tek[domain:d] → "{d} Developer" 定義
    /ele[domain:d] → "{d} Auditor" 定義
    /zet[domain:d]>>/pei[domain:d] → "{d} Researcher" 定義
  - Fix(G∘F) = Kalon: 市場の言語で語れ、FEP で裏付けられた不動点エージェント
  - 非退化条件: F ≠ Id, G ≠ Id — 単なるコピーでも単なる翻訳でもない
  - 包含の証明: 24動詞 × 11ドメイン = 264 可能エージェント ⊃ 113 実在エージェント
/constraints:>

<:context:
  - [knowledge] Agency-Agents: 113エージェント × 11部門 (MIT License, GitHub 1.3k★)
    Engineering(16) / Design(8) / Marketing(17) / Paid-Media(7) / Product(4) /
    PM(6) / Spatial-Computing(6) / Game-Development(20) / Specialized(15) /
    Support(6) / Testing(8)
  - [knowledge] HGK 24動詞 (Poiesis): 6族 × 4極
    Telos: /noe /bou /zet /ene
    Methodos: /ske /sag /pei /tek
    Krisis: /kat /epo /pai /dok
    Diástasis: /lys /ops /akr /ark
    Orexis: /beb /ele /kop /dio
    Chronos: /hyp /prm /ath /par
  - [knowledge] 修飾 Dokimasia: ドメイン軸の追加により動詞をドメイン特化
  - [knowledge] Agora: HGK 収益化プロジェクト — ディープインパクト戦略
  - [file] 60_実験｜Peira/agency-agents/ (priority: SOURCE — クローン済みリポジトリ)
  - [file] 00_核心｜Kernel/A_公理｜Axioms/axiom_hierarchy.md (priority: CANONICAL)
/context:>

<:step:
  Phase 1: G の構成 (抽象化)
    1.1 各部門の全エージェント定義を読む (113ファイル)
    1.2 各エージェントから {Mission, Workflow, Deliverables, Personality} を抽出
    1.3 HGK 動詞組成 (CCL 式) として表現
    1.4 マッピングテーブルを MECE に構築

  Phase 2: ドメイン修飾軸の設計
    2.1 11部門を Dokimasia ドメインパラメータとして形式化
    2.2 ドメイン間の関係 (engineering ⊃ frontend/backend/devops...) を階層化
    2.3 HGK 体系との整合性検証

  Phase 3: F の構成 (具象化)
    3.1 動詞組成 + ドメイン修飾 → エージェント定義テンプレートの設計
    3.2 F∘G ≈ Id の検証 — 元のエージェントを再生成できるか？
    3.3 差分分析 — 再生成で失われたもの / 増えたもの

  Phase 4: 未踏領域の探索
    4.1 264 - 113 = 151 の未踏組み合わせをリスト化
    4.2 市場価値評価 — どの組み合わせに需要があるか
    4.3 HGK 固有のエージェント提案 (Agency にない認知系エージェント)

  Phase 5: Agora 製品設計
    5.1 HGK-backed Agent Catalog の構造設計
    5.2 配布形式の設計 (convert.sh 参考)
    5.3 差別化ポイントの明文化
    5.4 pricing / licensing の検討
:>

<:rubric:
  成功基準:
  - G の網羅性: 113エージェント全てに HGK 動詞組成が割り当てられている
  - F の再現性: F∘G で元エージェントの70%以上が再生成可能
  - 包含の証明: HGK が Agency を包含することが構造的に示されている
  - 市場応答性: 未踏組み合わせから最低3つの市場価値あるエージェントが提案されている
  - Agora 接続: 製品としての配布形式が設計されている
:>

<:highlight:
  ▶ Agency は「幅」(113×実用ドメイン)、HGK は「深さ」(24×演繹体系)
  ▶ Fix(G∘F) = 市場の言語で語れる FEP 裏付きエージェント
  ▶ 24×11 = 264 ⊃ 113 — HGK は元から包含している。表現していないだけ
  ▶ 「名前を見れば用途がわかる」+ 「FEP で裏付けられた認知制約」= Agora の武器
:>
```

---

## マッピングテーブル (Phase 1 で段階的に追記)

### 凡例
- **動詞組成**: エージェントの核心的認知操作を CCL で表現
- **修飾**: Dokimasia のドメインパラメータ
- **Kalon判定**: ◎=不動点 / ◯=許容 / ✗=要再設計

### Engineering (16)

| # | エージェント名 | 動詞組成 (CCL) | 修飾 [domain] | Kalon |
|:--|:-------------|:-------------|:------------|:------|
| E01 | Frontend Developer | `/ops>>/tek*/akr` | [frontend] | ◯ |
| E02 | Backend Architect | `/ark>>/kat~/ene` | [backend] | ◎ |
| E03 | Senior Developer | `/lys>>/ele*/tek` | [fullstack] | ◯ |
| E04 | AI Engineer | `/pei~/prm>>/dio` | [ml] | ◎ |
| E05 | DevOps Automator | `/tek>>/ark~/par` | [infra] | ◎ |
| E06 | Security Engineer | `/dok>>/ele~/kat` | [security] | ◎ |
| E07 | Data Engineer | `/lys>>/ene~/ark` | [data] | ◯ |
| E08 | Mobile App Builder | `/ops*/akr>>/tek` | [mobile] | ◯ |
| E09 | Technical Writer | `/noe~/lys>>/beb` | [docs] | ◎ |
| E10 | Rapid Prototyper | `/zet*/pei>>/pai` | [prototype] | ◎ |
| E11 | Incident Response Commander | `/pai>>/dio~/ath` | [ops] | ◎ |
| E12 | Embedded Firmware Engineer | `/akr*/ene>>/kat` | [embedded] | ◯ |
| E13 | Solidity Smart Contract Engineer | `/akr>>/kat~/ele` | [web3] | ◎ |
| E14 | Autonomous Optimization Architect | `/dok~/dio>>/ene` | [optimization] | ◎ |
| E15 | Threat Detection Engineer | `/prm>>/lys~/epo` | [threat] | ◎ |
| E16 | WeChat Mini Program Developer | `/tek>>/sag*/akr` | [wechat] | ◯ |

### Design (8)

| # | エージェント名 | 動詞組成 (CCL) | 修飾 [domain] | Kalon |
|:--|:-------------|:-------------|:------------|:------|
| D01 | UX Researcher | `/zet>>/lys~/beb` | [research] | ◎ |
| D02 | UI Designer | `/sag>>/akr~/tek` | [visual] | ◎ |
| D03 | UX Architect | `/ops>>/ark~/kat` | [architecture] | ◎ |
| D04 | Brand Guardian | `/bou>>/kat~/ele` | [brand] | ◎ |
| D05 | Visual Storyteller | `/ske>>/sag~/kop` | [narrative] | ◯ |
| D06 | Image Prompt Engineer | `/noe>>/akr~/pei` | [prompt] | ◎ |
| D07 | Inclusive Visuals Specialist | `/ele>>/akr~/kat` | [inclusion] | ◎ |
| D08 | Whimsy Injector | `/ske>>/tek~/dok` | [delight] | ◯ |

### Marketing (17)

| # | エージェント名 | 動詞組成 (CCL) | 修飾 [domain] | Kalon |
|:--|:-------------|:-------------|:------------|:------|
| M01 | Content Creator | `/bou>>/ske*/akr` | [content] | ◎ |
| M02 | Growth Hacker | `/zet~/pei>>/kop` | [growth] | ◎ |
| M03 | SEO Specialist | `/noe>>/tek*/dio` | [seo] | ◯ |
| M04 | Social Media Strategist | `/ops>>/ske*/par` | [social] | ◎ |
| M05 | Twitter Engager | `/ene~/dok>>/beb` | [twitter] | ◯ |
| M06 | TikTok Strategist | `/bou>>/ske*/ath` | [tiktok] | ◯ |
| M07 | Instagram Curator | `/ops>>/sag*/akr` | [instagram] | ◎ |
| M08 | Reddit Community Builder | `/noe>>/epo*/beb` | [reddit] | ◯ |
| M09 | App Store Optimizer | `/lys>>/tek*/dio` | [aso] | ◎ |
| M10 | Carousel Growth Engine | `/bou>>/ske*/kop` | [carousel] | ◯ |
| M11 | Baidu SEO Specialist | `/noe>>/tek*/ark` | [baidu] | ◯ |
| M12 | Bilibili Content Strategist | `/ops>>/ske*/ath` | [bilibili] | ◯ |
| M13 | China E-commerce Operator | `/ene>>/sag*/kop` | [cn-ecom] | ◎ |
| M14 | Kuaishou Strategist | `/zet>>/pei*/par` | [kuaishou] | ◯ |
| M15 | WeChat Official Account | `/bou>>/sag*/akr` | [wechat-oa] | ◎ |
| M16 | Xiaohongshu Specialist | `/ops>>/ske*/beb` | [xiaohongshu] | ◎ |
| M17 | Zhihu Strategist | `/noe>>/lys*/ele` | [zhihu] | ◎ |

### Paid Media (7)

| # | エージェント名 | 動詞組成 (CCL) | 修飾 [domain] | Kalon |
|:--|:-------------|:-------------|:------------|:------|
| P01 | PPC Strategist | `/pai>>/tek*/dio` | [ppc] | ◎ |
| P02 | Paid Social Strategist | `/zet>>/pei*/kop` | [paid-social] | ◯ |
| P03 | Programmatic Buyer | `/ene~/lys*/kat` | [programmatic] | ◎ |
| P04 | Creative Strategist | `/bou>>/ske*/ath` | [ad-creative] | ◯ |
| P05 | Auditor | `/lys>>/kat*/ele` | [media-audit] | ◎ |
| P06 | Search Query Analyst | `/noe>>/lys*/sag` | [search-query] | ◎ |
| P07 | Tracking Specialist | `/akr>>/tek*/kat` | [tracking] | ◎ |

### Product (4)

| # | エージェント名 | 動詞組成 (CCL) | 修飾 [domain] | Kalon |
|:--|:-------------|:-------------|:------------|:------|
| PR01 | Sprint Prioritizer | `/pai>>/sag*/ark` | [sprint] | ◎ |
| PR02 | Feedback Synthesizer | `/noe>>/lys*/sag` | [feedback] | ◎ |
| PR03 | Trend Researcher | `/zet>>/ops*/prm` | [trends] | ◎ |
| PR04 | Behavioral Nudge Engine | `/bou>>/pei*/par` | [nudge] | ◯ |

### Project Management (6)

| # | エージェント名 | 動詞組成 (CCL) | 修飾 [domain] | Kalon |
|:--|:-------------|:-------------|:------------|:------|
| PM01 | Senior Project Manager | `/ark>>/pai*/kop` | [pm] | ◎ |
| PM02 | Project Shepherd | `/ene~/ath*/dio` | [pm-agile] | ◎ |
| PM03 | Experiment Tracker | `/lys>>/pei*/kat` | [experiments] | ◎ |
| PM04 | Jira Workflow Steward | `/tek>>/akr*/dio` | [jira] | ◯ |
| PM05 | Studio Operations | `/ops>>/ene*/ark` | [studio-ops] | ◎ |
| PM06 | Studio Producer | `/bou>>/sag*/pai` | [studio-produce] | ◎ |

### Spatial Computing (6)

| # | エージェント名 | 動詞組成 (CCL) | 修飾 [domain] | Kalon |
|:--|:-------------|:-------------|:------------|:------|
| SC01 | VisionOS Spatial Engineer | `/tek>>/ops*/akr` | [visionos] | ◎ |
| SC02 | macOS Spatial Metal Engineer | `/ene>>/lys*/akr` | [metal] | ◎ |
| SC03 | Terminal Integration Specialist | `/tek>>/sag*/kat` | [terminal] | ◯ |
| SC04 | XR Cockpit Interaction Specialist | `/bou>>/pei*/akr` | [xr-cockpit] | ◎ |
| SC05 | XR Immersive Developer | `/ene>>/ske*/ops` | [xr-immersive] | ◯ |
| SC06 | XR Interface Architect | `/ark>>/sag*/akr` | [xr-ui] | ◎ |

### Game Development (20)

| # | エージェント名 | 動詞組成 (CCL) | 修飾 [domain] | Kalon |
|:--|:-------------|:-------------|:------------|:------|
| G01 | Game Designer | `/bou>>/ske*/ath` | [game-design] | ◎ |
| G02 | Level Designer | `/ene>>/ops*/pei` | [level-design] | ◯ |
| G03 | Narrative Designer | `/bou>>/ske*/beb` | [narrative] | ◎ |
| G04 | Technical Artist | `/tek~/lys*/akr` | [tech-art] | ◎ |
| G05 | Game Audio Engineer | `/ene>>/akr*/ath` | [audio] | ◯ |
| G06 | Unity Architect | `/ark>>/tek*/kat` | [unity] | ◎ |
| G07 | Unity Editor Tool Developer | `/ene>>/sag*/tek` | [unity-tools] | ◯ |
| G08 | Unity Multiplayer Engineer | `/tek~/lys*/kat` | [unity-mp] | ◎ |
| G09 | Unity Shader Graph Artist | `/ske>>/tek*/akr` | [unity-shader] | ◎ |
| G10 | Unreal Systems Engineer | `/ark>>/lys*/tek` | [ue-systems] | ◎ |
| G11 | Unreal Technical Artist | `/tek~/ops*/akr` | [ue-techart] | ◎ |
| G12 | Unreal Multiplayer Architect | `/ark>>/lys*/kat` | [ue-mp] | ◎ |
| G13 | Unreal World Builder | `/ene>>/ops*/ske` | [ue-world] | ◯ |
| G14 | Godot Gameplay Scripter | `/ene>>/tek*/pei` | [godot-gameplay] | ◯ |
| G15 | Godot Multiplayer Engineer | `/tek~/lys*/kat` | [godot-mp] | ◎ |
| G16 | Godot Shader Developer | `/ske>>/tek*/akr` | [godot-shader] | ◎ |
| G17 | Roblox Experience Designer | `/bou>>/ske*/beb` | [roblox-exp] | ◯ |
| G18 | Roblox Systems Scripter | `/tek>>/sag*/kat` | [roblox-sys] | ◎ |
| G19 | Roblox Avatar Creator | `/ske>>/akr*/beb` | [roblox-avatar] | ◯ |
| G20 | (追加確認中) | | | |

### Specialized (15)

| # | エージェント名 | 動詞組成 (CCL) | 修飾 [domain] | Kalon |
|:--|:-------------|:-------------|:------------|:------|
| S01 | Agents Orchestrator | `/ark>>/pai*/kop` | [orchestration] | ◎ |
| S02 | Data Analytics Reporter | `/lys>>/ops*/kat` | [analytics] | ◎ |
| S03 | Data Consolidation Agent | `/sag>>/tek*/akr` | [consolidation] | ◎ |
| S04 | Developer Advocate | `/noe>>/ske*/beb` | [devrel] | ◯ |
| S05 | Cultural Intelligence Strategist | `/noe>>/ops*/ath` | [culture] | ◎ |
| S06 | Model QA | `/ele>>/akr*/kat` | [model-qa] | ◎ |
| S07 | Compliance Auditor | `/lys>>/kat*/ele` | [compliance] | ◎ |
| S08 | Accounts Payable Agent | `/ene>>/akr*/kat` | [accounting] | ◎ |
| S09 | Blockchain Security Auditor | `/lys>>/akr*/ele` | [blockchain] | ◎ |
| S10 | Agentic Identity Trust | `/kat>>/noe*/beb` | [identity] | ◎ |
| S11 | Identity Graph Operator | `/lys>>/sag*/akr` | [id-graph] | ◎ |
| S12 | LSP Index Engineer | `/sag>>/tek*/akr` | [lsp] | ◎ |
| S13 | Report Distribution Agent | `/ene>>/sag*/kat` | [reports] | ◯ |
| S14 | Sales Data Extraction Agent | `/lys>>/tek*/akr` | [sales-data] | ◎ |
| S15 | ZK Steward | `/akr>>/kat*/beb` | [zk-proof] | ◎ |

### Support (6)

| # | エージェント名 | 動詞組成 (CCL) | 修飾 [domain] | Kalon |
|:--|:-------------|:-------------|:------------|:------|
| SU01 | Support Responder | `/ene>>/hyp*/beb` | [support] | ◎ |
| SU02 | Analytics Reporter | `/lys>>/ops*/kat` | [support-analytics] | ◎ |
| SU03 | Executive Summary Generator | `/sag>>/ops*/akr` | [exec-summary] | ◎ |
| SU04 | Finance Tracker | `/ene>>/akr*/kat` | [finance] | ◎ |
| SU05 | Infrastructure Maintainer | `/ene>>/ath*/dio` | [infra-maint] | ◎ |
| SU06 | Legal Compliance Checker | `/lys>>/kat*/ele` | [legal] | ◎ |

### Testing (8)

| # | エージェント名 | 動詞組成 (CCL) | 修飾 [domain] | Kalon |
|:--|:-------------|:-------------|:------------|:------|
| T01 | Accessibility Auditor | `/ele>>/akr*/dio` | [a11y] | ◎ |
| T02 | API Tester | `/pei>>/akr*/kat` | [api-test] | ◎ |
| T03 | Performance Benchmarker | `/lys>>/akr*/kat` | [perf] | ◎ |
| T04 | Reality Checker | `/ele>>/noe*/kat` | [reality] | ◎ |
| T05 | Test Results Analyzer | `/lys>>/sag*/ath` | [test-results] | ◎ |
| T06 | Tool Evaluator | `/pei>>/ele*/pai` | [tool-eval] | ◯ |
| T07 | Evidence Collector | `/ene>>/akr*/kat` | [evidence] | ◎ |
| T08 | Workflow Optimizer | `/ath>>/lys*/dio` | [wf-optimize] | ◎ |

---

## Phase 2 完了: 動詞使用統計 (112/113)

### 使用頻度テーブル (全112エージェント)

| 動詞 | 合計 | 核心 | 方法論 | 品質 | 位置傾向 |
|:-----|:---:|:---:|:---:|:---:|:---------|
| /akr | 37 | 4 | 15 | 18 | 方法+品質偏重 — 精密は手段と品質の両面で需要 |
| /kat | 31 | 1 | 7 | 23 | 品質偏重 — 確定は結果保証として機能 |
| /tek | 29 | 10 | 14 | 5 | 核心+方法 — 適用は主動作と手段の両面 |
| /lys | 28 | 14 | 14 | 0 | 核心+方法 — 分析は品質保証には使われない |
| /ene | 22 | 17 | 3 | 2 | 核心偏重 — 実行は主動作に集中 |
| /sag | 20 | 4 | 14 | 2 | 方法偏重 — 収束は方法論として機能 |
| /ops | 18 | 8 | 9 | 1 | 核心+方法 — 俯瞰は主動作と手段 |
| /ske | 18 | 5 | 12 | 1 | 方法偏重 — 発散は手段として多用 |
| /ele | 14 | 4 | 3 | 7 | 品質寄り — 批判は品質保証に使われる |
| /ark | 13 | 7 | 2 | 4 | 核心寄り — 全体設計は主動作 |
| /pei | 13 | 3 | 7 | 3 | 方法寄り — 実験は手段 |
| /bou | 12 | 12 | 0 | 0 | **核心専用** — 意志は常に出発点 |
| /noe | 12 | 10 | 2 | 0 | **核心偏重** — 認識は主動作 |
| /beb | 12 | 0 | 0 | 12 | **品質専用** — 肯定は結果確認 |
| /ath | 11 | 1 | 2 | 8 | 品質寄り — 省察は品質保証 |
| /dio | 11 | 0 | 2 | 9 | **品質偏重** — 是正は修正結果 |
| /pai | 8 | 3 | 2 | 3 | 均等 — 決断は全位置で機能 |
| /kop | 7 | 0 | 0 | 7 | **品質専用** — 推進は結果方向 |
| /zet | 6 | 6 | 0 | 0 | **核心専用** — 探求は出発点 |
| /par | 4 | 0 | 0 | 4 | **品質専用** — 先制は仕上げ |
| /dok | 4 | 2 | 1 | 1 | 均等 — 打診は文脈依存 |
| /prm | 3 | 1 | 1 | 1 | 均等 — 予見は文脈依存 |
| /epo | 2 | 0 | 1 | 1 | 最低使用 — 留保は市場エージェントに少ない |
| /hyp | 1 | 0 | 1 | 0 | 最低使用 — 想起は1件のみ |

### 構造的洞察

1. **位置固定動詞** — /bou, /zet (核心専用), /beb, /kop, /par (品質専用), /dio (品質偏重)
2. **汎用動詞** — /akr(37), /kat(31), /tek(29) は全位置で使用される市場の「共通言語」
3. **不足領域** — /epo(2), /hyp(1), /prm(3) が著しく低い → 市場は「留保」「想起」「予見」を明示的に求めていない
4. **24動詞全使用** — 113エージェント中、24動詞が全て最低1回使用 → HGK の包含性を実証
