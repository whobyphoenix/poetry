# Poetry Archive

A minimalist poetry website built with Jekyll and GitHub Pages.

**Live site:** https://whobyphoenix.com  
**Repository:** https://github.com/whobyphoenix/poetry

## Architecture

- **Static site generator:** Jekyll (hosted on GitHub Pages)
- **E-pub generation:** Python script using Pandoc (runs in GitHub Actions)
- **Deployment:** Automatic via GitHub Actions on push to `main`

## Repository Structure

```
_poems/YYYY/MM/DD-slug.md    # Poems organized by date
_books/*.md                   # Book definitions
_authors/*.md                 # Author definitions
_layouts/
  default.html                # Base template
  book.html                   # Book page template
css/style.css                 # Styles (Lora + Inter fonts)
index.md                      # Homepage (latest poem + book list)
scripts/generate_epubs.py     # E-pub generation script
.github/workflows/deploy.yml  # CI/CD pipeline
_config.yml                   # Jekyll configuration
```

## Poem File Format

All poem content lives in YAML frontmatter to avoid Markdown processing issues.

```yaml
---
poem_title: "Optional Title"      # If omitted, uses book's default_poem_title
authors: phoenix                  # Comma-separated if multiple: "phoenix, claude"
books: drowning-admiration        # Required to publish; omit for drafts
date_display: "2018"              # Optional override (e.g., for uncertain dates)
body: |
  Poem text goes here.
  Line breaks are preserved.
  - Special characters work fine.
---
```

**Key conventions:**
- Filename pattern: `DD-slug.md` where DD is day of month
- Path provides date: `_poems/2024/07/15-example.md` → July 15, 2024
- Poems without `books:` field are drafts (not published anywhere)
- `poem_title` (not `title`) — avoids Jekyll's auto-generation from filename

## Book File Format

```yaml
---
title: "Book Display Title"
author: phoenix                   # References _authors/phoenix.md
default_poem_title: "..."         # Used when poem has no poem_title
---
```

**Filename is the book identifier** — poems reference it via `books: filename-without-extension`

## Author File Format

```yaml
---
name: "Phoenix"                   # Display name
link: "https://bsky.app/..."      # External URL (not 'url' — that's reserved by Jekyll)
---
```

**Filename is the author identifier** — poems/books reference it via `authors: filename-without-extension`

## Author Attribution Logic

Books have a single author. Per-poem attribution follows these rules:

| Poem authors | Display |
|--------------|---------|
| Book author only | *(just date, no attribution)* |
| Book author + others | *In collaboration with [others]* |
| Others only (no book author) | *[All authors listed]* |

## Site Structure

- **Homepage (`/`):** Latest published poem + list of all books with epub download links
- **Book pages (`/books/slug/`):** Full text of all poems in the book (like an e-reader)
- **No individual poem pages** — poems are only viewable within their book context
- **No author pages** — author names link to external URLs

## E-pub Generation

`scripts/generate_epubs.py` runs during GitHub Actions build:

1. Reads all poems with `books:` field
2. Groups by book
3. Generates one `.epub` per book via Pandoc
4. Output to `_site/downloads/`

E-pub metadata includes book title and author (from book's `author:` field).

## Jekyll Configuration Notes

```yaml
kramdown:
  hard_wrap: true    # Preserves line breaks in Markdown
```

Collections:
- `poems`: `output: false` (no individual pages)
- `authors`: `output: false` (no individual pages)  
- `books`: `output: true` (generates `/books/slug/` pages)

## Common Tasks

**Add a new poem:**
```yaml
# _poems/2026/01/15-new-poem.md
---
authors: phoenix
books: flashlight-in-the-dark
body: |
  Your poem here.
---
```

**Add a new book:**
```yaml
# _books/new-book.md
---
title: "New Book Title"
author: phoenix
default_poem_title: "..."
---
```

**Add a new author:**
```yaml
# _authors/claude.md
---
name: "Claude"
link: "https://claude.ai/"
---
```

**Mark poem as draft:** Omit the `books:` field.

**Poem in multiple books:** `books: book-one, book-two`

**Collaboration:** `authors: phoenix, claude`

## Gotchas & Lessons Learned

1. **Use `poem_title` not `title`** — Jekyll auto-generates `title` from filename
2. **Use `link` not `url` for authors** — `url` is reserved by Jekyll
3. **Poem body must be in YAML `body:` field** — avoids Markdown processing (lists, etc.)
4. **`|` in YAML preserves newlines** — essential for poetry formatting
5. **Special characters in titles:** Wrap in quotes, e.g., `poem_title: "What is 'truth'?"`
6. **Uncertain dates:** Use `date_display: "2018"` and put file in `01/01-slug.md`

## Tech Stack Versions

- Jekyll 4.x
- Python 3.11
- Pandoc (system package)
- GitHub Pages with GitHub Actions deployment
