#!/usr/bin/env python3
"""
Generate e-pub files for each book in the poetry archive.
Reads poem files, groups by book, generates epub via pandoc.
Extracts dates from file paths: _poems/YYYY/MM/DD-title.md
"""

import subprocess
import sys
import re
from pathlib import Path

def parse_frontmatter(content):
    """Extract YAML frontmatter and body from markdown file."""
    if not content.startswith('---'):
        return {}, content
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content
    
    frontmatter = {}
    for line in parts[1].strip().split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            value = value.strip()
            # Remove surrounding quotes if present
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            frontmatter[key.strip()] = value
    
    return frontmatter, parts[2].strip()

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
        meta, body = parse_frontmatter(content)
        
        date = extract_date_from_path(poem_file)
        date_display = meta.get('date_display', '')
        
        # Get title (empty if not set, will use book's default_title)
        title = meta.get('title', '')
        
        # Get books (can be comma-separated, support both 'book' and 'books')
        books_str = meta.get('books', meta.get('book', ''))
        books = [b.strip() for b in books_str.split(',') if b.strip()]
        
        # Skip poems without books (drafts)
        if not books:
            continue
        
        # Get authors (default to phoenix)
        authors_str = meta.get('authors', 'phoenix')
        authors = [a.strip() for a in authors_str.split(',') if a.strip()]
        
        poems.append({
            'path': poem_file,
            'title': title,
            'body': body,
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
            meta, _ = parse_frontmatter(content)
            name = book_file.stem  # filename without extension
            books[name] = {
                'title': meta.get('title', name),
                'description': meta.get('description', ''),
                'author': meta.get('author', ''),
                'default_title': meta.get('default_title', '...')
            }
    
    return books

def get_author_metadata():
    """Load author metadata from _authors directory."""
    authors = {}
    authors_dir = Path('_authors')
    
    if authors_dir.exists():
        for author_file in authors_dir.glob('*.md'):
            content = author_file.read_text(encoding='utf-8')
            meta, _ = parse_frontmatter(content)
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

def generate_epub(book_name, book_meta, poems, author_meta, output_dir):
    """Generate an epub file for a book."""
    title = book_meta.get('title', book_name)
    description = book_meta.get('description', '')
    book_author_id = book_meta.get('author', '')
    default_title = book_meta.get('default_title', '...')
    
    # Get book author display name
    if book_author_id and book_author_id in author_meta:
        book_author_name = author_meta[book_author_id]['name']
    elif book_author_id:
        book_author_name = book_author_id
    else:
        book_author_name = ''
    
    # Sort poems by date
    poems = sorted(poems, key=lambda p: p['date'])
    
    # Build markdown content
    lines = [f"# {title}\n"]
    if description:
        lines.append(f"*{description}*\n")
    lines.append("\n---\n")
    
    for poem in poems:
        poem_title = poem['title'] if poem['title'] else default_title
        lines.append(f"\n## {poem_title}\n")
        
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
            lines.append(f"*{attribution} — {date_display}*\n")
        elif attribution:
            lines.append(f"*{attribution}*\n")
        elif date_display:
            lines.append(f"*{date_display}*\n")
        
        lines.append(f"\n{poem['body']}\n")
        lines.append("\n---\n")
    
    combined = '\n'.join(lines)
    
    # Write temp markdown
    temp_file = Path(f'/tmp/{book_name}.md')
    temp_file.write_text(combined, encoding='utf-8')
    
    # Generate epub
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f'{book_name}.epub'
    
    cmd = [
        'pandoc', str(temp_file),
        '-f', 'markdown+hard_line_breaks',
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
