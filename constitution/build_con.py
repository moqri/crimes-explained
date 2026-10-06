"""Build constitution/crimes.json (the provisions of the Constitution of the United States) from the GovInfo text
(constitution/raw/us.htm, from fetch_con.py), plus the reviewed data in constitution/plain.json (captions, summaries,
topics, kinds, highlighted phrases) and constitution/elements.json (provision breakdowns).
Usage: python3 constitution/build_con.py [--batches DIR]
--batches writes the parsed provisions that are not yet in plain.json in batches as input for the review agents.

Units: the Preamble, each section of Articles I-IV, Articles V-VII, and each amendment (or each section of an amendment
that has sections). Ids: "preamble", "art1-s8", "art5", "amend1", "amend14-s1". The clause numbers of the GPO print
("\\3\\") become paragraph labels "[3]"; its notes ("This clause has been affected by amendment XVII") become footnotes.
The file is named crimes.json so the shared page code can load it like the other jurisdictions.
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

SRC_URL = "https://www.govinfo.gov/content/pkg/CDOC-110hdoc50/html/CDOC-110hdoc50.htm"
PDF_URL = "https://www.govinfo.gov/content/pkg/CDOC-110hdoc50/pdf/CDOC-110hdoc50.pdf"
ROMAN = {r: i + 1 for i, r in enumerate("I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX XXI XXII XXIII XXIV XXV XXVI XXVII".split())}
ART_TITLES = {"1": "Congress", "2": "The President", "3": "The Courts", "4": "The States", "5": "Amending the Constitution",
              "6": "Debts, Supremacy and Oaths", "7": "Ratification"}

raw = open(os.path.join(HERE, "raw", "us.htm"), encoding="utf-8", errors="replace").read()
raw = re.sub(r"</?(?:html|body|pre)>", "", raw).replace("``", "\u201c").replace("''", "\u201d")
start = raw.index("We the People of the United States")
end = raw.index("PROPOSED AMENDMENTS TO THE CONSTITUTION NOT RATIFIED")
lines = raw[start:end].split("\n")

# 1. Footnote blocks sit between lines of dashes; collect them by number and drop them from the text.
notes, body, i = {}, [], 0
while i < len(lines):
    if re.match(r"^-{20,}\s*$", lines[i]):
        j = i + 1
        while j < len(lines) and not re.match(r"^-{20,}\s*$", lines[j]): j += 1
        cur = None
        for ln in lines[i + 1:j]:
            if re.match(r"^\s*\*\s\*\s\*", ln): continue
            m = re.match(r"^\\(\d+)\\(.*)", ln)
            if m: cur = m.group(1); notes[cur] = m.group(2).strip(); continue
            if cur: notes[cur] += " " + ln.strip()
        i = j + 1; continue
    body.append(lines[i]); i += 1
notes = {k: re.sub(r"(\w)- (\w)", r"\1-\2", re.sub(r"\s+", " ", v)).strip() for k, v in notes.items()}

# 2. Paragraphs: a new one starts at an indented line ("    Section 2.", "    \3\…") or after a blank line.
paras, buf = [], []
def flush():
    if buf: paras.append(re.sub(r"(\w)- (\w)", r"\1-\2", re.sub(r"\s+", " ", " ".join(buf))).strip()); buf.clear()   # "Thirty- eighth": a hyphen at a line break
for ln in body:
    if not ln.strip(): flush(); continue
    if re.match(r"^ {4}\S", ln) or re.match(r"^\s{10,}(Article|Proposal and Ratification|Certification of Validity)", ln): flush()
    buf.append(ln.strip())
flush()

# 3. Walk the paragraphs into units.
units, cur, art, amend, mode = [], None, None, None, "pre"
def new_unit(uid, cite, chapter, chapter_title):
    global cur
    cur = {"section": uid, "code": uid, "cite": cite, "title": "", "chapter": chapter, "chapterTitle": chapter_title,
           "text": [], "source": "", "footnotes": [], "url": SRC_URL, "_notes": []}
    units.append(cur)
CLAUSE = [""]                                   # the clause label of the paragraph being read, e.g. "[3]"
def take_notes(t):
    for n in re.findall(r"\\(\d+)\\", t):
        if n in notes and cur is not None: cur["_notes"].append((n, CLAUSE[0]))
    return re.sub(r"\\\d+\\", "", t).strip()

new_unit("preamble", "Preamble", "pre", "Preamble")
skip = False
for p in paras:
    if "ARTICLES IN ADDITION TO" in p: mode = "amend"; skip = False; continue
    if p.lower().startswith("done in convention") or p.startswith("In witness whereof"): skip = True; continue
    m = re.match(r"^Article \[?([IVX]+)\.?\]?\.?\s*((?:\\\d+\\)*)\s*$", p)
    if m:
        skip = False
        num = ROMAN[m.group(1)]
        if mode == "amend":
            amend, art = num, None
            ch = "BR" if num <= 10 else "AM"
            new_unit(f"amend{num}", f"Amend. {m.group(1)}", ch, "Bill of Rights" if ch == "BR" else "Later Amendments")
            pending = m.group(2)
        else:
            art = str(num); new_unit(f"art{art}", f"Art. {m.group(1)}", art, ART_TITLES[art]); pending = m.group(2)
        take_notes(pending); cur["_roman"] = m.group(1)
        continue
    if skip: continue
    if re.fullmatch(r"[A-Z ,.\\\d]+", p): continue                   # the all-caps heading of the amendments
    if p in ("Proposal and Ratification", "Certification of Validity"):
        cur["_hist"] = p; continue
    if cur.get("_hist"):
        if cur["_hist"] == "Proposal and Ratification":
            first = re.split(r"(?<=\.)\s+(?:The dates of ratification|This amendment was ratified by|The amendment was ratified by|Ratification was)", p)[0]
            if not cur["source"]: cur["source"] = take_notes(first)
            if (r := re.search(r"Ratification was completed on ([^.]+)\.", p)): cur["source"] += f" Ratification was completed on {r.group(1)}."
        continue
    sm = re.match(r"^Section (\d+)\.\s*(.*)", p)
    if sm and cur["section"] != "preamble":
        base = cur["section"].split("-s")[0]
        roman, ch, cht = cur["_roman"], cur["chapter"], cur["chapterTitle"]
        if cur["section"] == base and not cur["text"]: units.pop()    # the heading's unit is replaced by its sections
        else: pass
        kind = "Amend." if base.startswith("amend") else "Art."
        new_unit(f"{base}-s{sm.group(1)}", f"{kind} {roman}, \u00a7 {sm.group(1)}", ch, cht); cur["_roman"] = roman
        p = sm.group(2)
    cm = re.match(r"^\\(\d+)\\\s*(.*)", p)
    label = ""
    if cm and not (cm.group(1) in notes and not cur["text"] and False):
        label, p = f"[{cm.group(1)}]", cm.group(2)
    CLAUSE[0] = label
    t = take_notes(p)
    if t: cur["text"].append({"i": 0, "t": (label + " " + t).strip()})

# Amendments I-X share the First Congress's note (proposal and ratification of the Bill of Rights).
for u in units:
    if u["section"].startswith("amend") and not u["source"]:
        base = u["section"].split("-s")[0]
        sib = next((v for v in units if v["section"].split("-s")[0] == base and v["source"]), None)
        if sib: u["source"] = sib["source"]
        elif u["chapter"] == "BR" and "12" in notes:
            n = notes["12"]
            u["source"] = n.split(". The first ten")[0].replace("The first ten amendments of the Constitution of the United States (and two others, one of which failed of ratification and the other which later became the 27th amendment) were", "The first ten amendments were") + ". Ratification was completed on December 15, 1791."
    keep = [(n, cl) for n, cl in dict.fromkeys(u.pop("_notes")) if n not in ("1", "12")
            and re.search(r"affected|superseded|repealed|changed|numbers assigned|modified", notes[n], re.I)]
    u["footnotes"] = [notes[n] for n, _ in keep]
    u["noteClauses"] = [cl for _, cl in keep]       # the clause each note is attached to ("" = the whole provision)
    for k in ("_roman", "_hist"): u.pop(k, None)
units = [u for u in units if u["text"]]
print(len(units), "provisions parsed")

plain_path, elements_path = os.path.join(HERE, "plain.json"), os.path.join(HERE, "elements.json")
plain = json.load(open(plain_path, encoding="utf-8")) if os.path.exists(plain_path) else {}
elements = json.load(open(elements_path, encoding="utf-8")) if os.path.exists(elements_path) else {}

if "--batches" in sys.argv:
    d = sys.argv[sys.argv.index("--batches") + 1]
    os.makedirs(d, exist_ok=True)
    todo = [u for u in units if u["section"] not in plain]
    size = 20
    for k in range(0, len(todo), size):
        batch = [{"section": u["section"], "cite": u["cite"], "part": f'{u["chapter"]}. {u["chapterTitle"]}', "notes": [{"clause": cl, "note": f} for f, cl in zip(u["footnotes"], u["noteClauses"])],
                  "text": [{"i": p["i"], "t": p["t"]} for p in u["text"]]} for u in todo[k:k + size]]
        json.dump(batch, open(os.path.join(d, f"in_{k // size + 1:02d}.json"), "w"), ensure_ascii=False, indent=1)
    print(f"wrote {(len(todo) + size - 1) // size} batches ({len(todo)} provisions) to {d}")
    sys.exit()

def apply_marks(u):
    """Highlighted phrases (review lists "rights", "powers", "limits") become ranges on the paragraph that holds them:
    p["m"] = [[start, end, kind], …], kind "right" | "power" | "limit". Returns how many phrases were not found."""
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
json.dump({"jurisdiction": "us", "doc": "con", "frequency": None,
           "edition": "The Constitution of the United States of America, As Amended (House Document 110-50, Government Printing Office, 2007; no amendment has been ratified since), from GovInfo",
           "source": SRC_URL, "pdf": PDF_URL, "crimes": units}, open(os.path.join(HERE, "crimes.json"), "w"), ensure_ascii=False, indent=1)
print(len(units), "provisions written to constitution/crimes.json")
