"""
step61_redirects.py — Preprocess redirects.html into a flat HTML that step4
can parse natively.

Transform:  <i>V.</i> <b>target</b>  →  V. target  (plain text)
            <i>(V.</i> <b>target</b>.) → (V. target.)  (plain text)

Dissolving stops at the next <i> after V. (preserves usage entries).
Outputs: step6_other_sections/redirects_flat.html
"""

import os
from bs4 import BeautifulSoup, NavigableString


def dissolve_redirect(p):
    """
    In a <p> tag:
      1. Find <i>V.</i> and dissolve it + following <b> tags into plain text.
         Stops dissolving when hitting another <i>.
      2. Dissolve extra <b> tags before V. (after the first one) into text.
         e.g. <b>aggrégat</b>, <b>aggrégation</b> → <b>aggrégat</b>, aggrégation
    Modifies the tree in-place.
    """
    # ── Step 1: dissolve V. region ──────────────────────────────────
    v_tag = p.find(
        'i',
        string=lambda s: s and (s.strip() == 'V.' or s.strip().startswith('(V.'))
    )
    if not v_tag:
        return

    v_text = v_tag.get_text().strip()

    # Collect <b> siblings after <i>V.</i>, stopping at next <i>
    b_siblings_after = []
    for sibling in v_tag.next_siblings:
        if sibling.name == 'b':
            b_siblings_after.append(sibling)
        elif sibling.name == 'i':
            break

    # Replace <i>V.</i> with text
    v_tag.replace_with(NavigableString(v_text + ' '))

    # Replace collected <b> tags with their text
    for b in b_siblings_after:
        b.replace_with(NavigableString(b.get_text()))

    # ── Step 2: dissolve extra <b> before V. (keep only the first) ──
    all_b_tags = p.find_all('b')
    if len(all_b_tags) > 1:
        for b in all_b_tags[1:]:
            # Only dissolve if it's not a feminine suffix (-e, -ve, etc.)
            # Feminine suffixes are short dashed patterns like "-e", "-ve", "-se"
            text = b.get_text().strip()
            if text.startswith('-') and len(text) <= 4:
                continue  # keep feminine suffix <b> tags
            b.replace_with(NavigableString(text))


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, '..', 'step3_clean_book', 'redirects.html')
    output_path = os.path.join(script_dir, 'redirects_flat.html')

    with open(input_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    count = 0
    for p in soup.find_all('p'):
        dissolve_redirect(p)
        count += 1

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))

    print(f"Processed {count} <p> tags → {output_path}")


if __name__ == '__main__':
    main()
