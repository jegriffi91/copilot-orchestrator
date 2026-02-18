# Copilot Orchestrator

**Harness-Agnostic Agentic Infrastructure for Enterprise Applications**

A composable framework for building specialized AI agents from modular knowledge layers. Designed to work with any LLM harness — GitHub Copilot CLI, Cursor, Claude, or custom tooling — without vendor lock-in.

---

## 🎯 Vision

Enterprise codebases need more than generic AI assistance — they need **governed, composable agents** with deep domain knowledge, consistent behavior, and verifiable outputs. This project provides the scaffolding to build them.

### The 3-Layer Architecture (Soul / Mind / Hands)

```
┌─────────────────────────────────────────────────────────────┐
│                 LAYER 3: AGENT (The Soul)                   │
│  • Identity (Persona from docs/personas/)                   │
│  • Memory (Session State, Retry Policy, Token Budget)       │
│  • Router (Reads Skill Catalog to select procedures)        │
└──────────────┬───────────────────────────────┬──────────────┘
               │ Loads                         │ Loads
               ▼                               ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│  LAYER 2: SKILL (The Mind)  │ │  LAYER 2: SKILL (The Mind)  │
│  "Code Review SOP"          │ │  "Testing SOP"              │
│  • Procedure (Steps)        │ │  • Procedure (Steps)        │
│  • Verification (Contract)  │ │  • Verification (Contract)  │
└──────────────┬──────────────┘ └──────────────┬──────────────┘
               │ Calls                         │ Calls
               ▼                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 LAYER 1: MCP (The Hands)                    │
│      [Git]    [Postgres]    [FileSystem]    [Linter]        │
│      (Atomic, Stateless, Deterministic)                     │
└─────────────────────────────────────────────────────────────┘
```

**Agents** decide *what* to do. **Skills** define *how* to do it. **MCPs** *execute* it.

---

## 🧩 Core Concepts

### What Goes Where

| Component | Question It Answers | Location | Lifecycle |
|-----------|---------------------|----------|-----------|
| **Persona** | "Who am I?" — voice, tone, rejection criteria | `docs/personas/` | Session-persistent |
| **Standard** | "What are the rules?" — immutable domain constraints | `docs/standards/` | Always loaded |
| **Skill** | "How do I do X?" — step-by-step procedures | `docs/skills/` | Loaded on-demand |
| **Workflow** | "How do I verify?" — tiered verification procedures | `docs/workflows/` | Loaded by skills |
| **MCP Tool** | "What can I touch?" — atomic system capabilities | `.copilot/tools/` | Always available |

### Agent vs Skill vs MCP

| Aspect | Agent | Skill | MCP |
|--------|-------|-------|-----|
| **Purpose** | Identity + routing | Procedural SOP | Atomic tool |
| **State** | Session context, memory | Stateless | Stateless |
| **Granularity** | Domain-level persona | Task-level procedure | Single operation |
| **Reuse** | Loads multiple skills | Shared across agents | Shared across skills |
| **Example** | "Swift 6 Migration Specialist" | "Convert completion handlers to async/await" | `git diff`, `filesystem read` |

**Rule of Thumb:**
- If it's an *identity*, it's an **Agent**
- If it's a *procedure*, it's a **Skill**
- If it's a *tool call*, it's an **MCP**
- If it's a *constraint*, it's a **Standard**
- If it's a *verification step*, it's a **Workflow**

---

## 📁 Project Structure

```
copilot-orchestrator/
├── docs/                           # ← Source of Truth (harness-agnostic)
│   ├── personas/                   #   Agent voice, tone, rejection criteria
│   ├── standards/                  #   Immutable domain rules (THE LAW)
│   │   ├── common/                 #     Base Swift/iOS patterns
│   │   ├── design/                 #     Atlas design system tokens
│   │   └── testing/                #     Unit test patterns, mocking
│   ├── skills/                     #   Procedural knowledge (THE MIND)
│   │   ├── skill-authoring/        #     Meta-skill: how to create skills
│   │   ├── swiftui/               #     SwiftUI best practices + references
│   │   ├── knowledge-architecture/ #     3-tier knowledge distribution
│   │   └── README.md
│   ├── workflows/                  #   Verification procedures (THE LOOP)
│   ├── scripts/                    #   Build tooling
│   │   ├── publish.py              #     Unified pipeline (agents + skills)
│   │   └── tsan-sanitizer.py       #     Output sanitizer for TSan logs
│   ├── adr/                        #   Architecture Decision Records
│   └── resources/                  #   Research & reference materials
│
├── .copilot/                       # ← Vendor: GitHub Copilot CLI
│   ├── agents/                     #   Compiled specialist agents
│   ├── skills/                     #   Published skills + references
│   ├── config.json                 #   Model tiering configuration
│   └── mcp-config.json             #   MCP server registration
```

---

## � How It Works

### Runtime Lifecycle

```
User Request
     │
     ▼
┌─────────────────────┐
│ 1. Parse Intent     │  "I need to review this code"
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ 2. Match Skill      │  Skill Catalog → code-review
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ 3. Load Skill       │  Inject docs/skills/code-review/SKILL.md
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ 4. Execute via MCP  │  Agent follows procedure, calls tools
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ 5. Verify           │  Run verification from docs/workflows/
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ 6. Cleanup          │  Unload skill, summarize results
└─────────────────────┘
```

### Agent & Skill Compilation

For harnesses that need pre-compiled agents (e.g., GitHub Copilot CLI), `publish.py` compiles Persona + Standards into deployable agent files and publishes skills:

```bash
python3 docs/scripts/publish.py agents   # Compile agents
python3 docs/scripts/publish.py skills   # Publish skills + references
python3 docs/scripts/publish.py all      # Both
```

Compiled agents contain:
- **IDENTITY** — Persona voice and mental model
- **THE LAW** — Immutable rules from `docs/standards/` (RULE types)
- **THE LOOP** — Verification steps from `docs/workflows/` (STEP/CMD types)

See [ADR-001](docs/adr/001-stitched-brain-architecture.md) for the full compilation architecture.

---

## � Quick Start

### 1. Generate Agents & Publish Skills

```bash
python3 docs/scripts/publish.py all
```

### 2. Configure a New Agent Recipe

```python
# In docs/scripts/publish.py
AGENT_RECIPES["my-agent.agent.md"] = {
    "persona": "my-persona.md",
    "sources": ["common", "testing"],
    "allowed_tags": ["testing", "common"],
    "skills": ["swiftui"],  # Skills this agent can load
    "description": "My Specialist Agent"
}
```

### 3. Create a New Skill

```bash
# Ask your AI assistant:
"Using the skill-authoring skill, help me create a new skill for <purpose>"
```

Or follow the [Skill Authoring Guide](docs/skills/skill-authoring/SKILL.md).

### 4. Use with Any Harness

Generated agents in `.copilot/agents/` are automatically available to GitHub Copilot CLI. Published skills in `.copilot/skills/` provide on-demand domain knowledge. Source skills in `docs/skills/` can be loaded by any harness that reads markdown.

---

## 🔮 LLM Portability

The architecture is harness-agnostic by design:

| Target | Status | Integration |
|--------|--------|-------------|
| GitHub Copilot CLI | ✅ Active | `.copilot/agents/` |
| Cursor | 🔄 Planned | `.cursor/rules/` via `publish.py skills` |
| Claude / Anthropic | 🔄 Planned | System prompts |
| Custom Tooling | 🔄 Planned | Direct `docs/` consumption |
| **Multi-Agent Orchestration** | ✅ Active | **[Orchard](https://github.com/jegriffi91/orchard)** — agent-agnostic runtime |

The same personas, standards, and skills generate agents for any target. Only the compilation/publishing step changes.

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [Personas README](docs/personas/README.md) | Creating agent identities |
| [Standards README](docs/standards/README.md) | Writing domain rules |
| [Skills README](docs/skills/README.md) | Building procedural knowledge |
| [Workflows README](docs/workflows/README.md) | Verification procedures |
| [Orchestration](https://github.com/jegriffi91/orchard) | Multi-agent orchestration (replaced MCP server) |
| [ADR-001](docs/adr/001-stitched-brain-architecture.md) | Stitched Brain architecture |
| [ADR-002](docs/adr/002-skills-runtime-architecture.md) | Skills Runtime architecture |

---

## License

MIT
