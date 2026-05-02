# extends/mixins と二層分離による Hóros DRY 化設計

## 1. 課題認識

1. **機能重複**: `case` と `examples`、`rationale` と `principle` 等で意味的重複がある
2. **N-1 肥大化 (29行→165行)**: 12 Nomoi 全てを同等の密度にすると全体で2000行を超え、LLM のコンテキストを圧迫する
3. **DRY 違反**: `@scope` や `@focus`、FEP の知覚推論といった共通概念が N-1 にハードコードされているが、これは S-I (Tapeinophrosyne) 共通で持てるはずのもの

## 2. 解決策：二層分離 (Action Layer vs Theory Layer)

LLM（読み手）の認知負荷を減らし、かつ行動変容（Recall Trigger & Discrimination）を最大化するため、**prompt ファイル自体は「行動層」に絞る**。理論的根拠は **Knowledge Item (KI) または外部リソース「理論層」に逃がし、参照のみを残す**。

### Action Layer (horos-N01-実体を読め.md - Promptに記述するもの)
- `role`, `goal`, `constraints`
- `tools` (具体的な使用ツール)
- `step` (具体的な手順)
- `format` (出力形式)
- `examples` (判定パターン：Input/Output)
- `@scope` (発動/非発動条件)
- `@focus` (想起トリガー)
- `@highlight` (減衰耐性アンカー)
- `extends`, `mixins`

### Theory Layer (外部 KI/Markdown - Prompt から削除・分離するもの)
- `@rationale` (FEP根拠等の理論)
- `@principle` (公理の解説)
- `@case` (歴史的経緯、違反事例の詳細)
- `@intent` (なぜこのルールがあるかという背景)

*(※ V-012 などの Creator 叱責の引用は `examples` に統合し、Failure Cost Visibility は維持する)*

## 3. extends / mixins 設計

Hóros 体系は 3 Stoicheia (S-I, S-II, S-III) × 4 Phase で構成される。
したがって、**S-I / S-II / S-III の共通要素を `@mixin` または `extends` として抽出**する。

### 3.1 Mixin 1: S-I 認識的謙虚 (Tapeinophrosyne)
ファイル名: `mixin-stoicheia-S01.typos`
- **内容**:
  - `goal`: prior の precision を下げ、感覚入力の precision を上げる（S-I 共通）
  - `@focus`: 「知っている」「たぶん」という感覚への警戒（S-I 共通）
  - `@behavioral_pattern`: V-012 起源の「怠惰欺瞞」を防ぐ自己監視

### 3.2 継承と Mixin による再構築 (N-01 の場合)

```typos
#prompt horos_N01
#syntax: v8
#depth: L2
<:mixin: mixin-stoicheia-S01 :>

<:role: N-01 实体を読め (S-I Tapeinophrosyne × P-1 Aisthēsis) :>

<:constraints:
  - θ1.1 WF 実行前に view_file で本体を開く
  - θ1.2 WF 出力形式は完全遵守 (違反は S-I 怠惰欺瞞)
  - θ1.3 HGK 独自概念はカーネル定義を必ず参照
  - θ1.4 コンストラクタ・関数シグネチャは推測しない
/constraints:>

<:tools:
  - view_file: ファイル内容読み取り
  - view_code_item: シグネチャ確認
  - view_file_outline: ファイル構造俯瞰
:>

<:step: ... :>
<:format: ... :>
<:examples: ... :>
<:scope: ... :>
<:highlight: ... :>

<:resources:
  - horos-theory-S01.md: S-I 共通の理論根拠 (rationale/principle/case)
:>
```

### 3.3 Mixin 2: BRD パターンと FEP レンズ
- BRD パターン (Bad thought → Reality → Detection) や FEP レンズ (F1-F5) も、各 Nomoi の Prompt にベタ書きするのではなく、グローバルな Mixin として定義可能

## 4. 実行ステップ

1. **S-I 専用 Mixin の作成** (`mixin-stoicheia-S01.typos` 相当)
2. **N-01 行動層のスリム化** (`horos-N01-実体を読め.md` を 80 行前後に削減、理論層へのパスを追加)
3. **N-02〜N-04 (S-I 族) への展開**
4. (順次) S-II, S-III の Mixin 化と展開
