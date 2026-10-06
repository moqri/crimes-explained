"""Related crimes: for every section, up to 3 similar sections in the same jurisdiction and, from each other jurisdiction,
its single most similar section (when one is similar enough; a jurisdiction with no good match is left out).

Similarity is TF-IDF cosine over each section's title, plain-English summary, category and crimes' acts (no outside data,
no AI at build time). Writes related.json: {"us:922": {"same": [["us", "924"], ...], "other": [["ma", "265/15A"], ...]}}.
build_pages.py reads it. Run after build_data.py / ma/build_ma.py / ca/build_ca.py / ny/build_ny.py, before build_pages.py.
Usage: python3 related.py [--show us:922 ma:265/1 ...]   (--show prints the matches for those sections)
"""
import json, math, os, re, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = {"us": "crimes.json", "ma": "ma/crimes.json", "ca": "ca/crimes.json", "ny": "ny/crimes.json"}
NAMES = {"us": "Federal", "ma": "Massachusetts", "ca": "California", "ny": "New York"}
ORDER = ["us", "ma", "ny", "ca"]   # the order of the switch at the top of the site
SAME_MIN, OTHER_MIN, CATEGORY_BOOST, TITLE_WEIGHT = 0.32, 0.38, 0.05, 0.5
OTHER_ANY_TYPE = 0.55   # a match in another jurisdiction must share the crime type unless it scores at least this

STOP = set("""a an and or the of to in on at by for with from as is are was be been being it its this that these those any all
such than then there their his her he she they them who whom whoever whose which what when where while if unless not no nor
shall may must can will would should upon into out over under between through after before during without within other another
person persons one two three more less not other offense offenses crime crimes unlawful guilty section subsection chapter title
degree first second third fourth fifth sixth law laws code act acts commits commit committed commission another another covers cover also including include includes
""".split())
KEEP_SHORT = {"dui", "rape", "arson", "theft", "gun", "drug", "sex", "bomb"}

def stem(w):
    for suf in ("ations", "ation", "ings", "ing", "ies", "ied", "es", "ed", "ly", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[: -len(suf)] + ("y" if suf in ("ies", "ied") else "")
    return w

def tokens(text):
    out = []
    for w in re.findall(r"[a-z]+", text.lower()):
        if w in STOP or (len(w) < 3 and w not in KEEP_SHORT): continue
        out.append(stem(w))
    return out

def doc(c):
    acts = " ".join(cr.get("act", "") for cr in (c.get("elements") or {}).get("crimes", []))
    # the title counts three times and the summary twice, so the subject of the crime dominates
    return tokens(c["title"]) * 3 + tokens(c.get("plain", "")) * 2 + tokens(acts) + tokens(c.get("category", "")) * 1

titles = []
items = []   # (jurisdiction, section, category, term counts)
for jur, f in SOURCES.items():
    path = os.path.join(HERE, f)
    if not os.path.exists(path): continue
    for c in json.load(open(path, encoding="utf-8"))["crimes"]:
        items.append((jur, c["section"], c.get("category"), Counter(doc(c)), c["title"]))
        titles.append(Counter(tokens(c["title"])))

df = Counter(t for it in items for t in it[3])
N = len(items)
idf = {t: math.log((1 + N) / (1 + n)) + 1 for t, n in df.items()}
vecs = []
for it in items:
    v = {t: (1 + math.log(n)) * idf[t] for t, n in it[3].items()}
    norm = math.sqrt(sum(x * x for x in v.values())) or 1
    vecs.append({t: x / norm for t, x in v.items()})

tvecs = []
for t in titles:   # title-only vectors: sharing the subject word in the title ("murder", "kidnapping") is the strongest sign
    v = {w: (1 + math.log(n)) * idf.get(w, 1) for w, n in t.items()}
    norm = math.sqrt(sum(x * x for x in v.values())) or 1
    tvecs.append({w: x / norm for w, x in v.items()})

def cos(a, b):
    if len(a) > len(b): a, b = b, a
    return sum(x * b.get(t, 0) for t, x in a.items())

related, scores = {}, {}
for i, (jur, sec, cat, _, _) in enumerate(items):
    same, best_other = [], {}
    for k, (j2, s2, cat2, _, _) in enumerate(items):
        if k == i: continue
        score = cos(vecs[i], vecs[k]) + TITLE_WEIGHT * cos(tvecs[i], tvecs[k]) + (CATEGORY_BOOST if cat and cat == cat2 else 0)
        if j2 == jur:
            if score >= SAME_MIN: same.append((score, s2))
        elif score >= OTHER_MIN and (cat == cat2 or score >= OTHER_ANY_TYPE):
            if score > best_other.get(j2, (0, None))[0]: best_other[j2] = (score, s2)
    same = sorted(same, reverse=True)[:3]
    # other jurisdictions: the single best match from each, in the site's order (Federal, Massachusetts, New York, California)
    chosen = [(best_other[j2][0], j2, best_other[j2][1]) for j2 in ORDER if j2 in best_other]
    related[f"{jur}:{sec}"] = {"same": [[jur, s] for _, s in same], "other": [[j2, s2] for _, j2, s2 in chosen]}
    scores[f"{jur}:{sec}"] = ([round(sc, 2) for sc, _ in same], [round(sc, 2) for sc, _, _ in chosen])

json.dump(related, open(os.path.join(HERE, "related.json"), "w"), indent=0)
n_same = sum(1 for v in related.values() if v["same"]); n_other = sum(1 for v in related.values() if v["other"])
print(f"{len(related)} sections; {n_same} have same-jurisdiction matches, {n_other} have other-jurisdiction matches; "
      f"avg {sum(len(v['same']) for v in related.values())/len(related):.2f} same, {sum(len(v['other']) for v in related.values())/len(related):.2f} other")
if "--show" in sys.argv:
    title = {f"{j}:{s}": t for j, s, _, _, t in items}
    for key in sys.argv[sys.argv.index("--show") + 1:]:
        print(f"\n{key}  {title.get(key)}")
        for grp in ("same", "other"):
            for n, (j, s) in enumerate(related[key][grp]): print(f"   {grp:5} {scores[key][0 if grp == 'same' else 1][n]:.2f} {NAMES[j]:13} {s:10} {title[f'{j}:{s}']}")
