# HGK Perception Stack — 方向性ドキュメント

> **起源**: /noe+ 分析 (2026-03-08)
> **ステータス**: 方向性確定・PoC 未着手
> **Kalon**: 0.85
> **AMBITION 関連**: F4 (AI 指揮台) / F6 (認知コロニー) / F10 (Plugin OS L5 埋込層)

---

## ビジョン

**HGK に「目と手」を与える** — 知覚 (Perception) と運動 (Action) のループを OSS で実現し、FEP の能動推論をソフトウェアアーキテクチャに実装する。

### Creator の要求 (原文)

> 「認識を共有したいほうが強い。"この画面のここ！"を直感的に共有したい」
> 「特にHGK APPのような"グラフィック"な作業は現状ではとてもやりにくい」
> 「CoworkやPerplexityのComputerなどのOSレベルでの操作権限がほしい」
> 「知覚と運動のループを動かしたい」
> 「動画（映像）対応もしたい」
> 「基本はOSSを利用したい」

---

## アーキテクチャ: 3 層 Perception Stack

```
          ┌────── Perceive ──────┐
          │                      │
    ┌─────▼─────┐          ┌─────┴─────┐
    │ Screen    │          │ a11y tree │
    │ Stream    │          │ (pywinauto│
    │ (ffmpeg)  │          │  /AT-SPI) │
    └─────┬─────┘          └─────┬─────┘
          │                      │
          ▼                      ▼
    ┌─────────────────────────────────┐
    │        HGK Perception MCP      │  ← 新 MCP サーバー
    │  (OmniParser + Florence-2 +    │
    │   accessibility tree の統合)    │
    └──────────────┬──────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────┐
    │     HGK 認知制御 (CCL/WF/COO)  │  ← 既存の脳
    └──────────────┬──────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────┐
    │        HGK Action MCP          │  ← 新 MCP サーバー
    │  (pywinauto / xdotool /        │
    │   keyboard+mouse injection)    │
    └──────────────┬──────────────────┘
                   │
                   └────── Act ──────→ OS → Perceive...
```

| 層 | 名前 | Creator の要求 | 技術 |
|:---|:-----|:-------------|:-----|
| **L0: Pointing** | 指す層 | 「この画面のここ！」 | HGK APP (Tauri) の領域選択 UI |
| **L1: Perception** | 知覚層 | 認識の共有 + 動画 | accessibility tree + VLM + Florence-2 + ffmpeg ストリーム |
| **L2: Action** | 運動層 | OS 操作権限 | pywinauto (Win) / xdotool (Linux) |

---

## 設計原則

1. **FEP 的に正しい** — 能動推論 = 知覚と運動のループ。`e2e_loop.py` と同型
2. **OSS 基本** — 閉じた API (Anthropic/Google CUA) に依存しない
3. **イベント駆動** — 常時 DOM ではなく、変化検出 or Creator の「ここ」で発火
4. **動画対応** — ffmpeg スクリーンストリーム + フレーム差分 = 変化時のみ Perception 発火
5. **MCP サーバーとして実装** — 既存 HGK エコシステムに統合。CCL/WF から呼べる
6. **フォールバック戦略** — 構造 (a11y tree) → 知覚 (VLM/Florence-2)

---

## OSS スタック

| 層 | OSS | ライセンス | 役割 | 状態 |
|:---|:----|:----------|:-----|:-----|
| **知覚 (Vision)** | Florence-2 | MIT | OCR + 座標検出 | ✅ 稼動中 (GALLERIA:8780) |
| **知覚 (Vision)** | OmniParser (Microsoft) | MIT | スクリーンショットから UI 要素構造化 | 🔍 評価候補 |
| **知覚 (構造)** | pywinauto | BSD | Windows UIA で accessibility tree 取得 | 🔍 PoC 対象 |
| **知覚 (構造)** | pyatspi2 | LGPL | Linux AT-SPI で accessibility tree 取得 | 🔍 PoC 対象 |
| **知覚 (動画)** | ffmpeg | LGPL | スクリーンストリーム + フレーム差分検出 | 利用可能 |
| **知覚 (統一)** | Computer Use Protocol | Apache 2.0 | OS 横断統一 accessibility tree スキーマ | 🔍 評価候補 |
| **運動** | pywinauto | BSD | Windows UI 操作 (click, type, scroll) | 🔍 PoC 対象 |
| **運動** | xdotool | BSD | Linux X11 操作 | 利用可能 |
| **参考実装** | UFO 2 (Microsoft) | MIT | Desktop AgentOS — ハイブリッド参考 | 参照のみ |

---

## ユースケース

| # | ユースケース | 主な層 | 優先度 |
|:--|:------------|:------|:-------|
| 1 | HGK APP のグラフィック作業 — CSS/レイアウト/3D を AI と共有 | L0 + L1 | 🔴 |
| 2 | Claude.ai / Perplexity デスクトップの DOM 取得 — API なしサービス活用 | L1 + L2 | 🟡 |
| 3 | Debian シェルの直接操作 | L2 | 🟡 |
| 4 | FM GUI 自動化 (別 WS) | L1 + L2 | 🟢 (別 WS) |
| 5 | HGK APP の自己参照的開発 (AMBITION MVP) | L0 + L1 + L2 | 🔴 |

---

## 最初の PoC

**目標**: 画面を「見て」→ 要素を「クリックする」最小ループを動かす

1. **環境調査**: pywinauto / xdotool / pyatspi2 の WSL2 での動作確認
2. **L1 Perception PoC**: スクリーンキャプチャ + Florence-2 で UI 要素検出
3. **L2 Action PoC**: 検出した要素を xdotool/pywinauto でクリック
4. **ループ統合**: Perceive → Decide → Act を 1 サイクル動かす

---

## 参照

- `/noe+ 分析`: `noe_os_dom_hgk_2026-03-08.md`
- 前回 `/noe+` (Vision vs Accessibility): `noe_vision_api_architecture_2026-03-08.md`
- `/zet` 問い候補: `zet_vision_api_improvement_2026-03-08.md`
- AMBITION.md: `40_応用｜Organon/_src｜ソースコード/hgk/docs/AMBITION.md`
- Periskopē 知見: Computer Use Protocol (Apache 2.0), ScaleCUA, A11y-CUA, Fara-7B, UFO 2

---

*作成: 2026-03-08 | /noe+ → 方向性確定 → PoC 着手へ*
