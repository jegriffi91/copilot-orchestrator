# SwiftUI Liquid Glass Reference (iOS 26+)

## Overview
Liquid Glass is Apple's new design language introduced in iOS 26. It provides translucent, dynamic glass effects that adapt to the content behind them.

## Availability
All Liquid Glass APIs require **iOS 26+**. Always use availability checks with appropriate fallbacks.

```swift
if #available(iOS 26, *) {
    content.glassEffect(.regular, in: .rect(cornerRadius: 16))
} else {
    content.background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 16))
}
```

## Core APIs

### glassEffect Modifier
```swift
content
    .glassEffect(.regular, in: .rect(cornerRadius: 16))
```

### GlassEffectStyle
| Style | Use Case |
|-------|----------|
| `.regular` | Standard glass appearance |
| `.regular.interactive()` | Tappable/focusable glass elements |

## GlassEffectContainer

Wrap multiple glass elements to coordinate their visual effects:

```swift
GlassEffectContainer {
    HStack {
        GlassButton1()
        GlassButton2()
    }
}
```

### With Spacing
```swift
GlassEffectContainer(spacing: 24) {
    HStack(spacing: 24) {
        GlassButton1()
        GlassButton2()
    }
}
```

## Glass Button Styles

```swift
Button("Confirm") { }
    .buttonStyle(.glass)

Button("Primary Action") { }
    .buttonStyle(.glassProminent)
```

### Custom Glass Buttons
```swift
Button {
    action()
} label: {
    Label("Share", systemImage: "square.and.arrow.up")
}
.padding()
.glassEffect(.regular.interactive(), in: .capsule)
```

## Morphing Transitions

Use `glassEffectID` with `@Namespace` for smooth morphing between glass elements:

```swift
@Namespace private var namespace

if isExpanded {
    ExpandedView()
        .glassEffect(in: .rect(cornerRadius: 20))
        .glassEffectID("card", in: namespace)
} else {
    CompactView()
        .glassEffect(in: .capsule)
        .glassEffectID("card", in: namespace)
}
```

### Requirements for Morphing
- Same `glassEffectID` and namespace on both views
- Wrapped in `withAnimation` for the state change
- Both views must have glass effects applied

## Modifier Order

**Apply `.glassEffect()` after layout and visual modifiers:**

```swift
// Correct order
content
    .padding()
    .foregroundStyle(.primary)
    .glassEffect(.regular, in: .rect(cornerRadius: 16))

// Wrong - glass before layout modifiers
content
    .glassEffect(.regular, in: .rect(cornerRadius: 16))
    .padding()
    .foregroundStyle(.primary)
```

## Complete Examples

### Toolbar with Glass Buttons
```swift
GlassEffectContainer(spacing: 16) {
    HStack(spacing: 16) {
        Button("Back", systemImage: "chevron.left") { }
            .buttonStyle(.glass)

        Spacer()

        Button("Share", systemImage: "square.and.arrow.up") { }
            .buttonStyle(.glass)
    }
    .padding()
}
```

### Card with Glass Effect
```swift
VStack(alignment: .leading) {
    Text("Card Title").font(.headline)
    Text("Description").font(.body)
}
.padding()
.frame(maxWidth: .infinity, alignment: .leading)
.glassEffect(.regular, in: .rect(cornerRadius: 20))
```

## Fallback Strategies

### Using Materials
```swift
if #available(iOS 26, *) {
    content.glassEffect(.regular, in: .rect(cornerRadius: 16))
} else {
    content.background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 16))
}
```

### Available Materials for Fallback
| Material | Appearance |
|----------|------------|
| `.ultraThinMaterial` | Lightest blur |
| `.thinMaterial` | Light blur |
| `.regularMaterial` | Medium blur |
| `.thickMaterial` | Heavy blur |
| `.ultraThickMaterial` | Heaviest blur |

## Best Practices

### Do
- Use `GlassEffectContainer` for grouped glass elements
- Apply `.interactive()` only on tappable/focusable elements
- Place `.glassEffect()` after layout modifiers
- Use `#available(iOS 26, *)` with material fallbacks
- Keep glass shapes consistent across related elements

### Don't
- Apply glass to every element (use sparingly)
- Nest glass effects inside glass effects
- Use `.interactive()` on non-interactive elements
- Forget availability checks

## Checklist
- [ ] `#available(iOS 26, *)` with fallback for all Liquid Glass
- [ ] Multiple glass views wrapped in `GlassEffectContainer`
- [ ] `.glassEffect()` applied after layout/appearance modifiers
- [ ] `.interactive()` only on user-interactable elements
- [ ] Shapes and tints consistent across related elements
- [ ] Material fallbacks provided for pre-iOS 26
