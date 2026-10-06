"""Download New York Penal Law, Part 3, Titles H (Offenses Against the Person), I (Offenses Involving Damage to and Intrusion
Upon Property) and J (Offenses Involving Theft) from the NY Senate Open Legislation API (https://legislation.nysenate.gov/api/3). Needs a free API key (https://legislation.nysenate.gov/): put it in ny/.api_key
(gitignored) or the environment variable NYSENATE_API_KEY. The key is never printed or written to any file.
Usage: python3 ny/fetch_ny.py     -> ny/raw/structure.json (tree without text) and ny/raw/title<H|I|J>.json (each title with text)
"""
import datetime, json, os, sys, time, urllib.parse, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://legislation.nysenate.gov/api/3/laws/PEN"
kf = os.path.join(HERE, ".api_key")
KEY = os.environ.get("NYSENATE_API_KEY") or (open(kf).read().strip() if os.path.exists(kf) else "")
if not KEY: sys.exit("No API key: put it in ny/.api_key or set NYSENATE_API_KEY")

def get(path="", **params):
    url = API + path + "?" + urllib.parse.urlencode({**params, "key": KEY})
    for attempt in range(3):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/json"}), timeout=120))
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 404): sys.exit(f"HTTP {e.code} for {path or '/'}")
            if attempt == 2: sys.exit(f"HTTP {e.code} for {path or '/'}")
        except Exception as e:
            if attempt == 2: sys.exit(f"request failed for {path or '/'}: {type(e).__name__}")
        time.sleep(3)

os.makedirs(os.path.join(HERE, "raw"), exist_ok=True)
tree = get()["result"]
json.dump(tree, open(os.path.join(HERE, "raw", "structure.json"), "w"), ensure_ascii=False, indent=1)

def walk(d, path=()):
    yield d, path
    for k in (d.get("documents") or {}).get("items", []): yield from walk(k, path + (d,))
TITLES = ["H", "I", "J"]
found = {d["docLevelId"]: d for d, _ in walk(tree["documents"]) if d["docType"] == "TITLE" and d["docLevelId"] in TITLES}
if set(found) != set(TITLES): sys.exit(f"Titles {sorted(set(TITLES) - set(found))} not found in structure; inspect ny/raw/structure.json")
for t in TITLES: print(f"Title {t}:", found[t]["locationId"], found[t]["title"])
# One request for the whole Penal Law with text (full=true); keep only the titles above.
full = get(full="true")["result"]
def find(d, loc):
    if d["locationId"] == loc: return d
    for k in (d.get("documents") or {}).get("items", []):
        if (r := find(k, loc)): return r
for t in TITLES:
    sub = find(full["documents"], found[t]["locationId"])
    out = {"fetched": datetime.date.today().isoformat(), "activeDate": tree["lawVersion"]["activeDate"], "title": found[t]["title"], "locationId": found[t]["locationId"], "tree": sub}
    json.dump(out, open(os.path.join(HERE, "raw", f"title{t}.json"), "w"), ensure_ascii=False, indent=1)
    print(f"Title {t} sections with text:", sum(1 for d, _ in walk(sub) if d["docType"] == "SECTION"))
