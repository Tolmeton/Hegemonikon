# Handoff: Cortex API LS Proxy 攻略完了 — セッション 3 (PM)

> **日時**: 2026-02-13 19:48-20:18 JST
> **Agent**: Claude (Antigravity)
> **テーマ**: LS API を Cortex プロキシとして LLM 呼び出し成功

---

## セッションの目的

Cortex API への直接アクセス (Token 傍受) が 28 ベクトルで失敗した後、
**LS 自体をプロキシとして使う代替ルート**を発見し、完全成功させる。

---

## 主要成果

### ✅ 完全成功

| 成果 | 詳細 |
|:-----|:-----|
| **LS API 経由 LLM 呼出成功** | 620KB trajectory, 25 steps, Gemini 3 Pro thinking 完全取得 |
| **4-Step フロー確立** | GetCascadeModelConfigData → StartCascade → SendUserCascadeMessage → GetCascadeTrajectory |
| **モデル一覧取得** | Gemini 3 Pro (M7, quota 100%), Gemini 3 Flash (M18, quota 100%) |
| **正しいリクエスト構造発見** | metadata + trajectoryType:17 + requestedModel:{model:"MODEL_PLACEHOLDER_M7"} |
| **ドキュメント v8 更新** | ls-standalone-reference.md に 6 セクション (18.15-18.20) + 攻略ベクトル #29-#37 追記 |

### 発見した鍵 (9 回の試行錯誤)

| # | 発見 | 重要度 |
|:--|:-----|:------|
| 1 | CSRF ヘッダー名 = `X-Codeium-Csrf-Token` | 🔑 認証の鍵 |
| 2 | ポート = `ss -tlnp` で動的取得 | 🔧 インフラ |
| 3 | `metadata` + `trajectoryType: 17` 必須 | 🔑 Trajectory 生成の鍵 |
| 4 | `requestedModel` = proto ModelOrAlias 型 | 🔑 LLM 起動の鍵 |
| 5 | 外部ターミナルから呼ぶ (デッドロック回避) | ⚠️ 運用制約 |

---

## 学びの永続化 (/ccl-learn)

| # | 信念 | 確信度 |
|:--|:-----|:------|
| B1 | 同じ層で失敗が反復したら層を変える (Function 公理) | 90% |
| B2 | エラーメッセージは最大の教師 — 意図的にエラーを発生させる戦略 | 95% |
| B3 | 難読化 JS からメソッド名/enum/proto 構造は復元可能 | 95% |
| B4 | IDE 内→外部ターミナル切替でデッドロック回避 | 75% |
| B5 | proto3 enum は文字列でなく enum 名 or 数値で渡す | 95% |

---

## 参照ドキュメント

- [ls-standalone-reference.md v8](file:///home/makaron8426/Sync/oikos/hegemonikon/mekhane/ochema/docs/ls-standalone-reference.md) — §18.15-18.20
- `/tmp/cortex_proxy.sh` — v6 (完全動作版)
- `/tmp/cortex_read.sh` — Trajectory 読み取りスクリプト
- `/tmp/cortex_trajectory_full.json` — 620KB の生 trajectory データ

---

## 残タスク

1. `antigravity_client.py` に v8 フロー (metadata + requestedModel) を統合
2. Ochēma MCP Server でモデル選択パラメータ化
3. StreamCascadeReactiveUpdates でリアルタイム応答
4. (optional) LS ラッパー + mitmdump で LS 内部 ya29 取得

---

*Handoff generated: 2026-02-13 20:18 JST*
