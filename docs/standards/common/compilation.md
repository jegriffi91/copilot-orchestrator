---
id: compilation_standards
type: process
tags: [common, ci]
stitcher_rules:
  - "RULE: Zero Warnings | ACTION: Treat all new compiler warnings as errors | SEVERITY: CRITICAL"
  - "RULE: No #if DEBUG Guards on Logic | ACTION: Debug-only code must be limited to logging, not logic branches | SEVERITY: WARN"
  - "STEP: Compile Check | CMD: xcodebuild build -quiet 2>&1 | tail -20 | SEVERITY: CRITICAL"
  - "STEP: Clean Build Verification | CMD: xcodebuild clean build -quiet for cross-module changes | SEVERITY: WARN"
---

# Compilation Standards

## Overview

Every code change must compile without errors or new warnings. This is the minimum bar — no agent should ever return code that doesn't build.

## Rule 1: Zero Warnings

**Rationale:** Warnings accumulate into a wall of noise that hides real issues. New code must not introduce warnings.

## Rule 2: Compile Check (Tier 1)

**Rationale:** A quick incremental build catches syntax errors, type mismatches, and missing imports in under 30 seconds. Always run this before presenting code to the user.

```bash
# Quick incremental build — most changes
xcodebuild build -quiet 2>&1 | tail -20

# Clean build — after cross-module changes
xcodebuild clean build -quiet 2>&1 | tail -20
```
