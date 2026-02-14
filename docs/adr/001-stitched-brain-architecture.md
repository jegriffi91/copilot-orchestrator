# ADR-001: Stitched Brain Architecture for LLM-Agnostic Agent Generation

**Status:** Accepted  
**Date:** 2026-02-02  
**Deciders:** Engineering Team  
**Tags:** architecture, agents, llm, copilot

---

## Context

Our enterprise iOS application currently uses GitHub Copilot CLI with some Cursor usage. As the codebase scales and AI tooling evolves, we face several challenges:

1. **Knowledge Fragmentation** — Coding standards, domain expertise, and verification procedures are scattered or implicit
2. **Agent Inconsistency** — Ad-hoc prompting leads to inconsistent agent behavior
3. **Vendor Lock-in** — Coupling to specific LLM providers limits flexibility
4. **Context Overload** — Generic agents lack focused domain knowledge

We need a structured approach to encode organizational knowledge into reusable, composable building blocks that can generate specialized agents for any LLM target.

---

## Decision

Implement a **"Stitched Brain" Architecture** that separates concerns into three composable layers:

### 1. Personas (Voice Layer)
- Define agent personality, tone, mental models
- Specify rejection criteria ("sins" the agent refuses)
- Stored in `docs/personas/*.md`

### 2. Standards (Knowledge Layer)
- Technical rules encoded as tagged markdown with `stitcher_rules` frontmatter
- Organized by domain: `common/`, `testing/`, `design/`, `sdui/`
- Filterable by tags for role-specific compilation
- Stored in `docs/standards/**/*.md`

### 3. Workflows (Verification Layer)
- CI commands, verification procedures, troubleshooting guides
- Linked via `related_verification` frontmatter field
- Injected into agent's "Loop" section
- Stored in `docs/workflows/*.md`

### Compilation via Recipes
A Python script (`stitch-brain.py`) compiles these layers:

```python
AGENT_RECIPES = {
    "testing.agent.md": {
        "persona": "qa-kien.md",
        "sources": ["testing", "workflows"],
        "allowed_tags": ["testing", "common", "ci"],
        "description": "Unit Testing Specialist"
    }
}
```

### Output Structure
Generated agents contain two primary sections:
- **THE LAW** — Immutable rules from `stitcher_rules` (RULE type)
- **THE LOOP** — Verification steps (STEP, CMD, BENEFIT types) + detailed workflows

---

## Alternatives Considered

### 1. Single Monolithic Prompt File
**Rejected:** Doesn't scale. Mixing personas with technical rules creates maintenance burden. Can't share rules across agents.

### 2. Runtime MCP Tool Injection
**Partially Adopted:** The MCP orchestrator handles multi-agent delegation, but agent identity still needs static compilation for consistency.

### 3. LLM-Native Memory Features
**Rejected:** Vendor-specific (Copilot memory, Claude projects). Doesn't provide version control or reproducibility.

### 4. External RAG System
**Deferred:** The iOS GraphRAG engine handles codebase knowledge, but agent identity/rules are orthogonal and benefit from static compilation.

---

## Consequences

### Positive
- ✅ **Separation of Concerns** — Personas, standards, workflows evolve independently
- ✅ **Composability** — Same standard can be used by multiple agents via tagging
- ✅ **LLM Portability** — Change output template, target any LLM
- ✅ **Version Control** — All agent knowledge is code-reviewable
- ✅ **Reduced Hallucination** — Explicit verification workflows reduce improvisation

### Negative
- ⚠️ **Compilation Step** — Agents must be regenerated after changes
- ⚠️ **Frontmatter Complexity** — `stitcher_rules` format has learning curve
- ⚠️ **Tag Discipline** — Incorrect tagging leads to missing/extra rules

### Mitigations
- Add pre-commit hook to regenerate agents
- Document `stitcher_rules` schema with examples
- Add script validation for tag consistency

---

## Implementation Notes

### Stitcher Rule Schema

```
RULE: <name> | ACTION: <what to do> | SEVERITY: <CRITICAL|WARN>
STEP: <name> | CMD: <command> | SEVERITY: <WARN>
CMD: <description> | ACTION: <command> | SEVERITY: <WARN>
BENEFIT: <name> | ACTION: <benefit text> | SEVERITY: <WARN>
```

- `RULE` → Goes to THE LAW (constraints during development)
- `STEP`, `CMD`, `BENEFIT` → Go to THE LOOP (verification process)

### File Linking

Standards can reference verification workflows:

```yaml
---
related_verification: verify_tests.md
---
```

The stitcher resolves these links and injects workflow content.

---

## Related Documents

- [README.md](../README.md) — Project overview
- [Personas README](personas/README.md) — Creating agent personalities
- GitHub Copilot CLI Workflows KI — Implementation patterns

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-02 | Team | Initial decision |
