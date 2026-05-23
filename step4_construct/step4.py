"""
step4.py — Parse clean.html <p> tags and map them to typed JSON entries.

For each <p> tag, compute the collapsed child-element pattern (same algorithm
as step2.py), match it against the 8 TypeScript types defined in type.ts, and
extract fields accordingly.  Unmatched patterns are silently skipped.

Output: step4_construct/entries.json — a flat array of { "type": "...", ... }.
"""

from bs4 import BeautifulSoup, NavigableString
import json
import os
import re
import argparse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_child_sequence(p):
    """
    Return a list of (type, element_or_text) tuples for direct children of <p>.
    type is one of 'b', 'i', 'text'.
    NavigableStrings that are blank after stripping are ignored.
    """
    seq = []
    for child in p.children:
        if isinstance(child, NavigableString):
            text = child.string
            if text and text.strip():
                seq.append(('text', text))
        elif child.name in ('b', 'i'):
            seq.append((child.name, child))
        # Other tags (e.g. <span>) that might appear as direct children are
        # treated as text by passing their get_text().
        elif child.name is not None:
            text = child.get_text(strip=True)
            if text:
                seq.append(('text', text))
    return seq


def collapse_pattern(types):
    """
    Collapse trailing consecutive i-text pairs into one i-text.
    Same algorithm as step2.py: while the last four elements are
    i, text, i, text, pop the last two.
    Returns the collapsed pattern as a hyphenated string, e.g. 'b-text-i-text'.
    """
    collapsed = list(types)
    while (
        len(collapsed) >= 4
        and collapsed[-4] == 'i'
        and collapsed[-3] == 'text'
        and collapsed[-2] == 'i'
        and collapsed[-1] == 'text'
    ):
        collapsed.pop()  # text
        collapsed.pop()  # i
    return '-'.join(collapsed)


def extract_pronunciation(text):
    """
    Extract a parenthetical pronunciation from a text node.
    Example: ' (-bèss-man), ' -> '-bèss-man'
    Returns empty string if no parenthetical found.
    """
    m = re.search(r'\(([^)]+)\)', text)
    return m.group(1) if m else ''


def normalize_ws(text):
    """
    Collapse all whitespace (including newlines) into single spaces.
    Example: ';\nair-shaft.' -> 'air-shaft.'
    """
    return re.sub(r'\s+', ' ', text).strip()


def clean_dict(d):
    """Remove keys whose value is None or an empty list."""
    result = {}
    for k, v in d.items():
        if isinstance(v, list) and not v:
            continue
        if v is None:
            continue
        if isinstance(v, dict):
            cleaned = clean_dict(v)
            if cleaned:
                result[k] = cleaned
        else:
            result[k] = v
    return result


def extract_usage(seq, start_idx):
    """
    Extract usage entries from alternating (i, text, ...) sequence.

    Real usage entries in this dictionary follow the pattern:
      <i>French phrase</i>; English translation.
    The trailing text always starts with ';'.  Pairs whose trailing text
    does NOT start with ';' are inline <i> tags (e.g. "<i>a</i> from <i>b</i>")
    and are silently skipped.

    Returns a list of {fr, en} objects with whitespace normalised.
    """
    usage = []
    i = start_idx
    while i + 1 < len(seq):
        if seq[i][0] == 'i' and seq[i + 1][0] == 'text':
            # Use get_text().strip() instead of get_text(strip=True) because
            # strip=True collapses spaces around nested tags (e.g. <span>).
            fr = normalize_ws(seq[i][1].get_text())
            en_raw = seq[i + 1][1].strip()
            # Only keep usage entries whose en text starts with ';'.
            # Entries without ';' are inline italics, not real usage.
            if en_raw.startswith(';'):
                en = normalize_ws(en_raw[1:])  # strip leading ';' + normalise
                if en:
                    usage.append({'fr': fr, 'en': en})
            i += 2
        else:
            break
    return usage


# ---------------------------------------------------------------------------
# Field extractors — one per type
# ---------------------------------------------------------------------------

def extract_base(seq, start_idx=0):
    """
    Pattern: b, text, i, text, (i, text)*
    """
    word = seq[start_idx][1].get_text().strip()

    # pronunciation from text between b and first i (None if absent)
    pron = extract_pronunciation(seq[start_idx + 1][1]) or None if start_idx + 1 < len(seq) and seq[start_idx + 1][0] == 'text' else None

    # pos from first i
    pos = ''
    if start_idx + 2 < len(seq) and seq[start_idx + 2][0] == 'i':
        pos = seq[start_idx + 2][1].get_text().strip()

    # translation from text after first i
    translation = ''
    if start_idx + 3 < len(seq) and seq[start_idx + 3][0] == 'text':
        translation = normalize_ws(seq[start_idx + 3][1])

    # usage from remaining i-text pairs
    usage = extract_usage(seq, start_idx + 4)

    return {
        'word': word,
        'pronunciation': pron,
        'pos': pos,
        'translation': translation,
        'usage': usage or None,
    }


def extract_base_with_feminine(seq, start_idx=0):
    """
    Pattern: b, text, b, text, i, text, (i, text)*
    Examples:
      <b>barbé</b>, <b>-e</b>, <i>adj.</i>, ...
      <b>barbelé</b>, <b>-e</b>, <i>adj.</i>, ...
    """
    word = seq[start_idx][1].get_text().strip()
    suffix = seq[start_idx + 2][1].get_text().strip()

    # pronunciation from text between second b and i (None if absent)
    pron = extract_pronunciation(seq[start_idx + 3][1]) or None if start_idx + 3 < len(seq) and seq[start_idx + 3][0] == 'text' else None

    # pos from i
    pos = ''
    if start_idx + 4 < len(seq) and seq[start_idx + 4][0] == 'i':
        pos = seq[start_idx + 4][1].get_text().strip()

    # translation
    translation = ''
    if start_idx + 5 < len(seq) and seq[start_idx + 5][0] == 'text':
        translation = normalize_ws(seq[start_idx + 5][1])

    usage = extract_usage(seq, start_idx + 6)

    return {
        'word': word,
        'pronunciation': pron,
        'pos': pos,
        'translation': translation,
        'usage': usage or None,
        'metadata': {'suffix': suffix},
    }


def extract_base_with_reflexive(seq, start_idx=0):
    """
    Pattern: i, b, text, i, text, (i, text)*
    Examples:
      <i>se</i> <b>blouser</b>, <i>v.r.</i>, ...
      <i>se</i> <b>battre</b>, <i>v.r.</i>, ...
    """
    reflexive = seq[start_idx][1].get_text().strip()
    word = seq[start_idx + 1][1].get_text().strip()

    # pronunciation from text between b and second i (None if absent)
    pron = extract_pronunciation(seq[start_idx + 2][1]) or None if start_idx + 2 < len(seq) and seq[start_idx + 2][0] == 'text' else None

    # pos from second i
    pos = ''
    if start_idx + 3 < len(seq) and seq[start_idx + 3][0] == 'i':
        pos = seq[start_idx + 3][1].get_text().strip()

    # translation
    translation = ''
    if start_idx + 4 < len(seq) and seq[start_idx + 4][0] == 'text':
        translation = normalize_ws(seq[start_idx + 4][1])

    usage = extract_usage(seq, start_idx + 5)

    return {
        'word': word,
        'pronunciation': pron,
        'pos': pos,
        'translation': translation,
        'usage': usage or None,
        'metadata': {'reflexive': reflexive},
    }


def extract_base_with_marker(seq, start_idx=0):
    """
    Pattern: text, b, text, i, text, (i, text)*
    The first text child is the marker ('*' or '†').
    """
    marker = seq[start_idx][1].strip()

    # Delegate to Base extraction on remaining sequence
    entry = extract_base(seq, start_idx + 1)
    entry['metadata'] = {'marker': marker}
    return entry


def extract_base_with_2gender(seq, start_idx=0):
    """
    Pattern: b, text, i, text, b, text, i, text, ...
    Examples:
      <b>bavard</b>, <i>n.m.</i>, <b>-e</b>, <i>n.f.</i>, ...
      <b>act-eur</b>, <i>n.m.</i>, <b>-rice</b>, <i>n.f.</i>, ...
    """
    word = seq[start_idx][1].get_text().strip()

    # pronunciation from text between first b and first i (None if absent)
    pron = extract_pronunciation(seq[start_idx + 1][1]) or None if start_idx + 1 < len(seq) and seq[start_idx + 1][0] == 'text' else None

    # pos from first i
    pos = ''
    if start_idx + 2 < len(seq) and seq[start_idx + 2][0] == 'i':
        pos = seq[start_idx + 2][1].get_text().strip()

    # feminine suffix from second b
    fem_suffix = seq[start_idx + 4][1].get_text().strip()

    # feminine pos from second i
    fem_pos = ''
    if start_idx + 6 < len(seq) and seq[start_idx + 6][0] == 'i':
        fem_pos = seq[start_idx + 6][1].get_text().strip()

    # translation after second i
    translation = ''
    if start_idx + 7 < len(seq) and seq[start_idx + 7][0] == 'text':
        translation = normalize_ws(seq[start_idx + 7][1])

    usage = extract_usage(seq, start_idx + 8)

    return {
        'word': word,
        'pronunciation': pron,
        'pos': pos,
        'translation': translation,
        'usage': usage or None,
        'metadata': {
            'feminineSuffix': fem_suffix,
            'femininePos': fem_pos,
        },
    }


def extract_marker_feminine(seq, start_idx=0):
    """
    Pattern: text, b, text, b, text, i, text, (i, text)*
    (= marker + BaseWithFeminine)
    """
    marker = seq[start_idx][1].strip()
    entry = extract_base_with_feminine(seq, start_idx + 1)
    entry['metadata']['marker'] = marker
    return entry


def extract_marker_2gender(seq, start_idx=0):
    """
    Pattern: text, b, text, i, text, b, text, i, text, ...
    (= marker + BaseWith2GenderNoun)
    """
    marker = seq[start_idx][1].strip()
    entry = extract_base_with_2gender(seq, start_idx + 1)
    entry['metadata']['marker'] = marker
    return entry


def extract_marker_reflexive(seq, start_idx=0):
    """
    Pattern: text, i, text, b, text, i, text, (i, text)*
    (= marker + BaseWithReflexive)
    """
    marker = seq[start_idx][1].strip()
    entry = extract_base_with_reflexive(seq, start_idx + 1)
    entry['metadata']['marker'] = marker
    return entry


# ---------------------------------------------------------------------------
# Dispatch table: collapsed pattern -> (type_name, extractor)
# ---------------------------------------------------------------------------

PATTERN_MAP = {
    'b-text-i-text':            ('Base',                        extract_base),
    'b-text-b-text-i-text':     ('BaseWithFeminine',            extract_base_with_feminine),
    'i-b-text-i-text':          ('BaseWithReflexive',           extract_base_with_reflexive),
    'text-b-text-i-text':       ('BaseWithMarker',              extract_base_with_marker),
    'b-text-i-text-b-text-i-text': ('BaseWith2GenderNoun',      extract_base_with_2gender),
    'text-b-text-b-text-i-text':   ('bouillonnant',             extract_marker_feminine),
    'text-b-text-i-text-b-text-i-text': ('baigneur',            extract_marker_2gender),
    'text-i-b-text-i-text':     ('barbouiller',                 extract_marker_reflexive),
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Parse clean.html <p> tags into typed JSON entries.'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print summary of matched/skipped entries.'
    )
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    clean_html = os.path.join(script_dir, '..', 'step3_clean_book', 'clean.html')
    output_json = os.path.join(script_dir, 'entries.json')

    with open(clean_html, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    entries = []
    total = 0
    matched = 0
    type_counts = {}

    for p in soup.find_all('p'):
        total += 1
        seq = get_child_sequence(p)
        if not seq:
            continue

        types_only = [t for t, _ in seq]
        collapsed = collapse_pattern(types_only)

        if collapsed in PATTERN_MAP:
            type_name, extract_fn = PATTERN_MAP[collapsed]
            try:
                entry = extract_fn(seq)
                entry = clean_dict(entry)
                entry['type'] = type_name
                entries.append(entry)
                matched += 1
                type_counts[type_name] = type_counts.get(type_name, 0) + 1
            except Exception as e:
                if args.verbose:
                    print(f"Warning: failed to extract {type_name} from: "
                          f"{p.get_text(strip=True)[:80]}... — {e}")

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print(f"Wrote {matched} entries to {output_json}")

    if args.verbose:
        skipped = total - matched
        print(f"\n{'='*60}")
        print(f"Total <p> tags:    {total}")
        print(f"Matched entries:   {matched}  ({matched/total*100:.1f}%)")
        print(f"Skipped entries:   {skipped}  ({skipped/total*100:.1f}%)")
        print(f"\nBreakdown by type:")
        for tname in sorted(type_counts, key=type_counts.get, reverse=True):
            print(f"  {tname:<30} {type_counts[tname]:>6}")
        if skipped:
            # Collect skipped patterns for reporting
            skipped_patterns = {}
            for p in soup.find_all('p'):
                seq = get_child_sequence(p)
                if not seq:
                    continue
                collapsed = collapse_pattern([t for t, _ in seq])
                if collapsed not in PATTERN_MAP:
                    skipped_patterns[collapsed] = skipped_patterns.get(collapsed, 0) + 1
            print(f"\nTop skipped patterns:")
            for pat, cnt in sorted(skipped_patterns.items(), key=lambda x: -x[1])[:10]:
                print(f"  {pat:<40} {cnt:>6}")


if __name__ == '__main__':
    main()
