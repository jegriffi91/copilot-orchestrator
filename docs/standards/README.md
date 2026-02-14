# Standards Architecture Guide

## Overview

This directory contains **dual-layer documentation**: Human-readable guides with embedded machine-readable rules for AI agents. Standards represent **The Law** — immutable domain constraints that every agent must follow.

> In the [3-layer architecture](../adr/002-skills-runtime-architecture.md), Standards are part of the **Agent (Soul)** layer's constitutional knowledge. They define *what rules apply*, while [Skills](../skills/README.md) define *how to do things* and [Workflows](../workflows/README.md) define *how to verify*.

## Directory Structure

```
docs/standards/
├── common/          # Swift, concurrency, architecture patterns
├── design/          # Atlas design system, UI tokens
├── sdui/            # Server-Driven UI, GraphQL schemas
└── testing/         # Unit testing, mocking, test infrastructure
```

> [!NOTE]
> Verification workflows have moved to `docs/workflows/` — see [Workflows README](../workflows/README.md).

## The Stitcher Rules Schema

Every standard file MUST begin with YAML frontmatter containing a `stitcher_rules` block. This block is what agents consume.

### Required Frontmatter Structure

```yaml
---
id: unique_snake_case_id
type: practice | process
tags: [swift6, testing, design, sdui, ci, common]
stitcher_rules:
  - "RULE: Name | ACTION: What to do | SEVERITY: CRITICAL"
  - "STEP: Name | CMD: command to run | SEVERITY: WARN"
  - "CMD: Description | ACTION: command here | SEVERITY: CRITICAL"
  - "BENEFIT: Description | ACTION: benefit text | SEVERITY: WARN"
related_verification: docs/workflows/verify_file.md
---
```

### Field Types

#### 1. RULE (Practices & Constraints)
Use for architectural decisions, banned patterns, or required practices.

**Format:**
```yaml
"RULE: Name | ACTION: Constraint description | SEVERITY: CRITICAL|WARN"
```

**Example:**
```yaml
stitcher_rules:
  - "RULE: No Raw Tasks | ACTION: Use Task.detached or Actor isolation | SEVERITY: CRITICAL"
  - "RULE: MainActor UI | ACTION: All UI updates must be on @MainActor | SEVERITY: CRITICAL"
  - "RULE: Sendable Types | ACTION: All passed data must conform to Sendable | SEVERITY: WARN"
```

**Output in Agent Brain:**
```
- [CRITICAL] | No Raw Tasks | → Use Task.detached or Actor isolation
- [CRITICAL] | MainActor UI | → All UI updates must be on @MainActor
- [WARN] | Sendable Types | → All passed data must conform to Sendable
```

#### 2. STEP (Verification Steps)
Use for sequential verification processes or checklists.

**Format:**
```yaml
"STEP: Name | ACTION: What to verify | SEVERITY: CRITICAL|WARN"
"STEP: Name | CMD: command to run | SEVERITY: CRITICAL|WARN"
```

**Example:**
```yaml
stitcher_rules:
  - "STEP: Strict Concurrency | CMD: Set SWIFT_STRICT_CONCURRENCY = complete | SEVERITY: CRITICAL"
  - "STEP: Compile Warnings | CMD: xcodebuild with -quiet to surface warnings | SEVERITY: CRITICAL"
  - "STEP: Package Check | ACTION: Verify component in correct package | SEVERITY: CRITICAL"
```

**Output in Agent Brain:**
```
- [CRITICAL] | STEP: Strict Concurrency | CMD: Set SWIFT_STRICT_CONCURRENCY = complete
- [CRITICAL] | STEP: Compile Warnings | CMD: xcodebuild with -quiet to surface warnings
- [CRITICAL] | STEP: Package Check | → Verify component in correct package
```

#### 3. CMD (Executable Commands)
Use for CLI commands, scripts, or tools that agents should run.

**Format:**
```yaml
"CMD: Description | ACTION: full command with arguments | SEVERITY: CRITICAL|WARN"
```

**Example:**
```yaml
stitcher_rules:
  - "CMD: Run TSan Sanitized | ACTION: python3 docs/scripts/tsan-sanitizer.py --scheme ECW | SEVERITY: CRITICAL"
  - "CMD: Parse Existing Log | ACTION: python3 docs/scripts/tsan-sanitizer.py --raw-log tsan.log | SEVERITY: WARN"
  - "CMD: CI JSON Output | ACTION: python3 docs/scripts/tsan-sanitizer.py --scheme ECW --json | SEVERITY: WARN"
```

**Output in Agent Brain:**
```
- [CRITICAL] | CMD: Run TSan Sanitized | → python3 docs/scripts/tsan-sanitizer.py --scheme ECW
- [WARN] | CMD: Parse Existing Log | → python3 docs/scripts/tsan-sanitizer.py --raw-log tsan.log
- [WARN] | CMD: CI JSON Output | → python3 docs/scripts/tsan-sanitizer.py --scheme ECW --json
```

#### 4. BENEFIT (Outcomes & Value)
Use to communicate the "why" or impact of a tool/process to agents.

**Format:**
```yaml
"BENEFIT: Description | ACTION: measurable outcome | SEVERITY: WARN"
```

**Example:**
```yaml
stitcher_rules:
  - "BENEFIT: Deduplication | ACTION: 47 raw issues → 12 unique patterns | SEVERITY: WARN"
  - "BENEFIT: Stack Reduction | ACTION: 50 frames → Top 3 relevant frames | SEVERITY: WARN"
  - "BENEFIT: Actionable Grouping | ACTION: Issues grouped by file for batch fixing | SEVERITY: WARN"
```

**Output in Agent Brain:**
```
- [WARN] | BENEFIT: Deduplication | → 47 raw issues → 12 unique patterns
- [WARN] | BENEFIT: Stack Reduction | → 50 frames → Top 3 relevant frames
- [WARN] | BENEFIT: Actionable Grouping | → Issues grouped by file for batch fixing
```

### Severity Levels

| Severity | Meaning | Agent Behavior |
|----------|---------|----------------|
| `CRITICAL` | Must follow / Must run | Blocking errors if violated |
| `WARN` | Should follow / Should run | Non-blocking warnings |

## Tag-Based Filtering

The stitcher uses tags to route rules to the correct specialized agents:

| Tag | Target Agent | Purpose |
|-----|--------------|---------|
| `common` | All agents | Swift patterns, architecture basics |
| `swift6` | Testing, Common | Concurrency, actors, Sendable |
| `testing` | Testing agent | Unit tests, mocks, XCTest |
| `ci` | Testing agent | Build scripts, automation |
| `design` | SDUI agent | Atlas, UI tokens, spacing |
| `sdui` | SDUI agent | GraphQL, component mapping |

**Example:** A file with `tags: [swift6, ci]` will be included in the Testing agent brain (both tags match `allowed_tags: [testing, common, ci]`).

## Agent Recipes

Configured in `docs/scripts/publish.py`:

```python
AGENT_RECIPES = {
    "testing.agent.md": {
        "persona": "qa-kien.md",
        "sources": ["testing"],  # Folders in docs/standards/ to scan
        "allowed_tags": ["testing", "common", "ci"],
        "description": "Specialist in Unit Testing, Mocking Strategies, and Snapshot Tests."
    },
    "sdui.agent.md": {
        "persona": "sdui-dev.md",
        "sources": ["sdui"],
        "allowed_tags": ["sdui", "common", "design"],
        "description": "Specialist in Server-Driven UI (SDUI), GraphQL Schemas, and Component Mapping."
    }
}
```

## Writing Standards

### Template

```markdown
---
id: my_standard
type: practice
tags: [common, swift6]
stitcher_rules:
  - "RULE: No Force Unwrap | ACTION: Use guard let or if let | SEVERITY: CRITICAL"
  - "RULE: Error Propagation | ACTION: Throw errors, don't return optionals | SEVERITY: WARN"
related_verification: verify-swift-patterns.md
---

# My Standard Title

## Overview
Human-readable explanation of why this standard exists...

## Rule 1: No Force Unwrap
**Rationale:** Force unwrapping causes crashes when nil...

**Examples:**
\`\`\`swift
// ❌ Bad
let value = dict["key"]!

// ✅ Good
guard let value = dict["key"] else { return }
\`\`\`

## Rule 2: Error Propagation
...
```

### Constraints

1. **Stitcher Block:**
   - ≤ 20 words per rule
   - No explanations or "why"
   - Boolean logic only
   - Must include SEVERITY

2. **Markdown Body:**
   - Detailed examples
   - Edge cases
   - Philosophy and rationale
   - Code snippets

3. **No Large Data Blocks:**
   - Don't embed full JSON/XML schemas
   - Use reference pointers: "REQUIRED CONTEXT: Add `docs/references/tokens.json` to chat"

## Agent Output Structure

The stitcher generates specialized agent brains with **frontmatter** and three content sections:

### Frontmatter (GitHub Copilot Integration)
```yaml
---
agent: testing                    # Agent identifier (kebab-case)
name: Testing                     # Display name
description: Specialist in...    # Brief description
version: 1.0.0                    # Semantic version
generated: 2026-01-16 13:50:14    # Generation timestamp
tags: testing, common, ci         # Allowed tags for filtering
---
```

This frontmatter allows GitHub Copilot to:
- Recognize the file as a custom agent
- Display proper metadata in the UI
- Track version and generation date
- Filter by tags

### 1. IDENTITY (Persona)
Human-readable voice, tone, and mental models from the persona file.

### 2. THE LAW (Stitcher Rules - RULE types only)
**Purpose:** Constraints and practices during development

**Contains:**
- `RULE` types: architectural decisions, banned patterns, required practices

**Example Output:**
```markdown
# 🏛️ THE LAW (Stitcher Rules)

> **Format:** RULE types define constraints during development.

## From: docs/standards/testing/service-mocking.md

- [CRITICAL] | Actor Services | → All services must be actors with @Service macro
- [CRITICAL] | Async Methods | → Use async/await exclusively, no completion handlers
- [WARN] | Singleton Access | → Access via ServiceName.shared
```

### 3. THE LOOP (Verification Process - STEP/CMD/BENEFIT types)
**Purpose:** Executable verification steps and commands

**Structure:**
- **Quick Commands & Steps:** Extracted `STEP`, `CMD`, `BENEFIT` rules
- **Detailed Workflows:** Full markdown from `related_verification` links

**Example Output:**
```markdown
# 🔄 THE LOOP (Verification Process)

> **Constraint:** Before finishing any task, you must run these verification steps.

## Quick Commands & Steps

### From: docs/workflows/tsan-quick-reference.md

- [CRITICAL] | CMD: Run TSan Sanitized | → python3 docs/scripts/tsan-sanitizer.py --scheme ECW
- [WARN] | BENEFIT: Deduplication | → 47 raw issues → 12 unique patterns

### From: docs/workflows/verify-swift6-incremental.md

- [CRITICAL] | STEP: Classify Change | → Determine tier (static/scoped/module) before verification
- [CRITICAL] | STEP: Tier 1 Compile | CMD: xcodebuild build -quiet 2>&1 | grep '<YourFile>'

## Detailed Workflows

### Verify: verify-swift6-incremental
[Full markdown content from docs/workflows/verify-swift6-incremental.md]
```

This separation ensures:
- **THE LAW** = What constraints apply while writing code
- **THE LOOP** = What steps to run to verify correctness

## Verification

After stitching, check that:
- [ ] CMD fields appear in workflow rules
- [ ] BENEFIT fields show measurable outcomes
- [ ] Tags filter correctly (testing agent shouldn't see design rules)
- [ ] All CRITICAL rules are blocking-worthy
- [ ] Commands are executable without modification

## Examples

See actual implementations:
- `docs/standards/testing/service-mocking.md` - RULE pattern
- `docs/workflows/tsan-quick-reference.md` - CMD + BENEFIT pattern
- `docs/workflows/verify-swift6-incremental.md` - STEP pattern (tiered verification)
- `docs/standards/sdui/component-generation.md` - Mixed patterns

---

**Philosophy:** Documentation is for Humans. Rules are for Agents. Write both layers well.
