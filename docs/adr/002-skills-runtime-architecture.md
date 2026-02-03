# ADR-002: Skills Runtime Architecture

**Status:** Proposed  
**Date:** 2026-02-02  
**Deciders:** Engineering Team  
**Tags:** architecture, skills, mcp, orchestration  
**Supersedes:** Partially supersedes ADR-001 (compile-time agent generation)

---

## Context

ADR-001 established the "Stitched Brain" architecture for compiling agents from Personas + Standards. While this provides version-controlled consistency, modern LLM harnesses (GitHub Copilot, Cursor, Antigravity) demonstrate a more flexible pattern: **runtime skill injection**.

The current state has limitations:

1. **Static Binding** — Agents must be regenerated when standards change
2. **Coarse Granularity** — Can't share a single procedure across agents without tag overlap
3. **No Dynamic Routing** — Agent selection happens before execution, not during
4. **Industry Divergence** — Modern systems favor runtime skill loading over compiled prompts

We need a layered architecture that separates:
- **Tool Access** (MCP Servers)
- **Procedural Knowledge** (Skills)
- **Orchestration Logic** (Agent)

---

## Decision

Adopt a **3-Layer Runtime Architecture** for skill management:

```
┌─────────────────────────────────────────────────────────┐
│  Layer 3: AGENT ORCHESTRATOR                            │
│  ┌───────────────────────────────────────────────────┐  │
│  │ • Simple routing loop: "Which skill for this?"    │  │
│  │ • Loads skills into context window                │  │
│  │ • Manages MCP server connections                  │  │
│  └───────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│  Layer 2: SKILLS                                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐    │
│  │ Code Review │ │ Unit Test   │ │ Security Scan   │    │
│  │ SKILL.md    │ │ SKILL.md    │ │ SKILL.md        │    │
│  └─────────────┘ └─────────────┘ └─────────────────┘    │
├─────────────────────────────────────────────────────────┤
│  Layer 1: MCP SERVERS                                   │
│  ┌────────┐ ┌──────────┐ ┌─────────┐ ┌────────────┐     │
│  │Postgres│ │FileSystem│ │  Git    │ │  Browser   │     │
│  │  MCP   │ │   MCP    │ │  MCP    │ │    MCP     │     │
│  └────────┘ └──────────┘ └─────────┘ └────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### Layer 1: MCP Servers (The Hands)

**Role:** Provide raw, atomic access to external systems.

**Design Principles:**
- ✅ **Keep them "dumb"** — A `postgres-mcp` that runs any query, not a `financial-analysis-mcp`
- ✅ **Maximize reuse** — Same MCP serves multiple skills
- ✅ **Minimal logic** — No business rules, just capability exposure

**Examples:**
| MCP Server | Operations |
|------------|------------|
| `filesystem` | read, write, list, search |
| `git` | status, diff, commit, log |
| `postgres` | query, execute, transaction |
| `browser` | navigate, click, screenshot |

### Layer 2: Skills (The Brain's Instructions)

**Role:** Define workflows and business logic as reusable procedures.

**Design Principles:**
- ✅ **Single-purpose** — One skill = one coherent task
- ✅ **Declarative dependencies** — Skill declares which MCPs it needs
- ✅ **Runtime loadable** — No pre-compilation required

**SKILL.md Schema:**

```yaml
---
name: code-review
version: 1.0.0
description: Perform structured code review following team standards
tags: [quality, review]
required_mcps: [filesystem, git]
trigger_phrases:
  - "review this code"
  - "code review"
  - "check this PR"
---

## Context
You are a Senior Code Reviewer. Your role is to identify bugs, 
security issues, and maintainability concerns in proposed changes.

## Procedure
1. **Understand scope**: Read the files or PR diff
2. **Check for bugs**: Logic errors, edge cases, null handling
3. **Security review**: Input validation, injection risks
4. **Style check**: Naming, formatting, consistency
5. **Summarize**: Provide actionable feedback

## Output Format
- List issues by severity: 🔴 Critical, 🟡 Warning, 🔵 Suggestion
- Include file paths and line numbers
- Provide fix suggestions

## Constraints
- Do not auto-fix; only report findings
- Focus on the changed code, not the entire file

## Verification (The Loop)
Before completing, verify your work:
1. **Tier 1**: Ensure code compiles (`swift build`)
2. **Tier 2**: Run targeted tests for changed files
3. **Fail?** → Fix issues and repeat from step 1
4. **Pass?** → Proceed to output
```

---

## Verification Ownership (Skills vs Agents)

Verification is a **shared responsibility** with clear ownership:

| Component | Owns | Doesn't Own |
|-----------|------|-------------|
| **Skill** | Verification *requirements* (what to check) | Loop execution, retry logic |
| **Agent** | Loop *execution*, retry limits, escalation | Domain-specific test commands |

### Why This Split?

- **Skills are stateless** — They define "run `swift test --filter X`" but don't track "I've failed 3 times"
- **Agents have session context** — They decide "retry once more" or "escalate to user"
- **Same skill, different agents** — Strict agent (1 retry) vs lenient agent (5 retries)

### The Pattern

```
┌─────────────────────────────────────────────────────────────┐
│  SKILL (defines requirements)                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ## Verification                                       │  │
│  │ - Compile: `swift build`                              │  │
│  │ - Test: `swift test --filter ChangedModule`           │  │
│  │ - Criteria: No errors, no new warnings                │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼ (agent reads skill, executes loop)
┌─────────────────────────────────────────────────────────────┐
│  AGENT (executes loop)                                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ max_retries = 3  # Agent-level policy                 │  │
│  │                                                       │  │
│  │ while not verified and retries < max_retries:         │  │
│  │     result = run_skill_verification_steps()           │  │
│  │     if result.failed:                                 │  │
│  │         fix_issues(result.errors)                     │  │
│  │         retries += 1                                  │  │
│  │     else:                                             │  │
│  │         verified = True                               │  │
│  │                                                       │  │
│  │ if not verified:                                      │  │
│  │     escalate_to_user()  # Agent decides escalation    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Tiered Verification (Skill-Defined)

| Tier | Type | Scope | Time | When to Use |
|------|------|-------|------|-------------|
| **Tier 1** | Static | Compile / Lint | <30s | Always — before any output |
| **Tier 2** | Scoped | Targeted Tests | 1-2m | After code changes |
| **Tier 3** | Module | Test Target | 5-10m | Cross-module changes |
| **Tier 4** | Full | CI Suite | 10-30m | Pre-merge validation |

**Agent Guidance:**
- **Minimum**: Always run Tier 1 before completing
- **Code changes**: Run Tier 1 + Tier 2
- **Never skip**: Agents must not return code that doesn't compile

### Verification Section Template

Every skill that modifies code should include:

```markdown
## Verification (The Loop)

Before completing, verify your work:

1. **Tier 1 - Compile Check**
   - Run: `swift build` or `xcodebuild ... build`
   - Fail? → Fix compilation errors, repeat

2. **Tier 2 - Targeted Tests** (if applicable)
   - Run: `swift test --filter <ChangedModule>`
   - Fail? → Fix test failures, repeat

3. **Completion Criteria**
   - [ ] Code compiles without errors
   - [ ] Targeted tests pass
   - [ ] No new warnings introduced
```

### Output Sanitization

Tool outputs (xcodebuild, TSan, etc.) should be sanitized to maximize signal:

| Before | After |
|--------|-------|
| 500-line xcodebuild log | "✅ Build succeeded" or "❌ 3 errors in AuthService.swift" |
| Raw TSan dump | Grouped issues with fix suggestions |

Use sanitization scripts (e.g., `tsan-sanitizer.py`) to convert verbose output into actionable summaries.

**Why This Matters:**
- Prevents agents from returning broken code to users
- Creates predictable, reliable agent behavior
- Reduces hallucination by grounding agents in real feedback

**Directory Structure:**

> [!NOTE]
> Skills live in `docs/` (not `.copilot/` or `.cursor/`) to remain **LLM-agnostic**. Any harness can read them.

```
docs/skills/
├── code-review/
│   └── SKILL.md
├── unit-testing/
│   ├── SKILL.md
│   └── templates/
│       └── swift_xctest.md      # Supporting templates
├── security-scan/
│   └── SKILL.md
└── documentation/
    └── SKILL.md
```

### Layer 3: Agent Orchestrator (The Router)

**Role:** Route requests to skills and manage execution context.

**Design Principles:**
- ✅ **Keep it light** — Simple loop: "Which skill should I load?"
- ✅ **No nested agents** — Stack skills into context, not agents on agents
- ✅ **Dynamic discovery** — Scan skills directory at runtime

**Orchestration Flow:**

```
User Request
     │
     ▼
┌─────────────────────┐
│ 1. Parse Intent     │ "I need to review this code"
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ 2. Match Skill      │ trigger_phrases → code-review
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ 3. Validate MCPs    │ required_mcps: [filesystem, git] ✓
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ 4. Inject Context   │ Load SKILL.md into context window
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│ 5. Execute          │ Agent follows skill procedure
└─────────────────────┘
```

---

## Skills vs Agents Clarification

The relationship between Skills and Agents is complementary:

| Aspect | Agent (`.agent.md`) | Skill (`SKILL.md`) |
|--------|---------------------|---------------------|
| **Identity** | "Who am I?" | "How do I do X?" |
| **Scope** | Domain-level persona | Task-level procedure |
| **Lifecycle** | Session-persistent | Loaded on-demand |
| **Composition** | May reference multiple skills | Self-contained |
| **State** | Maintains conversation context | Stateless instructions |

**Example Relationship:**
- `testing.agent.md` (Agent) defines the Testing Specialist persona
- The agent can load `unit-testing` skill for writing tests
- The agent can load `mock-generation` skill for creating mocks
- Skills share the agent's MCP connections

---

## Migration Strategy

### Phase 1: Parallel Operation (Immediate)

- Create `docs/skills/` directory structure
- Keep `stitch-brain.py` operational for existing agents
- New procedures go into skills, not standards

### Phase 2: Skill Extraction (Gradual)

- Extract reusable procedures from `docs/standards/` into skills
- Map `stitcher_rules` of type STEP/CMD/BENEFIT → Skills
- Keep RULE types in standards (they're constraints, not procedures)

### Phase 3: Runtime Loader (Implementation)

- Implement skill discovery in MCP orchestrator
- Add `load_skill` tool for dynamic injection
- Deprecate `stitch-brain.py` recipe system

### Phase 4: Cleanup

- Remove `stitch-brain.py` (or repurpose for documentation generation)
- Agents become lightweight identity + skill references
- Standards become pure constraints (THE LAW only)

---

## Alternatives Considered

### 1. Keep Everything Compiled (Status Quo)

**Rejected:** Doesn't support dynamic skill selection or cross-agent sharing without tag complexity.

### 2. Skills as MCP Tools

**Rejected:** Mixes abstraction layers. MCPs should be atomic tools, not procedures.

### 3. Skills as Subagents

**Rejected:** Creates coordination overhead. "Stack skills, not agents."

### 4. Central Skill Registry Service

**Deferred:** Adds infrastructure complexity. Filesystem-based discovery is sufficient for now.

---

## Consequences

### Positive

- ✅ **Dynamic Flexibility** — Skills can be added/updated without regeneration
- ✅ **Fine-Grained Reuse** — Share exact procedures across agents
- ✅ **Industry Alignment** — Matches patterns in Cursor, Antigravity, etc.
- ✅ **Clear Separation** — Tools vs Procedures vs Orchestration
- ✅ **Simpler Agents** — Agents become "identity + skill router"

### Negative

- ⚠️ **Runtime Discovery Overhead** — Must scan skills directory
- ⚠️ **Skill Proliferation** — Risk of too many fine-grained skills
- ⚠️ **No Type Safety** — SKILL.md is freeform markdown
- ⚠️ **Migration Effort** — Existing standards need extraction

### Mitigations

- Cache skill registry on startup
- Document guidelines for skill granularity (see below)
- Validate SKILL.md frontmatter schema at load time
- Phased migration allows gradual adoption

---

## Skill Granularity Guidelines

To answer "how granular should skills be?":

| Granularity | Example | When to Use |
|-------------|---------|-------------|
| **Coarse** | "Code Review" (multi-step) | Distinct workflow with clear start/end |
| **Fine** | "Check Security Headers" | Atomic check, likely called from another skill |

**Recommended:** Start with **coarse, single-purpose skills**. Split only when:
- A sub-procedure is reused across 3+ skills
- The skill exceeds ~50 lines of procedure steps
- Users naturally ask for the sub-task independently

**Anti-Patterns:**
- ❌ One skill per CLI command (too fine)
- ❌ "Mega-skill" covering entire domain (too coarse)
- ❌ Skills with significant overlap

---

## Implementation Notes

### Skill Discovery Algorithm

```python
def discover_skills(skills_dir: Path) -> dict[str, Skill]:
    """Scan skills directory and build registry."""
    registry = {}
    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir():
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                skill = parse_skill(skill_file)
                registry[skill.name] = skill
    return registry
```

### Skill Loading Verification

When a skill is loaded, the agent should acknowledge:

```
✓ Loaded skill: code-review (v1.0.0)
  Required MCPs: filesystem, git
  Procedure: 5 steps
```

This provides audit trail and debugging visibility.

### Skill Compilation: stitch-skills.py

While skills are authored in `docs/skills/` (LLM-agnostic), they must be compiled to vendor-specific locations for proper discovery.

**Compilation Flow:**

```
docs/skills/                    ← Source of truth (LLM-agnostic)
     │
     ▼  stitch-skills.py
     │
     ├── .github/skills/        ← GitHub Copilot CLI
     ├── .copilot/skills/       ← Alternative Copilot location
     └── .cursor/skills/        ← Cursor (if needed)
```

**Compilation Script Responsibilities:**

1. **Scan** `docs/skills/*/SKILL.md`
2. **Validate** frontmatter (`name`, `description` required)
3. **Transform** if needed (e.g., strip incompatible frontmatter fields)
4. **Copy** to vendor-specific output directories
5. **Log** skill registry for debugging

**Example Implementation:**

```python
#!/usr/bin/env python3
# stitch-skills.py

from pathlib import Path
import shutil

SKILLS_SOURCE = Path("docs/skills")
VENDOR_OUTPUTS = [
    Path(".github/skills"),
    Path(".copilot/skills"),
]

def stitch_skills():
    for skill_dir in SKILLS_SOURCE.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        
        # Copy to each vendor location
        for vendor_dir in VENDOR_OUTPUTS:
            target = vendor_dir / skill_dir.name
            target.mkdir(parents=True, exist_ok=True)
            shutil.copy2(skill_file, target / "SKILL.md")
            
            # Copy any templates
            templates = skill_dir / "templates"
            if templates.exists():
                shutil.copytree(templates, target / "templates", 
                               dirs_exist_ok=True)
        
        print(f"✓ Stitched: {skill_dir.name}")

if __name__ == "__main__":
    stitch_skills()
    print("✨ Skills compiled to vendor directories.")
```

**Integration with Agents:**

Run both scripts together:

```bash
# Compile agents and skills
python3 docs/scripts/stitch-brain.py
python3 docs/scripts/stitch-skills.py
```

Or add a combined command:

```bash
# In Makefile or package.json
make stitch  # Runs both
```

---

## Related Documents

- [ADR-001: Stitched Brain Architecture](001-stitched-brain-architecture.md)
- [Agents vs Skills Knowledge](../README.md)
- [MCP Orchestrator README](../../.copilot/tools/orchestrator/README.md)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-02 | Team | Initial proposal |
