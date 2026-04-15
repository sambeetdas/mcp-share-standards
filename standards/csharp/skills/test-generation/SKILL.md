---
name: dotnet-test-generation
description: Generate unit tests for C# classes using xUnit, Moq, and FluentAssertions. Use when the user asks to create tests, generate test cases, or add test coverage for a C# class.
---

# .NET Test Generation

## When to Use

- User asks to generate, create, or write tests for a class or method.
- User asks to add test coverage.

## Workflow

1. **Read the source class** to understand public methods, dependencies, and behavior.
2. **Identify the test project** — should mirror the source structure.
3. **Generate the test class** following the template below.
4. **Cover all scenarios**: happy path, edge cases, error cases, boundary values.
5. **Verify** tests compile and pass.

## Test Class Template

```csharp
using FluentAssertions;
using Moq;
using Xunit;

namespace SolutionName.UnitTests.Services;

public class OrderServiceTests
{
    private readonly Mock<IOrderRepository> _mockRepository;
    private readonly Mock<ILogger<OrderService>> _mockLogger;
    private readonly OrderService _sut; // System Under Test

    public OrderServiceTests()
    {
        _mockRepository = new Mock<IOrderRepository>();
        _mockLogger = new Mock<ILogger<OrderService>>();
        _sut = new OrderService(_mockRepository.Object, _mockLogger.Object);
    }

    [Fact]
    public async Task GetByIdAsync_WithValidId_ReturnsOrder()
    {
        // Arrange
        var expected = new Order { Id = 1, Total = 99.99m };
        _mockRepository
            .Setup(r => r.GetByIdAsync(1, It.IsAny<CancellationToken>()))
            .ReturnsAsync(expected);

        // Act
        var result = await _sut.GetByIdAsync(1, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result.Id.Should().Be(1);
        result.Total.Should().Be(99.99m);
    }

    [Fact]
    public async Task GetByIdAsync_WithInvalidId_ThrowsNotFoundException()
    {
        // Arrange
        _mockRepository
            .Setup(r => r.GetByIdAsync(999, It.IsAny<CancellationToken>()))
            .ReturnsAsync((Order?)null);

        // Act
        var act = () => _sut.GetByIdAsync(999, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<OrderNotFoundException>()
            .WithMessage("*999*");
    }

    [Theory]
    [InlineData(0)]
    [InlineData(-1)]
    [InlineData(-100)]
    public async Task GetByIdAsync_WithInvalidId_ThrowsArgumentException(int invalidId)
    {
        // Act
        var act = () => _sut.GetByIdAsync(invalidId, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<ArgumentOutOfRangeException>();
    }
}
```

## Test Case Generation Strategy

For each public method, generate tests for:

| Category | Examples |
|----------|----------|
| **Happy path** | Valid input returns expected result |
| **Null/empty input** | Null arguments throw `ArgumentNullException` |
| **Boundary values** | 0, -1, int.MaxValue, empty string, whitespace |
| **Not found** | Entity doesn't exist → exception or failure result |
| **Dependency failure** | Repository throws → service handles correctly |
| **Business rules** | Rule violations return proper errors |

## Naming Convention

`MethodName_Scenario_ExpectedBehavior`

```
GetByIdAsync_WithValidId_ReturnsOrder
GetByIdAsync_WithNullId_ThrowsArgumentNullException
CreateAsync_WhenRepositoryFails_ThrowsAndLogs
PlaceOrderAsync_WithInsufficientStock_ReturnsFailureResult
```

## Mocking Patterns

### Mock returning a value
```csharp
_mock.Setup(x => x.GetAsync(It.IsAny<int>(), It.IsAny<CancellationToken>()))
     .ReturnsAsync(expectedValue);
```

### Mock throwing an exception
```csharp
_mock.Setup(x => x.SaveAsync(It.IsAny<Order>(), It.IsAny<CancellationToken>()))
     .ThrowsAsync(new DbUpdateException("DB error"));
```

### Verify a method was called
```csharp
_mock.Verify(x => x.SaveAsync(It.Is<Order>(o => o.Id == 1), It.IsAny<CancellationToken>()), Times.Once);
```

### Verify a method was NOT called
```csharp
_mock.Verify(x => x.SendEmailAsync(It.IsAny<string>()), Times.Never);
```

## FluentAssertions Cheat Sheet

```csharp
result.Should().Be(expected);
result.Should().NotBeNull();
result.Should().BeEquivalentTo(expected);     // deep comparison
list.Should().HaveCount(3);
list.Should().Contain(x => x.Id == 1);
act.Should().Throw<InvalidOperationException>().WithMessage("*keyword*");
result.Should().BeInRange(1, 100);
```

## Rules

- One test class per production class.
- Use `_sut` for the System Under Test.
- AAA pattern in every test (Arrange / Act / Assert).
- `[Fact]` for single cases, `[Theory]` + `[InlineData]` for parameterized.
- Mock all dependencies — never use real databases or services.
- Test behavior, not implementation details.
