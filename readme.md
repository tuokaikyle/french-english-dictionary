# French–English Dictionary Pipeline

This project converts the HTML ebook [A Pocket Dictionary of the French and English Languages](https://www.gutenberg.org/ebooks/74672) into structured JSON data.

The source ebook is kept as HTML because its formatting carries useful information: bold text identifies words, italics identify parts of speech and usage, and surrounding text contains translations and examples.

## Pipeline

| Step | Script                                          | Purpose                                                                                                                                                      |
| ---- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1    | `step1_truncate_book/step1.py`                  | Slice the raw book (`pg74672-images.html`) into 5 HTML sections: explanation, abbreviations, main dictionary body, proper names, geographical names          |
| 2    | `step2_look_structure/step2.py`                 | Inspect the main dictionary and report recurring HTML tag patterns (`b`, `i`, `text`) used inside `<p>` tags                                                 |
| 3    | `step3_clean_book/step3.py`                     | Clean the HTML: remove page markers, separate obsolete words (`☉`) and redirect entries (`V.`), normalize plural notation                                    |
| 4    | `step4_construct/step4.py`                      | **Core parser** — map recognized child-element patterns to typed JSON entries (9 types)                                                                      |
| 5    | `step5_evaluate/step5.py`                       | Evaluate coverage: report handled vs. uncovered patterns and save unmatched entries for review                                                               |
| 6    | `step6_other_sections/step6_1.py`, `step6_2.py` | Process remaining sections: dissolve `V.` redirects (`step6_1`), then parse proper names, geographical names, and redirects through the same pattern matcher |
| 7    | `step7_edge_cases/step72.py`, `step73.py`       | Handle edge cases: consecutive `<i>` tags, multiple parts of speech, alternative spellings                                                                   |

## Running the pipeline

The project uses `uv`:

```bash
uv run step1_truncate_book/step1.py
uv run step2_look_structure/step2.py
uv run step3_clean_book/step3.py
uv run step4_construct/step4.py -v
uv run step5_evaluate/step5.py
uv run step6_other_sections/step6_1.py
uv run step6_other_sections/step6_2.py
uv run step7_edge_cases/step72.py
uv run step7_edge_cases/step73.py
```

Run the stages in order because later stages use files created by earlier stages. The source ebook is large, so it should not be inspected or copied unnecessarily.

## Outputs

The main dictionary output is `step4_construct/entries.json`.

Supplementary outputs include:

- `step6_other_sections/combined.json` — proper names, geographical names, and redirects.
- `step7_edge_cases/step72/step72.json` — entries recovered from selected edge cases.
- `step5_evaluate/uncovered.html` and `uncovered.tsv` — entries and patterns not handled by the main parser.

The project currently produces these JSON files separately; it does not yet merge them into one final dataset.

## Data model

Entries generally contain `word`, `pos`, and `translation`, plus optional pronunciation, plural, metadata, or usage fields. Each entry also has a `type` field identifying the HTML pattern used to parse it. Supplementary and unmatched entries include their source category in the type.
