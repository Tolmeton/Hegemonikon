# Handoff: Gateway 分割 Kalon

**日時**: 2026-02-28 16:29 JST
**セッション時間**: ~2.5h (14:00-16:29)

## 成果

| 変更 | Before | After |
|:--|:--|:--|
| hgk_gateway.py | 3,511 行 | **935 行** |
| gateway_tools/ | 0 files | **9 files** (58 tools) |
| 循環 import | 発生 | **解消** (遅延 import パターン) |
| 不足 import | 32 個 | **修復済** |

## アーキテクチャ

```
mekhane/mcp/
├── hgk_gateway.py (935行 — コア: OAuth, Config, Helpers)
└── gateway_tools/
    ├── __init__.py      register_all() → 9ドメイン
    ├── ccl.py           3 tools (dispatch, execute, run)
    ├── knowledge.py     12 tools (search, status, PKS, cowork...)
    ├── sympatheia.py    12 tools (health, WBC, basanos...)
    ├── ochema.py        9 tools (ask, models, chat...)
    ├── periskope.py     6 tools (research, track, benchmark...)
    ├── typos.py         6 tools (generate, parse, validate...)
    ├── digestor.py      5 tools (check, mark, list, topics, run)
    ├── jules.py         4 tools (create, status, repos, batch)
    └── search.py        1 tool (paper_search)
```

## 確立された解法: 遅延 Import パターン

```python
# gateway_tools/xxx.py
def register_xxx_tools():
    from mekhane.mcp.hgk_gateway import mcp, _traced, ...
    @mcp.tool()
    @_traced
    def hgk_xxx(...): ...
```

循環 import の原因は `register_all()` → domain.py → `from hgk_gateway import *` だった。
解法: `register_xxx_tools()` 関数内で遅延 import し、server.py の mount 直後に呼ぶ。

## 残課題

1. **動的ルーター修正**: `routes/hgk.py` が `hgk_status` を直接参照 → gateway_tools 対応が必要
2. **mount パス**: `mount("/")` のまま (FastMCP のデフォルト `streamable_http_path="/mcp"` を利用)。正道化は nginx reverse proxy か FastMCP upstream 変更待ち
3. **runtime テスト不完全**: CLI import が 120秒+ でタイムアウト。systemd サービスは正常動作中

## 教訓 (Doxa)

- **「できた」と思った瞬間が最も危険** — `/ele+` で 32 個の不足 import が発覚した
- **AST > sed**: sed は `\b` でも過剰置換する。Python AST で正確に関数を切り出すべき
- **最小打診 (/dok) の価値**: 3 tools だけ先にやることで、パターンが確立された
