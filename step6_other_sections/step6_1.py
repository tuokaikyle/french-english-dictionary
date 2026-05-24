import os

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, '..', 'step1_truncate_book', 'pg74672-images.html')

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# ── Section 1: VOCABULARY OF PROPER NAMES ──────────────────────────────
# Heading id: FR-EN_VOCABULARY_OF_PROPER_NAMES
# Entries: Aaron … Zosime
section1_heading_id = 'FR-EN_VOCABULARY_OF_PROPER_NAMES'
section1_end_entry = '<p><b>Zosime</b>, <i>m.</i>, Zosimus.</p>'

heading1_idx = content.find(section1_heading_id)
if heading1_idx == -1:
    raise SystemExit(f"Could not find heading: {section1_heading_id}")

# Find the first <h3>A</h3> after this heading
start1 = content.find('<h3>A</h3>', heading1_idx)
if start1 == -1:
    raise SystemExit("Could not find <h3>A</h3> after proper-names heading")

end1_idx = content.find(section1_end_entry, start1)
if end1_idx == -1:
    raise SystemExit(f"Could not find end entry: {section1_end_entry}")
end1 = end1_idx + len(section1_end_entry)

section1_content = content[start1:end1]
output1 = os.path.join(script_dir, 'proper_names.html')
with open(output1, 'w', encoding='utf-8') as f:
    f.write(section1_content)
print(f"Section 1 (Proper Names): {len(section1_content):,} chars -> {output1}")

# ── Section 2: VOCABULARY OF GEOGRAPHICAL NAMES ────────────────────────
# Heading id: FR-EN_VOCABULARY_OF_GEOGRAPHICAL_NAMES
# Entries: Abdère … Zollverein
section2_heading_id = 'FR-EN_VOCABULARY_OF_GEOGRAPHICAL_NAMES'
section2_end_entry = '<p><b>Zollverein</b>, <b>Le</b>, <i>m.</i>, the Zollverein.</p>'

heading2_idx = content.find(section2_heading_id)
if heading2_idx == -1:
    raise SystemExit(f"Could not find heading: {section2_heading_id}")

start2 = content.find('<h3>A</h3>', heading2_idx)
if start2 == -1:
    raise SystemExit("Could not find <h3>A</h3> after geographical-names heading")

end2_idx = content.find(section2_end_entry, start2)
if end2_idx == -1:
    raise SystemExit(f"Could not find end entry: {section2_end_entry}")
end2 = end2_idx + len(section2_end_entry)

section2_content = content[start2:end2]
output2 = os.path.join(script_dir, 'geographical_names.html')
with open(output2, 'w', encoding='utf-8') as f:
    f.write(section2_content)
print(f"Section 2 (Geographical Names): {len(section2_content):,} chars -> {output2}")

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
