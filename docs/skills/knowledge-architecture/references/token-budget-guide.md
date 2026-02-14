# Token Budget Guide

## Budget Allocation

The total instruction budget per agent session is **~6,000 tokens**, leaving ample room for user code and conversation in the context window.

| Tier | Budget | Contents |
|------|--------|----------|
| T1 (Constitution) | <1,000 tokens | THE LAW — ~15 universal rules |
| T2 (Playbook) | ~2,500 tokens | One SKILL.md loaded per task |
| T3 (Encyclopedia) | ~2,500 tokens | ~2 reference files per session |
| **Total** | **~6,000 tokens** | Agent identity + loaded knowledge |

## Measurement

### Counting Tokens
Approximate: **1 token ≈ 4 characters** (English text with code).

Quick checks:
- 15 rules × ~60 chars each = ~900 chars ≈ 225 tokens ✅ (well under T1 cap)
- A SKILL.md with 3,000 chars ≈ 750 tokens ✅ (under T2 budget)
- A reference with 2,000 lines of code may exceed budget ❌

### Measuring Files
```bash
# Rough token estimate (chars / 4)
wc -c docs/skills/swiftui/SKILL.md | awk '{print $1/4, "estimated tokens"}'

# Word count (tokens ≈ words × 1.3 for code-heavy content)
wc -w docs/skills/swiftui/SKILL.md
```

## Budget Enforcement (Current)

Currently enforced by authoring discipline:

1. **Write concisely** — Bullet points, not paragraphs
2. **Use imperative triggers** — Load T3 on-demand, not upfront
3. **Split large references** — Break into focused files (e.g., animation-basics vs animation-advanced)
4. **Remove redundancy** — If it's in a reference, don't repeat in SKILL.md

## Budget Enforcement (Planned)

`publish.py` will add automated checks:
- Fail if THE LAW section exceeds 1,000 tokens
- Warn if SKILL.md exceeds 3,000 tokens
- Warn if any reference exceeds 2,000 tokens

## Staying Under Budget

### SKILL.md Strategies
- Guidelines as single-line bullets, not multi-line explanations
- Review checklists as checkboxes, not prose
- Imperative triggers instead of inlined reference content
- Quick reference tables (compact, scannable)

### Reference File Strategies
- One topic per file (state-management, not state-management-and-bindings)
- Code examples: show ✅/❌ pairs, not exhaustive variations
- Summary checklist at the end, not after every section
- Link to Apple docs for deep dives instead of reproducing them

### When You're Over Budget
1. **Split:** Break the file into focused sub-files
2. **Promote:** Move the most critical rule up one tier (T3 → T2 bullet)
3. **Defer:** Move rarely-needed content to a separate reference
4. **Prune:** Remove content the AI already handles correctly without prompting
