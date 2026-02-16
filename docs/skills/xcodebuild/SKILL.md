---
name: xcodebuild
description: Run Xcode build and test commands with distilled, token-efficient output
---

# Xcodebuild Distillation Skill

You are running Xcode commands (build, test, TSan) in a way that prevents context window pollution. **Never** capture raw `xcodebuild` output — always route through the distillation pipeline.

## Required Tools
- `terminal` — Run shell commands
- `filesystem` — Read/write source files

## Required Scripts
- [`xcode-distill.py`](../../scripts/xcode-distill.py) — Distillation pipeline (must be in `docs/scripts/`)

## Procedure

### 1. **Discover the Workspace**

Before building or testing, understand the project's scheme/target topology:

```bash
python3 docs/scripts/xcode-distill.py discover --workspace <path>.xcworkspace
```

This outputs a compact manifest of schemes and test targets. Use it to scope all subsequent commands to the **narrowest scheme** that covers the changed files.

> [!CAUTION]
> If you do not know which scheme or target to use, you **MUST** run `discover` first. Never guess.

---

### 2. **Compile Check (Distilled)**

Pipe `xcodebuild` output through the `compile` subcommand:

```bash
xcodebuild build \
  -workspace <workspace> \
  -scheme <SCHEME> \
  -destination 'generic/platform=iOS Simulator' \
  2>&1 | python3 docs/scripts/xcode-distill.py compile --scheme <SCHEME>
```

Output is capped at 20 issues (errors grouped by file, warnings condensed).

---

### 3. **Test Failures from xcresult**

After a test run, extract failures from the `.xcresult` bundle:

```bash
python3 docs/scripts/xcode-distill.py test --path ./Build/Results.xcresult
```

---

### 4. **TSan (Thread Sanitizer)**

Run targeted TSan analysis with distilled output:

```bash
python3 docs/scripts/xcode-distill.py tsan \
  --scheme <SCHEME> \
  --target <TestTarget> \
  --device "iPhone 16 Pro"
```

Narrow further with `--test-class`:
```bash
python3 docs/scripts/xcode-distill.py tsan \
  --scheme <SCHEME> \
  --target <TestTarget> \
  --test-class <TestClassName>
```

---

### 5. **Circuit Breaker Protocol**

Track remediation attempts using `--attempt N`:

```bash
xcodebuild build ... 2>&1 | python3 docs/scripts/xcode-distill.py compile --attempt 2
```

| Attempt | Action |
|---------|--------|
| 1–2 | Fix errors and retry |
| 3+ | **STOP.** Revert changes, open Draft PR, tag `#requires-human-architect` |

When the circuit breaker fires (attempt ≥ 3), the script appends explicit revert instructions. **Follow them unconditionally.**

## Multi-Module Workspaces

In workspaces with multiple schemes and targets:

1. Run `discover` first to map the workspace topology
2. Scope builds to the **narrowest scheme** covering your changes
3. Use `--target` to test only the module(s) you touched
4. The `discover` output maps test targets → source modules — use it
5. Never build the full workspace when a scoped scheme exists

## Output Format

All distilled output follows this contract:

- **File paths** are project-relative (never absolute)
- **Errors** grouped by file with line numbers
- **Warnings** condensed to top 5
- **Test failures** grouped by class with assertion messages
- **TSan issues** deduplicated with top 3 app-level stack frames
- **Maximum** 20 items per report (override with `--max-issues`)

## Constraints

- **NEVER** run `xcodebuild` without piping through `xcode-distill.py`
- **NEVER** read `.xcresult` bundles directly — use the `test` subcommand
- **NEVER** exceed 3 remediation attempts on the same file
- **NEVER** paste raw xcodebuild logs into the conversation 
- **ALWAYS** use `--json` when output feeds into another script
- **ALWAYS** include `--attempt N` when retrying a fix

## Examples

**Input:** "Build the ECW scheme and tell me what's broken"
**Action:** 
```bash
xcodebuild build -workspace CreditWorks.xcworkspace -scheme ECW -destination 'generic/platform=iOS Simulator' 2>&1 | python3 docs/scripts/xcode-distill.py compile --scheme ECW
```

**Input:** "Run TSan on the SessionManager tests"
**Action:**
```bash
python3 docs/scripts/xcode-distill.py tsan --scheme ECW --target CMSCoreUnitTests --test-class SessionManagerTests
```

## Verification

This skill does not modify code directly. It provides distilled diagnostics to other skills (e.g., [swift6](../swift6/SKILL.md)) for action.
