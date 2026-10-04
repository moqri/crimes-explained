import json, glob, os, re, subprocess, sys
D = os.path.dirname(os.path.abspath(__file__))
SITE = "/Users/mahdimoqri/ai/usc18"
plain = json.load(open(f"{SITE}/plain.json"))
merged, problems = {}, []
for f in sorted(glob.glob(f"{D}/in*.json")):
    o = f.replace("/in", "/out")
    if not os.path.exists(o): problems.append(f"missing {os.path.basename(o)}"); continue
    r = subprocess.run([sys.executable, f"{D}/validate.py", f, o], capture_output=True, text=True).stdout.strip()
    if r != "OK": problems.append(f"{os.path.basename(o)}: {r[:300]}")
    merged.update(json.load(open(o)))
placeholders = [s for s, e in merged.items() if re.search(r"\(same as", json.dumps(e))]
def top(e):
    tiers = list(e["shared"].get("penalties") or [])
    for c in e["crimes"]: tiers += c.get("penalties") or []
    vals = [t.get("max") for t in tiers if isinstance(t.get("max"), (int, float))]
    return max(vals) if vals else None
mismatch = []
for s, e in merged.items():
    a, b = top(e), plain.get(s, {}).get("maxYears")
    if a is not None and b is not None and a != b: mismatch.append((s, b, a))
n_crimes = sum(len(e["crimes"]) for e in merged.values())
print(f"sections: {len(merged)} | crimes: {n_crimes} | problems: {len(problems)}")
for p in problems[:20]: print("  ", p)
print("placeholder text:", placeholders)
print(f"max-penalty mismatches (section, badge, elements): {len(mismatch)}")
for m in mismatch[:40]: print("  ", m)
if "--write" in sys.argv:
    json.dump(merged, open(f"{SITE}/elements.json", "w"), ensure_ascii=False, indent=1)
    print("elements.json written")
