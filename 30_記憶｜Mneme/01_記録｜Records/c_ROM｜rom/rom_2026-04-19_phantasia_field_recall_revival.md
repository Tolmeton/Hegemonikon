# ROM 2026-04-19 — Phantasia Field 検索基盤の蘇生

> Status: 完了 (実用達成)
> Origin: 至上命題「Claude がトークンをかけずに必要な情報を入手」の解決

## 1. 至上命題の達成度

**Tolmetes の本意 (4セッション前に開示)**:
> Claude ができる限りトークン（労力）をかけず、セッションに必要な情報を手に入れられるようにすること

**達成状況**: 70-80% (実用レベル)
- ✅ MCP `mcp__aisthetikon__search` が複数インデックス横断で実用品質の結果を返す
- ✅ recall() は source 横断検索が機能 (ROM + handoff + doxa + kernel)
- ✅ April 12 までの最新 handoff まで到達可能
- ⚠️ Symploke Chronos/Kairos インデックスの自動更新メカニズムは未調査
- ⚠️ April 13 以降の最新コンテンツの反映条件は未確認

## 2. 解決した3つのレイヤーの問題

### 2.1 Layer 1: VertexEmbedder 死亡 (前セッション、Codex が修復)

**症状**: `recall()` が n=0 を返す
**根因**: `google-genai` パッケージが root `.venv` に未 install
**修復**: `.venv/bin/python -m pip install google-genai==1.73.1` (コード変更ゼロ)
**実行venv**: 必ず root `.venv` (Python 3.14) を使う。`PYTHONPATH` で mekhane src を指す
- mekhane の `_src｜ソースコード/.venv` (Python 3.13) には faiss/google-genai 未 install

### 2.2 Layer 2: Source dedup 欠如 (今セッション、Claude が修復)

**症状**: top-5 が全て同一ファイルのチャンクで占有される (cluster fixation)
**根因**: `_refine_results()` は content-level dedup のみで source-level dedup なし
**修復**: `phantasia_field.py:_refine_results` に `max_per_source: int = 1` パラメータ追加
- `seen_urls: dict[str, int]` で URL 単位カウント
- U_fixation (固着) としてラベル
- `_recall_exploit` の oversample を `limit*2` → `limit*5` に増加
- 計 13 insertions / 2 deletions

### 2.3 Layer 3: 知識基盤の欠落 (今セッション、Codex 委譲で投入)

**症状**: April 2026 以降の ROM/handoff/Nous/Mekhane docs が未 dissolve
**規模**: 5,809 ファイル中 1,943 既処理、5,782 未処理
**修復スクリプト**: `80_運用｜Ops/_src｜ソースコード/scripts/bulk_dissolve_md.py` (411行、Codex 作成)
**結果**: 27分で 377 新規 dissolve / 11,830 chunks 追加 / 1 error (UTF-8 不正バイナリ)
- session 190 / sophia 93 / handoff 69 / doxa 11 / kernel 9 / rom 5
- Skip 5,431 (内部 primary_key dedup で既存判定)

## 3. 検索の運用 Tips

### 3.1 MCP 経由 (推奨)

```python
mcp__aisthetikon__search(
    query="...",
    scope="all",
    sources=["chronos","kairos","sophia","gnosis"],  # ★ 必須
    k=10,
)
```

- **`sources` を必ず指定せよ**: デフォルト all は category ごとに少数しか返さない
- 推奨組合せ: `["chronos","kairos","sophia","gnosis"]` で handoff・KI・論文横断
- PhantasiaField は内部で 1件/source に絞られる (今回 fix の効果)

### 3.2 直接 recall() (デバッグ用)

```bash
SRC="/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード"
PYTHON="/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/.venv/bin/python"
PYTHONPATH="$SRC" $PYTHON -c "
from mekhane.anamnesis.phantasia_field import PhantasiaField
f = PhantasiaField()
results = f.recall('クエリ', limit=10)
"
```

注意: 結果の dict キーは `url` (file path)、`source`、`title`、`_distance`、`_field_score`

### 3.3 サービス再起動

新規 dissolve を MCP に反映するには:
```bash
systemctl --user restart hgk-mcp@phantazein.service
```

## 4. 発見した構造的事実

### 4.1 二系統のインデックス

- **PhantasiaField (FAISS)**: `recall()` で直接アクセス。今回 dedup fix の対象
- **Symploke SearchEngine**: `mcp__aisthetikon__search` の Chronos/Kairos/Sophia/Gnosis 部分
- 両者は別系統。bulk dissolve は前者のみ更新 (後者は別の indexer 経由)

### 4.2 venv 二重構造

- root `.venv` (Python 3.14): faiss + google-genai 入り。MCP サーバーが使う
- mekhane `_src｜ソースコード/.venv` (Python 3.13): 必須パッケージ未 install
- ローカル実行時は **root venv + PYTHONPATH** で動かせ

### 4.3 url フィールドの暗黙的仕様

- `PhantasiaField.dissolve()` は `url` を空文字で記録
- ファイルパスは `parent_id` / `source_id` に入る
- ただし FAISS metadata 取得時には `_expand_metadata()` 経由で `url` にファイルパスがマップされる
- ローカル直 recall() の戻り値では `url` キーにパスが入る (Codex が偏差として記録)

### 4.4 mtime フィールドが metadata に無い

- 再 dissolve 判定は path 存在のみ (mtime 比較 不可)
- ファイル更新は新 primary_key で追加・古い行は残る (内部 chunk-level dedup で重複は自動除外)
- 今後 add_chunks() に created_at/updated_at を追加する案あり (別タスク)

## 5. 次の課題 (B 以降)

### B: Symploke インデックス更新メカニズム調査

- Chronos/Kairos インデックスは bulk dissolve では更新されない
- April 13 以降の handoff が MCP 検索でどこまで返るか実測
- 更新トリガー (cron? 手動? Hook?) を特定し、運用化

### C: 別トピックでの運用感確認 (任意)

- 「Hyphē ↔ Lethe」「Yugaku 論文XII」等で recall() / MCP search を試す
- 検索品質の体感値を集める

### D: max_per_source パラメータ化

- 現在 `max_per_source=1` ハードコード (recall() 経由)
- データが薄いトピックでは n=1 で頭打ちになる
- recall() に `max_per_source` 引数追加して呼出側で制御可能にするか検討

## 6. コミット対象

- `20_機構｜Mekhane/_src｜ソースコード/mekhane/anamnesis/phantasia_field.py`: source dedup 追加
- `80_運用｜Ops/_src｜ソースコード/scripts/bulk_dissolve_md.py`: 一括 dissolve スクリプト

## 7. 心法違反と是正

- **N-08 委譲パスの再確認**: bulk dissolve スクリプトは Codex 委譲で作成した (411行、Advisor Strategy 通り)
- **N-04 不可逆操作前確認**: phantazein サービス再起動は Tolmetes が選択肢 A を選んだ時点で承認済として実行
- **N-01 Codex 報告**: Codex が自認した N-01 違反 (Edit 前 Read 飛ばし → 自己是正済み) を accept

---

*Created: 2026-04-19 — 4セッション越しの記憶基盤蘇生プロジェクト完了*
