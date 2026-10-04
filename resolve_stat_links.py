"""Cache, for every "VOL Stat. PAGE" citation in crimes.json, the GovInfo PDF it resolves to (with #page) and its size.
Run once (and again after the data changes); build_data.py reads stat_links.json."""
import json, os, re, subprocess
from concurrent.futures import ThreadPoolExecutor
here = os.path.dirname(os.path.abspath(__file__))
cache_path = os.path.join(here, "stat_links.json")
cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}
c = json.load(open(os.path.join(here, "crimes.json")))["crimes"]
cites = set()
for x in c:
    for t in [x["source"]] + [p["t"] for p in x["text"]] + x["footnotes"]:
        cites |= {f"{v}:{p}" for v, p in re.findall(r"(\d+)\s+Stat\.\s+(\d+)", t)}
todo = sorted(cites - set(cache))
def resolve(key):
    v, p = key.split(":")
    h = subprocess.run(["curl", "-sIL", "-A", "Mozilla/5.0", "--max-time", "40", f"https://www.govinfo.gov/link/statute/{v}/{p}"],
                       capture_output=True, text=True).stdout
    loc = re.findall(r"(?i)^location:\s*(\S+)", h, re.M)
    size = re.findall(r"(?i)content-length:\s*(\d+)", h)
    codes = re.findall(r"^HTTP/\S+ (\d+)", h, re.M)
    if not loc or not codes or codes[-1] not in ("200", "206"): return key, None
    return key, {"pdf": loc[-1], "kb": round(int(size[-1]) / 1024) if size else None}
with ThreadPoolExecutor(8) as ex:
    for key, val in ex.map(resolve, todo): cache[key] = val
json.dump(cache, open(cache_path, "w"), indent=0, sort_keys=True)
print(f"{len(cites)} distinct citations | newly resolved {len(todo)} | unresolvable: {sorted(k for k, v in cache.items() if not v)[:10]}")

# Pair each Stat. citation with the Public Law cited just before it ("Pub. L. 104–294, …, 110 Stat. 3488").
# For laws from the 104th Congress on, GovInfo's Public Law HTML carries "[[Page 110 STAT. 3488]]" markers, so a
# text-fragment link can open the small HTML page at the cited page instead of the whole-law PDF.
pairs = {}
for x in c:
    for t in [x["source"]] + [p["t"] for p in x["text"]] + x["footnotes"]:
        last = None
        for m in re.finditer(r"Pub\.\s*L\.\s*(\d+)[–-](\d+)|(\d+)\s+Stat\.\s+(\d+)", t):
            if m.group(1): last = (int(m.group(1)), int(m.group(2)), m.end())
            elif last and last[0] >= 104 and m.start() - last[2] < 250:
                pairs.setdefault(f"{m.group(3)}:{m.group(4)}", f"{last[0]}-{last[1]}")
laws = sorted(set(pairs.values()))
plaw_cache_path = os.path.join(here, "plaw_pages.json")
plaw_pages = json.load(open(plaw_cache_path)) if os.path.exists(plaw_cache_path) else {}
def pages(law):
    cn, num = law.split("-")
    r = subprocess.run(["curl", "-sL", "-A", "Mozilla/5.0", "--max-time", "90", "-w", "\n%{http_code}",
                        f"https://www.govinfo.gov/content/pkg/PLAW-{cn}publ{num}/html/PLAW-{cn}publ{num}.htm"], capture_output=True, text=True).stdout
    body, code = r.rsplit("\n", 1)
    if code != "200" or "STAT." not in body: return law, None
    return law, sorted({f"{v}:{p}" for v, p in re.findall(r"\[\[Page (\d+) STAT\. (\d+)\]\]", body)})
with ThreadPoolExecutor(6) as ex:
    for law, pg in ex.map(pages, [l for l in laws if l not in plaw_pages]): plaw_pages[law] = pg
json.dump(plaw_pages, open(plaw_cache_path, "w"), indent=0, sort_keys=True)
for key, law in pairs.items():
    if plaw_pages.get(law) is None: continue
    entry = cache.get(key) or {}
    entry["plaw"] = law
    entry["exact"] = key in plaw_pages[law]
    cache[key] = entry
json.dump(cache, open(cache_path, "w"), indent=0, sort_keys=True)
html_ok = [k for k, v in cache.items() if v and v.get("plaw")]
print(f"paired with 104th+ Congress laws: {len(pairs)} | laws with HTML: {sum(1 for l in laws if plaw_pages.get(l))}/{len(laws)} "
      f"| citations linkable to HTML: {len(html_ok)} (exact page marker: {sum(cache[k]['exact'] for k in html_ok)})")
print("volume-138 citations now:", {k: cache.get(k) for k in cache if k.startswith('138:')})
