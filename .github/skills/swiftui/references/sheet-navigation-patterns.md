# SwiftUI Sheet and Navigation Patterns Reference

## Sheet Patterns

### Item-Driven Sheets (Preferred)
**Use `.sheet(item:)` instead of `.sheet(isPresented:)` for model-based content.**

```swift
@State private var selectedItem: Item?

var body: some View {
    List(items) { item in
        Button(item.name) { selectedItem = item }
    }
    .sheet(item: $selectedItem) { item in
        DetailView(item: item)
    }
}
```

### Sheets Own Their Actions
**Sheets should handle their own dismiss and completion logic.**

```swift
// Good - sheet owns dismiss
struct EditSheet: View {
    @Environment(\.dismiss) private var dismiss
    let item: Item
    let onSave: (Item) -> Void

    var body: some View {
        NavigationStack {
            Form { /* editing fields */ }
                .toolbar {
                    ToolbarItem(placement: .confirmationAction) {
                        Button("Save") {
                            onSave(item)
                            dismiss()
                        }
                    }
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Cancel") { dismiss() }
                    }
                }
        }
    }
}
```

## Navigation Patterns

### Type-Safe Navigation with NavigationStack
```swift
enum Route: Hashable {
    case detail(Item)
    case settings
    case profile(User)
}

struct ContentView: View {
    @State private var path = NavigationPath()

    var body: some View {
        NavigationStack(path: $path) {
            List {
                NavigationLink("Settings", value: Route.settings)
            }
            .navigationDestination(for: Route.self) { route in
                switch route {
                case .detail(let item): DetailView(item: item)
                case .settings: SettingsView()
                case .profile(let user): ProfileView(user: user)
                }
            }
        }
    }
}
```

### Programmatic Navigation
```swift
// Navigate programmatically
Button("Go to Settings") {
    path.append(Route.settings)
}

// Pop to root
Button("Back to Root") {
    path.removeLast(path.count)
}
```

## Presentation Modifiers

### Full Screen Cover
```swift
.fullScreenCover(item: $activeSheet) { sheet in
    switch sheet {
    case .onboarding: OnboardingView()
    case .login: LoginView()
    }
}
```

### Popover
```swift
.popover(isPresented: $showPopover) {
    PopoverContent()
}
```

### Alert with Actions
```swift
.alert("Delete Item?", isPresented: $showDeleteAlert) {
    Button("Delete", role: .destructive) { deleteItem() }
    Button("Cancel", role: .cancel) { }
} message: {
    Text("This action cannot be undone.")
}
```

### Confirmation Dialog
```swift
.confirmationDialog("Share", isPresented: $showShareDialog) {
    Button("Copy Link") { copyLink() }
    Button("Share via Messages") { shareMessages() }
    Button("Cancel", role: .cancel) { }
}
```

## Summary Checklist
- [ ] Using `.sheet(item:)` for model-based sheets
- [ ] Sheets own their dismiss and actions
- [ ] Using `NavigationStack` with `navigationDestination(for:)`
- [ ] Programmatic navigation via `NavigationPath`
- [ ] Using appropriate presentation (sheet, fullScreenCover, popover)
