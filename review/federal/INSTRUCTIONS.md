# Task: break each federal crime section into its elements

Input: a JSON array of sections of 18 U.S.C. Each has `section`, `title`, `text` (official paragraphs {i, t}), `acts` (phrases already identified as the prohibited conduct; use them as hints), and sometimes `penaltySources`: the text of other sections that this section's penalty points to (e.g. §922's penalties are in §924).

Output: a JSON object mapping section → `{"shared": {...}, "crimes": [...]}` as specified below. Include every input section.

## Principles (accuracy is critical)

- Use only the provided text (and `penaltySources` for penalties). No outside facts, case law, or sentencing guidelines.
- Stay close to the law's wording. Shorten only by dropping words, never by paraphrasing in a way that changes meaning. Keep "may" vs "shall", "and" vs "or", "knowingly" vs "willfully" exactly.
- A **crime** is one distinct prohibited act with its own elements. Alternative verbs that describe the same conduct are ONE crime with the alternatives in `ways` (e.g. §2(a): "aids, abets, counsels, commands, induces, or procures" is one crime). Separate subsections or paragraphs that prohibit different conduct are separate crimes.
- **Attempt / conspiracy**: if the section makes attempting or conspiring punishable the same as the crime, do NOT make a separate crime; add the tag `"attempt"` and/or `"conspiracy"` to each crime it covers. Make a separate crime only when the section gives attempt or conspiracy a different penalty.
- Put a field in `shared` only if it is identical for every crime in the section; put crime-specific values on the crime. A crime-level field replaces the shared one.

## Fields

`shared` (all optional; omit or leave empty when not common to all crimes):
- `who`: who can commit it, ONLY when the law limits it (e.g. "An officer or employee of the United States", "A licensed dealer"). Use `null` when it is anyone ("whoever", "any person", "a person").
- `federalBasis`: list. Why this is a federal crime: the jurisdictional element (in or affecting interstate or foreign commerce; uses the mail or wire; a federal officer, employee, program, property, or financial institution; within the special maritime and territorial jurisdiction; in Indian country; and where it applies outside the United States).
- `knowledge`: list. What the person must know (knowingly, knowing that …, with knowledge, has reason to know …).
- `mentalState`: list. Recklessness or negligence standards (recklessly, with reckless disregard, negligently).
- `intent`: list. Purpose (willfully, intentionally, with intent to …, in order to …, for the purpose of …, maliciously, corruptly).
- `penalties`: penalty tiers (see below).
- `consequences`: list. Non-prison consequences the section imposes besides the fine: forfeiture, removal or disqualification from office, license suspension or revocation, restitution, civil penalties, injunctions.
- `terms`: list. Definitions in this section that decide whether the crime applies, as `"\"term\": meaning"` (shortened).

each crime:
- `where`: subsection reference like "(a)(1)", or "" for an unlabeled section.
- `act`: the prohibited conduct, starting with the verb, in the law's words, WITHOUT knowledge/intent words and WITHOUT conditions (e.g. "Receives, relieves, comforts, or assists the offender").
- `ways`: list of the alternative verbs/means when the act lists several (e.g. ["aids", "abets", "counsels", "commands", "induces", "procures"]); otherwise [].
- `tags`: subset of ["attempt", "conspiracy"].
- `who`, `federalBasis`, `knowledge`, `mentalState`, `intent`, `penalties`, `consequences`, `terms`: only when different from `shared`.
- `conditions`: list. Facts that must be true for the act to be a crime (other than the federal basis), e.g. "The aircraft is in flight", "The value exceeds $1,000", "The victim is under 18".
- `exceptions`: list. Conduct or people the section excludes ("does not apply to …", "except …").
- `defenses`: list. Affirmative defenses the section creates ("it is an affirmative defense that …"); say who must prove it if the text says.

Penalty tiers (`penalties`): a list; the first tier has `"if": ""` (the base penalty). Each tier:
- `if`: the condition that triggers this tier, without the word "if" (e.g. "death results", "the value does not exceed $1,000", "the person has a prior conviction under this chapter", "the offense is committed by an organization"); "" for the base.
- `penalty`: plain text in the law's terms ("A fine, up to 20 years in prison, or both").
- `min`: minimum prison years as a number, or null. `max`: maximum prison years: a number, 999 for life (incl. "any term of years or for life"), 1000 if death is possible, 0 if fine only, null if not stated.
- `flags`: subset of ["mandatory minimum", "consecutive", "no probation", "civil"] when the text says so.
- If the penalty is in another section, fill the tiers from `penaltySources` and add `"source": "§924(a)(2)"` (the subsection that applies). If no penalty can be determined, use one tier with `penalty: "Set in another law"` and the reference.

## Examples (from sections already reviewed)

§3 (one crime, penalty tiers):
{"shared": {"who": null, "federalBasis": ["The underlying offense is an offense against the United States"], "knowledge": ["Knowing that an offense against the United States has been committed"], "intent": ["In order to hinder or prevent the offender's apprehension, trial, or punishment"],
  "penalties": [{"if": "", "penalty": "Up to half the maximum prison term and up to half the maximum fine prescribed for the main offense, or both", "min": null, "max": null, "flags": []},
                {"if": "the main offense is punishable by life imprisonment or death", "penalty": "Up to 15 years in prison", "min": null, "max": 15, "flags": []}]},
 "crimes": [{"where": "", "act": "Receives, relieves, comforts, or assists the offender", "ways": ["receives", "relieves", "comforts", "assists"], "tags": [], "conditions": [], "exceptions": ["The penalty rule applies except as otherwise expressly provided by any Act of Congress"], "defenses": []}]}

§32 (shared intent and penalty; (b) differs in federal basis; (c) differs in penalty; attempt/conspiracy as tags):
{"shared": {"who": null, "intent": ["Willfully"], "penalties": [{"if": "", "penalty": "A fine, up to 20 years in prison, or both", "min": null, "max": 20, "flags": []}],
            "terms": ["\"National of the United States\": as defined in section 101(a)(22) of the Immigration and Nationality Act"]},
 "crimes": [
  {"where": "(a)(1)", "act": "Sets fire to, damages, destroys, disables, or wrecks an aircraft", "ways": ["sets fire to", "damages", "destroys", "disables", "wrecks"], "tags": ["attempt", "conspiracy"], "federalBasis": ["The aircraft is in the special aircraft jurisdiction of the United States, or is a civil aircraft used, operated, or employed in interstate, overseas, or foreign air commerce"], "conditions": [], "exceptions": [], "defenses": []},
  {"where": "(a)(6)", "act": "Performs an act of violence against, or incapacitates, any individual on such an aircraft", "ways": [], "tags": ["attempt", "conspiracy"], "federalBasis": ["(same as (a)(1))"], "conditions": ["The act is likely to endanger the safety of the aircraft"], "exceptions": [], "defenses": []},
  {"where": "(b)(1)", "act": "Performs an act of violence against any individual on board a civil aircraft registered in a country other than the United States", "ways": [], "tags": ["attempt", "conspiracy"], "federalBasis": ["A U.S. national was or would have been on board, an offender is a U.S. national, or an offender is afterwards found in the United States"], "conditions": ["The aircraft is in flight", "The act is likely to endanger the safety of that aircraft"], "exceptions": [], "defenses": []},
  {"where": "(c)", "act": "Imparts or conveys a threat to do an act that would violate (a)(1)–(6) or (b)(1)–(3)", "ways": [], "tags": [], "intent": ["Willfully", "With an apparent determination and will to carry the threat into execution"], "penalties": [{"if": "", "penalty": "A fine, up to 5 years in prison, or both", "min": null, "max": 5, "flags": []}], "conditions": [], "exceptions": [], "defenses": []}]}
(Write every federalBasis out in full; "(same as (a)(1))" above is only to keep the example short.)

§38 (penalty tiers; organizations; consequences):
 "penalties": [{"if": "", "penalty": "Up to 10 years in prison, a fine, or both", "min": null, "max": 10, "flags": []},
  {"if": "the offense relates to the aviation quality of a part and the part is installed in an aircraft or space vehicle", "penalty": "Up to 15 years in prison, a fine of up to $500,000, or both", "min": null, "max": 15, "flags": []},
  {"if": "the part's failure to operate as represented causes a malfunction or failure resulting in serious bodily injury", "penalty": "Up to 20 years in prison, a fine of up to $1,000,000, or both", "min": null, "max": 20, "flags": []},
  {"if": "the part's failure causes a malfunction or failure resulting in death", "penalty": "Imprisonment for any term of years or life, a fine of up to $1,000,000, or both", "min": null, "max": 999, "flags": []},
  {"if": "the offense is committed by an organization", "penalty": "A fine of up to $10,000,000; up to $20,000,000 if the failure results in serious bodily injury or death", "min": null, "max": 0, "flags": []}],
 "consequences": ["Criminal forfeiture of proceeds and of property used to commit the offense", "Court orders to divest interests, restrict future activities, or dissolve an enterprise used for the offense"]

## Validate before finishing
python3 review/federal/validate.py <input> <output>
Fix every problem it reports and re-run until it prints "OK".

Reply with only: the count written, and one line per section where you were uncertain and why (real uncertainties only).
