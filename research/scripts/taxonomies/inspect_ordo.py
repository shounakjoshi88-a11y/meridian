"""inspect_ordo.py - structural counts + license block from the downloaded ORDO OWL."""

import re
import sys

p = sys.argv[1]
t = open(p, encoding="utf-8", errors="replace").read()

print("bytes                     :", format(len(t.encode("utf-8")), ","))
print("<Class rdf:about=         :", t.count("<Class rdf:about="))
subs = re.findall(r'<Class rdf:about="http://www\.orpha\.net/ORDO/([^"]+)"', t)
print("distinct ORPHA_ subjects  :", len(set(subs)))
print("DatatypeProperty          :", t.count("<DatatypeProperty"))
print("ObjectProperty            :", t.count("<ObjectProperty"))
print("AnnotationProperty        :", t.count("<AnnotationProperty"))
print("rdfs:subClassOf           :", t.count("<rdfs:subClassOf"))
print("owl:Deprecated true       :", t.count("<owl:Deprecated>true</owl:Deprecated>"))
print("hasDbXref                 :", t.count("hasDbXref"))

print("\n--- ontology header block ---")
i = t.find("<Ontology rdf:about")
print(re.sub(r"\s+", " ", t[i:i + 2200]))

print("\n--- every mention of creativecommons / license ---")
for m in re.finditer(r".{260}creativecommons\.org.{260}", t, re.S):
    print(re.sub(r"\s+", " ", m.group(0)))
    print("-" * 60)

print("\n--- xref namespaces ---")
import collections
c = collections.Counter(re.findall(r'hasDbXref="([^:"]+):', t))
for k, v in c.most_common(15):
    print("  %-16s %d" % (k, v))

print("\n--- HPO / phenotype linkage? ---")
for kw in ["HP:", "HP_", "PATO", "phenotype", "Phenotypic", "Human Phenotype"]:
    print("  %-16s %d" % (kw, t.count(kw)))