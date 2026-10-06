"""Build ma/constitution/crimes.json (the provisions of the Constitution of the Commonwealth of Massachusetts) from the
Legislature's page (ma/constitution/raw/constitution.html, from constitution/fetch_ma.py), plus the reviewed data in
ma/constitution/plain.json and ma/constitution/elements.json (same review format as the U.S. Constitution).
Usage: python3 constitution/build_ma.py [--batches DIR]

Units: the Preamble; each article of Part the First (the Declaration of Rights); each article of Part the Second (the
Frame of Government), by chapter and section; and each Article of Amendment (Article XLVIII, the initiative and
referendum, is split into its parts). Ids: "preamble", "decl14", "p2-c1-s2-a7", "p2-c3-a1", "amend48-init2", "amend121".
Bracketed editorial notes in the text ("[Annulled by Amendments, Art. CVI.]", "[See Amendments, Arts. XLVI and XLVIII.]")
become footnotes; other bracketed words are text the Legislature marks as superseded and stay in the text as printed.
Links the page itself makes between articles become paragraph link ranges p["l"] = [[start, end, unit id], …].
"""
import html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DIR = os.path.join(ROOT, "ma", "constitution")
SRC = "https://malegislature.gov/Laws/Constitution"
meta = json.load(open(os.path.join(DIR, "raw", "meta.json")))
page = open(os.path.join(DIR, "raw", "constitution.html"), encoding="utf-8").read()
body = page[page.index('id="constitution"'):]
body = body[:body.index('<h2 id="note"')]                      # the historical note after the amendments is left out

def roman(r):
    v = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
    return sum(-v[c] if i + 1 < len(r) and v[c] < v[r[i + 1]] else v[c] for i, c in enumerate(r))

# Editorial notes start with these words; any other bracketed passage is text the Legislature prints as superseded.
# The article number may itself be a link ("Art. <a …>XI</a> of the Amendments"), and a note at the end of a paragraph
# sometimes lacks its closing bracket ("[Annulled and superseded by Amendments, Art. LXXVII.").
NOTE = re.compile(r"\[\s*(?:[Ss]ee\b|For\s|Annulled\b|Superseded\b|Amended\b|This paragraph\b|Last two paragraphs\b|Art\.\s*(?:<a[^>]*>)?[IVXLC]+(?:</a>)?\s+of the Amendments)(?:[^\[\]]|<[^>]*>)*?(?:\]|(?=\s*$))", re.S)
# In Article XLVIII the later parts are headed by ordinary paragraphs ("II. Emergency Measures.", "General Provisions.").
HEAD48 = re.compile(r"^(?:The Referendum\.\s*)?(?:[IVX]+\.\s+[A-Z][^.]{2,90}\.?|General Provisions\.?|The Referendum\.?)$")

def clean(frag):
    """HTML of a paragraph → (text, link ranges to page anchors, bracketed notes)."""
    notes = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m.group(0)))).strip() for m in NOTE.finditer(frag)]
    frag = NOTE.sub(" ", frag)
    frag = re.sub(r"\[\s*(?:[Ss]ee|For)\b(?:[^\[\]]|<[^>]*>)*$", " ", frag)   # a broken, unclosed copy of a note ("[See Amendments, Art.")
    out, links, pos = "", [], 0
    for m in re.finditer(r'<a [^>]*href="#([^"]+)"[^>]*>(.*?)</a>|<[^>]+>|[^<]+', frag, re.S):
        if m.group(1) is not None:
            t = html.unescape(re.sub(r"<[^>]+>", "", m.group(2)))
            links.append([len(out), len(out) + len(t), m.group(1)]); out += t
        elif m.group(0).startswith("<"): continue
        else: out += html.unescape(m.group(0))
    # collapse whitespace while keeping the link offsets right
    keep, new, mapping = "", [], {}
    for i, ch in enumerate(out):
        if ch.isspace() and (not keep or keep[-1] == " "): mapping[i] = len(keep); continue
        mapping[i] = len(keep); keep += " " if ch.isspace() else ch
    mapping[len(out)] = len(keep)
    text = keep.strip(); lead = len(keep) - len(keep.lstrip())
    for s, e, a in links:
        s2, e2 = mapping[s] - lead, mapping[e] - lead
        while e2 > s2 and text[e2 - 1:e2] == " ": e2 -= 1
        if e2 > s2: new.append([s2, e2, a])
    text = re.sub(r"\s+([,.;:])", r"\1", text) if False else text
    return text, new, notes

units, anchors = [], {}
NOTE_RUN = [False]                               # inside a bracketed note that spans paragraphs
cur, part, chap, chap_title, sect, group = None, None, None, "", None, ""
def new_unit(uid, cite, chapter, chapter_title, anchor_ids=()):
    global cur
    cur = {"section": uid, "code": uid, "cite": cite, "title": "", "chapter": chapter, "chapterTitle": chapter_title,
           "text": [], "source": "", "footnotes": [], "url": SRC + (f"#{anchor_ids[0]}" if anchor_ids else ""), "_links": []}
    units.append(cur)
    for a in anchor_ids: anchors[a] = uid

def part48(aid, head):
    """Article XLVIII: each part is its own provision; "The Initiative." / "The Referendum." / "General Provisions." group the parts after them."""
    global group
    g = re.match(r"^(The Referendum)\.\s*(.*)$", head)
    if g: group = g.group(1); head = g.group(2)
    if not head: return
    if not re.match(r"^[IVX]+\.", head): group = head.rstrip("."); return
    pm = re.match(r"^([IVX]+)\.\s*(.*)", head)
    words = re.sub(r"[^a-z ]", "", pm.group(2).lower()).split()
    slug = ("".join(w[:4] for w in words[:3]) or "part") + str(roman(pm.group(1)))
    gslug = {"The Initiative": "init-", "The Referendum": "ref-", "General Provisions": "gen-"}.get(group, "")
    uid = f"amend48-{gslug}{slug}"
    while any(u["section"] == uid for u in units): uid += "x"
    if cur["section"] == "amend48" and not cur["text"]: units.pop()
    label = ((group + ", ") if group else "") + head.rstrip(".")
    new_unit(uid, f"Amend. Art. XLVIII, {label}", "amend", "Articles of Amendment", [aid] if aid else [])

CHAP_TITLES = {"1": "Legislative Power", "2": "Executive Power", "3": "Judiciary Power", "4": "Delegates to Congress",
               "5": "The University at Cambridge, and Encouragement of Literature", "6": "Oaths, Commissions and Other Provisions"}
for m in re.finditer(r'<(h[2-5]|p)\b([^>]*)>(.*?)</\1>', body, re.S):
    tag, attrs, inner = m.group(1), m.group(2), m.group(3)
    aid = (re.search(r'id="([^"]+)"', attrs) or [None, None])[1]
    head = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", inner))).strip()
    if tag != "p":
        if aid == "preamble": part = "pre"; new_unit("preamble", "Preamble", "pre", "Preamble", [aid]); continue
        if aid == "partTheFirst": part = "decl"; continue
        if aid == "partTheSecond":                    # its opening paragraph (the people form the Commonwealth) is its own provision
            part = "p2"; new_unit("p2", "Pt. 2, opening", "frame", "The Frame of Government", [aid]); continue
        if aid == "articlesOfAmendment": part = "amend"; continue
        if part == "decl" and aid and (a := re.fullmatch(r"article([IVXLC]+)", aid)):
            n = roman(a.group(1)); new_unit(f"decl{n}", f"Decl. of Rights, Art. {a.group(1)}", "decl", "Declaration of Rights", [aid]); continue
        if part == "p2" and aid and (c := re.fullmatch(r"chapter([IVX]+)(?:Section([IVX]+))?", aid)):
            chap, sect = str(roman(c.group(1))), (str(roman(c.group(2))) if c.group(2) else None)
            chap_title = CHAP_TITLES.get(chap, "")
            cid = f"p2-c{chap}" + (f"-s{sect}" if sect else "")
            new_unit(cid, f"Pt. 2, c. {c.group(1)}" + (f", § {c.group(2)}" if sect else ""), f"c{chap}", chap_title, [aid]); continue
        if part == "p2" and aid and (a := re.search(r"[Aa]rticle([IVXLC]+)$", aid)):
            n = roman(a.group(1)); base = f"p2-c{chap}" + (f"-s{sect}" if sect else "")
            if cur and cur["section"] == base and not cur["text"]: units.pop()     # the chapter heading's unit is replaced by its articles
            cite = f"Pt. 2, c. {['', 'I', 'II', 'III', 'IV', 'V', 'VI'][int(chap)]}" + (f", § {['', 'I', 'II', 'III', 'IV'][int(sect)]}" if sect else "") + f", Art. {a.group(1)}"
            new_unit(f"{base}-a{n}", cite, f"c{chap}", chap_title, [aid]); continue
        if part == "amend":
            if aid and (a := re.fullmatch(r"amendmentArticle([IVXLC]+)", aid)):
                n = roman(a.group(1)); group = ""
                new_unit(f"amend{n}", f"Amend. Art. {a.group(1)}", "amend", "Articles of Amendment", [aid]); continue
            if cur and cur["section"].startswith("amend48"): part48(aid, head); continue
        continue
    if cur is None: continue
    text, links, notes = clean(inner)
    if cur["section"].startswith("amend48") and HEAD48.match(text) and not links: part48(None, text); continue
    # A bracketed note can run over several paragraphs ("[For … see Amendments, Arts. II and LXXXIX." … "… Art. CXII.]").
    if NOTE_RUN[0] or re.match(r"^\[\s*(?:[Ss]ee\b|For\s|Annulled\b|Superseded\b|Amended\b)", text) and "]" not in text:
        NOTE_RUN[0] = not text.rstrip().endswith("]")
        cur["footnotes"].append(text.strip("[] ")); continue
    cur["footnotes"] += [n for n in notes if n not in cur["footnotes"]]
    if text:
        cur["text"].append({"i": 0, "t": text})
        if links: cur["_links"].append((len(cur["text"]) - 1, links))

# Resolve the page's own links to provision ids (an anchor inside Article XLVIII falls back to its first part).
ids = {u["section"] for u in units if u["text"]}
first48 = next(u["section"] for u in units if u["section"].startswith("amend48-"))
anchors = {a: (t if t in ids else first48 if t.startswith("amend48") else t) for a, t in anchors.items()}
for u in units:
    for k, links in u.pop("_links"):
        res = []
        for s, e, a in links:
            tid = anchors.get(a) or (anchors.get(re.sub(r"(Initiative|Referendum|Definition|GeneralProvisions|ProposedAmendments|ProposedLaws|Conflicts).*$", "", a)))
            if not tid and a.startswith("amendmentArticleXLVIII"): tid = next((x["section"] for x in units if x["section"].startswith("amend48-")), None)
            if tid and tid != u["section"]: res.append([s, e, tid])
        if res: u["text"][k]["l"] = res
units = [u for u in units if u["text"]]
print(len(units), "provisions parsed:", sum(u["section"].startswith("decl") for u in units), "in the Declaration of Rights,",
      sum(u["section"].startswith("p2") for u in units), "in the Frame of Government,", sum(u["section"].startswith("amend") for u in units), "Articles of Amendment")

plain_path, elements_path = os.path.join(DIR, "plain.json"), os.path.join(DIR, "elements.json")
plain = json.load(open(plain_path, encoding="utf-8")) if os.path.exists(plain_path) else {}
elements = json.load(open(elements_path, encoding="utf-8")) if os.path.exists(elements_path) else {}

if "--batches" in sys.argv:
    d = sys.argv[sys.argv.index("--batches") + 1]
    os.makedirs(d, exist_ok=True)
    todo = [u for u in units if u["section"] not in plain]
    size, first = 20, int(sys.argv[sys.argv.index("--start") + 1]) if "--start" in sys.argv else 1   # --start N: number the files from N
    for k in range(0, len(todo), size):
        batch = [{"section": u["section"], "cite": u["cite"], "part": u["chapterTitle"], "notes": [{"clause": "", "note": f} for f in u["footnotes"]],
                  "text": [{"i": p["i"], "t": p["t"]} for p in u["text"]]} for u in todo[k:k + size]]
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
parts = {"pre": "Preamble", "decl": "Declaration of Rights", "frame": "Pt. 2, opening", "c1": "Pt. 2, c. I", "c2": "Pt. 2, c. II", "c3": "Pt. 2, c. III",
         "c4": "Pt. 2, c. IV", "c5": "Pt. 2, c. V", "c6": "Pt. 2, c. VI", "amend": "Amendments"}
json.dump({"jurisdiction": "ma", "doc": "con", "frequency": None, "partNames": parts,
           "edition": f"Constitution of the Commonwealth of Massachusetts, official text from the Massachusetts Legislature (malegislature.gov, downloaded {meta['fetched']})",
           "source": SRC, "crimes": units}, open(os.path.join(DIR, "crimes.json"), "w"), ensure_ascii=False, indent=1)
print(len(units), "provisions written to ma/constitution/crimes.json")
