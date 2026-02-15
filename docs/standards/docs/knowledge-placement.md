---
id: knowledge_placement
type: practice
tags: [docs, common]
stitcher_rules:
  - "RULE: Tier 1 Budget | ACTION: Constitution (docs/standards/) must stay under 1000 tokens per agent | SEVERITY: CRITICAL"
  - "RULE: Tier 2 Budget | ACTION: Playbook (SKILL.md) must stay within 2000-3000 tokens | SEVERITY: WARN"
  - "RULE: Tier 3 Budget | ACTION: Encyclopedia (references/) must stay within 1000-2000 tokens per file | SEVERITY: WARN"
  - "RULE: Linter-Catchable Knowledge | ACTION: If a linter or compiler can catch it, do not waste agent context on it | SEVERITY: WARN"
  - "RULE: Zero-Exception to Tier 1 | ACTION: Only universal invariants with zero exceptions belong in docs/standards/ | SEVERITY: CRITICAL"
  - "RULE: Procedures to Tier 2 | ACTION: Multi-step processes and heuristics belong in docs/skills/ | SEVERITY: WARN"
  - "RULE: Examples to Tier 3 | ACTION: Code examples, flowcharts, and edge cases belong in references/ | SEVERITY: WARN"
---

# Knowledge Placement Standards

## Overview

Rules for placing new knowledge in the correct tier of the 3-Tier Cache Hierarchy. Misplaced knowledge wastes token budget and degrades agent performance.

## The 3-Tier Hierarchy

| Tier | Name | Location | Budget | Contains |
|------|------|----------|--------|----------|
| 1 | Constitution | `docs/standards/` | < 1,000 tokens | Zero-exception invariants |
| 2 | Playbook | `docs/skills/` | 2,000-3,000 tokens | Procedures, heuristics |
| 3 | Encyclopedia | `references/` | 1,000-2,000 tokens/file | Examples, flowcharts |

## Quick Decision Test

1. **Linter Test**: Can a linter/compiler catch it? → Use the tool, not AI context
2. **Exception Test**: Are there zero exceptions? → Tier 1
3. **Procedure Test**: Is it a multi-step process or heuristic? → Tier 2
4. **Depth Test**: Does it need code examples or flowcharts? → Tier 3

## Override Precedence

When rules conflict: **Reference > Skill > Law**

- A Tier 3 reference can override a Tier 2 skill guideline for specific cases
- A Tier 2 skill can provide exceptions to Tier 1 laws (rare, must be documented)
- Tier 1 laws are defaults, not absolute overrides
