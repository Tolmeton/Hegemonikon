# Handoff: BC→N 参照リファクタリング (Mekhane コード層)

- **日時**: 2026-03-15 10:32 JST
- **Agent**: Claude (Antigravity)
- **セッション種別**: 技術的負債清算
- **深度**: L2
- **前回Handoff**: (BC 違反ログ調査 → 本セッション)

---

## S: 状況

Nous 層の BC→N 移行は前セッションで完了済みだったが、Mekhane コード層（.py, .md, .typos）に大量の `BC-XX` 参照が残存していた。Creator が「いまやろう」と判断し、本セッションで一括処理を実行。

## B: 背景

- Hóros v4.1 で BC 体系から Nomoi 12法体系に移行済み
- user_rules, WF 定義, .agents/rules は既に N-XX 体系
- コード内の `BC-XX` 参照は API データ値・コメント・docstring・ドキュメントに分散
- BC→N マッピング: BC-1→N-1, BC-4→N-5, BC-5→N-4, BC-6→N-3/N-10, BC-7→N-7, BC-8→N-8, BC-11→θ12.1, BC-14→N-2, BC-15→N-11, BC-16→N-9, BC-18→Context Rot, BC-20→S-I

## A: 実施内容

### 修正ファイル: 40+ ファイル (3波で実行)

**第1波** — hermeneus + hgk/api + mekhane 主要コード:
- `hermeneus/src/mcp_server.py`: `(旧 BC-11)` 15件削除, `BC-4→N-5`, `BC-7→N-7`
- `hermeneus/src/dispatch.py`: `(旧 BC-11)` 削除, `BC-8→N-8`, `BC-14→N-2`, `BC-18→Context Rot`
- `hermeneus/src/translator.py`: `BC-6→N-10` 連携
- `hermeneus/src/subscribers/plan_recorder.py`: `BC-20→S-I`
- `hermeneus/tests/test_mcp_run.py`: `(旧 BC-11)` 削除
- `hgk/api/colony.py`, `tool_loop_guard.py`, `coo_synthesize.typos`
- `mekhane/periskope/`: citation_agent, engine, models, PROOF.md, ビジョン.md
- `mekhane/fep/`: kalon_checker, metacognitive_layer, krisis_adjunction_builder
- `mekhane/agent_guard/prostasia.py`: TAINT パターン bc_ids を N-XX に (BC-6→N-10, BC-4→N-5, BC-12→N-6, BC-5→N-2, BC-1→N-1)
- `mekhane/sympatheia/tests/test_violation_logger.py`: テストデータ BC→N

**第2波** — ochema, mcp, taxis, symploke, tools:
- `mekhane/ochema/antigravity_client.py`, `tools.py`
- `mekhane/mcp/mcp_base.py`, `sekisho_mcp_server.py`, `periskope_mcp_server.py`, `gateway_tools/ccl.py`
- `mekhane/taxis/morphism_proposer.py`
- `mekhane/symploke/intent_wal.py`, `tests/test_intent_wal.py`
- `mekhane/tools/enrich_*.py` (3ファイル)

**第3波** — ドキュメント:
- `mekhane/dendron/ビジョン.md`
- `mekhane/ergasterion/`: sage-blueprint.md, demo_v3.typos, eat_deep_research_tools.md
- `mekhane/mcp/project_knowledge/02_bc_summary.md` (全面書換)
- `mekhane/mcp/project_knowledge/04_ccl_reference.md`, `07_handoff_summary.md`

### 検証結果

| 対象 | BC-[0-9] 残存 | 状態 |
|:-----|:-------------|:-----|
| hermeneus (.py) | 0 | ✅ |
| hgk/api | 0 | ✅ |
| mekhane (.py) | 0 | ✅ |
| mekhane (.md) | `(旧 BC-XX)` 注釈のみ | ✅ 意図的保持 |

## R: 残タスク・Next Actions

1. **テスト実行**: `test_violation_logger.py`, `test_metacognitive_layer.py` は BC ID のテストデータを変更したため、回帰テスト必須
2. **`bc_registry.yaml` の N-XX 化**: 現在 BCRegistry は旧 BC-XX ID をキーとして使用。将来的に NomosRegistry にリネームする価値あり
3. **prostasia.py の BCRegistry リネーム**: クラス名・変数名に `bc` が残存。API 互換性を考慮した段階的移行が必要
4. **`02_bc_summary.md` の精査**: sed で一括置換したため、テーブルの整合性を目視確認すべき

---

## 🏷️ 法則化

- **大規模リファクタリングは3波に分けて実行**: 第1波で最も影響の大きいコア、第2波で周辺、第3波でドキュメント。各波の間に grep スキャンで残存を確認
- **sed の日本語パスの罠**: `find | xargs sed` が日本語パスでハングする場合がある。`grep_search` ツール → 対象特定 → sed 直接実行のパターンが安全
- **`(旧 BC-XX)` 表記は段階的移行に有用だったが、今や負債**: 移行期の併記表記は、移行完了後に一括削除すべき

---

## 📊 Session Metrics

| 指標 | 値 |
|:-----|:---|
| 修正ファイル数 | 40+ |
| sed コマンド実行回数 | 3波 × 各10-20置換 |
| 検証スキャン回数 | 4 |
| `.py` ファイル残存 | 0 |
