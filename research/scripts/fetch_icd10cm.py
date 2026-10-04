"""Fetch and inspect the ICD-10-CM code descriptions.

This is the real-code spine for the disease registry: US Government work,
public domain, and unlike HPOA it is a classification of the diseases a
clinic actually treats.
"""
import io
import os
import urllib.request
import zipfile

URL = ("https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Publications/"
       "ICD10CM/2027/icd10cm-code-descriptions-2027.zip")
OUT = os.path.join("research", "raw", "icd10cm_order_2027.txt")

req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=120) as response:
    data = response.read()
print(f"status {response.status}  {len(data):,} bytes")

archive = zipfile.ZipFile(io.BytesIO(data))
member = next(n for n in archive.namelist()
              if n.endswith("order-2027.txt") or n.endswith("order_2027.txt")
              or ("order" in n and n.endswith(".txt")))
print("member:", member)

text = archive.read(member).decode("utf-8", "replace")
with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(text)

lines = [line for line in text.splitlines() if line.strip()]
print(f"lines: {len(lines):,}")
print(f"first: {lines[0][:100]}")
print(f"last : {lines[-1][:100]}")

# The order file is whitespace aligned, not tab separated:
#   <line no> <code> <0|1 header-or-billable> <description> ...
def parse(line):
    parts = line.split(None, 3)
    if len(parts) < 4:
        return None
    return parts[0], parts[1], parts[2], parts[3].strip()


records = [r for r in (parse(l) for l in lines) if r]
print(f"parsed: {len(records):,}")
for rec in records[:3]:
    print("  ", rec[0], rec[1], rec[2], rec[3][:60])

billable = [r for r in records if r[2] == "1"]
print(f"billable codes: {len(billable):,}")

print()
print("=== chapter R, the symptom vocabulary ===")
chapter_r = [r for r in records if r[1].startswith("R")]
print(f"R-prefixed rows: {len(chapter_r):,}")
for rec in chapter_r[:6]:
    print(f"   {rec[1]:<8} {rec[3][:62]}")

print()
print("=== codes a triage tool actually needs ===")
for probe in ("E11", "I10", "J45", "J06", "A15", "E78", "M54", "K21",
              "F32", "N39", "J18", "E78"):
    hit = next((r for r in records if r[1].startswith(probe)), None)
    print(f"  {probe:<5} {hit[1] + '  ' + hit[3][:60] if hit else 'not found'}")