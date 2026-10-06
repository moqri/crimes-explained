# New York Constitution: differences from the U.S. review

Follow review/con/INSTRUCTIONS.md in full, with these changes for the Constitution of the State of New York.

- Input `section` ids: "preamble", "a1-s6" (Article I, section 6), "a7-s8". Each input has the official section `title`: do NOT write a `title` (the official one is used).
- Paragraphs may begin with a subdivision label: "1.", "a.", "A.", "(2)", "(b)". `where` is that label without the dot and parentheses kept as printed ("1", "a", "(2)", "(b)"), or "1(a)" when a lettered paragraph sits under a numbered one; "" for an unlabeled provision. Never include the label in a highlight phrase.
- `notes` are the Senate's editorial notes ("*So in original. ("th" should be "the".)"): they mark misprints, not changes, so never put them in `changedBy`. `changedBy` is [] for every New York provision.
- No `status` field.
- `category`: exactly one of "Founding & Purposes", "Individual Rights", "Criminal Justice", "Voting & Elections", "Equality & Citizenship", "The Legislature", "The Governor & Executive", "The Courts", "Local Government", "Taxes, Money & Commerce", "Education", "Military & Defense", "Conservation & Natural Resources", "Social Welfare, Health & Housing", "Public Officers & Civil Service", "Amending & Ratifying".
- Copy the text's own words exactly, including misprints the notes point out.
- Validate with: python3 review/con/validate.py --jur ny <input> <output>
