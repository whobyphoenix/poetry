---
layout: default
---
{% assign all_poems = site.poems %}
{% assign published_poems = "" | split: "" %}
{% for poem in all_poems %}
  {% if poem.books and poem.books != "" %}
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
    {% assign book_list = latest.books | split: ', ' %}
    {% assign first_book_id = book_list | first | strip %}
    {% assign first_book = site.books | where_exp: "b", "b.path contains first_book_id" | first %}
    {% assign poem_title = latest.poem_title | default: first_book.default_poem_title | default: "..." %}
    <h1 class="poem-title">{{ poem_title }}</h1>
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
{{ latest.text }}
  </div>
  
  {% if latest.books and latest.books != "" %}
  <footer class="poem-footer">
    <span class="in-books">In:
      {% assign book_list = latest.books | split: ', ' %}
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

<section id="books" class="books-section">
  <h2>Books</h2>
  <ul class="books-list">
    {% assign sorted_books = site.books | sort: "date" | reverse %}
    {% for book in sorted_books %}
    {% assign book_name = book.path | split: '/' | last | split: '.' | first %}
    <li>
      <a href="{{ book.url | relative_url }}">{{ book.title }}</a>
      <span class="book-date">{{ book.date | date: "%B %-d, %Y" }}</span>
      <a href="{{ '/downloads/' | relative_url }}{{ book_name }}.epub" class="download-link">↓ epub</a>
    </li>
    {% endfor %}
  </ul>
</section>
