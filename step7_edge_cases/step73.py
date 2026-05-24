"""
step73.py — Map <p> tags from step72 HTML files to existing step4 patterns.

Reads all 3 HTML files under step7_edge_cases/step72/ (*.html, not the TSV),
computes the collapsed child-element pattern for each <p> tag, matches against
step4's PATTERN_MAP, and writes matched entries to step72.json.

Usage: uv run step7_edge_cases/step73.py
"""

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

# Add step4_construct to path so we can reuse its logic
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(script_dir, '..', 'step4_construct'))
from step4 import (
    get_child_sequence,
    collapse_pattern,
    PATTERN_MAP,
    clean_dict,
)

# ---------------------------------------------------------------------------
# Gather HTML files
# ---------------------------------------------------------------------------
step72_dir = Path(script_dir) / "step72"
html_files = sorted(step72_dir.glob("*.html"))
print(f"Found {len(html_files)} HTML file(s):")
for f in html_files:
    print(f"  {f.name}")

# ---------------------------------------------------------------------------
# Process all <p> tags
# ---------------------------------------------------------------------------
entries = []
total = 0
matched = 0
type_counts = Counter()
file_matched = Counter()
skipped_patterns = Counter()

for html_path in html_files:
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    for p in soup.find_all("p"):
        total += 1
        seq = get_child_sequence(p)
        if not seq:
            continue

        # Build pattern types: treat 'plural' as 'text',
        # merge consecutive text nodes.
        pattern_types = []
        for t, _ in seq:
            t_norm = "text" if t == "plural" else t
            if pattern_types and pattern_types[-1] == "text" and t_norm == "text":
                continue
            pattern_types.append(t_norm)

        collapsed = collapse_pattern(pattern_types)

        if collapsed in PATTERN_MAP:
            type_name, extract_fn = PATTERN_MAP[collapsed]
            try:
                entry = extract_fn(seq)
                entry = clean_dict(entry)
                entry["type"] = f"{type_name} ({html_path.name})"
                entries.append(entry)
                matched += 1
                type_counts[type_name] += 1
                file_matched[html_path.name] += 1
            except Exception as e:
                if "--verbose" in sys.argv:
                    print(f"Warning: failed to extract {type_name} from "
                          f"{html_path.name}: {p.get_text(strip=True)[:80]}... — {e}")
        else:
            skipped_patterns[collapsed] += 1
            # Fallback: map to Unmatched type.
            # "word" = text between first <b> open tag and last </b> close tag.
            b_tags = p.find_all("b")
            if b_tags:
                first_b = b_tags[0]
                last_b = b_tags[-1]
                word_parts = []
                started = False
                for child in p.descendants:
                    if child is first_b:
                        started = True
                    if started and isinstance(child, NavigableString):
                        word_parts.append(child.string)
                    if child is last_b:
                        word_parts.append(last_b.get_text())
                        break
                    if started and child.name == "b":
                        word_parts.append(child.get_text())
                word = " ".join(word_parts)
                # Collapse all whitespace (including newlines) into single spaces
                word = re.sub(r"\s+", " ", word).strip()
            else:
                word = "?"
            text = p.get_text(strip=True)
            text = re.sub(r"\s+", " ", text)
            entries.append({
                "word": word,
                "text": text,
                "type": f"Unmatched ({html_path.name})",
            })

# ---------------------------------------------------------------------------
# Write step72.json
# ---------------------------------------------------------------------------
output_path = step72_dir / "step72.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(entries, f, ensure_ascii=False, indent=2)
print(f"\nWrote {len(entries)} entries to {output_path}")

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
print(f"\n{'='*60}")
print(f"Total <p> tags:      {total}")
print(f"Matched entries:     {matched}  ({matched/total*100:.1f}%)")
print(f"Unmatched entries:   {total - matched}  ({(total-matched)/total*100:.1f}%)")

print(f"\nBreakdown by type:")
for tname in sorted(type_counts, key=lambda k: type_counts[k], reverse=True):
    print(f"  {tname:<30} {type_counts[tname]:>6}")
print(f"  {'Unmatched':<30} {total - matched:>6}")

print(f"\nBreakdown by source file:")
for fname in sorted(file_matched.keys()):
    print(f"  {fname:<40} {file_matched[fname]:>6}")

if skipped_patterns:
    print(f"\nTop skipped patterns:")
    for pat, cnt in skipped_patterns.most_common(15):
        print(f"  {pat:<45} {cnt:>6}")
