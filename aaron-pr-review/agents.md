# Specialized Review Agents

This skill includes 6 specialized agents for deep analysis. Use them via the Task tool.

## code-reviewer

**Focus**: General code review for project guidelines

- Checks CLAUDE.md compliance
- Detects bugs and issues
- Reviews general code quality
- Confidence scoring (only reports issues ≥ 80)

**When to use**: Almost always—any non-trivial PR with code changes.

## code-simplifier

**Focus**: Code simplification and refactoring

- Simplifies complex code
- Improves clarity and readability
- Applies project standards
- Preserves functionality

**When to use**: PR has complex logic, deeply nested code, long functions, or code that could benefit from refactoring.

## comment-analyzer

**Focus**: Code comment accuracy and maintainability

- Verifies comment accuracy vs code
- Identifies comment rot and technical debt
- Checks documentation completeness

**When to use**: PR adds/modifies documentation comments, docstrings, or inline comments explaining complex logic.

## pr-test-analyzer

**Focus**: Test coverage quality and completeness

- Reviews behavioral test coverage
- Identifies critical gaps (rated 1-10)
- Evaluates test quality

**When to use**: PR adds/modifies functionality AND includes test files, OR adds functionality without tests.

## silent-failure-hunter

**Focus**: Error handling and silent failures

- Finds silent failures in catch blocks
- Reviews error handling patterns
- Checks error logging quality

**When to use**: PR contains try/catch blocks, error handling, fallback logic, optional chaining with defaults, or async code.

## type-design-analyzer

**Focus**: Type design and invariants

- Analyzes type encapsulation (rated 1-10)
- Reviews invariant expression (rated 1-10)
- Rates type design quality

**When to use**: PR introduces new types (structs, classes, enums, protocols) or significantly modifies existing type definitions.

## Agent Invocation

**Sequential approach** (one at a time):
- Easier to understand and act on
- Each report is complete before next
- Good for interactive review

**Parallel approach** (user can request):
- Launch all agents simultaneously
- Faster for comprehensive review
- Results come back together

## Tips

- **Run early**: Before creating PR, not after
- **Focus on changes**: Agents analyze git diff by default
- **Address critical first**: Fix high-priority issues before lower priority
- **Re-run after fixes**: Verify issues are resolved
- **Use specific reviews**: Target specific aspects when you know the concern

## Notes

- Agents run autonomously and return detailed reports
- Each agent focuses on its specialty for deep analysis
- Results are actionable with specific file:line references
- Agents use appropriate models for their complexity
