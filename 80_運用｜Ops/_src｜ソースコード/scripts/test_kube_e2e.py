import asyncio
import os
import sys

# ensure hegemonikon is in sys.path
sys.path.insert(0, str(os.path.abspath(".")))

from mekhane.mcp.kube_mcp_server import handle_kube_tool
from mekhane.periskope.cognition._llm import llm_ask

async def llm_call(prompt: str) -> str:
    # Use the existing LLM bridge from Periskope which resolves credentials properly
    return await llm_ask(prompt, model="gemini-3-flash-preview", max_tokens=1024)


async def main():
    print("=== Testing Kube MCP: kube_plan ===")
    plan_args = {"goal": "example.com にアクセスして H1 タイトルを取得する"}
    plan_out = await handle_kube_tool("kube_plan", plan_args, llm_callable=llm_call)
    print("Plan Output:")
    print(plan_out)
    
    print("\n=== Testing Kube MCP: kube_execute ===")
    exec_args = {
        "goal": "example.com にアクセスして H1 タイトルを取得する",
        "max_steps": 10,
        "headless": True
    }
    exec_out = await handle_kube_tool("kube_execute", exec_args, llm_callable=llm_call)
    print("Execute Output:")
    print(exec_out)

if __name__ == "__main__":
    asyncio.run(main())
