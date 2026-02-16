# SwiftUI Image Optimization Reference

## AsyncImage Best Practices

### Basic AsyncImage with Phase Handling
```swift
AsyncImage(url: imageURL) { phase in
    switch phase {
    case .empty:
        ProgressView()
    case .success(let image):
        image
            .resizable()
            .aspectRatio(contentMode: .fill)
    case .failure:
        Image(systemName: "photo")
            .foregroundStyle(.secondary)
    @unknown default:
        EmptyView()
    }
}
```

### AsyncImage with Transition
```swift
AsyncImage(url: imageURL) { phase in
    switch phase {
    case .success(let image):
        image
            .resizable()
            .transition(.opacity)
    default:
        Color.gray.opacity(0.2)
    }
}
.animation(.default, value: imageURL)
```

## Image Decoding and Downsampling (Optional Optimization)

When you encounter `UIImage(data:)` for large images, suggest downsampling as an optimization.

### Current Pattern That Could Be Optimized
```swift
// Potentially expensive for large images
if let image = UIImage(data: imageData) {
    Image(uiImage: image)
        .resizable()
        .frame(width: 100, height: 100)
}
```

### Suggested Optimization Pattern
```swift
// Downsample to target size, reducing memory
if let image = downsample(data: imageData, to: CGSize(width: 200, height: 200)) {
    Image(uiImage: image)
        .resizable()
        .frame(width: 100, height: 100)
}
```

### Reusable Image Downsampling Helper
```swift
func downsample(data: Data, to targetSize: CGSize, scale: CGFloat = UIScreen.main.scale) -> UIImage? {
    let options: [CFString: Any] = [
        kCGImageSourceCreateThumbnailFromImageAlways: true,
        kCGImageSourceShouldCacheImmediately: true,
        kCGImageSourceCreateThumbnailWithTransform: true,
        kCGImageSourceThumbnailMaxPixelSize: max(targetSize.width, targetSize.height) * scale
    ]

    guard let source = CGImageSourceCreateWithData(data as CFData, nil),
          let cgImage = CGImageSourceCreateThumbnailAtIndex(source, 0, options as CFDictionary)
    else { return nil }

    return UIImage(cgImage: cgImage)
}
```

### When to Suggest This Optimization
- Loading images from network/disk into fixed-size containers
- Displaying many images in a list or grid
- Large images displayed at small sizes

## SF Symbols

### Using SF Symbols
```swift
Image(systemName: "star.fill")
    .font(.title)
    .foregroundStyle(.yellow)

// With rendering mode
Image(systemName: "cloud.sun.fill")
    .symbolRenderingMode(.multicolor)
```

### SF Symbol Variants
```swift
Label("Favorites", systemImage: "heart")
    .symbolVariant(.fill)
```

## Image Rendering

### ImageRenderer for Snapshots
```swift
let renderer = ImageRenderer(content: MySwiftUIView())
if let uiImage = renderer.uiImage {
    // Use the rendered image
}
```

## Summary Checklist
- [ ] Using `AsyncImage` with phase handling for remote images
- [ ] Consider downsampling for large images in small containers
- [ ] Using SF Symbols with appropriate rendering modes
- [ ] Using `ImageRenderer` for view snapshots
