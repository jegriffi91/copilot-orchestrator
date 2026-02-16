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

> [!NOTE]
> **Revision (per Deep Think review):** Added explicit Session State concept. Agent is now "The Soul" (identity + memory + router), Skills are "The Mind" (SOPs), MCPs are "The Hands".

```
┌─────────────────────────────────────────────────────────────┐
│                 LAYER 3: AGENT (The Soul)                   │
│  • Identity (Persona from docs/personas/)                   │
│  • Memory (Session State, Retry Policy, Token Management)   │
│  • Router (Reads _skill_catalog.md to select procedures)    │
└──────────────┬───────────────────────────────┬──────────────┘
               │ Loads                         │ Loads
               ▼                               ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│  LAYER 2: SKILL (The Mind)  │ │  LAYER 2: SKILL (The Mind)  │
│  "Code Review SOP"          │ │  "Testing SOP"              │
│  • Procedure (Steps)        │ │  • Procedure (Steps)        │
│  • Verification (Contract)  │ │  • Verification (Contract)  │
└──────────────┬──────────────┘ └──────────────┬──────────────┘
               │ Calls                         │ Calls
               ▼                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 LAYER 1: MCP (The Hands)                    │
│      [Git]    [Postgres]    [FileSystem]    [Linter]        │
│      (Atomic, Stateless, Logic-Free)                        │
└─────────────────────────────────────────────────────────────┘
```

### Session State (Implicit Layer)

The Agent manages a **Session State** (the context window) which determines:
- Which skills are currently loaded
- Token budget remaining
- When to "unload" a skill to make room for another

This is not a separate layer but a critical responsibility of the Agent.

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

The relationship between Skills and Agents is complementary. Additionally, **Orchestrator logic and Agent logic are mutually exclusive**. Agents should never be aware of the "plumbing" (delegation files, result formats); they simply receive context and tools.

| Aspect | Agent (`.agent.md`) | Skill (`SKILL.md`) |Orchestrator|
|--------|---------------------|---------------------|---|
| **Identity** | "Who am I?" | "How do I do X?" | "Who does what?" |
| **Scope** | Domain-level persona | Task-level procedure | Workflow management |
| **Lifecycle** | Session-persistent | Loaded on-demand | Always active |
| **Composition** | May reference multiple skills | Self-contained | Coordinates agents |
| **State** | Maintains conversation context | Stateless instructions | Manages session state |

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

### Skill Publishing: publish-skills.py

> [!NOTE]
> **Renamed from stitch-skills.py** (per Deep Think): This is a "Publisher/Adapter", not a compiler. It adapts rich source files to vendor-specific formats.

While skills are authored in `docs/skills/` (LLM-agnostic), they must be published to vendor-specific locations for proper discovery.

**Publishing Flow:**

```
docs/skills/                    ← Source of truth (LLM-agnostic)
     │
     ▼  publish-skills.py
     │
     ├── .github/skills/        ← GitHub Copilot CLI
     │   └── _skill_catalog.md  ← Discovery index
     ├── .github/skills/       ← Alternative Copilot location
     └── .cursor/skills/        ← Cursor (if needed)
```

**Publisher Responsibilities:**

1. **Scan** `docs/skills/*/SKILL.md`
2. **Validate** frontmatter (`name`, `description` required)
3. **Shadow Frontmatter** — Strip incompatible fields for Copilot
4. **Generate Skill Catalog** — `_skill_catalog.md` for agent discovery
5. **Copy** to vendor-specific output directories

---

### The Shadow Frontmatter Pattern

GitHub Copilot CLI crashes on unknown frontmatter fields. Solution: keep rich metadata in source, strip for output.

**Source (`docs/skills/code-review/SKILL.md`):**
```yaml
---
name: code-review
description: Perform structured code review
required_mcps: [filesystem, git]       # ← Rich metadata
trigger_phrases: ["review this code"]  # ← Rich metadata
tags: [quality, review]                # ← Rich metadata
---
```

**Published (`.github/skills/code-review/SKILL.md`):**
```yaml
---
name: code-review
description: Perform structured code review
---

<!-- SKILL_METADATA
required_mcps: [filesystem, git]
trigger_phrases: ["review this code"]
tags: [quality, review]
-->

## Context
...
```

The publisher:
1. Strips non-standard YAML fields
2. Injects them as an HTML comment (LLMs can still read it)
3. Copilot CLI parses cleanly

---

### Skill Catalog Artifact

Instead of runtime filesystem scanning, generate a discovery index:

**`_skill_catalog.md`:**
```markdown
# Skill Catalog

| Name | Description | Triggers |
|------|-------------|----------|
| code-review | Perform structured code review | "review this code", "code review" |
| unit-testing | Write unit tests for Swift code | "write tests", "add tests" |
| security-scan | Check for OWASP vulnerabilities | "security check", "audit" |

## Usage
To load a skill, read the corresponding `<name>/SKILL.md` file.
```

**Agent Workflow:**
1. Agent reads `_skill_catalog.md` (cheap, single file)
2. Matches user intent to skill via triggers
3. Loads only the needed `SKILL.md` (on-demand)

---

### Core Skill (Rollback Safety)

> [!IMPORTANT]
> **Context Amnesia Risk**: Without "The Law" permanently loaded, agents might forget critical rules.

Create `docs/skills/common-core/SKILL.md` containing non-negotiable rules that **every agent loads by default**:

```yaml
---
name: common-core
description: Non-negotiable rules for all agents
---

## Verification Requirements
All code changes MUST pass Tier 1 verification before output.

## Security Rules
- Never commit secrets or credentials
- Validate all user inputs
- Use parameterized queries

## Code Quality
- Code must compile without errors
- No force unwraps in production code
- Handle all error cases explicitly
```

**Agent Policy:** Always load `common-core` first, then task-specific skills.

---

### Example Publisher Implementation

```python
#!/usr/bin/env python3
# publish-skills.py

import re
from pathlib import Path
import shutil

SKILLS_SOURCE = Path("docs/skills")
VENDOR_OUTPUTS = [
    Path(".github/skills"),
    Path(".github/skills"),
]

# Fields that Copilot CLI accepts
SAFE_FRONTMATTER = {"name", "description"}

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract frontmatter and body."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return {}, content
    yaml_text = match.group(1)
    body = content[match.end():]
    
    # Simple YAML parsing
    metadata = {}
    for line in yaml_text.split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            metadata[key.strip()] = val.strip()
    return metadata, body

def shadow_frontmatter(content: str) -> str:
    """Strip unsafe fields, inject as HTML comment."""
    metadata, body = parse_frontmatter(content)
    
    # Separate safe/unsafe fields
    safe = {k: v for k, v in metadata.items() if k in SAFE_FRONTMATTER}
    unsafe = {k: v for k, v in metadata.items() if k not in SAFE_FRONTMATTER}
    
    # Rebuild frontmatter
    new_fm = "---\n"
    for k, v in safe.items():
        new_fm += f"{k}: {v}\n"
    new_fm += "---\n\n"
    
    # Inject unsafe as comment
    if unsafe:
        comment = "<!-- SKILL_METADATA\n"
        for k, v in unsafe.items():
            comment += f"{k}: {v}\n"
        comment += "-->\n\n"
        return new_fm + comment + body
    
    return new_fm + body

def generate_catalog(skills: list[dict], output_dir: Path):
    """Generate _skill_catalog.md for discovery."""
    catalog = "# Skill Catalog\n\n"
    catalog += "| Name | Description | Tags |\n"
    catalog += "|------|-------------|------|\n"
    
    for skill in skills:
        catalog += f"| {skill['name']} | {skill['description']} | {skill.get('tags', '')} |\n"
    
    (output_dir / "_skill_catalog.md").write_text(catalog)

def publish_skills():
    skills = []
    
    for skill_dir in sorted(SKILLS_SOURCE.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name == "README.md":
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        
        content = skill_file.read_text()
        metadata, _ = parse_frontmatter(content)
        skills.append(metadata)
        
        # Shadow frontmatter and publish
        published_content = shadow_frontmatter(content)
        
        for vendor_dir in VENDOR_OUTPUTS:
            target = vendor_dir / skill_dir.name
            target.mkdir(parents=True, exist_ok=True)
            (target / "SKILL.md").write_text(published_content)
        
        print(f"✓ Published: {skill_dir.name}")
    
    # Generate catalog for each vendor
    for vendor_dir in VENDOR_OUTPUTS:
        vendor_dir.mkdir(parents=True, exist_ok=True)
        generate_catalog(skills, vendor_dir)
        print(f"✓ Catalog: {vendor_dir}/_skill_catalog.md")

if __name__ == "__main__":
    publish_skills()
    print("✨ Skills published to vendor directories.")
```

**Integration with Agents:**

```bash
# Publish agents and skills
python3 docs/scripts/stitch-brain.py
python3 docs/scripts/publish-skills.py
```

Or with Makefile:

```bash
make publish  # Runs both
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
