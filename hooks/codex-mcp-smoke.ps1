[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$wrapper = Join-Path $HOME ".claude\bin\hgk-codex-mcp.py"
$remoteHost = "100.83.204.102"
$env:HGK_CODEX_REPO = Join-Path $HOME "Sync\oikos\hgk-codex"

if (-not (Test-Path -LiteralPath $python)) {
    throw "python not found: $python"
}

if (-not (Test-Path -LiteralPath $wrapper)) {
    throw "wrapper not found: $wrapper"
}

$probe = @'
import asyncio
import json
import sys

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main() -> None:
    py, wrapper, axis, remote_host = sys.argv[1:5]
    args = [
        wrapper,
        "--transport",
        "stdio",
        "--axis",
        axis,
        "--placement-profile",
        "local",
        "--remote-upstream-host",
        remote_host,
    ]
    params = StdioServerParameters(command=py, args=args)
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            payload = {
                "axis": axis,
                "tool_count": len(tools.tools),
                "tools": [tool.name for tool in tools.tools[:8]],
            }
            print(json.dumps(payload, ensure_ascii=False))


asyncio.run(main())
'@

$axes = @("aisthetikon", "dianoetikon", "poietikon")
$results = @()

foreach ($axis in $axes) {
    Write-Host "== $axis =="
    $json = $probe | & $python - $python $wrapper $axis $remoteHost
    if ($LASTEXITCODE -ne 0) {
        throw "smoke failed for $axis"
    }
    $obj = $json | ConvertFrom-Json
    $results += $obj
    Write-Host ("tools={0}" -f $obj.tool_count)
    foreach ($tool in $obj.tools) {
        Write-Host ("  - {0}" -f $tool)
    }
}

Write-Host ""
Write-Host "codex-mcp-smoke: PASS"
