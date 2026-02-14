# SwiftUI View Structure Reference

## View Structure Principles

### Prefer Modifiers Over Conditional Views
Use modifiers to change appearance based on state rather than conditional view inclusion. This maintains view identity and enables smooth animations.

```swift
// Good - modifier preserves identity
Text("Status")
    .opacity(isVisible ? 1.0 : 0.0)

// Good - modifier for color
Text("Status")
    .foregroundStyle(isActive ? .blue : .gray)

// Bad - conditional inclusion changes identity
if isVisible {
    Text("Status")
}
```

### When Conditionals Are Appropriate
Use conditionals when view types genuinely differ:

```swift
// Appropriate - different view types
if isLoading {
    ProgressView()
} else {
    ContentView()
}
```

## Extract Subviews, Not Computed Properties

### The Problem with @ViewBuilder Functions
`@ViewBuilder` functions capture the parent view's state, causing unnecessary re-evaluations.

```swift
// Bad - captures self, re-evaluated with parent
@ViewBuilder
func headerView() -> some View {
    HStack {
        Text(title)
        Image(systemName: icon)
    }
}
```

### The Solution: Separate Structs
Extract into separate `View` structs for better performance and independence.

```swift
// Good - independent state, targeted updates
struct HeaderView: View {
    let title: String
    let icon: String

    var body: some View {
        HStack {
            Text(title)
            Image(systemName: icon)
        }
    }
}
```

### When @ViewBuilder Functions Are Acceptable
- Small, simple sections (2-3 lines)
- No captured state
- Used once, not reused

### When to Extract Subviews
- View body exceeds ~20 lines
- Section has its own state or logic
- Component is reusable
- Complex conditional rendering

## Container View Pattern

### Avoid Closure-Based Content
```swift
// Bad - closure-based
struct CardView<Content: View>: View {
    let content: () -> Content

    var body: some View {
        VStack { content() }
    }
}
```

### Use @ViewBuilder Property Instead
```swift
// Good - @ViewBuilder property
struct CardView<Content: View>: View {
    @ViewBuilder let content: Content

    var body: some View {
        VStack { content }
            .padding()
            .background(.regularMaterial)
            .clipShape(.rect(cornerRadius: 12))
    }
}

// Usage
CardView {
    Text("Title")
    Text("Subtitle")
}
```

## ZStack vs overlay/background

**Use `overlay`/`background` for secondary layers. Use `ZStack` when all layers are equal.**

```swift
// Prefer overlay - badge on top of content
Image("photo")
    .overlay(alignment: .topTrailing) {
        Badge(count: 3)
    }

// Prefer background - decorative layer behind content
Text("Hello")
    .padding()
    .background(.ultraThinMaterial)

// Use ZStack - equal-weight layers
ZStack {
    MapView()
    FloatingControls()
}
```

## Summary Checklist
- [ ] Prefer modifiers over conditional views for state changes
- [ ] Extract complex views into separate subview structs
- [ ] Keep views small (body < 20 lines)
- [ ] Use `@ViewBuilder let content: Content` for container views
- [ ] Prefer `overlay`/`background` over `ZStack` for layering
- [ ] `@ViewBuilder` functions only for small, simple, non-reusable sections
- [ ] Keep view `body` pure (no side effects)
