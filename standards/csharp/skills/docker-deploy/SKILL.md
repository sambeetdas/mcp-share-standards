---
name: dotnet-docker-deploy
description: Create production-ready Dockerfiles, docker-compose setups, and container configurations for .NET applications. Use when the user asks about Docker, containerization, or deployment of .NET apps.
---

# .NET Docker Deployment

## When to Use

- User asks to dockerize a .NET application.
- User asks about Dockerfile, docker-compose, or container setup.

## Multi-Stage Dockerfile

```dockerfile
# Stage 1: Build
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy csproj files and restore (layer caching)
COPY ["src/SolutionName.Api/SolutionName.Api.csproj", "src/SolutionName.Api/"]
COPY ["src/SolutionName.Core/SolutionName.Core.csproj", "src/SolutionName.Core/"]
COPY ["src/SolutionName.Infrastructure/SolutionName.Infrastructure.csproj", "src/SolutionName.Infrastructure/"]
RUN dotnet restore "src/SolutionName.Api/SolutionName.Api.csproj"

# Copy everything and build
COPY . .
RUN dotnet publish "src/SolutionName.Api/SolutionName.Api.csproj" \
    -c Release -o /app/publish --no-restore

# Stage 2: Runtime
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime
WORKDIR /app

# Security: run as non-root
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

COPY --from=build /app/publish .

EXPOSE 8080
ENV ASPNETCORE_URLS=http://+:8080
ENV ASPNETCORE_ENVIRONMENT=Production

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

ENTRYPOINT ["dotnet", "SolutionName.Api.dll"]
```

## Docker Compose

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      - ASPNETCORE_ENVIRONMENT=Development
      - ConnectionStrings__Default=Server=db;Database=AppDb;User=sa;Password=YourStrong!Passw0rd;TrustServerCertificate=true
    depends_on:
      db:
        condition: service_healthy

  db:
    image: mcr.microsoft.com/mssql/server:2022-latest
    environment:
      - ACCEPT_EULA=Y
      - MSSQL_SA_PASSWORD=YourStrong!Passw0rd
    ports:
      - "1433:1433"
    volumes:
      - sqldata:/var/opt/mssql
    healthcheck:
      test: /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "YourStrong!Passw0rd" -C -Q "SELECT 1" || exit 1
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  sqldata:
```

## .dockerignore

```
**/bin/
**/obj/
**/node_modules/
**/.git
**/.vs
**/.vscode
**/Dockerfile*
**/docker-compose*
**/*.md
**/*.env
```

## Health Check Endpoint

Add a health check in `Program.cs`:

```csharp
builder.Services.AddHealthChecks()
    .AddSqlServer(builder.Configuration.GetConnectionString("Default")!)
    .AddCheck("self", () => HealthCheckResult.Healthy());

app.MapHealthChecks("/health");
```

## Best Practices

- Always use multi-stage builds (smaller final image).
- Copy `.csproj` files first for layer caching of `dotnet restore`.
- Run as non-root user in production.
- Use `.dockerignore` to exclude unnecessary files.
- Set explicit health checks.
- Never embed secrets in Dockerfile — use environment variables or secrets.
- Pin base image versions (e.g., `8.0` not `latest`).
