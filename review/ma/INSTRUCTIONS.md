# Task: review Massachusetts criminal-law sections and break each crime into its elements

Input: a JSON array of sections of the Massachusetts General Laws (M.G.L.), each with `section` (key like "265/13A"), `cite`, `title`, and `text` (official paragraphs {i, t}; i = outline depth).

Output: ONE JSON object mapping each input `section` key → `{"review": {...}, "elements": {...}}`. Include every input section.

## Accuracy rules (critical)

- Use ONLY the text of that section. Never copy, paraphrase, or summarize text from another section or chapter, and never add outside facts, case law, or sentencing guidelines. If the section's penalty, definition, or mental state is set in another section ("shall be punished as provided in section 13A", "as defined in section 1 of chapter 140"), say only where it is set: e.g. a penalty tier `"penalty": "Set in section 13A of chapter 265"` with min/max null. Do not cite other sections with "§" in any field.
- Stay close to the law's wording. Shorten only by dropping words. Keep "may" vs "shall", "and" vs "or", "knowingly" vs "wilfully" exactly.
- `2½` in the text means two and one-half years.

## `review` fields

- `isOffense`: true if the section itself makes conduct a crime or sets the punishment for a crime it names (e.g. "Murder defined" with its degrees, or "Punishment for murder"). false for sections that only define terms, set procedure, venue, sentencing administration, reporting duties, civil remedies, or programs. If false, give only `isOffense` and `plain` (one sentence on what the section does) and omit `elements`.
- `plain`: one plain-English sentence (max ~35 words) saying what the crime is and, briefly, the top penalty. For general readers.
- `category`: exactly one of: "Violence & Threats", "Sex Crimes & Exploitation", "Human Trafficking & Slavery", "Weapons & Terrorism", "Fraud & Money", "Property Crimes", "Cyber, Privacy & Communications", "Government & Corruption", "Civil Rights", "Courts & Justice", "Family & Children", "Transportation & Aviation", "Animals & Wildlife".
- `maxYears`: the highest prison term in the section, as a number: years (2½ → 2.5; 6 months → 0.5), 999 for life (including "any term of years" with life), 0 for fine only, null if the section sets no penalty itself.
- `maxPlus`: true only if some form of the crime is punished under another section and may carry more; otherwise omit.
- `acts`: list of phrases copied EXACTLY (character for character, same case and punctuation) from one paragraph's `t`, each marking the prohibited conduct itself: start at the verb ("commits an assault and battery upon another", "to transport", "has sexual intercourse or unnatural sexual intercourse with a child under 16"). Exclude "Whoever", mental-state words (knowingly, wilfully, with intent to …), "if"/"unless" conditions, and the penalty. Keep each phrase within one paragraph. One phrase per distinct prohibited act.

## `elements` (same schema as the federal site)

`{"shared": {...}, "crimes": [...]}`. Put a field in `shared` only if it is identical for every crime; crime-level fields replace shared ones.

shared (all optional):
- `who`: who can commit it, ONLY when the law limits it (e.g. "A person 18 years of age or older", "A caretaker of a person with a disability"); null when anyone ("whoever", "any person").
- `knowledge`: list. What the person must know ("Knowing or having reason to know that the person is pregnant").
- `mentalState`: list. Recklessness or negligence ("Wantonly or recklessly").
- `intent`: list. Purpose ("With intent to murder", "Wilfully", "Maliciously").
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

A **crime** is one distinct prohibited act with its own elements. Alternative verbs for the same conduct are ONE crime (use `ways`). Different subsections/clauses that require different facts or carry different penalties are separate crimes. A second-or-subsequent-offense rule is a penalty tier (`"if": "the person has a prior conviction for this crime"`), not a separate crime.

Penalty tiers (`penalties`): list; the first tier has `"if": ""`. Each tier:
- `if`: what triggers this tier, without the word "if"; "" for the base.
- `penalty`: plain text in the law's terms, naming the place of imprisonment, e.g. "Up to 5 years in state prison or up to 2½ years in a house of correction, a fine of up to $5,000, or both". "Jail" and "house of correction" are both county sentences; keep the law's word.
- `min`: mandatory minimum prison years (number) or null. `max`: maximum prison years (2.5 for 2½; 999 life; 0 fine only; null if not stated).
- `flags`: subset of ["mandatory minimum", "no parole", "no probation", "consecutive", "civil"] when the text says so.

## Example (c. 265, § 13A, shortened)
{"265/13A": {"review": {"isOffense": true, "plain": "Assault or assault and battery is a crime punishable by up to 2½ years in a house of correction; causing serious injury, or assaulting a pregnant person or someone with a protective order against you, carries up to 5 years in state prison.", "category": "Violence & Threats", "maxYears": 5,
  "acts": ["commits an assault or an assault and battery upon another", "commits an assault or an assault and battery:"]},
 "elements": {"shared": {"who": null, "terms": ["\"Serious bodily injury\": bodily injury that results in a permanent disfigurement, loss or impairment of a bodily function, limb or organ, or a substantial risk of death"]},
  "crimes": [
   {"where": "(a)", "act": "Commits an assault or an assault and battery upon another", "ways": ["assault", "assault and battery"], "tags": [], "conditions": [], "exceptions": [], "defenses": [],
    "penalties": [{"if": "", "penalty": "Up to 2½ years in a house of correction or a fine of up to $1,000", "min": null, "max": 2.5, "flags": []}]},
   {"where": "(b)(i)", "act": "Commits an assault or an assault and battery upon another", "ways": ["assault", "assault and battery"], "tags": [], "conditions": ["The assault and battery causes serious bodily injury"], "exceptions": [], "defenses": [],
    "penalties": [{"if": "", "penalty": "Up to 5 years in state prison or up to 2½ years in a house of correction, a fine of up to $5,000, or both", "min": null, "max": 5, "flags": []}]},
   {"where": "(b)(ii)", "act": "Commits an assault or an assault and battery upon another who is pregnant", "ways": ["assault", "assault and battery"], "tags": [], "knowledge": ["Knowing or having reason to know that the person is pregnant"], "conditions": ["The victim is pregnant at the time"], "exceptions": [], "defenses": [],
    "penalties": [{"if": "", "penalty": "Up to 5 years in state prison or up to 2½ years in a house of correction, a fine of up to $5,000, or both", "min": null, "max": 5, "flags": []}]}]}}}
(The `acts` phrases must be exact substrings of the text; the example's are illustrative.)

## Validate before finishing
python3 review/ma/validate.py <input> <output>
Fix every problem it reports and re-run until it prints "OK".

Reply with only: the count written, how many are isOffense false, and one line per section where you were genuinely uncertain and why.
