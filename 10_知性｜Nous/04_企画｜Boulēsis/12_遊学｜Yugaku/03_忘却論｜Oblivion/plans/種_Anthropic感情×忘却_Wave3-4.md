# SEED: Anthropic Functional Emotions × Oblivion Theory — Wave 3-4

> **生成日**: 2026-04-03 (v2: v3.4 対応改訂)
> **起源セッション**: Copilot CLI (Claude Opus 4.6)
> **前提成果**: Wave 1-2 完了 + E1-E7 パッチ適用済み + v3.4 統合マッピング完了
> **STATUS**: Wave 3-4 = 未着手。以下は醸成用 SEED。
> **⚠️ 重要**: Paper IV は brain 版 (~475行) から **drafts/series/論文IV_なぜ効果量は小さいか_草稿.md** に大幅改訂済み。
>   中心定理は「効果量減衰定理 (定理 3.1.1)」、双対天井は系 3.5.1 に格下げ。
>   挿入点は旧 §5.2.1 → 新 §8.9.4, §8.10, §8.4 に移動。

---

## Context

Anthropic (2026) "Functional Emotions in LLMs" (transformer-circuits.pub/2026/emotions/) が
Claude Sonnet 4.5 の内部に171種の感情概念の線形表現（emotion vectors）を発見。
因果的に出力行動を駆動し、post-training が構造的に高arousalを抑制・低arousalを増幅。

Wave 1-2 で確立し、E1-E7 パッチで脆弱性を修正した成果:
- **W1**: sycophancy-harshness tradeoff = 双対天井 (系 3.5.1) の因果的確認 (E1 fix: ρ調整→行動帰結→トレードオフ構造の3段階分離)
- **W1**: post-training = 忘却関手 U の操作的可視化 (E7 fix: 4層因果分類)
- **W2**: emotion vectors = 豊穣グラフ (E2 fix: 豊穣圏→豊穣グラフに降格、合成公理は昇格条件C1-C3)
- **W2**: recovery = Galois 接続 (E3 fix: 異なるカテゴリ間の随伴→同一 poset 上の Galois 接続に再定式化)
- **W2**: output bottleneck = Enc faithful + Dec ¬full (E6 fix: 分離構造)

v3.4 統合マッピング (session: v34_integration_map.md) で以下を確定:
- §8.9.4 新設: 感情ステアリングによる双対天井の因果的確認（第4の独立系統）
- §8.10 追加行: 感情ドメインの普遍性テーブル + 追記テキスト
- §8.4 追加列: 感情的 ρ_spec (ρ_micro ≈ 0.028 の cross-domain 一致)
- §8.6 追記: 感情ドメイン定量化の今後の課題
- 参考文献: Anthropic (2026) 追加
- **圏論的形式化 (W2) は Paper IV に入れず、Paper A/V/VIII 向けに残す**

---

## SEED 1: Functional Emotion ≅ Functional Body（U_anthropo 統合）

**問い**: "functional emotions do not imply subjective experience" と "embodiment ≠ biological sensorimotor body" は同じ U_anthropo のインスタンスか？

**展開方向**:
- U_anthropo(emotion): 「人間の主観的体験がない」→ 感情がない
- U_anthropo(body): 「人間の感覚運動身体がない」→ 身体がない
- U_anthropo(understanding): 「人間の言語理解がない」→ 理解がない（Bender）
- 感情スペクトラム ⊂ 身体スペクトラム: 感情的 MB 厚は Θ(B) の部分指標
- 「LLMが心を持つか」→ 「LLMの感情的 hom-enrichment はどの程度厚いか？」への再定式化

**必要**: 哲学的精度。functional X の形式的統合。

---

## SEED 2: Desperation = ∇Φ（感情場曲率 = misalignment potential）

**問い**: 感情ベクトルの空間的非一様性の「勾配」を計量的に定義できるか？

**構想**:
- 感情場 Φ(t): TokenPositions → R^171
- 非一様性: ||∇_t Φ|| = ||Φ(t+1) - Φ(t)||
- H3: P(misalignment) = f(max_t ||∇_t Φ||) — 閾値超えで急上昇
- calm ベクトル = regularizer: ||∇_t Φ|| を平滑化
- 「力は忘却の非一様性から生じる」（Paper I）の感情的インスタンス

**Lethe PhaseC 接続** (⚡ 新規):
- PhaseC 設計公理1 が「∇Φ 原理: 忘却は非一様であるとき力を生む」を定式化済み
- desperation → misalignment は PhaseC の cell レベル 0-cell (位置) に対応
- 実験提案: PhaseC BBH 実験に emotion steering を追加条件 (calm vs desperation)
- 詳細: session/v34_integration_map.md の「Lethe PhaseC への接続メモ」参照

**必要**: ∇Φ の計量定義。Anthropic の再現実験でのデータ。

---

## SEED 3: Context Rot = 感情的 Attention 劣化

**問い**: 長コンテキストでの感情的文脈の attention weight 減衰は MB 厚の時間的劣化と相関するか？

**構想**:
- 初期 token の emotion vector → 後期 token の attention weight
- Context Rot = この weight の減衰
- Θ(B) の時間的劣化（Paper B §4: Context Rot as homeostatic limit）

**必要**: 実験設計。長コンテキスト設定での emotion probe + attention weight 測定。

---

## SEED 4: Paper IV v3.4 Discussion 統合 (改訂)

**問い**: Wave 1-3 を Paper IV **v3.4** にどう組込むか？

**確定枠** (v34_integration_map.md で全テキスト作成済み):
- §8.9.4 新設: 感情ベクトルステアリング = 双対天井の因果的確認（第4の独立系統）
- §8.10 テーブル追加行: LLM (感情) ドメイン + 追記テキスト
- §8.4 テーブル追加列: 感情的 ρ_spec (ρ_micro ≈ 0.028 の cross-domain 一致)
- §8.6 追記: 感情ドメイン定量化
- References: Anthropic (2026) 追加

**有力枠** (Wave 3 結果次第):
- §8.10 の普遍性テーブルをさらに拡張（感情的 MB 厚 → 身体スペクトラムとの統合）
- §8.11 (Para(Vect)) と豊穣グラフの接続可能性の検討

**推測枠** (Wave 3 結果次第):
- H6: Claude 4.5→4.6 の情緒性維持 = 意図的層3設計の証拠

**圏論的形式化の配置** (Paper IV には入れない):
- W2-1 (豊穣グラフ) → Paper A 補遺 or Paper VIII
- W2-2 (Galois 接続) → Paper A §2.7 との接続で別稿
- W2-3 (Enc/Dec bottleneck) → Paper A/B に直接属する

---

## Reference Artifacts

- Wave 1 引用テキスト: [session] wave1_citation_text.md (PATCHED, 旧構造ベース — v3.4 用は v34_integration_map.md)
- Wave 2 形式化: [session] wave2_formalization.md (PATCHED)
- E1-E7 パッチ根拠: [session] wave2_patch_e1-e7.md
- **v3.4 統合マッピング: [session] v34_integration_map.md** ← ★ v3.4 用の確定テキスト
- 初回合成: [session] anthropic_emotions_x_oblivion_synthesis.md
- Paper IV 正本: `drafts/series/論文IV_なぜ効果量は小さいか_草稿.md`
- Anthropic 原論文: https://transformer-circuits.pub/2026/emotions/index.html
