"""Download California Penal Code, Part 1, Titles 8 (Of Crimes Against the Person, sections 187-248) and 13 (Of Crimes
Against Property, sections 450-593) from the Legislature's official site (leginfo.legislature.ca.gov) into
ca/raw/<title>-<chapter>.html. Each chapter page holds every section's text.
Usage: python3 ca/fetch_ca.py [--resume]   (--resume reuses chapter pages already in ca/raw; each title's chapters come from
its official table of contents, which also lists chapters such as 12.5 and 12.6)
"""
import datetime, json, os, re, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
URL = "https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?lawCode=PEN&division=&title={}.&part=1.&chapter={}&article="
TITLES = ["8", "13"]
os.makedirs(os.path.join(HERE, "raw"), exist_ok=True)

def get(url):
    for attempt in range(3):
        try: return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=90).read().decode("utf-8")
        except Exception:
            if attempt == 2: raise
            time.sleep(3)

meta = {}
TOC = "https://leginfo.legislature.ca.gov/faces/codes_displayexpandedbranch.xhtml?tocCode=PEN&division=&title={}.&part=1.&chapter=&article="
chapters = []
for t in TITLES:
    found = sorted(set(re.findall(r"title=" + re.escape(t) + r"\.&(?:amp;)?part=1\.&(?:amp;)?chapter=([\d.]+?)\.&", get(TOC.format(t)))), key=float)
    if not found: sys.exit(f"no chapters found in the table of contents of Title {t}")
    chapters += [(t, ch) for ch in found]
    time.sleep(1)
for t, ch in chapters:
    path = os.path.join(HERE, "raw", f"{t}-{ch}.html")
    if "--resume" in sys.argv and os.path.exists(path): page = open(path, encoding="utf-8").read()   # already downloaded
    else:
        page = get(URL.format(t, ch + "."))
        time.sleep(1)
    if "manylawsections" not in page: continue
    secs = re.findall(r"submitCodesValues\('([^']+?)\.?'", page.split("manylawsections", 1)[1])
    if not secs: continue
    open(path, "w", encoding="utf-8").write(page)
    print(f"Title {t}, chapter {ch}:", len(secs), "sections", secs[0], "…", secs[-1], flush=True)
    meta[f"{t}:{ch}"] = len(secs)
json.dump({"fetched": datetime.date.today().isoformat(), "chapters": meta}, open(os.path.join(HERE, "raw", "meta.json"), "w"), indent=1)
