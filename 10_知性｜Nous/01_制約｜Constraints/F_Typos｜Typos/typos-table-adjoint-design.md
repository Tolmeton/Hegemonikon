---
description: "Týpos テーブル随伴設計 — LLM の暗黙2D座標系に関する知見と設計決定"
---

```typos
#prompt typos-table-adjoint-design
#syntax: v8
#depth: L2

<:role: Týpos v8.1 テーブル随伴 (:: デリミタ) の設計根拠。
  LLM の暗黙2D座標系再構築メカニズムに基づく。:>

<:goal: デリミタ選定・構文設計・実装方針を MECE に記録する :>

<:constraints:
  - 根拠なき設計決定の禁止。全ての選択は「なぜこれか」を明示する
  - 実装前にパーサー (typos/ 内) の影響範囲を確認すること
/constraints:>

<:context:
  - [knowledge] §1 問題: Týpos [knowledge] タグは1次元リスト。
    多次元知識 (実体×属性) の表現に不向き。
    LLM は「テーブルが読みやすい」と報告したが、その認知的根拠が不明だった。

  - [knowledge] §2 発見: LLM は内部で暗黙の2D座標系を再構築する。
    Zhang et al. (2026) arXiv:2602.08548 — Mechanistic Analysis of Cell Location。
    Qwen/Llama の activation patching + linear probing で解明。
    3段階パイプライン:
      Stage 1 Semantic Binding (初期層 1-16): クエリ制約とヘッダの意味的紐づけ
      Stage 2 Coordinate Localization (中間層 17-23): デリミタを数えて暗黙座標系を構築
      Stage 3 Information Extraction (後期層 24+): セル値を出力位置に伝播
    列インデックスは線形部分空間に符号化。ベクトル演算 (加算・スケーリング) で操作可能。
    多セル検索時は同じ attention head をマルチプレクシング。

  - [knowledge] §3 デリミタの必要十分条件 (論文 §4.2 + C.4 + C.5 から演繹):
    C1 discrete: 1トークンとしてトークン化されること
    C2 consistent: 各行で同数のデリミタが出現すること
    C3 unique: データ内にデリミタと同じトークンが出現しないこと
    C4 format-invariant: MD (|) でも CSV (,) でも HTML (</td>) でも同一メカニズムが発動
    反証実験 (C.5): ランダム文字挿入→精度不変。パイプ挿入→72.6%→26.2%に壊滅。
    結論: LLM はトークン長も絶対位置も見ていない。デリミタを数えているだけ。

  - [knowledge] §4 デリミタ候補のトークン化検証 (tiktoken/GPT-4o):
    ✅ 1-token: | (id=91), :: (id=742), → (id=20216), · (id=5366)
    ❌ multi-token: ¦ (2t), ‖ (2t), ⊣ (2t)
    文中での融合: ' ::' → 1 token (id=8648), ' |' → 1 token (id=1022)

  - [knowledge] §5 トークン効率比較 (同一データの行):
    pipe_md (| S-I | ... |) → 21 tokens
    dcolon (S-I :: ...) → 19 tokens (-9.5%)
    :: がパイプより効率的な理由: MD テーブルは行頭/行末にも | が必要

  - [knowledge] §6 設計決定: :: を Týpos テーブルデリミタに採用
    根拠1: 1トークン (C1 充足)
    根拠2: Týpos の : 系構文 (<:role:>, <:goal:>) と一貫
    根拠3: データ内衝突リスクが | より低い (C3 充足)
    根拠4: トークン効率が | より良い
    根拠5: C.4 の format-invariance により :: も | と同等に暗黙座標系を構築
    ⚠️ 重要帰結: :: はそのまま LLM に渡しても座標系が発動する。
    compile 時の :: → | 変換は不要。:: のまま使えば十分。
    _compile_table は人間向け MD 変換のオプショナル機能として存在する。

  - [knowledge] §7 推奨使用法:
    :: デリミタのテーブルは [knowledge] 内に直接書く。<:table:> ブロック不要。
    例:
      原理 :: Aisthēsis :: Dianoia :: Ekphrasis :: Praxis
      S-I :: N-1 実体を読め :: N-2 不確実性を追跡 :: N-3 確信度を明示 :: N-4 不可逆前に確認
    <:table:> は、compiler を通す場合のオプショナルなセマンティックマーカー。
    compile 時: :: → MD パイプテーブルに変換 (v8_compiler._compile_table)

  - [knowledge] §8 FEP 的正当化:
    テーブルは「複数実体×複数属性」の直積空間の VFE 最小化構造。
    公理からは N 次元構造が演繹されるが、2D で止まるのは媒体制約 (テキスト = 1D) から。
    LLM は 1D 入力から内部で 2D を再構築する能力を持つ (§2)。
    → Týpos にテーブルを入れる合理性あり。ただし 3D 以上は将来課題。

  - [knowledge] §9 タスク状態:
    ✅ T1: tokenizer 変更不要 (既存パターンで kind="table" にパース済み)
    ✅ T2: v8_compiler.py に _compile_table 追加 (オプショナル, 4テスト PASS)
    ✅ T3: episteme-entity-map.md の12法を :: テーブルに変換
    ✅ T4: テスト完了 (block / nested / mismatch / empty)
    ⚪ T5: spec.md は v2 系で古い。v8.1 として更新するかは別途判断
/context:>
```
