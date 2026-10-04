"""How common each Title 18 section is: people sentenced in federal court with at least one conviction under it.

Source: U.S. Sentencing Commission, Individual Datafiles (https://www.ussc.gov/research/datafiles/commission-datafiles).
Each record is one sentenced individual. TTSC{1,2,3}_{n} hold the title + section (no subsection) of every statute of
conviction, e.g. "182252A" = 18 U.S.C. § 2252A; a section is counted once per person however many counts cite it.
Writes frequency.json, which build_data.py merges into crimes.json. Usage: python3 ussc_frequency.py [fiscal year]
"""
import csv, io, json, os, re, sys, urllib.request, zipfile
from collections import Counter

FY = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
HERE = os.path.dirname(os.path.abspath(__file__))
URL = f"https://www.ussc.gov/sites/default/files/zip/opafy{FY % 100:02d}nid_csv.zip"

data = urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"}), timeout=300).read()
zf = zipfile.ZipFile(io.BytesIO(data))
name = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
csv.field_size_limit(10**9)
rows = csv.reader(io.TextIOWrapper(zf.open(name), encoding="latin-1", newline=""))
hdr = next(rows)
cols = [i for i, h in enumerate(hdr) if re.match(r"TTSC[123]_\d+$", h)]
i1028a = hdr.index("IS1028A")

people, flag_1028a, counts = 0, 0, Counter()
for row in rows:
    people += 1
    codes = {row[i].strip().upper() for i in cols if row[i].strip()}
    for sec in {c[2:] for c in codes if c.startswith("18") and len(c) > 2}:
        counts[sec] += 1
    flag_1028a += row[i1028a] == "1"

# Cross-check the parsing against the Commission's own flag for aggravated identity theft (§ 1028A).
assert counts["1028A"] == flag_1028a, f"§1028A parse {counts['1028A']} != IS1028A {flag_1028a}"
json.dump({"source": "U.S. Sentencing Commission, Individual Datafile", "url": URL, "fiscalYear": FY, "people": people,
           "measure": "People sentenced with at least one conviction under the section",
           "counts": dict(counts.most_common())}, open(os.path.join(HERE, "frequency.json"), "w"), indent=0)
print(f"FY{FY}: {people:,} people sentenced; {len(counts)} Title 18 sections cited; §1028A check OK ({flag_1028a})")
