# boot_artifacts

`/boot`・`/boot+` 実行時に保存する **生出力の正本** 置き場。

| 種別 | ファイル名パターン | 内容 |
|:-----|:-------------------|:-----|
| boot_integration | `boot_integration_stdout_YYYYMMDD_HHMM.md` | `boot_integration.py` の標準出力相当（間引き前全文） |
| Phantazein | `phantazein_report_YYYYMMDD_HHMM.md` | `phantazein_report(..., output_path=...)` が書き出すレポート全文（UTF-8、無改変） |

MCP の `phantazein_report` は応答が長いとチャット側で切り詰められる。**SOURCE としての正本は常に本ディレクトリのファイル**とする。

定義の正: `.agents/workflows/boot.md` Phase 0.0 / Phase 2.8。
