from bs4 import BeautifulSoup, NavigableString
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(script_dir, '..', 'step1_truncate_book', 'fr_en.html')
output_path = os.path.join(script_dir, 'clean.html')

with open(input_path, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

# Handle <span class="pagenum"> in two ways:
# 1. If the <p> contains ONLY the pagenum span (no other content), delete the whole <p>
# 2. If the <p> has other content too, just remove the span tag
removed_p = 0
removed_span = 0
for p in soup.find_all('p'):
    pagenum_span = p.find('span', class_='pagenum')
    if not pagenum_span:
        continue
    # Check if there's any meaningful content besides the pagenum span
    pagenum_span.extract()
    has_other_content = bool(p.find()) or bool(p.get_text(strip=True))
    if has_other_content:
        removed_span += 1
    else:
        p.decompose()
        removed_p += 1

print(f"Removed {removed_p} <p> tags (pagenum only).")
print(f"Removed {removed_span} <span class='pagenum'> tags from mixed <p> tags.")

# Save <p> tags starting with ☉ (obsolete words) to a separate file, then remove them
old_words = []
removed_old = 0
for p in soup.find_all('p'):
    if p.get_text(strip=True).startswith('☉'):
        old_words.append(str(p))
        p.decompose()
        removed_old += 1

old_path = os.path.join(script_dir, 'old_words.html')
with open(old_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(old_words))

print(f"Saved {removed_old} <p> tags starting with ☉ to {old_path}.")

# if a p tag has <i>V.</i>, save such p tags to a separate file, then remove them
redirect_entries = []
removed_redirect = 0
for p in soup.find_all('p'):
    v_found = any(i_tag.get_text(strip=True) == 'V.' for i_tag in p.find_all('i'))
    if v_found:
        redirect_entries.append(str(p))
        p.decompose()
        removed_redirect += 1

redirect_path = os.path.join(script_dir, 'redirects.html')
with open(redirect_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(redirect_entries))

print(f"Saved {removed_redirect} <p> tags with <i>V.</i> to {redirect_path}.")

# Convert plural notation <i> tags to <span class="plural">
# These appear right after the POS <i>, wrapped in parentheses: , (<i>—</i>)
# From explanation.html: (—), (—s), (n.p.), (n.s.), (lazaroni), etc.
converted_plural = 0
for p in soup.find_all('p'):
    i_tags = p.find_all('i')
    for i_tag in i_tags[1:]:  # skip the first <i> (it's the POS)
        prev = i_tag.previous_sibling
        nxt = i_tag.next_sibling
        if (isinstance(prev, NavigableString) and prev.string.rstrip().endswith('(') and
            isinstance(nxt, NavigableString) and nxt.string.lstrip().startswith(')')):
            i_tag.name = 'span'
            i_tag['class'] = 'plural'
            converted_plural += 1

print(f"Converted {converted_plural} plural notation <i> tags to <span class='plural'>.")

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(str(soup))

print(f"Saved cleaned HTML to {output_path}")