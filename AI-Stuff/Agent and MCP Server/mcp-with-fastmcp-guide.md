# MCP with FastMCP — Comprehensive Guide

## 1. What is FastMCP?

**FastMCP** is a high-level, Pythonic wrapper library built on top of the official low-level `mcp` Python SDK. It lets you turn ordinary Python functions into MCP (Model Context Protocol) tools using a single decorator (`@mcp.tool`), auto-generating everything the MCP protocol requires — tool schemas, request routing, and result formatting — instead of you writing that machinery by hand.

Put simply: **the `mcp` SDK is the protocol implementation; FastMCP is the productivity layer on top of it.** Both ultimately produce the same MCP server/client behavior — FastMCP just hides the repetitive, protocol-level boilerplate.

---

## 2. Why We Need FastMCP

Building an MCP server from scratch with the raw `mcp` SDK requires you to:
- Manually write a JSON Schema (`inputSchema`) for every tool
- Manually implement a `list_tools()` handler that returns `Tool` objects
- Manually implement a `call_tool()` handler with an `if/elif` dispatcher matching tool names to logic
- Manually wrap every return value into MCP's content-block format (e.g. `types.TextContent(type="text", text=json.dumps(result))`)
- Manually wire up the transport layer (`stdio_server`, read/write streams) and the server's run loop

This is a lot of repetitive, project-independent boilerplate — the same shape every single time, regardless of what your tools actually do. FastMCP exists to eliminate this:
- **Faster development** — decorate a function, done. No separate schema-writing step.
- **Fewer bugs** — schema and dispatch logic are auto-derived from your function signature, so they can never drift out of sync with the actual implementation (a real risk when you hand-write both separately, as in the raw SDK).
- **More Pythonic** — you write and think in terms of normal Python functions, type hints, and docstrings, not protocol objects.
- **Same underlying protocol** — FastMCP doesn't invent a different protocol; it produces the exact same MCP-compliant server/client behavor as the raw SDK, just with less code to write.

---

## 3. Two Approaches, Side by Side

| Aspect | Raw `mcp` SDK (manual) | FastMCP |
|---|---|---|
| Declaring tools | Manual `@server.list_tools()` returning hand-written `types.Tool(...)` objects | `@mcp.tool` decorator — schema auto-derived from type hints + docstring |
| Dispatching calls | Manual `@server.call_tool()` with `if name == ... elif ...` | Handled internally by FastMCP — no dispatcher code needed |
| Wrapping results | Manual `types.TextContent(type="text", text=json.dumps(result))` | Just `return result` (a dict/any JSON-serializable value) |
| Client connection | Manual `StdioServerParameters` → `stdio_client` → `ClientSession` → `.initialize()` | `async with Client("server.py") as mcp_client:` — one line |
| Reading tool results | `result.content[0].text` (manual unwrap) | `result.data` (already unwrapped) |
| Boilerplate | High — this is the "protocol-level" SDK | Low — FastMCP is a Pythonic wrapper over the exact same protocol/SDK |
| What you learn from it | Exactly how the MCP protocol works under the hood (schema format, content blocks, session lifecycle) | How to be productive quickly, at the cost of not seeing the protocol details |

**Key insight:** these are not two different protocols or architectures — the raw `mcp` SDK version is the *actual protocol implementation* that FastMCP is built on top of. Everything FastMCP does "automatically" (schema generation, dispatch, result wrapping, session setup) is exactly what you see written out explicitly in the raw SDK version. Seeing both is valuable: the raw version demystifies what the decorator is doing behind the scenes; FastMCP is what you'd reach for in most real projects since the raw version's boilerplate doesn't change per-project.

---

## 4. Approach A — Raw `mcp` SDK (Manual, Protocol-Level)

### 4.1 Server — `mcp_server.py`

```python
"""
WITH MCP SERVER — Part 1: The Server
=====================================
This is a standalone MCP server that exposes weather and stock tools.
It runs as a separate process and ANY MCP-compatible AI app can connect to it.

Install deps:  pip install mcp
Run directly:  python mcp_server.py
"""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
import json
import asyncio

# ─── 1. Create the MCP server ─────────────────────────────────────────────────
server = Server("weather-stocks-server")


# ─── 2. Declare what tools this server exposes ────────────────────────────────
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_weather",
            description="Get the current weather for a city",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name, e.g. Delhi"}
                },
                "required": ["city"]
            }
        ),
        types.Tool(
            name="get_stock_price",
            description="Get the current stock price for a ticker symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker, e.g. AAPL"}
                },
                "required": ["ticker"]
            }
        )
    ]


# ─── 3. Handle tool calls — the actual logic lives here ───────────────────────
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:

    if name == "get_weather":
        city = arguments["city"]
        fake_data = {
            "delhi":    {"temp": 38, "condition": "Sunny",  "humidity": "45%"},
            "london":   {"temp": 14, "condition": "Cloudy", "humidity": "78%"},
            "new york": {"temp": 22, "condition": "Windy",  "humidity": "60%"},
        }
        data = fake_data.get(city.lower(), {"temp": 20, "condition": "Clear", "humidity": "50%"})
        result = {"city": city, **data}

    elif name == "get_stock_price":
        ticker = arguments["ticker"].upper()
        fake_prices = {"AAPL": 189.5, "GOOGL": 175.2, "TSLA": 245.0, "MSFT": 420.0}
        result = {"ticker": ticker, "price": fake_prices.get(ticker, 100.0), "currency": "USD"}

    else:
        result = {"error": f"Unknown tool: {name}"}

    return [types.TextContent(type="text", text=json.dumps(result))]


# ─── 4. Run the server (listens via stdio — standard MCP transport) ────────────
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

### 4.2 Client — `mcp_client.py`

```python
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

            print(f"\nDiscovered {len(tool_schemas)} tools from MCP server:")
            for t in tool_schemas:
                print(f"   • {t['name']}")

            # ── 3. Agentic loop — same pattern, but tools come from server ────
            client = anthropic.Anthropic()
            messages = [{"role": "user", "content": user_question}]

            print(f"\nUSER: {user_question}")
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
                            print(f"\nCLAUDE: {block.text}")
                    break

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        print(f"\n→ Calling MCP tool: {block.name}({block.input})")

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


if __name__ == "__main__":
    asyncio.run(run_agent("What's the weather in Delhi, and what's Apple's stock price?"))
```

### 4.3 Detailed Explanation — Raw SDK Approach

**Server side:**
- `Server("weather-stocks-server")` creates the core MCP server object — no tools attached yet.
- `@server.list_tools()` registers a handler that runs whenever a client asks "what tools do you have?" You return a hand-built list of `types.Tool` objects, each requiring a manually written `inputSchema` (JSON Schema format) describing required/optional parameters.
- `@server.call_tool()` registers a handler that runs whenever a client asks "please run this tool." You receive the raw `name` (string) and `arguments` (dict), and must manually branch (`if/elif`) to the correct logic — this is structurally identical to the `TOOLS[block.name](**block.input)` dispatch pattern from the very first "no MCP" example, just written as explicit conditionals instead of a dict lookup.
- Every result must be manually wrapped: `types.TextContent(type="text", text=json.dumps(result))` — MCP results are always a *list* of content blocks (supporting text, images, etc.), so even a single dict result has to be serialized to a JSON string and wrapped in this structure.
- `stdio_server()` sets up the actual transport (stdin/stdout pipes) that the client subprocess will communicate over, and `server.run(...)` starts the protocol's main loop, listening for `list_tools`/`call_tool` requests.

**Client side:**
- `StdioServerParameters(command="python", args=["mcp_server.py"])` describes *how* to launch the server as a subprocess.
- `stdio_client(server_params)` actually spawns that subprocess and opens the raw `read`/`write` streams for communication.
- `ClientSession(read, write)` wraps those raw streams in a higher-level session object that understands the MCP protocol's message format.
- `session.initialize()` performs the MCP handshake (protocol version negotiation, capability exchange) — required before any other calls will work.
- `session.list_tools()` sends the discovery request and returns the tools the server declared in its `list_tools()` handler — this is what lets the client build `tool_schemas` **without hardcoding anything about the tools**.
- `session.call_tool(block.name, block.input)` sends a tool-execution request over the protocol; the *actual* Python function execution happens inside the **server's** process, not the client's — the client just gets the result back.
- `result.content[0].text` — because MCP results are a list of content blocks, you must manually index into the list (`[0]`) and pull out the `.text` field to get your JSON string back, then it gets passed along as-is into the `tool_result` content.

---

## 5. Approach B — FastMCP (High-Level Wrapper)

### 5.1 Server — `server.py`

```python
# server.py
from fastmcp import FastMCP

# Create a named MCP server instance
mcp = FastMCP("Demo Tools Server")

@mcp.tool
def get_weather(city: str) -> dict:
    """Get the current weather for a city"""
    fake_data = {
        "delhi":   {"temp": 38, "condition": "Sunny",  "humidity": "45%"},
        "london":  {"temp": 14, "condition": "Cloudy", "humidity": "78%"},
        "new york":{"temp": 22, "condition": "Windy",  "humidity": "60%"},
    }
    data = fake_data.get(city.lower(), {"temp": 20, "condition": "Clear", "humidity": "50%"})
    return {"city": city, **data}


@mcp.tool
def get_stock_price(ticker: str) -> dict:
    """Get the current stock price for a ticker symbol"""
    fake_prices = {"AAPL": 189.5, "GOOGL": 175.2, "TSLA": 245.0, "MSFT": 420.0}
    price = fake_prices.get(ticker.upper(), 100.0)
    return {"ticker": ticker.upper(), "price": price, "currency": "USD"}


if __name__ == "__main__":
    mcp.run()   # starts the MCP server (stdio transport by default)
```

### 5.2 Client — `client_agent.py`

```python
# client_agent.py
import asyncio
import json
import anthropic
from fastmcp import Client

anthropic_client = anthropic.Anthropic()

async def run_agent(user_question: str):
    # Connect to the MCP server as a subprocess over stdio
    async with Client("server.py") as mcp_client:

        # ─── Step A: Discover tools dynamically from the server ───────────
        mcp_tools = await mcp_client.list_tools()

        # Convert MCP's tool listing into the shape Claude's API expects
        tool_schemas = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in mcp_tools
        ]

        messages = [{"role": "user", "content": user_question}]
        print(f"\nUSER: {user_question}\n" + "─" * 60)

        while True:
            response = anthropic_client.messages.create(
                model="claude-opus-4-5",
                max_tokens=1024,
                tools=tool_schemas,     # ← schemas came from the MCP server, not hand-written
                messages=messages
            )

            if response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        print(f"\nCLAUDE: {block.text}")
                break

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"\n→ Calling MCP tool: {block.name}({block.input})")

                    # ─── Step B: Call the tool over the MCP protocol ───────
                    result = await mcp_client.call_tool(block.name, block.input)

                    print(f"   Result: {result}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result.data)
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    asyncio.run(run_agent("What's the weather in Delhi, and what's Apple's stock price?"))
```

### 5.3 Detailed Explanation — FastMCP Approach

**Server side:**
- `FastMCP("Demo Tools Server")` creates the server instance in one line — equivalent to `Server("weather-stocks-server")` in the raw SDK, but this single object also manages transport and run-loop setup internally.
- `@mcp.tool` on `get_weather` does everything the raw SDK's `list_tools()` + `call_tool()` handlers did, combined and automatic:
  - Function name (`get_weather`) → becomes the tool's `name`
  - Docstring (`"""Get the current weather for a city"""`) → becomes the tool's `description`
  - Type hints (`city: str`, return type `dict`) → auto-generates the `inputSchema` JSON Schema, equivalent to the hand-written schema in the raw SDK version
  - No separate dispatcher needed — when a `call_tool` request comes in for `"get_weather"`, FastMCP internally routes it straight to this function
- `return {"city": city, **data}` — you return a plain Python dict. FastMCP automatically wraps this into the correct MCP content-block format (equivalent to the raw SDK's manual `types.TextContent(type="text", text=json.dumps(result))`).
- `mcp.run()` starts the server with sensible defaults (stdio transport) — equivalent to the raw SDK's `stdio_server()` + `server.run(...)` combination.

**Client side:**
- `Client("server.py")` replaces the raw SDK's three-step setup (`StdioServerParameters` → `stdio_client` → `ClientSession`) with one line. It internally spawns the subprocess, opens the stdio transport, creates a session, and performs the `.initialize()` handshake — all automatically.
- `mcp_client.list_tools()` works the same conceptually as `session.list_tools()` in the raw SDK — it queries the server for its available tools, letting you build `tool_schemas` dynamically without hardcoding anything.
- `mcp_client.call_tool(block.name, block.input)` works the same conceptually as `session.call_tool(...)` — sends the request over the protocol; execution happens inside the server process.
- `result.data` replaces the raw SDK's `result.content[0].text` — FastMCP's client gives you the already-unwrapped, structured result directly, instead of requiring you to manually index into a content-block list and parse out the text field.

---

## 6. Full Step-by-Step Flow (Applies to Both Approaches)

The *conceptual* flow is identical whether you use the raw SDK or FastMCP — only the amount of code you write differs.

**Step 1 — Client launches the server as a subprocess.** The client process starts the server process (`python mcp_server.py` / `server.py`), and the two communicate over stdio (standard input/output pipes) using the MCP protocol's message format.

**Step 2 — Handshake/initialization.** The client and server exchange protocol version and capability information (`session.initialize()` in the raw SDK; done automatically inside FastMCP's `Client` context manager).

**Step 3 — Tool discovery.** The client asks the server "what tools do you have?" (`list_tools()`), and the server responds with each tool's name, description, and input schema — generated manually in the raw SDK, generated automatically by FastMCP from function signatures.

**Step 4 — Schemas handed to Claude.** The client converts the MCP tool listing into the shape Claude's Messages API expects (`name`, `description`, `input_schema`) and passes it as the `tools` parameter in the API call. From Claude's perspective, this is indistinguishable from tools defined any other way — Claude doesn't know or care that these came from an MCP server.

**Step 5 — Claude decides to call a tool.** Same as every earlier example — Claude returns a `tool_use` block with a `name` and `input`, without executing anything itself.

**Step 6 — Client dispatches the call over the MCP protocol**, not via a local dict/if-else lookup. `session.call_tool(...)` / `mcp_client.call_tool(...)` sends a request to the **server process**, which runs the actual tool function *in its own process* and sends the result back over the protocol.

**Step 7 — Result is unwrapped and fed back to Claude.** The raw SDK requires manually reaching into `result.content[0].text`; FastMCP exposes `result.data` directly. Either way, the result is packaged as a `tool_result` and appended to `messages`, and the agentic loop continues exactly as in every previous example (single-agent, multi-agent, or MCP) until `stop_reason == "end_turn"`.

---

## 7. MCP Client vs. MCP Host — And How `mcp_client.py` Plays Both Roles

This distinction is easy to blur together, so it's worth being precise about the terminology:

- **MCP Client** — the specific component that speaks the MCP protocol to one server. In the raw SDK, this is the `ClientSession` object (`session = ClientSession(read, write)`); in FastMCP, this is the `Client` object (`mcp_client = Client("server.py")`). Its job is narrow: handshake, discover tools, send tool-call requests, receive results — nothing more.
- **MCP Host** — the overall application that *embeds* one or more clients and orchestrates everything around them: deciding when to call Claude, managing the conversation/message history, running the agentic loop, deciding what to do with Claude's responses, presenting output to the user. The host is the umbrella term for "the application as a whole."

In official MCP terminology, **the host and the client(s) it uses almost always live in the same process** — "host" isn't a separate piece of infrastructure, it's just the name for the application that *contains* the client logic. A familiar real-world example: Claude Desktop is the *host*; each MCP server you configure in it (filesystem, GitHub, Slack, etc.) gets its own *client* connection inside that same host application.

### How `mcp_client.py` (and `client_agent.py`) Plays Both Roles

Looking at either client script from this guide, it is doing two distinct jobs simultaneously, in the same process:

1. **Acting as the MCP client** — the parts of the code that:
   - Launch the server subprocess (`stdio_client(server_params)` / `Client("server.py")`)
   - Perform the handshake (`session.initialize()` / handled inside FastMCP's context manager)
   - Discover tools (`session.list_tools()` / `mcp_client.list_tools()`)
   - Send tool-execution requests (`session.call_tool(...)` / `mcp_client.call_tool(...)`)

   This is the narrow, protocol-focused role — talking to exactly one MCP server.

2. **Acting as the MCP host** — the parts of the code that:
   - Call the Anthropic API (`client.messages.create(...)`)
   - Maintain the `messages` conversation history
   - Run the `while True` agentic loop, checking `stop_reason`
   - Decide what to do with each `tool_use` block Claude returns
   - Print output to the user

   This is the broader orchestration role — nothing here is MCP-protocol-specific; it's the same agentic loop structure from every earlier example (manual tools, multi-agent orchestration), just with tool calls routed through an MCP client instead of a local dictionary.

So when the script does something like:
```python
async with ClientSession(read, write) as session:      # ← MCP CLIENT role begins here
    await session.initialize()
    mcp_tools = await session.list_tools()

    client = anthropic.Anthropic()                       # ← MCP HOST role begins here
    messages = [{"role": "user", "content": user_question}]
    while True:
        response = client.messages.create(..., tools=tool_schemas, messages=messages)
        ...
        result = await session.call_tool(block.name, block.input)  # ← back to CLIENT role for this line
        ...
```
— the `session` object is the *client*; everything else surrounding it (the Anthropic call, the loop, the message history) is the *host* logic. Both roles are fulfilled by the same Python process and even the same function (`run_agent`), which is exactly why the comment in the original code (`# This script works as MCP host & client both here?`) is correct — there's no architectural rule requiring host and client to be separate programs; splitting them apart is only necessary if you want, for example, one host to manage multiple independent client connections to different MCP servers at once (which is common in real applications like Claude Desktop, but not required for a single-server example like this one).

---

## 8. Summary Cheat Sheet

- **FastMCP** = a high-level, decorator-based wrapper over the official `mcp` Python SDK, for building MCP servers/clients with minimal boilerplate.
- **Why it exists**: manually writing JSON schemas, dispatch logic, and result-wrapping for every tool is repetitive and error-prone; FastMCP auto-derives all of it from plain Python functions (name, docstring, type hints).
- **Raw `mcp` SDK** = the actual protocol implementation FastMCP is built on; using it directly means manually writing `list_tools()`, `call_tool()`, `inputSchema` dicts, and `TextContent` wrapping.
- **The conceptual agentic flow is identical either way**: launch server → handshake → discover tools → hand schemas to Claude → Claude requests a tool → dispatch over the MCP protocol (not a local dict) → server executes in its own process → result returned → fed back into the loop → repeat until `end_turn`.
- **MCP Client** = the narrow component that talks to one server (handshake, discovery, tool calls).
- **MCP Host** = the overall application that embeds the client(s) and drives the agent (calls Claude, manages conversation history, runs the loop).
- **Host and client typically live in the same process** — a single script can (and, in simple examples, usually does) play both roles at once, as seen in both `mcp_client.py` and `client_agent.py` in this guide.
