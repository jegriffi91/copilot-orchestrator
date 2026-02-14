# SwiftUI Animation Basics

## Core Concepts

SwiftUI provides two animation approaches:
- **Implicit**: `.animation(_:value:)` — applied to a view, animates when value changes
- **Explicit**: `withAnimation { }` — wraps state changes, animates affected views

## Implicit Animations

**Always use the value parameter** (the version without value is deprecated).

```swift
// Correct - with value parameter
@State private var isExpanded = false

Text("Hello")
    .scaleEffect(isExpanded ? 1.5 : 1.0)
    .animation(.spring, value: isExpanded)

// Deprecated - without value (too broad)
Text("Hello")
    .scaleEffect(isExpanded ? 1.5 : 1.0)
    .animation(.spring)  // Avoid!
```

## Explicit Animations

Use `withAnimation` for event-driven animations (button taps, gestures).

```swift
Button("Toggle") {
    withAnimation(.spring) {
        isExpanded.toggle()
    }
}
```

## Animation Placement

Where you place `.animation()` matters — it only affects modifiers **above** it:

```swift
Text("Hello")
    .scaleEffect(scale)      // ← Animated
    .opacity(opacity)         // ← Animated
    .animation(.spring, value: scale)
    .foregroundStyle(.blue)   // ← NOT animated
```

## Selective Animation

Disable animation for specific properties using `nil`:

```swift
Text("Hello")
    .offset(y: offset)
    .animation(.spring, value: offset)
    .opacity(opacity)
    .animation(nil, value: opacity)  // No animation for opacity
```

## Timing Curves

### Built-in Curves
| Curve | Use Case |
|-------|----------|
| `.linear` | Constant speed, mechanical |
| `.easeIn` | Starts slow, accelerates |
| `.easeOut` | Fast start, decelerates |
| `.easeInOut` | Smooth start and end |
| `.spring` | Natural bouncy feel |

### Good vs Bad Timing
```swift
// Good - appropriate timing
withAnimation(.easeOut(duration: 0.3)) {
    isPresented = true
}

// Bad - too slow
withAnimation(.easeInOut(duration: 2.0)) {
    isPresented = true
}
```

## Animation Performance

### Prefer Transforms Over Layout
```swift
// Good - GPU-efficient transforms
Text("Hello")
    .offset(x: offset)
    .scaleEffect(scale)
    .rotationEffect(.degrees(rotation))

// Bad - layout changes trigger expensive recalculation
Text("Hello")
    .frame(width: isExpanded ? 200 : 100)
    .padding(isExpanded ? 20 : 10)
```

### Narrow Animation Scope
```swift
// Good - only animates what's needed
HStack {
    Text("Static")
    Text("Animated")
        .opacity(opacity)
        .animation(.default, value: opacity)
}

// Bad - animates entire hierarchy
HStack {
    Text("Static")
    Text("Animated")
        .opacity(opacity)
}
.animation(.default, value: opacity)
```

## Disabling Animations

```swift
// Disable all animations within a transaction
var transaction = Transaction()
transaction.disablesAnimations = true
withTransaction(transaction) {
    value = newValue
}
```

## Quick Reference

### Do
- Use `.animation(_:value:)` with value parameter
- Use `withAnimation` for event-driven animations
- Prefer transforms over layout changes
- Keep animation durations short (0.2-0.5s)
- Use `.spring` for natural feel

### Don't
- Use `.animation()` without value (deprecated)
- Animate layout properties when transforms work
- Use long animation durations
- Animate in hot paths (scroll handlers, etc.)
