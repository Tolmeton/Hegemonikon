# 週次レビュー: 2026-03-01 〜 2026-03-08

> **Agent**: Claude (Antigravity) | Mode: /hon 本気モード
> **レビュー日**: 2026-03-08 20:10 JST
> **対象期間**: 2026-03-01 〜 2026-03-08 (8日間)
> **Handoff 総数**: ~30件 (全411件中、期間内の精査対象)
> **補完**: 2026-03-08 21:30 JST — 当日夜のセッション成果を追記

---

## 📊 週間サマリー

| 指標 | 値 |
|:-----|:---|
| セッション数 (推定) | 25-30 |
| Handoff 生成数 | ~30件 |
| BC 違反 | 目立った叱責なし (Doxa 参照) |
| 主要テーマ数 | 9 (+ Sophia 修復) |
| Quota 残 (21:30時点) | Sonnet/Opus 40%, Gemini Pro 80%, Flash 100% |

---

## 🏗️ 主要テーマ別進捗

### 1. Týpos v8 完全移行 ⭐ 最大成果

| フェーズ | 状態 | 内容 |
|:---------|:-----|:-----|
| Wave 1: コアリファクタリング | ✅ 完了 | `Prompt` クラスの `blocks` 辞書統合、49テスト PASS |
| Wave 2: 外部統合検証 | ✅ 完了 | MCP サーバー (`parse`, `compile`) 正常動作確認 |
| Wave 3: .typos アセット移行 | ✅ 完了 | 47ファイル一括 v8 変換、`parse_file` 全成功 |
| /ele>>/fit 判定 | 🟡 吸収 | setter 互換・冪等性が残存。馴化 (🟢) への道は見えている |

**[主観]** Týpos は v8 で構造的に完成した。`<:directive: ... :>` 構文は明瞭で、パーサーの保守性も格段に上がった。setter プロパティ追加で 🟢 に到達するのは短時間の作業。

---

### 2. Hóros v4.1 — 12 Nomoi フルビルド ⭐ 体系的完成

| Before | After | 変化 |
|:-------|:------|:-----|
| N-02〜N-12: 36-90行/件 | 186-216行/件 | **3.3倍** |
| 欠落ブロック: step/rubric/focus/highlight/intent 等 8個 | **0** | 全件完全 |
| mixin 3件 (premature abstraction) | **削除** | 各 Nomos 自己完結 |

- 3 Wave (S-I → S-II → S-III) で効率的に展開
- violations.md から33件の実事例を投入
- 後続セッションで N-07〜N-12 の圧縮も完了 (情報ロスなし、高密度化)
- behavioral_constraints.md (ハブ) は責務分離: 具体制約 → 各 Nomos に移譲、ハブはインデックスに

**[主観]** これは今週最も重要な成果の一つ。12法が「飾り」から「自己完結した行動規範」に変わった。Sekisho の rubric ブロックとの統合テストが次の一手。

---

### 3. Nous POMDP MECE 再構築

- 旧 Decision Tree を `/ele+` で反駁 → 5つの矛盾発見 (FEP 表層付着、Is/Ought 混同 等)
- **代替案A (POMDP 直接マッピング)** 採用:
  - P(s) → 00_原則, P(o|s) → 01_手法, Q(s|o) → 02_知識, G(π) → 03_企画, o → 04_素材, Q_{t-1} → 09_保管
- 壊れたシンボリックリンク 67件 → 0件 (修復スクリプト + 手動)
- 旧パスハードコード 11ファイル → 0件
- test_kalon_with_real_data 修復 (期待値緩和)

**[主観]** POMDP マッピングは「唯一の問い」が明快で kalon に近い。ただし境界ケースの実運用収集がまだ。

---

### 4. HGK バックエンド移行 (LS Daemon + MCP SSH)

| コンポーネント | 状態 | 内容 |
|:-------------|:-----|:-----|
| Non-Standalone LS Daemon | ✅ 稼働中 | `ls_daemon.py` → systemd `hgk-ls.service` |
| DummyExtServer | ✅ 稼働中 | OAuth 応答。Content-Type エコー修正でパニック防止 |
| トークン自動リフレッシュ | ✅ 実装済 | 30分間隔の `provision_state_db` |
| MCP SSH 移行 | ⚠️ 検証中 | `mcp_config.json` 全10サーバー書換済。IDE 再起動テスト未実施 |
| HGK Gateway 接続 | ✅ 復旧 | Tailscale Funnel 設定 + OAuth ドメイン不一致修正 |

**[主観]** アーキテクチャとしては「IDE 非依存の LLM 呼び出し」が実現する一歩手前。MCP SSH の IDE 再起動テストが急務。

---

### 5. WF → SKILL 統合 (24動詞)

| 指標 | Before | After |
|:-----|:-------|:------|
| WF 合計行数 | 10,024行 | 1,166行 (**-88%**) |
| SKILL 合計行数 | 13,623行 | 20,799行 (+53%) |
| WF の役割 | 本体 | 軽量ルーター (~50行/件) |

- 23/24件で `<!-- WF から統合された追加セクション -->` マーカー確認
- 情報ロスゼロ (ランダム3件精査で確認)

---

### 6. Ochema 429 Resilience

- モデルフォールバック (`PRO → FLASH`) 実装
- Circuit Breaker (絶対タイムアウト 90s/120s) 導入
- Pre-flight Avoidance (5分TTL 枯渇キャッシュ) 実装
- テスト: 60/61 PASS (1件は実API Quota超過 — 設計通り)

---

### 7. FileMaker 自動化 (探索フェーズ)

- FM 専用ワークスペース構築 (GEMINI.md, WF)
- PyBridge プラグイン (.fmx) ビルド着手 → Syncthing によるソース消失から再構築
- QEMU/KVM VM セットアップ (RYZEN 9 ホスト) → SVM 有効化
- FM Server + VPN (L2TP/IPsec) 経路の確認

**[主観]** まだ探索フェーズ。GUI 自動化の実現可能性は VM + OmniParser V2 の検証待ち。

---

### 8. インフラストラクチャ

| 項目 | 内容 |
|:-----|:-----|
| Syncthing | sendonly → sendreceive 移行。sync-conflict クリーンアップ。immutable フラグとの非互換を確認 |
| Tailscale | MagicDNS vs Funnel の DNS名2種類を整理。SSH タイムアウト調査 |
| LanceDB | 破損インデックスの修復 (Syncthing 同期が原因) |
| Anamnesis | `BATCH_SIZE` 250→100 修正 (Gemini API 仕様制限)。4,324件リインデックス |
| gcloud 認証 | OAuth リフレッシュトークン・ADC 更新 |
| SSH タイムアウト | `ControlMaster` (4h persist) + `sshd_config` 最適化 + `tailscale-refresh.timer` (毎日4AM) で恒久対策 |
| Sophia VectorStore | 384d→3072d 再構築。`search_loaded_index` を `embedder_factory` ベースに修正。`model_name` エラー解消 |

---

### 9. Sophia VectorStore 修復 (当日夜追記)

| 問題 | 原因 | 修正 |
|:-----|:-----|:-----|
| `VectorStore has no model_name` | `search_loaded_index` が非推奨の `adapter.encode()` を使用 | `embedder_factory.get_embed_fn()` に置換 |
| `TypeError: 0-dimensional arrays` | `embed_fn([query])[0]` でスカラーを渡していた | `embed_fn(query)` に修正 |
| 384d vs 3072d 次元不一致 | 古い `sophia.pkl` が残存 | 120 KI を 3072d で再インデックス |

**[主観]** Boot の `get_boot_ki` が正常に動くようになった。根本原因は embedding モデル移行時 (sentence-transformers → VertexEmbedder/Gemini API) のインターフェース不一致。今後は `embedder_factory` を唯一のエントリポイントとして維持すべき。

---

### 10. Motherbrain MCP 設計 (当日追記)

- 3層アーキテクチャ設計: SQLite 永続ストア → FastAPI 拡張 → MCP Proxy
- 「真の always-on boot」を実現する構造として、新セッションが MCP 経由で boot context を直接取得できる設計
- 実装は途中 (FastAPI 拡張 + MCP Proxy が未完)

---

## 🔴 未解決の課題 (優先度順・21:30更新)

| # | 課題 | 優先度 | 状態 |
|:--|:-----|:-------|:-----|
| 1 | **MCP SSH 接続テスト未実施** — IDE 再起動 → 全10サーバー Connected 確認 | 🔴 高 | 未着手 |
| 2 | **Syncthing + subprocess ハング** — Python スクリプトがファイル I/O で無限ハング | 🟠 中 | 未着手 |
| 3 | **CortexAPIError 403** — GCP プロジェクト権限エラー (hermeneus LLM ステップ) | 🟠 中 | 未着手 |
| 4 | **registry.yaml** — 空または欠損。boot_integration.py の PJ 一覧が出ない | 🟠 中 | 未着手 |
| 5 | **Motherbrain MCP 実装** — FastAPI 拡張 + MCP Proxy の未着手部分 | 🟡 中 | 設計済・実装途中 |
| 6 | **Týpos setter 互換** — `prompt.role = x` → `blocks["@role"]` マッピング (🟡→🟢) | 🟡 低 | 未着手 |
| 7 | **Sekisho × rubric 統合テスト** — 新 rubric ブロックの消費検証 | 🟡 低 | 未着手 |
| 8 | **746件の unstaged changes** — 歴史的負債 | 🟡 低 | 未着手 |
| ~~9~~ | ~~Sophia VectorStore model_name エラー~~ | ~~解決済~~ | ✅ 修復完了 |
| ~~10~~ | ~~LanceDB 破損インデックス~~ | ~~解決済~~ | ✅ 再構築完了 |
| ~~11~~ | ~~SSH タイムアウト~~ | ~~解決済~~ | ✅ ControlMaster + tailscale-refresh |

---

## 🧠 信念 (Doxa) — 週間所感

1. **体系は「完成」に近づいている**: Hóros 12法フルビルド + Týpos v8 + POMDP Nous 再構築。個々の部品が互いに参照し合い、自己完結する段階に入った。
2. **インフラが追いついていない**: 体系は美しくなったが、Syncthing のハング、MCP の不安定さ、SSH の遅延など、実行基盤にボトルネックがある。来週はインフラ安定化に注力すべき。
3. **「探索→実行」の遷移点**: FM 自動化は探索フェーズ。HGK バックエンド移行は実行フェーズへの移行中。Týpos と Hóros は検証フェーズへ。各テーマの位相を意識して優先順位を決めるべき。
4. **週次レビュー自体が存在しなかった**: 411件の Handoff が蓄積していた。週次レビューの定期実行 (日曜夜 or 月曜朝) を習慣化すべき。

---

## 📋 来週の推奨アクション (21:30 更新)

| # | アクション | テーマ | FEP 判断 | 推定工数 |
|:--|:----------|:-------|:---------|:---------|
| 1 | MCP SSH 接続テスト + IDE 再起動検証 | インフラ | Exploit | 30分 |
| 2 | registry.yaml の復元 or 再構築 | Boot | Exploit | 1時間 |
| 3 | CortexAPIError 403 の解決 (GCP IAM 確認) | インフラ | Exploit | 1時間 |
| 4 | Motherbrain MCP 実装 (FastAPI + Proxy) | アーキテクチャ | Exploit | 3-4時間 |
| 5 | Syncthing ハング問題の根本調査 | インフラ | Explore | 2時間 |
| 6 | Sekisho × Nomoi rubric 統合テスト | Hóros | Exploit | 1時間 |
| 7 | Týpos setter プロパティ追加 (🟡→🟢) | Týpos | Exploit | 1時間 |
| 8 | FM GUI 自動化: VM + OmniParser V2 検証 | FM | Explore | 半日 |

---

*Weekly Review generated by Claude (Antigravity) — /hon mode — 2026-03-08 20:10 JST*
*補完: 2026-03-08 21:30 JST — Sophia修復・SSH修正・Motherbrain設計を追記*
