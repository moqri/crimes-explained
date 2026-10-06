# Task: review provisions of the Constitution of the United States and break each into its rights, powers and limits

Input: a JSON array of provisions. Each has `section` (an id such as "preamble", "art1-s8", "art5", "amend1", "amend14-s1"), `cite` ("Art. I, § 8", "Amend. XIV, § 1"), `part`, `notes` (official notes from the Government Publishing Office print, e.g. "This clause has been affected by clause 1 of amendment XVII."), and `text` (official paragraphs {i, t}; a paragraph that starts with "[3]" is clause 3 of that section).

Output: ONE JSON object mapping each input `section` key → `{"review": {...}, "elements": {...}}`. Include every input provision.

## Accuracy rules (critical)

- Use ONLY the text of that provision and its `notes`. Never add case law, court interpretations, history, commentary, or what other provisions say. Do not write "the courts have held", "incorporated", "the Supreme Court", case names, or any doctrine (no "strict scrutiny", "commerce power has been read to…"). If the text is silent, say nothing.
- Stay close to the Constitution's wording. Shorten only by dropping words; modernize nothing that changes meaning. Keep "shall" vs "may", "and" vs "or", "No State" vs "Congress", exactly.
- The text keeps its original spelling and capitals ("chuse", "defence", "Persons"); copy phrases exactly as written.
- Never use the "§" sign in your output; write "Section 8" or "clause 3".
- A clause marked superseded or affected in `notes` is still part of the text: describe what it says, and put the note's words in `changedBy` (e.g. "Affected by clause 1 of amendment XVII"). Do not explain how it was changed beyond the note.

## `review` fields

- `title`: a short caption in plain words (max ~8 words), e.g. "Powers of Congress", "Freedom of religion, speech, press, assembly and petition", "Right to bear arms". The Constitution has no official section headings; the site says captions are added.
- `plain`: one or two plain sentences (max ~45 words) saying what the provision does, using only its text.
- `category`: exactly one of: "Founding & Purposes", "Individual Rights", "Criminal Justice", "Voting & Elections", "Equality & Citizenship", "Congress", "The Presidency", "The Courts", "States & Federalism", "Taxes, Money & Commerce", "War & Military", "Amending & Ratifying".
- `kind`: the provision's main kind, exactly one of "Right", "Power", "Limit", "Duty", "Structure":
  - Right: guarantees something to people ("The right of the people to be secure …", "shall enjoy the right to a speedy and public trial").
  - Power: grants authority ("The Congress shall have Power To …", "The President shall be Commander in Chief").
  - Limit: forbids government action ("Congress shall make no law …", "No State shall …", "shall not be infringed").
  - Duty: requires an act ("He shall take Care that the Laws be faithfully executed", "shall be bound by Oath").
  - Structure: sets up offices, terms, qualifications, elections and procedures without being mainly one of the above.
- Highlight phrases: `rights`, `powers`, `limits` — lists of phrases copied EXACTLY (character for character) from one paragraph's `t`, never including the "[3]" label, never spanning two paragraphs, never overlapping each other.
  - `rights`: the protected right itself ("the freedom of speech, or of the press", "the right of the people to keep and bear Arms", "to have the Assistance of Counsel for his defence").
  - `powers`: the grant of authority ("To lay and collect Taxes, Duties, Imposts and Excises", "shall have the sole Power of Impeachment", "The executive Power shall be vested in a President").
  - `limits`: the prohibition ("shall make no law respecting an establishment of religion", "No State shall enter into any Treaty", "shall not be infringed", "Excessive bail shall not be required").
  - Keep phrases short (the key words, not the whole sentence). Not every provision needs all three; use [] when none fits. Do not highlight conditions ("if", "unless", "when"), qualifications, or numbers alone.

## `elements`

`{"provisions": [...]}`, one entry per distinct right, power, limit or duty (a clause can hold more than one; a long list of powers in one clause, like Art. I, Section 8, is one entry per clause):

- `where`: the clause label as it appears ("[3]"), or "" for an unlabeled provision.
- `kind`: "right" | "power" | "limit" | "duty" | "structure".
- `what`: the substance in the Constitution's words, shortened only by dropping words ("Lay and collect Taxes, Duties, Imposts and Excises to pay the Debts and provide for the common Defence and general Welfare").
- `holder`: who has the right or power ("The people", "Congress", "The President", "Each House", "The accused"), or null.
- `binds`: who must act or is limited ("Congress", "No State", "The United States or any State"), or null.
- `requires`, `forbids`, `conditions`, `exceptions`: lists in the text's words, only what this provision says ("Duties, Imposts and Excises shall be uniform throughout the United States" is a requirement; "unless when in Cases of Rebellion or Invasion the public Safety may require it" is an exception).
- `terms`: `"\"term\": meaning"` only when the provision itself defines a term (e.g. Art. III, Section 3 defines treason). Never define a term the provision does not define.
- `changedBy`: the words of any `notes` entry that applies to this clause and says the text was changed, affected or superseded (a note that only explains numbering is not a change); when a note on the whole provision is about one sentence, put it only on the entry for that sentence; else [].

Omit empty lists or leave them as []. Every provision needs at least one entry.

## Example (shape only)
{"amend2": {"review": {"title": "Right to keep and bear arms", "plain": "Because a well regulated militia is necessary to the security of a free State, the right of the people to keep and bear arms shall not be infringed.", "category": "Individual Rights", "kind": "Right",
  "rights": ["the right of the people to keep and bear Arms"], "powers": [], "limits": ["shall not be infringed"]},
 "elements": {"provisions": [{"where": "", "kind": "right", "what": "The right of the people to keep and bear Arms, shall not be infringed", "holder": "The people", "binds": null, "requires": [], "forbids": ["Infringing the right of the people to keep and bear Arms"], "conditions": [], "exceptions": [], "terms": [], "changedBy": []}]}}}

## Validate before finishing
python3 review/con/validate.py <input> <output>
Fix every problem it reports and re-run until it prints "OK".

Reply with only: the count written, and one line per provision where you were genuinely uncertain and why.
