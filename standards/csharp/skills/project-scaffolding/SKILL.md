---
name: dotnet-project-scaffolding
description: Scaffold new .NET projects with correct structure, NuGet packages, and boilerplate. Use when the user asks to create a new project, add a class library, set up a new API, or initialize a .NET solution.
---

# .NET Project Scaffolding

## When to Use

- User asks to create a new .NET project, solution, API, or class library.
- User asks to add a new project to an existing solution.

## Solution Structure

Always follow this layout:

```
SolutionName/
├── src/
│   ├── SolutionName.Api/
│   ├── SolutionName.Core/
│   ├── SolutionName.Infrastructure/
│   └── SolutionName.Shared/
├── tests/
│   ├── SolutionName.UnitTests/
│   ├── SolutionName.IntegrationTests/
│   └── SolutionName.FunctionalTests/
├── SolutionName.sln
└── README.md
```

## Step-by-Step Workflow

### 1. Create the Solution

```bash
dotnet new sln -n SolutionName
mkdir src tests
```

### 2. Create Projects

```bash
# API / Entry point
dotnet new webapi -n SolutionName.Api -o src/SolutionName.Api

# Core (domain models, interfaces, business logic)
dotnet new classlib -n SolutionName.Core -o src/SolutionName.Core

# Infrastructure (data access, external services)
dotnet new classlib -n SolutionName.Infrastructure -o src/SolutionName.Infrastructure

# Shared (DTOs, utilities, cross-cutting)
dotnet new classlib -n SolutionName.Shared -o src/SolutionName.Shared

# Tests
dotnet new xunit -n SolutionName.UnitTests -o tests/SolutionName.UnitTests
dotnet new xunit -n SolutionName.IntegrationTests -o tests/SolutionName.IntegrationTests
```

### 3. Add Projects to Solution

```bash
dotnet sln add src/SolutionName.Api
dotnet sln add src/SolutionName.Core
dotnet sln add src/SolutionName.Infrastructure
dotnet sln add src/SolutionName.Shared
dotnet sln add tests/SolutionName.UnitTests
dotnet sln add tests/SolutionName.IntegrationTests
```

### 4. Add Project References

```bash
# Api depends on Core and Infrastructure
dotnet add src/SolutionName.Api reference src/SolutionName.Core
dotnet add src/SolutionName.Api reference src/SolutionName.Infrastructure

# Infrastructure depends on Core
dotnet add src/SolutionName.Infrastructure reference src/SolutionName.Core

# Tests depend on the projects they test
dotnet add tests/SolutionName.UnitTests reference src/SolutionName.Core
dotnet add tests/SolutionName.UnitTests reference src/SolutionName.Infrastructure
```

### 5. Add Standard NuGet Packages

```bash
# Infrastructure
dotnet add src/SolutionName.Infrastructure package Microsoft.EntityFrameworkCore
dotnet add src/SolutionName.Infrastructure package Microsoft.EntityFrameworkCore.SqlServer

# Api
dotnet add src/SolutionName.Api package Serilog.AspNetCore
dotnet add src/SolutionName.Api package Swashbuckle.AspNetCore

# Tests
dotnet add tests/SolutionName.UnitTests package Moq
dotnet add tests/SolutionName.UnitTests package FluentAssertions
```

### 6. Add GlobalUsings.cs

Create `GlobalUsings.cs` in each project with commonly used namespaces.

### 7. Verify

```bash
dotnet build
dotnet test
```

## Notes

- Replace `SolutionName` with the actual project name provided by the user.
- Ask the user which database provider they want if creating Infrastructure.
- Always enable nullable reference types: `<Nullable>enable</Nullable>` in all `.csproj` files.
- Use .NET 8+ unless the user specifies otherwise.
