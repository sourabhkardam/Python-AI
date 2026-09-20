"""
WITHOUT MCP SERVER
==================
Tools are defined directly in the API call.
Your app owns the tool logic — no external server needed.

Use case: You're building one app and need custom tools.
"""

import anthropic
import json

#Note: This program itself is an Agent. Agent is nothing but invoking LLM api with tools and LLM respond with, which tool it want to invoked 
# and we define the logic to call tools and append the tool result and invoke LLM api with the appended tool result and do this LLM api call
# till LLM has desired result. Invoking it again and again is called Agentic loop.

# ─── 1. Your actual tool logic (just plain Python functions) ───────────────────

def get_weather(city: str) -> dict:
    """Simulated weather lookup (replace with real API call)"""
    fake_data = {
        "delhi":   {"temp": 38, "condition": "Sunny",  "humidity": "45%"},
        "london":  {"temp": 14, "condition": "Cloudy", "humidity": "78%"},
        "new york":{"temp": 22, "condition": "Windy",  "humidity": "60%"},
    }
    data = fake_data.get(city.lower(), {"temp": 20, "condition": "Clear", "humidity": "50%"})
    return {"city": city, **data}


def get_stock_price(ticker: str) -> dict:
    """Simulated stock price lookup (replace with real API call)"""
    fake_prices = {
        "AAPL": 189.5,
        "GOOGL": 175.2,
        "TSLA": 245.0,
        "MSFT": 420.0,
    }
    price = fake_prices.get(ticker.upper(), 100.0)
    return {"ticker": ticker.upper(), "price": price, "currency": "USD"}


# ─── 2. Map tool names → functions (your app's dispatcher) ────────────────────

TOOLS = {
    "get_weather":     get_weather,
    "get_stock_price": get_stock_price,
}


# ─── 3. Tool schemas — defined inline in the API call ─────────────────────────

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


# ─── 4. Agentic loop — handles multi-step tool use automatically ───────────────

def run_agent(user_question: str):
    client = anthropic.Anthropic()

    # When content is provided by user, role will be user. Here content (user question) is user provided, so role is user.
    messages = [{"role": "user", "content": user_question}]

    print(f"\n USER: {user_question}")
    print("─" * 60)

    while True:
        # Invoking claude model using claude api
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            tools=TOOL_SCHEMAS,          # ← tools declared right here in the call, from these tools LLM check whether a tool is needed or not and if yes which one to use. Then in response it return if tool is required or not.
            messages=messages
        )

        # If Claude is done (no more tool calls), print final answer
        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"\n CLAUDE: {block.text}")
            break

        # Otherwise, Claude wants to call tools
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"\n → Calling tool: {block.name}({block.input})")

                # Below statement run the actual Python function
                # So, if block.name = get_weather so TOOLS[block.name] will return get_weather. So TOOLS[block.name](**block.input) will become get_weather(**block.input)
                # As block.input will be something like {"city": "Delhi"} so get_weather(**block.input) will become get_weather(**{"city": "Delhi"}).
                # And get_weather(**{"city": "Delhi"}) is equivalent to get_weather(city="Delhi")
                
                result = TOOLS[block.name](**block.input) # block.input is a dictinory object. ** convert dic object to function actual argument
                print(f"   Result: {result}")                

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result)
                })

        
        # Note: As claude API are stateless (api's don't remember anything about past calls), hence we are sending fully history using messages 
        # to claude API. That's why, Add Claude's response + tool results to conversation, then loop. 

        messages.append({"role": "assistant", "content": response.content}) # When content is given by llm, role will be assistant. Here content (response.content) is provided by LLM so we are passing role as assistant.
        messages.append({"role": "user",      "content": tool_results}) # When content is provided by user (we dev are also user), role will be user. Here content (tools result) is user provided, so role is user.


# ─── 5. Run it ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_agent("What's the weather in Delhi, and what's Apple's stock price?")