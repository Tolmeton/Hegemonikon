# Handoff: Týpos v3 思想的基盤の導出

## セッション概要

- **日時**: 2026-02-19 18:00 - 23:40
- **目的**: Týpos (.prompt) の思想的基盤 (公理) を定義する
- **結果**: 思想「記述は必ず欠ける」を発見。10成分を射の構造から演繹。PHILOSOPHY.md v3.1 作成。

## 成果物

| ファイル | 状態 | 内容 |
|:--------|:-----|:-----|
| `typos/docs/PHILOSOPHY.md` | ✅ v3.1 | 思想的基盤。10成分。Kalon 原理。反証条件 |
| `typos/demo_v3.prompt` | ✅ 作成 | 10成分を全て使った実用的デモ |
| `implementation_plan.md` | ❌ 要書き直し | /dia+! で致命的欠陥6つ発見 |

## 思想の要点

> **「記述は必ず欠ける」**
>
> - 記述 = 信念分布の記号化 = 不可逆圧縮
> - 射の10成分: SOURCE, AUDIENCE, PURPOSE, CONTENT, STRUCTURE, PRECISION, RUBRIC, SCOPE, TEMPORALITY, COMPOSITION
> - 消えたものを @ ディレクティブで書き足す
> - どこまで書き足すかが Kalon (必要十分)

## 導出の経緯

1. /sop++ 三角検証: 「フォーマットでは精度は上がらない」→ compile パイプラインが価値
2. /noe+ 公理探求: 「表現とは射」は A≒a → Creator が繰り返し否定
3. /u++ 対話: Creator「信念分布の記号化」「ベーステーブルと TO」→ 思想発見
4. /dia+ (Gemini): 6座標の欠落と冗長を指摘 → 10成分に拡張
5. /dia+!: 実装計画の致命的欠陥を6つ発見 → demo-first に方針転換

## 設計上の未決事項

1. **@purpose と @audience を必須にするか？** — Kalon (全部書くな) vs メタ座標 (AUDIENCE が全てを決める)
2. **compile は AUDIENCE 対応にすべき** — 現計画は一律 MD 出力で哲学と矛盾
3. **classify_task の位置づけ** — 座標ではなく操作。だが計画から消えている
4. **COMPOSITION の分解** — @mixin (合成) だけでは依存と参照が欠ける
5. **SOURCE vs PROVENANCE の分離** — BC-6 TAINT との整合

## BC 違反

- registry.yaml パースエラーで Týpos PJ 登録失敗 (BC-12)。要修正。

## 次セッションで最初にやること

1. registry.yaml 修正 + Týpos PJ 登録
2. 実装計画を demo_v3.prompt から逆算して書き直し
3. typos.py に最小 v3 パース対応を追加 (@source, @audience, @purpose, @precision, @freshness, @scope)

## 学んだこと (パターン化)

### P1: 思想は対話から生まれる

- /noe+ を一人で回しても A≒a にしかならなかった
- Creator の「それは当たり前」という否定が深度を生んだ
- 「信念分布の記号化」「ベーステーブルと TO」は Creator の実務者的直感

### P2: demo-first > spec-first

- 先に仕様を書くと「フィールドを追加する」だけの凡庸な計画になる
- 先に理想のユーザー体験を書くと、仕様が自然に決まる

### P3: /dia+! は自分で自分を壊す技術

- 自作の計画を容赦なく批判すると、致命的欠陥が見える
- 外部 (Gemini) + 内部 (自己批判) の二重検証が有効
