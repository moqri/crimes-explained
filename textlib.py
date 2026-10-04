"""Text helpers shared by build_data.py (U.S. Code) and ma/build_ma.py (Massachusetts General Laws):
outline levels, prohibited-act ranges, and the own-section-only filter for crime breakdowns."""
import re

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

def para_paths(text):
    path, out = [], []
    for p in text:
        m = LEAD_CHAIN.match(p["t"])
        if m:
            del path[p["i"]:]
            path += [""] * (p["i"] - len(path))
            path.append(m.group(0))
            out.append("".join(path))
        else:
            out.append(None)
    return out

def stem(w):
    w = w.lower()
    for suf in ("ies", "es", "s", "ed", "ing"):
        if w.endswith(suf) and len(w) - len(suf) >= 3: return w[: -len(suf)]
    return w

def fill_act_gaps(c):
    added, paths = 0, para_paths(c["text"])
    for cr in c["elements"]["crimes"]:
        m = re.match(r"^(?:\([A-Za-z0-9]+\))+", (cr.get("where") or "").replace(" ", ""))
        if not m: continue
        w = m.group(0)
        cand = [i for i, pp in enumerate(paths) if pp and (pp.startswith(w) or w.startswith(pp))]
        if not cand or any(c["text"][i].get("a") for i in cand): continue
        # unlabeled closing lines after the subsection ("…to ship or transport in interstate commerce…") belong to it too
        top = cand[-1]
        while top + 1 < len(paths) and paths[top + 1] is None: top += 1; cand.append(top)
        all_words = re.findall(r"[A-Za-z]+", cr["act"])[:5]
        if not all_words: continue
        order = sorted(cand, key=lambda i: (not (paths[i] or "").startswith(w), i))   # the crime's own paragraph first
        hit = None
        for k in range(len(all_words), 0, -1):          # 5 leading words, then fewer; one word only if unique
            rx = re.compile(r"(?i)\b" + r"\W+".join(re.escape(stem(x)) + r"\w*" for x in all_words[:k]) + r"\b")
            for i in order:
                found = list(rx.finditer(c["text"][i]["t"]))
                if found and (k > 1 or len(found) == 1): hit = (i, found[0]); break
            if hit: break
        if hit:
            i, mm = hit
            t = c["text"][i]["t"]
            end = mm.end()
            stop = re.search(r"[,;(—]", t[end:])
            end = min(len(t), end + (stop.start() if stop else len(t) - end), mm.start() + 240)
            while end > mm.start() and t[end - 1] in " ,;": end -= 1
            c["text"][i].setdefault("a", []).append([mm.start(), end]); added += 1
    return added

CITES_OTHER = re.compile(r"§\s*(\d+[A-Za-z]*(?:-\d+)?)")
OWN_ONLY = ["federalBasis", "knowledge", "mentalState", "intent", "consequences", "terms", "conditions", "exceptions", "defenses"]

def own_text_only(sec, el):
    """A section's crime list uses only that section's own text. Items the breakdown borrowed from another section
    (e.g. §922's "Willfully (§924(a)(1)(D))") are dropped, and penalty tiers copied from another section collapse
    into one pointer to it ("Set in §924(a)(2)"). Returns how many items and tiers were removed."""
    other = lambda v: any(m.upper() != sec.upper() for m in CITES_OTHER.findall(v))
    removed = 0
    for b in [el["shared"]] + el["crimes"]:
        for k in OWN_ONLY:
            if b.get(k):
                keep = [v for v in b[k] if not other(v)]
                removed += len(b[k]) - len(keep); b[k] = keep
        tiers = b.get("penalties") or []
        borrowed = [t for t in tiers if t.get("source") and other(t["source"])]
        if borrowed:
            srcs = list(dict.fromkeys(t["source"] for t in borrowed))
            own = [t for t in tiers if t not in borrowed]
            where = re.sub(r"§\s*", "section ", re.sub(r"§§\s*", "sections ", "; ".join(srcs)))
            b["penalties"] = own + [{"if": "", "penalty": "Set in " + where, "min": None, "max": None, "flags": []}]
            removed += len(borrowed)
    return removed

PURPOSE_BEFORE_TO = re.compile(r"(?i)\b(?:intent|intending|order|purpose|design|view|attempts?|attempting|conspires?|conspiring|endeavors?)\s+to\s+$")

def tidy_acts(c):
    """Every act highlight: start at a preceding infinitive "to" (unless it is "intent to", "in order to", …),
    end without trailing punctuation, and drop highlights that are only punctuation; then merge overlaps."""
    changed = 0
    for p in c["text"]:
        if "a" not in p: continue
        t, out = p["t"], []
        for s, e in p["a"]:
            s0, e0 = s, e
            while s < e and t[s] in " ,;.:—": s += 1
            while e > s and t[e - 1] in " ,;.:—": e -= 1
            before = t[max(0, s - 40):s]
            if re.search(r"(?i)\bto\s+$", before) and not PURPOSE_BEFORE_TO.search(before):
                s = s - len(re.search(r"(?i)to\s+$", before).group(0))
            if e - s < 2 or not re.search(r"[A-Za-z]", t[s:e]): changed += 1; continue
            changed += (s, e) != (s0, e0)
            out.append([s, e])
        merged = []
        for s, e in sorted(out):
            if merged and s <= merged[-1][1] + 1: merged[-1][1] = max(merged[-1][1], e)
            else: merged.append([s, e])
        p["a"] = merged
    return changed

def apply_acts(c):
    """Prohibited-act phrases ("acts") become character ranges on the paragraph that contains them: p["a"] = [[start, end], …].
    Returns how many phrases were not found in the text."""
    unmatched = 0
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
    return unmatched
