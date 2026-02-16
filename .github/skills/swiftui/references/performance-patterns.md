# SwiftUI Performance Patterns Reference

## Performance Optimization

### 1. Avoid Redundant State Updates
Check for value changes before assigning state.

```swift
// Bad - triggers update even if value hasn't changed
.onReceive(publisher) { newValue in
    self.value = newValue
}

// Good - only update if different
.onReceive(publisher) { newValue in
    if self.value != newValue {
        self.value = newValue
    }
}
```

### 2. Optimize Hot Paths
Minimize state updates in frequently executed code paths.

```swift
// Bad - updates state on every scroll event
.onScrollGeometryChange(for: CGFloat.self) { geo in
    geo.contentOffset.y
} action: { _, offset in
    scrollOffset = offset  // Fires every pixel
}

// Good - gate by threshold
.onScrollGeometryChange(for: CGFloat.self) { geo in
    geo.contentOffset.y
} action: { _, offset in
    if abs(offset - scrollOffset) > 10 {
        scrollOffset = offset
    }
}
```

### 3. Pass Only What Views Need
Avoid passing large objects when views only need specific values.

```swift
// Bad - view depends on entire model
struct UserRow: View {
    let user: UserModel  // Re-renders when ANY property changes

    var body: some View {
        Text(user.name)
    }
}

// Good - pass only needed values
struct UserRow: View {
    let name: String  // Re-renders only when name changes

    var body: some View {
        Text(name)
    }
}
```

### 4. Use Equatable Views
Add `Equatable` conformance to skip unnecessary body evaluations.

```swift
struct ExpensiveView: View, Equatable {
    let data: LargeDataSet

    static func == (lhs: Self, rhs: Self) -> Bool {
        lhs.data.id == rhs.data.id
    }

    var body: some View {
        // Complex rendering
    }
}
```

### 5. POD Views for Fast Diffing
Plain-Old-Data views (only value types, no references) diff faster.

```swift
// POD view - all value types, fastest diffing
struct StatsLabel: View {
    let count: Int
    let label: String

    var body: some View {
        Text("\(count) \(label)")
    }
}
```

### 6. Lazy Loading
Use `LazyVStack`/`LazyHStack` for large lists.

```swift
// Good - lazy loading for large datasets
ScrollView {
    LazyVStack {
        ForEach(items) { item in
            ItemRow(item: item)
        }
    }
}

// Bad for large lists - eagerly loads everything
ScrollView {
    VStack {
        ForEach(items) { item in
            ItemRow(item: item)
        }
    }
}
```

### 7. Task Cancellation
Use `.task` modifier for automatic cancellation of async work.

```swift
// Good - automatically cancels when view disappears
.task {
    await loadData()
}

// Good - re-runs when id changes, cancels previous
.task(id: selectedItem) {
    await loadDetails(for: selectedItem)
}
```

### 8. Debug View Updates
Use `Self._printChanges()` to understand why views are re-evaluating.

```swift
var body: some View {
    let _ = Self._printChanges()  // Debug only
    Text("Content")
}
```

### 9. Eliminate Unnecessary Dependencies
Remove dependencies that don't affect the view's output.

```swift
// Bad - depends on entire environment
struct MyView: View {
    @Environment(AppState.self) var appState

    var body: some View {
        Text("Static content")  // Doesn't use appState!
    }
}
```

## Anti-Patterns

### 1. Creating Objects in Body
```swift
// Bad - creates DateFormatter on every body evaluation
var body: some View {
    let formatter = DateFormatter()
    formatter.dateStyle = .long
    return Text(formatter.string(from: date))
}

// Good - use format parameter
var body: some View {
    Text(date, format: .dateTime.day().month().year())
}
```

### 2. Heavy Computation in Body
```swift
// Bad - expensive computation in body
var body: some View {
    let sorted = items.sorted { $0.score > $1.score }
    ForEach(sorted) { item in ItemRow(item: item) }
}

// Good - compute outside body, cache result
@State private var sortedItems: [Item] = []

var body: some View {
    ForEach(sortedItems) { item in ItemRow(item: item) }
        .onChange(of: items) { _, newItems in
            sortedItems = newItems.sorted { $0.score > $1.score }
        }
}
```

### 3. Unnecessary State
```swift
// Bad - derived state stored separately
@State private var items: [Item] = []
@State private var itemCount: Int = 0  // Redundant!

// Good - compute derived values
var itemCount: Int { items.count }
```

## Summary Checklist

- [ ] Check for value changes before assigning state
- [ ] Gate hot path updates by thresholds
- [ ] Pass only needed values to views
- [ ] Use `LazyVStack`/`LazyHStack` for large lists
- [ ] Use `.task` for async work with automatic cancellation
- [ ] No object creation in `body`
- [ ] No heavy computation in `body`
- [ ] No unnecessary stored state (compute derived values)
- [ ] Eliminate unused dependencies
- [ ] Use `Self._printChanges()` for debugging
