# Agent Applicability Assessment

**You MUST explicitly evaluate each agent before proceeding.** For each agent, assess its applicability to this specific PR and assign a confidence score from 0-100. Use the agent if the score is **≥ 80**.

## Assessment Format

Output your assessment in this exact format:

```
## Agent Applicability Assessment

| Agent | Confidence | Rationale | Use? |
|-------|------------|-----------|------|
| code-reviewer | [0-100] | [Brief reason based on PR content] | [Yes/No] |
| silent-failure-hunter | [0-100] | [Brief reason based on PR content] | [Yes/No] |
| pr-test-analyzer | [0-100] | [Brief reason based on PR content] | [Yes/No] |
| comment-analyzer | [0-100] | [Brief reason based on PR content] | [Yes/No] |
| type-design-analyzer | [0-100] | [Brief reason based on PR content] | [Yes/No] |
| code-simplifier | [0-100] | [Brief reason based on PR content] | [Yes/No] |
```

## Scoring Guidelines

| Agent | Score 80+ when... |
|-------|-------------------|
| **code-reviewer** | Almost always—any non-trivial PR with code changes |
| **silent-failure-hunter** | PR contains try/catch blocks, error handling, fallback logic, optional chaining with defaults, or async code |
| **pr-test-analyzer** | PR adds/modifies functionality AND includes test files, OR adds functionality without tests |
| **comment-analyzer** | PR adds/modifies documentation comments, docstrings, or inline comments explaining complex logic |
| **type-design-analyzer** | PR introduces new types (structs, classes, enums, protocols) or significantly modifies existing type definitions |
| **code-simplifier** | PR has complex logic, deeply nested code, long functions, or code that could benefit from refactoring |

## Example Assessment

```
## Agent Applicability Assessment

| Agent | Confidence | Rationale | Use? |
|-------|------------|-----------|------|
| code-reviewer | 95 | Large PR with 3000+ lines of new code across 37 files | Yes |
| silent-failure-hunter | 90 | New API client has extensive try/catch fallback patterns | Yes |
| pr-test-analyzer | 85 | PR adds new test file but coverage seems minimal for scope | Yes |
| comment-analyzer | 60 | Few documentation comments added, mostly code | No |
| type-design-analyzer | 95 | Introduces 15+ new model types and DTOs | Yes |
| code-simplifier | 75 | Some complex decoding logic but generally clean | No |
```

**After completing the assessment**, launch all agents marked "Yes" before writing your review.
