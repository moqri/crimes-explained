import re, json, html, urllib.request
SRC = "https://www.govinfo.gov/content/pkg/USCODE-2024-title18/html/USCODE-2024-title18-partI.htm"
doc = urllib.request.urlopen(urllib.request.Request(SRC, headers={"User-Agent": "Mozilla/5.0"})).read().decode("utf-8")
LIMIT = None  # set to a number to keep only the first N sections
# Pre-filter only the obvious: repealed/transferred entries ("[§ 14. Repealed…]") and pure definition sections.
# Whether a section actually defines a crime is decided per section in plain.json ("isOffense").
SKIP = re.compile(r"^(\[|Definitions?( for (certain provisions|chapter)\b.*)?$|.* defined$|Definitions? (for|relating to) )")

HEAD_THEN_LABEL = re.compile(r"^((?:\([A-Za-z0-9]+\)\s*)+[A-Z][^.—]{0,80}?\.—)\s*(\((?:[a-z]{1,2}|\d+|[A-Z]{1,2}|[ivxl]+)\)\s.*)$", re.S)

LEAD_CHAIN = re.compile(r"^(?:\((?:\d+[A-Za-z]?|[A-Za-z]{1,5})\))+(?=\s|$)")
ROMAN = re.compile(r"^(?=[ivxl])(xl|l?x{0,3})(ix|iv|v?i{0,3})$")

def label_kind(L, stack, last, upcoming):
    """Kind of an outline label: digit, lower, upper, rlower (i, ii…), rupper (I, II…), or double (aa, AA)."""
    if L[0].isdigit(): return "digit"
    lower = L.islower()
    letter, roman = ("lower", "rlower") if lower else ("upper", "rupper")
    if len(L) > 1:
        return roman if ROMAN.match(L.lower()) else "double"                    # (ii), (iv) vs (aa), (bb)
    if L.lower() not in "ivx": return letter
    if L.lower() == "i":                                                      # clause (i) if (ii) comes before (j)
        for u in upcoming:
            if u == ("ii" if lower else "II"): return roman
            if u == ("j" if lower else "J"): return letter
        return letter
    prev = last.get(letter)
    if letter in stack and prev and ord(L) == ord(prev) + 1: return letter     # (u) -> (v)
    if roman in stack: return roman                                           # (iv) -> (v)
    return letter                                                             # (u) -> (x) with (v), (w) repealed

def outline_levels(paras):
    """Indent by outline depth, not by the source's print layout. Depth follows the order label kinds appear in:
    a new kind opens a level, a kind already open closes everything below it. Usually (a) → (1) → (A) → (i) → (I),
    but this also handles sections numbered (1) → (a) → (i). A line starting with chained labels, e.g.
    "(b)(2)(A) …", sits at its first label's depth and opens the rest."""
    chains = [re.findall(r"\(([^)]+)\)", m.group(0)) if (m := LEAD_CHAIN.match(p["t"])) else None for p in paras]
    stack, last = [], {}
    for k, (p, chain) in enumerate(zip(paras, chains)):
        if not chain: continue
        depth = None
        for j, L in enumerate(chain):
            upcoming = chain[j + 1:] + [x for c in chains[k + 1:] if c for x in c]
            kind = label_kind(L, stack, last, upcoming)
            if kind in stack: del stack[stack.index(kind) + 1:]
            else: stack.append(kind)
            last[kind] = L
            for gone in [x for x in last if x not in stack]: del last[gone]
            depth = len(stack) - 1 if depth is None else depth
        p["i"] = depth

# Knowledge and intent wording inside a prohibited-act phrase is not part of the act: "receives … the offender in order
# to hinder or prevent his apprehension" → only "receives … the offender". Single words (knowingly, willfully, …) are
# cut out on their own; clauses (in order to …, with intent to …, knowing the …) run to the next comma or semicolon.
MENTAL_WORD = re.compile(r"(?i)\b(?:knowingly|willfully|wilfully|intentionally|maliciously|corruptly|recklessly|fraudulently|purposely)\b(?:\s+(?:and|or)\s+(?=(?:knowingly|willfully|intentionally|maliciously|corruptly|recklessly|fraudulently)\b))?")
MENTAL_CLAUSE = re.compile(r"(?i)\b(?:in order to|with (?:the )?intent(?: to| that)?|for the purpose of|with the purpose of|intending to|knowing(?! ly)\b|having knowledge|having reason to|has reason to|with reckless disregard)[^,;]*")

def without_mental_state(text, start, end):
    """Split the act range [start, end) around mental-state words and clauses; drop pieces that are only connectors."""
    cut = []
    for rx in (MENTAL_CLAUSE, MENTAL_WORD):
        for m in rx.finditer(text, start, end):
            e = min(m.end(), end)
            # a clause that ends a few words short of the phrase end ("…his apprehension, trial or punishment") runs to the end
            if rx is MENTAL_CLAUSE and len(text[e:end].split()) <= 5: e = end
            cut.append((m.start(), e))
    if not cut: return [[start, end]]
    cut.sort()
    pieces, pos = [], start
    for s, e in cut:
        if s > pos: pieces.append([pos, s])
        pos = max(pos, e)
    if pos < end: pieces.append([pos, end])
    out = []
    for s, e in pieces:                      # trim spaces, commas, and dangling "and"/"or"; drop leftover connectors
        while True:
            seg = text[s:e]
            m1 = re.match(r"(?i)^[\s,;]+|^(?:and|or)\b\s*", seg)
            m2 = re.search(r"(?i)[\s,;]+$|\s(?:and|or)$", seg)
            if m1 and m1.end(): s += m1.end(); continue
            if m2 and m2.end() > m2.start(): e -= m2.end() - m2.start(); continue
            break
        if e - s >= 4 and not re.fullmatch(r"(?i)(and|or|and/or|the|to|a|an)", text[s:e]): out.append([s, e])
    if not out:                              # the whole phrase was a clause ("a knowing attempt …"): only drop the words
        return [[start, end]] if not MENTAL_WORD.search(text, start, end) else without_words(text, start, end)
    return out

def without_words(text, start, end):
    pieces, pos = [], start
    for m in re.finditer(r"(?i)\b(?:knowingly|knowing|willfully|intentionally|maliciously|corruptly|recklessly|fraudulently)\b", text[start:end]):
        s, e = start + m.start(), start + m.end()
        if s > pos: pieces.append([pos, s])
        pos = e
    if pos < end: pieces.append([pos, end])
    return [[s + len(text[s:e]) - len(text[s:e].lstrip()), e - (len(text[s:e]) - len(text[s:e].rstrip()))] for s, e in pieces if text[s:e].strip(" ,;") and len(text[s:e].strip()) >= 4]

NEW_PROVISION = re.compile(r"(?<=[.)\]])\s+(?=(?:There is jurisdiction|For (?:the )?purposes of (?:this|such|subsection|section|paragraph)|As used in this|In this (?:section|subsection|paragraph|chapter)|This (?:section|subsection) (?:does not|shall not|shall apply|applies)|Nothing in this)\b)")

def clean(s):
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s = re.sub(r"<sup>\s*<a[^>]*>(.*?)</a>\s*</sup>", r"[\1]", s, flags=re.S)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()

def field(block, name):
    m = re.search(rf"<!-- field-start:{name} -->(.*?)<!-- field-end:{name} -->", block, re.S)
    return m.group(1) if m else ""

parts = re.split(r"(?=<!-- expcite:)", doc)
out, warn = [], []
for blk in parts:
    m = re.match(r"<!-- expcite:.*?CHAPTER (\w+)-(.*?)!@!Sec\. (\w+) -->", blk)
    if not m: continue
    chap, chapTitle, sec = m.groups()
    head = clean(re.search(r'class="section-head">(.*?)</h3>', blk, re.S).group(1))
    title = re.sub(r"^§\s*\w+\.\s*", "", head)
    if SKIP.search(title): continue
    statute = field(blk, "statute")
    paras = []
    # Paragraphs and table rows, in document order. Table rows become "cell — cell" lines.
    for cls, body, row in re.findall(r'<p class="(statutory-body[\w-]*)">(.*?)</p>|<tr>(.*?)</tr>', statute, re.S):
        if row:
            cells = [clean(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
            paras.append({"i": 1, "t": " — ".join(c for c in cells if c)})
            continue
        em = re.search(r"(\d)em", cls)
        indent, t = int(em.group(1)) if em else 0, clean(body)
        # "(b) Offense and Penalties.—(1) A person …" is one paragraph in the source; split it so "(1)"
        # starts its own line like its sibling "(2)" does.
        while (m := HEAD_THEN_LABEL.match(t)):
            paras.append({"i": indent, "t": m.group(1)})
            t = m.group(2)
        # "(b)(1) Subject to …" opens two outline levels on one line; give each label its own line so
        # "(1)" lines up with its sibling "(2)" and "(b)" with "(a)".
        if (chain := LEAD_CHAIN.match(t)) and len(labels := re.findall(r"\([^)]+\)", chain.group(0))) > 1:
            for L in labels[:-1]: paras.append({"i": indent, "t": L})
            t = t[chain.end() - len(labels[-1]):]
        # A closing line often runs into separate provisions ("…or both. There is jurisdiction over …. For purposes of
        # this subsection, …"); start each such provision on its own line.
        for piece in NEW_PROVISION.split(t):
            if piece: paras.append({"i": indent, "t": piece})
    if not paras: warn.append(f"§{sec} has no statute paragraphs")
    outline_levels(paras)
    out.append({
        "section": sec, "title": title, "chapter": chap,
        "chapterTitle": chapTitle.title().replace(" And ", " and ").replace(" Of ", " of ").replace(" In ", " in "),
        "text": paras,
        "source": clean(field(blk, "sourcecredit")),
        "footnotes": [clean(f) for f in re.findall(r'<p class="footnote">(.*?)</p>', field(blk, "footnote"), re.S)],
        "url": f"https://www.govinfo.gov/content/pkg/USCODE-2024-title18/html/USCODE-2024-title18-partI-chap{chap}-sec{sec}.htm",
    })
    if LIMIT and len(out) == LIMIT: break

import os
here = os.path.dirname(os.path.abspath(__file__))
plain_path = os.path.join(here, "plain.json")  # hand-reviewed plain-English summaries, keyed by section
if os.path.exists(plain_path):
    plain = json.load(open(plain_path, encoding="utf-8"))
    for c in out: c.update(plain.get(c["section"], {}))
    missing = [c["section"] for c in out if c["section"] not in plain]
    if missing: print(len(missing), "sections have no plain summary yet")
    # Prohibited-act phrases ("acts") become character ranges on the paragraph that contains them: p["a"] = [[start, end], …].
    unmatched = 0
    for c in out:
        for phrase in c.pop("acts", []):
            hits = [(k, p["t"].find(phrase)) for k, p in enumerate(c["text"]) if phrase in p["t"]]
            if not hits: unmatched += 1; continue
            for k, start in hits[:1] if len(hits) > 3 else hits:      # a very common phrase: mark its first use only
                c["text"][k].setdefault("a", []).append([start, start + len(phrase)])
        for p in c["text"]:
            if "a" in p: p["a"] = [r for s, e in p["a"] for r in without_mental_state(p["t"], s, e)]
        for p in c["text"]:
            if "a" in p:                                             # sort and merge overlapping ranges
                merged = []
                for s, e in sorted(p["a"]):
                    if merged and s <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], e)
                    else: merged.append([s, e])
                p["a"] = merged
    if unmatched: print(unmatched, "act phrases not found in the text")
    later_path = os.path.join(here, "later_amendments.json")  # amendments newer than the GovInfo edition
    if os.path.exists(later_path):
        later = json.load(open(later_path, encoding="utf-8"))
        for c in out:
            if c["section"] in later: c["later"] = later[c["section"]]
    elements_path = os.path.join(here, "elements.json")  # each section's crimes broken into elements
    if os.path.exists(elements_path):
        elements = json.load(open(elements_path, encoding="utf-8"))
        for c in out:
            if c["section"] in elements: c["elements"] = elements[c["section"]]
    dropped = [c["section"] for c in out if c.get("isOffense") is False]
    out = [c for c in out if c.get("isOffense") is not False]
    print(len(dropped), "sections excluded as not defining a crime")

# Every Part I section number, including repealed ones, so the page can tell a real Title 18 reference
# ("section 1111") from a bare reference to another Act ("section 106 (relating to …) of title 17").
part1 = sorted({m for m in re.findall(r"<!-- expcite:[^>]*?!@!\[?Sec\. (\w+)", doc)})

# Statutes at Large targets, cached by resolve_stat_links.py: Public Law HTML (with page) when available, else the PDF and its size.
stat_path = os.path.join(here, "stat_links.json")
stat_links = {}
if os.path.exists(stat_path):
    for k, v in json.load(open(stat_path)).items():
        if not v: continue
        if v.get("plaw"): stat_links[k] = {"plaw": v["plaw"], **({"exact": False} if not v.get("exact") else {})}
        elif v.get("pdf"): stat_links[k] = {"pdf": v["pdf"].replace("https://www.govinfo.gov/content/pkg/", ""), "kb": v.get("kb")}

# Where the law cites "section 101(a)(22) of the Immigration and Nationality Act (8 U.S.C. 1101(a)(22))", remember
# Act + section → Code section, so the same reference without a citation elsewhere can link too.
ACT_CITE = re.compile(r"[Ss]ections?\s+(\d+[A-Za-z]*)(?:\([^)]*\))*\s+of\s+the\s+([A-Z][^();,]{3,90}?)\s*\((\d+)\s+U\.S\.C\.\s+(\d+[a-zA-Z]*(?:[–-]\d+[a-zA-Z]*)?)")
act_sections = {}
for c in out:
    for p in c["text"]:
        for m in ACT_CITE.finditer(p["t"]):
            act_sections.setdefault(f"{re.sub(r'\s+', ' ', m.group(2)).strip().lower()}|{m.group(1)}", [m.group(3), m.group(4)])

json.dump({"partISections": part1, "statLinks": stat_links, "actSections": act_sections, "edition": "United States Code, 2024 Edition (current through Jan. 6, 2025)", "source": SRC, "crimes": out},
          open(os.path.join(here, "crimes.json"), "w"), ensure_ascii=False, indent=1)
print(len(out), "sections;", out[0]["section"], "→", out[-1]["section"])
print("warnings:", warn)
