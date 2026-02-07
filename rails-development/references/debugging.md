# Debugging

## General Approach

1. **Read the full stack trace.** The answer is usually in the first application frame, not the gem frames.
2. **Reproduce first.** Write a failing test or use `rails console` to reproduce the exact scenario before guessing at a fix.
3. **Fix root causes, not symptoms.** If the data model is wrong, fix the model. If a query returns wrong results, fix the query. Don't add workarounds.

## Rails Console

The most powerful debugging tool. Use it to test hypotheses quickly:

```ruby
# Load the environment
bin/rails console

# Find the specific record
card = Card.find(123)

# Test the behavior
card.closed?
card.close(creator: User.first)
card.closure

# Check scopes
Card.joins(:closure).count
Card.where.missing(:closure).to_sql

# Inspect SQL
Card.where(board_id: 1).explain
Card.joins(:closure).to_sql
```

**Sandbox mode** — rolls back all changes on exit:
```bash
bin/rails console --sandbox
```

## Common Error Categories

### ActiveRecord::RecordNotFound

Usually means scoping is wrong or the record doesn't exist in the current tenant:

```ruby
# Wrong — no scoping, could access other tenant's data
Card.find(params[:id])

# Right — scoped through current user/account
Current.user.accessible_cards.find(params[:id])
Current.account.cards.find(params[:id])
```

### ActiveRecord::RecordInvalid

A bang method (`create!`, `update!`) failed validation:

```ruby
# Check what's invalid
begin
  card.update!(title: "")
rescue ActiveRecord::RecordInvalid => e
  puts e.record.errors.full_messages
end

# In console, inspect directly
card.valid?
card.errors.full_messages
```

### NoMethodError on nil

Usually a missing association or a nil `Current` attribute:

```ruby
# Check if the association exists
card.creator  # nil? Check fixture/seed data
Current.user  # nil? Check authentication flow

# Use safe navigation or check presence
card.creator&.name
```

### ActionController::ParameterMissing

Strong parameters rejected the input:

```ruby
# Check what params are being sent
# In the controller, temporarily:
Rails.logger.debug params.inspect

# Verify params.expect/permit matches form field names
def card_params
  params.expect(card: [:title, :body])
end
```

### Routing Errors

```bash
# Show all routes
bin/rails routes

# Filter to specific controller
bin/rails routes -c cards

# Filter by grep
bin/rails routes -g closure
```

Check that your resource declarations in `config/routes.rb` match what you expect.

## N+1 Queries

Symptoms: slow page loads, many similar SQL queries in logs.

**Detect:**
```ruby
# In development, add to Gemfile
gem "bullet", group: :development

# Or check logs for repeated queries
# Look for patterns like:
#   SELECT "users".* FROM "users" WHERE "users"."id" = ?
# repeated many times
```

**Fix with eager loading:**
```ruby
# Add a preloaded scope
scope :preloaded, -> { includes(:creator, :assignees, :tags) }

# Use in controller
@cards = @board.cards.preloaded
```

**Use `strict_loading` to catch N+1s in development:**
```ruby
# On a specific query
@cards = Card.strict_loading.all

# On a model (development only)
class Card < ApplicationRecord
  self.strict_loading_by_default = true if Rails.env.development?
end
```

## Debugging Turbo/Stimulus

**Turbo Stream not updating?**
1. Check the target ID matches: `turbo_stream.replace(@card)` needs `id="card_123"` in the DOM.
2. Check the response format: ensure the request accepts `text/vnd.turbo-stream.html`.
3. Check the browser console for Turbo errors.

**Stimulus controller not connecting?**
1. Verify `data-controller="name"` matches the controller filename (`name_controller.js`).
2. Check the browser console for registration errors.
3. Verify importmap or build includes the controller.
4. Add `connect() { console.log("connected") }` to verify lifecycle.

**Turbo Frame not loading?**
1. Check that the frame ID in the response matches the frame ID in the page.
2. Check the `src` URL returns a page containing a matching `turbo_frame_tag`.
3. Look for `Content-Missing` errors in the browser console.

## Debugging Callbacks and Side Effects

When behavior is unexpected, check what callbacks fire:

```ruby
# List all callbacks for a model
Card.after_create_callbacks
Card.before_save_callbacks

# Or in console, check what happens step by step
card = Card.new(title: "Test", board: boards(:main))
card.valid?    # triggers validation callbacks
card.save!     # triggers save + commit callbacks
```

## Logging

**Add targeted logging** to narrow down issues:

```ruby
# In models/controllers
Rails.logger.debug "[DEBUG] card=#{card.id} closed?=#{card.closed?} closure=#{card.closure.inspect}"

# Tagged logging in controllers
logger.tagged("CardClose") { logger.debug "Closing card #{@card.id}" }
```

**Check logs:**
```bash
# Development log
tail -f log/development.log

# Test log (useful when tests fail unexpectedly)
tail -f log/test.log

# Filter for SQL
grep "SELECT\|INSERT\|UPDATE\|DELETE" log/development.log
```

## Database Debugging

```ruby
# Check the actual SQL being generated
Card.where(board_id: 1).to_sql
Card.joins(:closure).where(closures: { creator_id: 1 }).to_sql

# Explain query plan
Card.where(board_id: 1).explain

# Check for missing indexes
# Look for Seq Scan on large tables in EXPLAIN output

# Check table structure
ActiveRecord::Base.connection.columns(:cards).map(&:name)

# Check indexes
ActiveRecord::Base.connection.indexes(:cards)
```

## Migration Debugging

```bash
# Check migration status
bin/rails db:migrate:status

# Rollback last migration
bin/rails db:rollback

# Rollback specific number of steps
bin/rails db:rollback STEP=3

# Run a specific migration
bin/rails db:migrate:up VERSION=20240101000000

# Check current schema
bin/rails db:schema:dump
```

## Test Debugging

```bash
# Run a single test file
bin/rails test test/models/card_test.rb

# Run a single test by line number
bin/rails test test/models/card_test.rb:42

# Run with verbose output
bin/rails test -v

# Run with backtraces
bin/rails test -b
```

In test code:
```ruby
test "debugging example" do
  card = cards(:one)

  # Print to test output
  puts card.inspect
  puts card.errors.full_messages

  # Use debugger (Ruby 3.1+)
  debugger

  assert card.valid?
end
```

## Performance Debugging

```ruby
# Benchmark a block
require "benchmark"
puts Benchmark.measure { Card.preloaded.to_a }

# Memory profiling (add gem "memory_profiler" to Gemfile)
report = MemoryProfiler.report { Card.all.to_a }
report.pretty_print

# Check for slow queries in logs — anything over 100ms is suspicious
# Look for lines like: Completed 200 OK in 2345ms
```
