---
name: dotnet-api-design
description: Design and build REST APIs in ASP.NET Core with proper controller structure, DTOs, validation, error responses, pagination, and Swagger docs. Use when the user creates API endpoints, controllers, or asks about API design.
---

# .NET API Design

## When to Use

- User asks to create or modify API endpoints / controllers.
- User asks about REST API design, validation, or error handling in APIs.

## Controller Structure

```csharp
[ApiController]
[Route("api/[controller]")]
[Produces("application/json")]
public class OrdersController : ControllerBase
{
    private readonly IOrderService _orderService;

    public OrdersController(IOrderService orderService)
    {
        _orderService = orderService;
    }

    /// <summary>
    /// Get an order by ID.
    /// </summary>
    [HttpGet("{id:int}")]
    [ProducesResponseType(typeof(OrderResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(typeof(ProblemDetails), StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetById(int id, CancellationToken ct)
    {
        var order = await _orderService.GetByIdAsync(id, ct);
        return order is null ? NotFound() : Ok(order.ToResponse());
    }

    [HttpPost]
    [ProducesResponseType(typeof(OrderResponse), StatusCodes.Status201Created)]
    [ProducesResponseType(typeof(ValidationProblemDetails), StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> Create([FromBody] CreateOrderRequest request, CancellationToken ct)
    {
        var order = await _orderService.CreateAsync(request, ct);
        return CreatedAtAction(nameof(GetById), new { id = order.Id }, order.ToResponse());
    }
}
```

## Conventions

- **Route naming**: plural nouns (`/api/orders`, not `/api/order`).
- **HTTP verbs**: `GET` = read, `POST` = create, `PUT` = full update, `PATCH` = partial update, `DELETE` = remove.
- **Always accept `CancellationToken`** as the last parameter.
- **Return `IActionResult`** for flexibility in status codes.
- **Use `[ApiController]`** attribute for automatic model validation.

## Request / Response DTOs

Never expose domain entities directly. Use separate DTOs:

```csharp
// Request
public record CreateOrderRequest(string CustomerName, List<OrderItemRequest> Items);
public record OrderItemRequest(int ProductId, int Quantity);

// Response
public record OrderResponse(int Id, string CustomerName, decimal Total, DateTime CreatedAt);
```

## Validation with FluentValidation

```csharp
public class CreateOrderRequestValidator : AbstractValidator<CreateOrderRequest>
{
    public CreateOrderRequestValidator()
    {
        RuleFor(x => x.CustomerName).NotEmpty().MaximumLength(200);
        RuleFor(x => x.Items).NotEmpty();
        RuleForEach(x => x.Items).ChildRules(item =>
        {
            item.RuleFor(i => i.ProductId).GreaterThan(0);
            item.RuleFor(i => i.Quantity).InclusiveBetween(1, 1000);
        });
    }
}
```

## Error Responses — ProblemDetails

Use RFC 7807 `ProblemDetails` for all error responses:

```csharp
// In Program.cs
builder.Services.AddProblemDetails();

// Custom exception handler middleware maps exceptions to ProblemDetails
app.UseExceptionHandler();
app.UseStatusCodePages();
```

## Pagination

```csharp
public record PagedRequest(int Page = 1, int PageSize = 20);
public record PagedResponse<T>(IReadOnlyList<T> Items, int TotalCount, int Page, int PageSize);
```

## API Versioning

```csharp
builder.Services.AddApiVersioning(options =>
{
    options.DefaultApiVersion = new ApiVersion(1, 0);
    options.AssumeDefaultVersionWhenUnspecified = true;
    options.ReportApiVersions = true;
});
```

## Checklist for New Endpoints

- [ ] Correct HTTP verb and route
- [ ] Request/Response DTOs (not domain entities)
- [ ] FluentValidation validator for request
- [ ] `CancellationToken` accepted
- [ ] `ProducesResponseType` attributes for Swagger
- [ ] XML doc comment on the action
- [ ] Unit test covering happy path + error cases
