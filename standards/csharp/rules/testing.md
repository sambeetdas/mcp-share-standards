---
description: C# testing requirements and conventions
globs: **/*Test*.cs
alwaysApply: false
---

# C# Testing Standards

## Framework Stack

- **Test Framework**: xUnit (preferred) or NUnit.
- **Mocking**: Moq or NSubstitute.
- **Assertions**: FluentAssertions for readable assertions.

## Test Naming

Use the pattern: `MethodName_Scenario_ExpectedBehavior`

```csharp
// ✅ GOOD
public void GetOrderById_WithValidId_ReturnsOrder() { }
public void GetOrderById_WithInvalidId_ThrowsOrderNotFoundException() { }
public async Task PlaceOrderAsync_WhenInventoryInsufficient_ReturnsFailureResult() { }

// ❌ BAD
public void Test1() { }
public void GetOrderTest() { }
```

## Test Structure — Arrange / Act / Assert

Every test must follow AAA:

```csharp
[Fact]
public async Task GetOrderByIdAsync_WithValidId_ReturnsOrder()
{
    // Arrange
    var expectedOrder = new Order { Id = 1, Total = 99.99m };
    _mockRepository.Setup(r => r.GetByIdAsync(1)).ReturnsAsync(expectedOrder);

    // Act
    var result = await _sut.GetOrderByIdAsync(1);

    // Assert
    result.Should().NotBeNull();
    result.Id.Should().Be(1);
    result.Total.Should().Be(99.99m);
}
```

## Test Organization

- Mirror the source project structure in the test project.
- One test class per production class: `CustomerService` → `CustomerServiceTests`.
- Use nested classes to group related tests if a class has many methods.

## Requirements

- All public methods in service/domain classes must have unit tests.
- Cover: happy path, edge cases, error cases, boundary values.
- Tests must be independent — no shared mutable state between tests.
- Use `[Fact]` for single-case tests, `[Theory]` + `[InlineData]` for parameterized tests.

## What NOT to Do

- ❌ Don't test private methods directly — test through public API.
- ❌ Don't depend on test execution order.
- ❌ Don't use production databases or external services in unit tests.
- ❌ Don't write tests with multiple unrelated assertions (test one behavior per test).
