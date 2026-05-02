# claude-token-optimizer 深掘り調査

> **優先度**: B
> **repo**: `nadimtuhin/claude-token-optimizer`
> **stars**: 未検証
> **license**: MIT
> **HGK 対象**: `Pepsis`, `ant.tanaoroshi`, `Ochēma`
> **調査深度**: README + setup docs + 公式 Claude Code docs + HGK ローカル実装比較

## import_candidates

1. **token/prior 棚卸しの明示化 → `ant.tanaoroshi`**
   - repo の核心は「何が常時 context を食うか」を数えることにある。
   - HGK での用途: 既存の棚卸し skill を、より reader-facing な出力面へ接続する。
   - 判定: [ ]

2. **small startup surface の整理術 → `CLAUDE.md` / `hgk-runtime-index.md` / hooks**
   - repo は常時読む面を極小化する設計を強く推す。
   - HGK での用途: hook と runtime index を前提に、常駐面の薄さを維持する比較基準。
   - 判定: [ ]

3. **common mistakes の薄い digest → `Violations` / `decision_log` / `Pinakas`**
   - repo はメンテ文書を短く実践的に保つ。
   - HGK での用途: 失敗知見を 1 枚へ蒸留し、再発防止を軽量化する。
   - 判定: [ ]

4. **session/archive を live context から離す運用 → `Ochēma` / `Mneme` / `ROM`**
   - repo は sessions/completions/archive を live prompt から切り離す思想を持つ。
   - HGK での用途: 既存の session 要約・resume・ROM 化と比較し、UX を磨く。
   - 判定: [ ]

5. **`.claudeignore` を主制御面として使う案**
   - repo の実践上は重要だが、機能境界としては不安定。
   - HGK での用途: import ではなく watch/skip 判定の対象。
   - 判定: [ ]

## T1 対応表

### 完全対応

| claude-token-optimizer | HGK | 成立度 | 解説 |
|:-----------------------|:----|:------:|:-----|
| token overhead の棚卸し | `ant.tanaoroshi` | ★★★★★ | 「何が何 token 食っているかを数える」主機能は HGK 側に既に存在 |
| session/history の外部化 | `Ochēma session_store/session_notes` + `project_index/ROM` | ★★★★★ | 永続化・要約・必要時再注入の面は既に実装済み |

### 部分成立

| claude-token-optimizer | HGK | 成立度 | 差分 |
|:-----------------------|:----|:------:|:-----|
| small startup surface | `CLAUDE.md` + `hgk-runtime-index.md` + hooks | ★★★★☆ | 方向は一致。ただし repo 側の起動時想定は現行 Claude Code 正本と少しズレる |
| topic docs / maintenance guide | `hgk-runtime-index.md` + `project_index` | ★★★★☆ | HGK は on-demand index を持つが、repo の固定 4 ファイル主義とは違う |
| common mistakes digest | `Violations` + `decision_log` + `Pinakas` | ★★★☆☆ | 知見はあるが、1 枚の薄い失敗集としてはまだ未蒸留 |
| archive separation | `Mneme` + `ROM` + `session_notes` | ★★★★☆ | 目的は同じ。ただし HGK は path 除外より意味論的外部化を優先 |

### 未対応 / 非採用

| claude-token-optimizer | 判定 | 理由 |
|:-----------------------|:-----|:-----|
| `.claudeignore` を主要境界に置く | **Skip** | SOURCE 主義と再現性の土台にするには不安定 |
| 「90% token 削減」系の固定主張 | **Skip** | model・運用・読み込み条件が違うため移植不能 |
| repo 標準構成の全面移植 | **Skip** | HGK 既存面と重複しやすい |

## 判定

| candidate | 判定 | 理由 |
|:----------|:-----|:-----|
| token/prior 棚卸し | **Import** | 既に `ant.tanaoroshi` に近縁面があり、最も自然な吸収先 |
| small startup surface の整理術 | **Import** | `CLAUDE.md` / runtime index / hooks の監視指標として有効 |
| common mistakes digest | **Import** | HGK に足りないのは失敗知見そのものより、薄い再利用形式 |
| session/archive separation | **Watch** | 発想は良いが、HGK 側は既に `Ochēma` と `Mneme` で別解を持つ |
| `.claudeignore` 主制御 | **Skip** | 基盤境界としては弱い |

## 差分メモ

この repo は HGK 本体の随伴対象というより、**関連 PJ への分解随伴候補**として扱うのが正確である。

最も自然な列は次の通り:

```text
claude-token-optimizer
  -> Pepsis (外部思想の消化)
  -> ant.tanaoroshi (膨張検知として内在化)
  -> Ochēma (runtime 残差のみ輸入)
```

したがって、単一の 1:1 対応ではない。
`Kernel` に随伴させるには重心が軽すぎ、`Mneme` に直付けすると archive 面が二重化しやすい。
一方で `Pepsis` / `ant.tanaoroshi` / `Ochēma` の列なら、repo の価値がちょうど分配される。

## 次の実装タスク

1. `ant.tanaoroshi` の出力を reader-facing な `COMMON_FAILURES.md` 候補へ接続する。
2. `hgk-runtime-index.md` の各項目に「いつ読むか / 概算 token cost」を付与できるか確認する。
3. `Ochēma` の session 圧縮 UX と repo の archive 思想を比較し、差分だけを import 候補に切り出す。

## Sources

- Repo README: https://github.com/nadimtuhin/claude-token-optimizer
- Setup guide: https://github.com/nadimtuhin/claude-token-optimizer/blob/main/UNIVERSAL_SETUP.md
- Claude Code memory docs: https://code.claude.com/docs/en/memory
- Claude Code context window docs: https://code.claude.com/docs/en/context-window
- `/home/makaron8426/.claude/skills/ant-tanaoroshi/SKILL.md`
- `/home/makaron8426/.claude/_backups/token-optimizer/auto-snapshots/snap_20260420_171826.json`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/ochema/session_store.py`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/ochema/session_notes.py`

---

*Created: 2026-04-20*
