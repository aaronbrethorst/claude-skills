---
name: rails-development
description: Use when building features, fixing bugs, or refactoring Ruby on Rails applications. Triggers on Rails controller/model/view work, debugging Rails errors, writing migrations, adding Hotwire interactivity, or working with any Ruby on Rails codebase. Applies 37signals/DHH conventions — REST purity, rich domain models, Hotwire, Minitest, vanilla CSS, database-backed infrastructure.
---

# Rails Development

Build features and fix bugs in Ruby on Rails applications using 37signals/DHH conventions.

## Before Starting Any Task

1. **Understand the codebase.** Read the relevant models, controllers, routes, and tests before making changes. Run `bin/rails routes` scoped to the resource if routing is involved.
2. **Check for existing patterns.** The codebase may already have conventions for concerns, controllers, tests, and views. Match them.
3. **Run existing tests first.** `bin/rails test` (or the project-specific command) to establish a green baseline before changing anything.

## Building a Feature

Follow this order:

1. **Route** — map the feature to a RESTful resource. Custom verbs become noun resources (close → closure, archive → archival).
2. **Migration** — add tables/columns with database constraints (foreign keys, NOT NULL, unique indexes). Prefer state-as-records over boolean columns.
3. **Model** — add associations, scopes, and domain methods. Extract concerns when behavior is reusable across models. Use bang methods (`create!`, `update!`) to fail fast.
4. **Controller** — thin CRUD controller. Load resources via scoped queries (`Current.user.accessible_cards.find(params[:id])`). Use concerns for shared before_actions.
5. **Views** — server-rendered ERB with Turbo Streams/Frames for partial updates. Stimulus for client-side behavior. Standard partials, not ViewComponents.
6. **Tests** — Minitest with fixtures. Write unit tests for model logic, integration tests for controller actions, system tests for critical user flows. Tests ship in the same commit as the feature.

Read the relevant reference files below based on what you are working on.

## Fixing a Bug

1. **Reproduce** — write a failing test that demonstrates the bug before fixing anything.
2. **Locate** — use stack traces, `rails console`, and log output to find the root cause. Read [debugging.md](references/debugging.md) for strategies.
3. **Fix the root cause** — not the symptom. If the data model is wrong, fix the model. If the query is wrong, fix the query. Do not add workarounds.
4. **Verify** — the failing test now passes. Run the full test suite to catch regressions.
5. **Security bugs** always get a regression test.

## Core Conventions

**Vanilla Rails is plenty:**
- Rich domain models over service objects
- CRUD controllers over custom actions
- Concerns for horizontal code sharing
- State-as-records instead of boolean columns
- Database-backed everything (Solid Queue, Solid Cache, Solid Cable — no Redis)
- Build solutions before reaching for gems

**Naming:**
- Verbs for actions: `card.close`, `card.gild`, `board.publish`
- Predicates from state: `card.closed?`, `card.golden?`
- Concerns as adjectives: `Closeable`, `Publishable`, `Watchable`
- Controllers as nouns: `Cards::ClosuresController`
- Scopes: `chronologically`, `reverse_chronologically`, `preloaded`, `latest`

**REST mapping — verbs become noun resources:**

| Action | Resource |
|--------|----------|
| close a card | `POST /cards/:id/closure` |
| reopen a card | `DELETE /cards/:id/closure` |
| archive a card | `POST /cards/:id/archival` |
| watch a board | `POST /boards/:id/watching` |

**Ruby syntax preferences:**
```ruby
# Symbol arrays with spaces inside brackets
before_action :set_message, only: %i[ show edit update destroy ]

# Private method indentation (indented under private)
  private
    def set_message
      @message = Message.find(params[:id])
    end

# Bang methods for fail-fast
@message = Message.create!(message_params)

# Ternaries for simple conditionals
@room.direct? ? @room.users : @message.mentionees
```

**What to avoid:**
- devise (custom auth ~150 lines), pundit/cancancan (role checks on models)
- sidekiq (Solid Queue), redis (database for everything)
- view_component (partials work fine), GraphQL (REST + Turbo)
- factory_bot (fixtures), rspec (Minitest), Tailwind (native CSS)
- Service objects, form objects, decorators — keep logic in models

## Reference Index

Read the relevant reference based on what you are working on:

| File | When to read |
|------|-------------|
| [controllers.md](references/controllers.md) | REST mapping, concerns, Turbo responses, authorization, HTTP caching |
| [models.md](references/models.md) | Concerns, state records, callbacks, scopes, validations, POROs |
| [frontend.md](references/frontend.md) | Turbo Streams/Frames, Stimulus, CSS architecture, partials, broadcasting |
| [architecture.md](references/architecture.md) | Routing, authentication, jobs, Current attributes, caching, database patterns |
| [testing.md](references/testing.md) | Minitest, fixtures, unit/integration/system tests, testing patterns |
| [debugging.md](references/debugging.md) | Debugging strategies, common errors, Rails console techniques |
| [gems.md](references/gems.md) | What to use vs avoid, decision framework, Solid suite |
