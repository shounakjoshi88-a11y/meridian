import re
import ssl
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36"

URL = "https://international.nabh.co/frmViewAccreditedEntryLevelHosp.aspx"
r = urllib.request.urlopen(
    urllib.request.Request(URL, headers={"User-Agent": UA}), timeout=90, context=CTX
)
h = r.read().decode("utf-8", "replace")
print("bytes", len(h))
print("contains 'No Record':", "No Record" in h)

rows = re.findall(r"<tr[^>]*>(.*?)</tr>", h, re.S)
print("table rows:", len(rows))
nag = [x for x in rows if "Nagpur" in x]
print("rows mentioning Nagpur:", len(nag))
for x in rows[:8]:
    cells = [
        re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", c)).strip()
        for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", x, re.S)
    ]
    cells = [c for c in cells if c]
    if cells:
        print("  ROW: " + " ~ ".join(cells)[:200])

pdfs = sorted(set(re.findall(r"(/Documents/[^\"']+?\.pdf)", h)))
print("certificate pdf links:", len(pdfs))
for p in pdfs[:6]:
    print("   https://international.nabh.co" + p)

txt = re.sub(r"<[^>]+>", " ", h)
txt = re.sub(r"\s+", " ", txt)
m = re.search(r"(Accredited Hospitals.{0,400})", txt)
print("\ncontext:", m.group(1)[:400] if m else "n/a")