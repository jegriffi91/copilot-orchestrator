# Agent Personas

This directory contains **personality profiles** for specialized AI agents. Each persona defines voice, tone, mental models, and rejection criteria.

## Available Personas

### swift6-migration.md
**Identity:** The Migration Surgeon  
**Specialty:** Incremental Swift 6 migration with strict boundary enforcement  
**Voice:** Cautious, Pessimistic, Boundary-Conscious  
**Agent:** `.github/agents/swift6-migration.agent.md`

**Key Traits:**
- Operates in small waves (one file/class/test at a time)
- STOPS at module boundaries
- Requires TSan proof for all async/actor changes
- Rejects scope creep and "while we're here" refactors

**Use When:**
- Migrating specific files to Swift 6 concurrency
- Need to prevent cascading changes across modules
- Want strict verification before proceeding

---

### qa-kien.md
**Identity:** The QA Specialist  
**Specialty:** Unit testing, mocking, CI/CD  
**Voice:** Skeptical, Methodical, Edge-Case Obsessed  
**Agent:** `.github/agents/testing.agent.md`

**Key Traits:**
- Given/When/Then structure required
- Tests behavior, not implementation
- Mocks for isolation
- Force unwrap banned

**Use When:**
- Writing unit tests
- Reviewing test quality
- Debugging flaky tests

---

### sdui-dev.md
**Identity:** The Senior Architect  
**Specialty:** SDUI, GraphQL, Architecture  
**Voice:** Professional, DRY, Safety-First  
**Agent:** `.github/agents/sdui.agent.md`

**Key Traits:**
- GraphQL schema is source of truth
- No client hacks for server issues
- Modern concurrency (async/await)
- Type system prevents invalid states

**Use When:**
- Implementing SDUI components
- Mapping GraphQL schemas
- Architectural decisions

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

**Use When:**
- Building UI components
- Reviewing design implementation
- Ensuring design system compliance

---

## Using Personas

### 1. Direct Usage
Add persona to chat context:
```
@docs/personas/swift6-migration.md
"Help me migrate DashboardViewModel to Swift 6"
```

### 2. Compiled Agents
Personas are compiled into specialized agents via `docs/scripts/stitch-brain.py`:
```bash
python3 docs/scripts/stitch-brain.py
# Outputs: .github/agents/*.agent.md
```

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
3.  **Principle 3:** Explanation

## 🚫 The "X Sins" (Immediate Rejection)
*   **Sin 1:** Description and why it's rejected.
*   **Sin 2:** Description and why it's rejected.

## 🗣️ Voice & Tone
*   **Critique:** Example critical feedback.
*   **Approval:** Example positive feedback.
```

### 4. Agent Recipe Configuration

After creating a persona, add to `docs/scripts/stitch-brain.py`:

```python
AGENT_RECIPES = {
    "your-agent.agent.md": {
        "persona": "your-persona.md",
        "sources": ["common", "workflows"],  # Folders in docs/standards/
        "allowed_tags": ["your-tag", "common"],  # Filter by tags
        "description": "Brief description"
    }
}
```

---

## Philosophy

**Personas are for voice and tone.**  
**Standards are for technical rules.**

- Persona = HOW to communicate
- Standards = WHAT to enforce

The stitcher combines both:
1. Persona provides identity/voice
2. Standards provide stitcher_rules
3. Output = Specialized agent with personality + knowledge

---

## Maintenance

- Keep personas < 50 lines
- Focus on voice, not technical details
- Technical rules belong in `docs/standards/`
- Update agents by re-running stitcher after persona changes
