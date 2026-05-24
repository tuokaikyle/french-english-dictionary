import json
import re
import shutil
from pathlib import Path

# --- Helper: patterns for what counts as "consecutive" <i> tags ---
# Each pattern describes what can sit between </i> and the next <i>.
_CONNECTORS_CHECK = [
    r"</i>\s*<i>",            # whitespace (space, newline, etc.) or nothing
    r"</i>\s+and\s+<i>",     # " and "
    r"</i>\s*,\s+<i>",       # ", "
]
_CONNECTORS_EXTRACT = [
    r"<i>(.*?)</i>\s*<i>(.*?)</i>",
    r"<i>(.*?)</i>\s+and\s+<i>(.*?)</i>",
    r"<i>(.*?)</i>\s*,\s+<i>(.*?)</i>",
]
_CONNECTORS_REMOVE = [
    (r"</i>\s*<i>",          ""),     # remove </i><i> entirely
    (r"</i>\s+and\s+<i>",    " and "),
    (r"</i>\s*,\s+<i>",      ", "),
]


def has_consecutive_i(text: str) -> bool:
    """Return True if text contains any consecutive <i> tags."""
    return any(re.search(pat, text) for pat in _CONNECTORS_CHECK)


def find_consecutive_i_groups(text: str) -> list:
    """Return list of (content1, content2) for all consecutive <i> pairs."""
    groups = []
    for pat in _CONNECTORS_EXTRACT:
        groups.extend(re.findall(pat, text))
    return groups


def merge_i_tags(html_text: str) -> str:
    """Merge consecutive <i> tags, preserving text between them."""
    for pattern, replacement in _CONNECTORS_REMOVE:
        while True:
            merged = re.sub(pattern, replacement, html_text)
            if merged == html_text:
                break
            html_text = merged
    return html_text


# --- Load abbreviations ---
with open("z/abbreviations.json") as f:
    abbrs = {item["abbr"] for item in json.load(f)}
abbrs.update(["n.f.", "n.m."])

src = Path("step5_evaluate/uncovered.html")
dst_dir = Path("step7_edge_cases/step72")
dst_dir.mkdir(parents=True, exist_ok=True)
dst = dst_dir / "uncovered.html"

shutil.copy2(src, dst)
print(f"Copied {src} -> {dst}")

# --- Find rows with consecutive <i> tags whose content is in abbreviations ---
html = dst.read_text(encoding="utf-8")

# Find all <p> blocks with their full text
p_blocks = re.findall(r"<p>.*?</p>", html, re.DOTALL)

all_count = 0
abbr_count = 0
abbr_matched_blocks = []
other_consecutive_blocks = []

remaining_html = html

for block in p_blocks:
    inner = block[3:-4]  # strip <p> and </p>
    if not has_consecutive_i(inner):
        continue
    all_count += 1

    consecutive_groups = find_consecutive_i_groups(inner)

    # Check if at least one consecutive pair has both contents in abbrs
    has_abbr_consecutive = any(
        a in abbrs and b in abbrs for a, b in consecutive_groups
    )

    if has_abbr_consecutive:
        abbr_count += 1
        abbr_matched_blocks.append(block)
        remaining_html = remaining_html.replace(block, "", 1)

# --- Second pass: move remaining blocks with consecutive <i> to other_consecutive_i.html ---
remaining_blocks = re.findall(r"<p>.*?</p>", remaining_html, re.DOTALL)
other_html = remaining_html

for block in remaining_blocks:
    inner = block[3:-4]
    if has_consecutive_i(inner):
        other_consecutive_blocks.append(block)
        other_html = other_html.replace(block, "", 1)

# --- Write multiplePos.html (abbreviation-pair entries) ---
multiple_pos_path = dst_dir / "multiplePos.html"
with open(multiple_pos_path, "w", encoding="utf-8") as f:
    f.write("\n".join(abbr_matched_blocks) + "\n")
print(f"Wrote {len(abbr_matched_blocks)} entries to {multiple_pos_path}")

# --- Write other_consecutive_i.html (remaining consecutive <i> entries) ---
other_consecutive_path = dst_dir / "other_consecutive_i.html"
with open(other_consecutive_path, "w", encoding="utf-8") as f:
    f.write("\n".join(other_consecutive_blocks) + "\n")
print(f"Wrote {len(other_consecutive_blocks)} entries to {other_consecutive_path}")

# --- Write updated uncovered.html (without either category) ---
other_html = re.sub(r"\n\s*\n\s*\n+", "\n\n", other_html)
dst.write_text(other_html, encoding="utf-8")
print(f"Updated {dst} (removed {len(abbr_matched_blocks) + len(other_consecutive_blocks)} entries)")

print(f"\nTotal with consecutive <i>: {all_count}")
print(f"Moved to multiplePos.html (known abbreviations): {abbr_count}")
print(f"Moved to other_consecutive_i.html (other consecutive <i>): {len(other_consecutive_blocks)}")

# --- Merge consecutive <i> tags in multiplePos.html ---
multiple_html = multiple_pos_path.read_text(encoding="utf-8")
merged_html = merge_i_tags(multiple_html)
multiple_pos_path.write_text(merged_html, encoding="utf-8")
print(f"Merged consecutive <i> tags in {multiple_pos_path}")

# --- Merge consecutive <i> tags in other_consecutive_i.html ---
other_html = other_consecutive_path.read_text(encoding="utf-8")
merged_other = merge_i_tags(other_html)
other_consecutive_path.write_text(merged_other, encoding="utf-8")
print(f"Merged consecutive <i> tags in {other_consecutive_path}")
