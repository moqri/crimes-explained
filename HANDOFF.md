# Handoff: continuing Crimes Explained

Notes for picking this project up in a new Claude Code session or account. Read this first, then `README.md` (files and build commands).

- **Live site:** https://crimes.wiki/ (Federal), https://crimes.wiki/ma/ (Massachusetts), https://crimes.wiki/ny/ (New York), https://crimes.wiki/ca/ (California)
- **Repo:** https://github.com/moqri/crimes-explained (public, GitHub Pages from `main`, root folder)
- **Local copies:** `/Users/mahdimoqri/ai/usc18` on one Mac, `/Users/admin/ai/usc18` on another (the paths below use the first; use whichever copy you are in). `ny/.api_key` is gitignored, so each machine needs its own copy of the key.
- **State as of 2026-10-05:** everything is committed and pushed. Nothing is running except possibly a local server.

## What the site is

"Crimes Explained": every crime in a criminal code, as official text, annotated and linked, with each crime broken into its elements. Page titles are "Crimes Explained: Federal", "Crimes Explained: Massachusetts" and "Crimes Explained: California" and "Crimes Explained: New York"; the switch at the top of the list pages says Federal / Massachusetts / California / New York (full names).

- **Federal:** Title 18, Part I of the U.S. Code (GovInfo 2024 edition, current through Jan. 6, 2025): 710 sections, 1,731 crimes. List page `index.html`, one page per section `18/<section>.html`.
- **Massachusetts:** General Laws chapters 265 (Crimes Against the Person), 266 (Crimes Against Property) and 268 (Crimes Against Public Justice); official text from the Legislature's API: 317 sections, 569 crimes (265: 83/153, 266: 187/336, 268: 47/80). List page `ma/index.html` (generated), section pages `ma/<chapter>/<section>.html`.
- **California:** Penal Code, Part 1, Title 8 (Of Crimes Against the Person, sections 187-248; chapters 1, 2, 3, 3.5, 4, 5, 6, 8, 9) and Title 13 (Of Crimes Against Property, sections 450-593g; chapters 1-8, 10, 12, 12.5, 12.6, 12.7, 14, 15): 377 sections parsed, 279 define crimes, 532 crimes (Title 8: 141, Title 13: 391). Official text from leginfo.legislature.ca.gov. Chapter keys are `<title>:<chapter>` (e.g. `13:5`; shown as "Title 13, Ch. 5") because both titles number chapters from 1. List page `ca/index.html` (generated), section pages `ca/<section>.html` (e.g. `ca/243.4.html`). The Penal Code has no section headings, so each section's caption is written by the reviewer (`title` in `ca/plain.json`) and the site says so.
- **New York:** Penal Law, Part 3, Title H (Articles 120 assault, 121 strangulation, 125 homicide, 130 sex offenses, 135 kidnapping/coercion), Title I (140 burglary/trespass, 145 criminal mischief, 150 arson) and Title J (155 larceny, 156 computer offenses, 158 welfare fraud, 160 robbery, 165 other theft offenses): 199 sections parsed, 164 define crimes, 370 crimes. Official text and official section titles from the NY Senate Open Legislation API. List page `ny/index.html` (generated), section pages `ny/<section>.html` (e.g. `ny/120.05.html`, `ny/130.65-A.html`).
- Each section page ends with a "Simplified explanation" box (the section's plain-English summary; there is no per-crime summary).
- The list pages keep search and filters in the URL (`?q=&chapter=&type=&penalty=&sort=&text=0`).

## How to build and preview

The page builder renders with headless Chrome against a local server, so start one first, **from inside `usc18`**:

```sh
cd /Users/mahdimoqri/ai/usc18 && python3 serve.py     # serves http://localhost:8000/
```

Federal: `python3 build_data.py` then `python3 build_pages.py`.
Massachusetts: `python3 ma/fetch_ma.py <chapters…>`, then review (below), `python3 ma/build_ma.py`, then `python3 build_pages.py --jur ma`.
California: `python3 ca/fetch_ca.py`, review, `python3 ca/build_ca.py`, `python3 build_pages.py --jur ca`.
New York: `python3 ny/fetch_ny.py`, review, `python3 ny/build_ny.py`, `python3 build_pages.py --jur ny`.
After any data rebuild, run `python3 related.py` (writes `related.json`, the "Related crimes" box on section pages) before `build_pages.py` "In other jurisdictions" shows the single best match from each other jurisdiction, in the order Federal, Massachusetts, New York, California, and only when it scores at least `OTHER_MIN` and shares the crime type (or scores at least `OTHER_ANY_TYPE`); a jurisdiction without a good match is left out. The scoring is word overlap (TF-IDF), so lowering the thresholds brings in wrong matches. Run `build_pages.py` for all four jurisdictions after any change to `index.html` (it also rewrites `assets/site.css`, `assets/page.js`, `sitemap.xml`).

Key design: **`index.html` is the single source** of styles and rendering code for both jurisdictions. The page sets `data-jur="ma"` for Massachusetts; `build_pages.py --jur ma` writes `ma/index.html` from `index.html`, swapping the regions marked `<!-- jur:nav|lede|about|footer -->`. Shared Python text helpers are in `textlib.py`.

## Adding a Massachusetts chapter (the workflow used for 266 and 268)

1. `python3 ma/fetch_ma.py <chapter>` downloads `ma/raw/<chapter>.json`.
2. `mkdir -p review/ma/<chapter> && python3 ma/build_ma.py --batches review/ma/<chapter>` writes `in_01.json …` (batches of 30 unreviewed sections).
3. One review agent per batch, run one at a time (they use a lot of the user's usage limit; ask before launching many). Each follows `review/ma/INSTRUCTIONS.md` and validates with `python3 review/ma/validate.py <in> <out>` until it prints OK.
4. `python3 ma/merge_review.py review/ma/<chapter>/out_*.json`, then `python3 ma/build_ma.py` and `python3 build_pages.py --jur ma`. Check links (internal targets exist, external return 200); add cited sections that no longer exist to `MA_DEAD` in `index.html`.
5. `build_ma.py` leaves unreviewed sections out, so rebuilding at any point is safe. The header lists included chapters automatically.

## California (`ca/`)

Same design as Massachusetts: `index.html` has `data-jur="ca"` support (CA citation patterns, penalty wording, glossary, severity tiers; no frequency sort), `build_pages.py --jur ca` writes `ca/index.html` and `ca/<section>.html`. Workflow: `python3 ca/fetch_ca.py [--resume]` (reads each title's chapter list from its official table of contents, `TITLES` in the script, and downloads chapter pages to `ca/raw/<title>-<chapter>.html`; the site is slow, `--resume` reuses pages already downloaded), `python3 ca/build_ca.py --batches review/ca` (batches of 30 sections not yet in `ca/plain.json`), one review agent per batch run one at a time following `review/ca/INSTRUCTIONS.md` and validated with `python3 review/ca/validate.py <in> <out>`, `python3 ca/merge_review.py review/ca/out_*.json`, `python3 ca/build_ca.py`, `python3 build_pages.py --jur ca`. Extra rules: a "wobbler" tier flag; penalties set by Section 1170(h) are quoted, not expanded; maxYears 1000 = death, 999 = life. Cited sections that do not exist go in `CA_DEAD` in `index.html`. A section amended with a delayed start appears twice on leginfo (e.g. 451.5, current until 2029 and its replacement); `build_ca.py` keeps the version in effect on the download date. Title 13 reviews are in `review/ca/t13/`; New York Titles I and J in `review/ny/ij/`.

## New York (`ny/`)

Same design: `data-jur="ny"` in `index.html`, `build_pages.py --jur ny`. **API key:** `ny/fetch_ny.py` needs a free NY Senate Open Legislation key (sign up at https://legislation.nysenate.gov/), read ONLY from `ny/.api_key` (gitignored, chmod 600) or the env var `NYSENATE_API_KEY`; never print it or write it into any file (the repo is public). The script makes two requests (structure, then the whole Penal Law with `full=true`) and saves Titles H, I and J to `ny/raw/titleH.json`, `titleI.json`, `titleJ.json` (the list is `TITLES` in `fetch_ny.py` and `build_ny.py`) plus the structure to `ny/raw/structure.json` (no key in either). Workflow: `python3 ny/fetch_ny.py`, `python3 ny/build_ny.py --batches review/ny` (batches of 30), one review agent per batch run one at a time following `review/ny/INSTRUCTIONS.md` and validated with `python3 review/ny/validate.py <in> <out>`, `python3 ny/merge_review.py review/ny/out_*.json`, `python3 ny/build_ny.py`, `python3 build_pages.py --jur ny`.
Specifics: sections are `120.05`, `130.65-A` (file names too); captions are the official titles; the sentence of a crime is its class ("Class D felony (sentence set in Penal Law Article 70)"), never an Article 70/80 range: `penClass` in `ny/plain.json` drives the badge and filter (class A to E, misdemeanors, violation) and `maxYears` stays null unless the section states a term. Crimes `where` is "1", "3-a", "1(a)". Citations link to `https://www.nysenate.gov/legislation/laws/<LAWID>/<section>` (articles use ids like `P3THA125`, from `articleIds` in `ny/crimes.json`; `penSections` lists every Penal Law section so cites to repealed ones, `NY_DEAD`, stay unlinked). nysenate.gov returns 403 to scripts (bot challenge); the URL forms were verified against the API's location ids instead. Glossary meanings of felony/misdemeanor/physical injury/mental states are general explanations of Penal Law sections 10.00 and 15.05.

Other Title-level work not done: more of the Penal Code (Title 9 sex crimes 261+, weapons Part 6) and other codes (Health and Safety 11350+, Vehicle).

## U.S. Constitution (`constitution/`)

Started 2026-10-06 at the user's request: expand to the federal and state constitutions, U.S. first, on the same site (`crimes.wiki/constitution/`), annotated for rights, powers and limits. Every list page has a "Crimes | U.S. Constitution" switch (`docnav`) above the jurisdiction switch.

- **Source:** GovInfo, *The Constitution of the United States of America, As Amended* (House Document 110-50, GPO 2007; no amendment since). `python3 constitution/fetch_con.py` saves `constitution/raw/us.htm` (plain text in `<pre>`).
- **Units (74 provisions):** the Preamble, each section of Articles I-IV, Articles V-VII, and each amendment or amendment section. Ids `preamble`, `art1-s8`, `art5`, `amend1`, `amend14-s1` (also the page file names). Parts (`chapter`): `pre`, `1`-`7`, `BR` (Amendments I-X), `AM` (XI-XXVII). Clause numbers of the GPO print become paragraph labels `[3]`; GPO notes ("This clause has been affected by amendment XVII") become footnotes, with the clause each is attached to (`noteClauses`). The signatures and the unratified amendments are left out. Amendments carry their proposal and ratification note as `source`.
- **Workflow:** `python3 constitution/build_con.py --batches review/con/us` (batches of 20), one review agent per batch following `review/con/INSTRUCTIONS.md`, validated with `python3 review/con/validate.py <in> <out>`, `python3 constitution/merge_review.py review/con/us/out_*.json`, `python3 constitution/build_con.py`, `python3 build_pages.py --jur con`.
- **Review data:** `constitution/plain.json` (title, plain, category = topic, kind = Right/Power/Limit/Duty/Structure, and highlight phrases `rights`/`powers`/`limits`); `constitution/elements.json` (`provisions`: where, kind, what, holder, binds, requires, forbids, conditions, exceptions, terms, changedBy).
- **Page code:** `index.html` with `data-doc="con"` (the `CON` flag): its own glossary, topics, kinds (the card bar color), legend (right green `--hl-right`, power highlighted, limit red), `provisionsHTML` breakdown (holder/binds shown once when shared), amendment citations linked to their pages (`conLink`). `build_pages.py --jur con` writes `constitution/index.html` and `constitution/<id>.html`.
- **Rule:** breakdowns describe only the text and GPO notes, never case law or interpretation (the validator rejects case names, "courts have held", "incorporated", "doctrine").
- **Open items:** the GPO note on Art. I, Section 3, clause 2 reads "clause 2 of amendment XVIII" (it links to Amendment XVIII); the vacancy rule is in Amendment XVII, so the note is probably a misprint in the source, kept as published. Reviewers inserted a few bracketed words in breakdowns ("nor shall [any person] be compelled") and assigned holders like "The people" for the religion clauses; judgment calls: amend14-s2 (Structure), amend14-s3 (Limit, Equality & Citizenship), amend14-s4 (Taxes, Money & Commerce), amend18-s1/amend21-s2/amend27 (no named actor, binds null), amend23-s1 and amend25-s4 (kinds), art4-s2 [3] (duty), art6 (States & Federalism).
- **Massachusetts Constitution (`ma/constitution/`, started 2026-10-06):** source https://malegislature.gov/Laws/Constitution (the whole text on one page; the Legislature's API, https://malegislature.gov/api/swagger/index.html, has no constitution routes). `python3 constitution/fetch_ma.py` → `ma/constitution/raw/constitution.html`; `python3 constitution/build_ma.py [--batches DIR --start N]`; reviews in `review/con/ma/` following `review/con/INSTRUCTIONS.md` plus `review/con/INSTRUCTIONS_MA.md`, validated with `python3 review/con/validate.py --jur ma <in> <out>`; `python3 constitution/merge_review.py --into ma/constitution review/con/ma/out_*.json`; `python3 build_pages.py --jur macon`. Units: preamble, `decl1`-`decl30` (Declaration of Rights), `p2` (Part the Second's opening), `p2-c1-s2-a7` (chapter/section/article), `amend1`-`amend121`, with Article XLVIII split into its parts (`amend48-init-initpeti2`, `amend48-ref-…`, `amend48-gen-…`). The Legislature's bracketed notes ("[Annulled by …]", "[See Amendments, Arts. …]") become footnotes and link to the articles they name; other bracketed words are superseded wording kept in the text. Each provision has a `status`: in force / partly superseded / superseded (whole text bracketed) / annulled (a note says so); cards show it. The page's own links between articles become paragraph link ranges (`p.l`).
- **Massachusetts Constitution judgment calls and source quirks (from the review agents):**
  - MA Constitution batch 1: decl3/decl16 annulled (notes now captured); decl13 Structure (no stated right); decl17 Individual Rights (arms + military); decl11 The Courts.
  - MA Constitution batch 2: p2-c1-s2-a1 superseded (whole text bracketed); decl30 (Part 2 opening moved to its own provision "p2"); p2-c1-s1-a2 (veto article under The Legislature); p2-c1-s2-a2 ("unincorporated" reworded in breakdown because of a since-fixed validator rule).
  - MA Constitution batch 3: p2-c1-s3-a2 partly superseded (only the fines power unbracketed); p2-c2-s1-a3 ("[majority]" dropped from the breakdown wording); p2-c1-s3-a4 superseded voting text kind Right; p2-c1-s3-a7 Taxes, Money & Commerce; p2-c1-s3-a10 freedom from arrest as a right.
  - MA Constitution batch 4: p2-c2-s3-a2/a4/a7 annulled ("Superseded by" notes); p2-c2-s4-a1 superseded; p2-c2-s1-a7 note "Annulled and superseded by See Amendments, Art. LIV" copied as printed; p2-c2-s1-a9 a malformed nested bracket note in the source stays in the text; p2-c2-s1-a5 partly superseded.
  - MA Constitution batch 5: p2-c3-a2 annulled ("Amended and superseded" note on the whole article); p2-c6-a1 Quaker affirmation paragraph has a stray "]" in the source, treated as in force; p2-c6-a1/a2 The Governor & Executive; p2-c6-a3/a9 superseded; p2-c6-a7 habeas corpus as Individual Rights.
  - MA Constitution batch 6: amend1/12/18 annulled (whole text bracketed, "Superseded by" notes); amend15 superseded; amend10 in-text "[This paragraph superseded …]" note used in changedBy; amend11 in force (only cross-references); amend13 kind Limit; amend4 notes assigned to the paragraphs they name; amend19 Voting & Elections.
  - MA Constitution batch 7: amend31 superseded (no note); amend39 kind Power though it amends Decl. Art. X; amend28 stray "]" in the source, partly superseded; amend21/22/23 annulled; amend28/30 voting disqualification bans as Limit.
  - MA Constitution batch 8: amend46 Section 2 stray "]" in the source (in force); amend48-init-legiaction5 annulled (in-text "superseded" notes); bracketed sections in initpeti2, legiaction4, refepeti3 → partly superseded; unlabeled paragraphs after Section 2 of initpeti2 have where ""; amend43 The Legislature, amend47 Taxes, Money & Commerce.
  - MA Constitution batch 9: amend48 General Provisions V (Veto Power of the Governor) and VI (Power of Repeal) carry the same sentence on malegislature.gov (probable source error, kept as published); amend48-gen-infoforvote4 annulled (in-text "Subheading IV superseded" notes); amend58 and amend62 annulled ("Superseded by" notes; amend62 has a stray "]" after Section 1); amend63 annulled although its brackets cover only Sections 2 and 5 (could be partly superseded); amend57 partly superseded.
  - MA Constitution batch 10: amend74 stray "]" (in force); amend64 annulled though Sections 2-3 are unbracketed (notes say annulled); amend71 annulled (whole-article "Superseded" note); amend68 Amending & Ratifying; amend81 headings shortened with "…" because of a since-fixed validator rule, repeated "Section 2" labels.
  - MA Constitution batch 11: source typos copied as printed ("dopted" in amend89, a doubled phrase in its Section 6, "Articles of the Articles of Amendments" in amend90); amend101 census paragraph has a closing "]" without an opening one (partly superseded); amend89 home rule as Power; amend91 last paragraph printed twice in the source; amend90 Structure with highlights; amendments to Art. III (incl. amend68) under Voting & Elections.
  - MA Constitution batch 12: amend104-107 and 110 take the kind of their replacement text; amend117 partly superseded ("[fifth]"); amend119 new paragraph where ""; amend121 Structure with one limit highlight; amend112/116 Structure; amend106 Equality & Citizenship; amend118 Structure; amend109 "oF" copied as printed.
- **New York Constitution (`ny/constitution/`, 2026-10-06, complete):** source the NY Senate Open Legislation API, law id `CNS` (`https://legislation.nysenate.gov/api/3/laws/CNS?full=true&key=…`; same key as the Penal Law; public pages https://www.nysenate.gov/legislation/laws/CNS/A1S6). `python3 constitution/fetch_ny.py` → `ny/constitution/raw/cns.json`; `python3 constitution/build_ny.py [--batches DIR --start N]` (202 provisions: preamble and `a1-s1` … `a20-s1`; official section titles are the captions; the Senate's "*So in original" notes become footnotes); reviews in `review/con/ny/` (11 batches of 20) following `review/con/INSTRUCTIONS.md` plus `review/con/INSTRUCTIONS_NY.md`, validated with `python3 review/con/validate.py --jur ny <in> <out>`; `python3 constitution/merge_review.py --into ny/constitution review/con/ny/out_*.json`; `python3 build_pages.py --jur nycon`. All 202 provisions are reviewed and published (1,076 breakdown entries). Citations like "section 6 of article seven" link to that section (`nycLink`).
- **New York Constitution judgment calls (from the review agents):**
  - NY Constitution batch 1: a1-s7 text goes from (a) to (c) as published; a1-s6 waiver-of-immunity disqualification as a limit; a1-s9 kind Limit vs Right; a1-s1/s2/s9 Individual Rights, a1-s14 Founding & Purposes; a1-s18 Social Welfare, a1-s19 Conservation (after a validator fix).
  - NY Constitution batch 2: a3-s4 unlabeled paragraphs given the label of the subdivision above; a3-s5-b last "(i)" read as subdivision (i); a2-s7/s8 Structure; a2-s4 Limit; a3-s6 salary as a right of members; a3-s11 speech or debate as a right.
  - NY Constitution batch 3: a3-s25 "power and immediate duty" as Power; a3-s24 Duty vs Limit; a3-s21 Structure; a3-s20/s23 no highlights; a4-s6 Structure; a4-s7 (veto) Power in 11 entries.
  - NY Constitution batch 4: a5-s1 Structure (taxpayer's suit as a right); a5-s6 Duty (civil service merit and fitness); a6 jurisdiction sections Power, court organization Structure; a6-s3 b(1)-(3) appeals as of right with no named holder.
  - NY Constitution batch 5: a6-s18 jury trial under The Courts; a6-s22 misprint "an*" kept as printed; a6-s20 b(1)-(4) court list put in binds; a6-s32 The Courts/Duty (child's religion); a6-s29/s33 Duty.
  - NY Constitution batch 6: a6-s35 appeal routes as rights; a6-s36-a/s36-c effective-date rules, no highlights; a7-s8 "banking organizations" in terms (only "as defined by the legislature"); a7-s12/s13/s14 unlabeled paragraphs where "".
  - NY Constitution batch 7: Article VIII (local finances) under Local Government; a8-s5/a8-s7-a continuation paragraphs take their lettered paragraph's label; a8-s10 lists school districts without a percentage, described as printed.
  - NY Constitution batch 8: a9-s1/s2 heading-only first paragraphs not entered; a9-s2 (b)(1)-(3) "the legislature Shall …"; a9-s1 (b) election of local officers as structure; a11-s1 education as a right; a13-s4 The Legislature; a10-s2 no highlights.
  - NY Constitution batch 9: a14-s1 (forest preserve, many land exchanges) one entry per conveyance, kind Limit, some long descriptions shortened; a13-s13 (b) governor's removal duty; a14-s5 citizen suits as a right; a15 (canals) under Taxes, Money & Commerce.
  - NY Constitution batch 10: a17-s1/s3 (aid to the needy, public health) Duty with no highlights; a18-s3 Structure, inline (a)-(c) kept in the text; a18-s6 occupancy preference as a right; a19-s1 Structure, misprint "th*" kept; a19-s2 delegate pay as a right.
  - NY Constitution batch 11: a20-s1 Amending & Ratifying; a19-s3 Structure, no highlights.
- **Next:** California (leginfo `CONS`; it returned 403 on 2026-10-06, retry). The California crimes page's Constitution button goes to the U.S. Constitution until then. New York: the Senate API has it (law id `CNS`, 20 articles, 201 sections; same key). Massachusetts: malegislature.gov/Laws/Constitution (Declaration of Rights, Frame of Government, ~120 Articles of Amendment). California: leginfo `CONS` (returned 403 on 2026-10-06, possibly temporary). Each needs a fetch/parse script, the jurisdiction switch on the constitution pages, and its own review batches.

## States investigated and blocked

- **Texas:** statutes.capitol.texas.gov is a JavaScript app; no bulk download or API was found.

## The user's rules and preferences (follow these)

Content and accuracy
- "Set in Section X" only when the section's own text names Section X; otherwise "No punishment is stated in this section". (Title 8 still has older entries like 187 "Set in Section 190" that predate this.)
- **Each section's crime list uses only that section's own text.** Never borrow mental states, definitions, penalties, or exceptions from another section; point to it with a link instead (e.g. "Penalty: Set in section 924(a)(2)"). Enforced by `own_text_only` in `textlib.py`.
- Use only official sources: GovInfo for federal (not Cornell, not the House site); malegislature.gov for Massachusetts.
- No "Other" crime type.
- Knowledge ("knowingly", "knowing that …") is its own category (teal), not intent.

Official-text highlighting
- Prohibited act: amber background; always starts with the infinitive "to" when there is one; never a lone trailing "." or other punctuation.
- Mental state (knowledge, intent, recklessness, negligence: knowingly, willfully, with intent to, recklessly, wantonly, negligently, with criminal negligence…): ONE category, teal, in the official text and in the breakdown. The breakdown has a single "Mental state" row that merges the data fields `knowledge`, `mentalState` and `intent` (the JSON keeps them separate; the reviewers still fill them in). The word lists are `INTENT_KEYS` / `KNOWLEDGE_KEYS` in `index.html` (both render teal), and each jurisdiction's glossary must contain a term for a word to be colored.
- Conditions: only the word "if"/"unless" is marked, italic, in purple (the color `--hl-intent`; `.condw` in `index.html`). Penalty: only the penalty action word is red (e.g. "fined", "imprisoned", "class D felony"); the rest stays plain.
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
- Review agents fail with "Your computer went to sleep" if the Mac sleeps; run `caffeinate -s -i` while they run and keep the lid open.
- The user asked to stop the running review agents (usage limits) and to stop the local server; check before launching many agents again.

## Open items (offered, not started)

- New York judgment calls to check legally: 130.91 (sexually motivated felony, no class stated, penClass null); 120.03/120.04/120.04-A (presumptions put in conditions); 125.13/125.14 (7 subdivisions each as separate crimes); 121.11 (paragraphs a and b as two crimes); 120.05 subdivisions 3 and 11 (long victim lists summarized); 120.70 (category Family & Children); 135.35 subd. 3 and 135.60 (one crime with long condition lists). Other New York Penal Law titles (K fraud/forgery, Article 220 drugs, 265 weapons) not done.

- Title 13 / Titles I-J judgment calls to check legally (from the review agents):
  - NY I/J batch 1: 145.50 (littering on tracks; no class, fine/community service tiers, maxYears null); 145.40/145.45 (consumer product tampering categorized Violence & Threats); 140.10 (paragraphs a-g as 7 crimes); 140.25/140.30 (each aggravating circumstance a separate crime); 145.30 (presumption in subd. 2 put in conditions).
  - NY I/J batch 2: 155.35/155.40/155.42 (duplicate subdivision numbers from separately amended versions, both kept); 156.25(2) (prior conviction kept as its own crime); 145.70 (Fraud & Money; presumption omitted); 156.40 (gambling crime in Article 156, categorized Cyber); 150.01-150.20 and 155.43 (act phrases include "intentionally" or a cross-reference because the act is one sentence).
  - NY I/J batch 3: 160.00 (robbery defined, no class: marked not a crime); 165.15 (theft of services: subd. 5 split into 5(a)-(c); felony clause wording copied onto 5(a) and 5(b); presumptions put in conditions); 165.05/165.08/165.30 (presumptions in knowledge/intent); 165.16 (Fraud & Money); 158.35 (alternatives (i) and (ii) as two crimes).
  - NY I/J batch 4: 165.45 subd. 3 (broker/dealer put in who) and subd. 7 (methamphetamine use kept as a condition); 165.71-165.73 (trademark counterfeiting split into selling and possessing); 165.66 (Property Crimes); 165.35 (fortune telling, Fraud & Money).
  - CA Title 13 batch 1: 459 (burglary defined, kept as a crime with penalty "Set in Section 461", like 187); 451.1/452.1 (arson enhancements kept as crimes) vs 456 (fine add-on, not a crime); 462.5 (felony version max null); 457.1 (registration, Property Crimes); 466.65(a) (split, device crime without intent); 453, 461(b), 463, 465 (wobblers: max 1 from the county-jail year, maxPlus); 452(a)-(c) flagged wobblers.
  - CA Title 13 batch 2: 484 (theft defined) marked not a crime, unlike 459 burglary; 470-472, 475, 476 ("Set in Section 473") and 477 ("Set in Section 478") although those sections do not name 473/478; 484.1, 484c, 484e (guilty of theft/embezzlement, no punishment stated); 481.1(a) (max 1 from jail term); 468 sniperscope (Weapons & Terrorism); 466.8 (locksmith records); 484b/474 (Fraud & Money).
  - CA Title 13 batch 3: 487 (grand theft defined) and 486, 488 marked not crimes (like 484), punishment shown under 489; 490.1 (infraction petty theft kept as a crime); 490.5 (civil damages as a civil tier); 484f-487m "Guilty of X (no punishment is stated in this section)"; 487a(a) split into 4 crimes; animal theft (487e-487g) Property Crimes.
  - CA Title 13 batch 4: 496d, 500, 502(d) (max 3 from the term the section states under 1170(h)); 490.8 (restraining order; Courts & Justice); 502.7/502.8 (toll fraud as Cyber); 499d (wobbler, Property Crimes); 496a(b)/(c) record-keeping duties not listed as crimes; 499c(d) "no defense" rule placed in consequences.
  - CA Title 13 batch 5: 506a (collectors as agents) not a crime; 518/519 (extortion defined) not crimes; 514 (embezzlement punishment "in the manner prescribed for theft"); 504-508 "Guilty of embezzlement (no punishment stated)"; 524 (attempted extortion wobbler); 523 (Violence & Threats incl. ransomware); 521/522 and 528/528.5 (Fraud & Money).
  - CA Title 13 batch 6: 530/532 ("same manner as for larceny", no section named); 530.5(c)(3) (10+ victims as its own crime); 530.5(d)(2), 533 (1170(h) with no term, max null); 532(b)/532d(b) evidence rules placed in defenses/conditions; 537(c) presumption in consequences.
  - CA Title 13 batch 7: 538 (mortgaged property sale; Fraud & Money; exception from an incomplete sentence); 555.3 (article-wide misdemeanor kept as a crime) while 555-555.2 show "No punishment is stated in this section"; 538d/538e/538g (badge makers' fine as a separate tier); 548-550 (per-prior enhancements, max null); 539 (Courts & Justice).
  - CA Title 13 batch 8: 558 (Scripps lands, no punishment stated; 558.1 punishes); 571 (subleasing defined) not a crime, 570 act has no verb; 560-581 (1170(h) with no term, max null); 558.1/587b ("30 days" as 0.08 years); 560/560.6 (knowledge clause and exception applied to all three acts); railroad sections 587-587b as Property Crimes, fare evasion 587c as Fraud & Money.
  - CA Title 13 batch 9: 588a (Property Crimes though the felony needs intent to cause great bodily injury); 588b ("wilfully" only on the first act); 593d-593f (Cyber); 593a (consecutive 3-year injury term as a tier); 593g (operative only if SB 1176 was enacted; note left out).

- California judgment calls to check legally: 187, 189, 192, 193, 193.5, 204, 207, 211, 214, 236, 240 (definition-only sections kept as crimes with the penalty "Set in Section X"); 212.5, 242, 243.85 (marked not crimes); 190.2 (aiders and major participants split into separate crimes); 243.4(k); 241.4; 217.1.

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
