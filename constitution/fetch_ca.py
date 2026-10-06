"""Download the California Constitution from the Legislature's official site (leginfo.legislature.ca.gov) into
ca/constitution/raw/<article>.html, one page per article (e.g. "XIII+A.html"), and the article list in raw/meta.json.
leginfo now answers scripts with a Cloudflare challenge (HTTP 403), so pages are loaded in headless Google Chrome, which
passes it. Table of contents: https://leginfo.legislature.ca.gov/faces/codesTOCSelected.xhtml?tocCode=CONS
Usage: python3 constitution/fetch_ca.py [--resume]   (--resume skips articles already downloaded)
"""
import datetime, html, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "ca", "constitution", "raw")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
TOC = "https://leginfo.legislature.ca.gov/faces/codesTOCSelected.xhtml?tocCode=CONS&tocTitle=+California+Constitution+-+CONS"
ART = "https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?lawCode=CONS&article={}"
os.makedirs(OUT, exist_ok=True)

def chrome(url):
    for attempt in range(3):
        dom = subprocess.run(["perl", "-e", "alarm 120; exec @ARGV", CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=20000",
                              f"--user-agent={UA}", "--dump-dom", url], capture_output=True, text=True).stdout
        if "__cf_chl" not in dom and len(dom) > 20000: return dom
    sys.exit(f"could not load {url} (Cloudflare challenge not passed)")

toc = html.unescape(chrome(TOC))
arts = {}
for h, t in re.findall(r'href="([^"]*CONS[^"]*article=[^"&]*[^"]*)"[^>]*>(.*?)</a>', toc, re.S):
    a = re.search(r"article=([^&\"]+)", h).group(1)
    arts.setdefault(a, re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t)).strip())
if not arts: sys.exit("no articles found in the table of contents")
for a in arts:
    path = os.path.join(OUT, f"{a}.html")
    if "--resume" in sys.argv and os.path.exists(path): continue
    page = chrome(ART.format(a))
    if "manylawsections" not in page: sys.exit(f"article {a}: no section text on the page")
    open(path, "w", encoding="utf-8").write(page)
    print(a, len(re.findall(r"<h6", page.split("manylawsections", 1)[1])), "sections", flush=True)
pre = re.search(r"PREAMBLE:?\s*(We, the People[^<]*?\.)\s*<", toc)          # the Preamble is printed in the table of contents
json.dump({"fetched": datetime.date.today().isoformat(), "preamble": pre.group(1) if pre else "", "articles": arts}, open(os.path.join(OUT, "meta.json"), "w"), ensure_ascii=False, indent=1)
