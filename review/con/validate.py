"""Check a constitution review batch: python3 review/con/validate.py <in.json> <out.json>. Prints the problems, or OK."""
import json, re, sys

CATS = {"Founding & Purposes", "Individual Rights", "Criminal Justice", "Voting & Elections", "Equality & Citizenship", "Congress",
        "The Presidency", "The Courts", "States & Federalism", "Taxes, Money & Commerce", "War & Military", "Amending & Ratifying"}
KINDS = {"Right", "Power", "Limit", "Duty", "Structure"}
OUTSIDE = re.compile(r"\bv\.\s|\bcourts? (?:have|has) (?:held|ruled|read|found|interpreted)|\bcase law\b|incorporat|strict scrutiny|doctrine|§", re.I)   # "supreme Court" is the Constitution's own wording

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
    spans = []
    for key in ("rights", "powers", "limits"):
        for ph in r.get(key) or []:
            hits = [(k, t.find(ph)) for k, t in enumerate(paras) if ph in t]
            if not ph.strip() or not hits: problems.append(f"{s}: {key} phrase not found exactly in one paragraph: {ph!r}"); continue
            k, i = hits[0]
            if re.match(r"^\[\d+\]", ph): problems.append(f"{s}: {key} phrase includes the clause label: {ph!r}")
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
        if w and w not in labels: problems.append(f"{s}: provision {n + 1} where {w!r} is not a clause label in the text {sorted(labels)}")
        for k in ("requires", "forbids", "conditions", "exceptions", "terms", "changedBy"):
            if k in pv and not isinstance(pv[k], list): problems.append(f"{s}: provision {n + 1} {k} must be a list")
        if pv.get("changedBy") and not inp[s]["notes"]: problems.append(f"{s}: changedBy given but the provision has no notes")
    for txt in [r.get("title", ""), r.get("plain", "")] + [json.dumps(pv) for pv in provs or []]:
        if OUTSIDE.search(txt or ""): problems.append(f"{s}: outside material or a § sign: {OUTSIDE.search(txt).group(0)!r}"); break
print("\n".join(problems) if problems else "OK")
