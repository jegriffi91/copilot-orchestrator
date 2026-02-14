---
id: swift_fundamentals
type: practice
tags: [common]
stitcher_rules:
  - "RULE: No Force Unwrap | ACTION: Use guard let or if let, never force unwrap | SEVERITY: CRITICAL"
  - "RULE: Error Propagation | ACTION: Throw typed errors, never return optionals for failable operations | SEVERITY: WARN"
  - "RULE: Access Control | ACTION: Default to private, expose only what callers need | SEVERITY: WARN"
  - "RULE: No Implicitly Unwrapped Optionals | ACTION: Use lazy or computed properties instead of IUOs | SEVERITY: CRITICAL"
  - "RULE: Prefer Value Types | ACTION: Use structs over classes unless reference semantics required | SEVERITY: WARN"
  - "RULE: Protocol-Oriented Design | ACTION: Define capabilities as protocols, not base classes | SEVERITY: WARN"
---

# Swift Fundamentals

## Overview

Core rules for Swift code quality. These apply to **all** agents and cover safety, clarity, and idiomatic style.

## Rule 1: No Force Unwrap

**Rationale:** Force unwrapping (`!`) causes runtime crashes when the value is nil. Every `!` is a latent production incident.

```swift
// ❌ Bad
let value = dict["key"]!
let image = UIImage(named: "icon")!

// ✅ Good
guard let value = dict["key"] else { return }
let image = UIImage(named: "icon") ?? UIImage()
```

## Rule 2: Error Propagation

**Rationale:** Returning `nil` on failure hides the reason for failure. Typed errors make failures debuggable.

```swift
// ❌ Bad — caller can't know WHY it failed
func fetchUser(id: String) -> User? { ... }

// ✅ Good — caller knows exactly what went wrong
func fetchUser(id: String) throws(FetchError) -> User { ... }
```

## Rule 3: Access Control

**Rationale:** `private` by default communicates intent and prevents accidental coupling.

```swift
// ❌ Bad — everything is implicitly internal
class UserService {
    var cache: [String: User] = [:]
    func invalidate() { ... }
}

// ✅ Good — only the API surface is exposed
class UserService {
    private var cache: [String: User] = [:]
    func fetch(id: String) async throws -> User { ... }
}
```

## Rule 4: Prefer Value Types

**Rationale:** Structs avoid shared mutable state issues and are cheaper to reason about.

```swift
// ❌ Bad — class with no need for reference semantics
class UserSettings {
    var theme: Theme
    var language: String
}

// ✅ Good
struct UserSettings {
    var theme: Theme
    var language: String
}
```
