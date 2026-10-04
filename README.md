# Crime Code

Every crime in Title 18 of the United States Code (Part I, "Crimes"): 710 sections in their official text, annotated. Each section is color-coded to show the prohibited act, knowledge, intent, and penalty, and every citation links to its official source.

In the official text, color marks the parts of each crime:

- **Prohibited act** (amber highlight): what a person does that makes it a crime
- **Knowledge** (teal): what the law requires the person to be aware of, such as acting *knowingly* or knowing a statement is false
- **Intent** (purple): the purpose required, such as *willfully* or *with intent to*
- **Penalty** (red): prison terms, fines, and civil penalties
- **Legal terms** (dotted underline): tap or hover for a definition

Citations link to the official sources on GovInfo (U.S. Government Publishing Office). Sections can be filtered by type of crime, maximum penalty, and chapter.

## Pages

- `index.html`: the searchable list of all sections (search, filters, pages).
- `18/<section>.html`: one page per section with the color-coded official text and the crime breakdown, pre-rendered as static HTML so search engines can read it. Old `index.html#sec-1001` links redirect to `18/1001.html`.

## Run locally

The list page loads `crimes.json`, so serve the folder rather than opening the file directly:

```sh
python3 -m http.server 8000
# then open http://localhost:8000/
```

## Files

| File | What it is |
|---|---|
| `index.html` | The list page, and the single source of the site's styles and of the code that renders and links the text |
| `build_pages.py` | Pre-renders every section into `18/<section>.html` with that same code; writes `assets/site.css`, `assets/page.js`, `sitemap.xml`, `robots.txt` |
| `crimes.json` | Built data: official text of each section plus summaries, highlights, and link targets |
| `build_data.py` | Downloads Title 18, Part I from GovInfo and builds `crimes.json` |
| `plain.json` | Plain-English summaries, key points, penalties, crime types, and prohibited-act phrases for each section |
| `elements.json` | Each section's crimes broken into elements: act, ways to commit, attempt/conspiracy tags, who, federal basis, knowledge, mental state, intent, conditions, exceptions, defenses, penalty tiers (with mandatory-minimum, consecutive, and no-probation flags), other consequences, and key terms |
| `later_amendments.json` | Changes made by laws enacted after the GovInfo edition used here |
| `resolve_stat_links.py` | Finds the best GovInfo target for each Statutes at Large citation; writes `stat_links.json` and `plaw_pages.json` |
| `summary-fixes.json` | Log of corrections made when the summaries were checked against the law |

To rebuild after the source changes:

```sh
python3 build_data.py          # fetch the law text and merge in plain.json
python3 resolve_stat_links.py  # refresh Statutes at Large link targets
python3 build_data.py          # rebuild with the new link targets
python3 build_pages.py         # regenerate 18/*.html, assets/site.css, sitemap.xml (needs the local server and Chrome)
```

## Source and limits

- Text: United States Code, 2024 edition, current through January 6, 2025, from [GovInfo](https://www.govinfo.gov/app/collection/uscode). Two sections (§1992 and §2258A) were changed by Pub. L. 119–60 (December 18, 2025); the site flags both.
- Summaries, key points, crime types, maximum-penalty labels, and prohibited-act highlights were prepared with AI assistance and checked against the text, but they may contain errors. The official text is what counts.
- Covers Title 18, Part I only. Many federal crimes are defined elsewhere, such as drug crimes in Title 21 and tax crimes in Title 26.

**This is general information, not legal advice.**
