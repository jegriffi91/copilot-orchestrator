# Skills Directory

This directory contains reusable **procedural knowledge** for AI agents.

## Philosophy

Skills answer: **"How do I do X?"**

> In the [3-layer architecture](../adr/002-skills-runtime-architecture.md), Skills are **The Mind** — stateless, task-level procedures that any agent can load on-demand. They sit between the Agent (identity/routing) and MCP tools (atomic execution).

### Where Skills Fit

| Layer | Question | Location | Example |
|-------|----------|----------|---------|
| **Agent (Soul)** | "Who am I?" | `docs/personas/` | Swift 6 Migration Specialist |
| **Standards (Law)** | "What rules apply?" | `docs/standards/` | "No force unwraps" |
| **Skills (Mind)** | "How do I do X?" | `docs/skills/` | Code review procedure |
| **Workflows (Loop)** | "How do I verify?" | `docs/workflows/` | Tiered compile/test checks |
| **MCP (Hands)** | "What can I touch?" | `.copilot/tools/` | `git diff`, `filesystem read` |

### Skills vs MCPs vs Agents

| Aspect | Agent | Skill | MCP |
|--------|-------|-------|-----|
| **Purpose** | Identity + routing | Procedural SOP | Atomic tool call |
| **State** | Session context | Stateless | Stateless |
| **Loaded** | Session start | On-demand | Always available |
| **Contains** | Persona + skill refs | Steps + verification | Tool schema |
| **Example** | "Testing Specialist" | "Write unit tests" | `filesystem.read()` |

**Rule of Thumb:** If it's an identity, it's an Agent. If it's a procedure, it's a Skill. If it's a tool call, it's an MCP.

### Verification Ownership

Skills define verification *requirements* (what to check). Agents execute the verification *loop* (retries, escalation). Verification *procedures* live in `docs/workflows/`.

## Structure

```
docs/skills/
├── skill-authoring/          # Meta-skill: how to create skills/agents
│   └── SKILL.md
├── swiftui/                  # SwiftUI best practices + modern APIs
│   ├── SKILL.md
│   └── references/           # 14 Tier 3 reference files
│       ├── state-management.md
│       ├── modern-apis.md
│       └── ...
├── knowledge-architecture/   # 3-tier knowledge distribution
│   ├── SKILL.md
│   └── references/
│       ├── tier-placement-rubric.md
│       ├── token-budget-guide.md
│       └── publish-pipeline.md
└── README.md                 # This file
```

Each skill is a folder containing:
- `SKILL.md` — Required: Main skill definition (Tier 2 — Playbook)
- `references/` — Optional: Dense knowledge files loaded on-demand (Tier 3 — Encyclopedia)
- `templates/` — Optional: Supporting templates

### The References Convention

Reference files in `references/` are **lazy-loaded** — only read when the SKILL.md explicitly demands it via imperative triggers:

```markdown
**ACTION REQUIRED:** Read `references/state-management.md` BEFORE evaluating property wrappers.
```

This keeps token budgets low (~2,500 tokens for SKILL.md + ~1,500 per reference file loaded).

## Creating a Skill

Use the `skill-authoring` skill:

```bash
# Ask your AI assistant:
"Using the skill-authoring skill, help me create a new skill for <purpose>"
```

Or read [skill-authoring/SKILL.md](skill-authoring/SKILL.md) for the full procedure.

## SKILL.md Schema

```yaml
---
name: skill-name
description: One-line description
---

# Skill Title

## Required Tools
- `mcp-name` — What for

## Procedure
1. Step one
2. Step two

## Examples
**Input:** "Review the AuthService changes"
**Output:** Structured review with severity-tagged findings

## Output Format
Expected output structure

## Constraints
- Rules and limitations

## Verification (The Loop)
1. Tier 1: Compile check (`swift build`)
2. Tier 2: Tests
```

## Loading Skills at Runtime

Skills are loaded by the agent/orchestrator at runtime:
1. Agent reads `_skill_catalog.md` (lightweight index)
2. Matches user intent to skill via trigger phrases
3. Loads only the needed `SKILL.md` into context
4. After task completion, unloads skill to free token budget

See [ADR-002: Skills Runtime Architecture](../adr/002-skills-runtime-architecture.md) for details.
