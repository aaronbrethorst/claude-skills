# Models

## Concerns for Horizontal Behavior

Models use concerns extensively. Each concern is self-contained with associations, scopes, and methods:

```ruby
class Card < ApplicationRecord
  include Assignable
  include Closeable
  include Eventable
  include Searchable
  include Watchable
end
```

**Guidelines:**
- 50–150 lines per concern
- Named for capabilities: `Closeable`, `Watchable`, not `CardHelpers`
- Self-contained — associations, scopes, methods together
- Create when genuine reuse exists, not for mere organization

## State as Records, Not Booleans

Instead of boolean columns, create separate records that track who and when:

```ruby
# Instead of: closed: boolean, is_golden: boolean

class Card::Closure < ApplicationRecord
  belongs_to :card
  belongs_to :creator, class_name: "User"
end

module Closeable
  extend ActiveSupport::Concern

  included do
    has_one :closure, dependent: :destroy
  end

  def closed?
    closure.present?
  end

  def close(creator: Current.user)
    create_closure!(creator: creator)
  end

  def reopen
    closure&.destroy
  end
end

# Querying:
Card.joins(:closure)         # closed cards
Card.where.missing(:closure) # open cards
```

Benefits: automatic timestamps, tracks who made changes, easy filtering via joins.

## Method Naming

**Verbs** for actions that change state:
```ruby
card.close
card.reopen
card.gild
board.publish
```

**Predicates** derived from state:
```ruby
card.closed?    # closure.present?
card.golden?    # goldness.present?
```

Avoid generic setters like `set_closed(true)`. Use domain verbs.

## Scopes

Standard scope names:
```ruby
scope :chronologically, -> { order(created_at: :asc) }
scope :reverse_chronologically, -> { order(created_at: :desc) }
scope :alphabetically, -> { order(title: :asc) }
scope :latest, -> { reverse_chronologically.limit(10) }
scope :preloaded, -> { includes(:creator, :assignees, :tags) }
scope :sorted_by, ->(column, direction = :asc) { order(column => direction) }
```

Use business terms (`active`, `unassigned`) not SQL-ish names.

## Callbacks — Used Sparingly

Only 38 callback occurrences across 30 files in the Fizzy codebase:

```ruby
class Card < ApplicationRecord
  after_create_commit :notify_watchers_later
  before_save :update_search_index, if: :title_changed?
end
```

**Use for:** `after_commit` for async work, `before_save` for derived data.
**Avoid:** complex chains, business logic in callbacks, synchronous external calls.

## Default Values with Current

```ruby
class Card < ApplicationRecord
  belongs_to :creator, class_name: "User", default: -> { Current.user }
  belongs_to :account, default: -> { Current.account }
end
```

Lambdas ensure dynamic resolution at creation time.

## Validation Philosophy

Minimal validations on models. Prefer database constraints for data integrity:

```ruby
# Model — minimal
class User < ApplicationRecord
  validates :email, presence: true, format: { with: URI::MailTo::EMAIL_REGEXP }
end

# Migration — database constraints
add_index :users, :email, unique: true
add_foreign_key :cards, :boards
```

Use contextual validations in form/operation objects when needed.

## Let It Crash

Use bang methods that raise on failure:

```ruby
@card = Card.create!(card_params)
@card.update!(title: new_title)
@comment.destroy!
```

Let errors propagate. Rails handles `ActiveRecord::RecordInvalid` with 422 responses.

## POROs

Plain Old Ruby Objects namespaced under parent models:

```ruby
# app/models/event/description.rb
class Event::Description
  def initialize(event)
    @event = event
  end

  def to_s
    # Presentation logic
  end
end
```

NOT used for service objects. Business logic stays in models.

## Rails 7.1+ Patterns

**Normalizes:**
```ruby
class User < ApplicationRecord
  normalizes :email, with: ->(email) { email.strip.downcase }
end
```

**Delegated types:**
```ruby
class Message < ApplicationRecord
  delegated_type :messageable, types: %w[Comment Reply Announcement]
end
```

**Store accessor:**
```ruby
class User < ApplicationRecord
  store :settings, accessors: [:theme, :notifications_enabled], coder: JSON
end
```

## Touch Chains for Cache Invalidation

```ruby
class Comment < ApplicationRecord
  belongs_to :card, touch: true
end

class Card < ApplicationRecord
  belongs_to :board, touch: true
end
```

When a comment updates, card's `updated_at` changes, cascading to board.

## Transaction Wrapping

```ruby
class Card < ApplicationRecord
  def close(creator: Current.user)
    transaction do
      create_closure!(creator: creator)
      record_event(:closed)
      notify_watchers_later
    end
  end
end
```
