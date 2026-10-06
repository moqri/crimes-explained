# California Constitution: differences from the U.S. review

Follow review/con/INSTRUCTIONS.md in full, with these changes for the California Constitution.

- Input `section` ids: "preamble", "a1-s1", "a1-s1.1" (Article I, section 1.1), "a13a-s1" (Article XIII A, section 1). The Constitution has no official section headings: write a short `title` caption as in the U.S. review.
- `history` is the Legislature's note of when the section was added or amended ("Sec. 2 amended June 3, 1980, by Prop. 5."). It is not a change to the text; do not put it in `changedBy`. `changedBy` is [] for every California section.
- Paragraphs begin with labels "(a)", "(1)", "(A)", "(i)". `where` is the label path as printed, e.g. "(a)", "(b)(1)", "(c)(2)(A)"; "" for an unlabeled section or paragraph. Never include a label in a highlight phrase.
- A section that says it is operative only until, or only from, a date: describe it as written; do not decide whether it is now in effect.
- `category`: exactly one of "Founding & Purposes", "Individual Rights", "Criminal Justice", "Voting & Elections", "Equality & Citizenship", "The Legislature", "The Governor & Executive", "The Courts", "Local Government", "Taxes, Money & Commerce", "Education", "Water & Natural Resources", "Transportation", "Public Officers & Employees", "Labor", "Housing & Public Utilities", "Amending & Ratifying".
- No `status` field.
- Validate with: python3 review/con/validate.py --jur ca <input> <output>
- A duty is an obligation to do something ("The Legislature shall provide by law for …", "shall publish", "shall be presented"): never put a duty's phrase in `powers` or any highlight list. But a grant of authority is a power even when written with "shall": "shall be vested in", "shall have jurisdiction", "shall exercise … jurisdiction", "shall appoint", "shall fill vacancies by appointment", "may remove". Highlight those as powers.
