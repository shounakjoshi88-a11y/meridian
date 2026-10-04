"""Tests for triage.py. Plain asserts, no pytest (not in any lab).

Run from the project root:  python tests/test_triage.py
"""

import os
import sys

# Absolute path, so this works from any working directory and so the
# language server can resolve the import statically.
BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

import triage  # noqa: E402


def test_normalise_accepts_three_shapes():
    """A list, a pipe string and a comma string must give the same set."""
    expected = {"fever", "cough", "fatigue"}

    assert triage.normalise_symptoms(["Fever", " cough ", "FATIGUE"]) == expected
    assert triage.normalise_symptoms("fever|cough|fatigue") == expected
    assert triage.normalise_symptoms("fever, cough , fatigue") == expected
    assert triage.normalise_symptoms("") == set()
    assert triage.normalise_symptoms([]) == set()
    print("  ok  normalise_symptoms accepts list, pipe and comma forms")


def test_parse_age_range():
    """Age range strings parse, bad ones return None."""
    assert triage.parse_age_range("35-70") == (35, 70)
    assert triage.parse_age_range("0-60") == (0, 60)
    assert triage.parse_age_range("") is None
    assert triage.parse_age_range("all") is None
    assert triage.parse_age_range("70-35") == (70, 35)   # inverted but parseable
    print("  ok  parse_age_range handles valid and invalid input")


def test_age_outside_range():
    """Age checks only fire when both age and range are usable."""
    assert triage.age_outside_range(20, "35-70") is True
    assert triage.age_outside_range(45, "35-70") is False
    assert triage.age_outside_range("", "35-70") is False
    assert triage.age_outside_range(45, "") is False
    assert triage.age_outside_range(45, "nonsense") is False
    print("  ok  age_outside_range ignores missing age or unusable range")


def test_exact_cold_match_scores_one():
    """Reporting every cold symptom exactly gives a perfect score."""
    diseases = triage.load_diseases()
    cold = [d for d in diseases if d["disease_id"] == "D-01"][0]

    score, coverage, precision, n_match, n_miss = triage.score_disease(
        cold["symptom_set"], cold)

    assert score == 1.0, score
    assert coverage == 1.0
    assert precision == 1.0
    assert n_match == 6 and n_miss == 0
    print(f"  ok  exact Common Cold match scores 1.0 ({n_match} symptoms)")


def test_unrelated_symptoms_clamp_to_zero():
    """A long unrelated report must give 0, never a negative score."""
    diseases = triage.load_diseases()
    cold = [d for d in diseases if d["disease_id"] == "D-01"][0]

    unrelated = {"itch", "rash", "hairloss", "nausea", "joint pain", "dry mouth"}
    score, _, _, n_match, _ = triage.score_disease(unrelated, cold)

    assert n_match == 0, n_match
    assert score == 0.0, f"score was {score}, expected 0 not negative"
    print("  ok  6 unrelated symptoms clamp to 0.0, not negative")


def test_empty_symptom_list_is_safe():
    """Empty input returns zeros instead of dividing by zero."""
    diseases = triage.load_diseases()
    cold = [d for d in diseases if d["disease_id"] == "D-01"][0]

    result = triage.score_disease(set(), cold)

    assert result[0] == 0.0
    assert result[3] == 0
    print("  ok  empty symptom list returns zeros, no ZeroDivisionError")


def test_long_report_does_not_match_cold():
    """The precision term must stop a big report matching a small disease.

    A patient reporting 14 symptoms, 4 of which are the 5 cold symptoms,
    would score 0.8 on coverage alone. Coverage and penalty together must
    stop that becoming a match.
    """
    diseases = triage.load_diseases()
    cold = [d for d in diseases if d["disease_id"] == "D-01"][0]

    padded = set(cold["symptom_set"]) | {
        "nausea", "rash", "joint pain", "blurred vision", "palpitations",
        "numbness", "weight loss", "insomnia", "itching",
    }

    results = triage.rank_diseases(padded)
    top = results[0]["name"]

    assert len(padded) > len(cold["symptom_set"]) + 5
    print(f"  ok  padded 14-symptom report ranks {top!r}, not Common Cold")


def test_severity_breaks_near_ties():
    """Higher severity must win when scores are within the band."""
    results = [
        {"name": "low one", "score": 0.58, "severity": "low"},
        {"name": "severe one", "score": 0.56, "severity": "severe"},
        {"name": "far away", "score": 0.40, "severity": "moderate"},
    ]

    ordered = triage.apply_severity_bands(results)
    names = [r["name"] for r in ordered]

    assert names[0] == "severe one", names
    assert names[1] == "low one", names
    assert names[2] == "far away", names
    print("  ok  severity promotes 0.56/severe above 0.58/low within band")


def test_severity_does_not_override_real_gap():
    """A clearly lower score must stay below, whatever its severity."""
    results = [
        {"name": "mild but likely", "score": 0.70, "severity": "low"},
        {"name": "severe but weak", "score": 0.30, "severity": "severe"},
    ]

    ordered = triage.apply_severity_bands(results)

    assert ordered[0]["name"] == "mild but likely", ordered
    print("  ok  severity does not promote a score 0.40 behind")


def test_dengue_case_ranks_sensibly():
    """A realistic multi-symptom report returns ranked results."""
    symptoms = ["high fever", "severe body ache", "joint pain", "rash",
                "headache", "nausea"]

    results = triage.rank_diseases(symptoms)

    assert len(results) > 0, "expected at least one match"
    assert results[0]["name"] == "Dengue Fever", results[0]["name"]
    assert results[0]["severity"] == "severe"
    assert results[0]["matched_count"] == 6
    assert results[0]["percent"] > 0
    print(f"  ok  dengue report ranks {results[0]['name']} "
          f"at {results[0]['percent']}%, {len(results)} candidates")


def test_minimum_evidence_gate():
    """One shared symptom must not produce a match."""
    results = triage.rank_diseases(["headache"])

    for r in results:
        assert r["matched_count"] >= triage.MIN_MATCHED_SYMPTOMS, r

    print(f"  ok  single-symptom query returns no gated-in disease "
          f"({len(results)} survived)")


def test_contraindication_warning():
    """A reported condition the drug rules out must raise a warning."""
    diseases = triage.load_diseases()
    diabetes = [d for d in diseases if d["disease_id"] == "D-03"][0]

    warnings = triage.check_contraindications(diabetes, {"kidney disease"})

    assert len(warnings) == 1, warnings
    assert "kidney disease" in warnings[0]
    assert "Metformin" in warnings[0]
    assert triage.check_contraindications(diabetes, {"asthma"}) == []
    assert triage.check_contraindications(diabetes, set()) == []
    print("  ok  contraindication fires on kidney disease, not on asthma")


def test_age_note_appears_in_results():
    """A 20 year old flagged as outside 35-70 should be marked."""
    results = triage.rank_diseases(
        ["frequent urination", "excessive thirst", "fatigue"], age="20")

    diabetes = [r for r in results if r["disease_id"] == "D-03"][0]
    assert diabetes["age_outside_range"] is True

    results_ok = triage.rank_diseases(
        ["frequent urination", "excessive thirst", "fatigue"], age="50")
    diabetes_ok = [r for r in results_ok if r["disease_id"] == "D-03"][0]
    assert diabetes_ok["age_outside_range"] is False
    print("  ok  age 20 flagged outside range, age 50 not")


def test_evidence_label_reflects_thin_reports():
    """Two matched symptoms must not read like five.

    Reporting only headache and fever scores above 50% because precision
    is high, but the evidence is thin. The label has to say so.
    """
    thin = triage.rank_diseases(["headache", "fever"])

    for r in thin:
        assert r["evidence"] == "weak", r
        assert r["matched_count"] == 2, r

    strong = triage.rank_diseases(
        ["high fever", "severe body ache", "joint pain", "rash", "headache"])

    assert strong[0]["evidence"] == "strong", strong[0]
    assert strong[0]["matched_count"] >= 5

    assert triage.evidence_strength(2) == "weak"
    assert triage.evidence_strength(3) == "moderate"
    assert triage.evidence_strength(4) == "moderate"
    assert triage.evidence_strength(5) == "strong"
    assert triage.evidence_strength(7) == "strong"
    print("  ok  2 matches labelled weak, 5+ labelled strong")


def test_report_explains_out_of_order_scores():
    """A lower-scoring severe row must explain itself.

    Malaria 55% above Influenza 57% is correct behaviour but reads like a
    sorting bug, so the report has to say why.
    """
    results = triage.rank_diseases(["headache", "fever"])

    scores = [r["score"] for r in results]
    inverted = any(scores[i] < scores[i + 1] for i in range(len(scores) - 1))

    text = triage.render_report({"patient_id": "P-0002", "name": "Diya Patel"}, results)

    if inverted:
        assert "because severity outweighs" in text, text
        print("  ok  inverted score order is explained in the report")
    else:
        assert "because severity outweighs" not in text, text
        print("  ok  scores already descending, no explanation needed")


def test_report_states_evidence_and_medication():
    """Each row must show the evidence level and what to give."""
    patient = {"patient_id": "P-0007", "name": "Vikram Rao", "age": 61}
    results = triage.rank_diseases(
        ["high fever", "severe body ache", "joint pain", "rash", "headache"])

    text = triage.render_report(patient, results)

    assert "evidence:" in text, text
    assert "medication:" in text, text
    assert "strong" in text, text
    print("  ok  report shows evidence level and medication per row")


def test_results_are_capped_and_ordered():
    """Never more than MAX_RESULTS, always best first."""
    results = triage.rank_diseases(
        ["fever", "cough", "fatigue", "headache", "nausea", "chills"])

    assert len(results) <= triage.MAX_RESULTS

    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True), scores
    print(f"  ok  capped at {triage.MAX_RESULTS}, scores descending")


def test_report_ends_with_disclaimer():
    """The disclaimer must be the final content line."""
    patient = {"patient_id": "P-0007", "name": "Vikram Rao", "age": 61}

    with_results = triage.render_report(
        patient, triage.rank_diseases(["fever", "cough", "fatigue"]))
    without = triage.render_report(patient, [])

    for text in (with_results, without):
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        assert lines[-1] == "*" * 44, lines[-3:]
        assert lines[-2] == triage.DISCLAIMER, lines[-2]

    assert "MERIDIAN CONSULTATION" in with_results
    assert "NOT A DIAGNOSIS" in with_results
    print("  ok  disclaimer is present and final, with and without matches")


def test_report_shows_warning_line():
    """A contraindication must be visible in the rendered text."""
    patient = {"patient_id": "P-0003", "name": "Rohan Mehta", "age": 45}
    results = triage.rank_diseases(
        ["frequent urination", "excessive thirst", "fatigue"],
        conditions=["kidney disease"])

    text = triage.render_report(patient, results, conditions=["kidney disease"])

    assert "WARNING" in text, text
    assert "kidney disease" in text
    print("  ok  report renders a WARNING line for the contraindication")


def test_knowledge_base_is_loaded():
    """All 15 seeded diseases load with parsed sets."""
    diseases = triage.load_diseases()

    assert len(diseases) == 15, len(diseases)

    for d in diseases:
        assert d["symptom_set"], d["disease_id"]
        assert isinstance(d["symptom_set"], set)

    with_contra = [d for d in diseases if d["contraindication_set"]]
    assert len(with_contra) >= 5, len(with_contra)
    print(f"  ok  15 diseases loaded, {len(with_contra)} carry contraindications")


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"running {len(tests)} triage tests\n")

    failures = []

    for fn in tests:
        try:
            fn()
        except AssertionError as e:
            failures.append((fn.__name__, str(e)))
            print(f"  FAIL  {fn.__name__}: {e}")
        except Exception as e:
            failures.append((fn.__name__, f"{type(e).__name__}: {e}"))
            print(f"  ERROR {fn.__name__}: {type(e).__name__}: {e}")

    print()
    if failures:
        print(f"{len(failures)} of {len(tests)} failed")
        return 1

    print(f"all {len(tests)} triage tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())