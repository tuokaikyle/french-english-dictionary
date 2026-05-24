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
        # <span class="plural"> — plural notation markers from step3.py
        elif child.name == 'span' and 'plural' in (child.get('class') or []):
            seq.append(('plural', child))
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


def extract_translation_and_usage(seq, start_idx):
    """
    Walk seq from start_idx, collecting translation text and usage entries.

    - Text nodes are appended to the translation.
    - <i> tags whose trailing text starts with ';' are real usage entries.
    - <i> tags whose trailing text does NOT start with ';' are inline
      italics (e.g. parenthetical notes) — their content is merged into
      the translation string.
    - <span class="plural"> elements indicate plural notation — extracted
      separately into metadata; surrounding '(' and ')' are stripped
      from the translation.

    Returns (translation: str, usage: list, plural: str | None).
    """
    translation_parts = []
    usage = []
    plural = None
    strip_next_close_paren = False
    i = start_idx

    while i < len(seq):
        kind, value = seq[i]

        if kind == 'text':
            text = value.strip()
            if strip_next_close_paren:
                text = re.sub(r'^\)\s*', '', text)
                strip_next_close_paren = False
            text = normalize_ws(text)
            if text:
                translation_parts.append(text)
            i += 1

        elif kind == 'plural':
            plural = normalize_ws(value.get_text())
            # Strip trailing '(' from the last translation part
            if translation_parts:
                translation_parts[-1] = translation_parts[-1].rstrip('( ').rstrip()
            strip_next_close_paren = True
            i += 1

        elif kind == 'i' and i + 1 < len(seq) and seq[i + 1][0] == 'text':
            fr = normalize_ws(value.get_text())
            en_raw = seq[i + 1][1].strip()

            if en_raw.startswith(';'):
                # Real usage entry
                en = normalize_ws(en_raw[1:])
                if en:
                    usage.append({'fr': fr, 'en': en})
                i += 2
            else:
                # Inline italic — merge <i> text into translation;
                # the following text node will be picked up next iteration.
                translation_parts.append(fr)
                i += 1

        else:
            # Stray <i> without trailing text, or unexpected element
            if kind == 'i':
                translation_parts.append(normalize_ws(value.get_text()))
            i += 1

    translation = ' '.join(p for p in translation_parts if p)

    # --- Post-process: extract inline usage that bled into translation ---
    # Some entries have usage examples embedded in the last text node,
    # e.g. "...glosses. — à ses fins , to attain one's ends."
    # The headword placeholder — (em-dash) marks the start of usage.
    if '—' in translation:
        dash_idx = translation.index('—')
        before_dash = translation[:dash_idx]
        # Find the last sentence boundary ( . or ; ) before the dash
        last_dot = before_dash.rfind('. ')
        last_semi = before_dash.rfind('; ')
        split_at = max(last_dot, last_semi)
        if split_at > 0:
            extra = translation[split_at + 1:].strip().lstrip('.; ')
            translation = translation[:split_at].rstrip(';. ')
            # Try to split French, English on ', '
            if extra and ', ' in extra:
                fr, _, en = extra.partition(', ')
                if fr.strip() and en.strip():
                    usage.append({'fr': fr.strip(), 'en': en.strip()})

    translation = translation.lstrip(', ')  # strip structural comma after pos
    return translation, usage, plural


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

    # translation + usage + plural from everything after the pos <i>
    translation, usage, plural = extract_translation_and_usage(seq, start_idx + 3)

    metadata = {}
    if plural:
        metadata['plural'] = plural

    return {
        'word': word,
        'irregular_pronunciation': pron,
        'pos': pos,
        'translation': translation,
        'usage': usage or None,
        **( {'metadata': metadata} if metadata else {} ),
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

    # translation + usage + plural from everything after the pos <i>
    translation, usage, plural = extract_translation_and_usage(seq, start_idx + 5)

    metadata = {'feminineSuffix': suffix}
    if plural:
        metadata['plural'] = plural

    return {
        'word': word,
        'irregular_pronunciation': pron,
        'pos': pos,
        'translation': translation,
        'usage': usage or None,
        'metadata': metadata,
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

    # translation + usage + plural from everything after the pos <i>
    translation, usage, plural = extract_translation_and_usage(seq, start_idx + 4)

    metadata = {'reflexive': reflexive}
    if plural:
        metadata['plural'] = plural

    return {
        'word': word,
        'irregular_pronunciation': pron,
        'pos': pos,
        'translation': translation,
        'usage': usage or None,
        'metadata': metadata,
    }


def extract_base_with_marker(seq, start_idx=0):
    """
    Pattern: text, b, text, i, text, (i, text)*
    The first text child is the marker ('*' or '†').
    """
    marker = seq[start_idx][1].strip()

    # Delegate to Base extraction on remaining sequence
    entry = extract_base(seq, start_idx + 1)
    if 'metadata' not in entry:
        entry['metadata'] = {}
    entry['metadata']['marker'] = marker
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

    # translation + usage + plural from everything after the second (feminine) pos <i>
    translation, usage, plural = extract_translation_and_usage(seq, start_idx + 7)

    metadata = {
        'feminineSuffix': fem_suffix,
        'femininePos': fem_pos,
    }
    if plural:
        metadata['plural'] = plural

    return {
        'word': word,
        'irregular_pronunciation': pron,
        'pos': pos,
        'translation': translation,
        'usage': usage or None,
        'metadata': metadata,
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


def extract_base_with_alt_spelling(seq, start_idx=0):
    """
    Pattern: b, i, b, text, i, text, (i, text)*
    Examples:
      <b>aboiement</b> <i>or</i> <b>aboîment</b> (-boa-mān), <i>n.m.</i>, barking...
      <b>acare</b> <i>or</i> <b>acarus</b>, <i>n.m.</i>, acarus, itch...
    """
    word = seq[start_idx][1].get_text().strip()
    alt_spelling = seq[start_idx + 2][1].get_text().strip()

    # pronunciation from text between second b and pos i (None if absent)
    pron = extract_pronunciation(seq[start_idx + 3][1]) or None if start_idx + 3 < len(seq) and seq[start_idx + 3][0] == 'text' else None

    # pos from i after the second b
    pos = ''
    if start_idx + 4 < len(seq) and seq[start_idx + 4][0] == 'i':
        pos = seq[start_idx + 4][1].get_text().strip()

    # translation + usage + plural from everything after the pos <i>
    translation, usage, plural = extract_translation_and_usage(seq, start_idx + 5)

    metadata = {'altSpelling': alt_spelling}
    if plural:
        metadata['plural'] = plural

    return {
        'word': word,
        'irregular_pronunciation': pron,
        'pos': pos,
        'translation': translation,
        'usage': usage or None,
        'metadata': metadata,
    }


# ---------------------------------------------------------------------------
# Dispatch table: collapsed pattern -> (type_name, extractor)
# ---------------------------------------------------------------------------

PATTERN_MAP = {
    'b-text-i-text':            ('Base',                        extract_base),
    'b-text-b-text-i-text':     ('BaseWithFeminine',            extract_base_with_feminine),
    'i-b-text-i-text':          ('BaseWithReflexive',           extract_base_with_reflexive),
    'text-b-text-i-text':       ('BaseWithMarker',              extract_base_with_marker),
    'b-text-i-text-b-text-i-text': ('BaseWith2GenderNoun',      extract_base_with_2gender),
    'b-i-b-text-i-text':        ('BaseWithAltSpelling',         extract_base_with_alt_spelling),
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

        # Build pattern types for matching: treat 'plural' as 'text',
        # and merge consecutive text nodes into one.
        pattern_types = []
        for t, _ in seq:
            t_norm = 'text' if t == 'plural' else t
            if pattern_types and pattern_types[-1] == 'text' and t_norm == 'text':
                continue  # merge consecutive text
            pattern_types.append(t_norm)

        collapsed = collapse_pattern(pattern_types)

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
        for tname in sorted(type_counts, key=lambda k: type_counts[k], reverse=True):
            print(f"  {tname:<30} {type_counts[tname]:>6}")
        if skipped:
            # Collect skipped patterns for reporting
            skipped_patterns = {}
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
                if collapsed not in PATTERN_MAP:
                    skipped_patterns[collapsed] = skipped_patterns.get(collapsed, 0) + 1
            print(f"\nTop skipped patterns:")
            for pat, cnt in sorted(skipped_patterns.items(), key=lambda x: -x[1])[:10]:
                print(f"  {pat:<40} {cnt:>6}")


if __name__ == '__main__':
    main()
