"""Validate an elements output file against its input batch. Usage: validate.py <input> <output>"""
import json, re, sys

inp, out = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
LIST_FIELDS = ["federalBasis", "knowledge", "mentalState", "intent", "consequences", "terms", "conditions", "exceptions", "defenses", "ways"]
FLAGS = {"mandatory minimum", "consecutive", "no probation", "civil"}
problems = []

def check_tiers(where, tiers):
    if not isinstance(tiers, list) or not tiers:
        problems.append(f"{where}: penalties must be a non-empty list"); return
    if tiers[0].get("if", None) != "":
        problems.append(f"{where}: first penalty tier must have \"if\": \"\"")
    for t in tiers:
        for k in ("if", "penalty", "min", "max", "flags"):
            if k not in t: problems.append(f"{where}: tier missing {k}")
        if not str(t.get("penalty", "")).strip(): problems.append(f"{where}: empty penalty text")
        if re.match(r"(?i)^if\b", str(t.get("if", ""))): problems.append(f"{where}: tier 'if' should not start with the word 'if'")
        for k in ("min", "max"):
            v = t.get(k)
            if v is not None and not isinstance(v, (int, float)): problems.append(f"{where}: {k} must be a number or null")
        if not set(t.get("flags", [])) <= FLAGS: problems.append(f"{where}: unknown flags {set(t.get('flags', [])) - FLAGS}")

secs = {x["section"]: x for x in inp}
if set(out) != set(secs): problems.append(f"sections differ: missing {sorted(set(secs) - set(out))}, extra {sorted(set(out) - set(secs))}")
for s, e in out.items():
    if s not in secs: continue
    if not isinstance(e, dict) or "shared" not in e or "crimes" not in e:
        problems.append(f"§{s}: needs shared and crimes"); continue
    sh, crimes = e["shared"], e["crimes"]
    if not crimes: problems.append(f"§{s}: no crimes")
    for k in LIST_FIELDS:
        if k in sh and not isinstance(sh[k], list): problems.append(f"§{s} shared.{k} must be a list")
    if "penalties" in sh and sh["penalties"]: check_tiers(f"§{s} shared", sh["penalties"])
    has_shared_pen = bool(sh.get("penalties"))
    for i, c in enumerate(crimes):
        w = f"§{s} crime {i + 1} {c.get('where', '')}"
        if not str(c.get("act", "")).strip(): problems.append(f"{w}: empty act")
        if re.match(r"(?i)^(whoever|knowingly|willfully|intentionally|with intent|it shall be unlawful|any person)\b", str(c.get("act", ""))):
            problems.append(f"{w}: act should start with the verb, not '{c['act'][:25]}'")
        for k in LIST_FIELDS:
            if k in c and not isinstance(c[k], list): problems.append(f"{w}: {k} must be a list")
        if not set(c.get("tags", [])) <= {"attempt", "conspiracy"}: problems.append(f"{w}: tags must be attempt/conspiracy")
        if c.get("penalties"): check_tiers(w, c["penalties"])
        elif not has_shared_pen: problems.append(f"{w}: no penalty (neither on the crime nor shared)")
print("OK" if not problems else "\n".join(problems[:60]))
