---
id: unit_testing
type: practice
tags: [testing, common]
stitcher_rules:
  - "RULE: AAA Pattern | ACTION: Structure tests as Arrange, Act, Assert with clear separation | SEVERITY: CRITICAL"
  - "RULE: One Assertion Focus | ACTION: Each test verifies one behavior, use descriptive test names | SEVERITY: WARN"
  - "RULE: No Network in Unit Tests | ACTION: Mock all network dependencies, tests must run offline | SEVERITY: CRITICAL"
  - "RULE: Protocol-Based Mocks | ACTION: Depend on protocols, inject mock conformances in tests | SEVERITY: CRITICAL"
  - "RULE: No Sleep in Tests | ACTION: Use expectations or async/await, never Thread.sleep | SEVERITY: CRITICAL"
  - "RULE: Deterministic Tests | ACTION: No dependency on time, locale, or execution order | SEVERITY: CRITICAL"
  - "STEP: Run Targeted Tests | CMD: swift test --filter <ChangedModule> for scoped verification | SEVERITY: CRITICAL"
  - "STEP: Check Coverage | CMD: Verify new code has corresponding test coverage | SEVERITY: WARN"
---

# Unit Testing Standards

## Overview

Rules for writing reliable, fast, and maintainable unit tests. Tests are the primary verification mechanism for all code changes.

## Rule 1: AAA Pattern

**Rationale:** Consistent structure makes tests readable and reviewable at a glance.

```swift
func testFetchUser_returnsUser_whenAPISucceeds() async throws {
    // Arrange
    let mockAPI = MockUserAPI()
    mockAPI.stubResult = User(name: "Alice")
    let sut = UserService(api: mockAPI)

    // Act
    let user = try await sut.fetchUser(id: "123")

    // Assert
    XCTAssertEqual(user.name, "Alice")
}
```

## Rule 2: One Assertion Focus

**Rationale:** Tests that verify multiple unrelated behaviors are hard to debug when they fail.

```swift
// ❌ Bad — testing two unrelated behaviors
func testUserService() async throws {
    let user = try await sut.fetch(id: "1")
    XCTAssertEqual(user.name, "Alice")
    XCTAssertTrue(sut.cache.contains("1"))  // ← Separate behavior
}

// ✅ Good — separate tests for separate behaviors
func testFetch_returnsCorrectUser() async throws { ... }
func testFetch_cachesResult() async throws { ... }
```

## Rule 3: Protocol-Based Mocks

**Rationale:** Concrete dependencies make tests slow, flaky, and coupled to implementation.

```swift
// ❌ Bad — depends on concrete network layer
class UserService {
    let session = URLSession.shared
}

// ✅ Good — injectable protocol dependency
protocol UserAPIProtocol: Sendable {
    func fetchUser(id: String) async throws -> User
}

class UserService {
    private let api: UserAPIProtocol
    init(api: UserAPIProtocol) { self.api = api }
}

// In tests:
struct MockUserAPI: UserAPIProtocol {
    var stubResult: User?
    func fetchUser(id: String) async throws -> User {
        guard let result = stubResult else { throw TestError.notStubbed }
        return result
    }
}
```

## Rule 4: No Sleep in Tests

**Rationale:** `Thread.sleep` makes tests slow and flaky. Use proper async mechanisms.

```swift
// ❌ Bad
func testAsyncUpdate() {
    viewModel.load()
    Thread.sleep(forTimeInterval: 1.0)  // Slow, flaky
    XCTAssertTrue(viewModel.isLoaded)
}

// ✅ Good
func testAsyncUpdate() async {
    await viewModel.load()
    XCTAssertTrue(viewModel.isLoaded)
}
```
