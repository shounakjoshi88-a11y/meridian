"""The decisive planning number.

HPOA alone offers ~11k diseases with >=5 HPO terms, but most HPO terms are
specialist descriptors of rare disease ('Macrodactyly of toes') that nobody
types as 'fever, cough'. So measure how the yield collapses once the symptom
vocabulary is restricted to terms common enough that a non-expert could
actually report them.

Frequency-based filter, no hand-picked list: a term is 'lay-reportable' if
it is annotated to at least THRESHOLD distinct diseases in HPOA. Then count
diseases that still have >=5 such terms.

Usage: python plan_combination.py
"""

from __future__ import annotations

import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from analyse_hpo import HPOA, OBO, load_obo  # noqa: E402

terms = load_obo(OBO)
live = {t: d for t, d in terms.items() if not d["obsolete"]}
abn = "HP:0000118"
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
    memo[tid] = any(under_abn(p, stack + (tid,)) for p in d["parents"])
    return memo[tid]


# ---- read HPOA, drop NOT qualifiers ----
per_dis: dict[str, set] = collections.defaultdict(set)
names: dict[str, str] = {}
rows = 0
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
        rows += 1
        per_dis[f[0]].add(f[3])
        names.setdefault(f[0], f[1])

print(f"HPOA positive rows                : {rows:,}")
print(f"distinct diseases                 : {len(per_dis):,}")

df = collections.Counter()
for s in per_dis.values():
    for h in s:
        df[h] += 1
print(f"distinct HPO terms used           : {len(df):,}")

print("\n=== vocabulary rarity profile (how many diseases carry a term) ===")
buckets = [(1, 1), (2, 4), (5, 9), (10, 24), (25, 49), (50, 99),
           (100, 199), (200, 499), (500, 999), (1000, 10 ** 9)]
for lo, hi in buckets:
    n = sum(1 for v in df.values() if lo <= v <= hi)
    lbl = f"{lo}-{hi}" if hi < 10 ** 9 else f"{lo}+"
    print(f"  annotated in {lbl:>9} diseases : {n:>6} terms")

print("\n=== yield under a lay-reportable vocabulary filter ===")
print("    (term must be annotated in >= THRESHOLD distinct diseases)")
print(f"{'THRESHOLD':>10} {'vocab':>7} {'>=5 symp':>9} {'>=10 symp':>10} "
      f"{'>=15 symp':>10}")
for th in (1, 5, 10, 25, 50, 100, 200, 500, 1000):
    vocab = {h for h, v in df.items() if v >= th and h in live and under_abn(h)}
    g5 = g10 = g15 = 0
    for s in per_dis.values():
        n = len(s & vocab)
        if n >= 5:
            g5 += 1
        if n >= 10:
            g10 += 1
        if n >= 15:
            g15 += 1
    print(f"{th:>10} {len(vocab):>7} {g5:>9,} {g10:>10,} {g15:>10,}")

# ---- top common terms, with their lay synonyms ----
print("\n=== 40 most widely annotated terms (the natural lay symptom core) ===")
lay = {}
for h in df:
    if h in live:
        for s, scope in terms[h]["synonyms"]:
            if scope == "layperson":
                lay.setdefault(s, terms[h]["name"])
common = sorted(df.items(), key=lambda kv: -kv[1])[:40]
for h, c in common:
    d = terms.get(h, {})
    lay_syn = [s for s, sc in d.get("synonyms", []) if sc == "layperson"][:2]
    print(f"  {c:>5} diseases  {h}  {d.get('name','?')[:46]:<46} "
          f"lay={lay_syn}")

# ---- what the common core looks like in the seed data ----
print("\n=== seed-disease spot check against the >=100-disease vocabulary ===")
vocab = {h for h, v in df.items() if v >= 100 and h in live and under_abn(h)}
for probe in ("Fever", "Cough", "Headache", "Vomiting", "Diarrhea", "Rash",
              "Dyspnea", "Fatigue", "Seizure", "Pain", "Nausea",
              "Abdominal pain", "Skin rash", "Anosmia", "Ageusia"):
    hit = [h for h, d in terms.items()
           if d["name"].casefold() == probe.casefold() and not d["obsolete"]]
    for h in hit:
        print(f"  {probe:<16} -> {h}  in>=100-disease vocab: {h in vocab}"
              f"  (annotated in {df.get(h, 0)} diseases)")

print("\n=== diseases by source prefix, >=5 terms, >=100-disease vocabulary ===")
by_prefix = collections.Counter()
for did, s in per_dis.items():
    if len(s & vocab) >= 5:
        by_prefix[did.split(":")[0]] += 1
print(" ", dict(by_prefix))
print(f"  TOTAL: {sum(by_prefix.values()):,} diseases with >=5 common symptoms")