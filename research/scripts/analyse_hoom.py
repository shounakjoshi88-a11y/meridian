"""Count the real disease -> HPO yield of Orphanet's HOOM module.

HOOM (HPO-ORDO Ontological Module) is Orphanet's own disease -> HPO mapping,
distributed under CC BY 4.0. Each assertion is reified as its own owl:Class
whose IRI encodes the triple, e.g. "#Orpha:2632_HP:0000218_Freq:VF".

Usage: python analyse_hoom.py
"""

from __future__ import annotations

import collections
import os
import re
import zipfile
from xml.etree import ElementTree as ET

RAW = r"D:\Q_project\meridian\research\raw"
ZIP = os.path.join(RAW, "hoom_orphanet_2.5..zip")
RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
OWL = "{http://www.w3.org/2002/07/owl#}"

with zipfile.ZipFile(ZIP) as z:
    name = max(z.namelist(), key=lambda n: z.getinfo(n).file_size)
    data = z.read(name)
print(f"parsing {name} ({len(data):,} bytes)")
root = ET.fromstring(data)

classes = list(root.iter(f"{OWL}Class"))
print(f"owl:Class stanzas: {len(classes):,}")


def iri_of(c):
    """OWL/XML uses rdf:about for named nodes and a bare IRI attribute for
    anonymous ones. HOOM's reified assertions use the bare IRI attribute."""
    return c.get(f"{RDF}about") or c.get("IRI") or ""


# IRI shapes present
shapes = collections.Counter()
for c in classes[:200000]:
    shapes[re.sub(r"\d+", "N", iri_of(c))] += 1
print("\nIRI shapes (sampled 200k):")
for k, v in shapes.most_common(12):
    print(f"  {v:>7}  {k}")


ORPHA_RE = re.compile(r"Orpha:(\d+)_HP:(\d{7})(?:_Freq:(\S+?))?(?:_NC:(\S+?))?$")


per_dis: dict[str, set] = collections.defaultdict(set)
freqs = collections.Counter()
unmatched = 0
for c in classes:
    iri = iri_of(c)
    m = ORPHA_RE.search(iri)
    if not m:
        if "HP:" in iri:
            unmatched += 1
        continue
    orpha, hp, freq = m.group(1), "HP:" + m.group(2), m.group(3)
    per_dis[orpha].add(hp)
    freqs[freq or "(none)"] += 1

print(f"\nassertions carrying ORPHA+HP in the IRI : "
      f"{sum(len(v) for v in per_dis.values()):,}")
print(f"HP-containing IRIs the regex did NOT match: {unmatched:,}")
print(f"frequency qualifiers: {freqs.most_common(10)}")
print(f"\ndistinct ORPHA diseases with >=1 HPO term : {len(per_dis):,}")
for n in (3, 5, 10, 20, 50):
    print(f"  with >={n:>2} distinct HPO terms : "
          f"{sum(1 for v in per_dis.values() if len(v) >= n):,}")
allhp = set().union(*per_dis.values()) if per_dis else set()
print(f"  distinct HPO terms used : {len(allhp):,}")

# Do the asserted classes carry rdfs:label with the English HPO name?
sample = None
for c in classes:
    iri = c.get(f"{RDF}about") or ""
    if ORPHA_RE.search(iri):
        for sub in c.iter():
            if sub.text and sub.text.strip():
                sample = (iri, sub.tag, sub.text.strip())
                break
    if sample:
        break
print("\nfirst text found inside an assertion class:", sample)