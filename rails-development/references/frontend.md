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

## CSS Architecture

Vanilla CSS with modern features, no preprocessors or Tailwind:

```css
@layer reset, base, components, modules, utilities;

@layer components {
  .btn { /* button styles */ }
}
```

**OKLCH colors** for perceptual uniformity:
```css
:root {
  --color-primary: oklch(60% 0.15 250);
  --color-success: oklch(65% 0.2 145);
}
```

**Dark mode** via variables:
```css
:root { --bg: oklch(98% 0 0); --text: oklch(20% 0 0); }

@media (prefers-color-scheme: dark) {
  :root { --bg: oklch(15% 0 0); --text: oklch(90% 0 0); }
}
```

**Native CSS nesting:**
```css
.card {
  padding: var(--space-4);
  & .title { font-weight: bold; }
  &:hover { background: var(--bg-hover); }
}
```

Modern features: `@starting-style`, `color-mix()`, `:has()`, logical properties, container queries.

## View Patterns

Standard partials, no ViewComponents:

```erb
<article id="<%= dom_id(card) %>" class="card">
  <%= render "cards/header", card: card %>
  <%= render "cards/body", card: card %>
</article>
```

**Collection caching:**
```erb
<%= render partial: "card", collection: @cards, cached: true %>
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
