---
name: rails-development
description: Use when building features, fixing bugs, or refactoring Ruby on Rails applications. Triggers on Rails controller/model/view work, debugging Rails errors, writing migrations, adding Hotwire interactivity, or working with any Ruby on Rails codebase. Applies my Rails conventions — REST purity, service/command objects, rich domain models, RSpec, Tailwind CSS, database-backed infrastructure.
---

# Rails Development

Build features and fix bugs in Ruby on Rails applications using my conventions.

## Before Starting Any Task

1. **Understand the codebase.** Read the relevant models, controllers, routes, and specs before making changes. Run `bin/rails routes` scoped to the resource if routing is involved.
2. **Check for existing patterns.** The codebase may already have conventions for concerns, controllers, specs, and views. Match them.
3. **Run existing specs first.** `bin/rspec spec` (or the project-specific command) to establish a green baseline before changing anything.

## Building a Feature

Follow this order:

1. **Route** — map the feature to a RESTful resource. Custom verbs become noun resources (close → closure, archive → archival).
2. **Migration** — add tables/columns with database constraints (foreign keys, NOT NULL, unique indexes). Prefer state-as-records over boolean columns.
3. **Model** — add associations, scopes, and domain methods. Extract concerns when behavior is reusable across models. Use bang methods (`create!`, `update!`) to fail fast.
4. **Controller** — thin CRUD controller. Load resources via scoped queries (`Current.user.accessible_cards.find(params[:id])`). Use concerns for shared before_actions.
5. **Views** — server-rendered ERB with Turbo Streams/Frames for partial updates. Stimulus for client-side behavior. ViewComponents, not ERB partials.
6. **Tests** — RSpec with FactoryBot factories. Write specs for model logic, request specs for controller actions, system specs for critical user flows. Specs ship in the same commit as the feature.

Read the relevant reference files below based on what you are working on.

## Fixing a Bug

1. **Reproduce** — write a failing spec that demonstrates the bug before fixing anything.
2. **Locate** — use stack traces, `rails console`, and log output to find the root cause. Read [debugging.md](references/debugging.md) for strategies.
3. **Fix the root cause** — not the symptom. If the data model is wrong, fix the model. If the query is wrong, fix the query. Do not add workarounds.
4. **Verify** — the failing spec now passes. Run the full spec suite to catch regressions.
5. **Security bugs** always get a regression spec.

## Core Conventions

**Vanilla Rails is plenty:**
- Use service objects to orchestrate complex interactions between models, but keep domain logic in the models themselves. Avoid fat service objects that become dumping grounds for business logic.
- CRUD controllers over custom actions
- Concerns for horizontal code sharing
- State-as-records instead of boolean columns
- Use Sidekiq for background jobs, but avoid using Redis as a database for everything. Use the relational database for what it’s good at (data integrity, complex queries) and Sidekiq for what it’s good at (background processing).
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
- redis (database for everything)
- partials (ViewComponents are more maintainable and testable)
- GraphQL (REST + Turbo)
- minitest (RSpec is more expressive and has better ecosystem support)
- Fixtures (factory_bot is more flexible and easier to maintain)
- Vanilla CSS or CSS frameworks (Tailwind is more maintainable and has better integration with Rails)

## Reference Index

Read the relevant reference based on what you are working on:

| File | When to read |
|------|-------------|
| [controllers.md](references/controllers.md) | REST mapping, concerns, Turbo responses, authorization, HTTP caching |
| [models.md](references/models.md) | Concerns, state records, callbacks, scopes, validations, POROs |
| [frontend.md](references/frontend.md) | Turbo Streams/Frames, Stimulus, Tailwind CSS, ViewComponents, broadcasting |
| [architecture.md](references/architecture.md) | Routing, authentication, jobs, Current attributes, caching, database patterns |
| [testing.md](references/testing.md) | RSpec, factories, unit/integration/system specs, testing patterns |
| [debugging.md](references/debugging.md) | Debugging strategies, common errors, Rails console techniques |
| [gems.md](references/gems.md) | What to use vs avoid, decision framework |
