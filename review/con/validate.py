"""Check a constitution review batch: python3 review/con/validate.py [--jur ma] <in.json> <out.json>. Prints the problems, or OK."""
import json, re, sys

CATS = {"Founding & Purposes", "Individual Rights", "Criminal Justice", "Voting & Elections", "Equality & Citizenship", "Congress",
        "The Presidency", "The Courts", "States & Federalism", "Taxes, Money & Commerce", "War & Military", "Amending & Ratifying"}
MA = "--jur" in sys.argv and sys.argv[sys.argv.index("--jur") + 1] == "ma"
if MA:
    CATS = {"Founding & Purposes", "Individual Rights", "Criminal Justice", "Voting & Elections", "Equality & Citizenship", "The Legislature",
            "The Governor & Executive", "The Courts", "Local Government", "Taxes, Money & Commerce", "Education & Religion", "Military & Militia", "Amending & Ratifying"}
    sys.argv = [a for i, a in enumerate(sys.argv) if a != "--jur" and (i == 0 or sys.argv[i - 1] != "--jur")]
KINDS = {"Right", "Power", "Limit", "Duty", "Structure"}
OUTSIDE = re.compile(r"(?-i:\b[A-Z][a-z]+ v\. [A-Z])|\bcourts? (?:have|has) (?:held|ruled|read|found|interpreted)|\bcase law\b|\bincorporat(?:ed|ion)\s+(?:against|into|through|doctrine)|strict scrutiny|\b(?:incorporation|[a-z]+-clause|political question|state action) doctrine\b|§", re.I)   # "supreme Court" is the Constitution's own wording

def all_bracketed(paras):
    """True when every word of the text is inside square brackets (the Legislature's mark for superseded wording)."""
    depth = 0
    for ch in " ".join(paras).strip().rstrip("."):
        if ch == "[": depth += 1
        elif ch == "]": depth -= 1
        elif depth == 0 and not ch.isspace() and ch not in ".,;": return False
    return True

inp = {s["section"]: s for s in json.load(open(sys.argv[1], encoding="utf-8"))}
out = json.load(open(sys.argv[2], encoding="utf-8"))
problems = []
for s in inp:
    if s not in out: problems.append(f"{s}: missing")
for s, v in out.items():
    if s not in inp: problems.append(f"{s}: not in the input"); continue
    r, e = v.get("review") or {}, v.get("elements") or {}
    paras = [p["t"] for p in inp[s]["text"]]
    labels = {m.group(0) for t in paras if (m := re.match(r"^\[\d+\]", t))}
    if not (r.get("title") or "").strip(): problems.append(f"{s}: no title")
    if not (r.get("plain") or "").strip(): problems.append(f"{s}: no plain")
    if len((r.get("plain") or "").split()) > 60: problems.append(f"{s}: plain is too long")
    if r.get("category") not in CATS: problems.append(f"{s}: bad category {r.get('category')!r}")
    if r.get("kind") not in KINDS: problems.append(f"{s}: bad kind {r.get('kind')!r}")
    if MA and r.get("status") not in ("in force", "partly superseded", "superseded", "annulled"): problems.append(f"{s}: bad status {r.get('status')!r}")
    whole = all_bracketed(paras)
    if MA and whole and r.get("status") not in ("superseded", "annulled"): problems.append(f"{s}: the whole text is in brackets: status must be 'superseded' (or 'annulled' if a note says so)")
    if MA and r.get("status") == "superseded" and not (r.get("plain") or "").startswith("Superseded:"): problems.append(f"{s}: a superseded provision's plain must start with 'Superseded:'")
    if MA and r.get("status") == "annulled" and not (r.get("plain") or "").startswith("Annulled:"): problems.append(f"{s}: an annulled provision's plain must start with 'Annulled:'")
    spans = []
    for key in ("rights", "powers", "limits"):
        for ph in r.get(key) or []:
            hits = [(k, t.find(ph)) for k, t in enumerate(paras) if ph in t]
            if not ph.strip() or not hits: problems.append(f"{s}: {key} phrase not found exactly in one paragraph: {ph!r}"); continue
            k, i = hits[0]
            if re.match(r"^\[\d+\]", ph): problems.append(f"{s}: {key} phrase includes the clause label: {ph!r}")
            if MA and ("[" in ph or "]" in ph or paras[k].rfind("[", 0, i) > paras[k].rfind("]", 0, i)): problems.append(f"{s}: {key} phrase is inside or includes superseded [bracketed] wording: {ph!r}")
            spans.append((k, i, i + len(ph), ph))
    spans.sort()
    for a, b in zip(spans, spans[1:]):
        if a[0] == b[0] and b[1] < a[2]: problems.append(f"{s}: highlight phrases overlap: {a[3]!r} / {b[3]!r}")
    provs = e.get("provisions")
    if not provs: problems.append(f"{s}: elements.provisions is empty")
    for n, pv in enumerate(provs or []):
        if pv.get("kind") not in {k.lower() for k in KINDS}: problems.append(f"{s}: provision {n + 1} bad kind {pv.get('kind')!r}")
        if not (pv.get("what") or "").strip(): problems.append(f"{s}: provision {n + 1} has no 'what'")
        w = pv.get("where", "")
        if MA and w and not re.fullmatch(r"Section \d+", w): problems.append(f"{s}: provision {n + 1} where must be '' or 'Section N'")
        elif not MA and w and w not in labels: problems.append(f"{s}: provision {n + 1} where {w!r} is not a clause label in the text {sorted(labels)}")
        for k in ("requires", "forbids", "conditions", "exceptions", "terms", "changedBy"):
            if k in pv and not isinstance(pv[k], list): problems.append(f"{s}: provision {n + 1} {k} must be a list")
        if pv.get("changedBy") and not inp[s]["notes"] and not re.search(r"\[\s*(?:[^\]]*\b(?:superseded|annulled|amended)\b)", " ".join(paras), re.I): problems.append(f"{s}: changedBy given but the provision has no notes")
        if MA and any(re.match(r"\[?\s*(?:[Ss]ee|For)\b", c) for c in pv.get("changedBy") or []): problems.append(f"{s}: provision {n + 1} changedBy holds a cross-reference ('See …'/'For …'), not a change")
    for txt in [r.get("title", ""), r.get("plain", "")] + [json.dumps(pv) for pv in provs or []]:
        if OUTSIDE.search(txt or ""): problems.append(f"{s}: outside material or a § sign: {OUTSIDE.search(txt).group(0)!r}"); break
print("\n".join(problems) if problems else "OK")
