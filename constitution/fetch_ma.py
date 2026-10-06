"""Download the Constitution of the Commonwealth of Massachusetts from the Legislature's website (the whole text is on one
page: https://malegislature.gov/Laws/Constitution; the Legislature's API has no constitution routes) into
ma/constitution/raw/constitution.html, with the download date in ma/constitution/raw/meta.json.
Usage: python3 constitution/fetch_ma.py
"""
import datetime, json, os, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "ma", "constitution", "raw")
URL = "https://malegislature.gov/Laws/Constitution"
os.makedirs(OUT, exist_ok=True)
req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"})
data = urllib.request.urlopen(req, timeout=120).read()
open(os.path.join(OUT, "constitution.html"), "wb").write(data)
json.dump({"fetched": datetime.date.today().isoformat(), "url": URL}, open(os.path.join(OUT, "meta.json"), "w"), indent=1)
print(f"saved {len(data):,} bytes to ma/constitution/raw/constitution.html")
