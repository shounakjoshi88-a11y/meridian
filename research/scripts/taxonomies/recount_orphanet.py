"""recount_orphanet.py - correct-tag counts from the cached en_product1.xml."""

import collections
import re
import sys

p = sys.argv[1]
t = open(p, encoding="utf-8", errors="replace").read()

print("bytes                     :", format(len(t.encode("utf-8")), ","))
dl = re.search(r'<DisorderList count="(\d+)"', t)
print("declared DisorderList count:", dl.group(1) if dl else "n/a")
print("<Disorder id=             :", len(re.findall(r"<Disorder id=\"", t)))
codes = re.findall(r"<OrphaCode>([^<]+)</OrphaCode>", t)
print("OrphaCode occurrences     :", len(codes))
print("distinct OrphaCode        :", len(set(codes)))
groups = [c for c in set(codes) if len(c) < 6]
print("group/header codes (len<6):", len(groups))

types = re.findall(r"<DisorderType id=\"\d+\">\s*<Name lang=\"en\">([^<]+)</Name>", t)
print("DisorderType breakdown    :", dict(collections.Counter(types).most_common()))

grps = re.findall(r"<DisorderGroup id=\"\d+\">\s*<Name lang=\"en\">([^<]+)</Name>", t)
print("DisorderGroup breakdown   :", dict(collections.Counter(grps).most_common()))

print("\n--- external cross-refs carried ---")
srcs = re.findall(r"<Source>([^<]+)</Source>", t)
print("ExternalReference sources :", dict(collections.Counter(srcs).most_common(12)))
print("\n  HPO/symptom strings in file: HP:=%d  phenotype=%d  Symptom=%d"
      % (t.count("HP:"), t.count("phenotype"), t.count("Symptom")))
m = re.search(r"<Licence>.*?</Licence>", t, re.S)
print("\n--- license block in file ---")
print(re.sub(r"\s+", " ", m.group(0)) if m else "none")