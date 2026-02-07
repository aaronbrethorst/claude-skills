# Controllers

## Everything Maps to CRUD

Custom actions become new resources. Verbs on existing resources become noun resources with their own controllers:

```ruby
# Instead of custom actions:
#   POST /cards/:id/close
#   POST /cards/:id/archive

# Create noun resources:
#   POST /cards/:id/closure       → Cards::ClosuresController#create
#   DELETE /cards/:id/closure     → Cards::ClosuresController#destroy
#   POST /cards/:id/archival      → Cards::ArchivalsController#create

resources :cards do
  resource :closure       # closing/reopening
  resource :goldness      # marking important
  resource :not_now       # postponing
  resources :assignments  # managing assignees
end
```

Each resource gets its own controller with standard CRUD actions. Controllers stay thin.

## Controller Concerns

Use concerns for shared behavior across controllers:

```ruby
# Loads parent resource and provides helper methods
module CardScoped
  extend ActiveSupport::Concern

  included do
    before_action :set_card
  end

  private
    def set_card
      @card = Card.find(params[:card_id])
      @board = @card.board
    end

    def render_card_replacement
      render turbo_stream: turbo_stream.replace(@card)
    end
end
```

Common concern patterns:
- **ResourceScoped** — loads parent resource via `before_action`
- **Authorization** — permission checks via `before_action`
- **CurrentTimezone** — wraps request in user's timezone with `around_action`
- **CurrentRequest** — populates `Current` with request metadata

## Authorization

Controllers check permissions; models define what permissions mean:

```ruby
# Controller concern
module Authorization
  extend ActiveSupport::Concern

  private
    def ensure_can_administer
      head :forbidden unless Current.user.admin?
    end
end

# Usage in controller
class BoardsController < ApplicationController
  before_action :ensure_can_administer, only: [:destroy]
end

# Model defines permission logic
class Board < ApplicationRecord
  def editable_by?(user)
    user.admin? || user == creator
  end
end
```

## Turbo Stream Responses

Use Turbo Streams for partial page updates without full redirects:

```ruby
class Cards::ClosuresController < ApplicationController
  include CardScoped

  def create
    @card.close
    render_card_replacement
  end

  def destroy
    @card.reopen
    render_card_replacement
  end
end
```

For complex updates, use morphing:
```ruby
render turbo_stream: turbo_stream.morph(@card)
```

## API Responses

Same controllers, different format:

```ruby
def create
  @card = Card.create!(card_params)

  respond_to do |format|
    format.html { redirect_to @card }
    format.json { head :created, location: @card }
  end
end

def update
  @card.update!(card_params)

  respond_to do |format|
    format.html { redirect_to @card }
    format.json { head :no_content }
  end
end
```

Status codes: Create → 201 + Location header. Update/Delete → 204 No Content.

## HTTP Caching

Use ETags and conditional GETs extensively:

```ruby
class CardsController < ApplicationController
  def show
    @card = Card.find(params[:id])
    fresh_when etag: [@card, Current.user.timezone]
  end

  def index
    @cards = @board.cards.preloaded
    fresh_when etag: [@cards, @board.updated_at]
  end
end
```

Include timezone in ETags because times render differently per user timezone.

Global ETag seed in ApplicationController:
```ruby
class ApplicationController < ActionController::Base
  etag { "v1" }  # Bump to invalidate all caches
end
```

## Rate Limiting (Rails 8+)

```ruby
class MagicLinksController < ApplicationController
  rate_limit to: 10, within: 15.minutes, only: :create
end
```

Apply to auth endpoints, email sending, external API calls, resource creation.

## Security: Sec-Fetch-Site CSRF

Modern defense-in-depth alongside Rails CSRF tokens:

```ruby
module RequestForgeryProtection
  extend ActiveSupport::Concern

  included do
    before_action :verify_request_origin
  end

  private
    def verify_request_origin
      return if request.get? || request.head?
      return if %w[same-origin same-site].include?(
        request.headers["Sec-Fetch-Site"]&.downcase
      )
      verify_authenticity_token
    end
end
```

## Strong Parameters

Use `params.expect` (Rails 7.1+) for cleaner parameter filtering:

```ruby
def card_params
  params.expect(card: [:title, :body, :board_id])
end
```
