# AI Agents: How Everything Comes Together
### From Token Prediction to Autonomous Action in the World

> This document is a companion to *How Large Language Models Really Work*. It assumes familiarity with chain of thought, the KV cache, the orchestration layer, and tool use. If any of those concepts are unfamiliar, read that document first.

---

## Table of Contents

1. [What an Agent Actually Is](#1-what-an-agent-actually-is)
2. [How Agents Fit Into Everything We Already Know](#2-how-agents-fit-into-everything-we-already-know)
3. [The Agent Loop in Detail](#3-the-agent-loop-in-detail)
4. [Memory: How Agents Remember Across Steps](#4-memory-how-agents-remember-across-steps)
5. [Types of Agents](#5-types-of-agents)
6. [Multi-Agent Systems](#6-multi-agent-systems)
7. [How a Frontier Agent Actually Works End to End](#7-how-a-frontier-agent-actually-works-end-to-end)
8. [The New Hard Problems Agents Introduce](#8-the-new-hard-problems-agents-introduce)
9. [Where Agents Are Right Now](#9-where-agents-are-right-now)
10. [Key Takeaways](#10-key-takeaways)

---

## 1. What an Agent Actually Is

### The Simplest Possible Definition

A model answering a question is **not** an agent.

An agent is when you give a model a **goal** — not a question — and let it figure out the steps, execute them, observe what happened, and keep going until that goal is achieved, without a human approving each step.

The distinction is fundamental:

```
┌─────────────────────────────────────────────────────────────┐
│  MODEL (reactive)                                           │
│                                                             │
│  User input ──► [one forward pass] ──► Output              │
│                                                             │
│  Stops here. Waits for the next human message.             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  AGENT (proactive)                                          │
│                                                             │
│  Goal ──► Plan ──► Act ──► Observe ──► Replan ──► Act      │
│            ▲                                    │           │
│            └────────────────────────────────────┘           │
│                                                             │
│  Keeps running autonomously until goal is achieved.        │
└─────────────────────────────────────────────────────────────┘
```

The key word is **autonomously**. An agent decides its next action itself, based on what it observed from its last action. No human in the loop between steps.

### What Changes When You Go From Model to Agent

| Dimension | Model | Agent |
|---|---|---|
| Input | A question or instruction | A goal or objective |
| Output | A single response | A series of actions + a final result |
| Duration | One turn | Many turns, potentially hours |
| Decision making | None — just responds | Continuous — plans and replans |
| Tool use | Optional, one call | Core, many calls across many steps |
| Memory | Context window only | Context + external memory |
| Error handling | None — just outputs | Can detect failure and try again |
| Human involvement | Every turn | Only at start (and optionally at checkpoints) |

---

## 2. How Agents Fit Into Everything We Already Know

Every concept from the previous document is a **building block** of an agent. Nothing is discarded — it all stacks together.

```
┌─────────────────────────────────────────────────────────────────┐
│                        AGENT                                    │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  ORCHESTRATION LAYER (the agent loop)                     │  │
│  │  Python code that runs the plan/act/observe cycle        │  │
│  └───────────────────────────┬───────────────────────────────┘  │
│                              │ calls                            │
│  ┌───────────────────────────▼───────────────────────────────┐  │
│  │  FRONTIER MODEL                                           │  │
│  │  Uses chain of thought to reason about what to do next   │  │
│  │  Emergent capabilities: planning, self-correction,        │  │
│  │  theory of mind, calibrated uncertainty                   │  │
│  └───────────────────────────┬───────────────────────────────┘  │
│                              │ stores reasoning in              │
│  ┌───────────────────────────▼───────────────────────────────┐  │
│  │  KV CACHE / CONTEXT WINDOW                                │  │
│  │  Working memory: holds goal, plan, history of actions,    │  │
│  │  tool results, observations, and reasoning steps          │  │
│  └───────────────────────────┬───────────────────────────────┘  │
│                              │ reaches out to                   │
│  ┌───────────────────────────▼───────────────────────────────┐  │
│  │  TOOLS                                                    │  │
│  │  Web search, code runner, file system, APIs, browser,     │  │
│  │  databases, email, calendar, computer use                 │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

Here is exactly how each concept from before maps into the agent:

| Concept | Role in an Agent |
|---|---|
| **Chain of thought** | How the agent reasons about what step to take next. Each reasoning trace is a CoT pass. |
| **KV cache** | Where the agent's entire history lives — every action taken, every result observed |
| **Context window** | The agent's working memory. The longer it runs, the fuller this gets. |
| **Emergent capabilities** | Planning, self-correction, theory of mind — these are what make the agent smart enough to operate autonomously |
| **Orchestration loop** | The while loop that keeps running until the goal is achieved or the agent gives up |
| **Tools** | What the agent uses to actually change things in the world — not just produce text |
| **Model weights** | Where the agent's knowledge, reasoning patterns, and judgment live |

An agent is not a new concept on top of everything else. It is the **integration** of everything else into a system that can pursue a goal over time.

---

## 3. The Agent Loop in Detail

The core of every agent — regardless of framework, regardless of model — is a loop. Here is what that loop looks like in full detail.

### The Full Agent Loop

```
                        ┌─────────────────┐
                        │   RECEIVE GOAL  │
                        │                 │
                        │ "Research the   │
                        │  top 5 AI       │
                        │  companies and  │
                        │  write a report"│
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │      PLAN       │◄──────────────────┐
                        │                 │                   │
                        │ Model reasons   │                   │
                        │ about what      │                   │
                        │ steps are       │                   │
                        │ needed (CoT)    │                   │
                        └────────┬────────┘                   │
                                 │                            │
                                 ▼                            │
                        ┌─────────────────┐                   │
                        │      ACT        │                   │
                        │                 │                   │
                        │ Call a tool:    │                   │
                        │ web_search,     │                   │
                        │ run_code,       │                   │
                        │ read_file, etc. │                   │
                        └────────┬────────┘                   │
                                 │                            │
                                 ▼                            │
                        ┌─────────────────┐                   │
                        │     OBSERVE     │                   │
                        │                 │                   │
                        │ Tool result     │                   │
                        │ injected into   │                   │
                        │ context window  │                   │
                        └────────┬────────┘                   │
                                 │                            │
                                 ▼                            │
                        ┌─────────────────┐     replan       │
                        │     REFLECT     ├──────────────────►│
                        │                 │                   │
                        │ Did that work?  │                   │
                        │ Am I closer to  │                   │
                        │ the goal?       │                   │
                        │ What next?      │                   │
                        └────────┬────────┘                   │
                                 │                            │
                          goal   │  not done                  │
                         achieved│──────────────────────────►─┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  FINAL OUTPUT   │
                        │                 │
                        │ Deliver result  │
                        │ to user         │
                        └─────────────────┘
```

### What Happens at Each Stage

**1. Plan**
The model uses chain of thought to reason about what the goal requires. It thinks about what information it needs, what order to do things in, and what tools are available. This is a CoT pass — the reasoning lives in the context window.

**2. Act**
The model emits a tool call. The orchestration layer executes it. This could be a web search, a Python script, writing a file, calling an API, clicking a button in a browser — anything in the tool registry.

**3. Observe**
The tool result comes back. The orchestration layer injects it into the context window as a new block of tokens. The model now sees: original goal + plan + action taken + result observed.

**4. Reflect**
The model reasons over what it observed. Did the search return useful results? Did the code run without errors? Is the goal closer? This reflection — also a CoT pass — determines whether to proceed, replan, or try a different approach.

**5. Replan / Act Again**
If the goal is not yet achieved, the loop continues. The model may stick to the original plan or revise it based on what it observed. This cycle can repeat dozens or hundreds of times.

**6. Final Output**
When the model determines the goal is achieved — or decides it cannot proceed further — it produces a final response and the loop ends.

### What This Looks Like in Code

```python
import anthropic

client = anthropic.Anthropic()

def run_agent(goal: str):
    messages = [{"role": "user", "content": goal}]
    
    system_prompt = """You are an autonomous agent. You have access to tools.
    Think step by step about what you need to do to achieve the goal.
    Use tools as needed. When the goal is fully achieved, say DONE and
    provide the final result."""

    tools = [
        web_search_tool_schema,
        run_python_tool_schema,
        read_file_tool_schema,
        write_file_tool_schema,
    ]

    step = 0
    max_steps = 50  # prevent infinite loops

    # THE AGENT LOOP
    while step < max_steps:
        step += 1
        print(f"\n--- Agent Step {step} ---")

        response = client.messages.create(
            model="claude-sonnet-4-6",
            system=system_prompt,
            tools=tools,
            messages=messages,
            max_tokens=4096
        )

        # Agent wants to use a tool
        if response.stop_reason == "tool_use":
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    print(f"Calling tool: {block.name}")
                    result = execute_tool(block.name, block.input)
                    print(f"Result: {result[:200]}...")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)
                    })

            # Append agent's reasoning + tool results to history
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            # Loop again

        # Agent produced a final answer — no more tool calls
        elif response.stop_reason == "end_turn":
            final_text = next(
                b.text for b in response.content if b.type == "text"
            )
            print(f"\nAgent finished after {step} steps.")
            return final_text

    return "Agent reached maximum steps without completing the goal."
```

The entire agent is this loop. The intelligence is in the model. The persistence is in the `messages` list growing with every step.

---

## 4. Memory: How Agents Remember Across Steps

Memory is one of the most important and least understood parts of an agent. There are actually **four distinct types of memory** an agent can use, each serving a different purpose.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AGENT MEMORY ARCHITECTURE                        │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │   IN-CONTEXT     │  │    EXTERNAL      │  │    IN-WEIGHTS    │  │
│  │    MEMORY        │  │    MEMORY        │  │     MEMORY       │  │
│  │                  │  │                  │  │                  │  │
│  │ The context      │  │ Vector database  │  │ Knowledge baked  │  │
│  │ window itself    │  │ or file system   │  │ into the model   │  │
│  │                  │  │ outside the      │  │ during training  │  │
│  │ Everything the   │  │ model            │  │                  │  │
│  │ agent has done   │  │                  │  │ Permanent.       │  │
│  │ this session     │  │ Survives across  │  │ Cannot be        │  │
│  │                  │  │ sessions         │  │ changed at       │  │
│  │ Lost when        │  │                  │  │ runtime          │  │
│  │ session ends     │  │ Searched via     │  │                  │  │
│  │                  │  │ semantic query   │  │                  │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    EPISODIC MEMORY                           │   │
│  │  Summaries of past agent runs stored and retrieved           │   │
│  │  "Last time I tried this approach it failed because..."      │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### The Four Memory Types Explained

**1. In-Context Memory (Working Memory)**
This is the context window — the KV cache in GPU VRAM. Everything the agent has done in the current session: the goal, the plan, every tool call, every result, every reflection. It is fast and immediately available but limited in size and disappears when the session ends.

**2. External Memory (Long-Term Storage)**
A vector database (like Pinecone, Weaviate, or ChromaDB) or a file system the agent can read and write to. The agent stores important findings here and retrieves them semantically — "find everything I know about company X." This survives across sessions and can hold far more than the context window.

**3. In-Weights Memory (Baked-In Knowledge)**
Everything the model learned during training. This is not really "memory" in the traditional sense — it cannot be updated at runtime. But it is the deepest and most integrated form: the model just *knows* things without needing to look them up.

**4. Episodic Memory (Run History)**
Summaries of past agent runs stored externally. When starting a new task, the agent can retrieve: "the last 3 times I tried to scrape this website, it blocked me — use a different approach." This is what enables agents to genuinely learn from experience across sessions.

### How Memory Flows During an Agent Run

```
Session Start
     │
     ▼
┌─────────────────────────────────┐
│  Load relevant memories from    │
│  external DB into context       │
│  (RAG over past experiences)    │
└────────────┬────────────────────┘
             │
             ▼
        Agent Loop
        (Plan → Act → Observe → Reflect)
             │
             │ important finding
             ▼
┌─────────────────────────────────┐
│  Write to external memory       │
│  "Found that API X requires     │
│   OAuth2, not API keys"         │
└────────────┬────────────────────┘
             │
             ▼
        Continue Loop
             │
             ▼
        Goal Achieved
             │
             ▼
┌─────────────────────────────────┐
│  Write episode summary to       │
│  external memory for future     │
│  agent runs to learn from       │
└─────────────────────────────────┘
```

---

## 5. Types of Agents

Not all agents are the same. The architecture varies significantly depending on the task and how much autonomy is needed.

### Single Agent — One Model, Many Tools

The simplest architecture. One model runs the loop, has access to a set of tools, and works toward the goal alone.

```
                    ┌─────────────────┐
                    │     AGENT       │
                    │   (1 model)     │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
    ┌──────────┐      ┌──────────┐      ┌──────────┐
    │  Search  │      │   Code   │      │  Files   │
    │   Tool   │      │ Executor │      │  System  │
    └──────────┘      └──────────┘      └──────────┘
```

**Best for:** Well-defined tasks with a clear endpoint. Coding assistance, research summaries, data processing.

**Examples:** Claude Code, early versions of AutoGPT.

---

### Reflexion Agent — Self-Critique Before Acting

A single agent that explicitly critiques its own plan or output before proceeding. After each action, it asks itself: "Was that a good decision? What would I do differently?" This critique goes back into context before the next action.

```
                    ┌─────────────────┐
                    │   PLAN / ACT    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    OBSERVE      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  SELF-CRITIQUE  │◄── "Was this the right
                    │                 │     approach? What went
                    │                 │     wrong? What's better?"
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   REVISED PLAN  │
                    └────────┬────────┘
                             │
                             ▼
                          Act again
```

**Best for:** Tasks where errors are expensive. Writing, complex reasoning, multi-step planning.

---

### Hierarchical Agent — Manager + Specialists

A manager agent receives the goal, breaks it into subtasks, and delegates each to a specialized sub-agent. Results flow back up to the manager, which synthesizes the final output.

```
                    ┌─────────────────┐
                    │  MANAGER AGENT  │
                    │                 │
                    │ Receives goal,  │
                    │ decomposes it,  │
                    │ delegates tasks │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
   │  RESEARCH   │   │   CODING    │   │   WRITING   │
   │    AGENT    │   │    AGENT    │   │    AGENT    │
   │             │   │             │   │             │
   │ Searches    │   │ Writes and  │   │ Takes facts │
   │ and         │   │ runs code   │   │ and writes  │
   │ summarizes  │   │             │   │ the report  │
   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │ results
                             ▼
                    ┌─────────────────┐
                    │  MANAGER AGENT  │
                    │  synthesizes    │
                    │  final output   │
                    └─────────────────┘
```

**Best for:** Complex goals that have naturally separable subtasks. Large research projects, software development pipelines, content production at scale.

**Examples:** CrewAI, AutoGen multi-agent setups.

---

### Plan-and-Execute Agent — Commit to a Plan First

Instead of replanning at every step, this agent first generates a full plan, then executes each step in order. It only replans if a step fails catastrophically.

```
┌──────────────────────────────────────────────────────┐
│  PLANNING PHASE                                      │
│                                                      │
│  Goal → "Write a market analysis report on EV sector"│
│                                                      │
│  Step 1: Search for top 5 EV companies by market cap │
│  Step 2: Search for recent earnings for each         │
│  Step 3: Search for analyst sentiment                │
│  Step 4: Run code to generate comparison charts      │
│  Step 5: Write synthesis and conclusion              │
└──────────────────────────┬───────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│  EXECUTION PHASE                                     │
│                                                      │
│  Execute Step 1 ──► success ──► Execute Step 2       │
│  Execute Step 2 ──► success ──► Execute Step 3       │
│  Execute Step 3 ──► FAIL    ──► Replan Step 3 only   │
│  Execute Step 3 (revised) ──► success ──► Step 4     │
│  ...                                                 │
└──────────────────────────────────────────────────────┘
```

**Best for:** Tasks where the path is fairly predictable. Reduces unnecessary replanning overhead.

---

## 6. Multi-Agent Systems

Multi-agent systems are where individual agents coordinate to accomplish tasks too large or too complex for a single agent. This is the frontier of what is being built today.

### Why Multiple Agents?

| Problem | Solution |
|---|---|
| Context window fills up on long tasks | Split across agents, each with its own fresh context |
| One model is not specialized enough | Use specialist models for each domain |
| Tasks can be parallelized | Run multiple agents simultaneously |
| One agent's errors compound | Independent verification by a second agent |
| Manager cognitive load too high | Delegate to specialists |

### A Full Multi-Agent Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     USER / HUMAN                                 │
└─────────────────────────────┬────────────────────────────────────┘
                              │  goal
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT                            │
│                                                                  │
│  • Receives the high-level goal                                  │
│  • Decomposes into subtasks                                      │
│  • Assigns subtasks to specialist agents                         │
│  • Monitors progress                                             │
│  • Synthesizes final output                                      │
│  • Reports back to user                                          │
└──────┬──────────────┬────────────────┬────────────────┬──────────┘
       │              │                │                │
       ▼              ▼                ▼                ▼
┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────────┐
│ RESEARCH  │  │  CODING   │  │ ANALYSIS  │  │    CRITIC /       │
│  AGENT    │  │  AGENT    │  │  AGENT    │  │  VERIFICATION     │
│           │  │           │  │           │  │    AGENT          │
│ Searches  │  │ Writes,   │  │ Interprets│  │                   │
│ web and   │  │ runs, and │  │ data and  │  │ Reviews outputs   │
│ databases │  │ debugs    │  │ draws     │  │ from other agents │
│           │  │ code      │  │ insights  │  │ for errors or     │
│           │  │           │  │           │  │ hallucinations    │
└─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └────────┬──────────┘
      │              │               │                  │
      │   results    │               │                  │
      └──────────────┴───────────────┴──────────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │   ORCHESTRATOR    │
                    │   synthesizes     │
                    │   all results     │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │    FINAL OUTPUT   │
                    │    TO USER        │
                    └───────────────────┘
```

### How Agents Communicate With Each Other

Agents communicate by passing messages — either through a shared message queue, direct API calls between agents, or a shared memory store.

```
Agent A produces output
       │
       │  "I found the following 5 companies: ..."
       ▼
Shared message queue / orchestrator
       │
       │  Routes to Agent B
       ▼
Agent B receives output as part of its own context
       │
       │  "Based on those 5 companies, here is the financial analysis..."
       ▼
Orchestrator collects and routes further
```

Each agent is just a model with its own context window. Communication is just text — the output of one agent becomes part of the input context of another.

---

## 7. How a Frontier Agent Actually Works End to End

Let's walk through a complete real-world example: a frontier agent given the goal of **"Research the competitive landscape of the EV market and write a 5-page report with charts."**

This is what actually happens under the hood, step by step.

```
USER: "Research the competitive landscape of the EV market
       and write a 5-page report with charts."
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 1: AGENT INITIALIZES                              │
│                                                         │
│  • Goal loaded into context window                      │
│  • Relevant past memories retrieved from vector DB      │
│    "Previous EV research from 3 months ago..."          │
│  • Tool registry loaded: search, code, file write       │
│  • System prompt sets agent behavior and constraints    │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 2: CHAIN OF THOUGHT PLANNING (CoT pass)           │
│                                                         │
│  Model reasons internally:                              │
│  "To write this report I need:                          │
│   - Current market share data for top EV makers         │
│   - Recent earnings and revenue figures                 │
│   - Analyst forecasts and sentiment                     │
│   - Technology differentiation between companies        │
│   - I should search for each of these in order"         │
│                                                         │
│  This reasoning lives in the KV cache                   │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 3: FIRST TOOL CALL                                │
│                                                         │
│  Model emits: tool_use { name: "web_search",            │
│               query: "EV market share 2026 top makers" }│
│                                                         │
│  Orchestration layer executes the search                │
│  Result injected back into context window               │
│  "Tesla 19%, BYD 22%, Volkswagen 8%..."                 │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 4: REFLECT AND CONTINUE                           │
│                                                         │
│  CoT: "Good, I have market share. Now I need earnings.  │
│        I'll search for each company separately."        │
│                                                         │
│  → web_search: "Tesla Q1 2026 earnings revenue"         │
│  → web_search: "BYD Q1 2026 earnings revenue"           │
│  → web_search: "Volkswagen EV Q1 2026 results"          │
│  (Each result appended to context window)               │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 5: CODE EXECUTION FOR CHARTS                      │
│                                                         │
│  Model emits: tool_use { name: "run_python",            │
│    code: """                                            │
│      import matplotlib.pyplot as plt                    │
│      companies = ['Tesla','BYD','VW','Rivian','NIO']    │
│      market_share = [19, 22, 8, 4, 6]                   │
│      plt.bar(companies, market_share)                   │
│      plt.savefig('ev_market_share.png')                 │
│    """ }                                                │
│                                                         │
│  Code executes in sandbox                               │
│  Chart file saved to disk                               │
│  Result: "Chart saved successfully" → context window    │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 6: WRITING THE REPORT                             │
│                                                         │
│  Model now has in context:                              │
│  • Original goal                                        │
│  • All search results (market share, earnings, etc.)    │
│  • Confirmation that charts were generated              │
│  • Its own reasoning traces from each step              │
│                                                         │
│  CoT: "I have all the data I need. I'll now write       │
│        the full 5-page report integrating everything."  │
│                                                         │
│  Model emits: tool_use { name: "write_file",            │
│    content: [full report text with chart references] }  │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 7: SELF-VERIFICATION                              │
│                                                         │
│  CoT: "Let me check: did I cover all 5 companies?       │
│        Are the numbers consistent across sections?      │
│        Does the conclusion match the data?"             │
│                                                         │
│  Agent re-reads the file it just wrote                  │
│  Finds one inconsistency, corrects it                   │
│  Writes corrected version                               │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 8: STORE TO MEMORY AND FINISH                     │
│                                                         │
│  Writes episode summary to vector DB:                   │
│  "EV market research June 2026:                         │
│   BYD now leads in market share at 22%.                 │
│   Tesla strong on margins. VW struggling."              │
│                                                         │
│  Returns final result to user:                          │
│  "Report complete. 5 pages, 3 charts attached."         │
└─────────────────────────────────────────────────────────┘
```

### What the Context Window Looks Like at the End

By step 8, the context window contains the entire history of the run:

```
[system prompt]
[user goal]
[retrieved memories from past sessions]
[CoT: planning trace]
[tool_call: web_search #1] [tool_result: market share data]
[CoT: reflection]
[tool_call: web_search #2] [tool_result: Tesla earnings]
[tool_call: web_search #3] [tool_result: BYD earnings]
[tool_call: web_search #4] [tool_result: VW results]
[CoT: reflection]
[tool_call: run_python — chart generation] [tool_result: success]
[CoT: now writing report]
[tool_call: write_file — full report] [tool_result: saved]
[CoT: self-verification]
[tool_call: read_file — verify report] [tool_result: report content]
[CoT: found inconsistency, fixing]
[tool_call: write_file — corrected report] [tool_result: saved]
[final response to user]
```

This is why context window size matters so much for agents. Every action, every result, every reasoning trace — all of it accumulates here. A long agent run on a complex task can consume hundreds of thousands of tokens.

---

## 8. The New Hard Problems Agents Introduce

Agents are powerful but they introduce failure modes that simple model calls do not have.

### Problem 1: Compounding Errors

In a single model call, a mistake is contained. In an agent, a wrong decision in step 3 can corrupt steps 4 through 20 before anyone notices.

```
Step 1: Search for market data        ✓ correct
Step 2: Parse and store findings      ✓ correct
Step 3: Misidentify a company name    ✗ WRONG
Step 4: Search for wrong company      ✗ wrong (built on step 3)
Step 5: Analyze wrong company data    ✗ wrong (built on step 4)
Step 6: Write report with wrong data  ✗ wrong (built on steps 3-5)
```

Mitigation: checkpoints, self-verification steps, critic agents.

### Problem 2: Context Window Exhaustion

```
┌────────────────────────────────────────────────────────┐
│  Context window (128K tokens)                          │
│                                                        │
│  ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░  Step 10    │
│  ██████████████████░░░░░░░░░░░░░░░░░░░░░░  Step 20    │
│  ██████████████████████████░░░░░░░░░░░░░░  Step 30    │
│  ████████████████████████████████████████  Step 40    │
│                                         ↑             │
│                              Context full — agent      │
│                              must summarize or stop    │
└────────────────────────────────────────────────────────┘
```

Mitigation: summarize and compress older parts of context, use external memory to offload findings.

### Problem 3: Infinite Loops

An agent that cannot complete a step may keep retrying indefinitely — burning compute and cost with no progress.

```
Step 15: Try approach A  → fails
Step 16: Try approach A  → fails
Step 17: Try approach A  → fails
Step 18: Try approach A  → fails (stuck)
```

Mitigation: max step limits, failure detection, explicit "give up and explain" instructions.

### Problem 4: Trust and Safety

An agent with real tool access can cause real damage. A poorly specified goal can lead to unintended consequences.

| Tool | Potential risk if misused |
|---|---|
| File system write | Overwrite important files |
| Browser control | Submit forms, make purchases |
| Email | Send messages on your behalf |
| API calls | Rack up charges on external services |
| Code execution | Run destructive commands |

Mitigation: sandboxing, human-in-the-loop checkpoints on high-stakes actions, restricted tool permissions.

### Problem 5: Cost at Scale

A simple model call costs fractions of a cent. A 50-step agent run with large context windows can cost dollars per run. Multiplied across thousands of users or tasks, this becomes significant.

```
Single question:     1 API call  × $0.001  = $0.001
Simple agent run:   20 API calls × $0.05   = $1.00
Complex agent run: 100 API calls × $0.10   = $10.00
```

Mitigation: step budgets, early termination when goal confidence is high, cheaper models for simpler subtasks.

---

## 9. Where Agents Are Right Now

### What Agents Do Well Today

| Domain | Example | Maturity |
|---|---|---|
| **Coding** | Write, run, debug, fix code autonomously | High |
| **Research** | Search, synthesize, summarize documents | High |
| **Data processing** | ETL pipelines, analysis, chart generation | High |
| **Customer support** | Answer questions, look up records, escalate | Medium-High |
| **Content creation** | Research + write articles, reports | Medium |
| **Scheduling** | Book meetings, manage calendar | Medium |
| **Browser automation** | Fill forms, extract web data | Medium |
| **Long-horizon planning** | Multi-week projects without human input | Low |
| **Open-ended creative work** | Novel artistic or strategic decisions | Low |

### The Capability Frontier Right Now

The best agent systems in production today (Claude Code, Devin, Gemini Deep Research, OpenAI's Operator) share three characteristics:

1. **Strong underlying model** — at least 70B equivalent reasoning quality
2. **Rich tool access** — web, code execution, file system, APIs
3. **Careful orchestration** — checkpointing, error recovery, memory management

The bottleneck is no longer tools or orchestration — we know how to build those. The bottleneck is the model's ability to maintain **coherent goal-directedness** over many steps without drifting, hallucinating, or getting confused by ambiguous situations.

### The Six-Month Outlook

Every six months the agent capability bar rises significantly. The trajectory:

```
2023  Single tool calls, unreliable multi-step
2024  Reliable 10-20 step tasks, early coding agents
2025  50+ step tasks, multi-agent pipelines in production
2026  Complex long-horizon tasks, frontier agents deployed at scale
2027+ Agents handling entire workflows with minimal human oversight
```

---

## 10. Key Takeaways

| Concept | Core Insight |
|---|---|
| **What an agent is** | A model pursuing a goal autonomously over many steps, not just answering a question |
| **How it fits together** | Agent = orchestration loop + frontier model (CoT) + context window (KV cache) + tools |
| **The agent loop** | Plan → Act → Observe → Reflect → Replan — repeats until goal achieved |
| **Memory types** | In-context (working), external (long-term), in-weights (baked-in), episodic (past runs) |
| **Agent types** | Single, reflexion, hierarchical, plan-and-execute — each suited to different task structures |
| **Multi-agent systems** | Multiple models with specialized roles, coordinated by an orchestrator |
| **The hard problems** | Compounding errors, context exhaustion, infinite loops, safety, cost |
| **Where we are** | Agents work well for well-defined tasks; long-horizon open-ended tasks are still the frontier |

### The Big Picture

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   TOKEN PREDICTION  ──► CHAIN OF THOUGHT  ──► TOOL USE         │
│                                                                 │
│         │                                        │             │
│         ▼                                        ▼             │
│   KV CACHE /                            ORCHESTRATION          │
│   CONTEXT WINDOW                           LAYER               │
│                                                                 │
│         │                                        │             │
│         └────────────────┬───────────────────────┘             │
│                          │                                     │
│                          ▼                                     │
│                       AGENT                                    │
│                                                                 │
│         A system that pursues goals autonomously               │
│         by combining all of the above into a                   │
│         persistent, self-directing loop                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

The agent is not a new technology. It is the **emergent capability** that arises when you combine a sufficiently capable model with the right orchestration, memory, and tools — and give it a goal instead of a question.

---

*This document is a companion to "How Large Language Models Really Work." Together they form a complete picture of how frontier AI systems are actually built and how they operate. June 2026.*
