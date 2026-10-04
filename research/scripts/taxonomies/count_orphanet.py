"""count_orphanet.py - download Orphadata en_product1.xml (CC BY 4.0) and count
diseases from the actual bytes."""

import collections
import re
import ssl
import sys
import urllib.request

URL = sys.argv[1]
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=600, context=CTX) as r:
    raw = r.read()
    print("GET %s" % URL)
    print("  http         : %s" % r.status)
    print("  content-type : %s" % r.headers.get("Content-Type"))
    print("  content-len  : %s bytes" % format(len(raw), ","))
    print("  last-modified: %s" % r.headers.get("Last-Modified"))

txt = raw.decode("utf-8", errors="replace")
print("\n--- measured from en_product1.xml ---")
print("bytes                       : %s" % format(len(raw), ","))
print("<DisorderList>              : %d" % txt.count("<DisorderList>"))
codes = re.findall(r'<DisorderDisorderStatusCode>([^<]*)</DisorderDisorderStatusCode>', txt)
print("DisorderStatusCode values   : %s" % dict(collections.Counter(codes).most_common()))
orphacodes = re.findall(r"<OrphanetCode>([^<]+)</OrphanetCode>", txt)
print("OrphanetCode occurrences    : %d" % len(orphacodes))
print("distinct OrphanetCode       : %d" % len(set(orphacodes)))
groups = re.findall(r"<OrphanetCode>(ORPHA:(\d+))</OrphanetCode>", txt)
print("groups (ORPHA:1xxxx / 2xxxx): %d" % len(set(g[0] for g in groups)))

print("\n--- phenotype link present in this file? ---")
for kw in ["HPO", "HP:", "phenotype", "Phenotype", "Sign", "Symptom"]:
    print("  %-12s %d" % (kw, txt.count(kw)))

print("\n--- head of file (license / provenance) ---")
print(txt[:1500])