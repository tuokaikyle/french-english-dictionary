# step4.py — Walkthrough, Debugging & Tricky Parts

## Overview

`step4.py` parses `step3_clean_book/clean.html` and maps every `<p>` tag whose child-element structure matches one of the 8 TypeScript types defined in `type.ts` into a typed JSON entry. The output is `step4_construct/entries.json` — a flat array of `{ "type": "...", ... }` objects.

**Result**: 39,378 matched (98.0%) out of 40,189 `<p>` tags. 811 skipped (2.0%).

---

## Walkthrough

### Phase 1 — Compute child-element pattern

For each `<p>`, iterate its direct children and classify them as `b`, `i`, or `text` (NavigableString with non-blank stripped content). This mirrors `step2.py`:

```python
seq = [('b', <b>), ('text', ', '), ('i', <i>), ('text', ', ...'), ...]
```

### Phase 2 — Collapse trailing `i-text` pairs

Same algorithm as `step2.py`: while the last 4 elements are `i, text, i, text`, pop the last two. This normalises entries with multiple usage examples (`<i>fr</i>; en. <i>fr2</i>; en2.`) into the same collapsed pattern.

```
Raw:      b-text-i-text-i-text-i-text
Collapsed: b-text-i-text
```

### Phase 3 — Dispatch to extractor

The collapsed pattern string is looked up in a dispatch table:

| Collapsed Pattern                  | Type                  | Extractor                     |
| ---------------------------------- | --------------------- | ----------------------------- |
| `b-text-i-text`                    | `Base`                | `extract_base`                |
| `b-text-b-text-i-text`             | `BaseWithFeminine`    | `extract_base_with_feminine`  |
| `i-b-text-i-text`                  | `BaseWithReflexive`   | `extract_base_with_reflexive` |
| `text-b-text-i-text`               | `BaseWithMarker`      | `extract_base_with_marker`    |
| `b-text-i-text-b-text-i-text`      | `BaseWith2GenderNoun` | `extract_base_with_2gender`   |
| `text-b-text-b-text-i-text`        | `bouillonnant`        | `extract_marker_feminine`     |
| `text-b-text-i-text-b-text-i-text` | `baigneur`            | `extract_marker_2gender`      |
| `text-i-b-text-i-text`             | `barbouiller`         | `extract_marker_reflexive`    |

### Phase 4 — Field extraction

Each extractor knows the exact child sequence for its pattern. It walks through the raw (uncollapsed) `seq` list by index:

- **`extract_base`**: `seq[0]`=word (b), `seq[1]`=pron text, `seq[2]`=pos (i), `seq[3]`=translation, `seq[4:]`=usage pairs.
- **`extract_base_with_feminine`**: `seq[0]`=word (b), `seq[2]`=suffix (b), `seq[4]`=pos (i), …
- **Compound marker types** (`bouillonnant`, `baigneur`, `barbouiller`): strip the leading marker text (`seq[0]`), then delegate to the inner type's extractor starting at `seq[1]`.

Pronunciation is extracted via regex `\(([^)]+)\)` from the text node between a `<b>` and the following `<i>`. Empty string `""` when absent.

### Phase 5 — Output

JSON array written with `json.dump(..., ensure_ascii=False, indent=2)`. The `-v`/`--verbose` flag prints matched/skipped counts and top skipped patterns.

---

## Debugging Steps

### 1. `get_text(strip=True)` corrupts text with nested tags

**Symptom**: `"Il ne sait ni a ni b"` became `"Il ne sait nianib"`.

**Root cause**: `BeautifulSoup.Tag.get_text(strip=True)` strips whitespace from each individual text node before joining, losing spaces around nested `<span>` elements.

**Fix**: Changed all `get_text(strip=True)` to `get_text().strip()`.

### 2. `extract_base_with_reflexive` off-by-one indices

**Symptom**: 1,632 out of 1,670 `BaseWithReflexive` entries had `word: ","` and empty `pos`/`translation`.

**Root cause**: The pattern is `i, b, text, i, text` but the code accessed `seq[2]` for word instead of `seq[1]`. All five index references were off by one — the function was written as if the pattern were `i, text, b, text, i, text` (with an extra text node between the reflexive pronoun and the verb).

**Fix**: Corrected indices:

```
seq[+2] → seq[+1]   (word)
seq[+3] → seq[+2]   (pronunciation)
seq[+4] → seq[+3]   (pos)
seq[+5] → seq[+4]   (translation)
seq[+6:] → seq[+5:] (usage)
```

---

## Tricky Parts

### Collapsing vs. extraction use different sequences

The **collapsed** pattern (e.g., `b-text-i-text`) is used only for dispatch/matching. Field extraction always operates on the **raw uncollapsed** `seq`. This is critical because the raw sequence contains all the usage `<i>` tags that need to be extracted, not just the last one.

### Marker types are compound, not atomic

Types like `bouillonnant` (`text-b-text-b-text-i-text`) are not unique patterns — they are `BaseWithFeminine` with a leading marker. The extractor simply reads the marker from `seq[0]`, then delegates to the inner extractor at `seq[1:]`. This avoids duplicating extraction logic.

### Translation text starts with `, `

The text node after the first `<i>` (pos) often starts with `, ` (e.g., `", the first letter of the alphabet"`). This is left as-is in the output since it's faithful to the HTML structure. The alternative of stripping it would lose the comma that separates pos from translation in entries without pronunciation.

### Not every `i-text` pair is a usage example

The `<i>` tag is used both for usage examples (`<i>Panse d'a</i>; oval of an a.`) and for inline italic terms (`does not know <i>a</i> from <i>b</i>`). The extractor treats ALL trailing `i-text` pairs as usage, which means some entries (like the dictionary entry for "a") will have false-positive usage entries. The semantic distinction between "usage example" and "inline italic" requires context that the structural pattern alone cannot provide.
