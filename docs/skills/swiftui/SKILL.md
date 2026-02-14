---
name: swiftui
description: Write, review, or improve SwiftUI code following best practices for state management, view composition, performance, modern APIs, Swift concurrency, and iOS 26+ Liquid Glass adoption.
---

# SwiftUI Expert Skill

## Overview

Use this skill to build, review, or improve SwiftUI features with correct state management, modern API usage, Swift concurrency best practices, optimal view composition, and iOS 26+ Liquid Glass styling. Prioritize native APIs, Apple design guidance, and performance-conscious patterns. This skill focuses on facts and best practices without enforcing specific architectural patterns.

## Workflow Decision Tree

### 1) Review existing SwiftUI code
- Check property wrapper usage against the selection guide.
  **ACTION REQUIRED:** Read `references/state-management.md` BEFORE evaluating state.
- Verify modern API usage.
  **ACTION REQUIRED:** Read `references/modern-apis.md` to check for deprecated patterns.
- Verify view composition follows extraction rules (see `references/view-structure.md`)
- Check performance patterns are applied (see `references/performance-patterns.md`)
- Verify list patterns use stable identity (see `references/list-patterns.md`)
- Check animation patterns for correctness (see `references/animation-basics.md`, `references/animation-transitions.md`)
- Inspect Liquid Glass usage for correctness and consistency (see `references/liquid-glass.md`)
- Validate iOS 26+ availability handling with sensible fallbacks

### 2) Improve existing SwiftUI code
- Audit state management for correct wrapper selection (prefer `@Observable` over `ObservableObject`).
  **ACTION REQUIRED:** Read `references/state-management.md` BEFORE modifying property wrappers.
- Replace deprecated APIs with modern equivalents.
  **ACTION REQUIRED:** Read `references/modern-apis.md` for the full replacement table.
- Extract complex views into separate subviews (see `references/view-structure.md`)
- Refactor hot paths to minimize redundant state updates (see `references/performance-patterns.md`)
- Ensure ForEach uses stable identity (see `references/list-patterns.md`)
- Improve animation patterns (see `references/animation-basics.md`, `references/animation-transitions.md`)
- Suggest image downsampling when `UIImage(data:)` is used (see `references/image-optimization.md`)
- Adopt Liquid Glass only when explicitly requested by the user

### 3) Implement new SwiftUI feature
- Design data flow first: identify owned vs injected state.
  **ACTION REQUIRED:** Read `references/state-management.md` BEFORE writing any property wrappers.
- Use modern APIs (no deprecated modifiers or patterns).
  **ACTION REQUIRED:** Read `references/modern-apis.md` BEFORE writing view code.
- Use `@Observable` for shared state (with `@MainActor` if not using default actor isolation)
- Structure views for optimal diffing (see `references/view-structure.md`)
- Separate business logic into testable models (see `references/layout-best-practices.md`)
- Use correct animation patterns (see `references/animation-basics.md`, `references/animation-transitions.md`, `references/animation-advanced.md`)
- Apply glass effects after layout/appearance modifiers (see `references/liquid-glass.md`)
- Gate iOS 26+ features with `#available` and provide fallbacks

## Core Guidelines

### State Management
- **Always prefer `@Observable` over `ObservableObject`** for new code
- **Mark `@Observable` classes with `@MainActor`** unless using default actor isolation
- **Always mark `@State` and `@StateObject` as `private`** (makes dependencies clear)
- **Never declare passed values as `@State` or `@StateObject`** (they only accept initial values)
- Use `@State` with `@Observable` classes (not `@StateObject`)
- `@Binding` only when child needs to **modify** parent state
- `@Bindable` for injected `@Observable` objects needing bindings
- Use `let` for read-only values; `var` + `.onChange()` for reactive reads
- Legacy: `@StateObject` for owned `ObservableObject`; `@ObservedObject` for injected
- Nested `ObservableObject` doesn't work (pass nested objects directly); `@Observable` handles nesting fine

### Modern APIs
- Use `foregroundStyle()` instead of `foregroundColor()`
- Use `clipShape(.rect(cornerRadius:))` instead of `cornerRadius()`
- Use `Tab` API instead of `tabItem()`
- Use `Button` instead of `onTapGesture()` (unless need location/count)
- Use `NavigationStack` instead of `NavigationView`
- Use `navigationDestination(for:)` for type-safe navigation
- Use two-parameter or no-parameter `onChange()` variant
- Use `.sheet(item:)` instead of `.sheet(isPresented:)` for model-based content
- Use `ScrollViewReader` for programmatic scrolling with stable IDs
- Avoid `UIScreen.main.bounds` for sizing
- Avoid `GeometryReader` when alternatives exist (e.g., `containerRelativeFrame()`)

### Swift Best Practices
- Use modern Text formatting (`.format` parameters, not `String(format:)`)
- Use `localizedStandardContains()` for user-input filtering (not `contains()`)
- Prefer static member lookup (`.blue` vs `Color.blue`)
- Use `.task` modifier for automatic cancellation of async work
- Use `.task(id:)` for value-dependent tasks

### View Composition
- **Prefer modifiers over conditional views** for state changes (maintains view identity)
- Extract complex views into separate subviews for better readability and performance
- Keep views small for optimal performance
- Keep view `body` simple and pure (no side effects or complex logic)
- Use `@ViewBuilder` functions only for small, simple sections
- Prefer `@ViewBuilder let content: Content` over closure-based content properties
- Separate business logic into testable models
- Action handlers should reference methods, not contain inline logic
- Use relative layout over hard-coded constants
- Views should work in any context (don't assume screen size or presentation style)

### Performance
- Pass only needed values to views (avoid large "config" or "context" objects)
- Eliminate unnecessary dependencies to reduce update fan-out
- Check for value changes before assigning state in hot paths
- Avoid redundant state updates in `onReceive`, `onChange`, scroll handlers
- Use `LazyVStack`/`LazyHStack` for large lists
- Use stable identity for `ForEach` (never `.indices` for dynamic content)
- Ensure constant number of views per `ForEach` element
- Avoid inline filtering in `ForEach` (prefilter and cache)
- Avoid `AnyView` in list rows
- Consider POD views for fast diffing
- Use `Self._printChanges()` to debug unexpected view updates

### Animations
- Use `.animation(_:value:)` with value parameter (deprecated version without value is too broad)
- Use `withAnimation` for event-driven animations (button taps, gestures)
- Prefer transforms (`offset`, `scale`, `rotation`) over layout changes (`frame`) for performance
- Transitions require animations outside the conditional structure
- Custom `Animatable` implementations must have explicit `animatableData`
- Use `.phaseAnimator` for multi-step sequences (iOS 17+)
- Use `.keyframeAnimator` for precise timing control (iOS 17+)
- Implicit animations override explicit animations (later in view tree wins)

### Liquid Glass (iOS 26+)
**Only adopt when explicitly requested by the user.**
- Use native `glassEffect`, `GlassEffectContainer`, and glass button styles
- Wrap multiple glass elements in `GlassEffectContainer`
- Apply `.glassEffect()` after layout and visual modifiers
- Use `.interactive()` only for tappable/focusable elements
- Use `glassEffectID` with `@Namespace` for morphing transitions

## Quick Reference

### Property Wrapper Selection (Modern)
| Wrapper | Use When |
|---------|----------|
| `@State` | Internal view state (must be `private`), or owned `@Observable` class |
| `@Binding` | Child modifies parent's state |
| `@Bindable` | Injected `@Observable` needing bindings |
| `let` | Read-only value from parent |
| `var` | Read-only value watched via `.onChange()` |

**Legacy (Pre-iOS 17):**
| Wrapper | Use When |
|---------|----------|
| `@StateObject` | View owns an `ObservableObject` (use `@State` with `@Observable` instead) |
| `@ObservedObject` | View receives an `ObservableObject` |

### Modern API Replacements
| Deprecated | Modern Alternative |
|------------|-------------------|
| `foregroundColor()` | `foregroundStyle()` |
| `cornerRadius()` | `clipShape(.rect(cornerRadius:))` |
| `tabItem()` | `Tab` API |
| `onTapGesture()` | `Button` (unless need location/count) |
| `NavigationView` | `NavigationStack` |
| `onChange(of:) { value in }` | `onChange(of:) { old, new in }` or `onChange(of:) { }` |
| `GeometryReader` | `containerRelativeFrame()` or `visualEffect()` |
| `String(format:)` | `Text(value, format:)` |
| `string.contains(search)` | `string.localizedStandardContains(search)` |

## Review Checklist

### State Management
- [ ] Using `@Observable` instead of `ObservableObject` for new code
- [ ] `@Observable` classes marked with `@MainActor` (if needed)
- [ ] Using `@State` with `@Observable` classes (not `@StateObject`)
- [ ] `@State` and `@StateObject` properties are `private`
- [ ] Passed values NOT declared as `@State` or `@StateObject`
- [ ] `@Binding` only where child modifies parent state
- [ ] `@Bindable` for injected `@Observable` needing bindings

### Modern APIs
**ACTION REQUIRED:** Read `references/modern-apis.md` for full details and examples.
- [ ] Using `foregroundStyle()` instead of `foregroundColor()`
- [ ] Using `clipShape(.rect(cornerRadius:))` instead of `cornerRadius()`
- [ ] Using `Tab` API instead of `tabItem()`
- [ ] Using `Button` instead of `onTapGesture()`
- [ ] Using `NavigationStack` instead of `NavigationView`
- [ ] Avoiding `UIScreen.main.bounds`

### Sheets & Navigation
**ACTION REQUIRED:** Read `references/sheet-navigation-patterns.md` for patterns and examples.
- [ ] Using `.sheet(item:)` for model-based sheets
- [ ] Sheets own their actions and dismiss internally
- [ ] Using `navigationDestination(for:)` for type-safe navigation

### ScrollView
**ACTION REQUIRED:** Read `references/scroll-patterns.md` for patterns and examples.
- [ ] Using `ScrollViewReader` with stable IDs for programmatic scrolling
- [ ] Using `.scrollIndicators(.hidden)` instead of initializer parameter

### Text & Formatting
**ACTION REQUIRED:** Read `references/text-formatting.md` for modern formatting patterns.
- [ ] Using modern Text formatting (not `String(format:)`)
- [ ] Using `localizedStandardContains()` for search filtering

### View Structure
**ACTION REQUIRED:** Read `references/view-structure.md` for extraction and composition patterns.
- [ ] Using modifiers instead of conditionals for state changes
- [ ] Complex views extracted to separate subviews
- [ ] Views kept small for performance
- [ ] Container views use `@ViewBuilder let content: Content`

### Performance
**ACTION REQUIRED:** Read `references/performance-patterns.md` for optimization techniques.
- [ ] View `body` kept simple and pure (no side effects)
- [ ] Passing only needed values (not large config objects)
- [ ] State updates check for value changes before assigning
- [ ] Hot paths minimize state updates

### List Patterns
**ACTION REQUIRED:** Read `references/list-patterns.md` for ForEach identity rules.
- [ ] ForEach uses stable identity (not `.indices`)
- [ ] Constant number of views per ForEach element
- [ ] No inline filtering in ForEach

### Layout
**ACTION REQUIRED:** Read `references/layout-best-practices.md` for layout patterns.
- [ ] Using relative layout (not hard-coded constants)
- [ ] Views work in any context (context-agnostic)
- [ ] Business logic separated into testable models

### Animations
**ACTION REQUIRED:** Read `references/animation-basics.md`, `references/animation-transitions.md`, and `references/animation-advanced.md` for animation patterns.
- [ ] Using `.animation(_:value:)` with value parameter
- [ ] Transitions paired with animations outside conditional structure
- [ ] Preferring transforms over layout changes for performance

### Liquid Glass (iOS 26+)
**ACTION REQUIRED:** Read `references/liquid-glass.md` for Liquid Glass patterns.
- [ ] `#available(iOS 26, *)` with fallback
- [ ] Multiple glass views wrapped in `GlassEffectContainer`
- [ ] `.glassEffect()` applied after layout/appearance modifiers

## References

- `references/state-management.md` — Property wrappers and data flow (prefer `@Observable`)
- `references/view-structure.md` — View composition, extraction, and container patterns
- `references/performance-patterns.md` — Performance optimization techniques and anti-patterns
- `references/list-patterns.md` — ForEach identity, stability, and list best practices
- `references/layout-best-practices.md` — Layout patterns, context-agnostic views, and testability
- `references/modern-apis.md` — Modern API usage and deprecated replacements
- `references/animation-basics.md` — Core animation concepts, implicit/explicit animations
- `references/animation-transitions.md` — Transitions, custom transitions, Animatable protocol
- `references/animation-advanced.md` — Transactions, phase/keyframe animations (iOS 17+)
- `references/sheet-navigation-patterns.md` — Sheet presentation and navigation patterns
- `references/scroll-patterns.md` — ScrollView patterns and programmatic scrolling
- `references/text-formatting.md` — Modern text formatting and string operations
- `references/image-optimization.md` — AsyncImage, image downsampling, and optimization
- `references/liquid-glass.md` — iOS 26+ Liquid Glass API

## Attribution

Adapted from [AvdLee/SwiftUI-Agent-Skill](https://github.com/AvdLee/SwiftUI-Agent-Skill) with imperative trigger patterns for the copilot-orchestrator 3-tier architecture.

## Philosophy

This skill focuses on **facts and best practices**, not architectural opinions:
- We don't enforce specific architectures (e.g., MVVM, VIPER)
- We do encourage separating business logic for testability
- We prioritize modern APIs over deprecated ones
- We emphasize thread safety with `@MainActor` and `@Observable`
- We optimize for performance and maintainability
- We follow Apple's Human Interface Guidelines and API design patterns
