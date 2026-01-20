# Poetry Archive

A minimalist poetry website built with Jekyll and GitHub Pages.

**Live site:** https://whobyphoenix.com  
**Repository:** https://github.com/whobyphoenix/poetry

## Architecture

- **Static site generator:** Jekyll (hosted on GitHub Pages)
- **E-pub generation:** Python script using Pandoc (runs in GitHub Actions)
- **Deployment:** Automatic via GitHub Actions on push to `main`
- **Text rendering:** Raw text from YAML with CSS whitespace preservation (no Markdown processing)

## Text Rendering Philosophy

Poems are stored in YAML `text:` fields and rendered as literal text to preserve exact formatting:

- **Web pages:** `{{ poem.text }}` + CSS `white-space: pre-wrap` preserves all whitespace naturally
- **EPUBs:** HTML generation with leading spaces converted to `&nbsp;` entities for EPUB reader compatibility
- **No Markdown processing:** Special characters like `- ` (dialogue), `* ` (emphasis markers) display literally
- **No Jekyll plugins:** Everything works with standard Jekyll + CSS
- **Commentary support:** Optional `commentary:` field rendered as footnote-style text after the poem (same no-Markdown rendering as poem text)

## Repository Structure

```
_poems/YYYY/MM/DD-slug.md    # Poems organized by date
_books/*.md                   # Book definitions
_authors/*.md                 # Author definitions
_layouts/
  default.html                # Base template
  book.html                   # Book page template
assets/
  css/style.css               # Styles (Lora + Inter fonts)
  images/
    covers/                   # Book cover images
    favicon/                  # Favicon files (multiple sizes/formats)
    illustrations/            # Poem illustrations (future)
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
text: |
  Poem text goes here.
  Line breaks are preserved.
  - Special characters work fine.
commentary: |                     # Optional footnote-style text after poem
  Additional context or notes.
  Also preserves formatting.
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
cover: book-cover.jpg             # Optional cover image (filename in assets/images/covers/)
---
```

**Filename is the book identifier** — poems reference it via `books: filename-without-extension`

**Cover images:** Optional. If specified, the image should be placed in `assets/images/covers/` and referenced by filename only. Recommended specs: 1600×2400px (2:3 ratio), JPEG, under 500KB. The cover will display on both the web book page and in the generated EPUB.

**Web display:** Cover images are displayed as full-width background images with text overlaid at the top. The layout uses:
- `background-size: contain` to show the full image without cropping
- `padding-top: 150%` to maintain the 2:3 aspect ratio
- Gradient overlay at the top for text readability (title, author, download link appear in white with text shadows)
- Book title, author name, and download link are positioned absolutely over the cover

**EPUB display:** Cover images are added via Pandoc's `--epub-cover-image` flag. EPUBs display the cover as the first page, followed by an auto-generated title page with book title and author.

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

## Site Branding

**Favicon:** The site uses a four-leaf clover (🍀) emoji as the favicon, stored in multiple formats/sizes in `assets/images/favicon/`:
- `favicon.svg` - Vector format (modern browsers)
- `favicon.ico` - Legacy ICO format (16×16, 32×32)
- `favicon-96x96.png` - Standard PNG favicon
- `apple-touch-icon.png` - 180×180px for iOS devices
- `web-app-manifest-192x192.png` - 192×192px for Android
- `web-app-manifest-512x512.png` - 512×512px for high-res Android
- `site.webmanifest` - Web app manifest for PWA support

All favicon tags are included in `_layouts/default.html` in the `<head>` section.

## E-pub Generation

`scripts/generate_epubs.py` runs during GitHub Actions build:

1. Reads all poems with `books:` field (using PyYAML for proper multi-line YAML parsing)
2. Groups by book
3. Generates HTML (not Markdown) with poem text:
   - Leading spaces → `&nbsp;` HTML entities (for EPUB reader compatibility)
   - Newlines → `<br>` tags
   - CSS: `white-space: pre-wrap` as fallback
   - Commentary wrapped in `()` with empty line before it (for EPUB reader consistency)
4. Converts HTML to `.epub` via Pandoc (`-f html`)
5. Output to `_site/downloads/`

**Why HTML instead of Markdown?**
- Web and EPUB use identical rendering logic
- No Markdown processing = dialogue markers (`- `), emphasis markers (`*`), etc. display literally
- No fragile escaping needed
- Consistent whitespace handling

**E-pub metadata includes:**
- Book title and author (from book's `author:` field)
- Cover image (if `cover:` field is set in book metadata) — passed to Pandoc via `--epub-cover-image`

## Jekyll Configuration Notes

**Collections:**
- `poems`: `output: false` (no individual pages)
- `authors`: `output: false` (no individual pages)
- `books`: `output: true` (generates `/books/slug/` pages)

**CSS Whitespace Preservation:**
```css
.poem-body {
  white-space: pre-wrap;  /* Preserves spaces, tabs, and newlines */
}

.poem-commentary {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
  font-family: 'Inter', sans-serif;
  font-size: 0.85rem;
  color: var(--text-light);
  font-style: italic;
  white-space: pre-wrap;  /* Preserves formatting like poem text */
}
```

This CSS handles all text formatting—no Liquid filters or Jekyll plugins needed. The `pre-wrap` value:
- Preserves leading spaces (for custom indentation)
- Preserves newlines naturally (no `<br>` conversion needed in templates)
- Still wraps long lines at container boundaries

## Common Tasks

**Add a new poem:**
```yaml
# _poems/2026/01/15-new-poem.md
---
authors: phoenix
books: flashlight-in-the-dark
text: |
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
cover: new-book-cover.jpg  # Optional
---
```

**Add a book cover:**
1. Place image in `assets/images/covers/` (e.g., `book-name.jpg`)
2. Add `cover: book-name.jpg` to book's frontmatter
3. Recommended specs: 1600×2400px (2:3 ratio), JPEG, under 500KB
4. Cover displays on web book page and in EPUB

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
3. **Poem text must be in YAML `text:` field** — avoids Markdown processing (lists, etc.)
4. **`|` in YAML preserves newlines** — essential for poetry formatting
5. **Special characters in titles:** Wrap in quotes, e.g., `poem_title: "What is 'truth'?"`
6. **Uncertain dates:** Use `date_display: "2018"` and put file in `01/01-slug.md`
7. **Custom indentation:** Use leading spaces in poem text for visual structure (e.g., see `_poems/2024/06/28-funny-voices.md`)
8. **Literal special chars:** Lines starting with `- `, `* `, etc. display as-is (not as Markdown lists/emphasis)
9. **No filters needed:** Templates use `{{ poem.text }}` directly—CSS handles whitespace
10. **EPUB vs Web:** Both render identically, but EPUBs use `&nbsp;` entities for leading spaces (better reader compatibility)
11. **Commentary styling differs:** Web uses CSS border/spacing; EPUB wraps commentary in `()` with empty line before it (plain text formatting is more reliable across EPUB readers than CSS)

## Tech Stack Versions

- Jekyll 4.x
- Python 3.11 + PyYAML (for EPUB generation)
- Pandoc (system package)
- GitHub Pages with GitHub Actions deployment

## Historical Notes

**Migration to `text:` field (January 2026):**
- All poems were migrated from Markdown body format to YAML `text:` field
- Reason: Prevent Markdown processing of special characters in poems (dialogue markers, etc.)
- Result: Cleaner separation of metadata (frontmatter) and content (`text:` field)

**Commentary support (January 2026):**
- Added optional `commentary:` field for footnote-style text after poems
- Renders without Markdown processing (same as poem text)
- Web: Styled with smaller italic text, subtle border separator, `white-space: pre-wrap`
- EPUB: Wrapped in parentheses with empty line before it (plain text formatting for EPUB reader reliability)
- CSS `font-size: smaller` used in EPUB as nice-to-have enhancement (works in some readers)

**Book cover support (January 2026):**
- Added optional `cover:` field to book metadata for cover images
- Cover images stored in `assets/images/covers/` (recommended: 1600×2400px, 2:3 ratio, JPEG, <500KB)
- Web: Covers display as full-width background with text overlay at top (gradient for readability)
- EPUB: Covers included via Pandoc's `--epub-cover-image` flag
- CSS uses `padding-top: 150%` trick to maintain 2:3 aspect ratio
- Experimented with multiple display styles before settling on text-overlay-at-top approach

**Favicon addition (January 2026):**
- Added four-leaf clover (🍀) emoji as site favicon
- Generated multiple formats/sizes for cross-platform support
- Includes SVG (modern browsers), ICO (legacy), PNG variants, and web app manifest
- Stored in `assets/images/favicon/` directory
