"""Tests for registry.py. Plain asserts, no pytest.

Run from the project root:  python tests/test_registry.py
"""

import os
import sys

# Absolute path, so this works from any working directory and so the
# language server can resolve the import statically.
BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

import registry  # noqa: E402
import store  # noqa: E402


def load(record_type):
    """Read a registry's records from the real seed files."""
    records, _ = store.read_all(record_type)
    return records


def test_normalise_and_query_terms():
    """Values are lower cased and stripped before comparison."""
    assert registry.normalise("  Metformin ") == "metformin"
    assert registry.normalise("O+") == "o+"
    assert registry.normalise(500) == "500"

    assert registry.query_terms("Metformin, diabetes") == ["metformin", "diabetes"]
    assert registry.query_terms("  ") == []
    assert registry.query_terms("") == []
    print("  ok  normalise lowercases; query_terms splits on spaces and commas")


def test_blank_fields_never_score():
    """An empty cell must contribute nothing, in either direction.

    Scoring a blank as a mismatch would push otherwise good records down.
    """
    record = {"name": "Metformin 500mg", "generic": "", "notes": ""}

    score, fields = registry.match_score(
        record, ["metformin"], registry.FIELD_WEIGHTS["medicines"])

    assert fields == ["name"], fields
    assert score == 5, score

    blank_only = {"name": "", "generic": "", "category": ""}
    score2, fields2 = registry.match_score(blank_only, ["anything"], {})
    assert score2 == 0, score2
    assert fields2 == []
    print("  ok  blank fields are skipped, never counted as mismatch")


def test_id_fields_never_score():
    """Keys are not searchable content."""
    record = {"patient_id": "P-0001", "name": "Aarav Sharma"}

    score, fields = registry.match_score(record, ["p-0001"], {})
    assert fields == [], fields
    assert score == 0, score
    print("  ok  id fields excluded from matching")


def test_each_field_contributes_once():
    """A field matching two terms still scores only its own weight."""
    record = {"name": "metformin", "generic": "metformin hcl"}

    score, fields = registry.match_score(
        record, ["metformin", "name"], registry.FIELD_WEIGHTS["medicines"])

    assert fields == ["name", "generic"], fields
    assert score == 5 + 4, score
    print("  ok  field matching several terms still scores once")


def test_spec_example_metformin_diabetes():
    """The worked example from spec 6.1.

    Query "metformin diabetes" must rank the two Metformin rows above a
    glucometer that only matches on category.
    """
    medicines = load("medicines")

    results = registry.search_records(medicines, "metformin diabetes", "medicines")

    assert len(results) >= 2, results
    assert results[0]["name"].startswith("Metformin"), results[0]["name"]
    assert results[1]["name"].startswith("Metformin"), results[1]["name"]

    for r in results[:2]:
        assert "name" in r["matched_fields"], r

    glucometer = [r for r in results if "Glucometer" in r["name"]]
    if glucometer:
        assert results.index(glucometer[0]) > 1, "glucometer outranked Metformin"

    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True), scores
    print(f"  ok  'metformin diabetes' -> {[r['name'][:22] for r in results[:3]]}")


def test_weak_matches_are_returned_not_hidden():
    """A single low weight hit still comes back, sorted last."""
    medicines = load("medicines")

    results = registry.search_records(medicines, "refrigerated", "medicines")

    assert len(results) >= 1, "expected the refrigerated insulin row"
    assert results[0]["name"].startswith("Insulin"), results[0]["name"]
    assert results[0]["score"] == 1, results[0]["score"]
    print("  ok  weak single-field match returned at score 1, not dropped")


def test_no_matches_returns_empty_list():
    """Zero matches is an empty list, not an exception."""
    for record_type in ("medicines", "stores", "patients"):
        records = load(record_type)
        assert registry.search_records(records, "zzzznothing", record_type) == []

    print("  ok  nonsense query returns [] for all three registries")


def test_blank_query_returns_empty_list():
    """Empty query is handled by the caller as a 400, but must not crash."""
    medicines = load("medicines")

    assert registry.search_records(medicines, "", "medicines") == []
    assert registry.search_records(medicines, "   ", "medicines") == []
    assert registry.search_records(medicines, None, "medicines") == []
    print("  ok  blank query returns [] rather than matching everything")


def test_store_search_by_area():
    """Store search matches on area and city."""
    stores = load("stores")

    results = registry.search_records(stores, "bengaluru", "stores")

    assert len(results) >= 2, results
    for r in results:
        assert r["city"] == "Bengaluru", r
    print(f"  ok  store search 'bengaluru' -> {len(results)} matches")


def test_patient_search_tolerates_blank_blood_group():
    """P-0006 has no blood group and must still be findable by name."""
    patients = load("patients")

    by_name = registry.search_records(patients, "sneha", "patients")
    assert len(by_name) == 1, by_name
    assert by_name[0]["patient_id"] == "P-0006", by_name[0]
    assert by_name[0]["blood_group"] == "", repr(by_name[0]["blood_group"])

    by_bg = registry.search_records(patients, "A-", "patients")
    assert [r["patient_id"] for r in by_bg] == ["P-0007"], by_bg
    print("  ok  patient with blank blood group searchable by name")


def test_stock_set_skips_blank():
    """A blank stock cell means not recorded, so the store is skipped."""
    blank = {"store_id": "S-06", "stock_csv": ""}
    assert registry.stock_set_for(blank) == set()

    filled = {"store_id": "S-01", "stock_csv": "M-01|M-03"}
    assert registry.stock_set_for(filled) == {"M-01", "M-03"}
    print("  ok  blank stock_csv gives an empty set")


def test_stores_with_medicine():
    """Cross lookup finds every store stocking a matching medicine.

    "Metformin" resolves to two catalogue rows, M-03 and M-04, because both
    have generic Metformin. Four stores stock one or the other. The
    expectation is derived from the data rather than hardcoded, so editing
    the seed files cannot make this test lie.
    """
    medicines = load("medicines")
    stores = load("stores")

    wanted = {m["medicine_id"] for m in medicines
              if registry.normalise("Metformin") in registry.normalise(m["name"])
              or registry.normalise("Metformin") in registry.normalise(m["generic"])}
    expected = sorted(s["store_id"] for s in stores
                      if registry.stock_set_for(s) & wanted)

    found = registry.stores_with_medicine("Metformin", medicines, stores)

    assert len(wanted) == 2, f"expected 2 Metformin rows, got {sorted(wanted)}"
    assert sorted(s["store_id"] for s in found) == expected, (
        [s["name"] for s in found], expected)
    assert len(found) >= 2, [s["name"] for s in found]
    print(f"  ok  Metformin stocked by {[s['name'] for s in found]}")


def test_stores_with_medicine_skips_unrecorded_store():
    """S-06 has blank stock and must never appear."""
    medicines = load("medicines")
    stores = load("stores")

    every = registry.stores_with_medicine("Paracetamol", medicines, stores)

    assert all(s["stock_csv"] for s in every), "a blank-stock store matched"
    assert len(every) >= 3, [s["name"] for s in every]
    print(f"  ok  Paracetamol stocked by {len(every)} stores, none with blank stock")


def test_stores_with_medicine_unknown_name():
    """An unknown medicine returns nothing rather than everything."""
    medicines = load("medicines")
    stores = load("stores")

    assert registry.stores_with_medicine("Aspirin", medicines, stores) == []
    assert registry.stores_with_medicine("", medicines, stores) == []
    print("  ok  unknown or empty medicine name returns []")


def test_medicines_for_disease():
    """A disease's medication maps back to catalogue rows."""
    medicines = load("medicines")
    diseases = load("diseases")

    found = registry.medicines_for_disease("Type 2 Diabetes", medicines, diseases)

    assert len(found) == 2, [m["name"] for m in found]
    assert all(m["generic"] == "Metformin" for m in found), found
    print(f"  ok  Type 2 Diabetes -> {[m['name'] for m in found]}")


def test_validate_accepts_good_payload():
    """A clean record validates with no errors."""
    cleaned, errors = registry.validate_record("patients", {
        "name": "Aarav Sharma", "age": "34", "gender": "male",
        "blood_group": "O+", "city": "Bengaluru",
    })

    assert errors == [], errors
    assert cleaned["name"] == "Aarav Sharma"
    print("  ok  clean patient payload passes validation")


def test_validate_reports_all_problems_at_once():
    """Every bad field is reported in one call, not one per round trip."""
    cleaned, errors = registry.validate_record("patients", {
        "name": "", "age": "old", "gender": "maybe", "blood_group": "Z+",
    })

    joined = " | ".join(errors)
    assert len(errors) >= 4, errors
    assert "name is required" in joined, joined
    assert "age must be a number" in joined, joined
    assert "blood_group" in joined, joined
    assert "gender" in joined, joined
    print(f"  ok  {len(errors)} problems reported in one call")


def test_validate_allows_optional_blanks():
    """Optional fields may be blank; that is not an error."""
    cleaned, errors = registry.validate_record("patients", {"name": "New Patient"})

    assert errors == [], errors
    assert cleaned.get("blood_group", "") == ""
    assert cleaned.get("age", "") == ""
    print("  ok  minimal patient with only a name validates")


def test_validate_medicine_flags():
    """otc and rx_required must be yes or no."""
    _, errors = registry.validate_record("medicines", {
        "name": "Test", "otc": "maybe", "rx_required": "perhaps",
    })

    joined = " | ".join(errors)
    assert "otc must be yes or no" in joined, joined
    assert "rx_required must be yes or no" in joined, joined
    print("  ok  medicine yes/no flags validated")


def test_validate_store_stock_ids():
    """stock_csv must contain medicine ids in M-nn form."""
    _, errors = registry.validate_record("stores", {
        "name": "Test Store", "stock_csv": "M-01|banana",
    })

    assert any("M-01" in e for e in errors), errors

    _, ok_errors = registry.validate_record("stores", {
        "name": "Test Store", "stock_csv": "M-01|M-03",
    })
    assert ok_errors == [], ok_errors
    print("  ok  stock_csv validated as medicine ids")


def test_validate_coerces_types():
    """Numbers and lists are coerced so the caller need not pre-format."""
    cleaned, errors = registry.validate_record("stores", {
        "name": "Test Store", "rating": 4.5,
        "stock_csv": ["M-01", "M-03", " M-05 "],
    })

    assert errors == [], errors
    assert cleaned["rating"] == "4.5", cleaned["rating"]
    assert cleaned["stock_csv"] == "M-01|M-03|M-05", cleaned["stock_csv"]

    assert registry.validate_record("patients", {"name": None})[0]["name"] == ""
    print("  ok  numbers coerced to str, lists joined with pipes")


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"running {len(tests)} registry tests\n")

    failures = []

    for fn in tests:
        try:
            fn()
        except AssertionError as e:
            failures.append(fn.__name__)
            print(f"  FAIL  {fn.__name__}: {e}")
        except Exception as e:
            failures.append(fn.__name__)
            print(f"  ERROR {fn.__name__}: {type(e).__name__}: {e}")

    print()
    if failures:
        print(f"{len(failures)} of {len(tests)} failed: {', '.join(failures)}")
        return 1

    print(f"all {len(tests)} registry tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())