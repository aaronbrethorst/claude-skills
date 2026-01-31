# Usage Examples

## Basic Usage

**Full review (default):**
```
/aaron-pr-review
```

**Specific aspects:**
```
/aaron-pr-review tests errors
# Reviews only test coverage and error handling

/aaron-pr-review comments
# Reviews only code comments

/aaron-pr-review simplify
# Simplifies code after passing review
```

**Parallel review:**
```
/aaron-pr-review all parallel
# Launches all agents in parallel
```

## Available Review Aspects

- **comments** - Analyze code comment accuracy and maintainability
- **tests** - Review test coverage quality and completeness
- **errors** - Check error handling for silent failures
- **types** - Analyze type design and invariants (if new types added)
- **code** - General code review for project guidelines
- **simplify** - Simplify code for clarity and maintainability
- **all** - Run all applicable reviews (default)

## Workflow Integration

### Before Committing

1. Write code
2. Run: `/aaron-pr-review code errors`
3. Fix any critical issues
4. Commit

### Before Creating PR

1. Stage all changes
2. Run: `/aaron-pr-review all`
3. Address all critical and important issues
4. Run specific reviews again to verify
5. Create PR

### After PR Feedback

1. Make requested changes
2. Run targeted reviews based on feedback
3. Verify issues are resolved
4. Push updates
