#!/usr/bin/env python3
"""
Validate mandatory fields across the poetry archive.

Authors: name must be defined.
Books: title, author, and date must have valid values.
Poems (published only): books, authors, and text must have valid values.
"""

import re
import sys
import yaml
from pathlib import Path


def parse_frontmatter(content):
    """Extract YAML frontmatter from markdown file."""
    if not content.startswith('---'):
        return None

    parts = content.split('---', 2)
    if len(parts) < 3:
        return None

    try:
        frontmatter = yaml.safe_load(parts[1])
        return frontmatter if frontmatter else {}
    except yaml.YAMLError as e:
        return None


def validate_authors(authors_dir):
    """Validate all author files. Returns (author_ids, errors)."""
    errors = []
    author_ids = set()

    if not authors_dir.exists():
        errors.append("Directory _authors/ does not exist")
        return author_ids, errors

    for author_file in sorted(authors_dir.glob('*.md')):
        author_id = author_file.stem
        author_ids.add(author_id)
        content = author_file.read_text(encoding='utf-8')
        meta = parse_frontmatter(content)

        if meta is None:
            errors.append(f"_authors/{author_id}.md: invalid or missing frontmatter")
            continue

        name = meta.get('name', '')
        if not isinstance(name, str) or not name.strip():
            errors.append(f"_authors/{author_id}.md: missing or empty 'name'")

    return author_ids, errors


def validate_date(date_value):
    """Check that a date value is a valid YYYY-MM-DD date."""
    # PyYAML may parse dates as datetime.date objects
    if hasattr(date_value, 'isoformat'):
        return True
    # Also accept string in YYYY-MM-DD format
    if isinstance(date_value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', date_value):
        return True
    return False


def validate_books(books_dir, known_authors):
    """Validate all book files. Returns (book_ids, errors)."""
    errors = []
    book_ids = set()

    if not books_dir.exists():
        errors.append("Directory _books/ does not exist")
        return book_ids, errors

    for book_file in sorted(books_dir.glob('*.md')):
        book_id = book_file.stem
        book_ids.add(book_id)
        content = book_file.read_text(encoding='utf-8')
        meta = parse_frontmatter(content)

        if meta is None:
            errors.append(f"_books/{book_id}.md: invalid or missing frontmatter")
            continue

        # title: non-empty string
        title = meta.get('title', '')
        if not isinstance(title, str) or not title.strip():
            errors.append(f"_books/{book_id}.md: missing or empty 'title'")

        # author: must be a known author
        author = meta.get('author', '')
        if not isinstance(author, str) or not author.strip():
            errors.append(f"_books/{book_id}.md: missing or empty 'author'")
        elif author.strip() not in known_authors:
            errors.append(
                f"_books/{book_id}.md: author '{author.strip()}' "
                f"not found in _authors/ (known: {sorted(known_authors)})"
            )

        # date: must be a valid date
        date = meta.get('date')
        if date is None:
            errors.append(f"_books/{book_id}.md: missing 'date'")
        elif not validate_date(date):
            errors.append(
                f"_books/{book_id}.md: 'date' must be a valid YYYY-MM-DD date, "
                f"got: {date!r}"
            )

    return book_ids, errors


def validate_poems(poems_dir, known_authors, known_books):
    """Validate published poem files. Returns errors."""
    errors = []

    if not poems_dir.exists():
        errors.append("Directory _poems/ does not exist")
        return errors

    for poem_file in sorted(poems_dir.rglob('*.md')):
        rel_path = poem_file.relative_to(poems_dir.parent)
        content = poem_file.read_text(encoding='utf-8')
        meta = parse_frontmatter(content)

        if meta is None:
            errors.append(f"{rel_path}: invalid or missing frontmatter")
            continue

        # Check if published (has books field)
        books_str = meta.get('books', meta.get('book', ''))
        if not books_str:
            continue  # Draft, skip validation

        # books: all must be known
        book_list = [b.strip() for b in str(books_str).split(',') if b.strip()]
        for book_id in book_list:
            if book_id not in known_books:
                errors.append(
                    f"{rel_path}: book '{book_id}' "
                    f"not found in _books/ (known: {sorted(known_books)})"
                )

        # authors: non-empty, all must be known
        authors_str = meta.get('authors', '')
        if not authors_str:
            errors.append(f"{rel_path}: missing or empty 'authors'")
        else:
            author_list = [a.strip() for a in str(authors_str).split(',') if a.strip()]
            if not author_list:
                errors.append(f"{rel_path}: 'authors' has no valid entries")
            for author_id in author_list:
                if author_id not in known_authors:
                    errors.append(
                        f"{rel_path}: author '{author_id}' "
                        f"not found in _authors/ (known: {sorted(known_authors)})"
                    )

        # text: non-empty
        text = meta.get('text', '')
        if not isinstance(text, str) or not text.strip():
            errors.append(f"{rel_path}: missing or empty 'text'")

    return errors


def main():
    root = Path('.')

    all_errors = []

    # 1. Validate authors first (other validations depend on known author IDs)
    known_authors, author_errors = validate_authors(root / '_authors')
    all_errors.extend(author_errors)

    # 2. Validate books (depends on known authors)
    known_books, book_errors = validate_books(root / '_books', known_authors)
    all_errors.extend(book_errors)

    # 3. Validate published poems (depends on known authors and books)
    poem_errors = validate_poems(root / '_poems', known_authors, known_books)
    all_errors.extend(poem_errors)

    # Report
    if all_errors:
        print(f"Validation failed with {len(all_errors)} error(s):\n")
        for error in all_errors:
            print(f"  ERROR: {error}")
        sys.exit(1)
    else:
        print("Validation passed.")
        print(f"  {len(known_authors)} author(s), {len(known_books)} book(s)")
        sys.exit(0)


if __name__ == '__main__':
    main()
