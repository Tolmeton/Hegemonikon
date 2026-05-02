---
rom_id: rom_2026-02-14_rom_ecosystem
session_id: 83c91d8e-0b98-4c34-9952-a3c7aae8c9c1
created_at: 2026-02-14 16:31
rom_type: distilled
reliability: High
topics: [ROM, Indexer, LanceDB, boot, Savepoint, VSearch, session_indexer, cli]
exec_summary: |
  /rom WF で生成された蒸留コンテキストを LanceDB にインデックスし、
  /boot 時に自動復元するエコシステムを構築。Savepoint を /rom- に吸収。
---

# ROM エコシステム統合

> **[DECISION]** ROM Indexer は Handoff Indexer の parse→records→embed→LanceDB upsert パターンを完全に踏襲する。独自設計ではなく、既存パターンの複製。

## 1. ROM Indexer の実装

**ファイル**: `mekhane/anamnesis/session_indexer.py` (L808-1001 付近に追加)

> **[FACT]** 3関数を追加:
>
> - `parse_rom_md(path)` — Frontmatter YAML + タイトル + 日付 + 意味タグ + セクション見出しを抽出
> - `roms_to_records(roms)` — LanceDB 互換レコードへ変換 (`source="rom"`)
> - `index_roms(rom_dir)` — デデュプ + 埋め込み + LanceDB upsert

> **[DECISION]** source フィールドを `"rom"` に設定。これにより `--source rom` でフィルタ検索が可能。

> **[DECISION]** ファイル名から派生レベルを判定: `_snapshot_` → rom-, `_rag_` → rom+, それ以外 → rom。
> Primary key は `rom:{filename}` でデデュプ。

## 2. CLI エントリポイント

> **[FACT]** 2つのエントリポイントを追加:
>
> - `cli.py rom-index [--rom-dir DIR]` — Gnōsis CLI からの呼び出し
> - `session_indexer.py --roms [--rom-dir DIR]` — 直接実行

## 3. /boot WF v5.7 統合

**ファイル**: `.agent/workflows/boot.md`

> **[DECISION]** Savepoint を `/rom-` に完全吸収。「保存したいなら全部 /rom」— 派生で深度を選ぶ。
> 旧保存先: `sessions/savepoint_*.md` → 新保存先: `rom/rom_*_snapshot_*.md`

> **[DECISION]** Phase 3.45 として ROM 自動読込フェーズを新設。派生ごとに読込量を制御:
>
> - `/boot-`: スキップ可
> - `/boot`: 最新 2-3 件の exec_summary のみ
> - `/boot+`: 最新 5 件を精読 + ROM VSearch
> - Focus モード: intent に関連する ROM のみ VSearch で引く

> **[RULE]** ROM VSearch のコマンド:
>
> ```bash
> cd ~/oikos/hegemonikon && PYTHONPATH=. .venv/bin/python mekhane/anamnesis/cli.py search "{query}" --source rom --limit 3
> ```

## 4. 圏論的構造

```
/rom  = π: Ses → Rom (選択的射影)     — セッション中に焼く
/bye  = R: Ses → Mem (全体圧縮)       — セッション終了時に焼く
/boot = L: Mem → Ses (復元)           — セッション開始時に読む
/rom- = π|_partial (部分写像)          — 旧 Savepoint の正体
```

> **[FACT]** /rom で焼いたコンテキストは /boot Phase 3.45 で読み返される。
> このフィードバックループが /rom の存在意義。

## 関連情報

- 関連 WF: /rom, /boot, /bye
- 関連ファイル: `session_indexer.py`, `cli.py`, `boot.md`
- 関連 BC: BC-18 (コンテキスト予算意識)

<!-- ROM_GUIDE
primary_use: ROM エコシステムの設計判断と実装パスの参照
retrieval_keywords: ROM, Indexer, VSearch, Savepoint, boot, LanceDB, 蒸留
expiry: permanent
-->
