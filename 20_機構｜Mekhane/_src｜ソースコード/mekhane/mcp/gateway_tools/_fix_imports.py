#!/usr/bin/env python3
# PROOF: mekhane/mcp/gateway_tools/_fix_imports.py
# PURPOSE: mcp モジュールの _fix_imports
"""修復スクリプト: 各ドメインファイルの不足 import を追加する。

問題: _splitter.py は関数本体のみを移動し、関数が参照する
モジュールレベル変数や標準ライブラリの import を追加しなかった。
"""
import ast
import re
from pathlib import Path

GTD = Path("mekhane/mcp/gateway_tools")
GW = Path("mekhane/mcp/hgk_gateway.py")

# hgk_gateway.py からエクスポート可能な全変数を把握
gw_source = GW.read_text("utf-8")

# 各ドメインに必要な追加 import を定義 (ソースコード読み取りに基づく)
FIXUPS = {
    "knowledge.py": {
        "std_imports": ["import json", "import os", "import sys",
                        "from pathlib import Path", "from datetime import datetime"],
        "gw_imports_add": ["INCOMING_DIR", "PROCESSED_DIR", "_MNEME_DIR",
                           "_oauth_provider", "_COWORK_DIR", "_COWORK_ARCHIVE",
                           "_COWORK_MAX_ACTIVE"],
    },
    "ochema.py": {
        "std_imports": [],
        "gw_imports_add": ["SESSIONS_DIR", "_ask_timestamps", "_ASK_RATE_LIMIT",
                           "_ASK_RATE_WINDOW", "_chat_sessions", "_MAX_CHAT_SESSIONS"],
    },
    "sympatheia.py": {
        "std_imports": ["import json", "import os", "from pathlib import Path",
                        "from datetime import datetime"],
        "gw_imports_add": ["_MNEME_DIR"],
    },
    "digestor.py": {
        "std_imports": ["import json", "from pathlib import Path", "from datetime import datetime"],
        "gw_imports_add": [],
    },
    "jules.py": {
        "std_imports": ["import os", "import json"],
        "gw_imports_add": [],
    },
    "periskope.py": {
        "std_imports": ["import json"],
        "gw_imports_add": [],
    },
    "search.py": {
        "std_imports": ["import os", "import sys", "import signal"],
        "gw_imports_add": [],
    },
    "typos.py": {
        "std_imports": [],
        "gw_imports_add": [],
    },
}


def fix_file(filename, fixup):
    filepath = GTD / filename
    source = filepath.read_text("utf-8")
    lines = source.split("\n")

    # 1. 標準 import の追加 (ファイル先頭、docstring の後)
    std_imports = fixup.get("std_imports", [])
    if std_imports:
        # `import time` の行の後に追加
        for i, line in enumerate(lines):
            if line.strip() == "import time":
                for j, imp in enumerate(std_imports):
                    lines.insert(i + 1 + j, imp)
                break

    # 2. hgk_gateway import の追加
    gw_add = fixup.get("gw_imports_add", [])
    if gw_add:
        for i, line in enumerate(lines):
            if "from mekhane.mcp.hgk_gateway import" in line:
                # 既存の import 行に追加
                for symbol in gw_add:
                    if symbol not in line:
                        line = line.rstrip() + f", {symbol}"
                lines[i] = line
                break

    new_source = "\n".join(lines)
    filepath.write_text(new_source, "utf-8")
    return len(std_imports) + len(gw_add)


total_fixes = 0
for filename, fixup in FIXUPS.items():
    n = fix_file(filename, fixup)
    if n > 0:
        print(f"  ✅ {filename}: +{n} imports")
    else:
        print(f"  ⚪ {filename}: no changes needed")
    total_fixes += n

print(f"\n📊 Total: {total_fixes} imports added across {len(FIXUPS)} files")
