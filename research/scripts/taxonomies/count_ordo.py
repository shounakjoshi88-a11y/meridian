"""count_ordo.py - download ORDO (CC BY 4.0) and measure class count, license
statement, disease vs phenotype/symptom coverage from the actual bytes."""

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
with urllib.request.urlopen(req, timeout=300, context=CTX) as r:
    raw = r.read()
    print("GET %s" % URL)
    print("  http         : %s" % r.status)
    print("  content-type : %s" % r.headers.get("Content-Type"))
    print("  content-len  : %s" % format(len(raw), ","))
    print("  last-modified: %s" % r.headers.get("Last-Modified"))
    print("  final-url    : %s" % r.geturl())

txt = raw.decode("utf-8", errors="replace")

print("\n--- measured from ORDO OWL ---")
print("bytes                    : %s" % format(len(raw), ","))
print("owl:Class rdf:about count : %d" % txt.count('<owl:Class rdf:about='))
print("distinct ORPHA_ ids       : %d" % len(set(re.findall(r"http://www.orpha\.net/ORDO/(\w+)", txt))))
print("deprecated (owl:Deprecated): %d" % txt.count("<owl:Deprecated>true</owl:Deprecated>"))
print("subClassOf declarations   : %d" % txt.count("<rdfs:subClassOf"))
print("hasDbXref                 : %d" % txt.count("hasDbXref"))

print("\n--- license / rights in the file ---")
for m in re.finditer(r"<owl:AnnotationProperty[^>]*>(.{0,400}?)</owl:AnnotationProperty>", txt, re.S):
    if "license" in m.group(0).lower() or "rights" in m.group(0).lower():
        print("  AnnotationProperty snippet: %s" % re.sub(r"\s+", " ", m.group(0))[:300])
for kw in ["creativecommons.org", "CC BY", "Attribution 4.0", "license"]:
    print("  %-22s occurrences: %d" % (kw, txt.count(kw)))

print("\n--- disease vs phenotype/symptom ---")
names = re.findall(r"<rdfs:label>([^<]+)</rdfs:label>", txt)
print("rdfs:label count          : %d" % len(names))
sig = [n for n in names if re.search(r"sign|symptom|phenotyp", n, re.I)]
print("labels w/ sign|symptom|phenotyp: %d" % len(sig))
print("examples: %s" % "; ".join(sig[:8]))

for kw in ["HP:", "Phenotype", "phenotype", "HOOM", "OMIM", "Orphanet:"]:
    print("  %-14s occurrences: %d" % (kw, txt.count(kw)))

print("\n--- xref namespaces ---")
c = collections.Counter(re.findall(r'hasDbXref="([^:"]+):', txt))
for k, v in c.most_common(15):
    print("  %-16s %d" % (k, v))