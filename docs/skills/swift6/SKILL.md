---
name: swift6
description: Review and migrate Swift code to Swift 6 Strict Concurrency
---

# Swift 6 Strict Concurrency Migration

You are guiding a phased migration to Swift 6 strict concurrency. Follow each phase in order — commit after each phase passes verification. Never skip phases or batch unrelated changes.

## Required Tools
- `filesystem` — Read/write Swift source files
- `git` — Commit after each phase

## Required Skills
- [xcodebuild](../xcodebuild/SKILL.md) — Run Xcode commands with distilled output (never raw)

## Procedure

### 1. **Phase 0 — Zero-Risk Changes**

These changes have no cascade effect. Apply them broadly and commit.

| Pattern | Action | Example |
|---------|--------|---------|
| System framework imports | Add `@preconcurrency` | `@preconcurrency import CoreData` |
| Immutable value types | Add `Sendable` conformance | `struct Config: Sendable { let timeout: Int }` |
| Enums with no associated non-Sendable values | Add `Sendable` | `enum Mode: Sendable { case background, foreground }` |

**Commit gate:** Build succeeds, warning count decreases.

---

### 2. **Phase 1 — Leaf Node Actors**

Convert isolated classes with **few callers** to `actor`. Start at the dependency graph's leaves and work inward.

**Ideal candidates:**
- Classes protected by `NSLock`, `DispatchQueue`, or `os_unfair_lock`
- Classes with private mutable state and no `@objc` methods
- Classes not subclassing `NSObject`

```swift
// BEFORE: Manual locking
public class MetricsStore {
    private var metrics: [UUID: Metrics] = [:]
    private let lock = NSLock()
    public func record(_ id: UUID) {
        lock.lock(); defer { lock.unlock() }
        metrics[id] = Metrics(startTime: Date())
    }
}

// AFTER: Actor isolation
public actor MetricsStore {
    private var metrics: [UUID: Metrics] = [:]
    public func record(_ id: UUID) {
        metrics[id] = Metrics(startTime: Date())
    }
}
```

> **Cascade:** Every call site now requires `await`. This is why you start with leaf nodes — fewer callers = smaller cascade.

**Commit gate:** Build succeeds, all tests pass.

---

### 3. **Phase 2 — @MainActor for UI & ViewModels**

Mark ViewModel/UI classes `@MainActor`. The cascade is manageable because SwiftUI views already run on the main actor.

```swift
@MainActor
class ActionsListViewModel: ObservableObject {
    @Published var actions: [Action] = []
    @Published var isLoading = false

    func loadActions() async {
        isLoading = true
        actions = try? await store.loadAll() ?? []
        isLoading = false
    }
}
```

**Test pattern — CRITICAL:** `setUp()` and `tearDown()` of `XCTestCase` aren't main-actor-isolated. Use the `async throws` variants:

```swift
@MainActor
final class ViewModelTests: XCTestCase {
    var viewModel: MyViewModel!

    override func setUp() async throws {
        try await super.setUp()
        await MainActor.run {
            viewModel = MyViewModel()
        }
    }

    override func tearDown() async throws {
        await MainActor.run {
            viewModel = nil
        }
        try await super.tearDown()
    }
}
```

**Commit gate:** Build succeeds, updated test files pass.

---

### 4. **Phase 3 — The Tricky Bits**

These patterns require escape hatches. **Every escape hatch MUST have a justification comment.**

#### Singletons (`nonisolated(unsafe)`)

```swift
public class PersistenceController {
    // nonisolated(unsafe) justification:
    // 1. Static `let` initialization is thread-safe (dispatch_once semantics)
    // 2. NSPersistentContainer manages its own queue-based isolation
    // 3. All context operations use performAndWait/perform
    public nonisolated(unsafe) static let shared = PersistenceController()
}
```

**Checklist for each `nonisolated(unsafe)`:**
- [ ] Is the underlying type genuinely thread-safe?
- [ ] Is there a better alternative (actor, `@MainActor`)?
- [ ] Is the justification documented in a comment?

#### Non-Sendable Framework Types

Do NOT store non-`Sendable` Apple types (e.g., `EKCalendar`, `CLLocation`) in actors. Extract only the `Sendable` data you need:

```swift
// ❌ BAD: EKCalendar isn't Sendable
actor CalendarCache {
    private var cache: [String: EKCalendar] = [:]  // Error!
}

// ✅ GOOD: Extract Sendable metadata
struct CachedCalendar: Sendable {
    let identifier: String
    let title: String
}
actor CalendarCache {
    private var cache: [String: CachedCalendar] = [:]  // OK
}
```

#### @objc Methods in @MainActor Classes

Classes with `@objc` methods **cannot** be actors. Use `@MainActor` instead, and dispatch callbacks:

```swift
@MainActor
public class TaskManager: NSObject {
    @objc private func handleNotification(_ note: Notification) {
        Task { @MainActor in
            self.processNotification(note)
        }
    }
}
```

**Commit gate:** Build succeeds, all `nonisolated(unsafe)` justified.

---

### 5. **Phase 4 — Runtime Safety (Simulator Won't Catch These)**

> [!CAUTION]
> These issues compile cleanly and pass in the Simulator. They **only crash on real devices** via `dispatch_assert_queue_fail`. You MUST test on a physical device.

#### Combine Publishers in @MainActor Classes

```swift
// ❌ CRASHES on device: sink runs on background thread
NotificationCenter.default.publisher(for: .NSPersistentStoreRemoteChange)
    .sink { [weak self] note in
        Task { await self?.handle(note) }
    }

// ✅ FIX: Hop to main thread BEFORE the sink
NotificationCenter.default.publisher(for: .NSPersistentStoreRemoteChange)
    .receive(on: DispatchQueue.main)
    .sink { [weak self] note in
        Task { await self?.handle(note) }
    }
```

#### Closure Isolation Inheritance

Closures inherit the actor isolation of their defining context. If a `@MainActor` method defines a closure that a framework calls from a background thread, Swift 6 crashes **before any code in the closure runs**.

`Task { @MainActor in }` inside the closure does NOT help.

**The fix — define closures in `nonisolated` static methods:**

```swift
@MainActor
public class BackgroundTaskManager {
    func registerTasks() {
        // Delegate to nonisolated context
        Self.performRegistration(queue: backgroundQueue, id: Self.taskId)
    }

    // Closure defined HERE is nonisolated — no actor inheritance
    nonisolated static func performRegistration(queue: DispatchQueue, id: String) {
        BGTaskScheduler.shared.register(
            forTaskWithIdentifier: id,
            using: queue
        ) { task in
            // Safe — this closure is nonisolated
            Task { @MainActor in
                shared.handleTask(task)
            }
        }
    }
}
```

Same pattern applies to `task.expirationHandler`.

#### Gotchas Grep Checklist

After enabling Swift 6, grep for these patterns in `@MainActor` classes:

| Pattern | Risk | Fix |
|---------|------|-----|
| `.sink {` | Runs on publisher's thread | Add `.receive(on: DispatchQueue.main)` |
| `@objc func` that mutates state | May be called from background | Dispatch via `Task { @MainActor in }` |
| `BGTaskScheduler.shared.register` | Callback on background queue | Move closure to `nonisolated static` method |
| `task.expirationHandler = {` | Runs on background thread | Move closure to `nonisolated static` method |
| Any callback-based API | Unknown thread | Verify delivery thread in documentation |

#### Safe Patterns (No Fix Needed)

These are safe in `@MainActor` classes because they guarantee main-thread delivery:
- `Timer.scheduledTimer` / `Timer.publish(on: .main)`
- `NotificationCenter.addObserver(queue: .main)`
- `DispatchQueue.main.asyncAfter`
- SwiftUI `@Published` property observation

**Commit gate:** Zero crashes on real device. Run verification workflow.

---

### 6. **Phase 5 — Enable Swift 6 Language Mode**

```
SWIFT_VERSION = 6.0;
```

This also enables `Strict Concurrency Checking: Complete`. Expect a small number of new warnings (typically in test code). Fix and commit.

## Output Format

After each phase, report:

```markdown
## Phase N Complete
- **Files changed:** X
- **Patterns applied:** [list]
- **Warnings remaining:** N (was M)
- **Tests:** X/Y passing
- **Escape hatches added:** N (all justified: yes/no)
```

## Constraints

- **One phase per commit.** Do not batch phases.
- **Every `nonisolated(unsafe)` must have a justification comment.** No exceptions.
- **Never use `@unchecked Sendable`** unless the type is genuinely thread-safe AND has no Sendable alternative. Prefer `nonisolated(unsafe)` for singletons.
- **Third-party frameworks:** Use `@preconcurrency import`. If a type isn't `Sendable`, work around it (extract data, don't store the type).
- **Test code gets the same care as production code.** Concurrency bugs in tests are still bugs.

## Verification (The Loop)

Follow [swift6-verify](../../workflows/swift6-verify.md) after each phase:

1. **Tier 1:** `swift build` / `xcodebuild build` — zero errors
2. **Tier 2:** Run targeted tests with TSan (`docs/scripts/tsan-sanitizer.py`)
3. **Tier 3:** Full test suite with TSan — zero warnings
4. **Tier 4:** Deploy to real device — test Background Refresh, Notifications, CloudKit
5. **Fail?** → Fix and repeat from Tier 1
6. **Pass?** → Commit and proceed to next phase
