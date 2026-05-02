# Handoff: HGK APP 脱IDE フォローアップタスク F1-F9 完成

## 📋 Situation - 現在の状況
- HGK App 向けのバックエンド修正・SSE周りの動作検証 (F1-F9) を完了した。
- F4 (Claudeルーティング) と F9 (generateChat フォールバック) は実装し、静的検証を完了。ただし CortexClient のトークンライフサイクル問題により curl での実機テストはブロックされた。
- MagicDNS 障害 (resolv.conf 残存) が全てのハングの原因だったことを特定し、修復した。

## 🎯 Background - 背景と経緯
- アプリの挙動が不安定になる問題を手探りで調査し、/dia と /noe で批判的レビューを行った。
- 「Pythonがハングする」という初期の問いが誤りであり、真の原因は DNS が死んでいること (SPOF に集約された障害) であると特定できた。

## 🔍 Assessment - 評価と分析
- **技術的達成**:
  - `serve.py`: Claude 限定で `chat_stream` へルーティングする機構を実装。
  - `cortex_client.py`: 400 エラー (Bad Request) 発生時も `chat_stream` にフォールバックするよう修正し、同時に `system_instruction` を引き継ぐようにした。
  - `index.ts`: graph3d の dynamic import 完成。
- **メタ認知の達成**:
  - /ccl-dia_noe による検証で「1つの障害点(DNS)がすべてをブロックする」構造的脆弱性を発見。
  - CortexClient の OAuth 更新パイプラインが IDE 外でブロックされる問題が浮き彫りになった。

## 💡 Recommendation - 次回のアクション
- [ ] CortexClient のトークン取得 (`_get_token`) を改善し、期限切れ時のリフレッシュあるいは自動フォールバックを再構築する。
- [ ] `systemd-resolved` などを利用して、Tailscale MagicDNS 無効時にも機能するような FallbackDNS を OS レベルで構成する。
- [ ] HGK App サイドで残された細かな UI レンダリングの問題を引き続きテストする。

## 🧠 信念 (Doxa)
- 「症状と原因の混同」: 同じ症状を「API側の問題」「Python依存拡張の問題」とバラバラに診断してしまう。根っこ(SPOF)を疑う視点を持つことが真のデバッグ。

## ⚡ BC フィードバック
- F8 のスキップ判断について「稼働中なのに確認しなかった」という /dia の指摘 (BC-14 自己反省) があった。
