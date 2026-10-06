"""Build ny/crimes.json from the downloaded New York Penal Law, Part 3, Titles H, I and J (ny/raw/title<H|I|J>.json, from fetch_ny.py), plus the
reviewed data in ny/plain.json (which sections define crimes, summaries, categories, class of the offense, act phrases)
and ny/elements.json (crime breakdowns). Usage: python3 ny/build_ny.py [--batches DIR]
--batches writes the parsed sections that are not yet in plain.json in batches of 30 as input for the review agents.
Section captions are the official titles from the API. The API gives the text hard-wrapped; paragraphs start after "\n  ".
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from textlib import label_kind, apply_acts, own_text_only, tidy_acts

TITLES = ["H", "I", "J"]
raws = [json.load(open(os.path.join(HERE, "raw", f"title{t}.json"), encoding="utf-8")) for t in TITLES]
struct = json.load(open(os.path.join(HERE, "raw", "structure.json"), encoding="utf-8"))
SEC_URL = "https://www.nysenate.gov/legislation/laws/PEN/"
DIGIT = re.compile(r"^(\d+(?:-[A-Za-z])?)\.\s")
PAREN = re.compile(r"^\(([A-Za-z0-9]+(?:-[A-Za-z0-9]+)?)\)(?=\s|$)")

def walk(d):
    yield d
    for k in (d.get("documents") or {}).get("items", []): yield from walk(k)

def paragraphs(text):
    # the first chunk is the "§ 120.05 Title." header (a long title wraps onto indented lines); paragraphs start after "\n  "
    items = [re.sub(r"\s*\n\s*", " ", p).strip() for p in re.split(r"\n  (?=\S)", text.replace("\\n", "\n").strip("\n"))[1:]]
    paras = [{"i": 0, "t": t} for t in items if t]
    labels = [(m.group(1) if (m := PAREN.match(p["t"])) else None) for p in paras]
    stack, last = [], {}
    for k, p in enumerate(paras):
        if DIGIT.match(p["t"]): stack, last = ["digit"], {}; p["i"] = 0; continue
        L = labels[k]
        if L is None: p["i"] = 0 if not stack else 0; continue
        up = []
        for j in range(k + 1, len(paras)):
            if DIGIT.match(paras[j]["t"]): break
            if labels[j]: up.append(labels[j].split("-")[0])
        base = L.split("-")[0]
        kind = label_kind(base, stack, last, up)
        if kind in stack: del stack[stack.index(kind) + 1:]
        else: stack.append(kind)
        last[kind] = base
        for gone in [x for x in last if x not in stack]: del last[gone]
        p["i"] = len(stack) - 1
    return paras

out = []
for art in [d for raw in raws for d in walk(raw["tree"]) if d["docType"] == "ARTICLE"]:
    for s in art["documents"]["items"]:
        if s["docType"] != "SECTION" or s.get("repealed"): continue
        sec = s["locationId"]
        out.append({"section": sec, "code": sec, "cite": f"§ {sec}", "title": s["title"].rstrip("."), "chapter": art["docLevelId"],
                    "chapterTitle": art["title"].strip(), "text": paragraphs(s["text"]), "source": "", "footnotes": [], "url": SEC_URL + sec})

plain_path, elements_path = os.path.join(HERE, "plain.json"), os.path.join(HERE, "elements.json")
plain = json.load(open(plain_path, encoding="utf-8")) if os.path.exists(plain_path) else {}
elements = json.load(open(elements_path, encoding="utf-8")) if os.path.exists(elements_path) else {}

if "--batches" in sys.argv:                 # sections not yet in plain.json, in batches for review
    d = sys.argv[sys.argv.index("--batches") + 1]
    os.makedirs(d, exist_ok=True)
    todo = [c for c in out if c["section"] not in plain]
    for k in range(0, len(todo), 30):
        batch = [{"section": c["section"], "cite": c["cite"], "title": c["title"], "article": f'{c["chapter"]}. {c["chapterTitle"]}', "text": [{"i": p["i"], "t": p["t"]} for p in c["text"]]} for c in todo[k:k + 30]]
        json.dump(batch, open(os.path.join(d, f"in_{k // 30 + 1:02d}.json"), "w"), ensure_ascii=False, indent=1)
    print(f"{len(out)} sections parsed; wrote {(len(todo) + 29) // 30} batches of up to 30 sections ({len(todo)} sections) to {d}")
    sys.exit()

unmatched = removed = 0
for c in out:
    title = c["title"]
    c.update(plain.get(c["section"], {}))
    c["title"] = title                       # official caption from the API
    unmatched += apply_acts(c)
    if c["section"] in elements:
        c["elements"] = elements[c["section"]]
        removed += own_text_only(c["code"], c["elements"])
    tidy_acts(c)
print(f"{unmatched} act phrases not found; {removed} borrowed breakdown items removed")
missing = [c["section"] for c in out if c["section"] not in plain]
if missing: print(len(missing), "sections not reviewed yet (left out until they are in plain.json):", missing[:10])
dropped = [c["section"] for c in out if c.get("isOffense") is False]
out = [c for c in out if c["section"] in plain and c.get("isOffense") is not False]
print(len(dropped), "sections excluded as not defining a crime")

# Location ids of the Penal Law's articles on nysenate.gov ("70" -> "P2TEA70"), for links to "article 70 of this chapter".
art_ids = {d["docLevelId"]: d["locationId"] for d in walk(struct["documents"]) if d["docType"] == "ARTICLE"}
pen_secs = sorted(d["locationId"] for d in walk(struct["documents"]) if d["docType"] == "SECTION")   # every Penal Law section, to check cites
json.dump({"jurisdiction": "ny", "frequency": None, "articleIds": art_ids, "penSections": pen_secs,
           "edition": f"New York Penal Law, Part 3, Titles H (Offenses Against the Person), I (Offenses Involving Damage to and Intrusion Upon Property) and J (Offenses Involving Theft), official text from the NY Senate Open Legislation API (downloaded {raws[0]['fetched']})",
           "source": "https://www.nysenate.gov/legislation/laws/PEN/P3", "crimes": out}, open(os.path.join(HERE, "crimes.json"), "w"), ensure_ascii=False, indent=1)
print(len(out), "sections written to ny/crimes.json")
