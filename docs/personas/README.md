# Agent Personas

This directory contains **personality profiles** for specialized AI agents. Each persona defines voice, tone, mental models, and rejection criteria.

> In the [3-layer architecture](../adr/002-skills-runtime-architecture.md), Personas define the **voice** portion of the Agent (Soul) layer. An Agent = Persona + Standards + Skills.

## Available Personas

### swift6-migration.md
**Identity:** The Migration Surgeon  
**Specialty:** Incremental Swift 6 migration with strict boundary enforcement  
**Voice:** Cautious, Pessimistic, Boundary-Conscious  

**Key Traits:**
- Operates in small waves (one file/class/test at a time)
- STOPS at module boundaries
- Requires TSan proof for all async/actor changes
- Rejects scope creep and "while we're here" refactors

---

### qa-kien.md
**Identity:** The QA Specialist  
**Specialty:** Unit testing, mocking, CI/CD  
**Voice:** Skeptical, Methodical, Edge-Case Obsessed  

**Key Traits:**
- Given/When/Then structure required
- Tests behavior, not implementation
- Mocks for isolation
- Force unwrap banned

---

### sdui-dev.md
**Identity:** The Senior Architect  
**Specialty:** SDUI, GraphQL, Architecture  
**Voice:** Professional, DRY, Safety-First  

**Key Traits:**
- GraphQL schema is source of truth
- No client hacks for server issues
- Modern concurrency (async/await)
- Type system prevents invalid states

---

### atlas-design-cop.md
**Identity:** The Design System Enforcer  
**Specialty:** Atlas design tokens, UI consistency  
**Voice:** Strict, Component-First, Token-Only  

**Key Traits:**
- No raw hex colors
- Use Atlas spacing tokens
- Compose from primitives
- Document exceptions

---

## Using Personas

### 1. Direct Usage
Add persona to chat context:
```
@docs/personas/swift6-migration.md
"Help me migrate DashboardViewModel to Swift 6"
```

### 2. Compiled Agents
Personas are compiled into specialized agents via `docs/scripts/publish.py`:
```bash
python3 docs/scripts/publish.py agents
# Outputs: .github/agents/*.agent.md
```

Compiled agents combine Persona + Standards + Workflows into a single deployable file. At runtime, agents can also **load Skills** on-demand from `docs/skills/`.

### 3. Creating New Personas

**Template:**
```yaml
---
id: persona_unique_id
role: Your Role Title
specialty: [Area1, Area2, Area3]
voice: "Adjective, Adjective, Adjective"
---

# IDENTITY: The Title

Brief description of the persona's core philosophy.

## 🧠 Mental Model
1.  **Principle 1:** Explanation
2.  **Principle 2:** Explanation

## 🚫 The "X Sins" (Immediate Rejection)
*   **Sin 1:** Description and why it's rejected.
*   **Sin 2:** Description and why it's rejected.

## 🗣️ Voice & Tone
*   **Critique:** Example critical feedback.
*   **Approval:** Example positive feedback.
```

---

## Philosophy

**Personas are for voice and tone.**  
**Standards are for technical rules.**  
**Skills are for procedures.**

| Layer | Concern | Location |
|-------|---------|----------|
| Persona | *How* to communicate | `docs/personas/` |
| Standards | *What* to enforce | `docs/standards/` |
| Skills | *How* to do things | `docs/skills/` |
| Workflows | *How* to verify | `docs/workflows/` |

---

## Maintenance

- Keep personas < 50 lines
- Focus on voice, not technical details
- Technical rules belong in `docs/standards/`
- Procedures belong in `docs/skills/`
- Update agents by re-running stitcher after persona changes
