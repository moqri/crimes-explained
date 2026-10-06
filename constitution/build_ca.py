"""Build ca/constitution/crimes.json (the provisions of the California Constitution) from the article pages saved by
constitution/fetch_ca.py (ca/constitution/raw/<article>.html), plus the reviewed data in ca/constitution/plain.json and
ca/constitution/elements.json (same review format as the other constitutions).
Usage: python3 constitution/build_ca.py [--batches DIR] [--start N]

Units: the Preamble and each section. Ids "preamble", "a1-s1", "a1-s1.1", "a13a-s1" (Article XIII A, section 1).
Each section's history line ("Sec. 1 added Nov. 5, 1974, by Proposition 7. …") becomes its `source`.
The California Constitution has no official section headings, so captions are written by the reviewer.
"""
import html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from textlib import LEAD_CHAIN, outline_levels

DIR = os.path.join(ROOT, "ca", "constitution")
meta = json.load(open(os.path.join(DIR, "raw", "meta.json"), encoding="utf-8"))
SEC_URL = "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=CONS&article={}&sectionNum=SEC.%20{}."
ART_URL = "https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?lawCode=CONS&article={}"
ROMAN = {r: i + 1 for i, r in enumerate("I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX XXI XXII XXIII XXIV XXV XXVI XXVII XXVIII XXIX XXX XXXI XXXII XXXIII XXXIV XXXV".split())}

def clean(t):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", t))).replace(" ", " ").strip()

def paragraphs(items):
    paras = []
    for t in items:
        while (m := re.match(r"^(\((?:\d+[A-Za-z]?|[A-Za-z]{1,5})\))\s+(?=\((?:\d+[A-Za-z]?|[A-Za-z]{1,5})\)\s)", t)): t = m.group(1) + t[m.end():]
        if (chain := LEAD_CHAIN.match(t)) and len(labels := re.findall(r"\([^)]+\)", chain.group(0))) > 1:   # "(a)(1) …": one label per line
            for L in labels[:-1]: paras.append({"i": 0, "t": L})
            t = t[chain.end() - len(labels[-1]):]
        paras.append({"i": 0, "t": t.strip()})
    outline_levels(paras)
    return paras

units = []
if meta.get("preamble"):
    units.append({"section": "preamble", "code": "preamble", "cite": "Preamble", "title": "Preamble", "chapter": "pre", "chapterTitle": "Preamble",
                  "text": [{"i": 0, "t": meta["preamble"]}], "source": "", "footnotes": [], "url": "https://leginfo.legislature.ca.gov/faces/codesTOCSelected.xhtml?tocCode=CONS"})
part_names, part_titles = {"pre": "Preamble"}, {}
for art, label in meta["articles"].items():
    roman, letter = (art.split("+") + [""])[:2]
    key = f"{ROMAN[roman]}{letter.lower()}"
    name = f"Art. {roman}{' ' + letter if letter else ''}"
    title = re.sub(rf"^ARTICLE {roman}{' ' + letter if letter else ''}\s+", "", label)
    title = re.sub(r"\s*\[(?:SEC|Sec|Section|SECTION)[^\]]*\]\s*$", "", title).strip(" []").title().replace(" And ", " and ").replace(" Of ", " of ").replace(" For ", " for ").replace(" The ", " the ").replace(" Or ", " or ")
    part_names[key], part_titles[key] = name, title
    page = open(os.path.join(DIR, "raw", f"{art}.html"), encoding="utf-8").read()
    body = page.split("manylawsections", 1)[1]
    hs = list(re.finditer(r"<h6[^>]*>\s*<a [^>]*>\s*([^<]+?)\s*</a>\s*</h6>", body))
    for k, h in enumerate(hs):
        num = re.sub(r"^(?:SECTION|SEC\.)\s*", "", h.group(1).strip(), flags=re.I).rstrip(".")
        seg = body[h.end(): hs[k + 1].start() if k + 1 < len(hs) else len(body)]
        items, hist = [], ""
        for m in re.finditer(r'<p style="([^"]*)">(.*?)</p>', seg, re.S):
            t = clean(m.group(2))
            if not t: continue
            if "font-size:0.9em" in m.group(1): hist = (hist + " " if hist else "") + t.strip("() ").rstrip(".") + "."; continue
            items.append(t)
        text = paragraphs(items)
        if not text or (len(text) == 1 and re.match(r"(?i)^\(?(repealed|renumbered)\b", text[0]["t"])): continue
        uid = f"a{key}-s{num.lower()}"
        units.append({"section": uid, "code": uid, "cite": f"{name}, § {num}", "title": "", "chapter": key, "chapterTitle": title,
                      "text": text, "source": hist.replace(". Other Source:.", "."), "footnotes": [], "url": SEC_URL.format(art.replace("+", "%20"), num)})
print(len(units), "provisions parsed in", len(meta["articles"]), "articles")

plain_path, elements_path = os.path.join(DIR, "plain.json"), os.path.join(DIR, "elements.json")
plain = json.load(open(plain_path, encoding="utf-8")) if os.path.exists(plain_path) else {}
elements = json.load(open(elements_path, encoding="utf-8")) if os.path.exists(elements_path) else {}

if "--batches" in sys.argv:
    d = sys.argv[sys.argv.index("--batches") + 1]
    os.makedirs(d, exist_ok=True)
    todo = [u for u in units if u["section"] not in plain]
    size, first = 20, int(sys.argv[sys.argv.index("--start") + 1]) if "--start" in sys.argv else 1
    for k in range(0, len(todo), size):
        batch = [{"section": u["section"], "cite": u["cite"], "part": f'{part_names[u["chapter"]]}: {u["chapterTitle"]}' if u["chapter"] != "pre" else "Preamble",
                  "history": u["source"], "notes": [], "text": [{"i": p["i"], "t": p["t"]} for p in u["text"]]} for u in todo[k:k + size]]
        json.dump(batch, open(os.path.join(d, f"in_{k // size + first:02d}.json"), "w"), ensure_ascii=False, indent=1)
    print(f"wrote {(len(todo) + size - 1) // size} batches ({len(todo)} provisions) to {d}")
    sys.exit()

def apply_marks(u):
    missed = 0
    for key, kind in (("rights", "right"), ("powers", "power"), ("limits", "limit")):
        for phrase in u.pop(key, []) or []:
            hits = [(k, p["t"].find(phrase)) for k, p in enumerate(u["text"]) if phrase in p["t"]]
            if not hits: missed += 1; continue
            k, s0 = hits[0]
            u["text"][k].setdefault("m", []).append([s0, s0 + len(phrase), kind])
    for p in u["text"]:
        if "m" in p: p["m"].sort()
    return missed

unmatched = 0
for u in units:
    u.update(plain.get(u["section"], {}))
    u["title"] = (u.get("title") or "").rstrip(".") or u["cite"]
    unmatched += apply_marks(u)
    if u["section"] in elements: u["elements"] = elements[u["section"]]
print(f"{unmatched} highlighted phrases not found")
missing = [u["section"] for u in units if u["section"] not in plain]
if missing: print(len(missing), "provisions not reviewed yet (left out until they are in plain.json):", missing[:10])
units = [u for u in units if u["section"] in plain]
json.dump({"jurisdiction": "ca", "doc": "con", "frequency": None, "partNames": part_names,
           "edition": f"California Constitution, official text from the California Legislative Information site (leginfo.legislature.ca.gov, downloaded {meta['fetched']})",
           "source": "https://leginfo.legislature.ca.gov/faces/codesTOCSelected.xhtml?tocCode=CONS", "crimes": units}, open(os.path.join(DIR, "crimes.json"), "w"), ensure_ascii=False, indent=1)
print(len(units), "provisions written to ca/constitution/crimes.json")
