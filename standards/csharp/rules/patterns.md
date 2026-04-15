---
description: C# recommended patterns and anti-patterns to avoid
globs: **/*.cs
alwaysApply: false
---

# C# Patterns & Anti-Patterns

## Recommended Patterns

### Dependency Injection

Always inject dependencies via constructor. Never use `new` for services.

```csharp
// ❌ BAD — hard-coded dependency
public class OrderService
{
    private readonly CustomerRepository _repo = new CustomerRepository();
}

// ✅ GOOD — injected interface
public class OrderService
{
    private readonly ICustomerRepository _customerRepository;

    public OrderService(ICustomerRepository customerRepository)
    {
        _customerRepository = customerRepository ?? throw new ArgumentNullException(nameof(customerRepository));
    }
}
```

### Immutability

- Use `record` types for DTOs and value objects.
- Prefer `init` over `set` for properties that shouldn't change after creation.
- Use `readonly` on fields wherever possible.

```csharp
// ✅ GOOD
public record OrderResponse(int Id, decimal Total, DateTime CreatedAt);
```

### Async/Await

- Use `async/await` all the way down — never mix sync and async (no `.Result` or `.Wait()`).
- Accept `CancellationToken` in async methods and pass it through.

```csharp
// ❌ BAD — blocking async call
var order = _repository.GetOrderAsync(id).Result;

// ✅ GOOD
var order = await _repository.GetOrderAsync(id, cancellationToken);
```

### LINQ

- Prefer LINQ method syntax for simple queries, query syntax for complex joins.
- Never use LINQ in hot loops — prefer `for` loops for performance-critical code.

### Null Safety

- Enable `<Nullable>enable</Nullable>` in all projects.
- Use null-conditional (`?.`) and null-coalescing (`??`, `??=`) operators.
- Avoid returning `null` from methods — use `Result<T>` or `Option<T>` patterns.

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Do This Instead |
|--------------|--------------|-----------------|
| Service Locator | Hides dependencies, hard to test | Constructor injection |
| God Class (>500 lines) | Violates SRP, hard to maintain | Split into focused classes |
| Magic strings/numbers | Fragile, no compiler help | Use `const`, `enum`, or config |
| Static helper classes with state | Hidden coupling, untestable | Use injected services |
| Deep inheritance (>2 levels) | Fragile, hard to reason about | Prefer composition over inheritance |
| `public` fields | Breaks encapsulation | Use properties |
| `async void` | Exceptions are unobservable | Use `async Task` |

## SOLID Principles

- **S**ingle Responsibility — one reason to change per class.
- **O**pen/Closed — open for extension, closed for modification.
- **L**iskov Substitution — subtypes must be substitutable for base types.
- **I**nterface Segregation — prefer small, focused interfaces.
- **D**ependency Inversion — depend on abstractions, not concretions.
