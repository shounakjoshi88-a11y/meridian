"""Verify HPO + HPOA counts from the downloaded files.

Answers, with counts computed rather than remembered:
  * hp.obo total terms, phenotypic-abnormality subset, namespaces, obsolete
  * phenotype.hpoa rows, distinct diseases, distinct HPO terms
  * how many diseases have >= N distinct phenotypic-abnormality terms
    after rolling child terms up to their nearest ancestor

Usage: python analyse_hpo.py
"""

from __future__ import annotations

import collections
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(os.path.dirname(HERE), "raw")
OBO = os.path.join(RAW, "hp.obo")
HPOA = os.path.join(RAW, "phenotype.hpoa")


def load_obo(path):
    """Parse an OBO-format file.

    hp.obo contains only [Term] stanzas and no [Typedef] section, so the
    previous term must be flushed when a new [Term] opens rather than when a
    section header closes.
    """
    terms = {}
    cur = None
    in_term = False
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if line == "[Term]":
                if in_term and cur and cur["id"]:
                    terms[cur["id"]] = cur
                cur = {"id": "", "name": "", "namespace": "", "synonyms": [],
                       "parents": [], "obsolete": False, "xrefs": []}
                in_term = True
                continue
            if line.startswith("[") and line.endswith("]"):
                if in_term and cur and cur["id"]:
                    terms[cur["id"]] = cur
                in_term = False
                cur = None
                continue
            if not in_term or not cur:
                continue
            if line.startswith("id: "):
                cur["id"] = line[4:].strip()
            elif line.startswith("name: "):
                cur["name"] = line[6:].strip()
            elif line.startswith("namespace: "):
                cur["namespace"] = line[11:].strip()
            elif line.startswith("xref: "):
                cur["xrefs"].append(line[6:].strip())
            elif line.startswith("synonym: "):
                m = re.match(r'synonym: "([^"]+)" (EXACT|NARROW|BROAD|RELATED)\s+(\S+)', line)
                if m:
                    cur["synonyms"].append((m.group(1), m.group(3)))
            elif line.startswith("is_obsolete: true"):
                cur["obsolete"] = True
            elif line.startswith("is_a: "):
                cur["parents"].append(line[6:].strip().split("!")[0].strip())
    if in_term and cur and cur["id"]:
        terms[cur["id"]] = cur
    return terms


def header_meta(path):
    """OBO headers use bare 'key: value'; HPOA headers use '#key: value'."""
    meta = {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            if not line.startswith("#") and ":" not in line:
                break
            k, _, v = line.lstrip("#").partition(":")
            meta[k.strip()] = v.strip().strip('"')
    return meta


def main() -> None:
    meta = header_meta(OBO)
    print("=== hp.obo header ===")
    for k, v in meta.items():
        print(f"  {k}: {v[:200]}")

    terms = load_obo(OBO)
    live = {t: d for t, d in terms.items() if not d["obsolete"]}
    ns = collections.Counter(d["namespace"] for d in live.values())
    print("\n=== hp.obo term counts ===")
    print(f"  total [Term] stanzas          : {len(terms)}")
    print(f"  obsolete (excluded)          : {len(terms) - len(live)}")
    print(f"  live terms                   : {len(live)}")
    print("\n  namespaces (live):")
    for k, v in ns.most_common():
        print(f"    {v:>6}  {k or '(no namespace: line in hp.obo)'}")
    print(f"  terms whose name contains 'Phenotypic abnormality' substring: "
          f"{sum(1 for d in live.values() if 'Phenotypic abnormality' in d['name'])}")

    abn = "HP:0000118"
    direct = [t for t, d in live.items() if abn in d["parents"]]
    print(f"\n  direct children of {abn} (Phenotypic abnormality): {len(direct)}")
    print(f"  all live terms carrying 'Phenotypic abnormality' in xref: "
          f"{sum(1 for d in live.values() if abn in d['xrefs'])}")

    # Build ancestor closure over is_a so we can roll a child term up to the
    # nearest ancestor that sits directly under phenotypic_abnormality.
    memo: dict[str, bool] = {}

    def under_abn(tid, stack=()):
        if tid in memo:
            return memo[tid]
        if tid in stack:
            return False
        d = terms.get(tid)
        if not d or d["obsolete"]:
            memo[tid] = False
            return False
        if abn in d["parents"]:
            memo[tid] = True
            return True
        res = any(under_abn(p, stack + (tid,)) for p in d["parents"])
        memo[tid] = res
        return res

    rolled = sum(1 for t in live if under_abn(t))
    print(f"  live terms UNDER phenotypic_abnormality (transitive): {rolled}")

    # Common symptoms: how many phenotypic abnormality labels are 1-3 words
    short = [d for t, d in live.items()
             if under_abn(t) and 1 <= len(d["name"].split()) <= 3]
    print(f"  of those, labels that are 1-3 plain words: {len(short)}")
    for probe in ("Fever", "Cough", "Headache", "Vomiting", "Diarrhea",
                  "Rash", "Dyspnea", "Fatigue", "Seizure", "Pain"):
        hit = [t for t, d in live.items() if d["name"].casefold() == probe.casefold()]
        for t in hit:
            d = terms[t]
            print(f"    {t}  {d['name']!r}  under_abn={under_abn(t)}  "
                  f"syn={d['synonyms'][:2]}")

    # ---- HPOA ----
    print("\n=== phenotype.hpoa ===")
    ameta = header_meta(HPOA)
    for k, v in ameta.items():
        print(f"  {k}: {v[:300]}")

    rows = 0
    per_dis: dict[str, set] = collections.defaultdict(set)
    per_dis_direct: dict[str, set] = collections.defaultdict(set)
    prefix = collections.Counter()
    dis_names: dict[str, str] = {}
    qualifier = collections.Counter()
    all_hp = set()
    with open(HPOA, encoding="utf-8", errors="replace") as fh:
        cols = None
        for line in fh:
            if line.startswith("#"):
                continue
            if cols is None:
                cols = line.rstrip("\n").split("\t")
                continue
            f = line.rstrip("\n").split("\t")
            if len(f) < 12:
                continue
            rows += 1
            did, dname, qual, hpo = f[0], f[1], f[2], f[3]
            prefix[did.split(":")[0]] += 1
            dis_names.setdefault(did, dname)
            per_dis[did].add(hpo)
            all_hp.add(hpo)
            if hpo in live:
                per_dis_direct[did].add(hpo)
            qualifier[qual or "(blank)"] += 1

    print(f"\n  annotation rows                 : {rows}")
    print(f"  distinct database_id (diseases) : {len(per_dis)}")
    print(f"  distinct HPO terms used         : {len(all_hp)}")
    print(f"  disease ID prefixes (rows)      : {dict(prefix)}")
    print(f"  distinct diseases by prefix     : "
          f"{dict(collections.Counter(d.split(':')[0] for d in per_dis))}")
    print(f"  top qualifiers                  : {qualifier.most_common(8)}")

    print("\n  diseases with >= N distinct HPO terms:")
    for n in (3, 5, 10, 15, 20):
        g = sum(1 for s in per_dis.values() if len(s) >= n)
        gd = sum(1 for s in per_dis_direct.values() if len(s) >= n)
        print(f"    >={n:>3} : raw terms {g:>6}   |  direct phenotypic_abnormality {gd:>6}")

    # Coverage against the ontology
    known = sum(1 for h in all_hp if h in live)
    print(f"\n  HPO terms in annotations present in hp.obo: {known}/{len(all_hp)}")

    # Top diseases by annotation count
    top = sorted(per_dis.items(), key=lambda kv: -len(kv[1]))[:8]
    print("\n  most-annotated diseases:")
    for did, s in top:
        print(f"    {len(s):>4}  {did}  {dis_names[did][:60]}")

    # Vocabulary size actually usable: distinct names for phenotypic abnormalities
    usable = {terms[h]["name"] for h in all_hp
              if h in live and under_abn(h)}
    print(f"\n  distinct annotated terms that are live + under "
          f"phenotypic_abnormality : {len(usable)}")

    # The plain-English question. HPO tags some synonyms with a 'layperson'
    # scope, which is exactly a lay synonym for typing 'fever, cough'.
    annotated = [h for h in all_hp if h in live]
    with_lay = [h for h in annotated
                if any(scope == "layperson" for _, scope in terms[h]["synonyms"])]
    all_lay = [t for t in live if any(s == "layperson" for _, s in terms[t]["synonyms"])]
    print(f"  annotated terms carrying >=1 'layperson' synonym : {len(with_lay)}"
          f"  ({100 * len(with_lay) / max(1, len(annotated)):.1f}% of annotated)")
    print(f"  live HPO terms carrying >=1 'layperson' synonym   : {len(all_lay)}")

    one_word = sorted({terms[h]["name"] for h in annotated
                       if terms[h]["name"].count(" ") == 0})
    print(f"  annotated labels that are a SINGLE word           : {len(one_word)}")
    print(f"  sample single-word annotated labels: "
          f"{', '.join(one_word[:30])}")

    lay_pool = sorted({terms[h]["name"] for h in all_hp
                       if h in live
                       and any(s == "layperson" for _, s in terms[h]["synonyms"])})
    print(f"  single-word layperson-scored labels available    : "
          f"{sum(1 for n in lay_pool if ' ' not in n)}")
    print(f"  sample: {', '.join([n for n in lay_pool if ' ' not in n][:30])}")

    # How well would the CURRENT hand-written triage vocabulary survive?
    print("\n=== current Meridian symptom coverage check ===")
    seed = [
        "runny nose", "sore throat", "sneezing", "cough", "mild fatigue",
        "chills", "fever", "body ache", "headache", "fatigue", "frequent urination",
        "excessive thirst", "increased hunger", "blurred vision", "weight loss",
        "rash", "joint pain", "nausea", "bleeding gums", "sweating", "muscle pain",
        "dizziness", "chest pain", "shortness of breath", "irregular heartbeat",
        "weight gain", "cold intolerance", "dry skin", "hair loss", "constipation",
        "depression", "wheezing", "chest tightness", "diarrhoea", "vomiting",
        "abdominal pain", "dehydration", "burning urination", "cloudy urine",
        "pale skin", "fast heartbeat", "severe headache", "sensitivity to light",
        "sensitivity to sound", "visual disturbance", "persistent worry",
        "restlessness", "irritability", "difficulty concentrating",
        "sleep disturbance", "palpitations", "loss of taste", "loss of smell",
    ]
    names = {terms[h]["name"].casefold() for h in all_hp if h in live}
    syns: dict[str, str] = {}
    for h in all_hp:
        if h in live:
            for s, scope in terms[h]["synonyms"]:
                syns.setdefault(s.casefold(), terms[h]["name"])
    exact = [s for s in seed if s in names]
    viasyn = [s for s in seed if s not in names and s in syns]
    missing = [s for s in seed if s not in names and s not in syns]
    print(f"  seed symptoms matching an HPO label exactly : {len(exact)}/{len(seed)}")
    print(f"  matchable only via an HPO synonym         : {len(viasyn)}/{len(seed)}")
    for s in viasyn:
        print(f"      '{s}' -> {syns[s]}")
    print(f"  no HPO term at all                        : {len(missing)}/{len(seed)}")
    print(f"      {missing}")


if __name__ == "__main__":
    main()