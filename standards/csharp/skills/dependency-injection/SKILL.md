---
name: dotnet-dependency-injection
description: Guide for registering and organizing services in .NET dependency injection container. Use when the user registers services, asks about service lifetimes (scoped, transient, singleton), or organizes DI in Program.cs.
---

# .NET Dependency Injection

## When to Use

- User registers services in `Program.cs`.
- User asks about service lifetimes or DI patterns.
- User creates new services that need to be registered.

## Service Lifetimes

| Lifetime | When to Use | Example |
|----------|-------------|---------|
| **Transient** | Lightweight, stateless services | Validators, mappers |
| **Scoped** | Per-request state, database contexts | DbContext, repositories, unit of work |
| **Singleton** | Shared state, expensive to create | Cache, HttpClient factory, config |

```csharp
// Transient — new instance every time it's requested
builder.Services.AddTransient<IEmailSender, SmtpEmailSender>();

// Scoped — one instance per HTTP request
builder.Services.AddScoped<IOrderRepository, OrderRepository>();
builder.Services.AddScoped<IUnitOfWork, UnitOfWork>();

// Singleton — one instance for the app's lifetime
builder.Services.AddSingleton<ICacheService, InMemoryCacheService>();
```

## Organize with Extension Methods

Never dump all registrations in `Program.cs`. Group by layer:

```csharp
// In src/SolutionName.Infrastructure/DependencyInjection.cs
public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        services.AddDbContext<AppDbContext>(options =>
            options.UseSqlServer(configuration.GetConnectionString("Default")));

        services.AddScoped<IOrderRepository, OrderRepository>();
        services.AddScoped<ICustomerRepository, CustomerRepository>();
        services.AddScoped<IUnitOfWork, UnitOfWork>();

        return services;
    }
}

// In src/SolutionName.Core/DependencyInjection.cs
public static class DependencyInjection
{
    public static IServiceCollection AddCore(this IServiceCollection services)
    {
        services.AddScoped<IOrderService, OrderService>();
        services.AddScoped<ICustomerService, CustomerService>();
        return services;
    }
}

// In Program.cs — clean and readable
builder.Services.AddCore();
builder.Services.AddInfrastructure(builder.Configuration);
```

## Constructor Injection

Always inject dependencies through the constructor and store them in `private readonly` fields. Never use `new` to create dependencies inside a class.

```csharp
// Inject via constructor — the correct way
public class OrderController : Controller
{
    private readonly IOrderService _orderService;
    private readonly ICustomerService _customerService;

    public OrderController(IOrderService orderService, ICustomerService customerService)
    {
        _orderService = orderService;
        _customerService = customerService;
    }

    public async Task<IActionResult> Index()
    {
        var orders = await _orderService.GetRecentOrdersAsync();
        return View(orders);
    }

    public async Task<IActionResult> Details(int id)
    {
        var order = await _orderService.GetByIdAsync(id);
        if (order is null)
        {
            return NotFound();
        }

        var customer = await _customerService.GetByIdAsync(order.CustomerId);
        ViewData["CustomerName"] = customer?.Name;
        return View(order);
    }
}
```

**Why this pattern works:**

- The controller depends on `IOrderService` and `ICustomerService`, not concrete classes — easy to mock in tests.
- `private readonly` prevents accidental reassignment.
- The DI container resolves and injects `OrderService` and `CustomerService` automatically at runtime.
- Swapping implementations (e.g., for testing) only requires changing the registration.

## Common Patterns

### Decorator Pattern

```csharp
// Register base then decorate
builder.Services.AddScoped<IOrderService, OrderService>();
builder.Services.Decorate<IOrderService, CachedOrderService>();
builder.Services.Decorate<IOrderService, LoggingOrderService>();
// Resolution order: Logging → Cache → OrderService
```

Requires `Scrutor` NuGet package for `.Decorate<>()`.

### Factory Pattern

```csharp
builder.Services.AddSingleton<IPaymentGatewayFactory, PaymentGatewayFactory>();
// Factory creates the right gateway based on runtime config
```

### Keyed Services (.NET 8+)

```csharp
builder.Services.AddKeyedScoped<INotificationService, EmailNotificationService>("email");
builder.Services.AddKeyedScoped<INotificationService, SmsNotificationService>("sms");

// Inject with [FromKeyedServices("email")] INotificationService emailService
```

## Rules

- **Never** resolve services with `IServiceProvider.GetService()` in business logic (Service Locator anti-pattern).
- **Never** inject `Scoped` into `Singleton` — causes captive dependency.
- **Always** register interfaces, not concrete types.
- **Always** use constructor injection.
- Validate DI at startup: `builder.Host.UseDefaultServiceProvider(o => o.ValidateOnBuild = true);`
