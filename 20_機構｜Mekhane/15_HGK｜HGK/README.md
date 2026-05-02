# 15_HGK｜HGK — Hegemonikón デスクトップアプリ

> **_src 対応**: `_src/hgk/` (Tauri v2 + Vite + TypeScript)
> **詳細 README**: [`_src/hgk/README.md`](../../_src｜ソースコード/hgk/README.md)

---

## 概要

| レイヤー | 技術 |
|:---------|:-----|
| Desktop Shell | Tauri v2 (Rust) |
| Frontend | Vite + TypeScript (Vanilla) |
| 3D Visualization | Three.js + d3-force-3d |
| Accessibility | AT-SPI2 (Rust, Linux) |
| Backend API | FastAPI (UDS: `/tmp/hgk.sock`) |

## 24 Views

Dashboard, Chat, Graph 3D, Search, Sophia, Gnosis, FEP, Timeline,
Notifications, Synteleia, Basanos, PKS, Desktop DOM, Agent Manager,
Digestor, Quality, Postcheck, Orchestrator, DevTools, Cowork,
Jules, Aristos, Synedrion, Settings

> 全 View の詳細は `_src/hgk/README.md` を参照。

## 関連ドキュメント

| ドキュメント | 在処 | 状態 |
|:------------|:-----|:-----|
| HGK README | `_src/hgk/README.md` | 🟢 最新 |
| Task Notification Panel | `_src/hgk/TASK_NOTIFICATION_PANEL.md` | 🟢 設計書 |
| HGK 設計文書 | `Boulēsis/00_舵｜Helm/specs/` | 設計文書群 (旧 hgk/docs/ から移動) |
| E4 Tauri 企画 | `Boulēsis/03_市場/content/standalone/E4_tauri.md` | 🟡 企画書 |
| Zero Setup (Windows) | `Archive/text_mirror/docs/hgk-zero-setup-windows.md` | ⚪ 旧版 |
| Zero Setup (Linux) | `Archive/text_mirror/docs/hgk-zero-setup.md` | ⚪ 旧版 |

## 依存関係

```
hgk/ (Tauri Frontend)
  ├── mekhane/api/        → FastAPI バックエンド (UDS 経由)
  ├── mekhane/synteleia/  → Synteleia 監査エンジン
  └── mekhane/anamnesis/  → Gnōsis ベクトル検索
```

---

*HGK Desktop Docs v1.0 — 2026-03-13*
