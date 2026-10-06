"""Build ny/constitution/crimes.json (the provisions of the Constitution of the State of New York) from the Senate API
download (ny/constitution/raw/cns.json, from constitution/fetch_ny.py), plus the reviewed data in
ny/constitution/plain.json and ny/constitution/elements.json (same review format as the other constitutions).
Usage: python3 constitution/build_ny.py [--batches DIR]

Units: the Preamble and each section of Articles I-XX. Ids "preamble", "a1-s6", "a7-s8" (also the page file names).
Captions are the official section titles from the API. The API gives the text hard-wrapped; paragraphs start after "\\n  ".
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(os.path.dirname(HERE), "ny", "constitution")
raw = json.load(open(os.path.join(DIR, "raw", "cns.json"), encoding="utf-8"))
SEC_URL = "https://www.nysenate.gov/legislation/laws/CNS/"

def walk(d):
    yield d
    for k in (d.get("documents") or {}).get("items", []): yield from walk(k)

def level(t):
    """Outline depth from the label: "1." / "a." / "A." at 0, "(1)" / "(a)" at 1, "(i)" at 2."""
    if re.match(r"^\((?:i|ii|iii|iv|v|vi|vii|viii|ix|x)\)\s", t): return 2
    if re.match(r"^\([0-9a-zA-Z]{1,3}\)\s", t): return 1
    return 0

def paragraphs(text, first):
    t = text.replace("\\n", "\n")
    chunks = [re.sub(r"\s*\n\s*", " ", c).strip() for c in re.split(r"\n  (?=\S)", "\n" + t.lstrip(" "))]
    out = []
    for c in chunks:
        if not c or re.fullmatch(r"(?:ARTICLE [IVX]+.*|THE CONSTITUTION)", c): continue
        c = re.sub(r"^ARTICLE [IVX]+\s+[A-Z][^.]*?(?=Section \d)", "", c) if first else c
        c = re.sub(r"^(?:Section|§)\s*\d+(?:-[a-z])?\.\s*", "", c)          # the section's own number
        if c: out.append({"i": level(c), "t": c})
    return out

units = []
for d in walk(raw["tree"]):
    if d["docType"] == "PREAMBLE":
        units.append({"section": "preamble", "code": "preamble", "cite": "Preamble", "title": "Preamble", "chapter": "pre", "chapterTitle": "Preamble",
                      "text": [{"i": 0, "t": re.sub(r"\s+", " ", re.sub(r"^\s*THE CONSTITUTION", "", d["text"].replace("\\n", " "))).strip()}],
                      "source": "", "footnotes": [], "url": SEC_URL + d["locationId"]})
    if d["docType"] != "ARTICLE": continue
    roman, n = d["docLevelId"], str(len([u for u in units if u["chapter"] != "pre" and u["section"].endswith("-s1")]) + 1)
    n = str({r: i + 1 for i, r in enumerate("I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX".split())}[roman])
    for k, s in enumerate(x for x in d["documents"]["items"] if x["docType"] == "SECTION"):
        if s.get("repealed"): continue
        num = s["docLevelId"]
        units.append({"section": f"a{n}-s{num.lower()}", "code": f"a{n}-s{num.lower()}", "cite": f"Art. {roman}, § {num}", "title": re.sub(r"\s+", " ", s.get("title") or "").strip().rstrip("."),
                      "chapter": n, "chapterTitle": d["title"].strip(), "text": paragraphs(s["text"], k == 0), "source": "", "footnotes": [], "url": SEC_URL + s["locationId"]})
for u in units:   # the API's editorial notes ("*So in original. ("th" should be "the".)") become footnotes
    u["footnotes"] = [p["t"] for p in u["text"] if re.match(r"^\*", p["t"])]
    u["text"] = [p for p in u["text"] if not re.match(r"^\*", p["t"])]
units = [u for u in units if u["text"]]
print(len(units), "provisions parsed;", sum(len(u["footnotes"]) for u in units), "editorial notes")

plain_path, elements_path = os.path.join(DIR, "plain.json"), os.path.join(DIR, "elements.json")
plain = json.load(open(plain_path, encoding="utf-8")) if os.path.exists(plain_path) else {}
elements = json.load(open(elements_path, encoding="utf-8")) if os.path.exists(elements_path) else {}

if "--batches" in sys.argv:
    d = sys.argv[sys.argv.index("--batches") + 1]
    os.makedirs(d, exist_ok=True)
    todo = [u for u in units if u["section"] not in plain]
    size, first = 20, int(sys.argv[sys.argv.index("--start") + 1]) if "--start" in sys.argv else 1
    for k in range(0, len(todo), size):
        batch = [{"section": u["section"], "cite": u["cite"], "title": u["title"], "part": f'Article {u["cite"].split(",")[0][5:]}: {u["chapterTitle"]}' if u["chapter"] != "pre" else "Preamble",
                  "notes": [{"clause": "", "note": f} for f in u["footnotes"]], "text": [{"i": p["i"], "t": p["t"]} for p in u["text"]]} for u in todo[k:k + size]]
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
    title = u["title"]
    u.update(plain.get(u["section"], {}))
    u["title"] = title or u.get("title") or u["cite"]          # the official title
    unmatched += apply_marks(u)
    if u["section"] in elements: u["elements"] = elements[u["section"]]
print(f"{unmatched} highlighted phrases not found")
missing = [u["section"] for u in units if u["section"] not in plain]
if missing: print(len(missing), "provisions not reviewed yet (left out until they are in plain.json):", missing[:10])
units = [u for u in units if u["section"] in plain]
parts = {"pre": "Preamble", **{str(i + 1): f"Art. {r}" for i, r in enumerate("I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX".split())}}
json.dump({"jurisdiction": "ny", "doc": "con", "frequency": None, "partNames": parts,
           "edition": f"Constitution of the State of New York, official text and section titles from the NY Senate Open Legislation API (version of {raw['activeDate']}, downloaded {raw['fetched']})",
           "source": SEC_URL, "crimes": units}, open(os.path.join(DIR, "crimes.json"), "w"), ensure_ascii=False, indent=1)
print(len(units), "provisions written to ny/constitution/crimes.json")
