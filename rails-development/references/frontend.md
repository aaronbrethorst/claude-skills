# Frontend

## Turbo Streams

Partial page updates without full redirects:

```erb
<%# app/views/cards/closures/create.turbo_stream.erb %>
<%= turbo_stream.replace @card %>
```

**Morphing** for complex updates (preserves DOM state better than replace):
```ruby
render turbo_stream: turbo_stream.morph(@card)
```

**Global morphing** in layout:
```ruby
turbo_refreshes_with method: :morph, scroll: :preserve
```

Common morphing issues:

| Problem | Solution |
|---------|----------|
| Timers not updating | Clear/restart in `turbo:morph-element` listener |
| Forms resetting | Wrap form sections in turbo frames |
| Flickering on replace | Switch to morph instead of replace |

## Turbo Frames

**Lazy loading:**
```erb
<%= turbo_frame_tag "menu", src: menu_path, loading: :lazy do %>
  <div class="spinner">Loading...</div>
<% end %>
```

**Inline editing:**
```erb
<%= turbo_frame_tag dom_id(card, :edit) do %>
  <%= link_to "Edit", edit_card_path(card),
        data: { turbo_frame: dom_id(card, :edit) } %>
<% end %>
```

**Real-time subscriptions:**
```erb
<%= turbo_stream_from @card %>
```

## Stimulus Controllers

Single responsibility, configured via values/classes, most under 50 lines:

```javascript
// app/javascript/controllers/copy_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static values = { content: String }

  copy() {
    navigator.clipboard.writeText(this.contentValue)
    this.#showFeedback()
  }

  #showFeedback() {
    this.element.classList.add("copied")
    setTimeout(() => this.element.classList.remove("copied"), 1500)
  }
}
```

```javascript
// app/javascript/controllers/auto_submit_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static values = { delay: { type: Number, default: 300 } }

  connect() { this.timeout = null }

  submit() {
    clearTimeout(this.timeout)
    this.timeout = setTimeout(() => this.element.requestSubmit(), this.delayValue)
  }

  disconnect() { clearTimeout(this.timeout) }
}
```

**Best practices:**
- Values API over `getAttribute`
- Always clean up in `disconnect()`
- Action filters (`:self`) to prevent bubbling
- Event dispatching for loose coupling: `this.dispatch("selected", { detail: { id } })`

## View Helpers (Stimulus-Integrated)

```ruby
def dialog_tag(id, &block)
  tag.dialog(id: id, data: {
    controller: "dialog",
    action: "click->dialog#clickOutside keydown.esc->dialog#close"
  }, &block)
end

def copy_button(content:, label: "Copy")
  tag.button(label, data: {
    controller: "copy",
    copy_content_value: content,
    action: "click->copy#copy"
  })
end
```

## CSS with Tailwind

Use Tailwind CSS for styling. Utility-first approach keeps styles co-located with markup and avoids naming debates:

```erb
<article class="rounded-lg border border-gray-200 p-4 shadow-sm hover:shadow-md transition-shadow">
  <h2 class="text-lg font-semibold text-gray-900"><%= card.title %></h2>
  <p class="mt-2 text-sm text-gray-600"><%= card.body %></p>
</article>
```

**Dark mode** via Tailwind's `dark:` variant:
```erb
<div class="bg-white text-gray-900 dark:bg-gray-900 dark:text-gray-100">
  <h1 class="text-xl font-bold dark:text-white"><%= @title %></h1>
</div>
```

**Responsive design:**
```erb
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  <% @cards.each do |card| %>
    <%= render CardComponent.new(card: card) %>
  <% end %>
</div>
```

**Custom design tokens** in `tailwind.config.js` when needed:
```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: { 500: '#6366f1', 600: '#4f46e5' },
      },
    },
  },
}
```

Extract repeated utility patterns into ViewComponents, not `@apply` directives. Prefer composing Tailwind classes in components over creating custom CSS.

## ViewComponents

Use ViewComponents instead of ERB partials. They're testable in isolation, have explicit interfaces, and keep view logic out of helpers:

```ruby
# app/components/card_component.rb
class CardComponent < ViewComponent::Base
  def initialize(card:)
    @card = card
  end
end
```

```erb
<%# app/components/card_component.html.erb %>
<article id="<%= dom_id(@card) %>" class="rounded-lg border border-gray-200 p-4">
  <%= render CardHeaderComponent.new(card: @card) %>
  <%= render CardBodyComponent.new(card: @card) %>
</article>
```

**Rendering:**
```erb
<%= render CardComponent.new(card: @card) %>
```

**Collection rendering:**
```erb
<%= render CardComponent.with_collection(@cards) %>
```

**Component testing:**
```ruby
RSpec.describe CardComponent, type: :component do
  it "renders the card title" do
    card = build(:card, title: "My Card")
    render_inline(CardComponent.new(card: card))

    expect(page).to have_text("My Card")
  end
end
```

## User-Specific Content in Caches

Move personalization to client-side JavaScript:

```erb
<% cache card do %>
  <article class="card"
           data-controller="ownership"
           data-ownership-current-user-value="<%= Current.user.id %>"
           data-creator-id="<%= card.creator_id %>">
    <button data-ownership-target="ownerOnly" class="hidden">Delete</button>
  </article>
<% end %>
```

Or extract dynamic content to separate Turbo Frames that load independently.

## Broadcasting

```ruby
class Card < ApplicationRecord
  after_create_commit -> { broadcast_append_to [Current.account, board], :cards }
  after_update_commit -> { broadcast_replace_to [Current.account, board], :cards }
  after_destroy_commit -> { broadcast_remove_to [Current.account, board], :cards }
end
```

Scope by tenant using `[Current.account, resource]` pattern.
