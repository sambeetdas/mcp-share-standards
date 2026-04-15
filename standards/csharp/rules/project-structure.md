---
description: C# project file and folder structure conventions
alwaysApply: true
---

# C# Project Structure

## Solution Layout

```
SolutionName/
├── src/
│   ├── SolutionName.Api/            # API / entry point
│   ├── SolutionName.Core/           # Domain models, interfaces, business logic
│   ├── SolutionName.Infrastructure/ # Data access, external services, implementations
│   └── SolutionName.Shared/         # Cross-cutting concerns, DTOs, utilities
├── tests/
│   ├── SolutionName.UnitTests/
│   ├── SolutionName.IntegrationTests/
│   └── SolutionName.FunctionalTests/
├── docs/
├── SolutionName.sln
└── README.md
```

## Folder Conventions Inside a Project

- **One class per file** — file name must match the class name (`CustomerService.cs` → `class CustomerService`).
- **Group by feature/domain**, not by type. Prefer `Features/Orders/` over `Services/`, `Repositories/`, etc.
- **Interfaces** live alongside their implementations, or in a shared `Abstractions/` folder.
- **DTOs / ViewModels** go in a `Models/` or `Contracts/` folder.
- **Extensions** go in an `Extensions/` folder.
- **Constants** go in a `Constants/` folder or class.

## Namespace Convention

- Namespaces must mirror the folder path: `SolutionName.Core.Features.Orders`.
- Never use a namespace that doesn't match the folder location.

## What NOT to Do

- ❌ Don't put multiple unrelated classes in one file.
- ❌ Don't create deeply nested folder hierarchies (max 4 levels).
- ❌ Don't place business logic in the API/controller layer.
