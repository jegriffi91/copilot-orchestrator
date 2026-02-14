---
id: snapshot_testing
type: practice
tags: [testing, swiftui]
stitcher_rules:
  - "RULE: Fixed Device Size | ACTION: Pin snapshots to a specific device and scale, never use host screen size | SEVERITY: CRITICAL"
  - "RULE: Deterministic Content | ACTION: Use fixed data, no live images or dynamic timestamps in snapshots | SEVERITY: CRITICAL"
  - "RULE: Review Diffs | ACTION: Always visually inspect snapshot diffs before accepting new references | SEVERITY: WARN"
  - "STEP: Record Snapshots | CMD: Run tests with record mode to generate new reference images | SEVERITY: WARN"
---

# Snapshot Testing Standards

## Overview

Rules for reliable SwiftUI snapshot tests. Snapshot tests catch unintended visual regressions but are fragile if not configured correctly.

## Rule 1: Fixed Device Size

**Rationale:** Snapshots rendered on different devices produce different images. Pin to a consistent configuration.

```swift
func testProfileCard_snapshot() {
    let view = ProfileCard(user: .preview)
    assertSnapshot(
        of: view,
        as: .image(
            layout: .device(config: .iPhone13Mini),
            traits: .init(displayScale: 2.0)
        )
    )
}
```

## Rule 2: Deterministic Content

**Rationale:** Dynamic content (live images, timestamps, random data) causes false failures.

```swift
// ❌ Bad — timestamp changes every run
let card = EventCard(event: Event(date: Date()))

// ✅ Good — fixed preview data
let card = EventCard(event: Event(date: Date(timeIntervalSince1970: 1700000000)))
```
