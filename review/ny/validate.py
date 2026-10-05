"""Validate a New York review output against its input batch. Usage: validate.py <input> <output>"""
import json, re, sys
inp, out = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
LIST_FIELDS = ["knowledge", "mentalState", "intent", "consequences", "terms", "conditions", "exceptions", "defenses", "ways"]
PENCLASSES = {"Class A-I felony", "Class A-II felony", "Class B felony", "Class C felony", "Class D felony", "Class E felony", "Class A misdemeanor", "Class B misdemeanor", "Unclassified misdemeanor", "Violation"}
FLAGS = {"mandatory minimum", "no parole", "no probation", "consecutive", "civil"}
CATS = {"Violence & Threats", "Sex Crimes & Exploitation", "Human Trafficking & Slavery", "Weapons & Terrorism", "Fraud & Money", "Property Crimes",
        "Cyber, Privacy & Communications", "Government & Corruption", "Civil Rights", "Courts & Justice", "Family & Children", "Transportation & Aviation", "Animals & Wildlife"}
problems = []
def tiers_ok(where, tiers):
    if not isinstance(tiers, list) or not tiers: problems.append(f"{where}: penalties must be a non-empty list"); return
    if tiers[0].get("if", None) != "": problems.append(f'{where}: first tier must have "if": ""')
    for t in tiers:
        for k in ("if", "penalty", "min", "max", "flags"):
            if k not in t: problems.append(f"{where}: tier missing {k}")
        if re.match(r"(?i)^if\b", str(t.get("if", ""))): problems.append(f"{where}: tier 'if' should not start with 'if'")
        for k in ("min", "max"):
            if t.get(k) is not None and not isinstance(t[k], (int, float)): problems.append(f"{where}: {k} must be a number or null")
        if not set(t.get("flags", [])) <= FLAGS: problems.append(f"{where}: unknown flags {set(t.get('flags', [])) - FLAGS}")
secs = {x["section"]: x for x in inp}
if set(out) != set(secs): problems.append(f"sections differ: missing {sorted(set(secs) - set(out))}, extra {sorted(set(out) - set(secs))}")
for s, v in out.items():
    if s not in secs: continue
    r = v.get("review") or {}
    if not isinstance(r.get("isOffense"), bool): problems.append(f"{s}: review.isOffense must be true/false")
    if not str(r.get("plain", "")).strip(): problems.append(f"{s}: review.plain missing")
    if "title" in r: problems.append(f"{s}: do not write a title (the official title is used)")
    if r.get("isOffense") is False:
        if v.get("elements"): problems.append(f"{s}: isOffense false must have no elements")
        continue
    if r.get("category") not in CATS: problems.append(f"{s}: bad category {r.get('category')!r}")
    if r.get("maxYears") is not None and not isinstance(r["maxYears"], (int, float)): problems.append(f"{s}: maxYears must be a number or null")
    texts = [p["t"] for p in secs[s]["text"]]
    alltext = " ".join(texts).lower()
    pc = r.get("penClass")
    if pc is not None and pc not in PENCLASSES: problems.append(f"{s}: bad penClass {pc!r}")
    if pc and pc != "Unclassified misdemeanor" and not re.search(r"\bclass " + re.escape(pc.split()[1].lower()) + r"\b" if pc.startswith("Class") else r"\bviolation\b", alltext): problems.append(f"{s}: penClass {pc!r} not stated in this section's text")
    if pc is None and "class " in alltext and re.search(r"is an? (?:class|violation)", alltext): problems.append(f"{s}: section states a class but penClass is null")
    if r.get("maxYears") is not None and not re.search(r"imprison|life|years?|death", alltext): problems.append(f"{s}: maxYears set but the section states no term")
    if not r.get("acts"): problems.append(f"{s}: acts empty")
    for a in r.get("acts", []):
        if not any(a in t for t in texts): problems.append(f"{s}: act phrase not found exactly in text: {a[:70]!r}")
    e = v.get("elements")
    if not isinstance(e, dict) or "shared" not in e or not e.get("crimes"): problems.append(f"{s}: elements needs shared and non-empty crimes"); continue
    sh = e["shared"]
    blocks = [("shared", sh)] + [(f"crime {i + 1} {c.get('where', '')}", c) for i, c in enumerate(e["crimes"])]
    for w, b in blocks:
        if "federalBasis" in b and b["federalBasis"]: problems.append(f"{s} {w}: do not use federalBasis")
        for k in LIST_FIELDS:
            if k in b and not isinstance(b[k], list): problems.append(f"{s} {w}: {k} must be a list")
        for k, val in b.items():
            if "§" in json.dumps(val, ensure_ascii=False): problems.append(f"{s} {w}: '§' citation in {k}: use only this section's text")
    if sh.get("penalties"): tiers_ok(f"{s} shared", sh["penalties"])
    for w, c in blocks[1:]:
        if not str(c.get("act", "")).strip(): problems.append(f"{s} {w}: empty act")
        if re.match(r"(?i)^(whoever|knowingly|wilfully|willfully|intentionally|with intent|any person)\b", str(c.get("act", ""))): problems.append(f"{s} {w}: act should start with the verb")
        if not set(c.get("tags", [])) <= {"attempt", "conspiracy"}: problems.append(f"{s} {w}: bad tags")
        if c.get("penalties"): tiers_ok(f"{s} {w}", c["penalties"])
        elif not sh.get("penalties"): problems.append(f"{s} {w}: no penalty (neither on the crime nor shared)")
        for t in (c.get("penalties") or []) + (sh.get("penalties") or []):
            m = re.match(r"(?i)(class [A-E](?:-I+)? felony|class [AB] misdemeanor|violation)", str(t.get("penalty", "")))
            if m and m.group(1).lower() not in alltext: problems.append(f"{s} {w}: penalty class {m.group(1)!r} not stated in this section's text")
print("OK" if not problems else "\n".join(problems[:60]))
