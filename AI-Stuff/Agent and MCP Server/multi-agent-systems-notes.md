# Multi-Agent Systems — Detailed Notes

## 1. What is a Multi-Agent System?

A **multi-agent system** is an architecture where, instead of a single LLM agent handling an entire task alone, the task is broken across **multiple agents**, each with its own role, tools, system prompt, and (often) its own independent agentic loop — coordinating with each other to solve something bigger than any single agent should handle alone.

Instead of one generalist agent doing everything (research + writing + coding + reviewing), you have specialized agents, each good at one thing, working together under some form of coordination.

---

## 2. Why We Need Multi-Agent Systems

A single agent starts to break down as tasks grow in complexity:

1. **Too many tools confuse the model.** Give one agent 30 tools, and it gets worse at picking the right one — tool descriptions overlap and confuse the decision-making.
2. **Context window bloat.** A single agent doing research + writing + coding accumulates a huge, messy conversation history. Long, mixed-purpose context degrades response quality (sometimes called "context rot" — the more unrelated context a model holds, the less earlier context contributes usefully to the output).
3. **Separation of concerns.** Just like in software engineering, it's cleaner to have one agent that's *really good* at research and another that's *really good* at writing, rather than one generalist trying to do both.
4. **Specialization = better prompts.** A "Research Agent" can have a system prompt entirely focused on searching/verifying facts. A "Writer Agent" can have a system prompt entirely focused on tone/structure. Mixing both into one prompt dilutes both.
5. **Parallelism.** Independent sub-tasks (e.g., "research topic A" and "research topic B") can run concurrently instead of one agent doing them serially — saving real wall-clock time.
6. **Reliability/debuggability.** If something breaks, it's easier to isolate which agent failed, rather than debugging one giant tangled prompt/conversation.
7. **Context isolation.** A sub-agent can explore large amounts of information (e.g., many search results, many files) without cluttering the main/orchestrator conversation — it only reports back the relevant conclusions.

---

## 3. Common Multi-Agent Patterns

| Pattern | Description |
|---|---|
| **Orchestrator–Worker** | One "manager" agent breaks a task into subtasks and delegates each to specialized worker agents, then combines results. |
| **Sequential Pipeline** | Agent A's output becomes Agent B's input becomes Agent C's input (like an assembly line). |
| **Peer-to-peer / Debate** | Multiple agents critique or negotiate with each other before producing a final answer. |
| **Hierarchical** | Multi-level orchestration — a top orchestrator delegates to mid-level orchestrators, which delegate to workers. |

The most common and practical starting pattern is **Orchestrator–Worker**, usually implemented via a technique called **"agents as tools."**

---

## 4. Key Idea: "Agents as Tools"

This is the cleanest way to build multi-agent systems without a heavy framework: **a sub-agent is just a tool — except instead of the tool being a simple function (like `get_weather`), the tool itself runs its own internal agentic loop.**

The orchestrator doesn't know or care that "call `research_agent`" secretly triggers *another* full Claude conversation with its own tools — to the orchestrator, it just looks like calling a function that returns a result. This is exactly the same mechanical pattern as calling any normal tool (`TOOLS[block.name](**block.input)`), except the function being called happens to contain a full nested agent conversation inside it.

---

## 5. Manual Multi-Agent Example (No Framework, No MCP)

This example builds an orchestrator with two specialized worker agents — a Research Agent (has its own tool) and a Writer Agent (no tools, pure generation) — using only the raw Anthropic Messages API and plain Python.

```python
import anthropic
import json

client = anthropic.Anthropic()

# ─── 1. Worker Agent: Research Agent (has its own tool + own loop) ─────────────

def fake_search(query: str) -> dict:
    """Simulated search tool used only by the Research Agent"""
    fake_db = {
        "electric cars": "EV sales grew 35% globally in 2025, led by China and Europe.",
        "solar energy": "Solar panel costs dropped 20% due to new manufacturing techniques.",
    }
    return {"query": query, "result": fake_db.get(query.lower(), "No data found.")}

RESEARCH_TOOLS = {"fake_search": fake_search}
RESEARCH_TOOL_SCHEMAS = [{
    "name": "fake_search",
    "description": "Search for factual information on a topic",
    "input_schema": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"]
    }
}]

def research_agent(topic: str) -> str:
    """A self-contained agent: runs its OWN agentic loop with its OWN tools."""
    messages = [{"role": "user", "content": f"Research this topic and summarize key facts: {topic}"}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=500,
            system="You are a research specialist. Use the search tool to find facts before answering.",
            tools=RESEARCH_TOOL_SCHEMAS,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            return "".join(b.text for b in response.content if hasattr(b, "text"))

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = RESEARCH_TOOLS[block.name](**block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result)
                })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})


# ─── 2. Worker Agent: Writer Agent (no tools — pure generation) ────────────────

def writer_agent(research_notes: str) -> str:
    """A simpler agent — no tools, just transforms research into a polished blurb."""
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=400,
        system="You are a concise writer. Turn research notes into a short, engaging paragraph for a newsletter.",
        messages=[{"role": "user", "content": f"Write a short paragraph based on these notes:\n\n{research_notes}"}]
    )
    return "".join(b.text for b in response.content if hasattr(b, "text"))


# ─── 3. Orchestrator: exposes BOTH agents as "tools" ───────────────────────────

def call_research_agent(topic: str) -> dict:
    return {"summary": research_agent(topic)}

def call_writer_agent(research_notes: str) -> dict:
    return {"draft": writer_agent(research_notes)}

ORCHESTRATOR_TOOLS = {
    "call_research_agent": call_research_agent,
    "call_writer_agent": call_writer_agent,
}

ORCHESTRATOR_TOOL_SCHEMAS = [
    {
        "name": "call_research_agent",
        "description": "Delegate research on a topic to the specialized Research Agent. Returns a factual summary.",
        "input_schema": {
            "type": "object",
            "properties": {"topic": {"type": "string"}},
            "required": ["topic"]
        }
    },
    {
        "name": "call_writer_agent",
        "description": "Delegate writing to the specialized Writer Agent. Give it research notes; it returns a polished paragraph.",
        "input_schema": {
            "type": "object",
            "properties": {"research_notes": {"type": "string"}},
            "required": ["research_notes"]
        }
    }
]

def run_orchestrator(user_task: str):
    messages = [{"role": "user", "content": user_task}]
    print(f"\nUSER: {user_task}\n" + "─" * 60)

    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            system="You are an orchestrator. Break tasks into research + writing steps and delegate to the right agent.",
            tools=ORCHESTRATOR_TOOL_SCHEMAS,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"\nFINAL OUTPUT:\n{block.text}")
            break

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"\n→ Orchestrator delegating to: {block.name}({block.input})")
                result = ORCHESTRATOR_TOOLS[block.name](**block.input)  # ← triggers a SUB-AGENT LOOP
                print(f"   Sub-agent returned: {result}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result)
                })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    run_orchestrator("Write a short newsletter blurb about electric cars.")
```

### 5.1 Detailed Code Flow

**Step 1 — Orchestrator is called first**, same as a single-agent setup: user task → `client.messages.create(...)` with `ORCHESTRATOR_TOOL_SCHEMAS`. The orchestrator's system prompt tells it its job is to *delegate*, not do the work itself.

**Step 2 — Orchestrator decides to delegate**, returning a `tool_use` block, e.g.:
```json
{ "type": "tool_use", "name": "call_research_agent", "input": { "topic": "electric cars" } }
```
This looks identical to any normal tool call from Claude's point of view — Claude has no idea this "tool" is secretly another full agent.

**Step 3 — The critical difference from single-agent tools:**
```python
result = ORCHESTRATOR_TOOLS[block.name](**block.input)
# → call_research_agent(topic="electric cars")
# → which internally calls research_agent("electric cars")
```
This single dispatch line triggers an **entire nested agentic loop** (`research_agent`'s own `while True` loop, own tool `fake_search`, own system prompt, own back-and-forth with Claude). From the orchestrator's perspective, it just "called a function" — but that function contains a whole sub-agent conversation inside it.

**Step 4 — The sub-agent runs to completion internally**, using `fake_search` as needed, and returns a plain string summary once *its own* `stop_reason == "end_turn"` fires. This return value bubbles back up as the `result` of the orchestrator's tool call.

**Step 5 — Result flows back to the orchestrator** exactly like any tool result:
```python
tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(result)})
```

**Step 6 — Orchestrator loop continues.** Now that it has research notes, it likely calls `call_writer_agent` next, which similarly triggers `writer_agent(...)` — a much simpler agent with **no tools at all**, just one direct `client.messages.create` call.

**Step 7 — Orchestrator finishes.** Once it has both research and a draft, it produces a final `end_turn` response and the outer loop exits.

### 5.2 Key Architectural Insights

- **Nesting is invisible at each layer.** The orchestrator doesn't know `call_research_agent` runs a whole sub-loop; it just sees "a function that returns a summary." This is what makes multi-agent systems composable — you can nest agents arbitrarily deep, and each layer only needs to understand its immediate tools.
- **Each agent can have a totally different system prompt, tool set, and even model.** E.g., the Research Agent could use a cheaper/faster model since it's just fact-gathering, while the orchestrator uses a stronger model since it's making higher-level decisions.
- **Context isolation.** The Research Agent's internal `messages` history (with all its search back-and-forth) never pollutes the orchestrator's `messages` — the orchestrator only sees the final summary. This keeps each agent's context clean and focused.
- **This scales to real frameworks.** What's shown here by hand is essentially what tools like LangGraph, CrewAI, or Claude's own "subagents" (in the Claude Agent SDK / Claude Code) do under the hood — they formalize this "agent-as-a-callable-tool" pattern with more infrastructure (parallel execution, retries, structured handoffs).

### 5.3 Caveat: Sequential vs Parallel Execution

This manual example runs sub-agents **synchronously and sequentially** (one finishes before the next starts) for simplicity. In production multi-agent systems, independent sub-agent calls (e.g., two unrelated research tasks) are often run **in parallel** using `asyncio` or threading, since they don't depend on each other's results — a key performance benefit of multi-agent architectures over single-agent ones. The manual code shown here does **not** do this automatically — you'd need to add `asyncio.gather(...)` (or similar) yourself around the dispatch loop to get true parallelism.

---

## 6. The Built-In `Task` Tool (Claude Agent SDK)

Anthropic's **Claude Agent SDK** ships a **built-in `Task` tool** that formalizes the exact "agents as tools" pattern shown above — instead of you hand-writing the dispatcher and sub-agent loops, the SDK provides this natively.

Confirmed from Anthropic's documentation:
- The Agent SDK ships with 15+ built-in tools, and `Task` is listed explicitly as: **"Delegate work to subagents."**
- Subagents enable **parallelization** — you can spin up multiple subagents to work on different tasks simultaneously.
- Subagents help **manage context** — they use their own isolated context windows and only send relevant information back to the orchestrator, rather than their full context. This makes them ideal for tasks that require sifting through large amounts of information where most of it won't be useful.

### 6.1 Example Configuration Pieces (illustrative, not a runnable script)

These three snippets were shown as **illustrations of shapes/structures**, not as a program with real control flow — they don't call each other, and nothing in them literally executes anything by itself.

**(a) `coordinator_config` — the orchestrator's own setup**
```python
coordinator_config = {
    "model": "claude-haiku-4-5",      # cost-efficient for orchestration
    "system": """You are a research coordinator.
Decompose tasks and delegate to specialized subagents.
Specify research goals and quality criteria.
Do NOT provide step-by-step procedures.""",
    "tools": [
        {"type": "task", "name": "Task"},   # built-in Task tool type
    ],
    "allowedTools": ["Task", "compile_report"]  # Task MUST be explicitly allowed
}
```
- `model` — the coordinator uses a cheaper/faster model (Haiku) since its job is decomposition and delegation, not deep reasoning or content generation — a deliberate cost optimization.
- `system` — explicitly instructs the coordinator to describe **goals and quality bars**, not **procedures**. If the coordinator writes step-by-step instructions for subagents, it defeats the purpose of specialization — you want the subagent to bring its own judgment.
- `"tools": [{"type": "task", "name": "Task"}]` — declares `Task` as a special **built-in tool type** (not a custom function schema like `get_weather`). When the SDK sees `"type": "task"`, it knows this isn't a user-defined tool — it's the SDK's native subagent-spawning mechanism.
- `"allowedTools"` — a permissions allowlist. `"Task"` **must** be explicitly included here, otherwise the coordinator wouldn't be allowed to spawn subagents, regardless of whether `Task` is declared in `tools`. Tools must be both *declared* and *allowed*.

**(b) `task_tool_call` — anatomy of ONE delegation request (standalone example only)**
```python
task_tool_call = {
    "type": "tool_use",
    "id":   "tu_web_search_001",
    "name": "Task",
    "input": {
        # AgentDefinition fields
        "description":   "Web Search Specialist",    # label
        "prompt": """Research goal: Find 5-8 recent papers (2022-2025)
on offshore wind energy environmental impact in the EU.
Quality criteria: peer-reviewed, include key findings,
flag conflicting conclusions. Return as structured JSON.""",
        # Subagent scoped to its role — NO Task tool here
        "allowed_tools": ["web_search", "read_url"],
        "model": "claude-haiku-4-5"
    }
}
```
**Important clarification (from discussion):** `task_tool_call` is **not consumed, referenced, or executed anywhere** in this set of examples. It is not part of `coordinator_response`'s three tool calls (those have different ids: `tu_env`, `tu_econ`, `tu_policy`). It exists purely as a **standalone teaching example** — shown in isolation to explain what one `Task` delegation's `input` (its `AgentDefinition`) looks like, before showing the more complex parallel example. In a real running system, a block shaped exactly like this would be **generated by Claude's own API response** (when the coordinator decides to delegate) — it is never something your own code constructs and sends *to* Claude.

Structurally it's identical to any `tool_use` block (`type`, `id`, `name`, `input`) — the only difference is `name` is literally `"Task"`, and `input` follows the special `AgentDefinition` shape:
- `description` — a short label for this subagent's role (for logs/UI/tracking).
- `prompt` — the entire task brief handed to the subagent. Notice it specifies **goals and quality criteria** (e.g. "5-8 recent papers," "peer-reviewed," "flag conflicting conclusions") but never says *how* to search or *which* queries to run — consistent with "do not provide step-by-step procedures."
- `allowed_tools` — the subagent's **own scoped tool permissions**, separate from the coordinator's. Crucially, `"Task"` is **not** in this list — this prevents the subagent from spawning its own sub-subagents (avoiding uncontrolled recursive delegation).
- `model` — each subagent can independently choose its own model, decoupled from the coordinator's model choice.

**(c) `coordinator_response` — parallel delegation in one turn**
```python
coordinator_response = {
    "role": "assistant",
    "content": [
        {"type": "text", "text": "Researching in parallel across 3 domains."},
        {"type": "tool_use", "id": "tu_env", "name": "Task", "input": {"description": "Environmental Researcher", ...}},
        {"type": "tool_use", "id": "tu_econ", "name": "Task", "input": {"description": "Economic Data Researcher", ...}},
        {"type": "tool_use", "id": "tu_policy", "name": "Task", "input": {"description": "EU Policy Analyst", ...}},
    ]
    # ALL THREE in the same content array = PARALLEL execution
    # Separate turns = sequential anti-pattern
}
```
The key structural point: **multiple `tool_use` blocks in a single `content` array are independent requests that can be executed concurrently**, because none of them depends on another's result (they weren't produced in response to seeing each other's output).
- **Same message, 3 `Task` calls** → the SDK can dispatch all three subagent loops **in parallel**, directly reflecting the documented benefit that subagents enable parallelization.
- **The "anti-pattern" comment** warns against a subtly wasteful design: if the coordinator instead called `Task` once, waited for that full subagent loop to finish, *then* called `Task` again for the next domain, you'd get needless serialization — three independent research tasks running one after another instead of concurrently, wasting wall-clock time for no benefit.

---

## 7. Internal Flow of the Built-In `Task` Tool — Step by Step

This maps the `Task` tool's internal working directly onto the manual multi-agent example built earlier, so the parallels are explicit.

**Step 1 — Coordinator reasons and decides to delegate**
The coordinator LLM call runs exactly like any Claude API call. It sees the user's task + the `Task` tool's presence, and decides this task needs to be broken up (same as the manual orchestrator asking "should I call `call_research_agent`?"). It returns one or more `tool_use` blocks named `"Task"`, each with an `AgentDefinition` in `input`. Nothing has executed yet — the model only proposes.

**Step 2 — The SDK's control layer intercepts the `Task` call**
In the manual version, *your own Python `while` loop* saw `block.type == "tool_use"` and manually dispatched via `TOOLS[block.name](**block.input)`. In the Agent SDK, this dispatch logic is **built into the SDK/CLI runtime itself** — the CLI subprocess handles tool execution, API calls to Claude, and external MCP server management, while your own application code never directly calls the Anthropic API — it delegates that to the CLI. Conceptually the SDK is running **the same `while True` loop pattern** you wrote by hand — just inside Anthropic's own infrastructure.

**Step 3 — SDK spins up a brand-new agent instance per `Task` call**
When the SDK sees `name == "Task"`, instead of calling a plain function like `call_research_agent(topic)`, it **instantiates a whole new agent session** using the `AgentDefinition` fields as that session's configuration:
- `prompt` → becomes that subagent's task/system framing (equivalent to the message passed into `research_agent(topic)`)
- `allowed_tools` → becomes that subagent's own tool allowlist (equivalent to `RESEARCH_TOOL_SCHEMAS` + `RESEARCH_TOOLS`, scoped only to that agent)
- `model` → that subagent gets its own model choice, independent of the coordinator's

This maps 1:1 onto `research_agent()`: it opened its **own `messages` list**, ran its **own internal `while True` loop**, with its **own tools**, and returned a single result when done.

**Step 4 — The subagent runs its own full agentic loop, invisibly**
Exactly like `research_agent()`'s internal loop — call Claude → check `stop_reason` → if `tool_use`, execute (`web_search`, `read_url`) → feed results back → repeat until `end_turn`. This entire loop happens **inside the SDK/CLI**, in its own isolated context — subagents maintain separate context from the main agent, so a research-assistant subagent can explore dozens of pages without cluttering the main conversation, only returning relevant findings. This is the same benefit the manual version got by giving `research_agent()` its own separate `messages` list that never touched the orchestrator's `messages`.

**Step 5 — Subagent finishes, result flows back as a `tool_result`**
Once the subagent's own loop hits `end_turn`, its final output is packaged as the `tool_result` for the original `Task` call (matched via `tool_use_id`, same mechanism as `toolu_01A1B2C3` in the single-agent example). This gets appended back into the **coordinator's** message history — identical to:
```python
tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(result)})
```

**Step 6 — Coordinator loop continues**
The coordinator is called again with the new tool results in its history, same as the manual orchestrator loop. It decides: spawn more `Task` calls, or produce a final answer (`end_turn`).

### 7.1 Where Parallelism Actually Happens

In the hand-rolled code, three `Task`-equivalent calls in one `response.content` would still run **sequentially** unless `asyncio.gather(...)` was explicitly wrapped around the dispatch loop. The Agent SDK's runtime is built to recognize multiple `Task` calls appearing in the **same** coordinator turn as independent, and executes them concurrently by design — a scheduling optimization built into the SDK's runtime, not something magic about the `Task` tool's schema itself. This same behavior could be replicated by hand using `asyncio` around a custom dispatcher.

---

## 8. Side-by-Side: Manual Multi-Agent Code vs. Built-In `Task` Tool

| Step | Manual multi-agent code | Agent SDK `Task` tool |
|---|---|---|
| Entry point | `run_orchestrator(user_task)` | Coordinator agent call with `Task` tool declared in `coordinator_config` |
| Coordinator decides to delegate | Returns `tool_use` with `name="call_research_agent"` | Returns `tool_use` with `name="Task"` + `AgentDefinition` (illustrated by `task_tool_call`'s shape) |
| Who dispatches the call | `ORCHESTRATOR_TOOLS[block.name](**block.input)` line, written by hand | SDK/CLI's internal control loop |
| Subagent's own loop | `research_agent()`'s own `while True` + own `messages` | New isolated agent session spun up by the SDK from the `AgentDefinition` |
| Subagent's tool scoping | `RESEARCH_TOOLS` dict, defined manually | `allowed_tools` field, enforced by SDK permissions layer |
| Context isolation | Achieved by using a separate `messages` list per function | Native SDK feature — subagents keep separate context automatically |
| Result returned to coordinator | Plain string return value → wrapped as `tool_result` | Subagent's final `end_turn` text → wrapped as `tool_result` automatically |
| Parallel execution | Only if `asyncio` is added manually | Native — multiple `Task` calls in one turn run concurrently by design (as shown in `coordinator_response`) |

**Bottom line:** the *conceptual* flow built by hand — orchestrator loop → sees a "tool" that's secretly a full sub-agent → dispatch → sub-agent runs its own isolated loop → result bubbles back as a `tool_result` → orchestrator continues — is exactly what happens inside the Agent SDK's `Task` tool. The SDK just moves the dispatch/execution machinery (`TOOLS[block.name](**block.input)` and nested `while True` loops) into its own managed runtime, and adds native context isolation, permission enforcement, and parallel scheduling on top, rather than requiring it to be hand-built.

---

## 9. Important Notes on `task_tool_call` (Clarification)

This point came up specifically and is worth keeping separate for clarity:

- `task_tool_call` is **just an example/reference of how a single subagent delegation is structured** when Claude decides to create one.
- It is **not used internally by Claude or the SDK** in the sense of being a piece of code that executes or gets called by anything.
- In a real running system, a `tool_use` block shaped exactly like `task_tool_call` would be **generated by Claude's API response** (the model deciding to delegate) — never something the developer's code constructs and sends *to* Claude.
- Its sole purpose in the discussion was pedagogical: to show the **anatomy of one `Task` delegation** (`AgentDefinition` fields: `description`, `prompt`, `allowed_tools`, `model`) in isolation, before introducing `coordinator_response`, which shows three such delegations happening **simultaneously** (parallel dispatch).

---

## 10. Summary Cheat Sheet — Multi-Agent Systems

- **Multi-agent system** = breaking a task across multiple specialized agents (each with its own role/tools/prompt) instead of one generalist agent doing everything.
- **Why:** avoids tool-choice confusion, avoids context bloat, enables specialization, enables parallelism, improves debuggability, enables context isolation.
- **Most common pattern:** Orchestrator–Worker, implemented via "agents as tools."
- **Agents as tools** = a sub-agent is exposed to the orchestrator as a normal-looking tool; internally, that "tool" runs its own full agentic loop.
- **Manual implementation** = you write the dispatcher (`ORCHESTRATOR_TOOLS[block.name](**block.input)`) and each sub-agent's own loop yourself, using the raw Anthropic Messages API.
- **Built-in `Task` tool (Claude Agent SDK)** = the same "agents as tools" pattern, but implemented natively: declared via `{"type": "task", "name": "Task"}`, must be explicitly allowed via `allowedTools`, and subagents are defined via an `AgentDefinition` (`description`, `prompt`, `allowed_tools`, `model`).
- **Parallel execution** = multiple `Task`/tool_use calls appearing in the **same** response `content` array are independent and can run concurrently; calling them in separate sequential turns is an anti-pattern that wastes time.
- **Context isolation** = each sub-agent keeps its own separate conversation history; only the final result is returned to the orchestrator — this is true both in the manual implementation (separate `messages` list per function) and natively in the Agent SDK.
- **`task_tool_call`** = a standalone illustrative example only, showing the shape of one `Task` delegation — not executed code, not something sent to Claude, and not part of the `coordinator_response` example's three calls.
