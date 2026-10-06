"""Merge review-agent outputs ({provision: {"review": {...}, "elements": {...}}}) into constitution/plain.json and
constitution/elements.json. Usage: python3 constitution/merge_review.py [--into ma/constitution] review/con/us/out_*.json
Keys are provision ids ("art1-s8", "amend14-s1"). Entries already present are replaced.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
if "--into" in sys.argv:                          # e.g. ma/constitution for the Massachusetts Constitution
    i = sys.argv.index("--into"); HERE = os.path.join(os.path.dirname(HERE), sys.argv[i + 1]); del sys.argv[i:i + 2]
plain_path, el_path = os.path.join(HERE, "plain.json"), os.path.join(HERE, "elements.json")
plain = json.load(open(plain_path, encoding="utf-8")) if os.path.exists(plain_path) else {}
elements = json.load(open(el_path, encoding="utf-8")) if os.path.exists(el_path) else {}
n = 0
for f in sys.argv[1:]:
    for k, v in json.load(open(f, encoding="utf-8")).items():
        plain[k] = v["review"]
        if v.get("elements"): elements[k] = v["elements"]
        else: elements.pop(k, None)
        n += 1
json.dump(plain, open(plain_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(elements, open(el_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"merged {n} provisions; plain.json has {len(plain)}, elements.json has {len(elements)}")
