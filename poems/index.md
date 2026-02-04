---
layout: default
title: All Poems
---

{% assign all_poems = site.poems %}
{% assign published_poems = "" | split: "" %}
{% for poem in all_poems %}
  {% if poem.books and poem.books != "" %}
    {% assign published_poems = published_poems | push: poem %}
  {% endif %}
{% endfor %}
{% assign sorted_poems = published_poems | sort: "path" %}

{% assign years = "" | split: "" %}
{% for poem in sorted_poems %}
  {% assign path_parts = poem.path | split: '/' %}
  {% assign year = path_parts[1] %}
  {% unless years contains year %}
    {% assign years = years | push: year %}
  {% endunless %}
{% endfor %}

<header class="poems-page-header">
  <nav class="year-nav">
    {% for year in years %}
      <a href="#year-{{ year }}">{{ year }}</a>{% unless forloop.last %} · {% endunless %}
    {% endfor %}
  </nav>
</header>

<div class="book-poems">
  {% assign current_year = "" %}
  {% for poem in sorted_poems %}
    {% assign path_parts = poem.path | split: '/' %}
    {% assign year = path_parts[1] %}
    {% assign month = path_parts[2] %}
    {% assign filename = path_parts[3] | split: '-' %}
    {% assign day = filename[0] %}

    {% assign book_list = poem.books | split: ', ' %}
    {% assign first_book_id = book_list | first | strip %}
    {% assign first_book = site.books | where_exp: "b", "b.path contains first_book_id" | first %}

    {% if year != current_year %}
      {% assign current_year = year %}
      {% assign year_anchor = true %}
    {% else %}
      {% assign year_anchor = false %}
    {% endif %}

  <section class="book-poem"{% if year_anchor %} id="year-{{ year }}"{% endif %}>
    <header class="poem-header">
      {% assign poem_title = poem.poem_title | default: first_book.default_poem_title | default: "..." %}
      <h2 class="poem-title">{{ poem_title }}</h2>
      <div class="poem-meta">
        {% if poem.date_display %}
        <time>{{ poem.date_display }}</time>
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
        {% if poem.authors %}
        <span class="authors">
          {% assign author_list = poem.authors | split: ', ' %}
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
{{ poem.text }}
    </div>
    {% if poem.commentary %}
    <div class="poem-commentary">
{{ poem.commentary }}
    </div>
    {% endif %}

    <footer class="poem-footer">
      <span class="in-books">In:
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
  </section>
  {% endfor %}
</div>

<button class="scroll-to-top" aria-label="Scroll to top">↑</button>

<script>
(function() {
  var btn = document.querySelector('.scroll-to-top');
  window.addEventListener('scroll', function() {
    btn.classList.toggle('visible', window.scrollY > 400);
  });
  btn.addEventListener('click', function() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
})();
</script>
