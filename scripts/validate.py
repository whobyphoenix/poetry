#!/usr/bin/env python3
"""
Validate mandatory fields across the poetry archive.

Authors: name must be defined. Only known fields: name, link.
Books: title, author, and date must have valid values. Only known fields:
       title, author, date, default_poem_title, cover.
Poems (published only): books, authors, and text must have valid values.
Poems (all, drafts included): only known fields: poem_title, authors, books,
       date_display, images, text, commentary. images must be a comma-separated
       list of bare file names, each listed once, each a file in
       _illustrations/YYYY/MM/, the folder matching the poem's own _poems/YYYY/MM/.
"""

import re
import sys
import unicodedata
import yaml
from collections import Counter
from pathlib import Path


AUTHOR_FIELDS = {'name', 'link'}
BOOK_FIELDS = {'title', 'author', 'date', 'default_poem_title', 'cover'}
POEM_FIELDS = {'poem_title', 'authors', 'books', 'date_display', 'images', 'text', 'commentary'}

# Front matter ends at the first line that is exactly '---' (or '...'), as in Jekyll.
# Splitting on the first '---' anywhere in the file would cut a poem whose text contains '---'.
FRONTMATTER = re.compile(r'\A---[ \t]*\r?\n(.*?)^(?:---|\.\.\.)[ \t]*\r?$', re.S | re.M)
YEAR = re.compile(r'[0-9]{4}')
MONTH = re.compile(r'[0-9]{2}')


def parse_frontmatter(content):
    """Extract YAML frontmatter from markdown file."""
    m = FRONTMATTER.match(content)
    if not m:
        return None

    try:
        frontmatter = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None
    if not frontmatter:
        return {}
    return frontmatter if isinstance(frontmatter, dict) else None


def check_unknown_fields(meta, allowed, file_label):
    """Return errors for any fields not in the allowed set."""
    unknown = set(meta.keys()) - allowed
    if unknown:
        return [f"{file_label}: unknown field(s): {', '.join(sorted(unknown))}"]
    return []


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

        errors.extend(check_unknown_fields(meta, AUTHOR_FIELDS, f"_authors/{author_id}.md"))

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

        errors.extend(check_unknown_fields(meta, BOOK_FIELDS, f"_books/{book_id}.md"))

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


def nfc(name):
    return unicodedata.normalize('NFC', name)


def files_in(folder, cache):
    """Names (NFC) of the regular files in folder, or None if it is not a directory."""
    if folder not in cache:
        cache[folder] = {nfc(p.name) for p in folder.iterdir() if p.is_file()} if folder.is_dir() else None
    return cache[folder]


def validate_images(meta, poem_file, poems_dir, illustrations_dir, cache):
    """Check the images field of one poem file, draft or published.

    images is a comma-separated list of bare file names, each listed once; each must be a
    file in _illustrations/YYYY/MM/, where YYYY/MM is the poem's own folder under _poems/.
    Names are compared with the folder's actual listing, case included, so the answer is
    the same on a case-insensitive disk (macOS) and on the build machine (Linux).
    Returns (errors, number of names listed).
    """
    if 'images' not in meta:
        return [], 0
    rel_path = poem_file.relative_to(poems_dir.parent)
    value = meta['images']
    if not isinstance(value, str) or not value.strip():
        return [f"{rel_path}: 'images' must be a comma-separated list of file names, got: {value!r}"], 0

    errors = []
    names = [nfc(n.strip()) for n in value.split(',')]
    if '' in names:
        errors.append(f"{rel_path}: 'images' has an empty entry: {value!r}")
    names = [n for n in names if n]
    counts = Counter(names)
    for name, count in counts.items():
        if count > 1:
            errors.append(f"{rel_path}: image '{name}' is listed {count} times")
    bare = []
    for name in counts:
        if '/' in name or '\\' in name:
            errors.append(f"{rel_path}: image '{name}' must be a bare file name, without a folder")
        else:
            bare.append(name)

    parts = poem_file.relative_to(poems_dir).parts
    if len(parts) != 3 or not YEAR.fullmatch(parts[0]) or not MONTH.fullmatch(parts[1]):
        errors.append(f"{rel_path}: has 'images' but is not at _poems/YYYY/MM/, so its illustrations folder is unknown")
        return errors, len(names)
    folder = illustrations_dir / parts[0] / parts[1]
    label = f"{illustrations_dir.name}/{parts[0]}/{parts[1]}/"
    present = files_in(folder, cache)
    for name in bare:
        if present is None:
            errors.append(f"{rel_path}: image '{name}' not found: folder {label} does not exist")
        elif name not in present:
            near = sorted(p for p in present if p.casefold() == name.casefold())
            hint = f" (there is {', '.join(near)}: the case differs)" if near else ''
            errors.append(f"{rel_path}: image '{name}' not found in {label}{hint}")
    return errors, len(names)


def validate_poems(poems_dir, illustrations_dir, known_authors, known_books):
    """Validate poem files. Returns (errors, number of image names listed).

    Every poem file, drafts included: known fields only, and the images check.
    Published poems (non-empty books) also: mandatory fields and known references.
    """
    errors = []
    image_names = 0
    folders = {}

    if not poems_dir.exists():
        errors.append("Directory _poems/ does not exist")
        return errors, image_names

    for poem_file in sorted(poems_dir.rglob('*.md')):
        rel_path = poem_file.relative_to(poems_dir.parent)
        content = poem_file.read_text(encoding='utf-8')
        meta = parse_frontmatter(content)

        if meta is None:
            errors.append(f"{rel_path}: invalid or missing frontmatter")
            continue

        errors.extend(check_unknown_fields(meta, POEM_FIELDS, str(rel_path)))

        # images: checked on every poem file, drafts included
        image_errors, n = validate_images(meta, poem_file, poems_dir, illustrations_dir, folders)
        errors.extend(image_errors)
        image_names += n

        # Check if published (has books field)
        books_str = meta.get('books', '')
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

    return errors, image_names


def main():
    root = Path('.')

    all_errors = []

    # 1. Validate authors first (other validations depend on known author IDs)
    known_authors, author_errors = validate_authors(root / '_authors')
    all_errors.extend(author_errors)

    # 2. Validate books (depends on known authors)
    known_books, book_errors = validate_books(root / '_books', known_authors)
    all_errors.extend(book_errors)

    # 3. Validate poems: all of them for fields and images, published ones fully
    #    (depends on known authors and books)
    poem_errors, image_names = validate_poems(root / '_poems', root / '_illustrations',
                                              known_authors, known_books)
    all_errors.extend(poem_errors)

    # Report
    if all_errors:
        print(f"Validation failed with {len(all_errors)} error(s):\n")
        for error in all_errors:
            print(f"  ERROR: {error}")
        sys.exit(1)
    else:
        print("Validation passed.")
        print(f"  {len(known_authors)} author(s), {len(known_books)} book(s), "
              f"{image_names} image name(s) in poem files")
        sys.exit(0)


if __name__ == '__main__':
    main()
