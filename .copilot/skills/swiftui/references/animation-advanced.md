# SwiftUI Advanced Animations

## Transactions

### Basic Usage
Transactions control animation behavior within a scope.

```swift
withAnimation(.spring(duration: 0.5)) {
    isExpanded.toggle()
}
```

### The .transaction Modifier
Override animations for specific views:

```swift
ChildView()
    .transaction { transaction in
        transaction.animation = .linear(duration: 0.1)
    }
```

### Animation Precedence
- Implicit animations (`.animation()`) override explicit (`withAnimation`)
- Later modifiers in the view tree take precedence
- `.transaction` can override both

### Disabling Animations
```swift
var transaction = Transaction()
transaction.disablesAnimations = true
withTransaction(transaction) {
    position = newPosition
}
```

### Custom Transaction Keys (iOS 17+)
```swift
private struct IsSpecialAnimationKey: TransactionKey {
    static let defaultValue = false
}

extension Transaction {
    var isSpecialAnimation: Bool {
        get { self[IsSpecialAnimationKey.self] }
        set { self[IsSpecialAnimationKey.self] = newValue }
    }
}
```

## Phase Animations (iOS 17+)

Multi-step animations that cycle through phases automatically.

### Basic Usage
```swift
Text("Pulsing")
    .phaseAnimator([false, true]) { content, phase in
        content
            .scaleEffect(phase ? 1.2 : 1.0)
            .opacity(phase ? 1.0 : 0.7)
    }
```

### Enum Phases (Recommended for Clarity)
```swift
enum BouncePhase: CaseIterable {
    case initial, up, down

    var scale: CGFloat {
        switch self {
        case .initial: 1.0
        case .up: 1.3
        case .down: 0.9
        }
    }
}

Circle()
    .phaseAnimator(BouncePhase.allCases) { content, phase in
        content.scaleEffect(phase.scale)
    } animation: { phase in
        switch phase {
        case .initial: .spring(duration: 0.3)
        case .up: .spring(duration: 0.2)
        case .down: .spring(duration: 0.4)
        }
    }
```

## Keyframe Animations (iOS 17+)

Precise timing control with multiple synchronized tracks.

### Basic Usage
```swift
struct AnimationValues {
    var scale: CGFloat = 1.0
    var opacity: Double = 1.0
    var offset: CGFloat = 0
}

Text("Keyframed")
    .keyframeAnimator(initialValue: AnimationValues()) { content, value in
        content
            .scaleEffect(value.scale)
            .opacity(value.opacity)
            .offset(y: value.offset)
    } keyframes: { _ in
        KeyframeTrack(\.scale) {
            SpringKeyframe(1.5, duration: 0.3)
            SpringKeyframe(1.0, duration: 0.3)
        }
        KeyframeTrack(\.opacity) {
            LinearKeyframe(0.5, duration: 0.2)
            LinearKeyframe(1.0, duration: 0.4)
        }
    }
```

### Keyframe Types
| Type | Behavior |
|------|----------|
| `LinearKeyframe` | Constant speed interpolation |
| `SpringKeyframe` | Spring-based interpolation |
| `CubicKeyframe` | Bezier curve interpolation |
| `MoveKeyframe` | Instant jump (no interpolation) |

## Animation Completion Handlers (iOS 17+)

### With withAnimation
```swift
withAnimation(.spring(duration: 0.5)) {
    isExpanded = true
} completion: {
    showContent = true
}
```

### With Transaction (For Reexecution)
Use `.transaction(value:)` when you need the completion to re-fire:

```swift
.transaction(value: animationTrigger) { transaction in
    transaction.addAnimationCompletion {
        onAnimationComplete()
    }
}
```

## Quick Reference

| Feature | Minimum iOS | Use Case |
|---------|-------------|----------|
| `withAnimation { }` | All | Event-driven animations |
| `.animation(_:value:)` | All | Value-change animations |
| `.transaction` | All | Override animation per-view |
| Custom Transaction Keys | 17+ | Custom animation context |
| `.phaseAnimator` | 17+ | Multi-step sequences |
| `.keyframeAnimator` | 17+ | Precise timing control |
| `completion:` handler | 17+ | Post-animation actions |
