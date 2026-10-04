"""Count what Orphanet product4 ('rare diseases with associated phenotypes')
actually yields.

This is the file behind HPOA's ORPHA rows, but shipped by Orphanet itself
with an explicit CC-BY-4.0 <Licence> block inside the XML.

Usage: python analyse_orphanet_p4.py
"""

from __future__ import annotations

import collections
import os
from xml.etree import ElementTree as ET

RAW = r"D:\Q_project\meridian\research\raw"
P4 = os.path.join(RAW, "en_product4.xml.1")

tree = ET.parse(P4)
root = tree.getroot()

print("=== embedded licence / provenance ===")
print("  JDBOR attrs:", {k: v for k, v in root.attrib.items()})
for lic in root.iter("Licence"):
    for child in lic:
        print(f"  {child.tag:<16} {(child.text or '').strip()}")
status = root.find("HPODisorderSetStatusList")
if status is not None:
    print(f"  HPODisorderSetStatusList @count = {status.get('count')}")

disorders = root.findall(".//Disorder")
print(f"\n  <Disorder> elements      : {len(disorders):,}")

per_dis: dict[str, set] = {}
names: dict[str, str] = {}
freqs = collections.Counter()
for d in disorders:
    code_el = d.find("OrphaCode")
    name_el = d.find("Name")
    if code_el is None:
        continue
    code = code_el.text.strip()
    if name_el is not None and name_el.text:
        names[code] = name_el.text.strip()
    assoc = d.find("HPODisorderAssociationList")
    if assoc is None:
        continue
    terms = set()
    for a in assoc.findall("HPODisorderAssociation"):
        hid = a.findtext("HPO/HPOId")
        if hid:
            terms.add(hid.strip())
        f = a.findtext("HPOFrequency/Name")
        freqs[f or "(none)"] += 1
    if terms:
        per_dis[code] = terms

print(f"  disorders with >=1 HPO term : {len(per_dis):,}")
for n in (3, 5, 10, 20, 50):
    print(f"    with >={n:>2} distinct HPO terms : "
          f"{sum(1 for v in per_dis.values() if len(v) >= n):,}")
allhp = set().union(*per_dis.values()) if per_dis else set()
print(f"  distinct HPO ids used        : {len(allhp):,}")
print(f"  frequency qualifiers         : {freqs.most_common(8)}")

top = sorted(per_dis.items(), key=lambda kv: -len(kv[1]))[:6]
print("\n  most-annotated disorders:")
for c, t in top:
    print(f"    {len(t):>3}  ORPHA:{c}  {names.get(c, '?')[:55]}")

# Plain-English check: how many of the HPOTerm strings are short lay phrases?
terms_all = set()
for d in disorders:
    for a in d.findall(".//HPODisorderAssociation"):
        t = a.findtext("HPO/HPOTerm")
        if t:
            terms_all.add(t.strip())
print(f"\n  distinct HPOTerm strings     : {len(terms_all):,}")
short = sorted(t for t in terms_all if len(t.split()) <= 3)
print(f"  of those, 1-3 words           : {len(short):,}")
print(f"  sample: {', '.join(sorted(short)[:40])}")