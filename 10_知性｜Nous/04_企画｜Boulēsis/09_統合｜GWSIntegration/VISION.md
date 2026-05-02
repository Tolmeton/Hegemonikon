# GWS 随伴統合 — VISION

> Google Workspace CLI (`gws`) を HGK の CCL パイプラインに統合し、
> 認知系 (考える) + 行動系 (実世界を変える) の随伴対を完成させる。

## 前提

| 項目 | 値 |
|---|---|
| Upstream | <https://github.com/googleworkspace/cli> |
| Install | `npm install -g @googleworkspace/cli` |
| Prereqs | Node.js 18+, GCP Project, Google Workspace account |
| Status | Pre-v1.0, NOT officially supported Google product |
| Auth | OAuth (Desktop) / Service Account / Token Export |
| Skills | 89 skills (API base + helper + workflow + persona + recipe) |

## 行為可能性 (Affordance Map)

### Phase 0 — 即時 (Infrastructure)

**目的**: `gws` を動作環境に導入し、基本操作を検証する。

- `npm install -g @googleworkspace/cli`
- `gws auth setup` → OAuth 設定
- `gws auth login -s drive,gmail,sheets,calendar`
- `gws drive files list --params '{"pageSize": 5}'` → 疎通確認
- `--dry-run` による安全検証

**解放される行為可能性**:
- HGK 環境から Google Workspace の全 API に CLI アクセス可能になる
- `run_command` 経由で Claude が `gws` コマンドを実行可能

---

### Phase 1 — MCP Wrapper (Integration)

**目的**: `gws` コマンドを MCP server 化し、Claude から tool として呼び出せるようにする。

設計方針:
- 薄い Python ラッパー (`gws_mcp_server.py`)
- `subprocess.run(["gws", ...])` → JSON 出力をパース → MCP response
- Tools: `gws_drive_list`, `gws_gmail_triage`, `gws_calendar_insert`, `gws_sheets_read` 等
- `--dry-run` をデフォルトで付与 (N-4 不可逆前に確認)
- `--sanitize` を書き込み操作に自動付与 (Model Armor)

**解放される行為可能性**:
- Claude が `gws gmail +triage` を MCP tool として直接呼び出し
- CCL パイプライン内で GWS 操作を他の認知操作と連鎖可能

---

### Phase 2 — CCL マクロ (Composition)

**目的**: 業務パターンを CCL マクロとして定義し、1コマンドで実行可能にする。

```
@standup  = /ops+_gws:workflow:+standup-report_/kat+
@inbox    = /ops+_gws:gmail:+triage_(/lys+*/ele+)_/kat+
@prep     = /ops+_gws:workflow:+meeting-prep_/prm+_/kat+
@report   = /ops+_gws:sheets:+read_/lys+_gws:docs:create_/kat+
```

**解放される行為可能性**:
- 「朝の定型作業」が `/ccl-helm` の一部として自動化
- 認知操作 (分析/判断) と実世界操作 (メール/カレンダー) のシームレスな結合

---

### Phase 3 — 知識パイプライン (Knowledge)

**目的**: Google Workspace のデータを HGK の知識基盤に自動投入する。

- **Gmail → `/eat`**: 重要メールの内容を自動消化 → Gnōsis に投入
- **Drive → Gnōsis**: Google Docs/Sheets をベクトルインデックスに追加
- **Calendar → Chronos**: 予定データをセッションコンテキストに自動注入

**解放される行為可能性**:
- メールの内容を「知識」として蓄積 (手動コピペ不要)
- ドキュメントの変更を自動検知し、知識基盤を常に最新に保つ

---

### Phase 4 — Agora 連携 (Revenue)

**目的**: クライアント向け成果物の生成を自動化する。

- データ分析結果 → Google Sheets に自動出力
- 報告書 → Google Docs に自動生成
- プレゼン → Google Slides に自動生成
- 請求書・見積もり → Sheets テンプレートから生成

**解放される行為可能性**:
- 「分析して、まとめて、納品する」を CCL パイプライン1本で実行
- Creator の手作業を最小化し、HGK の直接的な経済価値を証明

---

### Phase 5 — Model Armor 統合 (Safety)

**目的**: `gws` の `--sanitize` (Model Armor) を HGK の安全層と統合する。

- `--sanitize` = Google の安全フィルタ (入力/出力のコンテンツスクリーニング)
- Sekisho (BC 監査) との並列運用
- 外部メール送信前の二重チェック: Sekisho (BC違反) + Model Armor (コンテンツ安全)

**解放される行為可能性**:
- 2層の独立した安全保証 (HGK 内部 + Google 外部)
- 誤送信・不適切コンテンツのリスクを構造的に最小化

---

## 随伴対の構造

```
HGK 認知系 (考える)          GWS 行動系 (変える)
────────────────────        ────────────────────
/noe  認識                   gws drive files list
/lys  分析                   gws sheets +read
/dia  判断                   gws gmail +triage
/ene  実行                   gws calendar +insert
/kat  確定                   gws chat send
/ops  俯瞰                   gws workflow +standup-report
```

**F (認知→行動)**: 認知的判断を実世界操作に変換する
**G (行動→認知)**: 実世界データを認知的入力に変換する
**Fix(G∘F)**: 認知と行動のサイクルが安定する点 = 自動化された業務フロー

---

## Phase 優先度

| Phase | 難易度 | 価値 | 依存 | 推定工数 |
|---|---|---|---|---|
| 0 | ★☆☆ | 基盤 | なし | 30min |
| 1 | ★★☆ | 高 | Phase 0 | 2-3h |
| 2 | ★★☆ | 高 | Phase 1 | 1-2h |
| 3 | ★★★ | 中 | Phase 1 | 3-5h |
| 4 | ★★★ | 最高 | Phase 2+3 | 5-10h |
| 5 | ★☆☆ | 中 | Phase 1 | 1h |

**推奨**: Phase 0 → 1 → 2 → 5 → 3 → 4 (価値/コスト比順)
