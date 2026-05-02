# A_手順｜Workflows

> **PURPOSE**: ワークフロー定義。24動詞 WF + ユーティリティ WF を Ω/Δ/τ の3階層で管理。

## 階層構造

### サブディレクトリ (5)

| ディレクトリ | 内容 |
|:-----------|:-----|
| `00_分野｜Domain/` | 分野別 WF (業務ドメイン別) |
| `01_CCL｜CCL/` | CCL マクロ WF (ccl-plan, ccl-fix 等) |
| `02_極限｜Peras/` | Ω層 Peras WF (/t, /m, /k, /d, /o, /c, /x, /ax) |
| `03_生成｜Poiesis/` | Δ層 24動詞のベース WF |
| `90_旧構造｜Archive/` | 旧バージョン WF |

### ルートファイル (τ層 ユーティリティ WF)

| ファイル | サイズ | 内容 |
|:---------|:------|:-----|
| `boot.md` | 34.6KB | /boot — セッション開始 |
| `bye.md` | 30.3KB | /bye — セッション終了 |
| `eat.md` | 19.1KB | /eat — 外部コンテンツ消化 |
| `fit.md` | 14.7KB | /fit — 適合検証 |
| `vet.md` | 9.4KB | /vet — クロスモデル監査 |
| `basanos.md` | 2KB | /basanos — 静的解析 |
| `wf_evaluation_axes.md` | 15.2KB | WF 評価軸 (Epistēmē から移動) |

## ランタイムとの関係
- `.agents/workflows/*.md` — Agent が直接参照する WF 定義
- ここに格納されるのは WF の**詳細定義と設計文書**

---
*Created: 2026-03-13*
