---
id: swift_concurrency
type: practice
tags: [common, swift6]
stitcher_rules:
  - "RULE: MainActor UI | ACTION: All UI updates must be on @MainActor | SEVERITY: CRITICAL"
  - "RULE: Sendable Types | ACTION: Data crossing isolation boundaries must conform to Sendable | SEVERITY: CRITICAL"
  - "RULE: No Bare Task | ACTION: Use structured concurrency or actor isolation, not bare Task {} | SEVERITY: WARN"
  - "RULE: Async Preference | ACTION: Use async/await over completion handlers for new code | SEVERITY: WARN"
  - "RULE: Actor Reentrancy | ACTION: Never assume actor state unchanged across await suspension points | SEVERITY: CRITICAL"
  - "STEP: Concurrency Check | CMD: Build with SWIFT_STRICT_CONCURRENCY=complete to surface issues | SEVERITY: CRITICAL"
related_verification: docs/workflows/swift6-verify.md
---

# Swift Concurrency Standards

## Overview

Rules for safe, correct Swift concurrency. These align with Swift 6 strict concurrency checking and apply to all agents writing async code.

## Rule 1: MainActor UI

**Rationale:** SwiftUI views and UIKit components are MainActor-isolated. Off-main-thread UI updates cause data races and undefined behavior.

```swift
// ❌ Bad — property update may be off MainActor
class ViewModel {
    var items: [Item] = []
    func load() async {
        items = try await api.fetch()  // ⚠️ May not be on MainActor
    }
}

// ✅ Good
@MainActor
@Observable
class ViewModel {
    var items: [Item] = []
    func load() async {
        items = try await api.fetch()  // ✅ Guaranteed MainActor
    }
}
```

## Rule 2: Sendable Types

**Rationale:** Non-Sendable types crossing actor boundaries create data races. The compiler will enforce this in Swift 6.

```swift
// ❌ Bad — mutable class crossing isolation
class Settings { var theme: Theme = .light }
actor DataStore {
    func apply(_ settings: Settings) { ... }  // ⚠️ Settings is not Sendable
}

// ✅ Good
struct Settings: Sendable { let theme: Theme }
```

## Rule 3: Actor Reentrancy

**Rationale:** After any `await`, the actor may have processed other messages. Never assume state is unchanged.

```swift
// ❌ Bad — state may have changed after await
actor Cache {
    var data: [String: Data] = [:]
    func loadIfNeeded(key: String) async throws {
        if data[key] == nil {
            let result = try await fetch(key)
            data[key] = result  // ⚠️ Another caller may have loaded it
        }
    }
}

// ✅ Good — re-check after await
actor Cache {
    var data: [String: Data] = [:]
    func loadIfNeeded(key: String) async throws {
        if data[key] == nil {
            let result = try await fetch(key)
            if data[key] == nil {  // Re-check after suspension
                data[key] = result
            }
        }
    }
}
```
