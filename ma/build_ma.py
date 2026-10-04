"""Build ma/crimes.json from the downloaded Massachusetts General Laws (ma/raw/*.json, from fetch_ma.py), plus the
hand-reviewed data in ma/plain.json (which sections define crimes, summaries, types, maximum penalties, act phrases)
and ma/elements.json (crime breakdowns). Usage: python3 ma/build_ma.py [--batches DIR]
--batches writes the parsed sections in batches of 30 as input for the review agents.
"""
import datetime, glob, html, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from textlib import LEAD_CHAIN, outline_levels, apply_acts, own_text_only, fill_act_gaps, tidy_acts

SITE = "https://malegislature.gov/Laws/GeneralLaws"

def frac(t):
    """The official text writes ½ and ¾ as "1/2" and "3/4" run into the number: "21/2 years" is 2½ years, section "13B1/2" is 13B½."""
    return re.sub(r"(?<=[\dA-Z])(1/2|3/4)\b", lambda m: "½" if m.group(1) == "1/2" else "¾", t)

# Part and title of each chapter, for official links (fractional sections such as 13B½ only resolve on the full path).
TITLE_OF = {**{str(n): ("IV", "I") for n in range(263, 275)}, **{c: ("IV", "I") for c in ("263A", "267A", "268A", "268B", "271A", "273A")}}

def clean(t):
    t = t.replace("&Prime;", "''")
    t = html.unescape(t)
    t = frac(t)
    return re.sub(r"\s+", " ", t).strip()                 # single line breaks inside a paragraph are soft wraps

def quotes(t):
    """''term'' → “term”: the API writes quotation marks as two apostrophes."""
    n = [0]
    def q(m): n[0] += 1; return "“" if n[0] % 2 else "”"
    return re.sub(r"''", q, t)

# An enumeration inside one paragraph ("… the following offenses:— (1) armed burglary …; (2) …") gets one line per item.
INLINE_ITEM = re.compile(r"([:;—])\s+((?:or|and)\s+)?(?=\((?:\d+|[a-z]|[ivx]+)\)\s)")   # "; or (11) …": "or" stays with the item before

# Amended text in transition carries notes like "[ First paragraph effective until March 3, 2026. …]" and
# "[ First paragraph as amended by 2025, 79, effective March 3, 2026. …]": keep the version in effect on the download date.
VERSION = re.compile(r"^\[\s*([^\]]*?\beffective (until )?([A-Z][a-z]+ \d{1,2}, \d{4})[^\]]*)\]\s*")

def paragraphs(text, code, on_date, notes):
    paras, skip = [], False
    text = re.sub(r"\s*(\[\s*[^\]]*\beffective\b[^\]]*\])\s*", r"\n\n\1\n\n", text)   # each version note is its own block
    for block in re.split(r"[ \t]*\r?\n[ \t]*\r?\n\s*", text):          # paragraphs are separated by a blank line
        block = clean(block)
        if (v := VERSION.match(block)) and not block[v.end():]:            # a note: it applies to the next paragraph
            when = datetime.datetime.strptime(v.group(3), "%B %d, %Y").date()
            skip = (when <= on_date) == bool(v.group(2))                 # that paragraph is not the version in effect
            if not skip and not v.group(2): notes.append(re.sub(r"amended by (\d{4}), (\d+)", r"amended by St. \1, c. \2", re.sub(r"\.\s*For text.*$", "", v.group(1))).strip().rstrip("."))
            continue
        if skip: skip = False; continue
        if not block: continue
        block = re.sub(rf"^Section\s+{re.escape(frac(code))}\.\s*", "", block)   # "Section 13B½. " opens the first paragraph
        block = quotes(block)
        if not block: continue
        pieces = INLINE_ITEM.sub(lambda m: m.group(1) + (" " + m.group(2).strip() if m.group(2) else "") + "\0", block).split("\0") if re.search(r"[:—]\s+\((?:1|a|i)\)\s", block) else [block]
        for t in pieces:
            # "(a)(1) …" opens two outline levels on one line; give each label its own line
            if (chain := LEAD_CHAIN.match(t)) and len(labels := re.findall(r"\([^)]+\)", chain.group(0))) > 1:
                for L in labels[:-1]: paras.append({"i": 0, "t": L})
                t = t[chain.end() - len(labels[-1]):]
            paras.append({"i": 0, "t": t.strip()})
    outline_levels(paras)
    # Items introduced by an unlabeled line ("Whoever commits …:") sit one level under it.
    base = 0
    for p in paras:
        if LEAD_CHAIN.match(p["t"]): p["i"] += base
        else: base = 1 if re.search(r"[:—]\s*$", p["t"]) else 0
    return paras

def title_case(s):
    small = {"and", "of", "in", "or", "the", "to", "for", "on", "a", "an", "by", "with"}
    return " ".join(w.capitalize() if i == 0 or w.lower() not in small else w.lower() for i, w in enumerate(s.lower().split()))

out, fetched = [], set()
for path in sorted(glob.glob(os.path.join(HERE, "raw", "*.json")), key=lambda p: (int(re.match(r"\d+", os.path.basename(p)).group()), p)):
    raw = json.load(open(path, encoding="utf-8"))
    fetched.add(raw["fetched"])
    chap = raw["chapter"]
    for s in raw["sections"]:
        if s["IsRepealed"] or not (s.get("Text") or "").strip(): continue
        code = frac(s["Code"])                                # display form: 13B½
        slug = code.replace("½", "1~2").replace("¾", "3~4")   # file and link form, as on malegislature.gov
        part, title = TITLE_OF.get(chap, (raw["part"], None))
        out.append({
            "section": f"{chap}/{slug}", "code": code, "cite": f"c. {chap}, § {code}",
            "title": s["Name"].rstrip("."), "chapter": chap, "chapterTitle": title_case(raw["name"]),
            "text": paragraphs(s["Text"], s["Code"], datetime.date.fromisoformat(raw["fetched"]), notes := []),
            "source": "", "footnotes": [f"{n}." for n in notes],
            "url": f"{SITE}/Part{part}/Title{title}/Chapter{chap}/Section{slug}" if title else f"{SITE}/Chapter{chap}/Section{slug}",
        })

if "--batches" in sys.argv:                 # sections not yet in plain.json, in batches for review
    d = sys.argv[sys.argv.index("--batches") + 1]
    os.makedirs(d, exist_ok=True)
    reviewed = json.load(open(os.path.join(HERE, "plain.json"))) if os.path.exists(os.path.join(HERE, "plain.json")) else {}
    out = [c for c in out if c["section"] not in reviewed]
    for k in range(0, len(out), 30):
        batch = [{"section": c["section"], "cite": c["cite"], "title": c["title"], "text": [{"i": p["i"], "t": p["t"]} for p in c["text"]]} for c in out[k:k + 30]]
        json.dump(batch, open(os.path.join(d, f"in_{k // 30 + 1:02d}.json"), "w"), ensure_ascii=False, indent=1)
    print(f"wrote {(len(out) + 29) // 30} batches of up to 30 sections to {d}")
    sys.exit()

plain_path, elements_path = os.path.join(HERE, "plain.json"), os.path.join(HERE, "elements.json")
plain = json.load(open(plain_path, encoding="utf-8")) if os.path.exists(plain_path) else {}
elements = json.load(open(elements_path, encoding="utf-8")) if os.path.exists(elements_path) else {}
unmatched = removed = filled = 0
for c in out:
    c.update(plain.get(c["section"], {}))
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

json.dump({"jurisdiction": "ma", "frequency": None,
           "edition": f"Massachusetts General Laws, official text from the Massachusetts Legislature (downloaded {max(fetched)})",
           "source": "https://malegislature.gov/Laws/GeneralLaws/PartIV/TitleI",
           "crimes": out}, open(os.path.join(HERE, "crimes.json"), "w"), ensure_ascii=False, indent=1)
print(len(out), "sections written to ma/crimes.json")
