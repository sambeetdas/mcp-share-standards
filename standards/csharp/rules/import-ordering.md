---
description: C# using directive ordering conventions
globs: **/*.cs
alwaysApply: false
---

# C# Using Directive Ordering

## Placement

- All `using` directives go **at the top of the file**, outside the namespace.
- Use **global usings** in a `GlobalUsings.cs` file for commonly used namespaces.

## Ordering Rules

Order `using` directives in these groups, separated by a blank line:

1. **System namespaces** (`System.*`)
2. **Third-party namespaces** (NuGet packages)
3. **Project namespaces** (your solution)
4. **Static usings**
5. **Aliases**

```csharp
// ✅ GOOD
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

using MyApp.Core.Models;
using MyApp.Infrastructure.Repositories;

using static System.Math;

using OrderDto = MyApp.Api.Contracts.OrderResponse;
```

## Global Usings

Place in a single `GlobalUsings.cs` at project root:

```csharp
// GlobalUsings.cs
global using System;
global using System.Collections.Generic;
global using System.Linq;
global using System.Threading;
global using System.Threading.Tasks;
```

## What NOT to Do

- ❌ Don't leave unused `using` directives — remove them.
- ❌ Don't mix ordering groups without blank-line separators.
- ❌ Don't place `using` directives inside namespace declarations.
