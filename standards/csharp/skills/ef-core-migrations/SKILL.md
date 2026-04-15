---
name: ef-core-migrations
description: Guide Entity Framework Core migration workflows including creating, applying, reverting, and troubleshooting migrations. Use when the user works with EF Core, database migrations, DbContext, or asks about schema changes.
---

# EF Core Migrations

## When to Use

- User adds/modifies entity models or DbContext.
- User asks to create, apply, revert, or fix migrations.
- User asks about database schema changes.

## Prerequisites

Ensure the EF Core tools are installed:

```bash
dotnet tool install --global dotnet-ef
# or update
dotnet tool update --global dotnet-ef
```

## Common Workflows

### Create a Migration

```bash
dotnet ef migrations add MigrationName \
  --project src/SolutionName.Infrastructure \
  --startup-project src/SolutionName.Api
```

**Naming convention**: Use descriptive PascalCase names:
- `AddCustomerTable`
- `AddOrderStatusColumn`
- `RenameEmailToEmailAddress`

### Apply Migrations

```bash
# Apply all pending migrations
dotnet ef database update \
  --project src/SolutionName.Infrastructure \
  --startup-project src/SolutionName.Api

# Apply up to a specific migration
dotnet ef database update MigrationName \
  --project src/SolutionName.Infrastructure \
  --startup-project src/SolutionName.Api
```

### Revert a Migration

```bash
# Revert to a previous migration (unapplies newer ones)
dotnet ef database update PreviousMigrationName \
  --project src/SolutionName.Infrastructure \
  --startup-project src/SolutionName.Api

# Remove the last unapplied migration file
dotnet ef migrations remove \
  --project src/SolutionName.Infrastructure \
  --startup-project src/SolutionName.Api
```

### Generate SQL Script (for production)

```bash
dotnet ef migrations script \
  --idempotent \
  --project src/SolutionName.Infrastructure \
  --startup-project src/SolutionName.Api \
  --output migrations.sql
```

Always use `--idempotent` for production scripts.

## Best Practices

1. **Review every migration** — check the generated `Up()` and `Down()` methods before applying.
2. **Never edit applied migrations** — create a new migration instead.
3. **Keep migrations small** — one logical change per migration.
4. **Seed data** in a separate migration or `DbContext.OnModelCreating`, not in application code.
5. **Test Down()** — ensure rollback works by reverting and reapplying.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No migrations found" | Check `--project` points to the project containing DbContext |
| "Build failed" | Fix compilation errors before running ef commands |
| Empty migration generated | Ensure changes are in entities tracked by DbContext |
| Migration conflict after merge | Remove conflicting migration, rebuild model snapshot, re-add |

## Data Loss Prevention

Before applying migrations that drop columns/tables:

1. Back up the database.
2. Check the `Up()` method for `DropColumn` / `DropTable`.
3. If data preservation is needed, add data migration logic in the `Up()` method before dropping.
