# SwiftUI Transitions

## Property Animations vs Transitions

- **Property animations**: Animate changes to existing view properties (opacity, scale, etc.)
- **Transitions**: Animate a view's insertion/removal from the hierarchy

## Basic Transitions

### Critical: Transitions Require Animation Context
Transitions only work when paired with an animation **outside** the conditional structure:

```swift
// Correct - animation wraps the state change
Button("Toggle") {
    withAnimation {
        showDetail.toggle()
    }
}

if showDetail {
    DetailView()
        .transition(.slide)
}

// Wrong - no animation context
Button("Toggle") {
    showDetail.toggle()  // No withAnimation!
}

if showDetail {
    DetailView()
        .transition(.slide)  // Won't animate
}
```

### Built-in Transitions
| Transition | Effect |
|------------|--------|
| `.opacity` | Fade in/out |
| `.slide` | Slide from leading edge |
| `.scale` | Scale up/down |
| `.move(edge:)` | Move from specific edge |
| `.push(from:)` | Push in from edge (iOS 16+) |

### Combining Transitions
```swift
.transition(.scale.combined(with: .opacity))
.transition(.move(edge: .bottom).combined(with: .opacity))
```

## Asymmetric Transitions

Different animation for insertion vs. removal:

```swift
.transition(.asymmetric(
    insertion: .scale.combined(with: .opacity),
    removal: .opacity
))
```

## Custom Transitions

### iOS 17+ (Transition Protocol)
```swift
struct RotateTransition: Transition {
    func body(content: Content, phase: TransitionPhase) -> some View {
        content
            .rotationEffect(.degrees(phase.isIdentity ? 0 : 90))
            .opacity(phase.isIdentity ? 1 : 0)
    }
}

extension AnyTransition {
    static var rotate: AnyTransition {
        .modifier(
            active: RotateModifier(angle: 90),
            identity: RotateModifier(angle: 0)
        )
    }
}
```

## Identity and Transitions

SwiftUI tracks view identity to determine insertions/removals. Conditional views (`if/else`) change identity, triggering transitions. Modifier changes (`.opacity`) maintain identity.

## The Animatable Protocol

For custom animations that interpolate between values:

```swift
struct AnimatableCircle: Shape, Animatable {
    var progress: CGFloat

    var animatableData: CGFloat {
        get { progress }
        set { progress = newValue }
    }

    func path(in rect: CGRect) -> Path {
        // Draw based on progress
    }
}
```

### Multiple Properties with AnimatablePair
```swift
var animatableData: AnimatablePair<CGFloat, CGFloat> {
    get { AnimatablePair(width, height) }
    set {
        width = newValue.first
        height = newValue.second
    }
}
```

## Quick Reference

### Do
- Wrap state changes in `withAnimation` for transitions
- Use `.combined(with:)` for multi-property transitions
- Use asymmetric transitions for different enter/exit
- Implement `animatableData` for custom `Animatable`

### Don't
- Forget animation context for transitions
- Use transitions on modifier changes (use property animation)
- Nest too many combined transitions
