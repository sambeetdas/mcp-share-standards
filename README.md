# Enterprise MCP Standards Server

A **Model Context Protocol (MCP) server** that distributes enterprise coding standards (rules and skills) to AI-powered IDEs like **Cursor**, **VS Code**, and **Visual Studio**.

One server. All standards. Every IDE. Zero file duplication.

---

## What It Does

```
┌─────────────────────────────────────────────────────────┐
│              MCP Standards Server                        │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ 7 Rules     │  │ 10 Skills    │  │ Audit &        │ │
│  │ (C# coding  │  │ (.NET work-  │  │ Analytics      │ │
│  │  standards)  │  │  flow guides)│  │                │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
│                          │                               │
│              MCP Protocol (stdio / SSE)                   │
└──────────────────────────┬──────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
    │  Cursor    │   │  VS Code  │   │  Visual   │
    │  IDE       │   │  + Copilot│   │  Studio   │
    └───────────┘   └───────────┘   └───────────┘
```

---

## Features

| Feature | Description |
|---------|-------------|
| **Rules as Resources** | 7 C# coding standard rules served as discoverable MCP resources |
| **Skills as Resources** | 10 .NET workflow skills (scaffolding, API design, testing, Docker, etc.) |
| **Context-Aware Retrieval** | `get_rules(language, category)` — fetch only relevant rules, saving context tokens |
| **Skill Lookup** | `get_skill(name)` — get step-by-step workflow instructions on demand |
| **Compliance Auditing** | `report_violation()` — centralized violation tracking |
| **Usage Analytics** | `get_usage_analytics()` — see which rules/skills are used most |
| **Hot Reload** | `reload_standards()` — update rules/skills without restarting |
| **Prompt Templates** | `generate_with_standards` and `review_with_standards` — inject rules into prompts |
| **Dual Transport** | stdio (local) and SSE (network) — works everywhere |

---

## Quick Start

### 1. Install Dependencies

```bash
cd mcp-standards-server
pip install -r requirements.txt
```

### 2. Test Locally (stdio)

```bash
python run.py --log-level DEBUG
```

### 3. Connect to Cursor

Copy `ide-configs/cursor-mcp.json` to your project's `.cursor/mcp.json` and update the path:

```json
{
  "mcpServers": {
    "enterprise-standards": {
      "command": "python",
      "args": [
        "C:/full/path/to/mcp-standards-server/run.py"
      ]
    }
  }
}
```

Restart Cursor. The agent now has access to all enterprise standards via MCP tools.

### 4. (Optional) Run as Network Server (SSE)

For team-wide deployment, run the server over HTTP:

```bash
python run.py --transport sse --port 8080
```

Then use the SSE configuration in your IDE:

```json
{
  "mcpServers": {
    "enterprise-standards": {
      "url": "http://your-server:8080/sse"
    }
  }
}
```

---

## IDE Configuration

### Cursor

Add to `.cursor/mcp.json` in your project (or globally):

**stdio (local):**
```json
{
  "mcpServers": {
    "enterprise-standards": {
      "command": "python",
      "args": ["C:/path/to/mcp-standards-server/run.py"]
    }
  }
}
```

**SSE (network):**
```json
{
  "mcpServers": {
    "enterprise-standards": {
      "url": "http://standards-server.internal:8080/sse"
    }
  }
}
```

### VS Code (with GitHub Copilot MCP support)

Add to VS Code `settings.json`:

```json
{
  "mcp": {
    "servers": {
      "enterprise-standards": {
        "type": "stdio",
        "command": "python",
        "args": ["C:/path/to/mcp-standards-server/run.py"]
      }
    }
  }
}
```

### Visual Studio

Visual Studio 2022 17.x+ with Copilot supports MCP via the same protocol. Configure in the IDE's MCP settings panel or via configuration file.

---

## Available Tools

The server exposes these tools to the AI agent:

| Tool | Description |
|------|-------------|
| **`get_coding_standards(language, task_type)`** | **Primary gateway** — fetches all mandatory rules + relevant skills in one call |
| `get_rules(language, category)` | Fetch mandatory coding rules filtered by language and category |
| `get_skills(language, stack)` | Fetch workflow skills for a language |
| `get_skill(skill_name, stack)` | Fetch a specific workflow skill by name or search term |
| `get_available_languages()` | Discover which languages have rules or skills |
| `list_available_standards(language)` | Browse all rules and skills directory |
| `report_violation(rule_id, file_path, description, severity)` | Report a coding standard violation |
| `get_compliance_report(rule_id, severity, limit)` | Get a compliance report of recorded violations |
| `get_usage_analytics()` | Get usage statistics for rules and skills |
| `reload_standards()` | Hot-reload rules and skills from disk |

### Tool Usage Examples

The AI agent calls these via MCP. Example interactions:

```
User: "Create a new ASP.NET Core controller for products"
Agent: [calls get_coding_standards("csharp", "generate")] → gets all rules + scaffolding/API skills
Agent: generates code following the mandatory rules and skill instructions
```

```
User: "Review this service class"
Agent: [calls get_coding_standards("csharp", "review")] → gets all rules + code review skill
Agent: provides structured review, calls report_violation() for each issue found
```

```
User: "Refactor the order processing service"
Agent: [calls get_coding_standards("csharp", "refactor")] → gets all rules + refactoring skill
Agent: refactors code following enterprise patterns
```

---

## Available Prompts

| Prompt | Description |
|--------|-------------|
| `generate_with_standards(language, task_description)` | Inject all rules for a language before code generation |
| `review_with_standards(language, code_to_review)` | Inject rules + review checklist before code review |

---

## Available Resources

| Resource URI | Description |
|-------------|-------------|
| `standards://rules` | Browse all available rules with metadata |
| `standards://skills` | Browse all available skills with metadata |

---

## Standards Included

### Rules (7)

| Rule | Language | Category |
|------|----------|----------|
| `csharp-naming-conventions` | C# | Naming |
| `csharp-project-structure` | C# | Project Structure |
| `csharp-error-handling` | C# | Error Handling |
| `csharp-testing` | C# | Testing |
| `csharp-documentation` | C# | Documentation |
| `csharp-import-ordering` | C# | Import Ordering |
| `csharp-patterns` | C# | Patterns |

### Skills (10)

| Skill | Stack | Description |
|-------|-------|-------------|
| `dotnet-project-scaffolding` | .NET | Solution/project setup |
| `ef-core-migrations` | .NET | EF Core migration workflows |
| `dotnet-api-design` | .NET | REST API design standards |
| `dotnet-dependency-injection` | .NET | DI registration patterns |
| `dotnet-logging` | .NET | Structured logging with Serilog |
| `dotnet-configuration` | .NET | Options pattern, secrets |
| `csharp-code-review` | .NET | Code review checklist |
| `dotnet-docker-deploy` | .NET | Docker deployment |
| `csharp-refactoring` | .NET | Refactoring recipes |
| `dotnet-test-generation` | .NET | Unit test generation |

---

## Adding New Standards

### Add a New Rule

1. Create a `.md` file in `standards/rules/`:

```markdown
---
description: Your rule description
globs: **/*.cs
alwaysApply: false
---

# Rule Title

Your rule content in markdown...
```

2. Run `reload_standards()` or restart the server.

### Add a New Skill

1. Create a directory in `standards/skills/` with a `SKILL.md`:

```
standards/skills/your-new-skill/
└── SKILL.md
```

```markdown
---
name: your-new-skill
description: When this skill should be triggered.
---

# Skill Title

## When to Use
- Trigger conditions...

## Instructions
Step-by-step workflow...
```

2. Run `reload_standards()` or restart the server.

---

## Project Structure

```
mcp-standards-server/
├── src/
│   └── standards_server/
│       ├── __init__.py            # Package metadata
│       ├── server.py              # MCP server (resources, tools, prompts)
│       ├── models.py              # Pydantic data models
│       └── stores/
│           ├── __init__.py
│           ├── rules_store.py     # Rule loading and querying
│           ├── skills_store.py    # Skill loading and querying
│           └── audit_store.py     # Violation tracking and analytics
├── standards/
│   ├── rules/                     # .md rule files
│   │   ├── csharp-naming-conventions.md
│   │   ├── csharp-project-structure.md
│   │   ├── csharp-error-handling.md
│   │   ├── csharp-testing.md
│   │   ├── csharp-documentation.md
│   │   ├── csharp-import-ordering.md
│   │   └── csharp-patterns.md
│   └── skills/                    # Skill directories with SKILL.md
│       ├── dotnet-project-scaffolding/
│       ├── ef-core-migrations/
│       ├── dotnet-api-design/
│       ├── dotnet-dependency-injection/
│       ├── dotnet-logging/
│       ├── dotnet-configuration/
│       ├── csharp-code-review/
│       ├── dotnet-docker-deploy/
│       ├── csharp-refactoring/
│       └── dotnet-test-generation/
├── ide-configs/                   # Ready-to-use IDE config files
│   ├── cursor-mcp.json           # Cursor stdio config
│   ├── cursor-mcp-sse.json       # Cursor SSE config
│   └── vscode-settings.json      # VS Code config
├── config.yaml                    # Server configuration
├── run.py                         # Entry point
├── pyproject.toml                 # Python package metadata
├── requirements.txt               # Dependencies
├── .gitignore
└── README.md
```

---

## Deployment Options

| Method | Best For | Command |
|--------|---------|---------|
| **Local (stdio)** | Individual developer | `python run.py` |
| **Local (SSE)** | Team on same network | `python run.py --transport sse --port 8080` |
| **Docker** | Production deployment | Build and run as container |
| **Cloud service** | Enterprise-wide | Deploy to Azure App Service, AWS ECS, etc. |

### Docker Deployment

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python", "run.py", "--transport", "sse", "--port", "8080"]
```

```bash
docker build -t mcp-standards-server .
docker run -p 8080:8080 mcp-standards-server
```

---

## How Enforcement Works

MCP is a protocol that **exposes** enterprise standards to AI agents. The server uses
several techniques to maximize compliance:

1. **Server `instructions`** — The MCP `instructions` field tells the AI it MUST call
   `get_coding_standards()` before generating, modifying, or reviewing any code. This is
   injected into the AI's context at connection time.

2. **Gateway tool** — `get_coding_standards(language, task_type)` is a single-call tool that
   returns all mandatory rules + relevant skills. Reducing friction from 3 calls to 1
   dramatically increases the chance the AI fetches standards.

3. **Tool descriptions** — Every tool description uses directive language (MUST, MANDATORY)
   so the AI understands these are requirements, not suggestions.

4. **Prompt templates** — `generate_with_standards` and `review_with_standards` inject rules
   directly into the prompt with mandatory compliance language.

### Limitations

MCP tools are inherently **advisory** — the AI agent decides whether to call them. No MCP
server can guarantee 100% compliance. The techniques above maximize the probability, but
for hard enforcement you should also consider:

- **CI/CD linters** — Run static analysis tools (e.g., StyleCop, Roslyn analyzers) in your
  build pipeline to catch violations that slip through.
- **Pre-commit hooks** — Validate naming conventions and formatting before code is committed.
- **Code review checklists** — Use the compliance report (`get_compliance_report()`) to track
  which rules are being violated most often.

### VS Code + GitHub Copilot Notes

GitHub Copilot's MCP support is evolving. To get the best results:

1. **Enable MCP in VS Code** — Ensure you are on VS Code 1.99+ and have the latest GitHub
   Copilot extension. MCP support must be enabled in Copilot settings.

2. **Configure the server** — Add to your VS Code `settings.json`:

```json
{
  "mcp": {
    "servers": {
      "enterprise-standards": {
        "type": "stdio",
        "command": "python",
        "args": ["C:/path/to/mcp-standards-server/run.py"]
      }
    }
  }
}
```

3. **Use Agent mode** — MCP tools are only available in Copilot's **Agent mode** (not inline
   completions or the default chat). Select "Agent" from the Copilot Chat mode picker.

4. **Prompt explicitly** — If Copilot does not call `get_coding_standards()` automatically,
   include phrasing like *"follow our enterprise coding standards"* or *"use the standards
   server"* in your prompt to trigger tool invocation.

5. **SSE for teams** — For team-wide deployment, run the server with `--transport sse` and
   use the SSE URL in each developer's VS Code settings.

---

## CLI Reference

```
python run.py [OPTIONS]

Options:
  --standards-dir PATH   Path to standards directory (default: ./standards)
  --audit-file PATH      Path to persist violation data as JSON
  --transport {stdio,sse} MCP transport (default: stdio)
  --host HOST            SSE server bind host (default: 0.0.0.0)
  --port PORT            SSE server port (default: 8080)
  --log-level LEVEL      Logging level: DEBUG/INFO/WARNING/ERROR (default: INFO)
```
