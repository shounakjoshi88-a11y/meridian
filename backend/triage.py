"""Symptom triage for Meridian.

Taught concepts: set intersection and difference (& -), dicts, list and set
comprehensions, sorted(key=lambda), while loops, string .strip() and
.casefold(), f-strings, default arguments.

Pure functions only. Nothing here touches Flask or writes files, so the
whole module is testable on its own.

Scoring is set algebra pointed at symptoms. It is the Practical 3 Venn
problem (comedy, fantasy, romance) with films replaced by diseases.
"""

DISCLAIMER = "NOT A DIAGNOSIS. TRIAGE GUIDANCE ONLY."

SEVERITY_RANK = {
    "low": 0,
    "moderate": 1,
    "elevated": 2,
    "high": 3,
    "severe": 4,
}

# Two diseases scoring within this distance of each other are treated as
# tied, and severity breaks the tie. Wider than this and a slightly better
# score would hide a genuinely more urgent condition.
BAND_WIDTH = 0.05

COVERAGE_WEIGHT = 0.6
PRECISION_WEIGHT = 0.4
EXTRA_PENALTY = 0.5

MIN_MATCHED_SYMPTOMS = 2
MAX_RESULTS = 5

# The score is a match strength, not a probability. Reporting two common
# symptoms can score above 50% simply because precision is high, yet the
# evidence is thin. This label lets the caller say how much the number is
# worth, so "55% from 2 of 8 symptoms" is not read as a 55% chance.
def evidence_strength(matched_count, total_symptoms=0):
    """Label how much the matched symptom count is actually worth.

    strong    5 or more symptoms matched
    moderate  3 to 4 matched
    weak      2 matched, the minimum we accept as evidence
    """
    if matched_count >= 5:
        return "strong"
    if matched_count >= 3:
        return "moderate"
    return "weak"


def normalise_symptoms(symptoms):
    """Turn a list or string of symptoms into a clean set.

    Accepts ["Fever", " cough "] or "fever|cough" or "fever, cough" and
    returns {"fever", "cough"}. Blank entries are dropped.
    """
    if isinstance(symptoms, str):
        parts = symptoms.replace("|", ",").split(",")
    else:
        parts = symptoms

    return {str(p).strip().casefold() for p in parts if str(p).strip()}


def load_diseases(path="data/diseases.csv"):
    """Read diseases.csv and attach a symptom set to each row.

    The symptoms cell is pipe delimited, so splitting is a single call.
    See spec section 4.4 for why commas cannot be used here.
    """
    import csv

    diseases = []

    with open(path, "r", newline="") as f:
        for row in csv.DictReader(f):
            row["symptom_set"] = {s.strip().casefold()
                                  for s in row["symptoms"].split("|") if s.strip()}
            row["contraindication_set"] = {
                c.strip().casefold()
                for c in (row.get("contraindications") or "").split("|")
                if c.strip()
            }
            diseases.append(row)

    return diseases


def score_disease(patient_symptoms, disease):
    """Score one disease against the reported symptoms.

    Returns (score, coverage, precision, matched_count, missing_count).

    coverage   how much of the disease's symptom list the patient shows
    precision  how much of the patient's report the disease explains
    penalty    charged for symptoms the disease cannot account for

    Three numbers rather than one, because a single ratio is misleading in
    both directions. A patient listing 14 symptoms should not match Common
    Cold on 4 of its 5; a patient reporting only fever, fatigue and cough
    should not be told nothing is wrong. precision punishes the first,
    coverage rescues the second.

    The score is clamped to [0, 1] so a long list of unrelated symptoms
    produces 0 rather than a negative percentage.
    """
    if not patient_symptoms:
        return 0.0, 0.0, 0.0, 0, len(disease["symptom_set"])

    matched = patient_symptoms & disease["symptom_set"]
    extra = patient_symptoms - disease["symptom_set"]
    missing = disease["symptom_set"] - patient_symptoms

    coverage = len(matched) / len(disease["symptom_set"])
    precision = len(matched) / len(patient_symptoms)
    penalty = len(extra) * EXTRA_PENALTY

    score = (coverage * COVERAGE_WEIGHT) + (precision * PRECISION_WEIGHT) - penalty
    score = max(0.0, min(1.0, score))

    return score, coverage, precision, len(matched), len(missing)


def apply_severity_bands(results):
    """Sort by score, then let severity break near ties.

    Severity is deliberately not multiplied into the score. Multiplying
    would let a low severity condition climb arbitrarily high, which is
    clinically wrong: severity changes urgency, not likelihood. Instead,
    diseases whose scores sit within BAND_WIDTH are treated as tied and
    ordered by severity.

    Python's sort is stable, so equal score and equal severity keep their
    existing relative order.
    """
    results.sort(key=lambda r: r["score"], reverse=True)

    banded = []
    i = 0

    while i < len(results):
        band = []
        anchor = results[i]["score"]

        while i < len(results) and anchor - results[i]["score"] < BAND_WIDTH:
            band.append(results[i])
            i += 1

        band.sort(key=lambda r: SEVERITY_RANK.get(r["severity"], 0),
                  reverse=True)
        banded.extend(band)

    return banded


def parse_age_range(text):
    """Turn "35-70" into (35, 70). Returns None if it cannot be read."""
    if not text:
        return None

    parts = text.split("-")

    if len(parts) != 2:
        return None

    low, high = parts[0].strip(), parts[1].strip()

    if not low.isdigit() or not high.isdigit():
        return None

    return int(low), int(high)


def age_outside_range(age, age_range):
    """True when age is known and falls outside the disease's usual range."""
    bounds = parse_age_range(age_range)

    if bounds is None or age in (None, ""):
        return False

    try:
        age = int(age)
    except (TypeError, ValueError):
        return False

    low, high = bounds
    return age < low or age > high


def check_contraindications(disease, conditions):
    """Return warning strings for any condition the disease rules out.

    conditions is a set of the patient's existing conditions, e.g.
    {"pregnancy", "kidney disease"}. Set intersection, same operator as
    the symptom match but pointing the other way.
    """
    if not conditions:
        return []

    clashes = conditions & disease.get("contraindication_set", set())

    if not clashes:
        return []

    listed = ", ".join(sorted(clashes))
    return [f"{disease['medication']} is contraindicated for: {listed}"]


def rank_diseases(symptoms, conditions=None, age=None, limit=MAX_RESULTS):
    """Rank candidate diseases for a set of reported symptoms.

    Returns a list of dicts, best first. Each carries the score, the
    matched and missing symptoms, severity, and any warnings.

    Diseases with fewer than MIN_MATCHED_SYMPTOMS shared symptoms are
    dropped. One shared symptom is not evidence: "fatigue" appears in
    most rows of the knowledge base and would match everything.
    """
    patient_symptoms = normalise_symptoms(symptoms)
    condition_set = normalise_symptoms(conditions) if conditions else set()

    if not patient_symptoms:
        return []

    results = []

    for disease in load_diseases():
        score, coverage, precision, n_match, n_miss = score_disease(
            patient_symptoms, disease)

        if n_match < MIN_MATCHED_SYMPTOMS:
            continue

        matched = sorted(patient_symptoms & disease["symptom_set"])
        missing = sorted(disease["symptom_set"] - patient_symptoms)
        unexplained = sorted(patient_symptoms - disease["symptom_set"])
        total = len(matched) + len(missing)

        results.append({
            "disease_id": disease["disease_id"],
            "name": disease["name"],
            "severity": disease["severity"],
            "score": round(score, 4),
            "percent": int(round(score * 100)),
            "evidence": evidence_strength(len(matched), total),
            "coverage": round(coverage, 4),
            "precision": round(precision, 4),
            "matched_count": n_match,
            "missing_count": n_miss,
            "total_symptoms": total,
            "matched_symptoms": matched,
            "missing_symptoms": missing,
            "unexplained_symptoms": unexplained,
            "medication": disease["medication"],
            "dosage": disease["dosage"],
            "age_range": disease["age_range"],
            "age_outside_range": age_outside_range(age, disease["age_range"]),
            "warnings": check_contraindications(disease, condition_set),
        })

    results = apply_severity_bands(results)
    return results[:limit]


def format_percent(result):
    """Return the score as a right aligned percentage string."""
    return f"{result['percent']:>3}%"


def render_report(patient, results, conditions=None):
    """Render the consultation report in the Lab 5 banner format.

    patient is a dict with at least patient_id, name and optionally age.
    The disclaimer is always the final line, per spec section 5.5.
    """
    line = "*" * 44
    out = []
    out.append(line)
    out.append(" MERIDIAN CONSULTATION")
    out.append(line)

    identity = f"{patient.get('patient_id', '')}  ({patient.get('name', '')})"
    if patient.get("age"):
        identity += f"  age {patient['age']}"
    out.append(f"Patient       : {identity}")

    if conditions:
        reported = ", ".join(sorted(normalise_symptoms(conditions)))
        out.append(f"Conditions    : {reported}")

    if not results:
        out.append("")
        out.append("No disease matched the reported symptoms.")
        out.append("")
        out.append(line)
        out.append(DISCLAIMER)
        out.append(line)
        return "\n".join(out)

    out.append("")
    out.append("MOST LIKELY")
    out.append("")

    for i, r in enumerate(results, start=1):
        out.append(
            f"  {i}. {r['name']:<22} {format_percent(r)}"
            f"   match {r['matched_count']}/{r['total_symptoms']}"
            f"   {r['severity'].upper()}"
        )
        out.append(
            f"     evidence: {r['evidence']}"
            f"   medication: {r['medication']} {r['dosage']}"
        )

        for warning in r["warnings"]:
            out.append(f"     WARNING: {warning}")

        if r["age_outside_range"]:
            out.append(
                f"     NOTE: usual age range is {r['age_range']},"
                f" patient is {patient.get('age', 'unknown')}"
            )

        # A later row can outrank an earlier one on raw score. Say so, rather
        # than letting the list look like it is mis-sorted.
        if i > 1 and r["score"] > results[i - 2]["score"]:
            out.append(
                f"     (listed below {results[i - 2]['name']} on score"
                f" because severity outweighs a"
                f" {abs(results[i - 2]['score'] - r['score']):.2f} difference)"
            )

    out.append("")
    out.append(line)
    out.append(DISCLAIMER)
    out.append(line)

    return "\n".join(out)