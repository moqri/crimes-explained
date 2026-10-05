"""Build ca/crimes.json from the downloaded California Penal Code chapters (ca/raw/*.html, from fetch_ca.py), plus the
reviewed data in ca/plain.json (which sections define crimes, captions, summaries, types, maximum penalties, act phrases)
and ca/elements.json (crime breakdowns). Usage: python3 ca/build_ca.py [--batches DIR]
--batches writes the parsed sections that are not yet in plain.json in batches of 30 as input for the review agents.
The Penal Code has no official section headings, so each section's caption ("title") comes from the review.
"""
import glob, html, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from textlib import LEAD_CHAIN, outline_levels, apply_acts, own_text_only, fill_act_gaps, tidy_acts

SEC_URL = "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=PEN&sectionNum="
TITLE_URL = "https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?lawCode=PEN&division=&title=8.&part=1.&chapter=&article="
meta = json.load(open(os.path.join(HERE, "raw", "meta.json")))

def clean(t):
    t = re.sub(r"<[^>]+>", "", t)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()

HIST_INLINE = re.compile(r"\s*\((?:Repealed|Amended|Added|Enacted)[^()]*(?:\([^()]*\)[^()]*)*\)\s*$")   # "(Repealed and added … Sec. 4.)" ends some paragraphs

def paragraphs(items):
    paras = []
    for t in items:
        t = HIST_INLINE.sub("", t)
        if not t: continue
        while (m := re.match(r"^(\((?:\d+[A-Za-z]?|[A-Za-z]{1,5})\))\s+(?=\((?:\d+[A-Za-z]?|[A-Za-z]{1,5})\)\s)", t)): t = m.group(1) + t[m.end():]   # "(a) (1) …" → "(a)(1) …"
        # "(a)(1) …" opens two outline levels on one line; give each label its own line
        if (chain := LEAD_CHAIN.match(t)) and len(labels := re.findall(r"\([^)]+\)", chain.group(0))) > 1:
            for L in labels[:-1]: paras.append({"i": 0, "t": L})
            t = t[chain.end() - len(labels[-1]):]
        paras.append({"i": 0, "t": t.strip()})
    outline_levels(paras)
    base = 0                                  # items under an unlabeled line ending in ":" sit one level under it
    for p in paras:
        if LEAD_CHAIN.match(p["t"]): p["i"] += base
        else: base = 1 if re.search(r"[:—]\s*$", p["t"]) else 0
    return paras

out = []
chapters = sorted(meta["chapters"], key=lambda c: float(c))
for ch in chapters:
    page = open(os.path.join(HERE, "raw", f"{ch}.html"), encoding="utf-8").read()
    head = re.search(r"<h5[^>]*><b>CHAPTER\s+([\d.]+)\.\s*(.*?)\s*\[", page, re.S)
    chap_title = clean(head.group(2))
    body = page.split("manylawsections", 1)[1]
    hs = list(re.finditer(r"<h6[^>]*>\s*<a [^>]*>\s*([^<]+?)\s*</a>\s*</h6>", body))
    for k, h in enumerate(hs):
        num = h.group(1).strip().rstrip(".")
        seg = body[h.end(): hs[k + 1].start() if k + 1 < len(hs) else len(body)]
        items, hist = [], ""
        for m in re.finditer(r'<p style="([^"]*)">(.*?)</p>', seg, re.S):
            t = clean(m.group(2))
            if not t: continue
            if "font-size:0.9em" in m.group(1): hist = t.strip("() ").rstrip("."); continue
            items.append(t)
        text = paragraphs(items)
        if not text or re.match(r"(?i)^\(?(repealed|renumbered)\b", text[0]["t"]) and len(text) == 1: continue
        out.append({
            "section": num, "code": num, "cite": f"§ {num}", "title": "", "chapter": ch, "chapterTitle": chap_title,
            "text": text, "source": hist + "." if hist else "", "footnotes": [], "url": SEC_URL + num,
        })

plain_path, elements_path = os.path.join(HERE, "plain.json"), os.path.join(HERE, "elements.json")
plain = json.load(open(plain_path, encoding="utf-8")) if os.path.exists(plain_path) else {}
elements = json.load(open(elements_path, encoding="utf-8")) if os.path.exists(elements_path) else {}

if "--batches" in sys.argv:                 # sections not yet in plain.json, in batches for review
    d = sys.argv[sys.argv.index("--batches") + 1]
    os.makedirs(d, exist_ok=True)
    todo = [c for c in out if c["section"] not in plain]
    for k in range(0, len(todo), 30):
        batch = [{"section": c["section"], "cite": c["cite"], "chapter": f'{c["chapter"]}. {c["chapterTitle"]}', "text": [{"i": p["i"], "t": p["t"]} for p in c["text"]]} for c in todo[k:k + 30]]
        json.dump(batch, open(os.path.join(d, f"in_{k // 30 + 1:02d}.json"), "w"), ensure_ascii=False, indent=1)
    print(f"{len(out)} sections parsed; wrote {(len(todo) + 29) // 30} batches of up to 30 sections ({len(todo)} sections) to {d}")
    sys.exit()

unmatched = removed = filled = 0
for c in out:
    c.update(plain.get(c["section"], {}))
    c["title"] = (c.get("title") or "").rstrip(".") or f"Section {c['section']}"
    unmatched += apply_acts(c)
    if c["section"] in elements:
        c["elements"] = elements[c["section"]]
        removed += own_text_only(c["code"], c["elements"])
        filled += fill_act_gaps(c)
    tidy_acts(c)
print(f"{unmatched} act phrases not found; {removed} borrowed breakdown items removed; {filled} act highlights added from breakdowns")
missing = [c["section"] for c in out if c["section"] not in plain]
if missing: print(len(missing), "sections not reviewed yet (left out until they are in plain.json):", missing[:10])
dropped = [c["section"] for c in out if c.get("isOffense") is False]
out = [c for c in out if c["section"] in plain and c.get("isOffense") is not False]
print(len(dropped), "sections excluded as not defining a crime")

json.dump({"jurisdiction": "ca", "frequency": None,
           "edition": f"California Penal Code, Part 1, Title 8 (Of Crimes Against the Person), official text from the California Legislative Information site (downloaded {meta['fetched']})",
           "source": TITLE_URL, "crimes": out}, open(os.path.join(HERE, "crimes.json"), "w"), ensure_ascii=False, indent=1)
print(len(out), "sections written to ca/crimes.json")
