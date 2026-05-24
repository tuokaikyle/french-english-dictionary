"""
step6_2.py — Try to fit all <p> tags from all three sections into step4 patterns.
              Unmatched entries go to a single leftover HTML file.

Inputs:
  step1_truncate_book/truncated/proper_names.html
  step1_truncate_book/truncated/geographical_names.html
  step6_other_sections/redirects_flat.html

Outputs:
  step6_other_sections/combined.json
  step6_other_sections/unmatched.html
"""

import sys
import os
import json
from collections import Counter
from bs4 import BeautifulSoup

# Allow importing from step4_construct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from step4_construct.step4 import (
    get_child_sequence,
    collapse_pattern,
    clean_dict,
    PATTERN_MAP,
)


def parse_html(html_path, category):
    """
    Try to match every <p> in an HTML file against step4 patterns.
    Matched → typed entry with type "TypeName (category)".
    Unmatched → Unmatched type: { word, text, type: "Unmatched (category)" }.
    Returns list of all entries.
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    entries = []
    matched = 0
    unmatched = 0

    for p in soup.find_all('p'):
        # Skip page number markers: <p><span class="pagenum">[586]</span></p>
        if p.find('span', class_='pagenum') and len(list(p.children)) == 1:
            continue

        seq = get_child_sequence(p)
        if not seq:
            continue

        # Build collapsed pattern
        pattern_types = []
        for t, _ in seq:
            t_norm = 'text' if t == 'plural' else t
            if pattern_types and pattern_types[-1] == 'text' and t_norm == 'text':
                continue
            pattern_types.append(t_norm)
        collapsed = collapse_pattern(pattern_types)

        if collapsed in PATTERN_MAP:
            type_name, extract_fn = PATTERN_MAP[collapsed]
            try:
                entry = extract_fn(seq)
                entry = clean_dict(entry)
                entry['type'] = f"{type_name} ({category})"
                entries.append(entry)
                matched += 1
            except Exception:
                pass  # fall through to Unmatched below
            else:
                continue

        # Unmatched: first <b> = word, full text = text
        first_b = p.find('b')
        word = first_b.get_text().strip() if first_b else ''
        text = p.get_text().replace('\n', ' ').strip()
        entries.append({
            'word': word,
            'text': text,
            'type': f"Unmatched ({category})",
        })
        unmatched += 1

    return entries, matched, unmatched


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # ── Three input files ──────────────────────────────────────────────
    html_files = [
        (os.path.join(script_dir, '..', 'step1_truncate_book', 'truncated', 'proper_names.html'),    'proper_names'),
        (os.path.join(script_dir, '..', 'step1_truncate_book', 'truncated', 'geographical_names.html'), 'geographical'),
        (os.path.join(script_dir, 'redirects_flat.html'),  'redirects'),
    ]

    all_entries = []
    total_matched = 0
    total_unmatched = 0
    total_p = 0

    for path, category in html_files:
        entries, matched, unmatched = parse_html(path, category)
        all_entries.extend(entries)
        total_matched += matched
        total_unmatched += unmatched
        print(f"{category:<20} {matched:>4} matched, {unmatched:>3} unmatched")
        total_p += matched + unmatched

    # ── Write combined JSON ────────────────────────────────────────────
    output_json = os.path.join(script_dir, 'combined.json')
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)
    print(f"\nTotal <p> tags:  {total_p}")
    print(f"Matched:         {total_matched}")
    print(f"Unmatched:       {total_unmatched}")
    print(f"Combined JSON:   {output_json}")

    # ── Type breakdown ─────────────────────────────────────────────────
    type_counts = Counter(e['type'] for e in all_entries)
    print("\nBreakdown by type:")
    for t, c in type_counts.most_common():
        print(f"  {t:<30} {c:>5}")


if __name__ == '__main__':
    main()
