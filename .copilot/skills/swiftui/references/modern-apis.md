# Modern SwiftUI APIs Reference

## Styling and Appearance

### foregroundStyle() vs foregroundColor()
**Always use `foregroundStyle()` instead of `foregroundColor()`.**

```swift
// Modern (Correct)
Text("Hello")
    .foregroundStyle(.primary)

Image(systemName: "star")
    .foregroundStyle(.blue)

// Legacy (Avoid)
Text("Hello")
    .foregroundColor(.primary)
```

**Why**: `foregroundStyle()` supports hierarchical styles, gradients, and materials.

### clipShape() vs cornerRadius()
**Always use `clipShape(.rect(cornerRadius:))` instead of `cornerRadius()`.**

```swift
// Modern (Correct)
Image("photo")
    .clipShape(.rect(cornerRadius: 12))

// Legacy (Avoid)
Image("photo")
    .cornerRadius(12)
```

### fontWeight() vs bold()
**Use `bold()` for bold text. Use `fontWeight()` only for specific weights.**

```swift
// Correct
Text("Important")
    .bold()

// Acceptable (specific weight needed)
Text("Semibold")
    .fontWeight(.semibold)
```

## Navigation

### NavigationStack vs NavigationView
**Always use `NavigationStack` instead of `NavigationView`.**

```swift
// Modern (Correct)
NavigationStack {
    List(items) { item in
        NavigationLink(value: item) {
            Text(item.name)
        }
    }
    .navigationDestination(for: Item.self) { item in
        DetailView(item: item)
    }
}

// Legacy (Avoid)
NavigationView {
    List(items) { item in
        NavigationLink(destination: DetailView(item: item)) {
            Text(item.name)
        }
    }
}
```

### navigationDestination(for:)
**Use `navigationDestination(for:)` for type-safe navigation.**

```swift
enum Route: Hashable {
    case profile
    case settings
}

NavigationStack {
    List {
        NavigationLink("Profile", value: Route.profile)
        NavigationLink("Settings", value: Route.settings)
    }
    .navigationDestination(for: Route.self) { route in
        switch route {
        case .profile: ProfileView()
        case .settings: SettingsView()
        }
    }
}
```

## Tabs

### Tab API vs tabItem()
**For iOS 18+, prefer the `Tab` API over `tabItem()`.**

```swift
// Modern (Correct) - iOS 18+
TabView {
    Tab("Home", systemImage: "house") {
        HomeView()
    }
    Tab("Search", systemImage: "magnifyingglass") {
        SearchView()
    }
}

// Legacy (Avoid)
TabView {
    HomeView()
        .tabItem {
            Label("Home", systemImage: "house")
        }
}
```

**Important**: When using `Tab(role:)`, you must use `Tab { } label: { }` syntax for all tabs. Mixing with `.tabItem()` causes compilation errors.

## Interactions

### Button vs onTapGesture()
**Never use `onTapGesture()` unless you need tap location or count.**

```swift
// Correct - standard tap action
Button("Tap me") {
    performAction()
}

// Correct - need tap location
Text("Tap anywhere")
    .onTapGesture { location in
        handleTap(at: location)
    }

// Wrong - use Button instead
Text("Tap me")
    .onTapGesture {
        performAction()
    }
```

### Button with Images
**Always specify text alongside images for accessibility.**

```swift
// Correct
Button("Add Item", systemImage: "plus") {
    addItem()
}

// Also correct
Button {
    addItem()
} label: {
    Label("Add Item", systemImage: "plus")
}

// Wrong - image only, no text
Button {
    addItem()
} label: {
    Image(systemName: "plus")
}
```

## Layout and Sizing

### Avoid UIScreen.main.bounds
**Never use `UIScreen.main.bounds` to read available space.**

```swift
// Better - use containerRelativeFrame (iOS 17+)
Text("Full width")
    .containerRelativeFrame(.horizontal)

// Best - let SwiftUI handle sizing
Text("Auto-sized")
    .frame(maxWidth: .infinity)
```

### GeometryReader Alternatives
**Don't use `GeometryReader` if a newer alternative works.**

```swift
// Modern - containerRelativeFrame
Image("hero")
    .resizable()
    .containerRelativeFrame(.horizontal) { length, axis in
        length * 0.8
    }

// Modern - visualEffect for position-based effects
Text("Parallax")
    .visualEffect { content, geometry in
        content.offset(y: geometry.frame(in: .global).minY * 0.5)
    }
```

## Type Erasure

### Avoid AnyView
**Avoid `AnyView` unless absolutely required.**

```swift
// Prefer - use @ViewBuilder
@ViewBuilder
func content() -> some View {
    if condition {
        Text("Option A")
    } else {
        Image(systemName: "photo")
    }
}
```

## Styling Best Practices

### Dynamic Type
**Don't force specific font sizes. Prefer Dynamic Type.**

```swift
// Correct
Text("Title").font(.title)
Text("Body").font(.body)

// Avoid - fixed size doesn't scale
Text("Title").font(.system(size: 24))
```

### UIKit Colors
**Avoid using UIKit colors in SwiftUI code.**

```swift
// Correct - SwiftUI colors
Text("Hello")
    .foregroundStyle(.blue)

// Wrong - UIKit colors
Text("Hello")
    .foregroundColor(Color(UIColor.systemBlue))
```

## Static Member Lookup
**Prefer static member lookup to struct instances.**

```swift
// Correct
Circle().fill(.blue)
Button("Action") { }.buttonStyle(.borderedProminent)

// Verbose
Circle().fill(Color.blue)
```

## Summary Checklist
- [ ] Use `foregroundStyle()` instead of `foregroundColor()`
- [ ] Use `clipShape(.rect(cornerRadius:))` instead of `cornerRadius()`
- [ ] Use `Tab` API instead of `tabItem()`
- [ ] Use `Button` instead of `onTapGesture()`
- [ ] Use `NavigationStack` instead of `NavigationView`
- [ ] Avoid `AnyView` unless required
- [ ] Avoid `UIScreen.main.bounds`
- [ ] Use Dynamic Type
- [ ] Use static member lookup
- [ ] Include text labels with button images
