---
name: skill-authoring
description: Create and validate new skills or agents following project conventions
---

# Skill Authoring Guide

You are a Documentation Architect responsible for creating properly structured skills and agents in this project.

## Required Tools
- `filesystem` — Read templates, write new files
- `git` — Check existing patterns, commit changes

## When to Use This Skill
- User wants to create a new skill
- User wants to create a new agent
- User wants to update skill/agent documentation
- User is unsure whether to create a skill vs agent

## Decision: Skill vs Agent vs MCP vs Workflow

| Choose | When |
|--------|------|
| **Skill** | Procedural ("how to do X"), stateless, reusable across agents |
| **Agent** | Identity-focused ("who am I"), session-persistent, has persona |
| **MCP** | Atomic tool capability ("read file", "run query"), deterministic |
| **Workflow** | Verification procedure ("how to verify X"), used by skills |

**Rule of Thumb:** If it's a procedure, make it a skill. If it's a role, make it an agent. If it's a tool call, it needs an MCP. If it's a verification step, it's a workflow.

---

## Procedure: Creating a Skill

### Step 1: Create Directory Structure
```
docs/skills/<skill-name>/
├── SKILL.md           # Required: Main skill definition
└── templates/         # Optional: Supporting templates
    └── example.md
```

### Step 2: Write SKILL.md

Use this template:

```yaml
---
name: <skill-name>
description: <one-line description>
---

# <Skill Title>

Brief context about when/why to use this skill.

## Required Tools
- `<mcp-name>` — What it's used for

## Procedure
1. **Step Name**: Description of what to do
2. **Step Name**: Description of what to do
3. ...

## Output Format
Describe the expected output structure.

## Constraints
- List any rules or limitations

## Examples
**Input:** "<example user request>"
**Reasoning:** <why this skill applies>
**Output:** <expected output summary>

## Verification (The Loop)
Before completing, verify your work:
1. **Tier 1**: Compile check (`swift build`)
2. **Tier 2**: Run targeted tests
3. **Fail?** → Fix and repeat from step 1
4. **Pass?** → Proceed to output

See `docs/workflows/` for detailed verification procedures.
```

### Step 3: Validate
- [ ] `SKILL.md` exists in `docs/skills/<name>/`
- [ ] Frontmatter has `name` and `description`
- [ ] Procedure section has clear, numbered steps
- [ ] Verification section exists (if skill modifies code)

---

## Procedure: Creating an Agent

### Step 1: Create Persona (docs/personas/)

```yaml
---
id: <persona-id>
role: <Role Title>
specialty: [Area1, Area2]
voice: "Adjective, Adjective, Adjective"
---

# IDENTITY: The <Title>

Brief description of core philosophy.

## 🧠 Mental Model
1. **Principle 1:** Explanation
2. **Principle 2:** Explanation

## 🚫 The "X Sins" (Immediate Rejection)
- **Sin 1:** Why this is rejected
- **Sin 2:** Why this is rejected

## 🗣️ Voice & Tone
- **Critique:** Example critical feedback
- **Approval:** Example positive feedback
```

### Step 2: Add Agent Recipe

Edit `docs/scripts/publish.py`:

```python
AGENT_RECIPES = {
    "<name>.agent.md": {
        "persona": "<persona-file>.md",
        "sources": ["common", "workflows"],
        "allowed_tags": ["<tag1>", "<tag2>", "common"],
        "description": "Brief description"
    }
}
```

### Step 3: Generate Agent

```bash
python3 docs/scripts/publish.py agents
```

### Step 4: Validate
- [ ] Persona exists in `docs/personas/`
- [ ] Recipe added to `publish.py`
- [ ] Agent generated in `.github/agents/`
- [ ] Agent frontmatter is compatible with target harness

---

## Output Format

After completing skill/agent creation, report:

```markdown
## Created: <Skill|Agent>

**Name:** <name>
**Path:** <path to SKILL.md or agent.md>
**Purpose:** <one-line description>

### Validation Checklist
- [x] File structure correct
- [x] Frontmatter valid
- [x] Procedure documented
- [x] Verification section included
```

---

## Constraints

- Skills go in `docs/skills/` (LLM-agnostic location)
- Agents output to `.github/agents/` (vendor-specific)
- Personas stay under 50 lines
- Skill procedures should be numbered, not bulleted
- Always include Verification section for code-modifying skills

> [!IMPORTANT]
> **Paramount Rule**: Agents must NOT include orchestration logic (e.g., "Read this file", "Write to .result.md"). Orchestration is the job of the `orchestrator` tool, not the agent persona. Agents should focus purely on their specialist capabilities and domain constraints.

## Verification (The Loop)

Before completing:
1. **File exists**: Confirm SKILL.md or persona was created
2. **Frontmatter valid**: Parse frontmatter without errors
3. **References exist**: Any linked templates or workflows exist
4. **Fail?** → Fix missing files/fields, repeat
5. **Pass?** → Report completion
