# Tier Placement Rubric

## Decision Framework

Use this rubric to determine where new knowledge should live in the 3-tier hierarchy.

## Step 1: The Linter Test

**Can a deterministic tool catch this?**

| If... | Then... |
|-------|---------|
| A linter rule can enforce it | Add linter rule, not AI context |
| A compiler flag can catch it | Enable the flag, not AI context |
| A code review automation exists | Use that, not AI context |

**Principle:** Don't spend token budget on things tools can catch deterministically.

## Step 2: The Tier Decision

```
Is this a universal, zero-exception rule?
├─ YES: Could it prevent catastrophic failure?
│       ├─ YES → TIER 1 (Constitution)
│       └─ NO: Is it truly universal across ALL agents?
│               ├─ YES → TIER 1
│               └─ NO → TIER 2 (domain-specific)
│
└─ NO: Does it require code examples or flowcharts?
        ├─ YES → TIER 3 (Reference)
        └─ NO: Is it a procedure, heuristic, or API guide?
                ├─ YES → TIER 2 (Skill)
                └─ NO → Reconsider if it needs AI context at all
```

## Tier 1 Criteria (Constitution)

**Add to `docs/standards/` ONLY if ALL of these are true:**
- [ ] Zero exceptions across the entire codebase
- [ ] Violating it causes catastrophic failure (crash, data loss, security breach)
- [ ] It's framework-agnostic (applies to SwiftUI, UIKit, backend, etc.)
- [ ] It can be stated in one sentence
- [ ] Adding it keeps THE LAW under 15 rules total

**Examples:**
- ✅ "All UI updates must be on @MainActor"
- ✅ "No force unwraps in production code"
- ❌ "Prefer @Observable over ObservableObject" (framework-specific → Tier 2)
- ❌ "Use foregroundStyle() instead of foregroundColor()" (API preference → Tier 3)

## Tier 2 Criteria (Playbook)

**Add to a SKILL.md if:**
- [ ] It's a domain-specific procedure or heuristic
- [ ] It has some exceptions or conditions
- [ ] It guides behavior but doesn't need code examples to understand
- [ ] It fits the skill's domain

**Examples:**
- ✅ Migration steps for Swift 6
- ✅ "Always prefer @Observable over ObservableObject for new code"
- ✅ Review checklists

## Tier 3 Criteria (Encyclopedia)

**Add to `references/*.md` if:**
- [ ] It needs code examples (good vs. bad patterns)
- [ ] It's a decision flowchart or lookup table
- [ ] It covers edge cases or exceptions
- [ ] It would bloat the SKILL.md beyond ~3,000 tokens

**Examples:**
- ✅ Property wrapper selection guide with code for each option
- ✅ Modern API replacement table with before/after code
- ✅ Animation patterns with detailed examples

## Anti-Patterns

### Don't Duplicate
If knowledge exists in a reference file, don't repeat it in the SKILL.md. Use an imperative trigger instead:

```markdown
# Bad - duplicates reference content
### State Management
Use @State for private state, @Binding for modifications...
[100 lines of examples]

# Good - triggers reference loading
### State Management
**ACTION REQUIRED:** Read `references/state-management.md` BEFORE evaluating property wrappers.
- [ ] Using @Observable instead of ObservableObject for new code
- [ ] @State and @StateObject are private
```

### Don't Over-Tier
Not everything needs to be in the AI's context. Ask:
- Can a developer learn this from autocomplete? → Skip
- Is this in Apple's documentation? → Only add if frequently misused
- Does the AI consistently get this wrong? → Add to appropriate tier
