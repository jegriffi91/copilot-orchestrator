# Publish Pipeline Reference

## Overview

The `publish.py` script is the unified pipeline for compiling agents and publishing skills to vendor-specific output directories. It replaces the original `stitch-brain.py` (agents only) and the planned-but-never-built `publish-skills.py`.

## Architecture

```
docs/personas/         ──┐
docs/standards/        ──┤── publish.py agents ──→ .github/agents/*.agent.md
AGENT_RECIPES config   ──┘

docs/skills/*/SKILL.md ──┐
docs/skills/*/refs/    ──┤── publish.py skills ──→ .github/skills/*/
                         └── generates _skill_catalog.md
```

## Subcommands

### `publish.py agents`

Compiles agent files from personas + standards:

1. Reads `AGENT_RECIPES` configuration (maps output filename → persona + sources + tags)
2. Scans `docs/personas/` for the persona file
3. Scans `docs/standards/` for rules matching allowed tags
4. Compiles into `.github/agents/<name>.agent.md` with sections:
   - **IDENTITY** — from persona file
   - **THE LAW** — from filtered standards rules
   - **SKILLS** — list of linked skills from recipe

**When to re-run:**
- After editing any file in `docs/personas/`
- After editing any file in `docs/standards/`
- After adding/removing an agent recipe

### `publish.py skills`

Publishes skills + references to vendor directories:

1. Scans `docs/skills/*/SKILL.md`
2. Validates YAML frontmatter (name, description required)
3. Applies shadow frontmatter (strips non-standard YAML fields for vendor compatibility)
4. Copies `references/` and `templates/` subdirectories alongside SKILL.md
5. Generates `_skill_catalog.md` discovery index
6. Outputs to `.github/skills/`

**When to re-run:**
- After creating or editing a SKILL.md
- After adding/editing reference files
- After adding a new skill directory

### `publish.py all`

Runs both `agents` and `skills` in sequence. Use this as the default.

## Agent Recipe Format

```python
AGENT_RECIPES = {
    "agent-filename.agent.md": {
        "persona": "persona-filename.md",     # From docs/personas/
        "sources": ["common", "design"],       # Standards subdirectories to scan
        "allowed_tags": ["common", "design"],  # Filter standards by these tags
        "skills": ["swiftui"],                 # Skills this agent can load
        "description": "One-line description."
    }
}
```

## Shadow Frontmatter

Some vendors (e.g., GitHub Copilot CLI) don't support custom YAML fields. Shadow frontmatter strips non-standard fields while preserving the content:

```
Original (docs/skills/):          Published (.github/skills/):
---                               ---
name: swiftui                     name: swiftui
description: ...                  description: ...
custom_field: value    ← stripped
---                               ---
```

## Skill Catalog

`publish.py skills` generates `_skill_catalog.md` — a discovery index listing all published skills:

```markdown
# Skill Catalog

| Skill | Description |
|-------|-------------|
| swiftui | Write, review, or improve SwiftUI code... |
| knowledge-architecture | Guidelines for distributing knowledge... |
```

Agents use this catalog to discover which skills are available at runtime.

## Output Directories

| Command | Output |
|---------|--------|
| `publish.py agents` | `.github/agents/*.agent.md` |
| `publish.py skills` | `.github/skills/<name>/SKILL.md` + `references/` |

## Validation Checks

The pipeline validates:
- [ ] All referenced persona files exist
- [ ] SKILL.md has valid YAML frontmatter (name + description)
- [ ] No orphan references (every file in `references/` is linked from SKILL.md)
- [ ] THE LAW section stays under 15 rules (planned)
- [ ] Token budgets are within limits (planned)

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Agent missing rules | Standards directory empty | Add rules to `docs/standards/<tag>/` |
| Skill not in catalog | No SKILL.md in directory | Create `SKILL.md` with frontmatter |
| References not copied | Missing `references/` dir | Create `references/` subdir in skill |
| Shadow frontmatter strips too much | Non-standard YAML field | Only use `name` and `description` in frontmatter |
