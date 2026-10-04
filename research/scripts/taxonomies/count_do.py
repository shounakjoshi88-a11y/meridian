"""count_do.py - download Disease Ontology doid.obo and measure class count,
license statement, and symptom/phenotype axis presence from the actual bytes."""

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
with urllib.request.urlopen(req, timeout=180, context=CTX) as r:
    raw = r.read()
    print("GET %s" % URL)
    print("  http         : %s" % r.status)
    print("  content-type : %s" % r.headers.get("Content-Type"))
    print("  content-len  : %s" % format(len(raw), ","))
    print("  last-modified: %s" % r.headers.get("Last-Modified"))
    print("  final-url    : %s" % r.geturl())

txt = raw.decode("utf-8", errors="replace")
print("\n--- measured from doid.obo ---")
print("total [Term] stanzas      : %d" % txt.count("\n[Term]\n"))
print("distinct DOID ids (id:)   : %d" % len(set(re.findall(r"^id: (DOID:\d+)", txt, re.M))))
print("obsolete:true stanzas     : %d" % txt.count("is_obsolete: true"))
print("alt_ids (merged/secondary): %d" % txt.count("alt_id:"))

print("\n--- license / provenance lines present in the file ---")
for line in txt.split("\n")[:40]:
    if any(k in line.lower() for k in ("license", "remark", "date", "format-version", "ontology")):
        print("  | %s" % line)

# DO asserted hierarchy root count
print("\n--- hierarchy ---")
print("is_a stanzas              : %d" % txt.count("is_a:"))
print("relationship: is_a        : %d" % txt.count("relationship: is_a"))

# Symptom axis in DO: look for the phenotypic abnormality / symptom branches
print("\n--- does DO carry SYMPTOM / PHENOTYPE annotations? ---")
for probe in ["DOID:0111", "symptom", "Symptom", "phenotype", "Phenotype",
              "clinical presentation", "Signs and Symptoms",
              "disease manifestation"]:
    print("  %-28s occurrences: %d" % (probe, txt.count(probe)))

names = re.findall(r"^name: (.+)$", txt, re.M)
print("\ntotal names               : %d" % len(names))
sym = [n for n in names if "symptom" in n.lower() or "sign" in n.lower()]
print("names containing symptom/sign: %d" % len(sym))
print("examples: %s" % "; ".join(sym[:10]))

ph = [n for n in names if "phenotyp" in n.lower()]
print("names containing phenotype: %d  -> %s" % (len(ph), "; ".join(ph[:8])))