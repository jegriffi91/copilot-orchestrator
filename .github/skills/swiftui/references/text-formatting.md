# SwiftUI Text Formatting Reference

## Modern Text Formatting

**Use SwiftUI's format parameters instead of `String(format:)` or manual formatters.**

## Number Formatting

### Basic Number Formatting
```swift
// Modern (Correct)
Text(1234, format: .number)  // "1,234"

// Legacy (Avoid)
Text(String(format: "%d", 1234))
```

### Integer Formatting
```swift
Text(42, format: .number.grouping(.never))  // "42"
Text(1000000, format: .number)  // "1,000,000"
```

### Decimal Precision
```swift
// Modern
Text(3.14159, format: .number.precision(.fractionLength(2)))  // "3.14"

// Legacy (Avoid)
Text(String(format: "%.2f", 3.14159))
```

## Currency Formatting
```swift
Text(29.99, format: .currency(code: "USD"))  // "$29.99"
Text(1499, format: .currency(code: "EUR"))   // "€1,499.00"
```

## Percentage Formatting
```swift
Text(0.85, format: .percent)  // "85%"
Text(0.123, format: .percent.precision(.fractionLength(1)))  // "12.3%"
```

## Date and Time Formatting

### Date Formatting
```swift
Text(date, format: .dateTime.day().month().year())  // "Feb 14, 2026"
Text(date, format: .dateTime.weekday(.wide))        // "Saturday"
```

### Time Formatting
```swift
Text(date, format: .dateTime.hour().minute())      // "2:30 PM"
Text(date, format: .dateTime.hour(.twoDigits(amPM: .omitted)).minute())  // "14:30"
```

### Relative Date Formatting
```swift
Text(date, format: .relative(presentation: .named))  // "yesterday"
Text(date, format: .relative(presentation: .numeric)) // "2 days ago"
```

## String Searching and Comparison

### Localized String Comparison
**Use `localizedStandardContains()` for user-input search filtering.**

```swift
// Correct - locale-aware, case/diacritic insensitive
items.filter { $0.name.localizedStandardContains(searchText) }

// Wrong - not locale-aware
items.filter { $0.name.contains(searchText) }

// Wrong - manual lowercasing misses diacritics
items.filter { $0.name.lowercased().contains(searchText.lowercased()) }
```

### Localized Sorting
```swift
let sorted = names.sorted { $0.localizedStandardCompare($1) == .orderedAscending }
```

## Attributed Strings

### Markdown in Text
```swift
Text("**Bold** and *italic* and [link](https://example.com)")
```

### Basic Attributed Text
```swift
var attributedString: AttributedString {
    var str = AttributedString("Hello World")
    str.foregroundColor = .blue
    str.font = .headline
    return str
}

Text(attributedString)
```

## Summary Checklist
- [ ] Using `Text(value, format:)` instead of `String(format:)`
- [ ] Using `.number.precision()` for decimal control
- [ ] Using `.currency(code:)` for money values
- [ ] Using `.dateTime` for date/time formatting
- [ ] Using `localizedStandardContains()` for search filtering
- [ ] Using `localizedStandardCompare()` for sorting
