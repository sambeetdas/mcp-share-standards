---
description: C# naming conventions and identifier standards
globs: **/*.cs
alwaysApply: false
---

# C# Naming Conventions

## General Rules

- Use **meaningful, descriptive names** — avoid abbreviations and single-letter names (except loop counters).
- Names should reveal intent: prefer `customerOrderCount` over `coc`.

## Casing Standards

| Element | Casing | Example |
|---------|--------|---------|
| Namespace | PascalCase | `MyApp.Services` |
| Class / Struct | PascalCase | `CustomerService` |
| Interface | I + PascalCase | `ICustomerRepository` |
| Method | PascalCase | `GetCustomerById()` |
| Property | PascalCase | `FirstName` |
| Public field | PascalCase | `MaxRetryCount` |
| Private field | _camelCase | `_customerRepository` |
| Parameter | camelCase | `orderId` |
| Local variable | camelCase | `totalAmount` |
| Constant | PascalCase | `DefaultTimeout` |
| Enum type | PascalCase (singular) | `OrderStatus` |
| Enum value | PascalCase | `OrderStatus.Pending` |
| Event | PascalCase | `OrderPlaced` |
| Delegate | PascalCase + Handler/Callback | `OrderPlacedHandler` |
| Generic type param | T + PascalCase | `TEntity`, `TResult` |

## Examples

```csharp
// ❌ BAD
public class custSvc
{
    private ICustomerRepository repo;
    public Customer getcust(int id) => repo.Get(id);
}

// ✅ GOOD
public class CustomerService
{
    private readonly ICustomerRepository _customerRepository;
    public Customer GetCustomerById(int customerId) => _customerRepository.GetById(customerId);
}
```

## Boolean Naming

- Prefix booleans with `is`, `has`, `can`, `should`: `isActive`, `hasPermission`, `canEdit`.

## Async Methods

- Suffix async methods with `Async`: `GetCustomerByIdAsync()`.

## Collections

- Use plural nouns: `orders`, `customerNames`, `activeUsers`.
