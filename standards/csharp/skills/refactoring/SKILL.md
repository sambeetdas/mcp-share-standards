---
name: csharp-refactoring
description: Common C# refactoring recipes for improving code structure, removing code smells, and applying design patterns. Use when the user asks to refactor, clean up, improve, or restructure C# code.
---

# C# Refactoring

## When to Use

- User asks to refactor, clean up, or improve code.
- User asks to remove code smells or apply a design pattern.
- Code review identified structural issues.

## Refactoring Workflow

1. **Identify** the code smell or improvement opportunity.
2. **Verify tests exist** — if not, add tests first to protect against regressions.
3. **Apply** the refactoring in small, incremental steps.
4. **Run tests** after each step to confirm nothing broke.

## Common Refactoring Recipes

### Extract Method

When a method is too long or does multiple things:

```csharp
// ❌ Before — method does too much
public async Task<OrderResult> PlaceOrderAsync(OrderRequest request)
{
    // 20 lines of validation...
    // 15 lines of inventory check...
    // 10 lines of payment processing...
    // 10 lines of notification...
}

// ✅ After — each concern in its own method
public async Task<OrderResult> PlaceOrderAsync(OrderRequest request)
{
    ValidateOrder(request);
    await ReserveInventoryAsync(request.Items);
    var payment = await ProcessPaymentAsync(request.Payment);
    await SendOrderConfirmationAsync(request.CustomerEmail, payment);
    return new OrderResult(payment.OrderId);
}
```

### Replace Inheritance with Composition

When inheritance hierarchies become deep or rigid:

```csharp
// ❌ Before — fragile inheritance
public class PremiumCustomer : Customer { ... }
public class VipCustomer : PremiumCustomer { ... }

// ✅ After — flexible composition
public class Customer
{
    public IPricingStrategy PricingStrategy { get; init; }
    public IReadOnlyList<IBenefit> Benefits { get; init; }
}
```

### Introduce Parameter Object

When methods have many parameters:

```csharp
// ❌ Before
public Order CreateOrder(string name, string email, string address, string city, string zip, string country)

// ✅ After
public record ShippingInfo(string Name, string Email, string Address, string City, string Zip, string Country);
public Order CreateOrder(ShippingInfo shipping)
```

### Replace Magic Values with Constants/Enums

```csharp
// ❌ Before
if (order.Status == 3) { }
if (retryCount > 5) { }

// ✅ After
if (order.Status == OrderStatus.Shipped) { }
if (retryCount > MaxRetryAttempts) { }
```

### Replace Conditional with Polymorphism

```csharp
// ❌ Before — switch on type
public decimal CalculateDiscount(Customer customer)
{
    switch (customer.Tier)
    {
        case "Gold": return 0.15m;
        case "Silver": return 0.10m;
        default: return 0.0m;
    }
}

// ✅ After — polymorphism via strategy
public interface IDiscountStrategy
{
    decimal Calculate(Order order);
}

public class GoldDiscount : IDiscountStrategy
{
    public decimal Calculate(Order order) => order.Total * 0.15m;
}
```

### Convert to Records

For immutable data types:

```csharp
// ❌ Before — mutable class with boilerplate
public class OrderResponse
{
    public int Id { get; set; }
    public decimal Total { get; set; }
    // + Equals, GetHashCode, ToString overrides
}

// ✅ After — record with value equality built in
public record OrderResponse(int Id, decimal Total);
```

## Code Smell Detection

| Smell | Symptom | Refactoring |
|-------|---------|-------------|
| Long Method (>30 lines) | Hard to read/test | Extract Method |
| God Class (>500 lines) | Too many responsibilities | Extract Class |
| Feature Envy | Method uses another class's data more than its own | Move Method |
| Primitive Obsession | Using strings/ints where a value object fits | Introduce Value Object |
| Shotgun Surgery | One change requires editing many files | Extract shared logic |
| Long Parameter List (>3 params) | Hard to call correctly | Introduce Parameter Object |

## Rules

- Always have tests before refactoring.
- Make one refactoring at a time — don't combine with new features.
- Run tests after each change.
- Keep commits small and focused.
