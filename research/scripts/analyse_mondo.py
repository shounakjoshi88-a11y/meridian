"""Does MONDO close the gap between HPOA disease IDs and a real disease KB?

HPOA keys diseases on OMIM: and ORPHA: identifiers. MONDO is the crosswalk
plus a large disease vocabulary in its own right. This measures:
  * MONDO size and how many diseases carry OMIM / Orphanet / MedGen xrefs
  * how many MONDO diseases can inherit >=5 HPO symptoms via those xrefs
  * whether MONDO adds common, non-rare conditions HPOA never covers
  * the licence statement actually written inside mondo.obo

Usage: python analyse_mondo.py
"""

from __future__ import annotations

import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from analyse_hpo import HPOA, OBO, load_obo  # noqa: E402

RAW = os.path.join(os.path.dirname(HERE), "raw")
MONDO = os.path.join(RAW, "mondo.obo")

# ---------- header / licence ----------
print("=== mondo.obo header ===")
with open(MONDO, encoding="utf-8", errors="replace") as fh:
    for i, line in enumerate(fh):
        if i > 40:
            break
        line = line.strip()
        if any(k in line for k in ("data-version", "ontology", "license",
                                   "rights", "remark", "default-namespace",
                                   "date", "format-version", "title")):
            print(f"  {line[:190]}")

# ---------- parse MONDO ----------
print("\n=== parsing mondo.obo ===")
classes: dict[str, dict] = {}
cur = None
in_term = False
with open(MONDO, encoding="utf-8", errors="replace") as fh:
    for line in fh:
        line = line.strip()
        if line == "[Term]":
            if in_term and cur and cur["id"]:
                classes[cur["id"]] = cur
            cur = {"id": "", "name": "", "xrefs": [], "parents": [],
                   "synonyms": [], "obsolete": False}
            in_term = True
            continue
        if line.startswith("[") and line.endswith("]"):
            if in_term and cur and cur["id"]:
                classes[cur["id"]] = cur
            in_term = False
            cur = None
            continue
        if not in_term or not cur:
            continue
        if line.startswith("id: MONDO"):
            cur["id"] = line[4:].strip()
        elif line.startswith("name: "):
            cur["name"] = line[6:].strip()
        elif line.startswith("xref: "):
            # xref values carry a trailing qualifier block, e.g.
            #   xref: OMIM:125853 {source="MONDO:equivalentTo", source="DOID:9352"}
            v = line[6:].strip().split("{")[0].strip().strip('"')
            cur["xrefs"].append(v)
        elif line.startswith("is_a: "):
            cur["parents"].append(line[6:].strip().split("!")[0].strip())
        elif line.startswith("is_obsolete: true"):
            cur["obsolete"] = True
if in_term and cur and cur["id"]:
    classes[cur["id"]] = cur

live = {k: v for k, v in classes.items() if not v["obsolete"]}
print(f"  [Term] stanzas           : {len(classes):,}")
print(f"  obsolete                 : {len(classes) - len(live):,}")
print(f"  live MONDO classes       : {len(live):,}")

ns = collections.Counter(
    "disease" if any(p in ("MONDO:0000001", "MONDO:0000002", "MONDO:0011719")
                     or p.startswith("MONDO:0005") for p in v["parents"])
    else "other"
    for v in live.values()
)
print(f"  rough grouping           : {dict(ns)}")

# ---------- crosswalk ----------
print("\n=== MONDO xref crosswalk (live terms) ===")
omim_x: dict[str, set] = collections.defaultdict(set)
orph_x: dict[str, set] = collections.defaultdict(set)
medgen_x = 0
for mid, d in live.items():
    for x in d["xrefs"]:
        if x.startswith("OMIM:"):
            omim_x[mid].add(x)
        elif x.startswith("Orphanet:"):
            # MONDO writes "Orphanet:123"; HPOA writes "ORPHA:123".
            orph_x[mid].add("ORPHA:" + x.split(":", 1)[1])
        elif x.startswith("MEDGEN:"):
            medgen_x += 1
print(f"  MONDO terms xref OMIM      : {len(omim_x):,}")
print(f"  MONDO terms xref Orphanet  : {len(orph_x):,}")
print(f"  MEDGEN xrefs               : {medgen_x:,}")
print(f"  sample OMIM xrefs          : "
      f"{sorted({x for v in omim_x.values() for x in v})[:5]}")
print(f"  sample Orphanet xrefs      : "
      f"{sorted({x for v in orph_x.values() for x in v})[:5]}")

# ---------- HPOA -> MONDO ----------
print("\n=== HPOA diseases resolved into MONDO ===")
per_dis: dict[str, set] = collections.defaultdict(set)
with open(HPOA, encoding="utf-8", errors="replace") as fh:
    cols = None
    for line in fh:
        if line.startswith("#"):
            continue
        if cols is None:
            cols = line.rstrip("\n").split("\t")
            continue
        f = line.rstrip("\n").split("\t")
        if len(f) < 12 or f[2] == "NOT":
            continue
        per_dis[f[0]].add(f[3])

omim_ids = {k for v in omim_x.values() for k in v}
orph_ids = {k for v in orph_x.values() for k in v}
res_omim = sum(1 for d in per_dis if d in omim_ids)
res_orph = sum(1 for d in per_dis if d in orph_ids)
unres = [d for d in per_dis if d not in omim_ids and d not in orph_ids]
print(f"  HPOA OMIM diseases        : "
      f"{sum(1 for d in per_dis if d.startswith('OMIM:')):,}"
      f"  resolvable in MONDO: {res_omim:,}")
print(f"  HPOA ORPHA diseases       : "
      f"{sum(1 for d in per_dis if d.startswith('ORPHA:')):,}"
      f"  resolvable in MONDO: {res_orph:,}")
print(f"  unresolved                : {len(unres):,} "
      f"(sample {unres[:6]})")

# Reverse index: OMIM:123 -> {MONDO ids}. omim_x above is keyed by MONDO id.
rev: dict[str, set] = collections.defaultdict(set)
for mid, xs in omim_x.items():
    for x in xs:
        rev[x].add(mid)
for mid, xs in orph_x.items():
    for x in xs:
        rev[x].add(mid)

reach = 0
reach5 = 0
seen_mondo = set()
collisions = 0
for did, terms in per_dis.items():
    mids = rev.get(did, set())
    if mids:
        reach += 1
        if len(mids) > 1:
            collisions += 1
        seen_mondo |= mids
        if len(terms) >= 5:
            reach5 += 1
print(f"  HPOA diseases mapped to MONDO       : {reach:,}")
print(f"  ... of those with >=5 HPO symptoms   : {reach5:,}")
print(f"  distinct MONDO ids implied          : {len(seen_mondo):,}")
print(f"  HPOA ids mapping to >1 MONDO id     : {collisions:,}")
print(f"  sample mapping                     : "
      f"{[(k, sorted(v)) for k, v in list(rev.items())[:2]]}")

# ---------- does MONDO add common conditions? ----------
print("\n=== common conditions HPOA never covers, found via MONDO names ===")
probe = ["influenza", "common cold", "cough", "asthma", "gastroenteritis",
         "urinary tract infection", "iron deficiency", "migraine",
         "generalized anxiety", "depressive disorder", "hypertension",
         "coronavirus", "malaria", "dengue", "pneumonia", "tuberculosis",
         "chikungunya", "acute respiratory", "otitis media", "conjunctivitis"]
names = {v["name"].casefold(): k for k, v in live.items()}
hits = 0
for p in probe:
    exact = names.get(p)
    print(f"  {p:<28} exact={'MONDO:'+exact if exact else '-':<18} "
          f"substring_matches="
          f"{sum(1 for n in names if p in n)}")
    hits += bool(exact)
print(f"  exact name hits: {hits}/{len(probe)}")

total_live = len(live)
print(f"\n  MONDO live classes overall      : {total_live:,}")
print(f"  ... vs HPOA diseases             : {len(per_dis):,}")
print(f"  => MONDO is {total_live / len(per_dis):.1f}x the HPOA disease count")