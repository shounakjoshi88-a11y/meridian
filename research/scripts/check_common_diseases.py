"""Does phenotype.hpoa cover the diseases an outpatient actually sees?

HPOA is a rare-disease corpus, so the triage engine may be unable to
distinguish influenza from a metabolic disorder. Check the real file
rather than assume.
"""
import collections
import io
import os

RAW = os.path.join("research", "raw")

COMMON = [
    "diabetes", "hypertension", "asthma", "influenza", "pneumonia",
    "tuberculosis", "typhoid", "anaemia", "anemia", "depression",
    "migraine", "arthritis", "fever", "cough", "diarrhoea", "diarrhea",
    "cholera", "hepatitis", "malaria", "dengue", "covid", "copd",
    "bronchitis", "gastritis", "meningitis", "epilepsy", "cancer",
]

# HPOA frequencies tell us how often a phenotype shows up in a disease.
# Counting how many diseases carry each term shows which terms are usable
# at all as a triage input.

term_freq = collections.Counter()
disease_terms = collections.defaultdict(set)
disease_names = {}

with io.open(os.path.join(RAW, "phenotype.hpoa"), encoding="utf-8",
             errors="replace") as f:
    header = None
    for line in f:
        if line.startswith("#"):
            continue
        parts = line.rstrip("\n").split("\t")
        if header is None:
            header = parts
            idx = {name: i for i, name in enumerate(header)}
            continue
        if len(parts) < 4:
            continue
        did = parts[idx["database_id"]]
        name = parts[idx["disease_name"]]
        hpo = parts[idx["hpo_id"]]
        disease_names[did] = name
        term_freq[hpo] += 1
        disease_terms[did].add(hpo)

print(f"diseases in file: {len(disease_terms):,}")
print(f"distinct HPO terms: {len(term_freq):,}")
print()

print("=== which common diseases are present? ===")
lower = {d: n.lower() for d, n in disease_names.items()}
for term in COMMON:
    hits = [d for d, n in lower.items() if term in n]
    mark = f"{len(hits):>4}" if hits else "   -"
    sample = disease_names[hits[0]][:52] if hits else ""
    print(f"  {mark}  {term:<12} {sample}")

print()
print("=== how many diseases carry >= 5 distinct HPO terms? ===")
tally = collections.Counter(min(len(t), 20) for t in disease_terms.values())
for n in (1, 2, 3, 5, 10, 15, 20):
    at_least = sum(v for k, v in tally.items() if k >= n)
    print(f"  >= {n:>2} terms : {at_least:>6,} diseases")

print()
print("=== top 20 most widely shared HPO terms (the usable input vocabulary) ===")
for hpo, count in term_freq.most_common(20):
    print(f"  {hpo}  {count:>6,} diseases")