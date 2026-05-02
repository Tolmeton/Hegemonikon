---
rom_id: rom_2026-02-24_searxng_periskope_optimization
session_id: 709c5864-dbea-4353-959a-c1a69bf7e6ef
created_at: 2026-02-24 21:50
rom_type: rag_optimized
reliability: High
topics: [SearXNG, Periskopē, reranking, LLM cascade, Docker, scale-out, deep research]
exec_summary: |
  SearXNG エンジン最適化を 🟢 Naturalized → Kalon 到達。
  3レプリカスケールアウト、深度連動 max_results (15/30/50)、
  min_iterations ガード (1/2/3) を実装。次は LLM カスケードリランク。
---

# SearXNG / Periskopē 最適化 — Full Session ROM {#sec_01_overview}

## §1 確定した設計判断 {#sec_02_decisions}

> **[DECISION]** SearXNG 全エンジン開放 — エンジンリストを空に設定し、SearXNG のデフォルト 70+ エンジンを全て使用。
> 根拠: SearXNG の存在意義はエンジン集約。5エンジンに絞るのは本末転倒。

> **[DECISION]** Google 3エンジン無効化 — google, google_scholar, google_news を `disabled: true`。
> 根拠: CAPTCHA 問題。Google カバーは Vertex AI Search で代替。

> **[DECISION]** 3レプリカスケールアウト — Docker Compose で searxng-1/2/3 (8888/8889/8890)。
> SearXNGSearcher に `base_url: str | list[str]` でラウンドロビン実装済み。

> **[DECISION]** 深度連動 max_results — L1=15, L2=30, L3=50。config.yaml `defaults.max_results_by_depth`。
> engine.py `_max_results_by_depth` で深度に応じて `self.max_results` を動的設定。

> **[DECISION]** min_iterations 新設 — L1=1, L2=2, L3=3。saturation check / no_gaps / high_confidence の3つの break に guard 追加。
> 理由: 1回目で飽和判定されると浅すぎる場合がある。

> **[DECISION]** iterative_deepening — max: L1=3, L2=12, L3=36。
> L3=36回は約27分。saturation_threshold=3.5% で早期停止が効くため「最大」であって「必ず」ではない。

> **[DECISION]** 4get/LibreY/Whoogle 導入見送り — JSON API なし。全て人間向けフロントエンド。
> 代替: Vertex AI Search カスタム App でドメイン特化検索を実現すべき。

> **[DECISION]** タイムアウト設計の分離:
>
> - SearXNG settings.yml `request_timeout: 30` = **個別エンジンのリクエスト上限**
> - SearXNGSearcher `timeout: 180` = **全体の応答上限 (httpx)**
> 180秒を個別エンジンに適用すると1つのエンジンが全体をブロックする。

## §2 発見と知見 {#sec_03_discoveries}

> **[DISCOVERY]** `use_default_settings: true` の意味 — settings.yml でエンジンを列挙しなくても、SearXNG のデフォルト 70+ エンジンは全て有効。列挙は「上書き」であって「限定」ではない。

> **[DISCOVERY]** Qwant は Access Denied で 86400秒 (24h) 自動停止 — SearXNG の正常挙動。問題なし。

> **[DISCOVERY]** Vertex AI Search カスタム App — Qiita/Zenn/CiNii/J-STAGE は SearXNG プラグインではなく、Vertex の Website Search タイプで対応するのが筋が良い。既存 VertexSearchSearcher をそのまま使える。

> **[DISCOVERY]** SearXNG メタデータ保持 — OSSなので response() を改修して引用数・著者を保持可能。但し専用 Searcher (S2, ArXiv) で既にカバー済みのため優先度低。

> **[DISCOVERY]** gluetun パターン — Docker で SearXNG だけ SurfShark VPN、Host は Tailscale 維持。`network_mode: "service:gluetun"` で分離可能。

## §3 LLM カスケードリランク設計ノート {#sec_04_rerank_design}

> **[RULE]** リランクのバッチサイズは深度連動:
>
> - L3 (Deep): **5件/プロンプト** → 30回呼び出し (深く見る)
> - L2 (Standard): **15件/プロンプト** → 10回呼び出し
> - L1 (Quick): **30件/プロンプト** → 5回呼び出し
> 理由:「悪魔は細部に宿る。150件を1プロンプトに詰めたら LLM も流し読みする」

> **[RULE]** カスケード構造:
>
> ```
> 150 raw results → Flash (bulk score) → 30 candidates → Pro (precision) → 10 final
> ```
>
> Cortex API 経由。Flash はほぼ無制限。Pro は上位のみ。

## §4 変更したファイル一覧 {#sec_05_files}

| ファイル | 変更 |
|:---------|:-----|
| `mekhane/periskope/docker/docker-compose.yml` | 1台→3レプリカ |
| `mekhane/periskope/docker/settings.yml` | Google 無効化、30sタイムアウト、全エンジン |
| `mekhane/periskope/config.yaml` | 全制限パラメータ緩和 |
| `mekhane/periskope/searchers/searxng.py` | ラウンドロビン (複数URL) |
| `mekhane/periskope/engine.py` | 深度連動、min_iterations、max_results_by_depth |

## §5 次セッションのタスク {#sec_06_next}

| # | タスク | 優先度 |
|:--|:-------|:-------|
| 1 | **LLM カスケードリランク実装** | 🔴 今セッションで /ccl-plan → 実装 |
| 2 | gluetun VPN 分離 | 🟡 CAPTCHA 問題が出てから |
| 3 | Vertex AI Search カスタム App (Qiita/Zenn/CiNii) | 🟡 次回 |

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "SearXNG の設定はどうなっている？"
  - "Periskopē の検索パラメータの値は？"
  - "LLM リランクの設計方針は？"
  - "なぜ Google を無効化した？"
  - "Docker の構成は？"
answer_strategy: "§2 の DECISION を直接引用。数値は config.yaml の値。"
confidence_notes: "全て実装・テスト済み。Docker 3台 HTTP 200 確認。"
related_roms: []
-->
