"""Download the Constitution of the United States from GovInfo (House Document 110-50, "The Constitution of the United
States of America, As Amended", the official GPO print) into constitution/raw/us.htm.
Usage: python3 constitution/fetch_con.py
"""
import os, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
URL = "https://www.govinfo.gov/content/pkg/CDOC-110hdoc50/html/CDOC-110hdoc50.htm"
os.makedirs(os.path.join(HERE, "raw"), exist_ok=True)
data = urllib.request.urlopen(URL, timeout=120).read()
open(os.path.join(HERE, "raw", "us.htm"), "wb").write(data)
print(f"saved {len(data):,} bytes to constitution/raw/us.htm")
