"""
Utility: search for a word in an HTML file and print matching <p> tags.

Usage:
  uv run z/util.py <word> <html_path>
  uv run z/util.py abaisser step3_clean_book/clean.html
"""

import sys
import os
from bs4 import BeautifulSoup


def main():
    if len(sys.argv) < 3:
        print("Usage: uv run z/util.py <word> <html_path>")
        print("Example: uv run z/util.py abaisser step3_clean_book/clean.html")
        sys.exit(1)

    word = sys.argv[1]
    html_path = sys.argv[2]

    if not os.path.exists(html_path):
        print(f"Error: file not found: {html_path}")
        sys.exit(1)

    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    matches = []
    for p in soup.find_all('p'):
        # Search only within <b> tags inside the <p>, case-insensitive
        bold_tags = p.find_all('b')
        if any(word.lower() in b.get_text().lower() for b in bold_tags):
            matches.append(p)

    if not matches:
        print(f"No <p> tags found containing '{word}'.")
        sys.exit(0)

    print(f"Found {len(matches)} <p> tag(s) containing '{word}':\n")
    for i, p in enumerate(matches, 1):
        print(f"{'─' * 70}")
        print(f"  [{i}]")
        print(f"{'─' * 70}")
        # Print the raw HTML of the <p> tag, pretty-formatted
        print(p.prettify())
        print()


if __name__ == '__main__':
    main()
