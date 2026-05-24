import re
from pathlib import Path

html_file = Path(__file__).parent / "uncovered.html"
html = html_file.read_text(encoding="utf-8")

# Find all <p> blocks
p_blocks = re.findall(r"<p>.*?</p>", html, re.DOTALL)

# Consecutive: </i> directly next to <i>, or joined by " and "
consecutive_pattern = re.compile(r"</i>(\s*|\s+and\s+)<i>")

count = 0

for i, block in enumerate(p_blocks, 1):
    inner = block[3:-4]
    groups = re.findall(r"<i>(.*?)</i>(?:\s*|\s+and\s+)<i>(.*?)</i>", inner)
    if groups:
        count += 1
        print(f"--- Entry {i} ---")
        for a, b in groups:
            print(f"  <i>{a}</i> + <i>{b}</i>")
        print()

print(f"Total entries with consecutive <i> tags: {count}")
