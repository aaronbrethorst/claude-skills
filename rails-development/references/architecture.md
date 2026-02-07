# Architecture

## Routing

Everything maps to CRUD. Nested resources for related actions:

```ruby
Rails.application.routes.draw do
  resources :boards do
    resources :cards, shallow: true do
      resource :closure
      resource :goldness
      resources :assignments
      resources :comments
    end
  end
end
```

**Verb-to-noun conversion:**

| Action | Resource |
|--------|----------|
| close a card | `card.closure` |
| watch a board | `board.watching` |
| archive a card | `card.archival` |

Use `shallow: true` to avoid deep URLs. Use singular `resource` for one-per-parent.

## Current Attributes

Request-scoped state via `Current`:

```ruby
# app/models/current.rb
class Current < ActiveSupport::CurrentAttributes
  attribute :session, :user, :account, :request_id

  delegate :user, to: :session, allow_nil: true

  def account=(account)
    super
    Time.zone = account&.time_zone || "UTC"
  end
end
```

Set in controller:
```ruby
class ApplicationController < ActionController::Base
  before_action :set_current_request

  private
    def set_current_request
      Current.session = authenticated_session
      Current.account = Account.find(params[:account_id])
    end
end
```

Use throughout app: `belongs_to :creator, default: -> { Current.user }`

## Authentication

Custom passwordless magic link auth (~150 lines, no Devise):

```ruby
class Session < ApplicationRecord
  belongs_to :user
  before_create { self.token = SecureRandom.urlsafe_base64(32) }
end

class MagicLink < ApplicationRecord
  belongs_to :user
  before_create do
    self.code = SecureRandom.random_number(100_000..999_999).to_s
    self.expires_at = 15.minutes.from_now
  end

  def expired?
    expires_at < Time.current
  end
end
```

Bearer token for APIs:
```ruby
module Authentication
  extend ActiveSupport::Concern

  included do
    before_action :authenticate
  end

  private
    def authenticate
      if bearer_token = request.headers["Authorization"]&.split(" ")&.last
        Current.session = Session.find_by(token: bearer_token)
      else
        Current.session = Session.find_by(id: cookies.signed[:session_id])
      end

      redirect_to login_path unless Current.session
    end
end
```

## Background Jobs

Jobs are shallow wrappers calling model methods:

```ruby
class NotifyWatchersJob < ApplicationJob
  def perform(card)
    card.notify_watchers
  end
end
```

Naming: `_later` for async, `_now` for immediate:
```ruby
module Watchable
  def notify_watchers_later
    NotifyWatchersJob.perform_later(self)
  end

  def notify_watchers
    watchers.each { |w| WatcherMailer.notification(w, self).deliver_later }
  end
end
```

Database-backed with Solid Queue — no Redis. Use `enqueue_after_transaction_commit = true` for transaction safety.

Error handling by type:
```ruby
class DeliveryJob < ApplicationJob
  retry_on Net::OpenTimeout, wait: :polynomially_longer
  discard_on Net::SMTPSyntaxError
end
```

## Database Patterns

**UUIDs as primary keys** (UUIDv7, time-sortable):
```ruby
create_table :cards, id: :uuid do |t|
  t.references :board, type: :uuid, foreign_key: true
end
```

**State as records** instead of booleans — see [models.md](models.md).

**Hard deletes** — no soft delete. Use event logs for auditing:
```ruby
card.record_event(:deleted, by: Current.user)
card.destroy!
```

**Counter caches:**
```ruby
class Comment < ApplicationRecord
  belongs_to :card, counter_cache: true
end
```

**Account scoping:**
```ruby
class Card < ApplicationRecord
  belongs_to :account
  default_scope { where(account: Current.account) }
end
```

## Caching

**HTTP caching** with ETags:
```ruby
fresh_when etag: [@card, Current.user.timezone]
```

**Fragment caching:**
```erb
<% cache card do %>
  <%= render card %>
<% end %>
```

**Russian doll caching** with `touch: true` on associations for invalidation.

**Solid Cache** — database-backed, no Redis:
```ruby
config.cache_store = :solid_cache_store
```

## Event Tracking

Events as the single source of truth:

```ruby
module Eventable
  extend ActiveSupport::Concern

  included do
    has_many :events, as: :eventable, dependent: :destroy
  end

  def record_event(action, particulars = {})
    events.create!(
      creator: Current.user,
      action: action,
      particulars: particulars
    )
  end
end
```

## Multi-Tenancy

Path-based with middleware extracting tenant from URL prefix. Key principles:
- Cookie scoping per tenant path
- Background jobs serialize tenant context
- Controllers always scope queries through tenant: `Current.user.accessible_cards.find(params[:id])`

## Security Patterns

**SSRF protection** — resolve DNS once, pin IP, block private networks.

**Content Security Policy:**
```ruby
config.content_security_policy do |policy|
  policy.default_src :self
  policy.script_src :self
  policy.style_src :self, :unsafe_inline
  policy.base_uri :none
end
```

**ActionText sanitization** — whitelist allowed tags explicitly.

## Configuration

ENV.fetch with defaults:
```ruby
config.active_job.queue_adapter = ENV.fetch("QUEUE_ADAPTER", "solid_queue").to_sym
config.cache_store = ENV.fetch("CACHE_STORE", "solid_cache").to_sym
```
