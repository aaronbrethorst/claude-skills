# Testing

## RSpec, Not Minitest

More expressive, better ecosystem support, widely adopted:

```ruby
RSpec.describe Card, type: :model do
  describe "#close" do
    it "creates a closure" do
      card = create(:card)
      user = create(:user)

      expect { card.close(creator: user) }.to change(Card::Closure, :count).by(1)
      expect(card).to be_closed
    end
  end
end
```

## FactoryBot, Not Fixtures

More flexible, easier to maintain, explicit about what matters per test:

```ruby
# spec/factories/users.rb
FactoryBot.define do
  factory :user do
    sequence(:email) { |n| "user#{n}@example.com" }
    account
    role { :member }

    trait :admin do
      role { :admin }
    end
  end
end

# spec/factories/cards.rb
FactoryBot.define do
  factory :card do
    sequence(:title) { |n| "Card #{n}" }
    board
    creator { association(:user) }

    trait :closed do
      after(:create) do |card|
        create(:card_closure, card: card, creator: card.creator)
      end
    end
  end
end
```

Use `build` when you don't need persistence, `create` when you do. Use traits for variations:
```ruby
create(:user, :admin)
create(:card, :closed)
build(:card, title: "Specific Title")
```

## Model Specs

Verify business logic:

```ruby
RSpec.describe Card, type: :model do
  describe "#close" do
    it "creates a closure" do
      card = create(:card)
      user = create(:user)

      expect { card.close(creator: user) }.to change(Card::Closure, :count).by(1)
      expect(card).to be_closed
      expect(card.closure.creator).to eq(user)
    end
  end

  describe "#reopen" do
    it "destroys the closure" do
      card = create(:card, :closed)

      expect { card.reopen }.to change(Card::Closure, :count).by(-1)
      expect(card).not_to be_closed
    end
  end
end
```

## Request Specs

Full request/response cycles:

```ruby
RSpec.describe "Cards::Closures", type: :request do
  let(:user) { create(:user) }
  let(:card) { create(:card) }

  before { sign_in user }

  describe "POST /cards/:card_id/closure" do
    it "closes the card" do
      post card_closure_path(card)

      expect(response).to have_http_status(:success)
      expect(card.reload).to be_closed
    end
  end

  context "when unauthorized" do
    let(:guest) { create(:user, role: :guest) }

    before { sign_in guest }

    it "returns forbidden" do
      post card_closure_path(card)

      expect(response).to have_http_status(:forbidden)
    end
  end
end
```

## System Specs

Browser-based specs with Capybara:

```ruby
RSpec.describe "Messages", type: :system do
  it "sends a message" do
    user = create(:user)
    room = create(:room)

    sign_in user
    visit room_path(room)

    fill_in "Message", with: "Hello, world!"
    click_button "Send"

    expect(page).to have_text("Hello, world!")
  end
end
```

## Advanced Patterns

**Time travel:**
```ruby
it "expires after 15 minutes" do
  magic_link = create(:magic_link)
  travel 16.minutes
  expect(magic_link).to be_expired
end
```

**Job assertions:**
```ruby
it "enqueues a notification job when closing" do
  card = create(:card)
  user = create(:user)

  expect { card.close(creator: user) }.to have_enqueued_job(NotifyWatchersJob).with(card)
end
```

**Email assertions:**
```ruby
it "sends a welcome email on signup" do
  expect {
    create(:identity, email: "new@example.com")
  }.to change { ActionMailer::Base.deliveries.count }.by(1)
end
```

**Turbo Stream broadcasts:**
```ruby
it "broadcasts the message to the room" do
  room = create(:room)
  user = create(:user)

  expect {
    room.messages.create!(body: "Test", creator: user)
  }.to have_broadcasted_to([room, :messages])
end
```

## ViewComponent Specs

```ruby
RSpec.describe CardComponent, type: :component do
  it "renders the card title" do
    card = build(:card, title: "My Card")
    render_inline(CardComponent.new(card: card))

    expect(page).to have_text("My Card")
  end

  it "shows closed state" do
    card = create(:card, :closed)
    render_inline(CardComponent.new(card: card))

    expect(page).to have_css(".closed")
  end
end
```

## Testing Principles

1. **Test observable behavior** — what the code does, not how. Assert `Notification.count` changes, not that `notify` was called.
2. **Don't over-mock** — test the real thing with request specs. Mocking hides bugs.
3. **Specs ship with features** — same commit, not before or after.
4. **Security fixes always include regression specs.**
5. **Request specs validate complete workflows.**

## Spec Helper

```ruby
# spec/rails_helper.rb
require "spec_helper"
ENV["RAILS_ENV"] ||= "test"
require_relative "../config/environment"
require "rspec/rails"

Dir[Rails.root.join("spec/support/**/*.rb")].each { |f| require f }

RSpec.configure do |config|
  config.use_transactional_fixtures = true
  config.infer_spec_type_from_file_location!

  config.include FactoryBot::Syntax::Methods
  config.include SignInHelper, type: :request
  config.include SignInHelper, type: :system
  config.include ViewComponent::TestHelpers, type: :component
end

Capybara.default_driver = :selenium_chrome_headless
```

## File Organization

```
spec/
  components/     # ViewComponent specs
  factories/      # FactoryBot factories
  models/         # Model specs
  requests/       # Request specs
  system/         # Browser specs
  support/        # Shared helpers
  rails_helper.rb # Configuration
  spec_helper.rb  # RSpec configuration
```
