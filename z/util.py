"""
Utility: search for a word in an HTML file and print matching <p> tags.
         parse abbreviations.html into JSON.

Usage:
  uv run z/util.py <word> <html_path>
  uv run z/util.py --abbrs              # parse abbreviations.html → JSON
"""

import sys
import os
import json
from bs4 import BeautifulSoup


def parse_abbreviations():
    """
    Parse step1_truncate_book/truncated/abbreviations.html into a list of dicts.

    Each <li> has the format:  abbr., english, <i>french</i>.
    Example:  <li>adj., adjective, <i>adjectif</i>.</li>

    Returns:
        list[dict]: [{"abbr": "adj.", "english": "adjective", "french": "adjectif"}, ...]
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(
        script_dir, '..', 'step1_truncate_book', 'truncated', 'abbreviations.html'
    )

    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    result = []
    # Only parse <li> inside the first <ul> (there may be other <ul>s)
    ul = soup.find('ul')
    if not ul:
        return result

    for li in ul.find_all('li'):
        abbr_tag = li.find('b')
        if abbr_tag:
            # Some entries have <b> around the abbreviation
            abbr = abbr_tag.get_text(strip=True)
        else:
            abbr = None

        i_tag = li.find('i')
        french = i_tag.get_text(strip=True) if i_tag else ''

        # Get the full text and extract english part between ", " and the french
        full_text = li.get_text().strip()
        # Remove trailing period
        if full_text.endswith('.'):
            full_text = full_text[:-1]

        # Split:  "adj., adjective, adjectif"
        # We have abbr from <b> or first comma-separated part
        # English is between the first two commas, French is after last comma

        if abbr is None:
            # No <b> tag, parse from text: "adj., adjective, adjectif"
            parts = full_text.split(',', 2)
            abbr = parts[0].strip() if len(parts) > 0 else ''
            english = parts[1].strip() if len(parts) > 1 else ''
        else:
            # Abbreviation already extracted, get the rest
            rest = full_text[len(abbr):].lstrip(',').strip()
            # Now rest is "adjective, adjectif"
            parts = rest.rsplit(',', 1)
            english = parts[0].strip() if len(parts) > 0 else ''

        result.append({
            'abbr': abbr,
            'english': english,
            'french': french,
        })

    return result


def main():
    # ── Subcommand: parse abbreviations ──────────────────────────
    if len(sys.argv) >= 2 and sys.argv[1] in ('--abbrs', '--abbreviations'):
        abbrs = parse_abbreviations()
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'abbreviations.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(abbrs, f, indent=2, ensure_ascii=False)
        print(f"Wrote {len(abbrs)} abbreviations to {out_path}")
        return

    # ── Subcommand: search word in HTML ──────────────────────────
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
