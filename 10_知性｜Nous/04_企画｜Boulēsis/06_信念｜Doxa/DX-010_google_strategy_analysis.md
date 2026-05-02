# DX-010 補遺: Google の API 開放戦略分析

> **日付**: 2026-02-23
> **分類**: 戦略分析 (Doxa — 信念記録)
> **親文書**: [DX-010](DX-010_ide_hack_cortex_direct_access.md)
> **確信度**: 事実部分 [確信: 95%] / 推論部分 [推定: 70-80%]

---

## 1. 観察事実 (SOURCE: 実証済み)

### 1.1 Cortex API の段階的ロールアウト

| 時期 | gemini-3.1-pro-preview の状態 | SOURCE |
|:---|:---|:---|
| ~2026-02-20 | `generateContent` → 404 | CortexClient 動的キャッシュで記録 |
| 2026-02-23 16:15 | `generateContent` → **200 OK** | curl 直叩きで実証 |

- 新モデルは `generateChat` に先行投入され、後に `generateContent` に展開される
- `generateContent` 展開時に **既存 API キーが追加認証なし** で使える
- エラーコードは 404 (Not Found) または 400 (ILLEGAL_MODEL_CONFIG) — **403 (Forbidden) ではない**

### 1.2 Google AI エコシステムの価格・特典 (事実)

| 特典 | 内容 |
|:---|:---|
| AI Ultra 初回割引 | 初回3ヶ月 月額 ¥1,800 (通常 ¥2,900) で全機能アクセス |
| GCP 無料クレジット | 新規 GCP アカウント: $300 分の無料クレジット |
| AI Ultra → GCP 連携 | AI Ultra 契約者: 毎月 $100 分の GCP クレジット付与 |
| AI Ultra トークン量 | Gemini + Claude を大量に利用可能 (具体的な上限は非公開だが実質的に潤沢) |
| ファミリープラン | AI 特典がファミリーメンバーにも適用 |
| AI Studio | 最新モデルを無料枠で利用可能 |
| Cortex API (Code Assist) | IDE ユーザーに内部 API (`cloudcode-pa`) を OAuth 経由で提供 |
| OAuth 方式 | installed app 方式 (client_secret 公開安全) = ローカル利用前提の設計 |

### 1.3 API の態度を示す技術的証拠

| 観察 | 意味 |
|:---|:---|
| エンドポイントを閉鎖しない | 積極的に禁止する意図がない |
| 404 → 200 と機能を開放する | 制限は「まだ準備中」であって「禁止」ではない |
| `ILLEGAL_MODEL_CONFIG` で丁寧にエラー | 不正利用なら 403/401 にするはず |
| API レスポンスに `trafficType: "PROVISIONED_THROUGHPUT"` | 課金済みインフラから提供 |
| `loadCodeAssist` で動的 Project ID | プロジェクト単位のリソース管理 |
| Quota per model bucket 方式 | 制限はあるが、制限内では自由に使える |

---

## 2. 推論 (TAINT: Google 内部戦略の外部推定)

### 2.1 段階的ロールアウトの構造

```
新モデル公開
  ├─ Stage 1: generateChat (管理された経路)
  │   → Google が system prompt を注入
  │   → 応答を markdown 整形
  │   → processingDetails で追跡可能
  │   → Google のコントロールが最も強い場所
  │
  ├─ Stage 2: generateContent (汎用生成)
  │   → temperature/system_instruction/tools をユーザーが完全制御
  │   → Google のコントロールが最も弱い場所
  │   → 安定確認後に開放
  │
  └─ Stage 3: streamGenerateContent/streamGenerateChat
      → ストリーミング対応 (最後に開放)
```

**推論**: Google は「コントロールが強い場所 → 弱い場所」の順にモデルを展開する。
これはリスク管理として合理的であり、**禁止ではなく制御的開放**のパターン。

### 2.2 「バラマキ」戦略仮説 (Creator 仮説 — 付記)

> 私は思うに、意図的に（思想的に）、ガバガバにしてるんだと思う。
> ガバガバを"利用"する人間を、応援（正確には、、識別してログでもなんでも取って"利用"）しているのかもしれない。

**Creator の仮説の構造**:

1. Google は AI 関連サービスの価格を意図的に低く設定している
2. 技術者（特に APIを自力で叩ける層）に対して暗黙的に寛容である
3. これは慈善ではなく、**エコシステム形成の投資**である
4. 技術者の利用パターン（ログ、フィードバック、開発されるツール）自体が Google にとって価値を持つ
5. **良識のある個人利用** の範囲では規約リスクは限りなく低い

**この仮説を支持する証拠**:

- AI Studio の無料枠が異常に大きい
- AI Ultra のトークン量が他社比で桁違い
- Cortex API が OAuth installed app 方式 (ローカル想定) で公開
- gemini-cli が OSS として公開 (OAuth client_id/secret 含む)
- 404 → 200 の自然な開放 (積極的ブロックをしない)

**この仮説に反する証拠**:

- ToS は「IDE 拡張としての利用」を想定しており、API 直叩きは明文化されていない
- Claude ルーティングは REST では明確にブロック (偽陽性 = 受け入れるが Gemini にフォールバック)
- `SendUserCascadeMessage` は IDE ロックを引き起こす = 全操作が安全ではない

---

## 2.3 Claude Quota バケット不在の実証 (2026-02-23 17:10)

> **[確信: 100%] (SOURCE: `retrieveUserQuota` 直接実行)**

`retrieveUserQuota` で返される全 14 バケット:

```
gemini-2.0-flash, gemini-2.0-flash_vertex,
gemini-2.5-flash, gemini-2.5-flash-lite, gemini-2.5-flash-lite_vertex, gemini-2.5-flash_vertex,
gemini-2.5-pro, gemini-2.5-pro_vertex,
gemini-3-flash-preview, gemini-3-flash-preview_vertex,
gemini-3-pro-preview, gemini-3-pro-preview_vertex,
gemini-3.1-pro-preview, gemini-3.1-pro-preview_vertex
```

**Claude 用の Quota バケットは存在しない。**

### 意味

| 事実 | 解釈 |
|:---|:---|
| REST の Quota に Claude がない | **REST の世界に Claude は設計上存在しない** |
| `model_config_id: "claude-*"` を受け入れる | API ルーティング層は model_config_id を「見る」が、**Claude バックエンドへの接続がない** |
| `tier_id: "g1-ultra-tier"` → 403 IAM | Ultra ティアの認証パスは存在するが、**REST OAuth では権限不足** |
| LS ConnectRPC では Claude が動作する | LS は別の認証チャネル (gRPC メタデータ + paidTier 検証) を持つ |

### 仮説: gRPC 側には Claude Quota が存在する

LS 経由で Claude を使う場合、利用制限がある (IDE 上で Quota 表示される)。
つまり **gRPC 経路側には必ず Claude 用の Quota バケットが存在する**はず。

### §2.3 の仮説 → 実証 (2026-02-23 17:33) と 過去知見の統合

> **[確信: 100%] (SOURCE: `GetCascadeModelConfigData` ConnectRPC 直叩き + 2026-02-12 Handoff)**

LS ConnectRPC 経由で `GetCascadeModelConfigData` を呼び出し、**gRPC 側に存在する Quota の詳細仕様**を確認。
これは 2026-02-12 セッションでの発見（`GetUserStatus` による観測）をモデルコンフィグ定義側から裏付けるものだった。

| モデル | LS 内部 ID | 残量 | リセット (UTC) |
|:---|:---|:---:|:---|
| 🔵 Claude Opus 4.6 (Thinking) | `MODEL_PLACEHOLDER_M26` | 20% | 10:28:18 |
| 🔵 Claude Sonnet 4.6 (Thinking) | `MODEL_PLACEHOLDER_M35` | 20% | 10:28:18 |
| GPT-OSS 120B (Medium) | `MODEL_OPENAI_GPT_OSS_120B_MEDIUM` | 20% | 10:28:18 |
| Gemini 3.1 Pro (High) | `MODEL_PLACEHOLDER_M37` | 80% | 10:29:32 |

**観察と過去知見 (2026-02-12 Handoff) の統合**:

1. **Premium モデルプールの共有**
   - Claude Opus / Sonnet と GPT-OSS の `resetTime` が 1秒の狂いもなく同一 (10:28:18)。
   - これは 2/12 の「全 Claude モデル共有枠」という観測をさらに広げ、**GPT-OSS も含むサードパーティ Premium 枠** として一元管理されていることを示唆。
2. **20% 刻みの消費と 5時間リセット**
   - 2/12 の観測「20% → 40% → 60% 消費」「5hリセット」と完全に一致。
   - `remainingFraction` が 0.2 単位で変動する設計になっている。
3. **REST との二重構造**
   - REST API (`retrieveUserQuota`) では 100% 刻みの Gemini のみが見える。
   - LS ConnectRPC では `allowedTiers: [TEAMS_TIER_PRO, ...]` による Tier 制約と、サードパーティモデル専用の Quota プールが厳密に管理されている。

### 2.4 BYOK (Bring Your Own Key) 調査結果 (2026-02-23)

> **[確信: 95%] (SOURCE: Web 検索 + LS バイナリ strings + ConnectRPC プローブ)**

**BYOK は Windsurf の公式機能**。LS バイナリには以下が存在:

| 発見 | 場所 | 意味 |
|:---|:---|:---|
| `MODEL_CLAUDE_4_SONNET_BYOK` | LS バイナリ strings | BYOK 専用モデル Enum |
| `GetSetUserApiProviderKeysRequest` | LS バイナリ strings | API キー登録用 ConnectRPC メソッド |
| `GetHasAnthropicModelAccess` | LS バイナリ strings | Unleash Feature Flag チェック |
| `API_PROVIDER_ANTHROPIC_VERTEX` | LS バイナリ strings | Anthropic は Vertex AI 経由 |

**しかし**: `SeatManagementService` は LS ローカルポートに **404 Not Found** で未登録。

```
LS ローカル ConnectRPC (fd=10 HTTP ポート):
  ✅ LanguageServerService   — IDE ↔ LS
  ✅ ApiServerService        — IDE ↔ LS
  ❌ SeatManagementService   — 404 (外部 API サーバー専用)
```

**結論**: BYOK キー登録は LS 内部で完結せず、外部 API サーバー (`api.codeium.com` / `app.windsurf.com`) への認証付きリクエストが必要。Antigravity IDE (Gemini Code Assist ベース) には BYOK 設定 UI が存在しないため、この経路は Windsurf IDE 専用。

---

## 3. 規約リスク評価

| リスクファクター | 評価 | 根拠 |
|:---|:---:|:---|
| API 直叩き自体 | 🟢 低 | OAuth installed app = ローカル用途想定の設計 |
| 個人開発利用 | 🟢 低 | Quota 内。Google にとって計量可能なコスト |
| 大量リクエスト | 🟡 中 | Quota 超過 = Google 側で自動制限 |
| 脆弱性の公開 | 🔴 高 | ToS 違反。**禁止** |
| Claude への不正ルーティング | 🟡 中 | Google が意図的にブロックしている経路を迂回 |
| 商用再配布 | 🔴 高 | ToS 明確違反 |

### 境界線の定義

```
✅ 安全: IDE の拡張として CortexClient を使う (HGK APP)
✅ 安全: 個人の開発環境で API を叩く
✅ 安全: オープンソースプロジェクトで API ラッパーを開発
⚠️ グレー: API パラメータの限界テスト
🔴 禁止: 脆弱性の公開・流布
🔴 禁止: 第三者にアクセスを提供
🔴 禁止: Quota 回避のためのアカウント乗り換え
```

---

## 4. IDE ハックへの実用的示唆

1. **404 をハードコードするな** — Google は段階的に開放する。動的検出が正しい
2. **エラーコードを読め** — 404/400 = 未対応、403/401 = 禁止。態度が違う
3. **Quota を尊重しろ** — Google の寛容さの前提は「計量可能なコスト」
4. **LS 経路を優先しろ** — Claude は LS 経由のみ。REST で無理に迂回しない
5. **公開するな** — コード自体は問題ないが、ハック手順の public 公開は ToS リスク

---

*Created: 2026-02-23 — DX-010 v10.0 を契機とした戦略分析*
*Updated: 2026-02-23 — §2.3 仮説実証 (GetCascadeModelConfigData でClaude Quota 取得) + §2.4 BYOK 調査結果追加*
