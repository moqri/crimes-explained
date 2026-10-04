"""Download Massachusetts General Laws chapters from the Legislature's public API into ma/raw/<chapter>.json.

Source: https://malegislature.gov/api (official text of the General Laws, current as of the download date).
Usage: python3 ma/fetch_ma.py 265 [266 …]
"""
import datetime, json, os, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://malegislature.gov/api"
get = lambda url: json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"}), timeout=60))

os.makedirs(os.path.join(HERE, "raw"), exist_ok=True)
for chap in sys.argv[1:]:
    ch = get(f"{API}/Chapters/{chap}")
    secs = []
    for s in ch["Sections"]:
        for attempt in range(3):
            try: secs.append(get(s["Details"].replace(" ", "%20"))); break
            except Exception as e:
                if attempt == 2: raise
                time.sleep(2)
    json.dump({"chapter": chap, "name": ch["Name"], "part": ch["Part"]["Code"], "fetched": datetime.date.today().isoformat(), "sections": secs},
              open(os.path.join(HERE, "raw", f"{chap}.json"), "w"), ensure_ascii=False, indent=1)
    print(f"c. {chap} {ch['Name']}: {len(secs)} sections ({sum(not s['IsRepealed'] for s in secs)} in force)")
