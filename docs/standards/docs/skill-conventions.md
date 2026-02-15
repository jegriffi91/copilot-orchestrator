---
id: skill_conventions
type: practice
tags: [docs, common]
stitcher_rules:
  - "RULE: Frontmatter Required | ACTION: Every SKILL.md must have name and description in YAML frontmatter | SEVERITY: CRITICAL"
  - "RULE: Numbered Procedures | ACTION: Skill procedures must use numbered steps, not bullets | SEVERITY: WARN"
  - "RULE: Persona Line Budget | ACTION: Personas must be under 50 lines, voice only | SEVERITY: WARN"
  - "RULE: No Orchestration in Agents | ACTION: Agent personas must NOT contain orchestration logic (read file, write result) | SEVERITY: CRITICAL"
  - "RULE: Imperative Triggers | ACTION: Reference loads must use ACTION REQUIRED pattern at point of decision | SEVERITY: WARN"
  - "RULE: Reference Token Budget | ACTION: Each references/ file must stay within 1000-2000 tokens | SEVERITY: WARN"
  - "STEP: Validate Frontmatter | CMD: Check that name and description fields exist in SKILL.md frontmatter | SEVERITY: CRITICAL"
  - "STEP: Validate Persona Length | CMD: Count lines in persona file, must be under 50 | SEVERITY: WARN"
---

# Skill & Agent Conventions

## Overview

Standards for authoring skills, agents, and personas in the copilot-orchestrator. These rules ensure consistency across the documentation layer and prevent architectural drift.

## Rule 1: Frontmatter Required

Every `SKILL.md` must begin with YAML frontmatter containing at minimum:

```yaml
---
name: skill-name
description: One-line description of when to use this skill.
---
```

Without these fields, the platform cannot index or discover the skill.

## Rule 2: Numbered Procedures

Skills represent step-by-step SOPs. Using numbered steps (not bullets) communicates sequence and dependency:

```markdown
## Procedure
1. **Analyze** the existing code structure
2. **Create** the migration plan
3. **Execute** changes one file at a time
```

## Rule 3: Persona Line Budget

Personas define *voice*, not *knowledge*. Keep them under 50 lines. Technical rules belong in `docs/standards/`, procedures in `docs/skills/`.

## Rule 4: No Orchestration in Agents

Agent personas must focus on identity and rejection criteria. They must **never** include orchestration instructions like "read this file", "write to .result.md", or "delegate to agent X". Orchestration is the job of the MCP orchestrator tool.

## Rule 5: Imperative Triggers

When a skill needs to load a reference file, use the imperative trigger pattern at the *point of decision*, not in a generic header:

```markdown
**ACTION REQUIRED:** Read `references/state-management.md` BEFORE evaluating property wrappers.
```

## Rule 6: Reference Token Budget

Each file in `references/` should contain ~1,000-2,000 tokens. If a reference exceeds this, split it into focused sub-references.
