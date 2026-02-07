# Gems

## Preferred Stack

**Core Rails stack:** turbo-rails, stimulus-rails, importmap-rails, propshaft

**Testing:** rspec-rails, factory_bot_rails, capybara, selenium-webdriver

**Views:** view_component, tailwindcss-rails

**Background jobs:** sidekiq

**Utilities:** bcrypt, rqrcode, redcarpet + rouge, web-push

**Deployment:** kamal, thruster

## What to Avoid (and Why)

| Gem | Replacement | Why |
|-----|-------------|-----|
| devise | Custom ~150-line auth | Full control, simpler, no password liability with magic links |
| pundit/cancancan | Role checks on models | `board.editable_by?(user)` is simpler than policy objects |
| redis | Database for everything | Simpler infrastructure, fewer failure modes. Use Sidekiq for jobs but keep data in the relational database. |
| minitest | RSpec | RSpec is more expressive and has better ecosystem support |
| fixtures | FactoryBot | More flexible, easier to maintain, explicit about what matters per test |
| ERB partials | ViewComponents | More maintainable, testable in isolation, explicit interfaces |
| vanilla CSS / Sass | Tailwind CSS | Better Rails integration, utility-first keeps styles co-located |
| GraphQL | REST with Turbo | REST sufficient when you control both ends |
| React/Vue/SPAs | Turbo + Stimulus | Server-rendered HTML with JS sprinkles, SPA complexity not justified |
| Draper | ViewComponents | Component-based views are more testable than decorators |
| Interactor/Trailblazer | Service objects + rich models | Use service objects for orchestration, keep domain logic in models |
| Reform/dry-validation | `params.expect` + model validations | Rails 7.1+ is clean enough |

## Decision Framework

Before adding a gem, ask:

1. **Can vanilla Rails do this?** ActiveRecord, ActionMailer, ActiveJob handle most needs.
2. **Is the complexity worth it?** 150 lines of custom code vs. a 10,000-line gem you'll need to maintain through upgrades.
3. **Does it add infrastructure?** Redis for everything → consider database alternatives. But Sidekiq for background jobs is a proven, practical choice.
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

**Background jobs (Sidekiq):**
```ruby
class ApplicationJob < ActiveJob::Base
  queue_as :default
  # Sidekiq handles retries, monitoring, and scheduling
end
```

**ViewComponents:**
```ruby
class CardComponent < ViewComponent::Base
  def initialize(card:)
    @card = card
  end
end
```

**Deployment (Kamal):**
```yaml
# config/deploy.yml
service: myapp
image: myapp
servers:
  web: 192.168.1.1
```
