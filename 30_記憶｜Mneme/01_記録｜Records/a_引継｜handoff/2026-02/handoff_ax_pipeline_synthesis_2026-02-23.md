# Handoff: AxPipeline 合成逐次化と Cortex API 移行

## セッション概要

- **日時**: 2026-02-23 13:00 - 15:00
- **目的**: AxPipeline Phase 2 (6 Series の合成) の精度向上と E2E 確認
- **結果**: Phase 2 の S1-S4 逐次化完了。google-genai SDK 依存の import ハングを特定し、TokenVault + urllib による Cortex API 直接呼び出しへ移行。E2E 実証成功。

## 成果物

| ファイル | 状態 | 内容 |
|:--------|:-----|:-----|
| `runtime.py` | ✅ 更新 | `_call_cortex_direct` 追加。Cortex REST API 優先・SDK フォールバック化 |
| `ax_pipeline.py` | ✅ v2化 | `_phase2_synthesis` を S1(俯瞰)→S2(緊張)→S3(メタ結論)→S4(Kalon検証) の4連 LLM 呼び出しに分割 |
| `peras_pipeline.py` | ✅ v2化 | Phase 1 で先行動詞の出力結果を後続プロンプトに注入する定理間対話 (`depth='+'`) 実装 |
| `task.md` | ✅ 完了 | Phase 2 逐次化 E2E テストまで完了 |

## 技術的教訓 (ROM/RAM)

### 1. `asyncio.to_thread` と SDK の C拡張ハング

E2E テストが `import` 段階から一切進まずタイムアウトする問題に直面。
調査の結果、`google-genai` や `httpx`, `h2` などの重いネットワーク依存ライブラリのロード中や C 拡張の実行中に Python プロセスがブロッキングされ、SIGTERM の保留 + その他の `venv` プロセスの立ち上がりブロックを引き起こしていた。

### 2. TokenVault + urllib = 最強の軽量ラッパー

この事態を受け、`CortexClient` の import を避け、`TokenVault` (`get_token("default")`) と Python 標準ライブラリ (`urllib.request`) のみを使用して直接 `cloudcode-pa/v1internal` エンドポイントを叩く `_call_cortex_direct` を `runtime.py` に実装。
→ 結果、環境ブロックは完全に解消し、E2E 4連続 LLM コールが **41秒** で完了した。

## 次のステップ

1. **AxPipeline Phase 3 (X-series 接続)**
   - 生成したメタ結論 (S3) と Kalon 検証 (S4) を受け取り、X-series 関係式へ接続する実装。
2. **PerasPipeline Phase 2 (Limit) 解析ロジックの強化**
   - Markdown パーサーの堅牢化は完了しているが、C0-C3 以外の微小な出力ブレへの完全対応。
3. **E2E 統合テスト (/ax 全体)**
   - mock ではなく実際に /ax パイプラインを 6 Series ✕ 4 verbs ✕ 4 limits でフルランし、コンテキスト破綻がないかを確認する。
