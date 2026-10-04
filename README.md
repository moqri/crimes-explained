# Federal Crimes Explained

Every crime in Title 18 of the United States Code (Part I, "Crimes"): 710 sections, each with the full official text and a plain-English summary.

In the official text, color marks the parts of each crime:

- **Prohibited act** (amber highlight): what a person does that makes it a crime
- **Intent** (purple): the mental state required, such as *willfully* or *with intent to*
- **Penalty** (red): prison terms, fines, and civil penalties
- **Legal terms** (dotted underline): tap or hover for a definition

Citations link to the official sources on GovInfo (U.S. Government Publishing Office). Sections can be filtered by type of crime, maximum penalty, and chapter.

## Run locally

The page loads `crimes.json`, so serve the folder rather than opening the file directly:

```sh
python3 -m http.server 8000
# then open http://localhost:8000/
```

## Files

| File | What it is |
|---|---|
| `index.html` | The whole site: layout, styles, and the script that renders and links the text |
| `crimes.json` | Built data: official text of each section plus summaries, highlights, and link targets |
| `build_data.py` | Downloads Title 18, Part I from GovInfo and builds `crimes.json` |
| `plain.json` | Plain-English summaries, key points, penalties, crime types, and prohibited-act phrases for each section |
| `later_amendments.json` | Changes made by laws enacted after the GovInfo edition used here |
| `resolve_stat_links.py` | Finds the best GovInfo target for each Statutes at Large citation; writes `stat_links.json` and `plaw_pages.json` |
| `summary-fixes.json` | Log of corrections made when the summaries were checked against the law |

To rebuild after the source changes:

```sh
python3 build_data.py          # fetch the law text and merge in plain.json
python3 resolve_stat_links.py  # refresh Statutes at Large link targets
python3 build_data.py          # rebuild with the new link targets
```

## Source and limits

- Text: United States Code, 2024 edition, current through January 6, 2025, from [GovInfo](https://www.govinfo.gov/app/collection/uscode). Two sections (§1992 and §2258A) were changed by Pub. L. 119–60 (December 18, 2025); the site flags both.
- Summaries, key points, crime types, maximum-penalty labels, and prohibited-act highlights were prepared with AI assistance and checked against the text, but they may contain errors. The official text is what counts.
- Covers Title 18, Part I only. Many federal crimes are defined elsewhere, such as drug crimes in Title 21 and tax crimes in Title 26.

**This is general information, not legal advice.**
