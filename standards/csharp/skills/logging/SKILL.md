---
name: dotnet-logging
description: Structured logging standards using ILogger, Serilog, and Application Insights. Use when the user adds logging, asks about log levels, structured logging, correlation IDs, or configures Serilog.
---

# .NET Logging

## When to Use

- User adds logging to a service or controller.
- User sets up Serilog or Application Insights.
- User asks about log levels, structured logging, or correlation.

## Standard Setup with Serilog

```csharp
// Program.cs
builder.Host.UseSerilog((context, config) => config
    .ReadFrom.Configuration(context.Configuration)
    .Enrich.FromLogContext()
    .Enrich.WithProperty("Application", "SolutionName.Api")
    .WriteTo.Console()
    .WriteTo.Seq("http://localhost:5341")); // or ApplicationInsights

app.UseSerilogRequestLogging();
```

## Using ILogger

Always inject `ILogger<T>` — never create loggers manually.

```csharp
public class OrderService
{
    private readonly ILogger<OrderService> _logger;

    public OrderService(ILogger<OrderService> logger)
    {
        _logger = logger;
    }

    public async Task<Order> GetByIdAsync(int orderId, CancellationToken ct)
    {
        _logger.LogInformation("Retrieving order {OrderId}", orderId);

        var order = await _repository.GetByIdAsync(orderId, ct);

        if (order is null)
        {
            _logger.LogWarning("Order {OrderId} not found", orderId);
            throw new OrderNotFoundException(orderId);
        }

        return order;
    }
}
```

## Log Levels

| Level | When to Use |
|-------|-------------|
| `Trace` | Detailed diagnostic info (never in production) |
| `Debug` | Development diagnostics |
| `Information` | Normal operations: request started, order placed |
| `Warning` | Something unexpected but not broken: missing optional config, retry |
| `Error` | Operation failed: unhandled exception, external service down |
| `Critical` | App is crashing: out of memory, data corruption |

## Structured Logging Rules

```csharp
// ✅ GOOD — structured with named placeholders (searchable properties)
_logger.LogInformation("Order {OrderId} placed by {CustomerId} for {Total:C}", orderId, customerId, total);

// ❌ BAD — string interpolation (not structured, not searchable)
_logger.LogInformation($"Order {orderId} placed by {customerId} for {total:C}");
```

- Use **PascalCase** for placeholder names: `{OrderId}`, not `{orderId}`.
- Never log sensitive data: passwords, tokens, PII.
- Include context (IDs, counts, durations), not raw objects.

## Correlation IDs

Add a middleware or use Serilog's `CorrelationId` enricher:

```csharp
app.Use(async (context, next) =>
{
    var correlationId = context.Request.Headers["X-Correlation-Id"].FirstOrDefault()
        ?? Guid.NewGuid().ToString();
    context.Response.Headers["X-Correlation-Id"] = correlationId;

    using (LogContext.PushProperty("CorrelationId", correlationId))
    {
        await next();
    }
});
```

## What NOT to Do

- Never use `Console.WriteLine` for logging.
- Never log entire request/response bodies (performance + security).
- Never use string interpolation (`$""`) in log messages.
- Never log at `Information` level inside tight loops.
