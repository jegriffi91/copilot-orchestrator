# Skills Directory

This directory contains reusable **procedural knowledge** for AI agents.

## Philosophy

Skills answer: **"How do I do X?"**

| Layer | Location | Purpose |
|-------|----------|---------|
| Personas | `docs/personas/` | Agent identity (who) |
| Standards | `docs/standards/` | Domain rules (what) |
| **Skills** | `docs/skills/` | Procedures (how) |

Skills are **LLM-agnostic**—they work with any harness (Copilot, Cursor, Claude, etc.).

## Structure

```
docs/skills/
├── skill-authoring/      # Meta-skill: how to create skills/agents
│   └── SKILL.md
├── code-review/          # Example: code review procedure
│   └── SKILL.md
└── README.md             # This file
```

Each skill is a folder containing:
- `SKILL.md` — Required: Main skill definition
- `templates/` — Optional: Supporting templates

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

## Output Format
Expected output structure

## Constraints
- Rules and limitations

## Verification (The Loop)
1. Tier 1: Compile check
2. Tier 2: Tests
```

## Loading Skills at Runtime

Skills are loaded by the agent/orchestrator at runtime:
1. Orchestrator scans `docs/skills/*/SKILL.md`
2. Builds a skill registry
3. Injects relevant skill into agent context when needed

See [ADR-002: Skills Runtime Architecture](../adr/002-skills-runtime-architecture.md) for details.
