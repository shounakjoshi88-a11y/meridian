"""count_icd10cm.py - count real billable ICD-10-CM codes from the CDC order file.

Fixed-width layout observed in the downloaded file (0-based):
    [0:5]   order number
    [5]     space
    [6:14]  code (blank for a category header)
    [14]    '0' = header (not billable), '1' = valid billable code
    [16:61] short description
    [61:]   long description
All counts below are measured from the downloaded bytes.
"""

import collections
import io
import ssl
import sys
import urllib.request
import zipfile

URL = sys.argv[1]
MEMBER_HINT = sys.argv[2] if len(sys.argv) > 2 else "icd10cm-order-"

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=180, context=CTX) as r:
    data = r.read()
    print("GET %s" % URL)
    print("  http         : %s" % r.status)
    print("  content-type : %s" % r.headers.get("Content-Type"))
    print("  content-len  : %s" % format(len(data), ","))
    print("  last-modified: %s" % r.headers.get("Last-Modified"))

z = zipfile.ZipFile(io.BytesIO(data))
name = [n for n in z.namelist() if n.endswith(".txt") and MEMBER_HINT in n][0]
print("  member       : %s (%s bytes)" % (name, format(z.getinfo(name).file_size, ",")))

raw = z.read(name).decode("latin-1")
rows = [l.rstrip("\r\n") for l in raw.split("\n") if l.strip()]

billable = []
headers = []
for line in rows:
    code = line[6:14].strip()
    flag = line[14:15]
    (billable if flag == "1" else headers).append((code, line[16:61].strip(), line[61:].strip()))

print()
print("  total non-empty lines  : %d" % len(rows))
print("  BILLABLE codes (flag=1): %d" % len(billable))
print("  header rows   (flag=0) : %d" % len(headers))

nm = {"A": "Infectious", "B": "Neoplasms", "C": "Circulatory", "D": "Blood/Immune",
      "E": "Endocrine", "F": "Mental", "G": "Nervous", "H": "Eye", "I": "Ear",
      "J": "Respiratory", "K": "Digestive", "L": "Skin", "M": "Musculoskeletal",
      "N": "Genitourinary", "O": "Pregnancy", "P": "Perinatal", "Q": "Congenital",
      "R": "SYMPTOMS/SIGNS/ABNORMAL", "S": "Injury", "T": "Injury", "U": "Special"}

ch = collections.Counter(c[0] for c, _, _ in billable if c)
print("\n  --- billable codes by chapter ---")
for k in sorted(ch):
    print("    %s  %-26s %6d" % (k, nm.get(k, "?"), ch[k]))

r_n = ch.get("R", 0)
print()
print("  >>> Chapter R  symptoms/signs/abnormal findings : %d codes" % r_n)
print("  >>> all other chapters (disease + injury)      : %d codes" % (len(billable) - r_n))
print("\n  sample Chapter R codes: %s" % ", ".join(c for c, _, _ in billable if c.startswith("R"))[:10])