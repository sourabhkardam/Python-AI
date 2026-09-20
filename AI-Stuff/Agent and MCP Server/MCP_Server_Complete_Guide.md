# MCP Server — Complete Guide

> A full walkthrough from first principles to working Python code.

---

## Table of Contents

1. [What is MCP?](#1-what-is-mcp)
2. [The Problem MCP Solves](#2-the-problem-mcp-solves)
3. [Before MCP vs After MCP](#3-before-mcp-vs-after-mcp)
4. [The Three Pieces of MCP](#4-the-three-pieces-of-mcp)
5. [Can We Declare Tools Without MCP?](#5-can-we-declare-tools-without-mcp)
6. [Direct Tools vs MCP Tools — Comparison](#6-direct-tools-vs-mcp-tools--comparison)
7. [Python Example — Without MCP](#7-python-example--without-mcp)
8. [Python Example — With MCP](#8-python-example--with-mcp)
9. [Side-by-Side Difference](#9-side-by-side-difference)
10. [When to Use What](#10-when-to-use-what)

---

## 1. What is MCP?

**MCP** stands for **Model Context Protocol**. It is an open standard created by Anthropic that defines a universal way for AI models to communicate with external tools, data sources, and services.

Think of MCP as a **universal plug**. Just like a USB port lets you connect any USB device to any computer — MCP lets any AI model connect to any tool that follows the MCP standard.

Before MCP, every AI-to-tool integration was custom built. After MCP, you build the connector once and any MCP-compatible AI can use it instantly.

---

## 2. The Problem MCP Solves

Imagine you hired a brilliant assistant (an AI like Claude). They're incredibly smart, but they sit in a locked room. Every time they need to:

- Check your calendar
- Read your emails
- Look up a file
- Run some code

...they can't do it themselves. They have to shout at you through the door, you go check, come back, and tell them. It's slow, lossy, and frustrating.

**MCP gives that assistant a standardized key** that works on any system — email, calendar, GitHub, Slack, your database — so they can go check things themselves.

### The Old World (Before MCP)

Each AI integration was custom-built one at a time:

- Want Claude to read Gmail? Write a one-off Gmail connector.
- Want it to check Notion too? Write another custom connector.
- Want both to work together? Good luck — they were never designed to talk to each other.

Every tool needed its own translation layer. Developers duplicated work constantly. The AI was stuck answering from memory, not from live data.

### The New World (After MCP)

Anthropic created an open standard. Any tool that follows MCP can immediately talk to any AI that supports MCP.

- Build the connector once → use it everywhere
- AI reads live data and takes real actions, not just answering from memory
- Adding a new tool = plug in, no custom glue code needed

---

## 3. Before MCP vs After MCP

### Before MCP — Custom connectors everywhere

```
AI Model
  |--- custom code ---> Gmail
  |--- custom code ---> Slack
  |--- custom code ---> GitHub
  |--- custom code ---> Database
```

Every arrow is a one-off, brittle, hard-to-maintain integration. Adding a new tool means writing more custom glue code.

### After MCP — One universal standard

```
AI Model
    |
    ▼
MCP Protocol (one standard)
    |--- MCP ---> Gmail MCP Server
    |--- MCP ---> Slack MCP Server
    |--- MCP ---> GitHub MCP Server
    |--- MCP ---> Database MCP Server
    |--- MCP ---> Any new tool (plug in instantly)
```

The AI speaks one language. Every tool speaks the same language back.

---

## 4. The Three Pieces of MCP

Think of it like a restaurant:

| MCP Piece | Restaurant Analogy | What it does |
|---|---|---|
| **MCP Host** | The customer | The AI app (Claude, Cursor, etc.) that wants to do things |
| **MCP Client** | The waiter | Lives inside the AI app, manages connections to servers |
| **MCP Server** | The kitchen | A program that gives the AI access to one specific tool |

The genius is: the waiter (client) speaks the **exact same language** to every kitchen. The kitchens don't need to know anything about each other.

### A Real-World Example

You ask: *"What meetings do I have today, and draft a Slack message to my team summarizing them."*

**Without MCP:**
- AI can't see your calendar — it makes something up, or asks you to paste meetings manually
- AI can't send Slack messages — gives you text to copy-paste yourself
- You are the middleman for every step

**With MCP:**
1. AI connects to a **Google Calendar MCP Server**
2. AI connects to a **Slack MCP Server**
3. AI asks Calendar MCP: *"What's on the calendar today?"* → gets real data
4. AI drafts a summary using that live data
5. AI asks Slack MCP: *"Post this to #team-updates"* → done

You said one sentence. The AI did a multi-step workflow across two real external systems, with zero copy-pasting from you.

---

## 5. Can We Declare Tools Without MCP?

**Yes, absolutely.** You can define tools directly inside the API call itself — no MCP server needed.

```python
response = client.messages.create(
    model="claude-opus-4-5",
    tools=[
        {
            "name": "get_weather",
            "description": "Get current weather for a city",
            "input_schema": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"}
                },
                "required": ["city"]
            }
        }
    ],
    messages=[{"role": "user", "content": "What's the weather in Delhi?"}]
)
```

The AI sees the tool, decides to call it, returns a `tool_use` block — and then your own code handles the actual logic. You run the function, send back the result, and the AI responds.

**This works great.** MCP is not a requirement to give AI tools.

---

## 6. Direct Tools vs MCP Tools — Comparison

| | Direct Tools (in API) | MCP Server |
|---|---|---|
| **Who writes the logic?** | You, in your app's code | A separate server program |
| **Who can reuse it?** | Only your app | Any MCP-compatible AI app |
| **Setup complexity** | Simple | More setup needed |
| **Best for** | App-specific logic | Shared, reusable integrations |
| **Tool schemas** | Hardcoded in your app | Discovered dynamically |
| **Example** | Search our internal database | Connect to Gmail — usable by Claude, Cursor, any agent |

**The analogy:** Direct tools are like cooking in your own kitchen for yourself. MCP servers are like opening a restaurant — the same food, but now anyone can come eat.

MCP becomes valuable when:
- You want the **same tool usable across many different AI apps**
- You're building a **tool for others to use** (e.g. a company publishing a GitHub MCP server)
- You're building complex **agentic systems** where many tools need to be managed as separate services

---

## 7. Python Example — Without MCP

One self-contained file. Tool schemas, Python functions, and the agentic loop all live together.

```python
"""
WITHOUT MCP SERVER
Tools are defined directly in the API call.
Your app owns the tool logic — no external server needed.
"""

import anthropic
import json

# 1. Your actual tool logic (plain Python functions)

def get_weather(city: str) -> dict:
    fake_data = {
        "delhi":    {"temp": 38, "condition": "Sunny",  "humidity": "45%"},
        "london":   {"temp": 14, "condition": "Cloudy", "humidity": "78%"},
        "new york": {"temp": 22, "condition": "Windy",  "humidity": "60%"},
    }
    data = fake_data.get(city.lower(), {"temp": 20, "condition": "Clear", "humidity": "50%"})
    return {"city": city, **data}


def get_stock_price(ticker: str) -> dict:
    fake_prices = {"AAPL": 189.5, "GOOGL": 175.2, "TSLA": 245.0, "MSFT": 420.0}
    price = fake_prices.get(ticker.upper(), 100.0)
    return {"ticker": ticker.upper(), "price": price, "currency": "USD"}


# 2. Map tool names → functions (your app's dispatcher)

TOOLS = {
    "get_weather":     get_weather,
    "get_stock_price": get_stock_price,
}


# 3. Tool schemas — defined inline in the API call

TOOL_SCHEMAS = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a city",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name, e.g. Delhi"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "get_stock_price",
        "description": "Get the current stock price for a ticker symbol",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock ticker, e.g. AAPL"}
            },
            "required": ["ticker"]
        }
    }
]


# 4. Agentic loop — handles multi-step tool use automatically

def run_agent(user_question: str):
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": user_question}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            tools=TOOL_SCHEMAS,          # ← tools declared right here
            messages=messages
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"CLAUDE: {block.text}")
            break

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = TOOLS[block.name](**block.input)   # ← calls local function
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result)
                })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user",      "content": tool_results})


if __name__ == "__main__":
    run_agent("What's the weather in Delhi, and what's Apple's stock price?")
```

**To run:**
```bash
pip install anthropic
python without_mcp.py
```

---

## 8. Python Example — With MCP

Two files: a server that exposes tools, and a client that connects to it.

### Part 1: The MCP Server (`mcp_server.py`)

Standalone program. Exposes tools over the MCP protocol. Knows nothing about Claude or your app.

```python
"""
WITH MCP SERVER — Part 1: The Server
Any MCP-compatible AI app can connect to this server and use its tools.
"""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
import json
import asyncio

server = Server("weather-stocks-server")


# Declare what tools this server exposes

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


# Handle tool calls — the actual logic lives here

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


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

### Part 2: The MCP Client (`mcp_client.py`)

Connects to the server, discovers tools dynamically, runs the agentic loop.

```python
"""
WITH MCP SERVER — Part 2: The Client
Connects to mcp_server.py and uses its tools — without knowing the tool logic.
mcp_server.py is launched automatically as a subprocess.
"""

import anthropic
import json
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def run_agent(user_question: str):
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            # Discover tools from server — no hardcoding needed
            await session.initialize()
            mcp_tools = await session.list_tools()

            tool_schemas = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }
                for tool in mcp_tools.tools
            ]

            client = anthropic.Anthropic()
            messages = [{"role": "user", "content": user_question}]

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
                            print(f"CLAUDE: {block.text}")
                    break

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = await session.call_tool(block.name, block.input)  # ← calls server
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result.content[0].text
                        })

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user",      "content": tool_results})


if __name__ == "__main__":
    asyncio.run(run_agent("What's the weather in Delhi, and what's Apple's stock price?"))
```

**To run:**
```bash
pip install anthropic mcp
python mcp_client.py    # automatically spawns mcp_server.py
```

---

## 9. Side-by-Side Difference

The single most important line to compare:

```python
# Without MCP — calls a local Python function
result = TOOLS[block.name](**block.input)

# With MCP — calls the remote MCP server
result = await session.call_tool(block.name, block.input)
```

Everything else in the agentic loop is identical. The difference is purely where the tool logic lives.

| | `without_mcp.py` | `mcp_server.py` + `mcp_client.py` |
|---|---|---|
| **Files needed** | 1 | 2 |
| **Tool logic location** | Inside your app | Separate server process |
| **Tool schemas** | Hardcoded in your app | Discovered dynamically |
| **Reusable by other apps?** | No | Yes — any MCP client can connect |
| **Setup complexity** | Low | Moderate |
| **Right choice when** | Building one app | Building shared/reusable tools |

---

## 10. When to Use What

### Use direct tools (without MCP) when:
- You're building a **single application** and don't need to share tools
- You want **simplicity** — one file, no extra processes
- The tools are **specific to your app's logic** (e.g. querying your own database)
- You're **prototyping** or learning

### Use MCP when:
- You want the **same tools usable across multiple AI apps** (Claude, Cursor, custom agents)
- You're **publishing tools for others** to consume (e.g. a SaaS company building a GitHub MCP server)
- You're building **complex agentic systems** where tools need to be managed as independent services
- You want **hot-swappable tools** — update the server without touching your AI app

### The mental model

> Direct tools = cooking in your own kitchen for yourself.
>
> MCP server = opening a restaurant. Same food, but now anyone can come eat.

---

## Key Takeaways

- **MCP is a standard, not a requirement.** You can give AI tools without it.
- **MCP solves the sharing problem**, not the capability problem.
- **The agentic loop is identical** in both approaches — only where the tool logic lives differs.
- **MCP is the foundation of agentic AI** — it's what lets AI step out of the chat box and take real actions in the real world.
- Before MCP, AI was like a genius locked in a library. MCP is the door.
