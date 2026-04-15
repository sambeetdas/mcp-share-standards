---
name: dotnet-configuration
description: Manage .NET app configuration using Options pattern, IOptions, appsettings, secrets, and environment-specific config. Use when the user works with appsettings.json, configuration classes, IOptions, or secret management.
---

# .NET Configuration

## When to Use

- User adds or modifies `appsettings.json`.
- User asks about Options pattern, secrets, or environment config.
- User creates configuration/settings classes.

## Options Pattern (Preferred)

Always bind config sections to strongly-typed classes:

```csharp
// 1. Define the options class
public class SmtpOptions
{
    public const string SectionName = "Smtp";

    public string Host { get; init; } = string.Empty;
    public int Port { get; init; } = 587;
    public string Username { get; init; } = string.Empty;
    public string Password { get; init; } = string.Empty;
    public bool UseSsl { get; init; } = true;
}

// 2. Register in Program.cs
builder.Services
    .AddOptions<SmtpOptions>()
    .BindConfiguration(SmtpOptions.SectionName)
    .ValidateDataAnnotations()
    .ValidateOnStart();  // Fail fast if config is invalid

// 3. appsettings.json
{
  "Smtp": {
    "Host": "smtp.example.com",
    "Port": 587,
    "Username": "noreply@example.com",
    "Password": "use-user-secrets-instead"
  }
}

// 4. Inject
public class EmailService
{
    private readonly SmtpOptions _options;
    public EmailService(IOptions<SmtpOptions> options)
    {
        _options = options.Value;
    }
}
```

## IOptions Variants

| Interface | Lifetime | Reloads on change? | Use When |
|-----------|----------|---------------------|----------|
| `IOptions<T>` | Singleton | No | Config read once at startup |
| `IOptionsSnapshot<T>` | Scoped | Yes (per request) | Config may change, need per-request values |
| `IOptionsMonitor<T>` | Singleton | Yes (callback) | Singleton services that need live updates |

## Environment-Specific Config

```
appsettings.json                  ← base/shared settings
appsettings.Development.json      ← dev overrides
appsettings.Staging.json          ← staging overrides
appsettings.Production.json       ← production overrides
```

Set `ASPNETCORE_ENVIRONMENT` to control which file loads. Environment-specific files override base.

## Secrets Management

**Development** — Use User Secrets (never commit secrets to source):

```bash
dotnet user-secrets init --project src/SolutionName.Api
dotnet user-secrets set "Smtp:Password" "my-secret-password"
```

**Production** — Use Azure Key Vault, AWS Secrets Manager, or environment variables:

```csharp
builder.Configuration.AddAzureKeyVault(
    new Uri("https://mykeyvault.vault.azure.net/"),
    new DefaultAzureCredential());
```

## Validation

Add data annotations to options classes and validate on start:

```csharp
public class SmtpOptions
{
    [Required, MinLength(1)]
    public string Host { get; init; } = string.Empty;

    [Range(1, 65535)]
    public int Port { get; init; } = 587;
}
```

## Rules

- Never read `IConfiguration` directly in services — use the Options pattern.
- Never commit secrets to `appsettings.json` — use User Secrets or a vault.
- Always validate configuration at startup with `ValidateOnStart()`.
- Use `init` setters on options classes for immutability after binding.
