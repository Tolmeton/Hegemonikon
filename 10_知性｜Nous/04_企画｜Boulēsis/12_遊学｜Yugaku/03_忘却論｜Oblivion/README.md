# 忘却論｜Oblivion

このディレクトリは、忘却論の公開候補と内部制作線を分離して管理する。
公開・編集導線の主入口は4つに固定し、それ以外の作業面は補助面として分けて扱う。

## 4つの主入口

### 1. 公開シリーズ
- `drafts/series/`
- 正本は `論文0_忘却の忘却_草稿.md` と `論文I` から `論文XIII` までの数字付き系列。
- 各番号につき正本は1ファイルだけに固定する。

### 2. 公開番外編
- `drafts/standalone/`
- 独立公開候補を置く。
- 単独稿だけでなく、忘却論から派生した衛星クラスタもここに置く。
- 現行の衛星クラスタ:
  - `drafts/standalone/llm_embodiment/`
  - `drafts/standalone/oblivion_satellites/`
- 昇格条件は以下の3点:
  - 単独要旨が書ける
  - シリーズ本文を前提にしない最小定義がある
  - 参考文献と主張水準ラベルが自前で閉じる

### 3. 内部インフラ
- `drafts/infra/`
- `plans/出版計画_忘却論シリーズ.md`
- 出版順・系列番号・公開境界の正本は `plans/出版計画_忘却論シリーズ.md`。
- 記号・定理索引の正本は `drafts/infra/リファレンス/統一記号表.md`。
- 新規参加者向け導入は `drafts/infra/リファレンス/忘却論オンボーディング.md`。
- Face Lemma の概念入口は `drafts/infra/リファレンス/FaceLemma.md`。符号理論対応・修復可能性設計・calculations 進捗を含む backstage は `drafts/infra/FaceLemma_技術設計.md`。
- モノグラフ線は `drafts/infra/リファレンス/モノグラフ構成設計.md` で管理するが、現時点では内部制作線であり公開正本ではない。

### 4. インキュベータ
- `drafts/incubator/`
- 橋渡しメモ、先行研究超克、AI接続メモ、旧版、吸収済み断片を退避する。
- `_absorbed/`, `legacy/`, `archive/` は公開レイヤから外した履歴置き場。

## 補助作業面

- `calculations/` は計算ノート、証明パッチ、数値実験レポートを置く補助面。
- `experiments/` は実験設計・実験用チェックリストの補助面。
- `thermodynamic_correspondence_v3.md` は熱力学対応表のリビングノートであり、4レイヤの入口には数えない。
- `Ξ計算_軌跡から不均一度.py` は補助計算スクリプトであり、公開系列や番外編の正本ではない。

## 命名と非推奨

- `Oblivion/` 内部の案内文書では、経路表記の正規形を `README.md`, `drafts/...`, `plans/...`, `calculations/...`, `experiments/...` にそろえる。
- 旧 `drafts/infra/*.md` 参照が残っている場合、正本 alias は `drafts/infra/リファレンス/忘却論オンボーディング.md` の legacy 対応表を参照する。
- 実際に相対リンクとして解決する必要がある Markdown link だけは、ファイル相対パスを使ってよい。
- `paper_IV_draft.md` は廃止。正本は `drafts/series/論文IV_なぜ効果量は小さいか_草稿.md`。
- `drafts/` 直下に公開候補の `.md` を戻さない。新規文書は最初から4レイヤのどこに置くかを決める。
- `monograph_design.md` は旧版アーカイブであり、長期設計の正本ではない。
