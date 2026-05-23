"""
step61_redirects.py — Simple extraction for proper names, geographical names,
and redirect sections.

For every <p> tag:
  - word = first <b> tag's text
  - text = entire <p> tag's text (get_text())
Matches the `Other` type: { word: string; text: string }

Inputs:
  step6_other_sections/proper_names.html
  step6_other_sections/geographical_names.html
  step3_clean_book/redirects.html

Outputs:
  step6_other_sections/proper_names.json
  step6_other_sections/geographical_names.json
  step6_other_sections/redirects.json
"""

import os
import json
from bs4 import BeautifulSoup


def extract_entries(html_path):
    """Parse an HTML file and return [{word, text}, ...] for every <p> tag."""
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    entries = []
    for p in soup.find_all('p'):
        first_b = p.find('b')
        if not first_b:
            continue
        word = first_b.get_text().strip()
        text = p.get_text().strip()
        entries.append({'word': word, 'text': text})

    return entries


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    tasks = [
        (
            os.path.join(script_dir, 'proper_names.html'),
            os.path.join(script_dir, 'proper_names.json'),
        ),
        (
            os.path.join(script_dir, 'geographical_names.html'),
            os.path.join(script_dir, 'geographical_names.json'),
        ),
        (
            os.path.join(script_dir, '..', 'step3_clean_book', 'redirects.html'),
            os.path.join(script_dir, 'redirects.json'),
        ),
    ]

    for input_path, output_path in tasks:
        entries = extract_entries(input_path)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        print(f"{os.path.basename(input_path):<30} → {len(entries):>5} entries  → {output_path}")


if __name__ == '__main__':
    main()
