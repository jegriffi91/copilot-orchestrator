# SwiftUI ScrollView Patterns Reference

## ScrollView Modifiers

### Hiding Scroll Indicators
**Use `.scrollIndicators(.hidden)` instead of the initializer parameter.**

```swift
// Modern (Correct)
ScrollView {
    content
}
.scrollIndicators(.hidden)

// Legacy (Avoid)
ScrollView(showsIndicators: false) {
    content
}
```

## ScrollViewReader for Programmatic Scrolling

Use `ScrollViewReader` with stable IDs:

```swift
ScrollViewReader { proxy in
    ScrollView {
        ForEach(messages) { message in
            MessageRow(message: message)
                .id(message.id)
        }
    }
    .onChange(of: messages.count) {
        if let lastMessage = messages.last {
            withAnimation {
                proxy.scrollTo(lastMessage.id, anchor: .bottom)
            }
        }
    }
}
```

### Scroll-to-Top Pattern
```swift
ScrollViewReader { proxy in
    ScrollView {
        Color.clear.frame(height: 0).id("top")

        ForEach(items) { item in
            ItemRow(item: item)
        }
    }
    .toolbar {
        Button("Scroll to Top") {
            withAnimation { proxy.scrollTo("top") }
        }
    }
}
```

## Scroll Position Tracking

### Basic Scroll Position
```swift
@State private var scrollPosition: ScrollPosition = .init(idType: Item.ID.self)

ScrollView {
    LazyVStack {
        ForEach(items) { item in
            ItemRow(item: item)
        }
    }
}
.scrollPosition($scrollPosition)
```

### Scroll-Based Header Visibility
```swift
@State private var showHeader = true

ScrollView {
    content
}
.onScrollGeometryChange(for: CGFloat.self) { geo in
    geo.contentOffset.y
} action: { _, offset in
    let shouldShow = offset < 100
    if showHeader != shouldShow {
        withAnimation { showHeader = shouldShow }
    }
}
```

## Scroll Transitions and Effects

### Scroll-Based Opacity
```swift
ForEach(items) { item in
    ItemRow(item: item)
        .scrollTransition { content, phase in
            content.opacity(phase.isIdentity ? 1 : 0.3)
        }
}
```

### Parallax Effect
```swift
Image("hero")
    .visualEffect { content, geometry in
        content.offset(y: geometry.frame(in: .global).minY * 0.3)
    }
```

## Scroll Target Behavior

### Paging ScrollView
```swift
ScrollView(.horizontal) {
    LazyHStack(spacing: 16) {
        ForEach(pages) { page in
            PageView(page: page)
                .containerRelativeFrame(.horizontal)
        }
    }
}
.scrollTargetBehavior(.paging)
```

### Snap to Items
```swift
ScrollView(.horizontal) {
    LazyHStack(spacing: 12) {
        ForEach(cards) { card in
            CardView(card: card)
        }
    }
    .scrollTargetLayout()
}
.scrollTargetBehavior(.viewAligned)
```

## Summary Checklist
- [ ] Using `.scrollIndicators(.hidden)` instead of initializer parameter
- [ ] `ScrollViewReader` uses stable IDs
- [ ] Scroll position changes gated by thresholds
- [ ] Using `.scrollTargetBehavior` for snapping/paging
- [ ] Using `.scrollTransition` for scroll-based effects
