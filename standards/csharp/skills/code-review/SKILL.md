---
name: csharp-code-review
description: Review C# code for quality, security, performance, and adherence to project standards. Use when the user asks for a code review, PR review, or wants feedback on C# code.
---

# C# Code Review

## When to Use

- User asks to review code, a file, or a pull request.
- User asks "is this code okay?" or "any improvements?"

## Review Workflow

1. Read the code being reviewed.
2. Run through each checklist category below.
3. Present findings grouped by severity.
4. Provide specific fix suggestions with code examples.

## Severity Levels

- **CRITICAL** — Must fix: bugs, security vulnerabilities, data loss risk.
- **WARNING** — Should fix: performance issues, maintainability concerns, missing error handling.
- **SUGGESTION** — Nice to have: style improvements, minor refactors.
- **GOOD** — Positive callouts for well-written code (always include at least one).

## Review Checklist

### Correctness
- [ ] Logic is correct and handles edge cases
- [ ] Null checks and guard clauses present
- [ ] Async/await used correctly (no `.Result`, `.Wait()`, `async void`)
- [ ] Disposable resources properly disposed (`using` statements)
- [ ] Thread safety if applicable

### Security
- [ ] No SQL injection (parameterized queries / EF Core)
- [ ] No sensitive data in logs or error messages
- [ ] Input validation present
- [ ] Authorization checks on endpoints
- [ ] No hardcoded secrets

### Performance
- [ ] No N+1 queries (check EF LINQ)
- [ ] No unnecessary allocations in hot paths
- [ ] Appropriate use of `AsNoTracking()` for read-only queries
- [ ] No LINQ in tight loops where `for` is better
- [ ] CancellationToken passed through async chains

### Naming & Style
- [ ] Follows project naming conventions (PascalCase, _camelCase, etc.)
- [ ] Names are descriptive and reveal intent
- [ ] Async methods suffixed with `Async`
- [ ] Using directives ordered correctly

### Architecture
- [ ] Single Responsibility — class/method does one thing
- [ ] Dependencies injected via constructor (no `new` for services)
- [ ] Domain entities not exposed in API responses (DTOs used)
- [ ] No business logic in controllers
- [ ] Interfaces used for external dependencies

### Testing
- [ ] New public methods have corresponding tests
- [ ] Tests follow AAA pattern
- [ ] Edge cases and error paths tested

## Output Format

```markdown
## Code Review: [FileName or PR Title]

### CRITICAL
- **[Issue]**: [Description]
  - File: `path/to/file.cs`, Line: XX
  - Fix: [Specific suggestion with code]

### WARNING
- **[Issue]**: [Description]
  - Fix: [Suggestion]

### SUGGESTION
- **[Issue]**: [Description]

### GOOD
- [Positive observation about the code]

### Summary
[1-2 sentence overall assessment]
```
