---
name: knowledge-architecture
description: Guidelines for distributing knowledge to AI agents using the 3-tier cache hierarchy (Constitution, Playbook, Encyclopedia). Use when creating new skills, authoring agents, placing knowledge, or maintaining the publish pipeline.
---

# Knowledge Architecture Skill

## Overview

This skill codifies how knowledge is distributed to AI agents in the copilot-orchestrator. It defines the 3-tier cache hierarchy, the placement rubric for new knowledge, agent authoring guidelines, and the publish pipeline.

## The 3-Tier Cache Hierarchy

### Tier 1: Constitution (Compile-Time)
**Universal, zero-exception invariants baked into agent `.agent.md` files.**

- Managed by `publish.py agents`
- Budget: **<1,000 tokens** (~15 rules max)
- Source: `docs/standards/` → compiled into THE LAW section
- Examples: "All UI updates must be on @MainActor", "No force unwraps in production"
- **Do NOT put framework-specific rules here** (e.g., SwiftUI patterns belong in Tier 2)

### Tier 2: Playbook (Runtime SKILL.md)
**Domain-specific procedures, heuristics, and guides loaded on-demand.**

- Lives in `docs/skills/<name>/SKILL.md`
- Budget: **~2,000-3,000 tokens** per skill
- Contains imperative triggers that force-load Tier 3 references
- Examples: SwiftUI best practices, Swift 6 migration procedure, testing patterns

### Tier 3: Encyclopedia (Lazy-Loaded References)
**Dense knowledge files loaded only when explicitly triggered by Tier 2.**

- Lives in `docs/skills/<name>/references/*.md`
- Budget: **~1,000-2,000 tokens** per reference file
- Contains code examples, decision flowcharts, edge cases
- Loaded via imperative triggers: `ACTION REQUIRED: Read references/foo.md BEFORE...`

## Placing New Knowledge

**ACTION REQUIRED:** Read `references/tier-placement-rubric.md` BEFORE deciding where to put new knowledge.

**Quick Decision Test:**
1. **Linter Test**: Can a linter/compiler catch it? → Use the tool, not AI context
2. **Exception Test**: Are there zero exceptions? → Tier 1
3. **Procedure Test**: Is it a multi-step process or heuristic? → Tier 2
4. **Depth Test**: Does it need code examples or flowcharts? → Tier 3

## Authoring Skills

### SKILL.md Structure
```markdown
---
name: skill-name
description: One-line description of when to use this skill.
---

# Skill Title

## Overview
Brief description of what this skill covers.

## Workflow Decision Tree
Numbered workflows with imperative triggers to references.

## Core Guidelines
Condensed rules (heuristics, not exhaustive examples).

## Review Checklist
Checkbox items grouped by concern area.

## References
List of all reference files with one-line descriptions.
```

### Imperative Trigger Pattern
Force the AI to load Tier 3 content before acting:

```markdown
**ACTION REQUIRED:** Read `references/state-management.md` BEFORE evaluating property wrappers.
```

**Rules for triggers:**
- Place at the point of decision, not in a generic "read all" header
- Use `BEFORE` to clarify timing (read before acting)
- Link to the specific reference that contains the needed knowledge

### Reference File Structure
Each reference file should:
- Have a clear `# Title` and `## Section` structure
- Contain code examples with ✅ Good / ❌ Bad patterns
- End with a `## Summary Checklist`
- Stay within ~1,000-2,000 tokens

## Authoring Agents

### What Goes in `.agent.md`
An agent file contains three sections, each from a different source:

| Section | Source | Content |
|---------|--------|---------|
| **IDENTITY** | `docs/personas/*.md` | Voice, tone, mental model, rejection criteria |
| **THE LAW** | `docs/standards/` | Tier 1 constitutional rules (max 15) |

### What Stays Out of `.agent.md`
- Framework-specific rules (belong in skills)
- Code examples (belong in references)
- Multi-step procedures (belong in skills)
- Anything that varies by context (use spatial `.agentrules.md` files)

## The Publish Pipeline

**ACTION REQUIRED:** Read `references/publish-pipeline.md` for full pipeline details.

### Quick Reference
```bash
# Compile agents from personas + standards
python3 docs/scripts/publish.py agents

# Publish skills + references to vendor directories
python3 docs/scripts/publish.py skills

# Both
python3 docs/scripts/publish.py all
```

## Token Budget Summary

**ACTION REQUIRED:** Read `references/token-budget-guide.md` for budget enforcement details.

| Tier | Budget | Enforced By |
|------|--------|-------------|
| T1 (Constitution) | <1,000 tokens | `publish.py` (planned) |
| T2 (Playbook) | ~2,000-3,000 tokens | Authoring discipline |
| T3 (Encyclopedia) | ~1,000-2,000 tokens per file | Authoring discipline |
| **Total per session** | **~6,000 tokens** | T1 + one T2 + ~2 T3 |

## Override Precedence

When rules conflict: **Reference > Skill > Law**

- A Tier 3 reference can override a Tier 2 skill guideline for specific cases
- A Tier 2 skill can provide exceptions to Tier 1 laws (rare, must be documented)
- Tier 1 laws are defaults, not absolute overrides

## References

- `references/tier-placement-rubric.md` — Decision framework for placing new knowledge
- `references/token-budget-guide.md` — Token budget caps, measurement, and enforcement
- `references/publish-pipeline.md` — How `publish.py` compiles agents and publishes skills