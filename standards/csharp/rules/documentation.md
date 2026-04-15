---
description: C# documentation and comment style standards
globs: **/*.cs
alwaysApply: false
---

# C# Documentation & Comments

## XML Documentation (Required)

Add XML docs to all **public** and **protected** members:

```csharp
// ✅ GOOD
/// <summary>
/// Retrieves an order by its unique identifier.
/// </summary>
/// <param name="orderId">The unique identifier of the order.</param>
/// <returns>The order if found; otherwise throws <see cref="OrderNotFoundException"/>.</returns>
/// <exception cref="OrderNotFoundException">Thrown when no order matches the given ID.</exception>
public async Task<Order> GetOrderByIdAsync(int orderId) { }
```

## When to Use XML Docs

| Member | Required? |
|--------|-----------|
| Public class / struct / interface | Yes |
| Public / protected method | Yes |
| Public property (non-obvious) | Yes |
| Public property (self-evident like `Id`, `Name`) | Optional |
| Private / internal members | No — only if logic is complex |

## Inline Comments

- **Explain WHY, not WHAT** — the code shows what, comments explain why.
- Place comments on the line above the code, not inline.

```csharp
// ❌ BAD — explains what (obvious from the code)
// Increment counter by one
counter++;

// ✅ GOOD — explains why
// Retry count is offset by 1 because the initial attempt is not counted
counter++;
```

## TODO / HACK / FIXME

- Use `// TODO:` for planned work with a brief description.
- Use `// HACK:` for temporary workarounds — include reason and ticket number.
- Use `// FIXME:` for known bugs that need attention.

```csharp
// TODO: Replace with bulk insert for performance (JIRA-1234)
// HACK: Workaround for EF Core issue #12345 — remove after upgrading to v9
// FIXME: Race condition when concurrent orders target same inventory (BUG-567)
```

## File Headers

Not required. Avoid boilerplate copyright headers unless mandated by legal/compliance.

## What NOT to Do

- ❌ Don't write comments that restate the code.
- ❌ Don't leave commented-out code — delete it (use source control).
- ❌ Don't write novel-length comments — keep them concise.
