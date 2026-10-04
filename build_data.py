import re, json, html, urllib.request
SRC = "https://www.govinfo.gov/content/pkg/USCODE-2024-title18/html/USCODE-2024-title18-partI.htm"
doc = urllib.request.urlopen(urllib.request.Request(SRC, headers={"User-Agent": "Mozilla/5.0"})).read().decode("utf-8")
LIMIT = None  # set to a number to keep only the first N sections
# Pre-filter only the obvious: repealed/transferred entries ("[§ 14. Repealed…]") and pure definition sections.
# Whether a section actually defines a crime is decided per section in plain.json ("isOffense").
SKIP = re.compile(r"^(\[|Definitions?( for (certain provisions|chapter)\b.*)?$|.* defined$|Definitions? (for|relating to) )")

from textlib import *   # outline levels, act ranges, and other text helpers shared with the Massachusetts build

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
    unmatched = sum(apply_acts(c) for c in out)
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
        print(sum(own_text_only(c["section"], c["elements"]) for c in out if c.get("elements")),
              "breakdown items or penalty tiers taken from other sections removed")
    freq_path = os.path.join(here, "frequency.json")  # how often each section is used: people sentenced (USSC)
    if os.path.exists(freq_path):
        freq = json.load(open(freq_path))
        by_upper = {k.upper(): v for k, v in freq["counts"].items()}
        for c in out: c["sentenced"] = by_upper.get(c["section"].upper(), 0)
    # Fill act highlights the phrase pass missed (e.g. §922(a)(3) "to transport into or receive"), using each crime's
    # act from the breakdown: match its first words by stem in that crime's subsection (or its lead-in) and highlight
    # to the end of the clause.
    filled = 0
    for c in out:
        if c.get("elements"): filled += fill_act_gaps(c)
    print(filled, "act highlights added from the crime breakdowns")
    fixed = sum(tidy_acts(c) for c in out)
    print(fixed, "act highlights tidied (leading \"to\", trailing punctuation)")
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

freq_meta = {k: v for k, v in json.load(open(os.path.join(here, "frequency.json"))).items() if k != "counts"} if os.path.exists(os.path.join(here, "frequency.json")) else None
json.dump({"frequency": freq_meta, "partISections": part1, "statLinks": stat_links, "actSections": act_sections, "edition": "United States Code, 2024 Edition (current through Jan. 6, 2025)", "source": SRC, "crimes": out},
          open(os.path.join(here, "crimes.json"), "w"), ensure_ascii=False, indent=1)
print(len(out), "sections;", out[0]["section"], "→", out[-1]["section"])
print("warnings:", warn)
