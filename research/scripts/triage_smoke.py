"""Smoke test the rebuilt knowledge base through the real triage engine."""
import sys

sys.path.insert(0, "backend")

import triage

diseases = triage.load_diseases("data/diseases.csv")
print(f"loaded {len(diseases)} diseases")
print(f"first: {diseases[0]['disease_id']} {diseases[0]['name']}")
print()

CASES = [
    "fever, cough, sore throat, runny nose",
    "excessive thirst, frequent urination, weight loss, fatigue",
    "chest pain, breathlessness on exertion, cold sweat, palpitations",
    "lower back pain, stiffness, body ache, tingling",
    "itching, rash, red eye, watery eyes",
    "heartburn, difficulty swallowing, upper abdominal pain, nausea",
    "low mood, sleep disturbance, poor concentration, fatigue",
    "painful urination, frequent urination, urinary urgency, fever",
]

for symptoms in CASES:
    results = triage.rank_diseases(symptoms)
    print(symptoms)
    if not results:
        print("   (no match)")
    for r in results[:3]:
        name = r["name"][:46]
        print(f"   {name:<46} {r['percent']:>3}%  "
              f"{r['evidence']:<8} {r['severity']}")
    print()