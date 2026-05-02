# A5.4: GUI/Web エージェント Action Grounding — HGK 翻訳メモ

> **出典**: GUI-Libra (ASFT), World-Model Augmented Web Agents
> **パプくんレポート**: A5.4
> **ステータス**: 参考情報 (KI) — 直接適用不可

---

## 原提言の要旨

### GUI-Libra: Action-aware SFT

- reasoning token と action/grounding token を区別
- action token に高い重みを与える ASFT (action-aware SFT) で、長い CoT が grounding 精度を悪化させる問題を緩和

### World-Model Augmented Web Agents

- LLM が提案するアクション候補を world-model が評価・絞り込み
- 実行前に「環境と整合的か」を検証

## HGK への含意

これらは code ツールや REST API 呼び出しにも類推でき、以下の設計原則を示唆する:

1. **ツール呼び出しをそのまま信用せず、別モジュールで検証・補正する** → HGK の P4 ペンディング検出はこの原則の部分的実装
2. **action token を重視する学習** → HGK では学習不可だが、dispatch 出力の構造で「アクション部分を視覚的に際立たせる」ことで代替 (tool-required 判定セクション)

## 直接適用不可の理由

- ASFT は SFT (教師あり微調整) を前提としており、API 利用の Claude/Gemini には適用不可
- World-model は独自の環境エミュレータを要求し、HGK のスコープ外
- ただし、**「検証→補正」の設計パターン** 自体は P4 + check_pending_dispatches で既に翻訳済み
