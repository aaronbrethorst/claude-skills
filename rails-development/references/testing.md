# Testing

## Minitest, Not RSpec

Simpler, ships with Rails, faster boot, less DSL magic:

```ruby
class CardTest < ActiveSupport::TestCase
  test "closing a card creates a closure" do
    card = cards(:one)

    assert_difference -> { Card::Closure.count } do
      card.close(creator: users(:david))
    end

    assert card.closed?
  end
end
```

## Fixtures, Not Factories

Loaded once, deterministic, explicit relationships:

```yaml
# test/fixtures/users.yml
david:
  identity: david
  account: basecamp
  role: admin

jason:
  identity: jason
  account: basecamp
  role: member

# test/fixtures/cards.yml
open_card:
  title: Open Card
  board: main
  creator: david

closed_card:
  title: Closed Card
  board: main
  creator: bob
```

Dynamic timestamps with ERB:
```yaml
recent:
  title: Recent
  created_at: <%= 1.hour.ago %>

old:
  title: Old
  created_at: <%= 1.month.ago %>
```

## Unit Tests

Verify business logic:

```ruby
class CardTest < ActiveSupport::TestCase
  setup do
    @card = cards(:one)
    @user = users(:david)
  end

  test "closing creates closure" do
    assert_difference -> { Card::Closure.count } do
      @card.close(creator: @user)
    end
    assert @card.closed?
    assert_equal @user, @card.closure.creator
  end

  test "reopening destroys closure" do
    @card.close(creator: @user)
    assert_difference -> { Card::Closure.count }, -1 do
      @card.reopen
    end
    refute @card.closed?
  end
end
```

## Integration Tests

Full request/response cycles:

```ruby
class CardsControllerTest < ActionDispatch::IntegrationTest
  setup do
    @user = users(:david)
    sign_in @user
  end

  test "closing a card" do
    card = cards(:one)
    post card_closure_path(card)

    assert_response :success
    assert card.reload.closed?
  end

  test "unauthorized user cannot close card" do
    sign_in users(:guest)
    post card_closure_path(cards(:one))

    assert_response :forbidden
  end
end
```

## System Tests

Browser-based tests with Capybara:

```ruby
class MessagesTest < ApplicationSystemTestCase
  test "sending a message" do
    sign_in users(:david)
    visit room_path(rooms(:watercooler))

    fill_in "Message", with: "Hello, world!"
    click_button "Send"

    assert_text "Hello, world!"
  end
end
```

## Advanced Patterns

**Time travel:**
```ruby
test "expires after 15 minutes" do
  magic_link = MagicLink.create!(user: users(:alice))
  travel 16.minutes
  assert magic_link.expired?
end
```

**Job assertions:**
```ruby
test "closing card enqueues notification" do
  assert_enqueued_with(job: NotifyWatchersJob, args: [cards(:one)]) do
    cards(:one).close
  end
end
```

**Email assertions:**
```ruby
test "welcome email sent on signup" do
  assert_emails 1 do
    Identity.create!(email: "new@example.com")
  end
end
```

**Turbo Stream broadcasts:**
```ruby
test "message broadcasts to room" do
  assert_turbo_stream_broadcasts [rooms(:watercooler), :messages] do
    rooms(:watercooler).messages.create!(body: "Test", creator: users(:david))
  end
end
```

## Testing Principles

1. **Test observable behavior** — what the code does, not how. Assert `Notification.count` changes, not that `notify` was called.
2. **Don't over-mock** — test the real thing with integration tests. Mocking hides bugs.
3. **Tests ship with features** — same commit, not before or after.
4. **Security fixes always include regression tests.**
5. **Integration tests validate complete workflows.**

## Test Helper

```ruby
# test/test_helper.rb
ENV["RAILS_ENV"] ||= "test"
require_relative "../config/environment"
require "rails/test_help"

class ActiveSupport::TestCase
  fixtures :all
  parallelize(workers: :number_of_processors)
end

class ActionDispatch::IntegrationTest
  include SignInHelper
end

class ApplicationSystemTestCase < ActionDispatch::SystemTestCase
  driven_by :selenium, using: :headless_chrome
end
```

## File Organization

```
test/
  controllers/    # Integration tests
  fixtures/       # YAML fixtures
  helpers/        # Helper tests
  jobs/           # Job tests
  mailers/        # Mailer tests
  models/         # Unit tests
  system/         # Browser tests
  test_helper.rb  # Configuration
```
