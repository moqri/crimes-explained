"""Merge review-agent outputs ({section: {"review": {...}, "elements": {...}}}) into ca/plain.json and ca/elements.json.
Usage: python3 ca/merge_review.py review/ca/out_*.json
Section keys are the Penal Code section numbers ("187", "243.4"). Entries already present are replaced.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
# Decisions made after review (see HANDOFF.md): sections a reviewer marked as crimes that are not.
NOT_CRIMES = {}

plain_path, el_path = os.path.join(HERE, "plain.json"), os.path.join(HERE, "elements.json")
plain = json.load(open(plain_path, encoding="utf-8")) if os.path.exists(plain_path) else {}
elements = json.load(open(el_path, encoding="utf-8")) if os.path.exists(el_path) else {}
n = 0
for f in sys.argv[1:]:
    for k, v in json.load(open(f, encoding="utf-8")).items():
        key = k
        review = v["review"]
        if key in NOT_CRIMES:
            review = {"isOffense": False, "plain": NOT_CRIMES[key]}
        plain[key] = review
        if review.get("isOffense") and v.get("elements"): elements[key] = v["elements"]
        else: elements.pop(key, None)
        n += 1
json.dump(plain, open(plain_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(elements, open(el_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"merged {n} sections; plain.json has {len(plain)}, elements.json has {len(elements)}")
