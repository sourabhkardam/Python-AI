"""
WITH MCP SERVER — Part 1: The Server
=====================================
This is a standalone MCP server that exposes weather and stock tools.
It runs as a separate process and ANY MCP-compatible AI app can connect to it.

Install deps:  pip install mcp
Run directly:  python mcp_server.py

Once running, ANY agent (Claude, Cursor, your custom app) can plug in
and get these tools — no copy-pasting tool logic into each app.
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