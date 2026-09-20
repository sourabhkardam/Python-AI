# Understanding AI Agents & Tool Use (Without MCP)

## 1. What is an Agent?

An **agent**, in the context of LLMs like Claude, is a system where the model can:
- Make decisions about **what to do next** based on the current state of a conversation/task
- **Take multiple steps** autonomously (not just one question → one answer)
- **Use tools** (functions, APIs, databases) to gather information or perform actions it cannot do on its own
- **React to results** of its own actions and decide the next step, until it determines the task is complete

The key distinction from a plain chatbot: a plain LLM call is a single request → single response. An **agent** wraps the LLM in a **loop**, where the LLM's output can trigger actions, and the results of those actions are fed back in, potentially triggering more actions — until the LLM decides it's done.

> Important: The LLM itself does not "act" in the world. It only **decides and requests**. Your code (or an external system) is what actually **executes** actions. This separation is central to how agents work.

---

## 2. Can an Agent Exist Without Tools?

Yes — but it's a limited/degenerate case.

- An LLM with **no tools** can still show some "agentic" behavior in a narrow sense: e.g., multi-turn reasoning, planning steps in text, self-correction across a conversation.
- However, without tools, it **cannot fetch real-world/live data**, **cannot take real actions** (send an email, query a database, call an API), and is limited entirely to what it can generate from its own knowledge and the conversation context.
- Most of what people mean by "AI agent" today implies **tool use** — the ability to go outside the model's own knowledge/generation and interact with the real world (weather APIs, stock prices, databases, file systems, etc.).

So: an agent *can* technically exist without tools, but it's the addition of **tools + a loop** that makes agents genuinely useful.

---

## 3. How Does an Agent Work Internally? (The Agentic Loop)

The **agentic loop** is the core mechanism. At a high level:

```
1. Send user query + available tool definitions to the LLM
2. LLM responds with either:
     a) A final answer (done) → exit loop
     b) A request to call one or more tools (not done yet)
3. If (b): your code executes the requested tool(s) with the arguments the LLM provided
4. Send the tool results back to the LLM (as part of conversation history)
5. Go back to step 2 — repeat until the LLM gives a final answer
```

This loop is often implemented as a `while True` loop in code, breaking when the model signals it's finished (e.g., `stop_reason == "end_turn"` in Claude's API).

**Critical point:** the LLM never executes the tool itself. It only ever returns a *structured request* ("please run this function with these arguments"). The actual execution always happens in your application code (or, in MCP's case, in an external MCP server that your application talks to).

---

## 4. Agent With Tools — WITHOUT MCP (Local/Native Tools Pattern)

This is the pattern demonstrated in the example Python program. Here, **you define and own the tools directly in your app** — no external protocol or server involved.

### 4.1 The Building Blocks

| Component | Purpose |
|---|---|
| **Tool functions** | Plain Python functions that do the real work (e.g., `get_weather`, `get_stock_price`) |
| **`TOOLS` dict** | Dispatcher mapping tool *name* (string) → the actual *function* to call |
| **`TOOL_SCHEMAS`** | JSON schema per tool describing its `name`, `description`, and `input_schema` (expected arguments) — sent to Claude on every API call so it knows what tools exist |
| **Agentic loop (`run_agent`)** | Drives the conversation: calls Claude, checks if a tool is requested, executes it, sends result back, repeats |

### 4.2 Example Program Structure (recap)

```python
def get_weather(city: str) -> dict: ...
def get_stock_price(ticker: str) -> dict: ...

TOOLS = {
    "get_weather": get_weather,
    "get_stock_price": get_stock_price,
}

TOOL_SCHEMAS = [
    {"name": "get_weather", "description": "...", "input_schema": {...}},
    {"name": "get_stock_price", "description": "...", "input_schema": {...}},
]

def run_agent(user_question):
    messages = [{"role": "user", "content": user_question}]
    while True:
        response = client.messages.create(model=..., tools=TOOL_SCHEMAS, messages=messages)

        if response.stop_reason == "end_turn":
            # print final text, break
            break

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = TOOLS[block.name](**block.input)   # <-- ACTUAL TOOL CALL
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result)
                })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
```

### 4.3 Step-by-Step Internal Flow

**Step 1 — Initial API call**
```python
response = client.messages.create(..., tools=TOOL_SCHEMAS, messages=messages)
```
The user's question and the tool schemas are sent to Claude. Claude does **not** execute anything here — it only decides, using the tool `name`/`description`/`input_schema`, whether a tool is needed and which one.

**Step 2 — Claude responds with a decision (not an execution)**
Claude's response (`response.content`) contains either:
- Just `text` blocks with `stop_reason == "end_turn"` → Claude is done, no tool needed.
- One or more `tool_use` blocks with `stop_reason == "tool_use"` → Claude wants tool(s) run.

Example raw response when Claude wants two tools at once:
```json
{
  "role": "assistant",
  "stop_reason": "tool_use",
  "content": [
    { "type": "text", "text": "I'll check the weather in Delhi and Apple's stock price." },
    { "type": "tool_use", "id": "toolu_01A1B2C3", "name": "get_weather", "input": { "city": "Delhi" } },
    { "type": "tool_use", "id": "toolu_01D4E5F6", "name": "get_stock_price", "input": { "ticker": "AAPL" } }
  ]
}
```
Notes:
- `stop_reason` is the signal the loop checks to decide whether to continue.
- Claude can request **multiple tool calls in a single response** — no need for one round-trip per tool.
- Each `tool_use` block has a unique `id` — this must be echoed back in the matching `tool_result` so Claude can match results to requests.

**Step 3 — Your code executes the tool (the actual "tool call")**
```python
result = TOOLS[block.name](**block.input)
```
This is the **exact line where real code execution happens** — driven entirely by your Python program, not by Claude. Claude only *asked*; your dispatcher *looks up* the function by name and *runs* it with the arguments Claude supplied.

**Step 4 — Results are packaged and sent back**
```python
tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(result)})
messages.append({"role": "assistant", "content": response.content})  # Claude's tool_use request
messages.append({"role": "user", "content": tool_results})           # the results
```
The conversation history now includes: user question → Claude's tool_use request → the actual tool output (labeled `"user"` role per API convention, tagged with `tool_use_id`).

**Step 5 — Loop back to Step 1**
`client.messages.create(...)` is called again with updated `messages`. Claude now has real data and can either:
- Request more tools (loop continues), or
- Produce a final answer (`stop_reason == "end_turn"`) → loop exits.

Example final response:
```json
{
  "role": "assistant",
  "stop_reason": "end_turn",
  "content": [
    { "type": "text", "text": "The weather in Delhi is sunny at 38°C with 45% humidity. Apple (AAPL) is trading at $189.50." }
  ]
}
```

### 4.4 Who Does What

| Actor | Responsibility |
|---|---|
| **Claude (the model/API)** | Decides *if* a tool is needed, *which* one, and *what arguments* to pass. Never executes code. |
| **Your Python program** | Reads the `tool_use` request, looks up the real function via `TOOLS[block.name]`, executes it, sends the result back into the loop. |

**One-line mental model:** *Claude proposes, your code disposes, loop until `end_turn`.*

---

## 5. How This Differs From MCP (Preview — to study in detail later)

MCP (Model Context Protocol) solves a **different problem**: tool distribution and standardization — not the core agentic loop itself.

- **Local/native tools (what we built):** tool logic lives in your own app; you hand-write `TOOL_SCHEMAS` and a `TOOLS` dispatcher.
- **MCP:** tool logic lives in an external MCP server; your app/client discovers the server's tools and schemas via a standard protocol instead of hardcoding them. This lets the same MCP server (e.g., a GitHub or Slack server) be reused across many different apps/agents.

**Key insight:** the core agentic loop mechanics — *Claude proposes a tool call → code executes it → result goes back → repeat* — are the same either way. MCP only changes **where the tool implementation and schema come from** (external/standardized vs. local/hardcoded), not **how** Claude decides to use tools.

---

## 6. Summary Cheat Sheet

- **Agent** = LLM + loop + (optionally) tools, enabling multi-step autonomous decision-making.
- **Agent without tools** = possible but limited to reasoning/generation only; no real-world interaction.
- **Agentic loop** = call model → check if tool requested → execute tool → feed result back → repeat until model signals completion (`end_turn`).
- **Tools without MCP** = you define functions + schemas + a dispatcher yourself, all living in your own codebase.
- **The model never executes tools** — it only emits a structured `tool_use` request (name + arguments + unique id).
- **Your code is the executor** — the actual tool call happens at the line where you look up and invoke the function by name.
- **MCP** = same loop, but tool implementation/schema comes from an external, standardized server instead of your own hardcoded dictionary.
