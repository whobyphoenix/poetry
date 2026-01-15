#!/usr/bin/env python3
"""
Generate e-pub files for each book in the poetry archive.
Reads poem files, groups by book, generates epub via pandoc.
Extracts dates from file paths: _poems/YYYY/MM/DD-title.md
"""

import subprocess
import sys
import re
import yaml
from pathlib import Path

def parse_frontmatter(content):
    """Extract YAML frontmatter from markdown file."""
    if not content.startswith('---'):
        return {}

    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}

    try:
        frontmatter = yaml.safe_load(parts[1])
        return frontmatter if frontmatter else {}
    except yaml.YAMLError as e:
        print(f"Warning: Failed to parse YAML frontmatter: {e}")
        return {}

def extract_date_from_path(poem_path):
    """Extract date from path like _poems/2024/07/01-title.md"""
    parts = poem_path.parts
    try:
        # Find _poems in path and get subsequent parts
        poems_idx = list(parts).index('_poems')
        year = parts[poems_idx + 1]
        month = parts[poems_idx + 2]
        filename = parts[poems_idx + 3]
        # Extract day from filename (first part before -)
        day_match = re.match(r'^(\d+)', filename)
        if day_match:
            day = day_match.group(1).zfill(2)
        else:
            day = '01'
        return f"{year}-{month}-{day}"
    except (ValueError, IndexError):
        return "unknown"

def get_poems():
    """Load all poems from _poems directory."""
    poems = []
    poems_dir = Path('_poems')

    if not poems_dir.exists():
        print(f"Warning: {poems_dir} not found")
        return poems

    for poem_file in sorted(poems_dir.rglob('*.md')):
        content = poem_file.read_text(encoding='utf-8')
        meta = parse_frontmatter(content)

        date = extract_date_from_path(poem_file)
        date_display = meta.get('date_display', '')

        # Get title (empty if not set, will use book's default_title)
        title = meta.get('poem_title', '')

        # Get books (can be comma-separated, support both 'book' and 'books')
        books_str = meta.get('books', meta.get('book', ''))
        books = [b.strip() for b in books_str.split(',') if b.strip()]

        # Skip poems without books (drafts)
        if not books:
            continue

        # Get authors (default to phoenix)
        authors_str = meta.get('authors', 'phoenix')
        authors = [a.strip() for a in authors_str.split(',') if a.strip()]

        # Get poem text from 'text' field in frontmatter
        text = meta.get('text', '').strip()

        # Get commentary from 'commentary' field in frontmatter
        commentary = meta.get('commentary', '').strip()

        poems.append({
            'path': poem_file,
            'title': title,
            'text': text,
            'commentary': commentary,
            'books': books,
            'authors': authors,
            'date': date,
            'date_display': date_display
        })

    return poems

def get_book_metadata():
    """Load book metadata from _books directory."""
    books = {}
    books_dir = Path('_books')

    if books_dir.exists():
        for book_file in books_dir.glob('*.md'):
            content = book_file.read_text(encoding='utf-8')
            meta = parse_frontmatter(content)
            name = book_file.stem  # filename without extension
            books[name] = {
                'title': meta.get('title', name),
                'description': meta.get('description', ''),
                'author': meta.get('author', ''),
                'default_poem_title': meta.get('default_poem_title', '...')
            }

    return books

def get_author_metadata():
    """Load author metadata from _authors directory."""
    authors = {}
    authors_dir = Path('_authors')

    if authors_dir.exists():
        for author_file in authors_dir.glob('*.md'):
            content = author_file.read_text(encoding='utf-8')
            meta = parse_frontmatter(content)
            name = author_file.stem  # filename without extension
            authors[name] = {
                'name': meta.get('name', name)
            }

    return authors

def format_date(date_str):
    """Format date string for display."""
    if date_str == "unknown":
        return ""
    try:
        year, month, day = date_str.split('-')
        months = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
        return f"{months[int(month)]} {int(day)}, {year}"
    except:
        return date_str

def text_to_html_preserving_spaces(text):
    """Convert poem text to HTML, preserving leading spaces and newlines.

    Converts leading spaces on each line to &nbsp; entities to ensure they're
    preserved in EPUB readers, and newlines to <br> tags.
    """
    if not text:
        return ''

    lines = text.split('\n')
    html_lines = []

    for line in lines:
        # Count leading spaces
        leading_spaces = len(line) - len(line.lstrip(' '))
        if leading_spaces > 0:
            # Replace leading spaces with &nbsp; entities
            html_line = '&nbsp;' * leading_spaces + line[leading_spaces:]
        else:
            html_line = line
        html_lines.append(html_line)

    # Join with <br> for line breaks
    return '<br>\n'.join(html_lines)

def generate_epub(book_name, book_meta, poems, author_meta, output_dir):
    """Generate an epub file for a book using HTML to match web rendering."""
    title = book_meta.get('title', book_name)
    description = book_meta.get('description', '')
    book_author_id = book_meta.get('author', '')
    default_poem_title = book_meta.get('default_poem_title', '...')

    # Get book author display name
    if book_author_id and book_author_id in author_meta:
        book_author_name = author_meta[book_author_id]['name']
    elif book_author_id:
        book_author_name = book_author_id
    else:
        book_author_name = ''

    # Sort poems by date
    poems = sorted(poems, key=lambda p: p['date'])

    # Build HTML content (matching web page structure)
    html_parts = [
        '<!DOCTYPE html>',
        '<html>',
        '<head>',
        '<meta charset="UTF-8">',
        f'<title>{title}</title>',
        '<style>',
        '  .poem-body { white-space: pre-wrap; }',  # Preserve whitespace like web CSS
        '  .poem-commentary { margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid #e5e3df; font-size: 0.85rem; color: #666; font-style: italic; white-space: pre-wrap; }',
        '</style>',
        '</head>',
        '<body>',
        f'<h1>{title}</h1>'
    ]

    if description:
        html_parts.append(f'<p><em>{description}</em></p>')

    html_parts.append('<hr>')

    for poem in poems:
        poem_title = poem['title'] if poem['title'] else default_poem_title
        html_parts.append(f'<h2>{poem_title}</h2>')

        # Use date_display if set, otherwise format the date
        if poem['date_display']:
            date_display = poem['date_display']
        else:
            date_display = format_date(poem['date'])

        # Author attribution logic
        poem_authors = poem['authors']
        poem_has_book_author = book_author_id in poem_authors
        other_authors = [a for a in poem_authors if a != book_author_id]

        # Get display names for other authors
        other_author_names = []
        for a in other_authors:
            if a in author_meta:
                other_author_names.append(author_meta[a]['name'])
            else:
                other_author_names.append(a)

        if poem_has_book_author and other_author_names:
            # Collaboration
            attribution = f"In collaboration with {', '.join(other_author_names)}"
        elif poem_has_book_author:
            # Only book author, no attribution needed
            attribution = ""
        else:
            # External authors (republished work)
            all_author_names = []
            for a in poem_authors:
                if a in author_meta:
                    all_author_names.append(author_meta[a]['name'])
                else:
                    all_author_names.append(a)
            attribution = ', '.join(all_author_names)

        # Combine attribution and date
        if attribution and date_display:
            html_parts.append(f'<p><em>{attribution} — {date_display}</em></p>')
        elif attribution:
            html_parts.append(f'<p><em>{attribution}</em></p>')
        elif date_display:
            html_parts.append(f'<p><em>{date_display}</em></p>')

        # Convert poem text to HTML, preserving leading spaces and newlines
        poem_html = text_to_html_preserving_spaces(poem['text'])
        html_parts.append(f'<div class="poem-body">{poem_html}</div>')

        # Add commentary if present
        if poem.get('commentary'):
            commentary_html = text_to_html_preserving_spaces(poem['commentary'])
            html_parts.append(f'<div class="poem-commentary">{commentary_html}</div>')

        html_parts.append('<hr>')

    html_parts.extend(['</body>', '</html>'])
    html_content = '\n'.join(html_parts)

    # Write temp HTML file
    temp_file = Path(f'/tmp/{book_name}.html')
    temp_file.write_text(html_content, encoding='utf-8')

    # Generate epub from HTML
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f'{book_name}.epub'

    cmd = [
        'pandoc', str(temp_file),
        '-f', 'html',  # Input is HTML, not Markdown
        '-o', str(output_file),
        '--metadata', f'title={title}',
        '--toc',
        '--toc-depth=1'
    ]
    if book_author_name:
        cmd.extend(['--metadata', f'author={book_author_name}'])

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error generating {book_name}.epub: {result.stderr}")
        return False

    print(f"Generated: {output_file} ({len(poems)} poems)")
    return True

def main():
    output_dir = sys.argv[1] if len(sys.argv) > 1 else '_site/downloads'
    
    poems = get_poems()
    book_meta = get_book_metadata()
    author_meta = get_author_metadata()
    
    print(f"Found {len(poems)} poems")
    print(f"Found {len(book_meta)} books: {list(book_meta.keys())}")
    
    # Group poems by book
    books = {}
    for poem in poems:
        for book in poem['books']:
            if book not in books:
                books[book] = []
            books[book].append(poem)
    
    if not books:
        print("No poems assigned to any books yet.")
        print("Add 'books: bookname' to poem frontmatter to include them in books.")
        return
    
    # Generate epub for each book
    for book_name, book_poems in books.items():
        meta = book_meta.get(book_name, {'title': book_name})
        generate_epub(book_name, meta, book_poems, author_meta, output_dir)
    
    print(f"\nGenerated {len(books)} e-pub file(s)")

if __name__ == '__main__':
    main()
