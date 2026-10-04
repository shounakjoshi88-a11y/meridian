"""Verify every HP ID asserted in the notes' synonym table.

The label -> synonym mapping was observed, but the IDs were filled in from
memory. This resolves each label in hp.obo and prints the authoritative ID so
the notes can be corrected rather than trusted.

Usage: python verify_synonym_ids.py
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from analyse_hpo import OBO, load_obo  # noqa: E402

# label -> the HP ID the notes currently claim
CLAIMED = {
    "Rhinorrhea": "HP:0002231",
    "Pharyngalgia": "HP:0000205",
    "Pollakisuria": "HP:0000021",
    "Skin rash": "HP:0000988",
    "Arthralgia": "HP:0001367",
    "Gingival bleeding": "HP:0000176",
    "Hyperhidrosis": "HP:0000966",
    "Myalgia": "HP:0003324",
    "Vertigo": "HP:0002321",
    "Dyspnea": "HP:0002094",
    "Arrhythmia": "HP:0001645",
    "Increased body weight": "HP:0004324",
    "Alopecia": "HP:0001596",
    "Diarrhea": "HP:0002014",
    "Anosmia": "HP:0000458",
    "Pain": "HP:0012531",
    "Ageusia": "HP:0041051",
}

terms = load_obo(OBO)
by_name: dict[str, str] = {}
for tid, d in terms.items():
    if not d["obsolete"]:
        by_name.setdefault(d["name"].casefold(), tid)

# reverse: label -> the lay synonym the notes claim maps to it
REVERSE = {
    "runny nose": "Rhinorrhea",
    "sore throat": "Pharyngalgia",
    "frequent urination": "Pollakisuria",
    "rash": "Skin rash",
    "joint pain": "Arthralgia",
    "bleeding gums": "Gingival bleeding",
    "sweating": "Hyperhidrosis",
    "muscle pain": "Myalgia",
    "dizziness": "Vertigo",
    "shortness of breath": "Dyspnea",
    "irregular heartbeat": "Arrhythmia",
    "weight gain": "Increased body weight",
    "hair loss": "Alopecia",
    "diarrhoea": "Diarrhea",
    "loss of smell": "Anosmia",
}

print("=== HP IDs asserted in the notes ===")
wrong = 0
for label, claimed in CLAIMED.items():
    actual = by_name.get(label.casefold())
    ok = actual == claimed
    if not ok:
        wrong += 1
    lay = [s for s, sc in terms.get(actual, {}).get("synonyms", [])
           if sc == "layperson"][:2] if actual else []
    print(f"  {'OK ' if ok else 'BAD'}  {label:<24} claimed={claimed:<12} "
          f"actual={actual or 'NOT FOUND':<12} lay={lay}")
print(f"\n  {wrong} of {len(CLAIMED)} claimed HP IDs are wrong\n")

print("=== seed symptom -> actual HPO label, via synonyms ===")
syn_index: dict[str, list[str]] = {}
for tid, d in terms.items():
    if d["obsolete"]:
        continue
    for s, _sc in d["synonyms"]:
        syn_index.setdefault(s.casefold(), []).append(d["name"])

for seed in sorted(REVERSE):
    tid = by_name.get(REVERSE[seed].casefold())
    hits = syn_index.get(seed, [])
    mark = "OK " if REVERSE[seed] in hits else "?? "
    print(f"  {mark}'{seed}' -> {REVERSE[seed]} ({tid}) "
          f"verified-as-synonym={REVERSE[seed] in hits}")
    if not hits:
        print(f"        no HPO synonym equals '{seed}'")