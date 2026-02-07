# Gems

## What 37signals Uses

**Core Rails stack:** turbo-rails, stimulus-rails, importmap-rails, propshaft

**Solid suite (database-backed, no Redis):**
- solid_queue — background jobs
- solid_cache — caching
- solid_cable — WebSockets/Action Cable

**Their own gems:** geared_pagination, kamal (deployment), thruster (HTTP/2 proxy), mission_control-jobs

**Utilities:** bcrypt, rqrcode, redcarpet + rouge, web-push

## What They Avoid (and Why)

| Gem | Replacement | Why |
|-----|-------------|-----|
| devise | Custom ~150-line auth | Full control, simpler, no password liability with magic links |
| pundit/cancancan | Role checks on models | `board.editable_by?(user)` is simpler than policy objects |
| sidekiq | Solid Queue | Database-backed, no Redis, same transactional guarantees |
| redis | Database for everything | Simpler infrastructure, fewer failure modes |
| view_component | Standard partials | Partials work fine, no added complexity |
| GraphQL | REST with Turbo | REST sufficient when you control both ends |
| factory_bot | Fixtures | Simpler, faster, encourages thinking about data relationships |
| rspec | Minitest | Ships with Rails, less DSL magic, faster boot |
| Tailwind/Sass | Native CSS | Modern CSS has nesting, variables, layers — no build step needed |
| React/Vue/SPAs | Turbo + Stimulus | Server-rendered HTML with JS sprinkles, SPA complexity not justified |
| Draper | View helpers + partials | No decorator indirection |
| Interactor/Trailblazer | Fat models | `card.close` instead of `CardCloser.call(card)` |
| Reform/dry-validation | `params.expect` + model validations | Rails 7.1+ is clean enough |

## Decision Framework

Before adding a gem, ask:

1. **Can vanilla Rails do this?** ActiveRecord, ActionMailer, ActiveJob handle most needs.
2. **Is the complexity worth it?** 150 lines of custom code vs. a 10,000-line gem you'll need to maintain through upgrades.
3. **Does it add infrastructure?** Redis → consider database alternatives. External service → consider building in-house.
4. **Is it well-maintained and focused?** Kitchen-sink gems are usually overkill.

> "Build solutions before reaching for gems." Not anti-gem, but pro-understanding.

## Gem Usage Patterns

**Pagination (cursor-based):**
```ruby
class CardsController < ApplicationController
  def index
    @cards = @board.cards.geared(page: params[:page])
  end
end
```

**Markdown rendering:**
```ruby
class MarkdownRenderer
  def self.render(text)
    Redcarpet::Markdown.new(
      Redcarpet::Render::HTML.new(filter_html: true),
      autolink: true, fenced_code_blocks: true
    ).render(text)
  end
end
```

**Background jobs (Solid Queue):**
```ruby
class ApplicationJob < ActiveJob::Base
  queue_as :default
  # Database-backed, just works
end
```

**Caching (Solid Cache):**
```ruby
# config/environments/production.rb
config.cache_store = :solid_cache_store
```

**Deployment (Kamal):**
```yaml
# config/deploy.yml
service: myapp
image: myapp
servers:
  web: 192.168.1.1
```
