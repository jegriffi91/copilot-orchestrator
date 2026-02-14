# Workflows Directory

This directory contains **verification procedures** for AI agents.

## Philosophy

Workflows answer: **"How do I verify my work?"**

> In the [3-layer architecture](../adr/002-skills-runtime-architecture.md), Workflows implement the **verification loop**. Skills declare *what to verify*, and Workflows define *how to verify it*.

### Where Workflows Fit

| Component | Declares | Executes |
|-----------|----------|----------|
| **Skill** | Verification *requirements* ("run `swift build`") | — |
| **Workflow** | Verification *procedure* (step-by-step instructions) | — |
| **Agent** | — | Verification *loop* (retries, escalation) |

## Tiered Verification

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

## Creating a Workflow

```markdown
# Workflow: Verify <Domain>

## Tier 1 — Compile Check
- Run: `swift build` or `xcodebuild ... build`
- Fail? → Fix compilation errors, repeat

## Tier 2 — Targeted Tests
- Run: `swift test --filter <ChangedModule>`
- Fail? → Fix test failures, repeat

## Completion Criteria
- [ ] Code compiles without errors
- [ ] Targeted tests pass
- [ ] No new warnings introduced
```

## Output Sanitization

Tool outputs (xcodebuild, TSan, etc.) should be sanitized to maximize signal:

| Before | After |
|--------|-------|
| 500-line xcodebuild log | "✅ Build succeeded" or "❌ 3 errors in AuthService.swift" |
| Raw TSan dump | Grouped issues with fix suggestions |

Use sanitization scripts (e.g., `docs/scripts/tsan-sanitizer.py`) to convert verbose output into actionable summaries.

## Related

- [Skills README](../skills/README.md) — Skills declare verification requirements
- [Standards README](../standards/README.md) — Standards define immutable rules
- [ADR-002](../adr/002-skills-runtime-architecture.md) — Full architecture reference
