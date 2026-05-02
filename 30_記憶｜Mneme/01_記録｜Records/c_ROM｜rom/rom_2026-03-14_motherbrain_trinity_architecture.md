---
rom_id: rom_2026-03-14_motherbrain_trinity_architecture
session_id: 62da1799-99a0-4462-b40e-78f866d2e19d
created_at: 2026-03-14 10:16
rom_type: distilled
reliability: High
topics: [Motherbrain, Hyphē, TYPOS, 場⊣結晶, FEP, アーキテクチャ, 実装設計]
exec_summary: |
  Motherbrain = FEP による DB の LLM。場(記憶)⊣結晶(想起)の全体。
  Hyphē = Motherbrain 内部の場⊣結晶メカニズム。TYPOS = G|_{Description}。
  2モード想起 (Exploit/Explore)、場と棚の分離、5反証の処理方針が確定。
---

# Motherbrain 三位一体アーキテクチャ — 設計確定

> **[DECISION]** Motherbrain = FEP による DB の LLM

全セッションデータの1元管理。場 (記憶) に溶解させ、Hyphē で結晶化 (想起) する。
SQLite は「結晶棚」であり「場」ではない。

## 構造

> **[DECISION]** 三位一体の配置

```
Motherbrain (全体 = FEP による DB の LLM)
  ├─ Hyphē (場⊣結晶メカニズム)
  │    ├─ Field (embedding 空間 = 記憶の場)
  │    ├─ Crystallizer (MB 検出 = 想起)
  │    └─ τ/λ (臨界パラメータ: τ_cos=0.70, τ_ρ≈0.21)
  ├─ Store (SQLite = 結晶棚。永続化のみ)
  ├─ Indexer (Session → Field への溶解 = F)
  └─ Reporter (Field → レポート = G の一形態)

TYPOS = Hyphē.Crystallizer|_{Description → .typos}
  = 場に溶かした多次元情報を Kalon に1次元テキストに結晶化 (射影)
```

## 2モード想起

> **[DECISION]** Function 座標 (Explore↔Exploit) の直接的操作化

| モード | FEP 対応 | 操作 | いつ |
|:-------|:---------|:-----|:-----|
| Exploit 想起 | VFE 最小化 | 文脈にフィットする記憶 | 実行・実装時 |
| Explore 想起 | EFE epistemic 最大化 | 驚きのある接続 | 設計・探索時 |

> **[DISCOVERY]** 「驚きの最小化」だけでは既知しか思い出せない

Surprise ≒ 情報量 (Shannon self-information = -log p(o))。
Explore 想起は「まだ接続されていないが接続すべき記憶」を見つける。
例: Possati 論文とチャンク分割の接続発見。

## 正確性と有用性

> **[DISCOVERY]** 2軸は犠牲関係ではなく前提関係

| 軸 | FEP 対応 | 役割 |
|:---|:---------|:-----|
| 客観的正確性 | Accuracy (VFE 第1項) | 前提。保存の忠実性 |
| 主観的有用性 | -Complexity + EFE | 結晶化の選択基準 |

正確性を犠牲にした有用性は VFE を増大させるので FEP 的に選ばれない。
正確な記憶の中から有用な想起を結晶化する。

## 場と棚の分離

> **[DECISION]** 場 ≠ 棚

| レイヤー | 技術 | 役割 |
|:---------|:-----|:-----|
| 場 (Field) | NumPy/FAISS + `.npy` 永続化 | ベクトル空間、密度推定、k-NN |
| 棚 (Store) | SQLite (既存 motherbrain_store.py) | 結晶メタデータ、FTS5 |
| 界面 | Hyphē エンジン | F⊣G サイクル、τ 計算、ρ(x) 推定 |

## 5反証の処理方針

> **[DECISION]** 「潰そうと思えば潰せる」(Creator)

| # | 反証 | 処理 |
|:--|:-----|:-----|
| ① | LLM≠Hyphē | 手段の差異は実装レベル。目的(VFE最小化)は同一 |
| ② | Drift O(n²) | 局所近傍 k-NN で O(n·k) に設計回避 |
| ③ | VFE≠真理 | **無関係**。目的は正しさではなく有用な想起 |
| ④ | PDE不在 | Possati 2025 で部分解決 |
| ⑤ | Kalon△≠▽ | △(内部)で開始、▽(外部)は後段 |

## 関連情報

- 関連 Session: session_164ceafc (場⊣結晶発見)、session_df9fdd10 (Possati+Beck&Ramstead)
- 関連 KI: linkage_hyphe.md、typos_hyphe_map.md
- 関連 PoC: NucleatorChunker (session_7838fc1c)
- 次のアクション: **場のスキーマ設計** — 何を embedding にし、どう格納するか

<!-- ROM_GUIDE
primary_use: Motherbrain アーキテクチャの設計判断のリファレンス
retrieval_keywords: Motherbrain, Hyphē, TYPOS, 三位一体, 場, 結晶, FEP, DB, LLM, Explore, Exploit, 想起
expiry: permanent
-->
