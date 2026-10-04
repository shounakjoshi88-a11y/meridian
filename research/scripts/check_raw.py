"""Quick sanity check on the downloaded research/raw files.

Confirms the big files parse and reports the real numbers, so the build is
planned against measured counts rather than quoted ones.
"""
import collections
import csv
import gzip
import io
import os

RAW = os.path.join("research", "raw")


def size_mb(name):
    return round(os.path.getsize(os.path.join(RAW, name)) / 1024 / 1024, 2)


print("=== phenotype.hpoa ===")
path = os.path.join(RAW, "phenotype.hpoa")
if not os.path.exists(path):
    print("  MISSING")
else:
    diseases = set()
    hpo_ids = set()
    rows = 0
    header = []
    with io.open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("#"):
                continue
            if not header:
                header = line.rstrip("\n").split("\t")
                continue
            rows += 1
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2:
                diseases.add(parts[0])
                hpo_ids.add(parts[1])
    print(f"  size          : {size_mb('phenotype.hpoa')} MB")
    print(f"  header        : {header}")
    print(f"  annotation rows: {rows:,}")
    print(f"  distinct diseases: {len(diseases):,}")
    print(f"  distinct HPO terms: {len(hpo_ids):,}")
    print(f"  sample disease ids: {sorted(diseases)[:4]}")

print()
print("=== mondo.obo ===")
path = os.path.join(RAW, "mondo.obo")
if not os.path.exists(path):
    print("  MISSING")
else:
    terms = 0
    names = 0
    with io.open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("[Term]"):
                terms += 1
            elif line.startswith("name: "):
                names += 1
            elif line == "\n":
                pass
    print(f"  size    : {size_mb('mondo.obo')} MB")
    print(f"  [Term] blocks : {terms:,}")
    print(f"  name: lines   : {names:,}")

print()
print("=== hp.obo ===")
path = os.path.join(RAW, "hp.obo")
if os.path.exists(path):
    terms = 0
    with io.open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("[Term]"):
                terms += 1
    print(f"  size    : {size_mb('hp.obo')} MB")
    print(f"  [Term] blocks : {terms:,}")