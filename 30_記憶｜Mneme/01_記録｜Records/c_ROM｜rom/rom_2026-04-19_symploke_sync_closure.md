# ROM 2026-04-19 Symploke sync の二重構造閉合

## 文脈

前日 (2026-04-18) の bulk_dissolve で PhantasiaField (lancedb) を 199K → 211K records に拡大した後、`mcp__aisthetikon__search` での検索品質を測ると、**Symploke Chronos/Kairos インデックスだけが 2026-04-12 で停滞していた**。PhantasiaField と Symploke が別インデックスで、bulk_dissolve は前者しか更新していなかった。

## 発見した構造

| Index | 実体 | 更新経路 |
|-------|------|----------|
| PhantasiaField | `30_記憶｜Mneme/04_知識｜Gnosis/.../lancedb` | `bulk_dissolve_md.py` (今日の実装) |
| Symploke Kairos | `30_記憶｜Mneme/02_索引｜Index/kairos.faiss` | `kairos_ingest.py --all` (手動 CLI) |
| Symploke Sophia | 同上 `sophia.faiss` | `sophia_ingest.py` (手動 CLI) |
| Symploke Chronos | 同上 `chronos.faiss` | **TODO 未実装** (`mneme_cli.py:102`) |
| Symploke handoffs | 同上 `handoffs.faiss` | 別ルート (未特定) |

## 行ったこと

1. **A (即時手動)**: `mneme_cli.py ingest --kairos --sophia` 実行。Kairos 302→823 docs / Sophia 253 docs 追加。kairos.faiss mtime 2026-04-12 → 2026-04-19。
2. **B 調査 → 既存 unit 発見**: `hgk-symploke-refresh.timer` が本日 10:06:38 に active 化、日次 06:30 JST 実行、ExecStartPost で phantazein 再起動。新規作成を取り下げた (Codex が N-06 違和感検知で停止)。
3. **C (Codex 実装)**: `bulk_dissolve_md.py` に `_post_dissolve_sync` hook 追加。dissolve 完了後に kairos_ingest + sophia_ingest を subprocess で呼び、phantazein を自動再起動する。`--skip-sync` フラグでスキップ可能。

## 構造的教訓 (N-01 / N-06)

- **仕様書を書く前に `systemctl --user list-timers --all` で既存 unit を確認すべきだった** — B 要件はすでに満たされていた。仕様書起草は「知っている」記憶からの射影で、現物確認を飛ばした N-01 違反
- **Codex の θ6.3 入力不整合検出が機能した** — 仕様書と現物の矛盾で停止し Tolmetes に判断を戻した。道具の精度は手書き推測より高い

## 至上命題の進捗

「Claude がトークンをかけずセッションに必要な情報を手に入れる」への到達度:

- ✅ PhantasiaField recall() 復活 (4月17日: google-genai インストール)
- ✅ source dedup 修正 (4月18日: max_per_source=1)
- ✅ PhantasiaField に全 .md/.typos 投入 (4月18日: 11,830 chunks 追加)
- ✅ Symploke Kairos/Sophia 最新化 (本日: Kairos 823 docs で April 14 handoff が到達可能)
- ✅ bulk_dissolve → Symploke sync 自動化 (本日 Codex C: post-dissolve hook)
- ✅ 日次 timer 稼働 (既存 `hgk-symploke-refresh.timer`, 06:30 JST)

## 残課題

- **Chronos ingestion TODO** (`mneme_cli.py:102`) — セッション履歴はインデックスされない。別タスク
- **handoffs.faiss** の更新ルートが未特定 — 04-16 mtime でやや古い
- **sync hook の実 run 検証** — Codex は syntax/dry-run/AST で通したが、実 sync 呼出し経路は未観測。本ROM書き込み後の dissolve で自然に検証される

## 検索可用性の現状

```
recall("Face Lemma 射影 oblivion", sources=[kairos,chronos,sophia])
→ Kairos: handoff-handoff_2026-04-14_2042 (April 14 まで届く)
→ Chronos: handoff_2026-04-10 (April 10 止まり、TODO)
→ Sophia: hegemonikon_theoretical_foundations
→ Phantasia Field: rom_2026-03-31_oblivion_deepening
```
