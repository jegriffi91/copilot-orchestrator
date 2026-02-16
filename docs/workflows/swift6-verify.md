# Workflow: Verify Swift 6 Migration

Verification procedure for Swift 6 strict concurrency changes. Referenced by the [swift6 skill](../skills/swift6/SKILL.md). All commands use [xcode-distill.py](../scripts/xcode-distill.py) to keep output token-efficient — see the [xcodebuild skill](../skills/xcodebuild/SKILL.md).

## Tier 0 — Diff Lint (Concurrency Guardrails)

Before compiling, lint the diff for forbidden concurrency patterns:

```bash
python3 docs/scripts/xcode-distill.py lint-diff
```

Or from a specific diff file:
```bash
git diff HEAD~1 | python3 docs/scripts/xcode-distill.py lint-diff
```

- **Pass:** Zero errors, warnings reviewed
- **Fail?** → Remove forbidden patterns (`@unchecked Sendable`, `.assumeIsolated`, `DispatchSemaphore`, `Task.detached`). Add justification comments for `nonisolated(unsafe)`. If blast radius exceeded, revert and contain scope.

> [!CAUTION]
> If Tier 0 fails, do NOT proceed to Tier 1. Fix the violations first.

## Tier 1 — Compile Check (Distilled)

> [!IMPORTANT]
> Ensure your project has `SWIFT_STRICT_CONCURRENCY = complete` in build settings. The agent must never weaken this flag.

```bash
xcodebuild build \
  -workspace <WORKSPACE> \
  -scheme <SCHEME> \
  -destination 'generic/platform=iOS Simulator' \
  2>&1 | python3 docs/scripts/xcode-distill.py compile --scheme <SCHEME> --attempt <N>
```

- **Pass:** Zero errors, warning count ≤ previous phase
- **Fail?** → Fix compilation errors, increment `--attempt`, repeat

## Tier 2 — Targeted Tests with TSan (Distilled)

Run only the test targets affected by changes. Tests run with **TSan**, **Thread Performance Checker**, and a **30-second timeout** per test (catches hung continuations and deadlocks):

```bash
python3 docs/scripts/xcode-distill.py tsan \
  --scheme <SCHEME> \
  --target <ChangedTestTarget> \
  --device "iPhone 16 Pro" \
  --attempt <N>
```

- **Pass:** All tests pass, zero TSan warnings, zero timeouts
- **Fail?** → Fix data races, increment `--attempt`, repeat from Tier 1
- **Timeout?** → Audit `withCheckedContinuation` for missing `.resume()`, check for `DispatchSemaphore` deadlocks

> [!TIP]
> Use `--test-class` to narrow further: `--test-class MyViewModelTests`

## Tier 3 — Full Test Suite with TSan (Distilled)

```bash
python3 docs/scripts/xcode-distill.py tsan \
  --scheme <SCHEME> \
  --device "iPhone 16 Pro"
```

- **Pass:** All tests pass, zero TSan warnings, zero timeouts
- **Fail?** → Fix regressions, repeat from Tier 1

> [!WARNING]
> If `--attempt` reaches 3, the script triggers the **circuit breaker**. Follow the revert instructions unconditionally.

## Tier 4 — Real Device Deployment

> [!CAUTION]
> **This tier cannot be done in the Simulator.** The following features only crash on real devices due to Objective-C framework boundary crossings that Swift 6 cannot check statically.

Deploy to a physical device and exercise:

| Feature | Why It's Risky |
|---------|----------------|
| Background App Refresh | `BGTaskScheduler` callbacks run on background queue |
| Push Notifications | `UNUserNotificationCenter` delegates may fire off-main |
| CloudKit / CoreData sync | `.NSPersistentStoreRemoteChange` fires on background thread |
| NotificationCenter observers | Combine `.sink` may run on publisher's thread |

**What to look for:** Crashes with `dispatch_assert_queue_fail` in the crash log — this is Swift 6's runtime actor isolation check failing.

- **Pass:** App runs stably through all features without crashes
- **Fail?** → Check crash logs for `dispatch_assert_queue_fail`, apply nonisolated static method pattern, repeat from Tier 1

## Completion Criteria

- [ ] Code compiles without errors under `SWIFT_VERSION = 6.0`
- [ ] Zero TSan warnings in full test suite
- [ ] Zero `dispatch_assert_queue_fail` crashes on real device
- [ ] All `nonisolated(unsafe)` instances have justification comments
- [ ] No new warnings introduced
