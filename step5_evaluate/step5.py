"""
step5.py — Evaluate step4 coverage: which collapsed patterns are handled,
which are not, and how entries distribute across types.

Usage: uv run step5_evaluate/step5.py
"""

import sys
import os
from collections import Counter

from bs4 import BeautifulSoup, NavigableString

# Add step4_construct to path so we can reuse its logic
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(script_dir, '..', 'step4_construct'))
from step4 import (
    get_child_sequence,
    collapse_pattern,
    PATTERN_MAP,
)

# ---------------------------------------------------------------------------
# 1. Analyse clean.html — same pattern-building as step4 main loop
# ---------------------------------------------------------------------------

clean_html = os.path.join(script_dir, '..', 'step3_clean_book', 'clean.html')
with open(clean_html, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

covered_counts = Counter()
uncovered_counts = Counter()
total_tags = 0

for p in soup.find_all('p'):
    total_tags += 1
    seq = get_child_sequence(p)
    if not seq:
        continue

    # Same pattern-building as step4 main loop: plural→text, merge consecutive
    pattern_types = []
    for t, _ in seq:
        t_norm = 'text' if t == 'plural' else t
        if pattern_types and pattern_types[-1] == 'text' and t_norm == 'text':
            continue
        pattern_types.append(t_norm)

    collapsed = collapse_pattern(pattern_types)

    if collapsed in PATTERN_MAP:
        covered_counts[collapsed] += 1
    else:
        uncovered_counts[collapsed] += 1

covered_total = sum(covered_counts.values())
uncovered_total = sum(uncovered_counts.values())
covered_pct = covered_total / total_tags * 100

# ---------------------------------------------------------------------------
# 2. Report
# ---------------------------------------------------------------------------

print(f"{'='*70}")
print(f"step4 COVERAGE REPORT")
print(f"{'='*70}")
print(f"Total <p> tags:          {total_tags:>6}")
print(f"Covered by step4 types:  {covered_total:>6}  ({covered_pct:.1f}%)")
print(f"Not covered:             {uncovered_total:>6}  ({100-covered_pct:.1f}%)")
print(f"Unique covered patterns:   {len(covered_counts):>6}")
print(f"Unique uncovered patterns: {len(uncovered_counts):>6}")

# ── Top 20 covered patterns ──
print(f"\n{'─'*70}")
print(f"TOP 20 COVERED PATTERNS")
print(f"{'─'*70}")
print(f"{'Pattern':<40} {'Count':>8} {'%':>8}  {'→ Type'}")
print(f"{'─'*70}")
for pattern, count in covered_counts.most_common(20):
    pct = count / total_tags * 100
    type_name = PATTERN_MAP[pattern][0]
    print(f"{pattern:<40} {count:>8} {pct:>7.2f}%  → {type_name}")

# ── Top 20 uncovered patterns ──
print(f"\n{'─'*70}")
print(f"TOP 20 UNCOVERED PATTERNS")
print(f"{'─'*70}")
print(f"{'Pattern':<40} {'Count':>8} {'%':>8}")
print(f"{'─'*70}")
for pattern, count in uncovered_counts.most_common(20):
    pct = count / total_tags * 100
    print(f"{pattern:<40} {count:>8} {pct:>7.2f}%")

print(f"{'─'*70}")
uncovered_top20_total = sum(c for _, c in uncovered_counts.most_common(20))
print(f"{'TOP 20 UNCOVERED SUBTOTAL':<40} {uncovered_top20_total:>8} {uncovered_top20_total/total_tags*100:>7.2f}%")

# ── Type breakdown (from step4's perspective) ──
print(f"\n{'─'*70}")
print(f"TYPE BREAKDOWN  (collapsed pattern → type → count)")
print(f"{'─'*70}")
type_totals = {}
for pattern, count in covered_counts.items():
    tname = PATTERN_MAP[pattern][0]
    type_totals[tname] = type_totals.get(tname, 0) + count

print(f"{'Type':<30} {'Count':>8} {'%':>8}")
print(f"{'─'*70}")
for tname in sorted(type_totals, key=lambda k: type_totals[k], reverse=True):
    print(f"{tname:<30} {type_totals[tname]:>8} {type_totals[tname]/total_tags*100:>7.2f}%")
print(f"{'─'*70}")
print(f"{'TOTAL':<30} {sum(type_totals.values()):>8} {sum(type_totals.values())/total_tags*100:>7.2f}%")

# ── Write uncovered entries to TSV ──
tsv_path = os.path.join(script_dir, 'uncovered.tsv')
with open(tsv_path, 'w', encoding='utf-8') as tsv:
    tsv.write("word\ttag_length\tpattern\tpattern_count\n")
    for p in soup.find_all('p'):
        seq = get_child_sequence(p)
        if not seq:
            continue
        pattern_types = []
        for t, _ in seq:
            t_norm = 'text' if t == 'plural' else t
            if pattern_types and pattern_types[-1] == 'text' and t_norm == 'text':
                continue
            pattern_types.append(t_norm)
        collapsed = collapse_pattern(pattern_types)
        if collapsed in PATTERN_MAP:
            continue
        first_b = p.find('b')
        word = first_b.get_text(strip=True) if first_b else '?'
        tag_length = len(p.get_text(strip=True))
        tsv.write(f"{word}\t{tag_length}\t{collapsed}\t{uncovered_counts[collapsed]}\n")

print(f"\nWrote uncovered entries to {tsv_path}")
