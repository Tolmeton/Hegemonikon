# token-savior 実装面固定

> **repo**: `Mibayy/token-savior`
> **upstream HEAD**: `729cf7aac04f1815cdbcbfebc5da65f6131cf28e` (検証日 2026-04-23)
> **license**: MIT
> **HGK 対象**: `OssAdjoint`, `Organon`, `Mekhane`, `Codex MCP`
> **実装深度**: bounded-root sidecar の practical fixation

## carry-forward

- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/d_成果物｜artifacts/pei_token_savior_nav_sidecar_poc_2026-04-21.md`
  は `TOKEN_SAVIOR_PROFILE=nav` を sidecar PoC として実験し、`repo root` ではなく `bounded root` が自然だと示した。
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/research/token-savior/VISION.md`
  は概念吸収の候補を `Organon sidecar` に置き、`Mneme` 正本置換を棄却した。

今回の `/tek` は、この `/pei` の結論を **noncanonical config surface** と **governance note** に固定する。

## practical surfaces

1. **bounded-root sidecar**
   - 対象 root は `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane`
   - current HEAD 再検証では `nav` 実測 `29 tools`、`reindex 7.894s`、`find_symbol("PhantazeinStore")` 成功
   - 判定: **Import**

2. **repo-root attach の棄却**
   - current HEAD 再検証では repo root `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon` が `Project has 10000+ files, stopping at MAX_FILES=10000` に到達
   - upstream `ProjectIndexer` の default `max_files` は `10000`
   - 判定: **Skip**

3. **manifest shaping と permission boundary の分離**
   - `nav` は `tools/list` を絞る
   - ただし hidden handler は live のまま残る
   - したがって `nav` は **低 prompt 化** には効くが、**権限境界** ではない
   - 判定: **Guard**

## practical verdict

| surface | 判定 | 理由 |
|:--------|:-----|:-----|
| `mekhane` bounded-root sidecar | **Adopt** | 現物 probe で `reindex` と `find_symbol` が成立。最小侵襲で利得が出る |
| repo root sidecar | **Reject** | current HEAD で `MAX_FILES=10000` cap に達し、実務上の起動面が荒い |
| `nav` を read-only 権限境界と見なす | **Reject** | hidden tools が callable であり、manifest 非表示は capability disable ではない |
| canonical `~/.codex/config.toml` 直編集 | **Defer** | まず noncanonical snippet と wrapper で導入面を固定し、Zero-Trust を通す |

## fixed surfaces

### 1. wrapper script

path:
`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/research/token-savior/run-token-savior-nav-mekhane.sh`

役割:
- `WORKSPACE_ROOTS` を bounded root に固定
- `TOKEN_SAVIOR_PROFILE=nav` を明示
- `TOKEN_SAVIOR_CLIENT=codex` を明示
- Codex TOML 側に env 記法の推測を持ち込まず、command 1 本に閉じる

### 2. noncanonical config snippet

path:
`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/research/token-savior/codex.config.snippet.toml`

役割:
- `~/.codex/config.toml` へ later merge するための最小 surface
- canonical config をこのターンで直接変更しない

### 3. root policy

初回 attach の root は次に限定する:

`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane`

当面 attach しない root:

`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon`

## governance note

1. **profile を必ず明示する**
   - current HEAD では `TOKEN_SAVIOR_PROFILE` 未指定かつ `_PROFILE == "full"` の時、`v3.0.0` で default が `full -> lean` に変わる warning を出す
   - したがって HGK 側では profile implicit を禁止し、`nav` を明示する

2. **README を authority にしない**
   - current README は `full=106`, `nav=28` と書く
   - current server code / live probe は `full catalog=94`, `nav probe=29` を返した
   - つまり **README と live surface が drift** している

3. **nav を権限境界とみなさない**
   - `server.py` は `nav` を `set(_MEMORY_HANDLERS) | set(_META_HANDLERS) | set(_SLOT_HANDLERS)` の advertised exclusion として実装する
   - hidden handlers 自体は live で、前回 `/pei` でも `list_projects`, `reindex` が callable だった
   - したがって Zero-Trust 的には `nav = manifest slimming` であり `nav = read-only sandbox` ではない

4. **導入前の Zero-Trust 手順**
   - `8a` `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/80_運用｜Ops/_src｜ソースコード/scripts/check_mcp_smell.py`
   - `8b` description の人手レビュー
   - `8c` sandbox dry-run
   - `8d` 戻り値の `<instructions>`, `<system>` 汚染検査

5. **repo root attach は性能以前に統治面が荒い**
   - repo root では staged-release `.gitignore` と repo 規模の両方がノイズになる
   - current HEAD では default cap `10000` に達し、bounded root の方がはるかに予測可能

## attach 手順

1. upstream install を実施する  
   `python3 -m venv ~/.local/token-savior-venv`  
   `~/.local/token-savior-venv/bin/pip install -e ".[mcp]"`

2. wrapper script を使って bounded root で起動する

3. `~/.codex/config.toml` へは
   `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/research/token-savior/codex.config.snippet.toml`
   の内容だけを later merge する

4. merge 前に smell / manual review / dry-run / return-value audit を通す

## next tasks

1. `adjoint_map.yaml` へ直接追加する前に、`mekhane` bounded-root attach を一度だけ noncanonical で運用確認する
2. `nav` hidden-handler 問題が残るなら、HGK 側 wrapper で許可コマンドをさらに狭める
3. 利得が継続するなら `multi-language structural nav` と `progressive disclosure façade` を `Mekhane` へ部分吸収する
4. repo root attach は `TOKEN_SAVIOR_MAX_FILES`, custom excludes, `.gitignore` 互換性を別 `/pei.measure` で切るまで凍結する

## sources

- HGK
  - `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/research/token-savior/VISION.md`
  - `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/d_成果物｜artifacts/pei_token_savior_nav_sidecar_poc_2026-04-21.md`
  - `/home/makaron8426/.codex/config.toml`
  - `/home/makaron8426/.claude/rules/horos-hub.md`
- upstream
  - `https://github.com/Mibayy/token-savior/blob/729cf7aac04f1815cdbcbfebc5da65f6131cf28e/llms-install.md`
  - `https://github.com/Mibayy/token-savior/blob/729cf7aac04f1815cdbcbfebc5da65f6131cf28e/src/token_savior/server.py`
  - `https://github.com/Mibayy/token-savior/blob/729cf7aac04f1815cdbcbfebc5da65f6131cf28e/src/token_savior/project_indexer.py`

---

*Created: 2026-04-23*
