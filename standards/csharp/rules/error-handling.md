---
description: C# error handling patterns and exception standards
globs: **/*.cs
alwaysApply: false
---

# C# Error Handling

## Core Principles

- **Never swallow exceptions** — always log or rethrow.
- **Catch specific exceptions** — never catch bare `Exception` unless at a top-level boundary.
- **Fail fast** — validate inputs early with guard clauses.
- **Use exceptions for exceptional cases**, not for control flow.

## Guard Clauses

```csharp
// ✅ GOOD — validate early, fail fast
public Order GetOrder(int orderId)
{
    ArgumentOutOfRangeException.ThrowIfNegativeOrZero(orderId);
    // ... logic
}

public void ProcessCustomer(Customer customer)
{
    ArgumentNullException.ThrowIfNull(customer);
    // ... logic
}
```

## Exception Handling

```csharp
// ❌ BAD — empty catch, bare Exception, loses stack trace
try { Save(order); }
catch (Exception ex) { }

// ❌ BAD — throw ex resets stack trace
catch (SqlException ex) { throw ex; }

// ✅ GOOD — catch specific, log, rethrow with context
try
{
    await _repository.SaveAsync(order);
}
catch (DbUpdateException ex)
{
    _logger.LogError(ex, "Failed to save order {OrderId}", order.Id);
    throw;  // preserves stack trace
}
```

## Custom Exceptions

- Create domain-specific exceptions inheriting from `Exception`.
- Include relevant context in the message.

```csharp
public class OrderNotFoundException : Exception
{
    public int OrderId { get; }
    public OrderNotFoundException(int orderId)
        : base($"Order with ID {orderId} was not found.")
    {
        OrderId = orderId;
    }
}
```

## Result Pattern (Alternative to Exceptions)

For expected failures (validation, business rules), prefer a Result pattern over exceptions:

```csharp
public Result<Order> PlaceOrder(OrderRequest request)
{
    if (!request.IsValid)
        return Result<Order>.Failure("Invalid order request.");

    var order = CreateOrder(request);
    return Result<Order>.Success(order);
}
```

## What NOT to Do

- ❌ Don't use `try/catch` for control flow.
- ❌ Don't catch `Exception` in library/service code.
- ❌ Don't log and rethrow the same exception at multiple layers (log once at the boundary).
- ❌ Don't return null to indicate failure — use the Result pattern or throw.
