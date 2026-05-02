# HGK Health (full) — 緑化のための実体側チェックリスト

`HGK_HEALTH_PROFILE` 未設定または `full` のとき、`python -m mekhane.peira.hgk_health` は品質行の閾値を緩めません。  
ここでは **閾値ではなくデータ/実装** で満たすための参照コマンドをまとめます。

## 閾値（実装ソース）

- `mekhane/peira/hgk_health.py` 内の各 `check_*` を参照（Dendron L1 90%/70%、MECE、定理 20/16、Kalon、認知 3.5 & 80% 等）。

## ローカル検証コマンド（例）

```text
cd 20_機構｜Mekhane/_src｜ソースコード
set PYTHONPATH=.
python -m mekhane.peira.hgk_health
python -m mekhane.peira.hgk_health --json
```

- **Windows**: Gnosis/Tier1 は Task Scheduler 相当文字列の検出。`schtasks` 出力はコンソールロケールでデコードします。
- **Linux/WSL**: systemd user timer / crontab / `pgrep` 系のチェックが有効です。

## 品質行を改善する一般的な手順

| 項目 | 向き先 |
|------|--------|
| Dendron L1 (Purpose カバレッジ) | `python -m mekhane.dendron.cli check mekhane/ --format ci` で欠落を減らす |
| Dendron MECE | `python -m mekhane.dendron.cli mece mekhane/ --ci` の warnings/errors を構造修正で減らす |
| Kalon | `mekhane.fep.kalon_checker` の指摘に沿ってコード整合を取る |
| Krisis 随伴 | builder の `details` に従い失敗ペアを修正 |
| 認知品質 | Handoff の violations を減らす（ルール準拠の出力） |
| 定理活性 | 90 日窓で Handoff に 24 定理の direct/hub 記録を増やす |

## 運用行（ops）

Digest ログ/レポート、Tier1 スケジュール等は環境依存です。開発用に運用のみ緩めたい場合は `HGK_HEALTH_PROFILE=cursor`（品質閾値は変わりません）。

## 検証メモ（開発環境）

- **Windows (PowerShell)**: `PYTHONPATH=.` で `python -m mekhane.peira.hgk_health --json` → `effective_profile: "full"` を確認。
- **WSL/Linux**: 同コマンドで JSON が生成されること、`Gnosis Index` / `Hermēneus` 等は OS により異なる（systemd/crontab/pgrep）。
- 終了コードは `score >= 0.7` で 0、未満で 1（`hgk_health.main`）。
