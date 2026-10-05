# Crimes Explained

Every crime in Title 18 of the United States Code (Part I, "Crimes"): 710 sections in their official text, annotated. A Massachusetts edition covers General Laws chapters 265, 266 and 268. Each section is color-coded to show the prohibited act, knowledge, intent, and penalty, and every citation links to its official source.

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
python3 serve.py
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
| `elements.json` | Each section's crimes broken into elements: act, ways to commit, attempt/conspiracy tags, who, federal basis, knowledge, mental state, intent, conditions, exceptions, defenses, penalty tiers (with mandatory-minimum, consecutive, and no-probation flags), other consequences, and key terms. The build shows only each section's own text: items citing another section are dropped, and penalties set elsewhere become a link such as "Set in section 924(a)(2)" |
| `ussc_frequency.py` / `frequency.json` | How common each section is: people sentenced in federal court with at least one conviction under it, from the U.S. Sentencing Commission's individual datafile (FY2025: 66,662 people). Re-run with a newer fiscal year to update. |
| `later_amendments.json` | Changes made by laws enacted after the GovInfo edition used here |
| `resolve_stat_links.py` | Finds the best GovInfo target for each Statutes at Large citation; writes `stat_links.json` and `plaw_pages.json` |
| `summary-fixes.json` | Log of corrections made when the summaries were checked against the law |

To rebuild after the source changes:

```sh
python3 ussc_frequency.py 2025 # how often each section is used (U.S. Sentencing Commission)
python3 build_data.py          # fetch the law text and merge in plain.json
python3 resolve_stat_links.py  # refresh Statutes at Large link targets
python3 build_data.py          # rebuild with the new link targets
python3 build_pages.py         # regenerate 18/*.html, assets/site.css, sitemap.xml (needs the local server and Chrome)
```

## Massachusetts (`ma/`)

The same site for the Massachusetts General Laws, starting with chapter 265 (Crimes Against the Person): a list page at `ma/index.html` and one page per section at `ma/<chapter>/<section>.html`. It reuses the root `index.html` code (the page sets `data-jur="ma"`), so styles and rendering stay in one place; `build_pages.py --jur ma` writes `ma/index.html` from `index.html`, replacing the regions marked `<!-- jur:… -->`.

| File | Purpose |
|---|---|
| `ma/fetch_ma.py` | Downloads chapters from the Legislature's public API (`malegislature.gov/api`) into `ma/raw/<chapter>.json` |
| `ma/build_ma.py` | Parses the text (paragraphs, outline levels, ½ and ¾ in numbers, quotation marks, the version of amended text in effect on the download date) and merges `ma/plain.json` and `ma/elements.json` into `ma/crimes.json` |
| `ma/plain.json` | Per section: whether it defines a crime, one-line summary, type, maximum prison term, prohibited-act phrases |
| `ma/elements.json` | Crime breakdowns, same schema as `elements.json`, from that section's own text only |
| `textlib.py` | Text helpers shared with `build_data.py` (outline levels, act ranges, the own-section-only filter) |

```sh
python3 ma/fetch_ma.py 265          # download chapter 265 (add more chapter numbers to extend)
python3 ma/build_ma.py              # build ma/crimes.json
python3 build_pages.py --jur ma     # write ma/index.html and ma/<chapter>/*.html (needs the local server and Chrome)
```

New chapters need `ma/plain.json` and `ma/elements.json` entries; `python3 ma/build_ma.py --batches DIR` writes the parsed sections in batches for review. Massachusetts has no source like the Sentencing Commission's datafile, so its list has no "Most common first" sort.

## California (`ca/`)

The Penal Code, Part 1, Title 8 (Crimes Against the Person, sections 187-248): list page `ca/index.html`, one page per section at `ca/<section>.html`. Same code as Massachusetts (`index.html` with `data-jur="ca"`).

| File | Purpose |
|---|---|
| `ca/fetch_ca.py` | Downloads the Title 8 chapter pages from leginfo.legislature.ca.gov into `ca/raw/` |
| `ca/build_ca.py` | Parses sections and outline levels and merges `ca/plain.json` and `ca/elements.json` into `ca/crimes.json`; `--batches DIR` writes review batches |
| `ca/merge_review.py` | Merges review-agent output into `ca/plain.json` and `ca/elements.json` |
| `ca/plain.json`, `ca/elements.json` | Per-section review (caption, summary, type, maximum penalty, act phrases) and crime breakdowns, own section text only |

```sh
python3 ca/fetch_ca.py && python3 ca/build_ca.py   # download and build ca/crimes.json
python3 build_pages.py --jur ca                     # write ca/index.html and ca/<section>.html (needs the local server and Chrome)
```

California has no frequency data, so its list has no "Most common first" sort. `review/ca/` holds the instructions, validator, and reviewed batches.

## Review tools

`review/federal/` and `review/ma/` hold the instructions, validators, and (federal) merge script used to produce `elements.json`, `plain.json`, and their Massachusetts counterparts with review agents. `review/ma/266/` and `review/ma/268/` hold the reviewed batches for those chapters. See `HANDOFF.md` for the current state and next steps.

## Source and limits

- Text: United States Code, 2024 edition, current through January 6, 2025, from [GovInfo](https://www.govinfo.gov/app/collection/uscode). Two sections (§1992 and §2258A) were changed by Pub. L. 119–60 (December 18, 2025); the site flags both.
- Summaries, key points, crime types, maximum-penalty labels, and prohibited-act highlights were prepared with AI assistance and checked against the text, but they may contain errors. The official text is what counts.
- Covers Title 18, Part I only. Many federal crimes are defined elsewhere, such as drug crimes in Title 21 and tax crimes in Title 26.

**This is general information, not legal advice.**
