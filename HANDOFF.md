# Handoff: continuing Crimes Explained

Notes for picking this project up in a new Claude Code session or account. Read this first, then `README.md` (files and build commands).

- **Live site:** https://moqri.github.io/crimes-explained/ (Federal) and https://moqri.github.io/crimes-explained/ma/ (MA)
- **Repo:** https://github.com/moqri/crimes-explained (public, GitHub Pages from `main`, root folder)
- **Local copy:** `/Users/mahdimoqri/ai/usc18` (the parent folder `/Users/mahdimoqri/ai` is otherwise empty)
- **State as of 2026-10-04:** everything is committed and pushed. Nothing is running except possibly a local server.

## What the site is

"Crimes Explained": every crime in a criminal code, as official text, annotated and linked, with each crime broken into its elements. Page titles are "Crimes Explained: Federal" and "Crimes Explained: MA"; the switch at the top of the list pages says Federal / MA.

- **Federal:** Title 18, Part I of the U.S. Code (GovInfo 2024 edition, current through Jan. 6, 2025): 710 sections, 1,731 crimes. List page `index.html`, one page per section `18/<section>.html`.
- **Massachusetts:** General Laws chapters 265 (Crimes Against the Person), 266 (Crimes Against Property) and 268 (Crimes Against Public Justice); official text from the Legislature's API: 317 sections, 569 crimes (265: 83/153, 266: 187/336, 268: 47/80). List page `ma/index.html` (generated), section pages `ma/<chapter>/<section>.html`.
- Each section page ends with a "Simplified explanation" box (the section's plain-English summary; there is no per-crime summary).
- The list pages keep search and filters in the URL (`?q=&chapter=&type=&penalty=&sort=&text=0`).

## How to build and preview

The page builder renders with headless Chrome against a local server, so start one first, **from inside `usc18`**:

```sh
cd /Users/mahdimoqri/ai/usc18 && python3 serve.py     # serves http://localhost:8000/
```

Federal: `python3 build_data.py` then `python3 build_pages.py`.
Massachusetts: `python3 ma/fetch_ma.py <chapters…>`, then review (below), `python3 ma/build_ma.py`, then `python3 build_pages.py --jur ma`.
Run `build_pages.py` for both jurisdictions after any change to `index.html` (it also rewrites `assets/site.css`, `assets/page.js`, `sitemap.xml`).

Key design: **`index.html` is the single source** of styles and rendering code for both jurisdictions. The page sets `data-jur="ma"` for Massachusetts; `build_pages.py --jur ma` writes `ma/index.html` from `index.html`, swapping the regions marked `<!-- jur:nav|lede|about|footer -->`. Shared Python text helpers are in `textlib.py`.

## Adding a Massachusetts chapter (the workflow used for 266 and 268)

1. `python3 ma/fetch_ma.py <chapter>` downloads `ma/raw/<chapter>.json`.
2. `mkdir -p review/ma/<chapter> && python3 ma/build_ma.py --batches review/ma/<chapter>` writes `in_01.json …` (batches of 30 unreviewed sections).
3. One review agent per batch, run one at a time (they use a lot of the user's usage limit; ask before launching many). Each follows `review/ma/INSTRUCTIONS.md` and validates with `python3 review/ma/validate.py <in> <out>` until it prints OK.
4. `python3 ma/merge_review.py review/ma/<chapter>/out_*.json`, then `python3 ma/build_ma.py` and `python3 build_pages.py --jur ma`. Check links (internal targets exist, external return 200); add cited sections that no longer exist to `MA_DEAD` in `index.html`.
5. `build_ma.py` leaves unreviewed sections out, so rebuilding at any point is safe. The header lists included chapters automatically.

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
- Commits: author `Mahdi Moqri <4342458+moqri@users.noreply.github.com>` (GitHub noreply; never the personal email), message ends with `Co-Authored-By: the Claude model name from the session attribution reminder`. The user usually says "push" explicitly; ask before pushing otherwise.
- The user asked to stop the running review agents (usage limits) and to stop the local server; check before launching many agents again.

## Open items (offered, not started)

- More Massachusetts chapters: 269 (public peace and weapons), 272 (public order), then 94C (drugs), 90 (motor vehicles), 140 §§121–131 (firearms), 209A. Chapter 268 took 2 agent batches.
- Judgment calls to check legally: chapter 266 sections 75, 75C, 76, 78, 87, 89, 147; chapters 266/268 sections split into several crimes (266/28, 30A, 37B, 37C, 53A, 60; 268/31, 32); 268/14A marked not an offense (it only says contempt); sections with no penalty of their own (266/32–34, 37, 38, 58, 59; 268/1A, 2, 25); federal §709 split into 24 crimes, §922 into 45; Massachusetts 265 §§1, 3, 4 with no penalty of their own, mandatory-minimum readings, §21A's ambiguous fine.
- 33 federal and 21 MA sections have no numeric maximum penalty (`maxYears` null) because the penalty is set elsewhere or by reference; this is correct under the own-text rule.
- Federal §1112/§1113 penalty tiers show "Set in another law"; a fill pass was offered (must respect the own-text rule).
- About 10 federal crimes still lack act highlights.
- Per-crime simplified explanations (about 2,300 crimes) were offered and not chosen; the section summary is used instead.
- Massachusetts frequency data: the Trial Court and the Sentencing Commission publish charge and sentencing counts; not yet checked for per-section downloads.
- Custom domain.

## Gotchas

- Massachusetts text quirks handled in `ma/build_ma.py`: "21/2" means 2½ and "13B1/2" is section 13B½ (file and link form `13B1~2`, matching malegislature.gov); quotation marks arrive as two apostrophes; amended sections can contain two versions with "[ … effective … ]" notes (only the version in effect on the download date is kept, e.g. 265/13D).
- Fractional sections only resolve on the full official path (`/Laws/GeneralLaws/PartIV/TitleI/Chapter265/Section13B1~2`); plain sections also work on the short path.
- Massachusetts citations may spell numbers out ("section eighty-seven of chapter two hundred and seventy-six"); `index.html` parses them (`MA_NUM`, `maNum`). "said section N" refers back and is left unlinked. `MA_DEAD` lists cited sections that no longer exist.
- `build_pages.py` needs Google Chrome at the default macOS path and the local server.
- The federal review tools (instructions, validator, merge script used for `elements.json`) are in `review/federal/`.
