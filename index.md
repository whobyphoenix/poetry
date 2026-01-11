---
layout: default
---
{% assign published_poems = site.poems | where_exp: "poem", "poem.books != nil and poem.books != '' and poem.book != nil and poem.book != ''" %}
{% comment %}Handle both 'books' and 'book' fields{% endcomment %}
{% assign all_poems = site.poems %}
{% assign published_poems = "" | split: "" %}
{% for poem in all_poems %}
  {% assign has_books = poem.books | default: poem.book | default: "" %}
  {% if has_books != "" %}
    {% assign published_poems = published_poems | push: poem %}
  {% endif %}
{% endfor %}
{% assign sorted_poems = published_poems | sort: "path" | reverse %}
{% assign latest = sorted_poems | first %}

{% if latest %}
{% assign path_parts = latest.path | split: '/' %}
{% assign year = path_parts[1] %}
{% assign month = path_parts[2] %}
{% assign filename = path_parts[3] | split: '-' %}
{% assign day = filename[0] %}

<article class="poem">
  <header class="poem-header">
    <h1 class="poem-title">{{ latest.title }}</h1>
    <div class="poem-meta">
      {% if latest.date_display %}
      <time>{{ latest.date_display }}</time>
      {% else %}
      <time>
        {% assign month_num = month | plus: 0 %}
        {% case month_num %}
          {% when 1 %}January{% when 2 %}February{% when 3 %}March{% when 4 %}April
          {% when 5 %}May{% when 6 %}June{% when 7 %}July{% when 8 %}August
          {% when 9 %}September{% when 10 %}October{% when 11 %}November{% when 12 %}December
        {% endcase %}
        {{ day | plus: 0 }}, {{ year }}
      </time>
      {% endif %}
      {% if latest.authors %}
      <span class="authors">
        {% assign author_list = latest.authors | split: ', ' %}
        {% for author_id in author_list %}
          {% assign author_id_stripped = author_id | strip %}
          {% assign author = site.authors | where_exp: "a", "a.path contains author_id_stripped" | first %}
          {% if author and author.link %}
            <a href="{{ author.link }}">{{ author.name }}</a>{% unless forloop.last %}, {% endunless %}
          {% elsif author %}
            {{ author.name }}{% unless forloop.last %}, {% endunless %}
          {% else %}
            {{ author_id_stripped }}{% unless forloop.last %}, {% endunless %}
          {% endif %}
        {% endfor %}
      </span>
      {% endif %}
    </div>
  </header>
  
  <div class="poem-body">
{{ latest.content | newline_to_br }}
  </div>
  
  {% assign has_books = latest.books | default: latest.book | default: "" %}
  {% if has_books != "" %}
  <footer class="poem-footer">
    <span class="in-books">In: 
      {% assign book_list = has_books | split: ', ' %}
      {% for book_id in book_list %}
        {% assign book_id_stripped = book_id | strip %}
        {% assign book = site.books | where_exp: "b", "b.path contains book_id_stripped" | first %}
        {% if book %}
          <a href="{{ book.url | relative_url }}">{{ book.title }}</a>{% unless forloop.last %}, {% endunless %}
        {% else %}
          {{ book_id_stripped }}{% unless forloop.last %}, {% endunless %}
        {% endif %}
      {% endfor %}
    </span>
  </footer>
  {% endif %}
</article>
{% endif %}

<section class="books-section">
  <h2>Books</h2>
  <ul class="books-list">
    {% for book in site.books %}
    {% assign book_name = book.path | split: '/' | last | split: '.' | first %}
    <li>
      <a href="{{ book.url | relative_url }}">{{ book.title }}</a>
      <a href="{{ '/downloads/' | relative_url }}{{ book_name }}.epub" class="download-link">↓ epub</a>
    </li>
    {% endfor %}
  </ul>
</section>
