# VISION: Kyvernetes CDP 直接化

> **ステータス**: 将来計画 (Kube が成熟した後)
> **日付**: 2026-02-24

## 現状

Kube は Playwright Python ライブラリをブラウザ操作層として使用。
`playwright_bridge.py` で抽象化し、将来の差し替えに備えている。

## ビジョン

Playwright (Microsoft) への依存を排除し、CDP (Chrome DevTools Protocol) を直接操作する
最小・最純粋なブラウザドライバーを自作する。

### なぜ将来か

- Playwright は十分に成熟しており、今は自作のコストが見合わない
- Kube の OODA ループと LLM 統合を先に完成させるべき
- CDP 直接化は Kube の操作パターンが安定してから実施する方が効率的

### 移行条件

1. Kube の OODA ループが安定稼動している
2. Playwright の抽象化が不要な機能を含みすぎて邪魔になった
3. または Playwright の破壊的変更で migration コストが発生した

### CDP 直接化の利点

- バイナリ依存ゼロ (websockets のみ)
- Accessibility Tree の取得を自分で制御
- ブラウザプロセスのライフサイクルを完全管理
- HGK の設計思想 (最小・自律・制御可能) に合致

---

*VISION registered: 2026-02-24*
