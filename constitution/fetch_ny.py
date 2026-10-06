"""Download the Constitution of the State of New York from the NY Senate Open Legislation API (law id CNS, one request
with full=true) into ny/constitution/raw/cns.json. Needs the same free API key as ny/fetch_ny.py (ny/.api_key or the
environment variable NYSENATE_API_KEY); the key is never printed or written to any file.
Usage: python3 constitution/fetch_ny.py
"""
import datetime, json, os, sys, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
kf = os.path.join(ROOT, "ny", ".api_key")
KEY = os.environ.get("NYSENATE_API_KEY") or (open(kf).read().strip() if os.path.exists(kf) else "")
if not KEY: sys.exit("No API key: put it in ny/.api_key or set NYSENATE_API_KEY")
url = "https://legislation.nysenate.gov/api/3/laws/CNS?" + urllib.parse.urlencode({"full": "true", "key": KEY})
res = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/json"}), timeout=180))["result"]
out = os.path.join(ROOT, "ny", "constitution", "raw")
os.makedirs(out, exist_ok=True)
json.dump({"fetched": datetime.date.today().isoformat(), "activeDate": res["lawVersion"]["activeDate"], "tree": res["documents"]},
          open(os.path.join(out, "cns.json"), "w"), ensure_ascii=False, indent=1)
print("saved ny/constitution/raw/cns.json, version of", res["lawVersion"]["activeDate"])
