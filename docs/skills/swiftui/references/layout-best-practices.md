# SwiftUI Layout Best Practices Reference

## Relative Layout Over Constants
**Always prefer relative sizing and spacing over hard-coded values.**

```swift
// Good - relative sizing
Image("hero")
    .resizable()
    .aspectRatio(contentMode: .fill)
    .containerRelativeFrame(.horizontal)

// Bad - hard-coded constant
Image("hero")
    .frame(width: 375, height: 200)
```

## Context-Agnostic Views
**Views should work in any context. Don't assume screen size or presentation style.**

```swift
// Good - works in any context
struct ProfileCard: View {
    let user: User

    var body: some View {
        VStack(alignment: .leading) {
            Text(user.name).font(.headline)
            Text(user.email).font(.subheadline)
        }
        .padding()
    }
}

// Bad - assumes full screen width
struct ProfileCard: View {
    let user: User

    var body: some View {
        VStack {
            Text(user.name)
        }
        .frame(width: UIScreen.main.bounds.width)
    }
}
```

## Own Your Container
**Let the view define its own padding and background, not the caller.**

```swift
// Good - view owns its appearance
struct InfoCard: View {
    let title: String

    var body: some View {
        Text(title)
            .padding()
            .background(.regularMaterial)
            .clipShape(.rect(cornerRadius: 12))
    }
}

// Usage - caller just positions
VStack {
    InfoCard(title: "Hello")
}
```

## Layout Performance

### Avoid Layout Thrash
- Minimize deep view hierarchies
- Avoid excessive `GeometryReader` nesting
- Gate frequent geometry updates by thresholds
- Prefer `containerRelativeFrame` over `GeometryReader` when possible

## View Logic and Testability

### Separate View Logic from Views
Extract business logic into testable models. This isn't about enforcing an architecture — it's about testability.

```swift
// Good - testable logic
struct ItemListModel {
    var items: [Item]

    func filteredItems(query: String) -> [Item] {
        items.filter { $0.name.localizedStandardContains(query) }
    }
}

struct ItemListView: View {
    @State private var model = ItemListModel(items: [])
    @State private var searchText = ""

    var body: some View {
        List(model.filteredItems(query: searchText)) { item in
            Text(item.name)
        }
        .searchable(text: $searchText)
    }
}
```

## Action Handlers
**Action handlers should reference methods, not contain inline logic.**

```swift
// Good - clear, testable
Button("Save") { save() }
Button("Delete") { confirmDelete() }

// Bad - inline logic
Button("Save") {
    isLoading = true
    Task {
        try await api.save(item)
        isLoading = false
        dismiss()
    }
}
```

## Summary Checklist
- [ ] Using relative layout (not hard-coded constants)
- [ ] Views work in any context (context-agnostic)
- [ ] Views own their container appearance
- [ ] Business logic separated into testable models
- [ ] Action handlers reference methods (not inline logic)
- [ ] No deep view hierarchy nesting
- [ ] Geometry updates gated by thresholds
