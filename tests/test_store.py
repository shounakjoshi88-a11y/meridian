"""Tests for store.py and models.py. Plain asserts, no pytest.

Run from the project root:  python tests/test_store.py

Every test that writes runs inside a rollback block, so the seed CSVs are
restored afterwards and the suite is safe to run repeatedly.
"""

import os
import shutil
import sys

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

import store  # noqa: E402
from models import Patient, Visit  # noqa: E402

SNAPSHOTS = {}


def rollback(*record_types):
    """Restore registry files after a test writes to them."""
    class _Block:
        def __enter__(self):
            if not SNAPSHOTS:
                for record_type in store.RECORDS:
                    with open(store.path_for(record_type), "r", newline="") as f:
                        SNAPSHOTS[record_type] = f.read()
            return self

        def __exit__(self, *exc):
            for record_type, text in SNAPSHOTS.items():
                with open(store.path_for(record_type), "w", newline="") as f:
                    f.write(text)
            SNAPSHOTS.clear()
            return False

    return _Block()


def test_ensure_csv_does_not_clobber():
    """ensure_csv must never truncate an existing file."""
    before = os.path.getsize("data/patients.csv")

    assert store.ensure_csv("patients") is False
    assert os.path.getsize("data/patients.csv") == before, "file was truncated"
    print("  ok  ensure_csv leaves an existing file alone")


def test_next_id_increments():
    """next_id reads existing ids and returns the next free one."""
    with rollback():
        assert store.next_id("patients", "P-") == "P-0009", store.next_id("patients", "P-")
        assert store.next_id("visits", "V-") == "V-0013"
        assert store.next_id("medicines", "M-") == "M-0021"
        assert store.next_id("stores", "S-") == "S-0007"
    print("  ok  next_id returns P-0009, V-0013, M-0021, S-0007")


def test_next_id_after_delete_reuses_the_gap():
    """Deleting the highest row means the id is handed out again."""
    with rollback():
        new_id = store.next_id("patients", "P-")
        store.append_row("patients", {"patient_id": new_id, "name": "Temp"})

        assert store.next_id("patients", "P-") == "P-0010"
        store.delete_row("patients", "patient_id", new_id)
        assert store.next_id("patients", "P-") == new_id
    print("  ok  next_id tracks the highest id, not a row count")


def test_append_and_read_round_trip():
    """A patient survives the write and read cycle unchanged."""
    with rollback():
        patient = Patient("P-9001", "Round Trip", "30", "female", "",
                          "O+", "Area", "City", "2026-05-01", "note")
        store.append_row("patients", dict(zip(Patient.FIELDS, patient.to_row())))

        found = store.get_by_id("patients", "P-9001")

        assert found is not None, "row not found after append"
        assert found["name"] == "Round Trip"
        assert found["phone"] == "", repr(found["phone"])
        assert Patient.from_row(found).to_row() == patient.to_row()
    print("  ok  patient round trips through CSV unchanged, blanks preserved")


def test_append_handles_missing_trailing_newline():
    """A file not ending in a newline must not corrupt the appended row.

    Without the guard, the new row is joined onto the last one and both
    records are lost in a single malformed line.
    """
    path = "data/patients.csv"

    with open(path, "rb") as f:
        original = f.read()

    stripped = original.rstrip(b"\n")

    with open(path, "wb") as f:
        f.write(stripped)

    try:
        with rollback():
            new_id = store.next_id("patients", "P-")
            store.append_row("patients", {"patient_id": new_id, "name": "No Newline"})

            found = store.get_by_id("patients", new_id)
            assert found is not None, "append produced an unreadable row"
            assert found["name"] == "No Newline"

            records, skipped = store.read_all("patients")
            assert skipped == [], f"malformed rows appeared: {skipped}"
            assert len(records) == 9, len(records)
    finally:
        with open(path, "wb") as f:
            f.write(original)

    print("  ok  append repairs a missing trailing newline instead of merging rows")


def test_read_all_reports_short_rows():
    """A row with too few fields must be skipped, not silently blanked.

    DictReader pads a short row with None rather than omitting the key, so
    a naive check for missing keys never fires. The trailing field would
    quietly become "" and the record would look valid with data lost.
    """
    path = "data/patients.csv"

    with open(path, "r", newline="") as f:
        original = f.read()

    # Ten columns declared, only eight supplied.
    with open(path, "a", newline="") as f:
        f.write("P-9003,Short Row,30,male,9845012399,O+,Area\n")

    try:
        records, skipped = store.read_all("patients")

        assert len(skipped) == 1, skipped
        assert "too few fields" in skipped[0]["reason"], skipped[0]
        assert "city" in skipped[0]["reason"] or "registered_on" in \
            skipped[0]["reason"], skipped[0]

        assert all(r["patient_id"] != "P-9003" for r in records), \
            "short row was accepted"
        assert len(records) == 8, len(records)
    finally:
        with open(path, "w", newline="") as f:
            f.write(original)

    print("  ok  short row is detected and skipped, not padded with blanks")


def test_read_all_reports_malformed_rows():
    """A row with too many fields is skipped and reported, not hidden."""
    path = "data/patients.csv"

    with open(path, "r", newline="") as f:
        original = f.read()

    with open(path, "a", newline="") as f:
        f.write("P-9002,Bad Row,30,male,123,O+,Area,City,2026-05-01,note,EXTRA\n")

    try:
        records, skipped = store.read_all("patients")

        assert len(skipped) == 1, skipped
        assert "too many fields" in skipped[0]["reason"], skipped[0]
        assert all(r["patient_id"] != "P-9002" for r in records)
    finally:
        with open(path, "w", newline="") as f:
            f.write(original)

    print("  ok  malformed row is skipped and reported, not silently dropped")


def test_read_all_handles_blank_cells():
    """A blank cell reads back as an empty string, never a sentinel."""
    records, _ = store.read_all("patients")

    sneha = [r for r in records if r["patient_id"] == "P-0006"][0]
    assert sneha["blood_group"] == "", repr(sneha["blood_group"])
    assert sneha["notes"] == "Blood group not recorded"

    for record in records:
        for value in record.values():
            assert value is not None, record
    print("  ok  blank cells read as empty strings throughout")


def test_visits_for_patient_sorted():
    """Visit history comes back in date order."""
    visits = store.visits_for("P-0003")

    dates = [v["visit_date"] for v in visits]
    assert dates == sorted(dates), dates
    assert len(visits) == 3, len(visits)
    print(f"  ok  P-0003 visit history sorted: {dates}")


def test_visits_for_unknown_patient_is_empty():
    assert store.visits_for("P-9999") == []
    print("  ok  unknown patient has an empty visit history")


def test_get_by_id_returns_none_when_missing():
    assert store.get_by_id("patients", "P-9999") is None
    assert store.get_by_id("diseases", "D-99") is None
    print("  ok  get_by_id returns None for a missing id")


def test_update_row_changes_only_named_fields():
    """update_row rewrites the file but leaves other fields untouched."""
    with rollback():
        updated = store.update_row("patients", "patient_id", "P-0001",
                                   {"city": "Chennai"})

        assert updated is not None
        assert updated["city"] == "Chennai"
        assert updated["name"] == "Aarav Sharma", "name was clobbered"
        assert updated["blood_group"] == "O+", "blood group was clobbered"

        again = store.update_row("patients", "patient_id", "P-0001",
                                 {"city": "Pune"})
        assert again["city"] == "Pune", "second update failed"
        assert store.count_records("patients") == 8, "row count changed"
    print("  ok  update_row changes one field, row count stays 8")


def test_update_row_rejects_id_change():
    """The id field itself must not be writable."""
    with rollback():
        result = store.update_row("patients", "patient_id", "P-0001",
                                  {"patient_id": "P-7777", "city": "Pune"})

        assert result["patient_id"] == "P-0001", "id was changed"
    print("  ok  update_row refuses to change the id field")


def test_update_row_unknown_returns_none():
    assert store.update_row("patients", "patient_id", "P-9999",
                            {"city": "X"}) is None
    print("  ok  update_row on a missing id returns None")


def test_delete_row_reports_whether_it_removed_anything():
    """Deleting twice must not silently succeed the second time."""
    with rollback():
        assert store.delete_row("patients", "patient_id", "P-9999") is False
        assert store.count_records("patients") == 8

        assert store.delete_row("patients", "patient_id", "P-0008") is True
        assert store.count_records("patients") == 7
        assert store.delete_row("patients", "patient_id", "P-0008") is False
    print("  ok  delete_row returns True then False for a repeat delete")


def test_backup_copies_only_the_registries():
    """Backups must not sweep in the research datasets.

    data/datasets/ holds files whose names collide with registry files, so
    flattening everything into one folder silently overwrites one with
    the other.
    """
    shutil.rmtree(store.BACKUP_DIR, ignore_errors=True)

    written = store.backup_all()

    names = sorted(os.path.basename(p) for p in written)

    assert len(written) == 5, names
    assert names == ["diseases.csv", "medicines.csv", "patients.csv",
                     "stores.csv", "visits.csv"], names

    for path in written:
        assert os.path.exists(path), path
        source = os.path.join(store.DATA_DIR, os.path.basename(path))
        with open(source, "rb") as a, open(path, "rb") as b:
            assert a.read() == b.read(), f"{path} differs from source"

    shutil.rmtree(store.BACKUP_DIR, ignore_errors=True)
    print("  ok  backup copies exactly the 5 registries, byte identical")


def test_backup_twice_does_not_collide():
    """Two backups in the same second must not overwrite each other."""
    shutil.rmtree(store.BACKUP_DIR, ignore_errors=True)

    first = store.backup_all()
    second = store.backup_all()

    folders = os.listdir(store.BACKUP_DIR)
    assert len(folders) == 2, folders

    for a, b in zip(first, second):
        assert a != b, f"{a} and {b} share a folder"

    shutil.rmtree(store.BACKUP_DIR, ignore_errors=True)
    print("  ok  consecutive backups land in separate folders")


def test_patient_model_defaults():
    """Unfilled fields default to empty strings, never sentinels."""
    p = Patient("P-1", "Name")

    assert p.age == ""
    assert p.blood_group == ""
    assert p.notes == ""

    for value in p.to_row():
        assert value == "" or value == "P-1" or value == "Name", value
    print("  ok  Patient defaults every optional field to empty string")


def test_patient_summary():
    """summary() omits the parts that are not filled in."""
    assert Patient("P-1", "A", age="34").summary() == "P-1 - A - age 34"
    assert Patient("P-1", "B").summary() == "P-1 - B"
    assert Patient("P-1", "A", age="34", city="Pune").summary() == \
        "P-1 - A - age 34 - Pune"
    print("  ok  Patient.summary omits unfilled fields")


def test_visit_symptom_set():
    """Visit.symptom_set splits pipes and normalises case."""
    v = Visit("V-1", "P-1", "2026-01-01", " Fever | cough |FEVER")

    assert v.symptom_set() == {"fever", "cough"}, v.symptom_set()
    assert Visit("V-2", "P-1", "2026-01-01", "").symptom_set() == set()
    assert Visit("V-3", "P-1", "2026-01-01").symptom_set() == set()
    print("  ok  Visit.symptom_set normalises, de-duplicates, handles blanks")


def test_model_row_order_matches_csv_header():
    """to_row must line up with the field order DictReader produces."""
    assert Patient.FIELDS == store.PATIENT_FIELDS, "Patient.FIELDS drifted"
    assert Visit.FIELDS == store.VISIT_FIELDS, "Visit.FIELDS drifted"

    p = Patient("P-1", "N")
    row = p.to_row()

    for field, value in zip(Patient.FIELDS, row):
        assert p.to_dict()[field] == value, field
    print("  ok  model FIELDS match the store's, to_row aligns with to_dict")


def test_count_records_matches_seeds():
    """Row counts are what the integrity checker expects."""
    counts = {t: store.count_records(t) for t in store.RECORDS}

    assert counts == {"patients": 8, "visits": 12, "medicines": 20,
                      "stores": 6, "diseases": 15}, counts
    print(f"  ok  seed row counts {counts}")


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"running {len(tests)} store tests\n")

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

    print(f"all {len(tests)} store tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())