# Phase C ローカル dry-run 記録

- **日時**: 2026-03-26（`/bou` 承認後 `/ene` 相当）
- **コマンド**: `C:\tmp\lethe_scp` で  
  `…\.venv\Scripts\python.exe train_structural_attention.py --dry-run --max-pairs 10`
- **終了コード**: **1**（失敗）
- **原因 [SOURCE: 実行ログ]**: `ModuleNotFoundError: No module named 'torch_xla'` → `RuntimeError: TPU 必須 / TPU 使用不可 … のため終了します`
- **補足**: CodeBERT 重みのロードは完了（HF 未認証の警告・`torch_dtype` 非推奨警告あり）。TPU ランタイムが無い Windows ローカルでは本スクリプトの `load_llm` が終了する設計。
- **生ログ**: `C:\tmp\lethe_scp\phase_c_dryrun_20260326.log`

## 次の一手（提案）

- TPU 環境（Lethe 側）で同一コマンドを実行し、exit code とログ先頭〜30行をここへ追記するか、別タイムスタンプ `.md` で保存する。
