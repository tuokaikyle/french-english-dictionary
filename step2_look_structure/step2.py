from bs4 import BeautifulSoup
from collections import Counter
import random
import os
import argparse

script_dir = os.path.dirname(os.path.abspath(__file__))

parser = argparse.ArgumentParser()
parser.add_argument(
    '--input', '-i',
    type=str,
    default=None,
    help='Path to the .html file to analyze (default: step1_truncate_book/fr_en.html)'
)
args = parser.parse_args()

if args.input:
    fr_en_path = os.path.abspath(args.input)
else:
    fr_en_path = os.path.join(script_dir, '..', 'step1_truncate_book', 'truncated', 'fr_en.html')

print(f"Reading from: {os.path.normpath(fr_en_path)}\n")

with open(fr_en_path, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

patterns = []
p_tags = soup.find_all('p')
total_tags = len(p_tags)

# Map to store list of 'B' word examples for each pattern
pattern_to_b_examples = {}

# Map: collapsed pattern -> list of B-word examples
collapsed_to_b_examples = {}

# Map: collapsed pattern -> list of text lengths
collapsed_to_lengths = {}

for p in p_tags:
    structure_list = []
    for child in p.children:
        if child.name:
            structure_list.append(child.name)
        elif child.strip():
            structure_list.append('text')

    pattern_str = "-".join(structure_list)
    patterns.append(pattern_str)

    # Collapse trailing consecutive i-text into one i-text
    collapsed = list(structure_list)
    while len(collapsed) >= 4 and collapsed[-4] == 'i' and collapsed[-3] == 'text' and collapsed[-2] == 'i' and collapsed[-1] == 'text':
        collapsed.pop()  # text
        collapsed.pop()  # i
    collapsed_str = "-".join(collapsed)

    text_len = len(p.get_text(strip=True))
    if collapsed_str not in collapsed_to_lengths:
        collapsed_to_lengths[collapsed_str] = []
    collapsed_to_lengths[collapsed_str].append(text_len)

    # Check if the entry starts with 'B'
    first_bold = p.find('b')
    is_b_word = first_bold and first_bold.get_text(strip=True).lower().startswith('b')

    if is_b_word:
        first_bold_text = first_bold.get_text(strip=True)
        if pattern_str not in pattern_to_b_examples:
            pattern_to_b_examples[pattern_str] = []
        pattern_to_b_examples[pattern_str].append(first_bold_text)
        if collapsed_str not in collapsed_to_b_examples:
            collapsed_to_b_examples[collapsed_str] = []
        collapsed_to_b_examples[collapsed_str].append(first_bold_text)

# Count and display the patterns with percentages
pattern_counts = Counter(patterns)
unique_patterns = len(pattern_counts)
print(f"Analyzed {total_tags} <p> tags across {unique_patterns} unique patterns.\n")
print(f"{'Pattern':<40} | {'Count':<10} | {'Percentage':<10}")
print("-" * 70)

top_15 = pattern_counts.most_common(15)
top_15_total = sum(count for _, count in top_15)
for pattern, count in top_15:
    percentage = (count / total_tags) * 100
    label = str(pattern) if pattern else "(empty)"
    print(f"{label:<40} | {count:<10} | {percentage:>9.2f}%")

top_15_pct = (top_15_total / total_tags) * 100
missed_total = total_tags - top_15_total
missed_pct = 100 - top_15_pct
missed_pattern_count = len(pattern_counts) - 15
print("-" * 70)
print(f"{'TOP 15 SUBTOTAL':<40} | {top_15_total:<10} | {top_15_pct:>9.2f}%")
print(f"{'MISSED (remaining patterns)':<40} | {missed_total:<10} | {missed_pct:>9.2f}%")
print(f"\n({missed_pattern_count} other unique patterns account for the missed {missed_pct:.2f}%)")

# --- Table 2: collapse consecutive trailing i-text into one ---
collapsed_patterns = [p for p in collapsed_to_lengths.keys() for _ in collapsed_to_lengths[p]]
# Rebuild in original order
collapsed_patterns_ordered = []
for p in p_tags:
    structure_list = []
    for child in p.children:
        if child.name:
            structure_list.append(child.name)
        elif child.strip():
            structure_list.append('text')
    collapsed = list(structure_list)
    while len(collapsed) >= 4 and collapsed[-4] == 'i' and collapsed[-3] == 'text' and collapsed[-2] == 'i' and collapsed[-1] == 'text':
        collapsed.pop()
        collapsed.pop()
    collapsed_patterns_ordered.append("-".join(collapsed))

collapsed_counts = Counter(collapsed_patterns_ordered)
unique_collapsed = len(collapsed_counts)
print(f"\n{'='*70}")
print(f"TABLE 2: Trailing consecutive i-text collapsed into one i-text")
print(f"{'='*70}")
print(f"Unique collapsed patterns: {unique_collapsed}\n")
print(f"{'Collapsed Pattern':<40} | {'Count':<10} | {'Percentage':<10} | {'Example'}")
print("-" * 85)

collapsed_top_15 = collapsed_counts.most_common(15)
collapsed_top_15_total = sum(count for _, count in collapsed_top_15)
for pattern, count in collapsed_top_15:
    percentage = (count / total_tags) * 100
    label = str(pattern) if pattern else "(empty)"
    examples = collapsed_to_b_examples.get(pattern, [])
    example = random.choice(examples) if examples else "—"
    print(f"{label:<40} | {count:<10} | {percentage:>9.2f}% | {example}")

collapsed_top_15_pct = (collapsed_top_15_total / total_tags) * 100
collapsed_missed_total = total_tags - collapsed_top_15_total
collapsed_missed_pct = 100 - collapsed_top_15_pct
collapsed_missed_pattern_count = len(collapsed_counts) - 15
print("-" * 70)
print(f"{'TOP 15 SUBTOTAL':<40} | {collapsed_top_15_total:<10} | {collapsed_top_15_pct:>9.2f}%")
print(f"{'MISSED (remaining patterns)':<40} | {collapsed_missed_total:<10} | {collapsed_missed_pct:>9.2f}%")
print(f"\n({collapsed_missed_pattern_count} other unique collapsed patterns account for the missed {collapsed_missed_pct:.2f}%)")

