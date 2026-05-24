"""
step6_1.py — Dissolve <i>V.</i> + following <b> tags in redirects.html
             (Sections 1 & 2 moved upstream to step1_truncate_book/step1.py)
"""

import os

script_dir = os.path.dirname(os.path.abspath(__file__))

# ── Section 3: dissolve <i>V.</i> + following <b> in redirects.html ────
from bs4 import BeautifulSoup, NavigableString

redirects_path = os.path.join(script_dir, '..', 'step3_clean_book', 'redirects.html')
output3 = os.path.join(script_dir, 'redirects_flat.html')

with open(redirects_path, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

count = 0
for p in soup.find_all('p'):
    v_tag = p.find(
        'i',
        string=lambda s: s and (s.strip() == 'V.' or s.strip().startswith('(V.'))
    )
    if v_tag:
        v_text = v_tag.get_text().strip()

        # Collect <b> siblings after <i>V.</i>, stopping at next <i>
        b_siblings = []
        for sibling in v_tag.next_siblings:
            if sibling.name == 'b':
                b_siblings.append(sibling)
            elif sibling.name == 'i':
                break

        # Replace <i>V.</i> with text
        v_tag.replace_with(NavigableString(v_text + ' '))

        # Replace following <b> tags with their text
        for b in b_siblings:
            b.replace_with(NavigableString(b.get_text()))

        count += 1

with open(output3, 'w', encoding='utf-8') as f:
    f.write(str(soup))

print(f"Section 3 (Redirects flat): {count} <i>V.</i> + targets dissolved -> {output3}")
