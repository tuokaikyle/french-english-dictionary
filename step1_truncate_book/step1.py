"""
step1.py — Slice the raw book (pg74672-images.html) into five sections:
  1. EXPLANATION OF THE SIGNS USED IN THIS WORK   → truncated/explanation.html
  2. ABBREVIATIONS USED IN THIS WORK              → truncated/abbreviations.html
  3. Main French-English dictionary body           → truncated/fr_en.html
  4. VOCABULARY OF PROPER NAMES                    → truncated/proper_names.html
  5. VOCABULARY OF GEOGRAPHICAL NAMES              → truncated/geographical_names.html
"""

import os

script_dir = os.path.dirname(os.path.abspath(__file__))
truncated_dir = os.path.join(script_dir, 'truncated')
os.makedirs(truncated_dir, exist_ok=True)

file_path = os.path.join(script_dir, 'pg74672-images.html')

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# ── Helper: extract section from <h3>A … end_entry ────────────────────
def extract_section(content, heading_id, end_entry, label, output_name):
    """Find a section by heading ID, then slice from <h3>A to end_entry."""
    idx = content.find(heading_id)
    if idx == -1:
        raise SystemExit(f"Could not find heading: {heading_id}")

    start = content.find('<h3>A</h3>', idx)
    if start == -1:
        raise SystemExit(f"Could not find <h3>A</h3> after {label} heading")

    end_idx = content.find(end_entry, start)
    if end_idx == -1:
        raise SystemExit(f"Could not find end entry for {label}: {end_entry}")
    end = end_idx + len(end_entry)

    section = content[start:end]
    output_path = os.path.join(truncated_dir, output_name)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(section)
    print(f"{label}: {len(section):,} chars -> {output_path}")


# ── Helper: extract section from <h2> heading … next <hr> ────────────
def extract_h2_section(content, heading_id, label, output_name):
    """Find a section by <h2> heading ID, slice to next <hr class="chap">."""
    idx = content.find(heading_id)
    if idx == -1:
        raise SystemExit(f"Could not find heading: {heading_id}")

    # Backtrack to find the <h2> tag start
    start = content.rfind('<h2', 0, idx)
    if start == -1:
        raise SystemExit(f"Could not find <h2> start for {label}")

    end = content.find('<hr class="chap', idx)
    if end == -1:
        raise SystemExit(f"Could not find <hr> after {label}")

    section = content[start:end]
    output_path = os.path.join(truncated_dir, output_name)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(section)
    print(f"{label}: {len(section):,} chars -> {output_path}")


# ── Section 1: EXPLANATION OF THE SIGNS ──────────────────────────────
extract_h2_section(
    content,
    heading_id='EXPLANATION_OF_THE_SIGNS_USED_IN_THIS_WORK',
    label='Explanation of Signs',
    output_name='explanation.html',
)

# ── Section 2: ABBREVIATIONS USED IN THIS WORK ───────────────────────
extract_h2_section(
    content,
    heading_id='ABBREVIATIONS_USED_IN_THIS_WORK',
    label='Abbreviations',
    output_name='abbreviations.html',
)

# ── Section 3: Main dictionary body (A–zymotique) ─────────────────────
extract_section(
    content,
    heading_id='<h3>A</h3>',
    end_entry='<p><b>zymotique</b>, <i>adj.</i>, zymotic.</p>',
    label='Main dictionary body',
    output_name='fr_en.html',
)

# ── Section 4: VOCABULARY OF PROPER NAMES ─────────────────────────────
extract_section(
    content,
    heading_id='FR-EN_VOCABULARY_OF_PROPER_NAMES',
    end_entry='<p><b>Zosime</b>, <i>m.</i>, Zosimus.</p>',
    label='Proper Names',
    output_name='proper_names.html',
)

# ── Section 5: VOCABULARY OF GEOGRAPHICAL NAMES ───────────────────────
extract_section(
    content,
    heading_id='FR-EN_VOCABULARY_OF_GEOGRAPHICAL_NAMES',
    end_entry='<p><b>Zollverein</b>, <b>Le</b>, <i>m.</i>, the Zollverein.</p>',
    label='Geographical Names',
    output_name='geographical_names.html',
)