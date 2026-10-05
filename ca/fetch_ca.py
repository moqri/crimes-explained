"""Download California Penal Code, Part 1, Title 8 (Of Crimes Against the Person, sections 187-248) from the Legislature's
official site (leginfo.legislature.ca.gov) into ca/raw/<chapter>.html. Each chapter page holds every section's text.
Usage: python3 ca/fetch_ca.py            (discovers the chapters by trying chapter numbers 1 to 15 and the .5 variants)
"""
import datetime, json, os, re, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
URL = "https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?lawCode=PEN&division=&title=8.&part=1.&chapter={}&article="
os.makedirs(os.path.join(HERE, "raw"), exist_ok=True)

def get(url):
    for attempt in range(3):
        try: return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60).read().decode("utf-8")
        except Exception:
            if attempt == 2: raise
            time.sleep(3)

meta = {}
cands = [f"{n}.{h}" if h else f"{n}." for n in range(1, 16) for h in ("", "5")]
for ch in cands:
    page = get(URL.format(ch))
    time.sleep(1)
    if "manylawsections" not in page: continue
    secs = re.findall(r"submitCodesValues\('([^']+?)\.?'", page.split("manylawsections", 1)[1])
    if not secs: continue
    open(os.path.join(HERE, "raw", f"{ch.rstrip('.')}.html"), "w", encoding="utf-8").write(page)
    print(ch, len(secs), "sections", secs[0], "…", secs[-1])
    meta[ch.rstrip(".")] = len(secs)
json.dump({"fetched": datetime.date.today().isoformat(), "chapters": meta}, open(os.path.join(HERE, "raw", "meta.json"), "w"), indent=1)
