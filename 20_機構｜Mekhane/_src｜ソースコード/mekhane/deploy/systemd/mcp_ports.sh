#!/bin/bash
# PURPOSE: MCP サーバーのポートマッピング (単一定義ファイル)
# 参照元: run_mcp_service.sh, hgk-mcp@.service (ExecStartPre)
# 変更時はここだけ修正すればよい

declare -A MCP_PORTS=(
    ["ochema"]=9701
    ["sympatheia"]=9702
    ["hermeneus"]=9703
    ["phantazein"]=9704  # 旧 mneme
    ["sekisho"]=9705
    ["periskope"]=9706
    ["digestor"]=9707
    ["jules"]=9708
    ["typos"]=9709
    ["phantazein-boot"]=9710  # boot/health (将来 phantazein に統合)
    ["gws"]=9711
    ["opsis"]=9712
    ["xmcp"]=9713
    ["aisthetikon"]=9720
    ["dianoetikon"]=9721
    ["poietikon"]=9722
    ["api"]=9696
)
