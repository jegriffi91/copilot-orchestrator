# Copilot Orchestrator

**LLM-Agnostic Agent Generation Infrastructure for Enterprise Applications**

A modular framework for generating specialized AI agents from composable knowledge building blocks. Currently supports GitHub Copilot CLI and Cursor, with an architecture designed to extend to any LLM.

---

## 🎯 Vision

Enterprise codebases need more than generic AI assistance—they need **specialized agents** with deep domain knowledge and consistent behavior. This project provides:

1. **Personas** — Voice, tone, and behavioral constraints for agents
2. **Standards** — Technical knowledge blocks (tagged, filterable)
3. **Workflows** — Verification procedures and CI commands
4. **Stitcher** — A script that compiles these into deployable agents

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    PERSONAS     │     │   STANDARDS     │     │   WORKFLOWS     │
│  (Voice/Tone)   │  +  │ (Tech Rules)    │  +  │ (Verification)  │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌────────────────────────┐
                    │   stitch-brain.py      │
                    │   (Agent Compiler)     │
                    └────────────┬───────────┘
                                 ▼
                    ┌────────────────────────┐
                    │  .github/agents/*.md   │
                    │  (Deployable Agents)   │
                    └────────────────────────┘
```

---

## 📁 Project Structure

```
copilot-orchestrator/
├── docs/
│   ├── personas/           # Agent personalities (voice, rejection criteria)
│   │   ├── README.md
│   │   ├── swift6-migration.md
│   │   ├── qa-kien.md
│   │   └── sdui-dev.md
│   │
│   ├── standards/          # Knowledge building blocks (tagged)
│   │   ├── common/         # Base Swift/iOS rules
│   │   ├── testing/        # Unit test patterns, mocking
│   │   ├── design/         # Design tokens, UI patterns
│   │   └── workflows/      # CI commands, verification steps
│   │
│   ├── scripts/
│   │   └── stitch-brain.py # Agent compiler script
│   │
│   └── adr/                # Architecture Decision Records
│
├── .copilot/               # GitHub Copilot CLI integration
│   ├── agents/             # Sample specialist agents
│   ├── tools/orchestrator/ # MCP server for multi-agent delegation
│   ├── config.json         # Model tiering configuration
│   └── mcp-config.json     # MCP server registration
│
└── .github/agents/         # OUTPUT: Generated agent files
```

---

## 🚀 Quick Start

### 1. Generate Agents

```bash
python3 docs/scripts/stitch-brain.py
```

This compiles all configured agents to `.github/agents/`.

### 2. Configure Recipes

Edit `docs/scripts/stitch-brain.py` to define new agents:

```python
AGENT_RECIPES = {
    "testing.agent.md": {
        "persona": "qa-kien.md",
        "sources": ["testing", "workflows"],
        "allowed_tags": ["testing", "common", "ci"],
        "description": "Unit Testing Specialist"
    }
}
```

### 3. Use with Copilot CLI

Generated agents in `.github/agents/` are automatically available when GitHub Copilot CLI detects the repository.

---

## 🧠 The "Stitched Brain" Architecture

### Core Concepts

| Component | Purpose | Location |
|-----------|---------|----------|
| **Persona** | Defines agent voice, mental model, rejection criteria | `docs/personas/*.md` |
| **Standards** | Tagged technical rules (stitcher_rules in frontmatter) | `docs/standards/**/*.md` |
| **Workflows** | Verification procedures linked via `related_verification` | `docs/standards/workflows/*.md` |
| **Recipe** | Maps persona + standards → output agent | `stitch-brain.py` |

### How Stitching Works

1. **Persona Injection** — Agent identity and communication style
2. **Rule Extraction** — Parses `stitcher_rules` from standards frontmatter
3. **Tag Filtering** — Only includes rules matching recipe's `allowed_tags`
4. **Verification Linking** — Pulls in workflows from `related_verification`
5. **Output Generation** — Writes structured agent file with THE LAW + THE LOOP

### Frontmatter Schema

Standards files use YAML frontmatter:

```yaml
---
tags: [swift6, common]
stitcher_rules:
  - "RULE: No force unwraps | ACTION: Use guard/if-let | SEVERITY: CRITICAL"
  - "STEP: Run tests | CMD: swift test | SEVERITY: WARN"
related_verification: verify_build.md
---
```

---

## 🎭 MCP Orchestrator (Advanced)

For multi-agent workflows with model tiering, the project includes an MCP server:

```
.copilot/tools/orchestrator/
├── src/index.ts       # MCP server implementation
├── package.json
└── README.md          # Setup instructions
```

### Features

- **Model Tiering** — Premium models for planning, cheap models for execution
- **Topic Isolation** — Switch between isolated work contexts
- **Agent Delegation** — Spawn specialist agents in tmux panes
- **Session Persistence** — Separate from native Copilot state

See [`.copilot/tools/orchestrator/README.md`](.copilot/tools/orchestrator/README.md) for setup.

---

## 📝 Creating New Agents

### Step 1: Create Persona

```markdown
<!-- docs/personas/my-persona.md -->
---
id: my_persona
role: Role Title
specialty: [Area1, Area2]
voice: "Adjective, Adjective"
---

# IDENTITY: The Title

Core philosophy description.

## 🧠 Mental Model
1. **Principle 1:** Explanation

## 🚫 Rejection Criteria
- **Anti-pattern 1:** Why it's rejected
```

### Step 2: Add Standards

```markdown
<!-- docs/standards/my-domain/rule.md -->
---
tags: [my-domain, common]
stitcher_rules:
  - "RULE: Rule Name | ACTION: What to do | SEVERITY: CRITICAL"
related_verification: my_workflow.md
---

# Rule Documentation
Detailed explanation...
```

### Step 3: Configure Recipe

```python
# In stitch-brain.py
AGENT_RECIPES["my-agent.agent.md"] = {
    "persona": "my-persona.md",
    "sources": ["my-domain", "common"],
    "allowed_tags": ["my-domain", "common"],
    "description": "My Agent Description"
}
```

### Step 4: Generate

```bash
python3 docs/scripts/stitch-brain.py
```

---

## 🔮 LLM Portability

The architecture is designed to be LLM-agnostic:

| Target | Status | Output Format |
|--------|--------|---------------|
| GitHub Copilot CLI | ✅ Active | `.github/agents/*.md` |
| Cursor | 🔄 Planned | `.cursorrules` |
| Claude/Anthropic | 🔄 Planned | System prompts |
| Custom MCP | 🔄 Planned | Tool-based injection |

The same personas and standards can generate agents for any target by adapting the output template in `stitch-brain.py`.

---

## 📚 Related Documentation

- [Personas README](docs/personas/README.md) — Creating agent personalities
- [Orchestrator README](.copilot/tools/orchestrator/README.md) — MCP server setup
- [ADR-001](docs/adr/001-stitched-brain-architecture.md) — Architecture decision record

---

## License

MIT
