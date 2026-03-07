# claude-skills

Custom skills for [Claude Code](https://claude.ai/code) that extend Claude's capabilities with specialized workflows.

## Skills

### localizer

Translates software projects to new languages using a dual-translation verification approach.

**Features:**
- Auto-detects localization frameworks (React i18n, Vue i18n, iOS .strings, Android XML, Rails YAML, Django PO, and more)
- Uses two independent translator agents plus an adjudicator for quality
- Preserves placeholders, HTML tags, and formatting
- Handles pluralization and ICU message formats

**Usage:**
```
/localizer
```
Then specify your target language and project path.

### rails-development

Opinionated Ruby on Rails development workflow applying consistent conventions.

**Features:**
- REST purity — custom verbs become noun resources
- Service/command objects, rich domain models
- RSpec testing with TDD workflow
- Hotwire (Turbo + Stimulus) for interactivity
- Tailwind CSS for styling
- Database-backed infrastructure over Redis/external services

**Usage:**
```
/rails-development
```
Triggers automatically when working with Rails controllers, models, views, migrations, or debugging Rails errors.

### investigate-sentry

Investigates and fixes production errors from Sentry using a TDD approach.

**Features:**
- Fetches full issue data via the Sentry MCP
- Analyzes root cause and scores fix confidence on three dimensions
- Branches on confidence: plan-only, plan-then-fix, or auto-fix
- Applies TDD red-to-green fixes — writes a failing spec from Sentry data, then implements the fix

**Usage:**
```
/investigate-sentry VOTERLETTERS-9R
/investigate-sentry https://sentry.io/organizations/org/issues/12345/
```

### aaron-pr-review

Reviews GitHub pull requests with structured, prioritized feedback.

**Features:**
- Six specialized review agents:
  - **code-reviewer** - General code quality and guidelines compliance
  - **code-simplifier** - Code clarity and refactoring opportunities
  - **comment-analyzer** - Documentation accuracy
  - **pr-test-analyzer** - Test coverage gaps
  - **silent-failure-hunter** - Error handling issues
  - **type-design-analyzer** - Type design and invariants
- Applicability scoring to run only relevant agents
- Outputs structured markdown with critical/important/suggestion tiers

**Usage:**
```
/aaron-pr-review https://github.com/owner/repo/pull/123
```

## Installation

Add this repository to your Claude Code skills directory:

```bash
# Clone to your skills location
git clone https://github.com/aaronbrethorst/claude-skills.git ~/.claude/skills/claude-skills
```

Or symlink individual skills:

```bash
ln -s /path/to/claude-skills/localizer ~/.claude/skills/localizer
ln -s /path/to/claude-skills/aaron-pr-review ~/.claude/skills/aaron-pr-review
```

## Skill Structure

Each skill follows a standard format:

```
skill-name/
├── SKILL.md              # Main definition with YAML frontmatter
├── supporting-doc.md     # Additional instructions
└── agents/               # Sub-agent definitions (if applicable)
    └── agent-name.md
```

The `SKILL.md` frontmatter defines:
- `name` - Skill identifier
- `description` - When Claude should invoke this skill
- `allowed-tools` - Tool restrictions (optional)
- `argument-hint` - Usage hint shown to users (optional)

## License

MIT
