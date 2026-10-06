# Task: review California Penal Code sections (Part 1: Title 8, Crimes Against the Person; Title 13, Crimes Against Property) and break each crime into its elements

Input: a JSON array of sections of the California Penal Code, each with `section` (the section number, e.g. "187", "243.4"), `cite`, `chapter`, and `text` (official paragraphs {i, t}; i = outline depth: (a) → (1) → (A) → (i)). Sections have no official headings, so you also write a short caption for each.

Output: ONE JSON object mapping each input `section` key → `{"review": {...}, "elements": {...}}`. Include every input section.

## Accuracy rules (critical)

- Use ONLY the text of that section. Never copy, paraphrase, or summarize text from another section, and never add outside facts, case law, jury instructions, or sentencing ranges. If the penalty, a definition, or a mental state is set in another section ("shall be punished as provided in Section 190", "as defined in Section 12022.7"), say only where it is set: a penalty tier `"penalty": "Set in Section 190"` with min/max null. Do not use the "§" sign anywhere in the output; write "Section 190". Quoting the section's own wording that mentions another section is fine (e.g. "imprisonment pursuant to subdivision (h) of Section 1170").
- Write "Set in Section X" only when this section's own text names Section X. A section that names a crime but states no punishment and names no section for it gets the penalty "No punishment is stated in this section" (min/max null).
- Stay close to the law's wording. Shorten only by dropping words. Keep "may" vs "shall", "and" vs "or", "knowingly" vs "willfully" vs "maliciously" exactly.
- Do not add a term of years that the section does not state. A felony punished only "pursuant to subdivision (h) of Section 1170" has no term in this section: say so in the law's words and leave min/max null.

## California terms

- Place of imprisonment: "state prison" (felony) vs "county jail" (misdemeanor, or a felony sentenced under subdivision (h) of Section 1170). Keep the law's words ("in a county jail", "in the state prison", "pursuant to subdivision (h) of Section 1170").
- Wobbler: a crime the section itself punishes either as a felony or as a misdemeanor (typically "by imprisonment in a county jail not exceeding one year, or by imprisonment pursuant to subdivision (h) of Section 1170" or "in the state prison"). Give such a crime ONE penalty tier listing the alternatives in the law's words and add the flag "wobbler". Do not use the word "wobbler" in the penalty text.
- "Great bodily injury", "serious bodily injury", "deadly weapon", "malice aforethought": list as `terms` only if THIS section defines them; otherwise just keep the words in `conditions`.
- Enhancements and extra terms stated in this section ("an additional and consecutive term of 3, 4, or 5 years") are penalty tiers with an `if`; do not describe enhancements that are set in other sections.
- Degrees (first/second degree murder, etc.) with different penalties are separate crimes only when this section sets what differs; if the penalty is in another section say "Set in Section X".
- Death penalty or life: `maxYears` 1000 if death is possible; 999 for life (with or without parole, "25 years to life").

## `review` fields

- `title`: a short descriptive caption for the section (2 to 8 words, no final period, plain words, e.g. "Murder defined", "Assault with a deadly weapon", "Human trafficking"). It is not an official heading; do not copy a long clause.
- `isOffense`: true if the section itself makes conduct a crime or sets the punishment for a crime it names (e.g. a section defining murder with its degrees, or "Punishment for murder"). false for sections that only define terms, set procedure, venue, sentencing administration, reporting duties, civil remedies, or programs. If false, give only `title`, `isOffense` and `plain` (one sentence on what the section does) and omit `elements`. Sections that only define terms, set procedure, venue, evidence, or civil remedies, or only say how a punishment is applied, are isOffense false.
- `plain`: one plain-English sentence (max ~35 words) saying what the crime is and, briefly, the top penalty. For general readers.
- `category`: exactly one of: "Violence & Threats", "Sex Crimes & Exploitation", "Human Trafficking & Slavery", "Weapons & Terrorism", "Fraud & Money", "Property Crimes", "Cyber, Privacy & Communications", "Government & Corruption", "Civil Rights", "Courts & Justice", "Family & Children", "Transportation & Aviation", "Animals & Wildlife".
- `maxYears`: the highest prison term in the section, as a number: years (2½ → 2.5; 6 months → 0.5; 16 months → 1.33), 1000 if death is possible, 999 for life (including "25 years to life"), 0 for fine only, null if the section sets no penalty itself.
- `maxPlus`: true if the section's punishment is partly or wholly set in another section (including "pursuant to subdivision (h) of Section 1170" and enhancements elsewhere) so the real maximum may be higher; otherwise omit.
- `acts`: list of phrases copied EXACTLY (character for character, same case and punctuation) from one paragraph's `t`, each marking the prohibited conduct itself: start at the verb ("commits an assault and battery upon another", "to transport", "has sexual intercourse or unnatural sexual intercourse with a child under 16"). Exclude "Whoever", mental-state words (knowingly, wilfully, with intent to …), "if"/"unless" conditions, and the penalty. Keep each phrase within one paragraph. One phrase per distinct prohibited act.

## `elements` (same schema as the federal site)

`{"shared": {...}, "crimes": [...]}`. Put a field in `shared` only if it is identical for every crime; crime-level fields replace shared ones.

shared (all optional):
- `who`: who can commit it, ONLY when the law limits it (e.g. "A person 18 years of age or older", "A caretaker of a person with a disability"); null when anyone ("whoever", "any person").
- `knowledge`: list. What the person must know ("Knowing or having reason to know that the person is pregnant").
- `mentalState`: list. Recklessness or negligence ("Recklessly", "With gross negligence").
- `intent`: list. Purpose ("With intent to murder", "Willfully", "Maliciously").
- `penalties`: penalty tiers (below).
- `consequences`: list. Non-prison consequences in this section: no parole/probation/furlough until a term is served, sentence served consecutively, license loss, restitution, required treatment programs, sex-offender registration if the section says so, etc.
- `terms`: list of `"\"term\": meaning"` for definitions IN THIS SECTION that decide whether the crime applies.
- Do not use `federalBasis`.

each crime:
- `where`: subsection reference like "(b)(ii)", or "" for an unlabeled section. For an unlabeled paragraph inside a subsection, use the subsection (e.g. "(a)").
- `act`: the prohibited conduct, starting with the verb, in the law's words, WITHOUT mental-state words or conditions ("Commits an assault and battery upon another by means of a dangerous weapon").
- `ways`: alternative verbs/means when the act lists several (e.g. ["assault", "assault and battery"]); otherwise [].
- `tags`: subset of ["attempt", "conspiracy"] when the section makes attempting/conspiring punishable the same way.
- `conditions`: list. Facts that must be true for the act to be this crime ("The victim is 60 years or older", "The victim is under 16", "Serious bodily injury results").
- `exceptions`, `defenses`: lists, from this section only.
- `who`, `knowledge`, `mentalState`, `intent`, `penalties`, `consequences`, `terms`: only when different from shared.

Property crimes (Title 13): a value threshold ("the value of the money, labor, real or personal property taken exceeds nine hundred fifty dollars"), the kind of property, or the kind of building ("an inhabited dwelling house") is a condition, in the law's words; a different penalty by value or by kind of building is a penalty tier with `if`, not a new crime, unless the section defines a separate act. Sections that only define a term, a degree, or how value is measured (such as the degrees of burglary or the definition of theft) are isOffense false unless they themselves state a punishment. Categories: arson, burglary, theft, embezzlement, receiving stolen property, vandalism and trespass are "Property Crimes"; forgery, counterfeiting, false personation, insurance fraud, check and access-card fraud are "Fraud & Money"; extortion is "Violence & Threats" only if the section is about force or threats of injury, otherwise "Fraud & Money"; computer crimes (Section 502) are "Cyber, Privacy & Communications".

A **crime** is one distinct prohibited act with its own elements. Alternative verbs for the same conduct are ONE crime (use `ways`). Different subsections/clauses that require different facts or carry different penalties are separate crimes. A second-or-subsequent-offense rule is a penalty tier (`"if": "the person has a prior conviction for this crime"`), not a separate crime.

Penalty tiers (`penalties`): list; the first tier has `"if": ""`. Each tier:
- `if`: what triggers this tier, without the word "if"; "" for the base.
- `penalty`: plain text in the law's terms, naming the place of imprisonment, e.g. "Imprisonment in the state prison for 2, 3, or 4 years". "County jail" is a local sentence; keep the law's words.
- `min`: mandatory minimum prison years (number) or null (for "25 years to life" use 25). `max`: maximum prison years (1000 death possible; 999 life; 0 fine only; null if not stated).
- `flags`: subset of ["mandatory minimum", "no parole", "no probation", "consecutive", "civil", "wobbler"] when the text says so ("wobbler" per the rule above).

## Example (Section 243(d), shortened; battery with serious bodily injury)
{"243": {"review": {"title": "Battery", "isOffense": true, "plain": "Battery is the willful and unlawful use of force on another; it is a misdemeanor, and battery causing serious bodily injury is punishable in county jail up to one year or as a felony.", "category": "Violence & Threats", "maxYears": 4, "maxPlus": true,
  "acts": ["uses force or violence upon the person of another"]},
 "elements": {"shared": {"who": null},
  "crimes": [
   {"where": "(a)", "act": "Uses force or violence upon the person of another", "ways": [], "tags": [], "intent": ["Willfully and unlawfully"], "conditions": [], "exceptions": [], "defenses": [],
    "penalties": [{"if": "", "penalty": "A fine not exceeding two thousand dollars ($2,000), or imprisonment in a county jail not exceeding six months, or both", "min": null, "max": 0.5, "flags": []}]},
   {"where": "(d)", "act": "Commits a battery that causes serious bodily injury", "ways": [], "tags": [], "conditions": ["Serious bodily injury is inflicted on the person"], "exceptions": [], "defenses": [],
    "penalties": [{"if": "", "penalty": "Imprisonment in a county jail for not more than one year, or imprisonment in the state prison for 2, 3, or 4 years", "min": null, "max": 4, "flags": ["wobbler"]}]}]}}}
(The example is illustrative, not the exact text of the section. The `acts` phrases must be exact substrings of the text.)

## Validate before finishing
python3 review/ca/validate.py <input> <output>
Fix every problem it reports and re-run until it prints "OK".

Reply with only: the count written, how many are isOffense false, and one line per section where you were genuinely uncertain and why.
