# MCP Ecosystem Extensions

> **Origin**: 2026-02-01 Perplexity Task 2 — MCP エコシステム監視
> **Purpose**: Hegemonikón の mekhane/ 層に MCP 関連機能を拡張

---

## 概要

Perplexity Task 2 の調査結果から、以下の MCP 拡張が Hegemonikón に有用と判断されました。

---

## 1. MCP Apps UI → exagoge/ 拡張

### 背景

Anthropic × OpenAI 共同発表の「MCP Apps」正式版により、UI リソース仕様が確定。

### 適用先

`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/exagoge/`

### 設計

```yaml
module: mcp_apps_ui
purpose: "MCP Apps の UI リソースをレンダリング"
features:
  - resource_type: "ui_component"
    handler: render_component
  - resource_type: "ui_layout"
    handler: render_layout
integration:
  - library/mcp_apps_sdk
dependencies:
  - mcp-core >= 2.0
```

### 実装優先度

**HIGH** — UI 統合の標準として採用すべき

---

## 2. OpenCV MCP → ergasterion/ 拡張

### 背景

コンピュータビジョン処理を MCP 経由で利用可能に。

### 適用先

`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/ergasterion/`

### 設計

```yaml
module: opencv_mcp
purpose: "画像処理・CV 操作を MCP ツールとして提供"
features:
  - tool: image_analyze
    description: "画像の内容分析"
  - tool: ocr_extract
    description: "画像からテキスト抽出"
  - tool: object_detect
    description: "オブジェクト検出"
integration:
  - ergasterion/prompts/vision_analysis.md
dependencies:
  - opencv-mcp-server
```

### 実装優先度

**MEDIUM** — 画像処理が必要な場合に導入

---

## 3. Plotting MCP → exagoge/ 拡張

### 背景

リアルタイムデータ可視化。

### 適用先

`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/exagoge/`

### 設計

```yaml
module: plotting_mcp
purpose: "データ可視化を MCP 経由で提供"
features:
  - tool: create_chart
    description: "チャート生成"
  - tool: create_graph
    description: "グラフ生成"
  - resource: chart_image
    description: "生成されたチャート画像"
integration:
  - exagoge/library/data_visualization
dependencies:
  - plotting-mcp-server
```

### 実装優先度

**MEDIUM** — データ分析タスクで活用

---

## 4. MATLAB MCP → anamnesis/ 拡張

### 背景

ハードウェア・センサーコンテキストの統合。

### 適用先

`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/anamnesis/`

### 設計

```yaml
module: hardware_context
purpose: "ハードウェア状態・センサーデータをコンテキストに追加"
features:
  - resource: system_metrics
    description: "CPU/メモリ/ディスク状態"
  - resource: sensor_data
    description: "センサー情報（温度等）"
integration:
  - anamnesis/collectors/hardware_collector.py
dependencies:
  - matlab-mcp-core-server
```

### 実装優先度

**LOW** — 特定のハードウェア統合シナリオで必要

---

## 実装ロードマップ

| Phase | Module | 期限 | 状態 |
|:------|:-------|:-----|:-----|
| 1 | MCP Apps UI | 2月中旬 | 📋 設計済 |
| 2 | Plotting MCP | 2月末 | 📋 設計済 |
| 3 | OpenCV MCP | 3月上旬 | 📋 設計済 |
| 4 | MATLAB MCP | 必要時 | 📋 設計済 |

---

## KI 昇格

このドキュメントは `Model Context Protocol (MCP) Ecosystem` KI に統合予定。

---

*Consumed from Perplexity Task 2: MCP エコシステム監視 (2026-02-01)*
