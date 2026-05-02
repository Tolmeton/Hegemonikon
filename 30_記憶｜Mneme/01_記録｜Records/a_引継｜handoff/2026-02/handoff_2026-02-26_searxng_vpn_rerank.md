# Handoff: SearXNG VPN Integration + LLM Reranking — 2026-02-26

## セッション概要

SearXNG × Surfshark VPN 統合 (Phase 1) を完了し、LLM リランキング強化 (Phase 2) のベンチマークを開始した。

## 完了した作業

### Phase 1: VPN インフラ ✅

- Gluetun 3 台 (JP/CH/NL) + SearXNG 3 台を Docker Compose で構築
- VPN IP 分散を実証:
  - gluetun-1: `138.199.22.140` (JP)
  - gluetun-2: `156.146.62.50` (CH)  
  - gluetun-3: `212.102.35.205` (NL)
- 9 時間以上の安定稼働を確認
- Coverage 1.00 (IP バン回避を実証)

### depends_on 自動起動修正 ✅

- `condition: service_healthy` → `service_started` に変更
- `docker compose up -d` 一発起動を確認

### 変更ファイル

| ファイル | 変更内容 |
|:---------|:---------|
| `mekhane/periskope/docker/docker-compose.yml` | Gluetun 3台追加、healthcheck を `127.0.0.1:9999` に修正、depends_on を `service_started` に変更 |
| `mekhane/periskope/docker/.env` | Surfshark WireGuard 認証情報 (gitignore 済み) |
| `mekhane/periskope/docker/.env.example` | テンプレート |

## 進行中の作業

### LLM リランキングベンチマーク 🔄

- PID `1782430` で `/tmp/rerank_benchmark.log` に出力中
- L2 × 3 クエリ × 2 パス (llm_rerank=True/False)
- API レート制限 (`rairaixoxoxo`) が 60s クールダウンで発生中
- 完了まで 30-40 分の見込み（10:12 時点で進行中）

**確認コマンド**:

```bash
pgrep -f rerank_benchmark && echo "RUNNING" || echo "DONE"
grep -E 'score=|COMPARISON|AVERAGE' /tmp/rerank_benchmark.log
cat /tmp/rerank_benchmark.json  # 完了後
```

## 未着手の作業 (Phase 2 計画)

| # | ステップ | 内容 |
|:--|:---------|:-----|
| 1 | ベンチマーク | ⏳ 実行中 (上記) |
| 2 | プロンプト改良 | ルブリック強化: SNS/EC ペナルティ条件追加 |
| 3 | ブラックリスト縮小 | メディア系 (medium, note 等) を除外しリランキングで代替 |
| 4 | ドキュメント | walkthrough.md に VPN + リランキング設計概要 |
| 5 | テスト追加 | 既存テスト確認 + E2E テスト |

## Creator の方針決定

- **Google 検索**: 不要
- **レイテンシ**: 速度より質を優先
- **ノイズ対策**: LLM リランキング (ブラックリストは「美しくない」)
- **ブラックリスト**: 既存 28 ドメインあり → リランキングで品質担保後に段階的に縮小

## 既存実装の発見

LLM リランカー (`llm_reranker.py`, 291行) は **既にフル実装済み**:

- 5 次元ルブリック (Relevance, Specificity, Authority, Freshness, Completeness)
- 2 段カスケード (Flash → Pro)
- Cohere フォールバック
- `config.yaml` で `enabled: true`

→ 「新規実装」ではなく「検証・強化」がフォーカス

## 次セッションの最初の行動

1. ベンチマーク結果を確認 (`/tmp/rerank_benchmark.json`)
2. 結果に基づいてプロンプト改良 (Step 2)
3. ブラックリスト縮小実験 (Step 3)
