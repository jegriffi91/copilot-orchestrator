# Copilot Orchestrator

An MCP-based orchestration layer for GitHub Copilot CLI that enables **multi-agent delegation**, **model tiering**, and **topic-based isolation**.

## Where This Fits

In the [3-layer architecture](../../../docs/adr/002-skills-runtime-architecture.md), the orchestrator is a **Layer 1 MCP Server (The Hands)**. It provides atomic delegation and topic management tools that the Agent (Soul) invokes to coordinate work across specialist agents.

| Layer | Component | This Server Provides |
|-------|-----------|---------------------|
| Agent (Soul) | Identity + Router | — (consumes this server) |
| Skill (Mind) | Procedures | — |
| **MCP (Hands)** | **Orchestrator** | `create_topic`, `delegate_to`, `switch_topic`, `check_delegations` |

## 🚀 Quick Setup

This system runs as a local [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that GitHub Copilot CLI connects to.

1.  **Install Dependencies**
    ```bash
    cd .copilot/orchestrator
    npm install
    npm run build
    ```

2.  **Verify Configuration**
    Ensure `.copilot/mcp-config.json` exists and points to your orchestrator:
    ```json
    {
      "mcpServers": {
        "orchestrator": {
          "command": "npx",
          "args": ["tsx", "~/.copilot/orchestrator/src/index.ts"]
        }
      }
    }
    ```

3.  **Start Using**
    Open GitHub Copilot CLI and start chatting! The tools (`create_topic`, `delegate_to`, etc.) will be automatically available to the agent.

---

## 🎯 Architecture Goals

### 1. Model Tiering (Cost Optimization)
Instead of doing everything with expensive models, we split the work:
*   **Coordinator (Premium)**: Uses high-reasoning models (e.g., o1-preview) to plan and decompose tasks.
*   **Specialists (Cheap)**: Uses faster/cheaper models (e.g., gpt-4o-mini) to execute specific, context-rich delegations.

### 2. Specialist Agents
Agents are defined in `.copilot/agents/` as markdown files (e.g., `swift6.agent.md`). They act as "personas" with specific constraints, capabilities, and context limitations.

### 3. Topic Isolation
Prevents "Context Rot" by isolating work into **Topics**. Switching topics completely swaps the context available to the CLI, ensuring you only see the plan/tasks relevant to your current focus.

---

## 🧠 Session State & "Plan Mode"

GitHub Copilot CLI has a native "Plan Mode" that stores state in `~/.copilot/session-state/`. **We do not touch this.**

Our orchestrator uses a completely separate directory structure to avoid conflicts and provide persistence:

*   ⛔ **Native Copilot State**: `~/.copilot/session-state/` (Ephemeral, session-bound)
*   ✅ **Orchestrator State**: `~/.copilot/workflows/<topic>/` (Persistent, topic-bound)

This means you can have multiple persistent topics (e.g., "auth-refactor", "bug-fix-123") and switch between them, effectively "hydrating" your current CLI session with the chosen topic's context.

---

## 💡 Common Use Cases

### Starting a New Feature
**User:** "Plan a new feature for adding Apple Pay support."
**Coordinator:**
1.  Calls `create_topic(name="apple-pay")`
2.  Writes high-level plan to `workflows/apple-pay/plan.md`

### Delegating Implementation
**User:** "Great plan. Let's start implementing the API client."
**Coordinator:**
1.  Calls `delegate_to(agent="swift6", task="Implement ApplePayClient backed by new API", model_tier="cheap")`
2.  Creates a delegation file in `workflows/apple-pay/.delegations/`
3.  Spawns a specialist agent (e.g., in a tmux pane) to handle that specific file.

### Reviewing Progress
**User:** "What's the status of the API client?"
**Coordinator:**
1.  Calls `check_delegations()`
2.  Reads the `.result.md` file returned by the specialist agent.
3.  Updates the main `task.md`.

### Context Switching
**User:** "I need to fix a critical bug in Auth before continuing."
**Coordinator:**
1.  Calls `switch_topic(name="auth-hotfix")`
2.  Unloads "apple-pay" context.
3.  Loads "auth-hotfix" `plan.md` and `task.md`.
