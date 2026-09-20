"""
WITH MCP SERVER — Part 2: The Client
======================================
This client connects to the MCP server (mcp_server.py) and uses
its tools to answer questions — without knowing the tool logic at all.

Install deps:  pip install mcp anthropic
Usage:         python mcp_client.py
               (mcp_server.py will be launched automatically as a subprocess)

Key difference from without_mcp.py:
  - No tool logic here at all
  - No tool schemas hardcoded here
  - Just: connect → discover tools → let Claude use them
"""

import anthropic
import json
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# This script works as MCP host & client both here?

# ─── 1. Connect to MCP server and run the agent ───────────────────────────────

async def run_agent(user_question: str):
    # Launch mcp_server.py as a subprocess — it communicates via stdio
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            # ── 2. Discover tools from the server (no hardcoding needed) ──────
            await session.initialize()
            mcp_tools = await session.list_tools()

            # Convert MCP tool format → Anthropic API tool format
            tool_schemas = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }
                for tool in mcp_tools.tools
            ]

            print(f"\n Discovered {len(tool_schemas)} tools from MCP server:")
            for t in tool_schemas:
                print(f"   • {t['name']}")

            # ── 3. Agentic loop — same pattern, but tools come from server ────
            client = anthropic.Anthropic()
            messages = [{"role": "user", "content": user_question}]

            print(f"\n USER: {user_question}")
            print("─" * 60)

            while True:
                response = client.messages.create(
                    model="claude-opus-4-5",
                    max_tokens=1024,
                    tools=tool_schemas,      # ← discovered from MCP server
                    messages=messages
                )

                if response.stop_reason == "end_turn":
                    for block in response.content:
                        if hasattr(block, "text"):
                            print(f"\n CLAUDE: {block.text}")
                    break

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        print(f"\n → Calling MCP tool: {block.name}({block.input})")

                        # ── Tool call goes to MCP server, not local function ──
                        result = await session.call_tool(block.name, block.input)
                        result_text = result.content[0].text
                        print(f"   Result: {result_text}")

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_text
                        })

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user",      "content": tool_results})


# ─── 4. Run it ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    asyncio.run(run_agent("What's the weather in Delhi, and what's Apple's stock price?"))