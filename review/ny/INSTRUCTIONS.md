# Task: review New York Penal Law sections (Part 3, Title H, Articles 120-135) and break each crime into its elements

Input: a JSON array of sections, each with `section` (the number, e.g. "120.05", "130.65-A"), `cite`, `title` (the official title, already used as the caption), `article`, and `text` (official paragraphs {i, t}; i = outline depth: subdivision "1." at 0 → paragraph "(a)" → subparagraph "(i)" → "(A)").

Output: ONE JSON object mapping each input `section` key → `{"review": {...}, "elements": {...}}`. Include every input section. Do NOT write a `title` (the official title is used).

## Accuracy rules (critical)

- Use ONLY the text of that section. Never copy, paraphrase or summarize text from another section, and never add outside facts: no Article 15 (culpable mental states), Article 10 (definitions), Article 70/80 (sentences), no case law, no CPL, no sentencing ranges. If a definition, mental state, or penalty is set in another section or article, say only where it is set, using the section's own words ("as defined in section 10.00 of this chapter") or "Set in Penal Law Article 70". Do not use the "§" sign anywhere in the output; write "section 125.25". Quoting the section's own wording that mentions another section is fine.
- Stay close to the law's wording. Shorten only by dropping words. Keep "may" vs "shall", "and" vs "or", "intentionally" vs "knowingly" vs "recklessly" vs "with criminal negligence" exactly. The statute uses "he" / "he or she": keep the law's pronouns in `act` only if needed; prefer "Causes physical injury to another person".
- Do not state a prison term unless THIS section states one. New York defines the sentence of a crime by its class; the class is stated in a final line such as "Assault in the second degree is a class D felony." and the sentence range is in Penal Law Articles 70 and 80, outside this section.

## Penalty tiers when only a class is stated

- `penalty`: "Class D felony (sentence set in Penal Law Article 70)". For a class A or B misdemeanor or a violation: "Class A misdemeanor (sentence set in Penal Law Articles 70 and 80)", "Violation (sentence set in Penal Law Articles 70 and 80)". Felonies: "Class B felony (sentence set in Penal Law Article 70)"; keep the full class label as the section writes it ("Class A-I felony", "Class B violent felony offense" only if the section says "violent").
- `min`: null, `max`: null, `flags`: []. Never put an Article 70 range in.
- When a subdivision raises the class ("… is a class E felony, provided, however, that if … a class A felony, then … a class C felony"), make a base tier and a tier with `if`.
- If the section states a term itself (rare), use it: years in `min`/`max` (999 = life, 1000 = death), quoted in the law's words.
- When the section applies to several crimes with the same class, put the tier in `shared.penalties`.

## `review` fields

- `isOffense`: true if the section itself makes conduct a crime (a "person is guilty of X when" section, or a section that sets the class of a crime it describes). false for definitions ("As used in this article…"), lack-of-consent rules, defenses and presumptions, limitations of prosecution, sentencing instructions, and other provisions that create no crime of their own. If false, give only `isOffense` and `plain` (one sentence on what the section does) and omit `elements`.
- `plain`: one plain sentence (max ~35 words) saying what the crime is and its class.
- `category`: exactly one of: "Violence & Threats", "Sex Crimes & Exploitation", "Human Trafficking & Slavery", "Weapons & Terrorism", "Fraud & Money", "Property Crimes", "Cyber, Privacy & Communications", "Government & Corruption", "Civil Rights", "Courts & Justice", "Family & Children", "Transportation & Aviation", "Animals & Wildlife".
- `penClass`: the HIGHEST class the section states for any crime in it, spelled exactly one of: "Class A-I felony", "Class A-II felony", "Class B felony", "Class C felony", "Class D felony", "Class E felony", "Class A misdemeanor", "Class B misdemeanor", "Unclassified misdemeanor", "Violation"; null if the section states no class (then use `maxYears` if the section states a term, else null). The same words must appear in the section's text (a "class B violent felony offense" is penClass "Class B felony").
- `maxYears`: null unless the section itself states a term (then the highest: years; 999 life; 1000 death; 0 fine only).
- `maxPlus`: omit.
- `acts`: phrases copied EXACTLY (character for character) from one paragraph's `t`, each marking the prohibited conduct itself: start at the verb or the infinitive "to" ("causes such injury to such person or to a third person", "restrains another person", "engages in sexual intercourse with another person"). Exclude "A person is guilty of … when", mental-state words (intentionally, knowingly, recklessly, with intent to …), "if"/"unless" conditions, and the class. One phrase per distinct prohibited act; a phrase must not span two paragraphs.

## `elements`

`{"shared": {...}, "crimes": [...]}`. Put a field in `shared` only if it is identical for every crime; crime-level fields replace shared ones.

shared (all optional): `who`, `knowledge`, `mentalState`, `intent`, `penalties`, `consequences`, `terms` as below. Do not use `federalBasis`.
- `who`: ONLY when the law limits it ("A person eighteen years old or more"); null when "a person".
- `knowledge`: list ("Knowing that the person is a police officer", "Knowing or reasonably should have known …").
- `mentalState`: list ("Recklessly", "With criminal negligence", "With depraved indifference to human life" if the section says so).
- `intent`: list ("With intent to cause physical injury to another person", "Intentionally").
- `consequences`: list of non-sentence consequences the section itself states.
- `terms`: list of `"\"term\": meaning"` for definitions IN THIS SECTION that decide whether the crime applies. Never define a term from another section.

each crime:
- `where`: the subdivision/paragraph reference in the form "1", "3-a", "1(a)", "2(b)(ii)" (no dots, no "subd."); "" for an unlabeled section. For several crimes in one subdivision, use the paragraph label.
- `act`: the prohibited conduct, starting with the verb, in the law's words, WITHOUT mental-state words or conditions ("Causes serious physical injury to another person by means of a deadly weapon").
- `ways`: alternative verbs/means for the same act; otherwise [].
- `tags`: ["attempt","conspiracy"] only when this section itself says attempts/conspiracies are punished the same way (rare in New York; normally []).
- `conditions`: facts that must be true ("The victim is a police officer", "The victim is less than eleven years old", "The person is eighteen years old or more" goes in `who`).
- `exceptions`, `defenses`: lists, from this section only (an "affirmative defense" stated in the section goes in `defenses`).
- `who`, `knowledge`, `mentalState`, `intent`, `penalties`, `consequences`, `terms`: only when different from shared.

A **crime** is one distinct prohibited act with its own elements. In New York a section reads "A person is guilty of X when: 1. …; or 2. …": each numbered subdivision (and each lettered paragraph that stands alone) that requires different facts is a separate crime. Alternative verbs for the same conduct are ONE crime (use `ways`). A subdivision that only lists victim categories as alternatives in sub-items (i), (ii), (iii) is ONE crime with the categories as one condition or a `conditions` list item "Any of the following: …". A higher penalty for a repeat offense is a penalty tier with `if`, not a new crime. Do not create crimes for lines that only say the class.

Penalty tiers (`penalties`): list; the first tier has `"if": ""`. Each tier: `if` (no leading "if"), `penalty`, `min`, `max`, `flags` ⊆ ["mandatory minimum", "no parole", "no probation", "consecutive", "civil"] — only when the section's text says so.

## Example (shape only; text illustrative)
{"120.05": {"review": {"isOffense": true, "plain": "Assault in the second degree covers causing serious injury intentionally, injury with a weapon, and other listed assaults; it is a class D felony.", "category": "Violence & Threats", "penClass": "Class D felony", "maxYears": null,
  "acts": ["he causes such injury to such person or to a third person"]},
 "elements": {"shared": {"penalties": [{"if": "", "penalty": "Class D felony (sentence set in Penal Law Article 70)", "min": null, "max": null, "flags": []}]},
  "crimes": [
   {"where": "1", "act": "Causes serious physical injury to another person or to a third person", "ways": [], "tags": [], "intent": ["With intent to cause serious physical injury to another person"], "conditions": [], "exceptions": [], "defenses": []},
   {"where": "4", "act": "Causes serious physical injury to another person by means of a deadly weapon or a dangerous instrument", "ways": [], "tags": [], "mentalState": ["Recklessly"], "conditions": [], "exceptions": [], "defenses": []}]}}}

## Validate before finishing
python3 review/ny/validate.py <input> <output>
Fix every problem it reports and re-run until it prints "OK".

Reply with only: the count written, how many are isOffense false, and one line per section where you were genuinely uncertain and why.
