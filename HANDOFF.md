# Handoff: continuing Crime Code

Notes for picking this project up in a new Claude Code session or account. Read this first, then `README.md` (files and build commands).

- **Live site:** https://moqri.github.io/federal-crimes-explained/ (federal) and https://moqri.github.io/federal-crimes-explained/ma/ (Massachusetts)
- **Repo:** https://github.com/moqri/federal-crimes-explained (public, GitHub Pages from `main`, root folder)
- **Local copy:** `/Users/mahdimoqri/ai/usc18` (the parent folder `/Users/mahdimoqri/ai` holds an unrelated hello-world `index.html` from the very start)
- **State as of 2026-10-04:** everything below is committed and pushed. Nothing is running (no local server, no agents).

## What the site is

"Crime Code": every crime in a criminal code, as official text, annotated and linked, with each crime broken into its elements.

- **Federal:** Title 18, Part I of the U.S. Code (GovInfo 2024 edition, current through Jan. 6, 2025): 710 sections, 1,731 crimes. List page `index.html`, one page per section `18/<section>.html`.
- **Massachusetts:** General Laws chapter 265 (Crimes Against the Person), official text from the Legislature's API: 83 sections, 153 crimes. List page `ma/index.html` (generated), section pages `ma/<chapter>/<section>.html`.
- Both list pages have a Federal / Massachusetts switch at the top.

## How to build and preview

The page builder renders with headless Chrome against a local server, so start one first:

```sh
cd /Users/mahdimoqri/ai && python3 -m http.server 8000     # serves http://localhost:8000/usc18/
```

Federal: `python3 build_data.py` then `python3 build_pages.py`.
Massachusetts: `python3 ma/fetch_ma.py <chapters…>`, `python3 ma/build_ma.py`, then `python3 build_pages.py --jur ma`.
Run `build_pages.py` for both jurisdictions after any change to `index.html` (it also rewrites `assets/site.css`, `assets/page.js`, `sitemap.xml`).

Key design: **`index.html` is the single source** of styles and rendering code for both jurisdictions. The page sets `data-jur="ma"` for Massachusetts; `build_pages.py --jur ma` writes `ma/index.html` from `index.html`, swapping the regions marked `<!-- jur:nav|lede|about|footer -->`. Shared Python text helpers are in `textlib.py`.

## In progress: Massachusetts chapter 266 (Crimes Against Property)

- `ma/raw/266.json` is downloaded (222 sections, 212 in force).
- **32 sections are reviewed** and saved in `review/ma/266/`: `out_04.json` (266/71A … 266/91B) and `out_08.json` (266/147, 266/148). Both pass the validator.
- **180 sections still need review.** They were in batches whose agents were stopped to save usage.
- `ma/build_ma.py` leaves out any section not yet in `ma/plain.json`, so chapter 266 does not appear on the site until it is reviewed. Rebuilding now is safe.

To finish it:

1. Merge the saved results into `ma/plain.json` and `ma/elements.json` (each output maps `section → {"review": {...}, "elements": {...}}`; `review` goes to plain.json, `elements` to elements.json). **Change 266/148 to `"isOffense": false`** and drop its elements: it only has civil fines and license sanctions, so it is not a crime.
2. `python3 ma/build_ma.py --batches <dir>` writes the remaining unreviewed sections in batches of 30.
3. Run one review agent per batch with `review/ma/INSTRUCTIONS.md`; each validates with `python3 review/ma/validate.py <in> <out>` until it prints OK.
4. Merge, `python3 ma/build_ma.py`, `python3 build_pages.py --jur ma`, then check links (every `xref` link on `ma/*/*.html`: internal targets exist, external return 200) and skim a few pages.
5. The header lists included chapters automatically (from `ma/crimes.json`).

Also pending from this step: chapter titles now capitalize "Against" ("Crimes Against the Person"); the change is in `ma/build_ma.py` but the published data and pages still say "against" until the next Massachusetts rebuild.

Judgment calls the chapter 266 agents flagged (worth a look): 266/75 ("as in the case of larceny" penalty, max unknown), 266/75C (which crime the exception covers), 266/76 (common-law "gross fraud or cheat"), 266/78 (split into two crimes), 266/87 (intent applied to all three acts), 266/89 (three crimes), 266/147 (tiers mixing item count, value, and prior offenses).

## The user's rules and preferences (follow these)

Content and accuracy
- **Each section's crime list uses only that section's own text.** Never borrow mental states, definitions, penalties, or exceptions from another section; point to it with a link instead (e.g. "Penalty: Set in section 924(a)(2)"). Enforced by `own_text_only` in `textlib.py`.
- Use only official sources: GovInfo for federal (not Cornell, not the House site); malegislature.gov for Massachusetts.
- No "Other" crime type.
- Knowledge ("knowingly", "knowing that …") is its own category (teal), not intent.

Official-text highlighting
- Prohibited act: amber background; always starts with the infinitive "to" when there is one; never a lone trailing "." or other punctuation.
- Knowledge: teal. Intent: purple. Conditions: only the word "if"/"unless" is marked (italic, slate). Penalty: only the penalty action word is red (e.g. "fined", "imprisoned"); the rest stays plain.
- A clause like "if … would be an offense" that defines the act is not a condition.
- No bold anywhere. Legal terms get a dotted underline with a popup, but simple phrases ("in order to", "knowing") are not underlined.
- Correct outline indentation; chained labels like "(b)(1)" on separate lines; subsections separated by dividers; separate provisions ("There is jurisdiction …", "For purposes of …") start new paragraphs.
- Every citation is a link (sections, chapters, "this chapter", other titles, Acts via their Code citations, Public Laws, Statutes at Large).

Crime breakdowns (right-hand column on section pages)
- Heading "1 crime in this section" / "N crimes in this section".
- Each crime: act, then its elements indented under it (Who only if limited, Knowledge, Intent, Conditions, Exceptions, Defenses, Penalty tiers with "If …", Other consequences, Key terms).
- "+ attempt" / "+ conspiracy" go at the bottom of each crime ("Also covers"), not next to the act.
- Fields common to all crimes go in an "Applies to all N crimes above" block at the **bottom**.
- The goal: the breakdown should be easier to read than the official text.

List page
- Filters in the order: type, chapter, penalty, sort. Default 10 per page. Chapter counts in the chapter filter.
- Federal sort "Most common first" uses U.S. Sentencing Commission FY2025 data (`ussc_frequency.py`); Massachusetts has no such data, so the option is hidden.
- Cards open section pages in a new tab. Header: short subtitle with counts; the rest in a collapsed "About this site".

Working style
- The user writes short, fast messages; interpret generously and act. Ask only when genuinely ambiguous.
- Commits: author `Mahdi Moqri <4342458+moqri@users.noreply.github.com>` (GitHub noreply; never the personal email), message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. The user usually says "push" explicitly; ask before pushing otherwise.
- The user asked to stop the running review agents (usage limits) and to stop the local server; check before launching many agents again.

## Other open items (offered, not started)

- Federal §1112/§1113 penalty tiers show "Set in another law"; a fill pass was offered (must respect the own-text rule).
- About 10 federal crimes still lack act highlights.
- Save search and filters in the URL.
- Custom domain or a repo rename (the repo name says "federal" but now holds Massachusetts too; `BASE_URL` in `build_pages.py` must change with it).
- Legal review of judgment calls (e.g. federal §709 split into 24 crimes, §922 into 45; Massachusetts 265 items such as §§1, 3, 4 having no penalty of their own, mandatory-minimum readings, §21A's ambiguous fine).
- Massachusetts frequency data: the Trial Court and the Sentencing Commission publish charge and sentencing counts; not yet checked for per-section downloads.
- More Massachusetts chapters after 266: 268 (public justice), 269 (public peace and weapons), 272 (public order), and crimes elsewhere (90 motor vehicles, 94C drugs, 140 §§121–131 firearms, 209A).

## Gotchas

- Massachusetts text quirks handled in `ma/build_ma.py`: "21/2" means 2½ and "13B1/2" is section 13B½ (file and link form `13B1~2`, matching malegislature.gov); quotation marks arrive as two apostrophes; amended sections can contain two versions with "[ … effective … ]" notes (only the version in effect on the download date is kept, e.g. 265/13D).
- Fractional sections only resolve on the full official path (`/Laws/GeneralLaws/PartIV/TitleI/Chapter265/Section13B1~2`); plain sections also work on the short path.
- Massachusetts citations may spell numbers out ("section eighty-seven of chapter two hundred and seventy-six"); `index.html` parses them (`MA_NUM`, `maNum`). "said section N" refers back and is left unlinked. `MA_DEAD` lists cited sections that no longer exist.
- `build_pages.py` needs Google Chrome at the default macOS path and the local server.
- The federal review tools (instructions, validator, merge script used for `elements.json`) are in `review/federal/`.
