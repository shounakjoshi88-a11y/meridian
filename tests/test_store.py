"""Tests for store.py and models.py. Plain asserts, no pytest.

Run from the project root:  python tests/test_store.py

Every test that writes runs inside a rollback block, so the seed CSVs are
restored afterwards and the suite is safe to run repeatedly.
"""

import csv
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


def highest_id(record_type, id_field, prefix):
    """The largest numeric id suffix currently in a registry.

    next_id is expected to be this plus one. Derived rather than written
    down, because the registries are generated: the answer moves whenever
    scripts/build_synthetic_registries.py is re-run, and a pinned literal
    would only prove the fixture had not been regenerated.
    """
    _filename, _fields, _id_field = store.RECORDS[record_type]
    best = 0

    for row in store.read_all(record_type)[0]:
        digits = row[id_field].partition(prefix)[2]

        if digits.isdigit():
            best = max(best, int(digits))

    return best


def test_next_id_increments():
    """next_id reads existing ids and returns the next free one."""
    with rollback():
        for record_type, prefix in (("patients", "P-"), ("visits", "V-"),
                                    ("medicines", "M-"), ("stores", "S-"),
                                    ("hospitals", "H-"), ("doctors", "D-")):
            id_field = store.RECORDS[record_type][2]
            highest = highest_id(record_type, id_field, prefix)

            got = store.next_id(record_type, prefix)

            assert got.startswith(prefix), f"{record_type}: {got} lost its prefix"
            assert int(got.partition(prefix)[2]) == highest + 1, (
                f"{record_type}: next_id is {got}, expected one past "
                f"{highest}")

    print("  ok  next_id is one past the highest id in every registry")


def test_next_id_after_delete_reuses_the_gap():
    """Deleting the highest row means the id is handed out again."""
    with rollback():
        first = store.next_id("patients", "P-")
        store.append_row("patients", {"patient_id": first, "name": "Temp"})

        after_append = store.next_id("patients", "P-")
        assert after_append != first, "next_id did not move past the new row"
        assert int(after_append.partition("P-")[2]) == \
            int(first.partition("P-")[2]) + 1, (first, after_append)

        store.delete_row("patients", "patient_id", first)
        assert store.next_id("patients", "P-") == first
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

    baseline = store.count_records("patients")

    try:
        with rollback():
            new_id = store.next_id("patients", "P-")
            store.append_row("patients", {"patient_id": new_id, "name": "No Newline"})

            found = store.get_by_id("patients", new_id)
            assert found is not None, "append produced an unreadable row"
            assert found["name"] == "No Newline"

            records, skipped = store.read_all("patients")
            assert skipped == [], f"malformed rows appeared: {skipped}"
            assert len(records) == baseline + 1, (len(records), baseline)
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

    baseline = store.count_records("patients")

    # Sixteen columns declared, only seven supplied.
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
        assert len(records) == baseline, (len(records), baseline)
    finally:
        with open(path, "w", newline="") as f:
            f.write(original)

    print("  ok  short row is detected and skipped, not padded with blanks")


def test_read_all_reports_malformed_rows():
    """A row with too many fields is skipped and reported, not hidden."""
    path = "data/patients.csv"

    with open(path, "r", newline="") as f:
        original = f.read()

    # Built from the field list rather than hand counted, so widening the
    # schema cannot quietly turn this into a short-row test.
    values = ["P-9002", "Bad Row", "30", "male", "123", "x@example.in",
              "O+", "Somewhere", "Nagpur", "440001", "Nagpur",
              "Maharashtra", "Kin", "9999999999", "2026-05-01", "note",
              "EXTRA"]
    assert len(values) == len(store.PATIENT_FIELDS) + 1, len(values)

    with open(path, "a", newline="") as f:
        f.write(",".join(values) + "\n")

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

    dates = [v["scheduled_date"] for v in visits]
    assert dates == sorted(dates), dates
    assert len(visits) == 3, len(visits)
    assert all(v["patient_id"] == "P-0003" for v in visits), visits
    print(f"  ok  P-0003 visit history sorted: {dates}")


def test_visits_for_unknown_patient_is_empty():
    assert store.visits_for("P-9999") == []
    print("  ok  unknown patient has an empty visit history")


def test_get_by_id_returns_none_when_missing():
    assert store.get_by_id("patients", "P-9999") is None
    assert store.get_by_id("diseases", "D-9999") is None
    print("  ok  get_by_id returns None for a missing id")


def test_update_row_changes_only_named_fields():
    """update_row rewrites the file but leaves other fields untouched."""
    baseline = store.count_records("patients")

    with rollback():
        updated = store.update_row("patients", "patient_id", "P-0001",
                                   {"city": "Chennai"})

        assert updated is not None
        assert updated["city"] == "Chennai"
        assert updated["name"] == "Aarav Sharma", "name was clobbered"
        assert updated["blood_group"] == "O+", "blood group was clobbered"

        again = store.update_row("patients", "patient_id", "P-0001",
                                 {"city": "Pune"})
        assert again is not None, "second update failed"
        assert again["city"] == "Pune", "second update failed"
        assert store.count_records("patients") == baseline, "row count changed"
    print(f"  ok  update_row changes one field, row count stays {baseline}")


def test_update_row_rejects_id_change():
    """The id field itself must not be writable."""
    with rollback():
        result = store.update_row("patients", "patient_id", "P-0001",
                                  {"patient_id": "P-7777", "city": "Pune"})

        assert result is not None, "update returned nothing"
        assert result["patient_id"] == "P-0001", "id was changed"
    print("  ok  update_row refuses to change the id field")


def test_update_row_unknown_returns_none():
    assert store.update_row("patients", "patient_id", "P-9999",
                            {"city": "X"}) is None
    print("  ok  update_row on a missing id returns None")


def test_delete_row_reports_whether_it_removed_anything():
    """Deleting twice must not silently succeed the second time."""
    baseline = store.count_records("patients")

    with rollback():
        assert store.delete_row("patients", "patient_id", "P-9999") is False
        assert store.count_records("patients") == baseline

        assert store.delete_row("patients", "patient_id", "P-0008") is True
        assert store.count_records("patients") == baseline - 1
        assert store.delete_row("patients", "patient_id", "P-0008") is False
    print("  ok  delete_row returns True then False for a repeat delete")


def test_backup_copies_only_the_registries():
    """Backups must not sweep in the research datasets.

    data/datasets/ holds files whose names collide with registry files, so
    flattening everything into one folder silently overwrites one with
    the other.

    The expected list is derived from RECORDS rather than written out, so
    adding a registry cannot leave this asserting a stale count.
    """
    shutil.rmtree(store.BACKUP_DIR, ignore_errors=True)

    written = store.backup_all()

    names = sorted(os.path.basename(p) for p in written)

    expected = sorted(filename for filename, _f, _i in store.RECORDS.values())

    assert len(written) == len(store.RECORDS), names
    assert names == expected, names

    for path in written:
        assert os.path.exists(path), path
        assert os.path.getsize(path) > 0, f"{path} was copied empty"
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
    v = Visit("V-1", "P-1", symptoms=" Fever | cough |FEVER")

    assert v.symptom_set() == {"fever", "cough"}, v.symptom_set()
    assert Visit("V-2", "P-1", symptoms="").symptom_set() == set()
    assert Visit("V-3", "P-1").symptom_set() == set()
    print("  ok  Visit.symptom_set normalises, de-duplicates, handles blanks")


def test_visit_links_doctor_and_hospital():
    """A visit carries the doctor and hospital it happened at."""
    v = Visit("V-1", "P-1", doctor_id="D-0002", hospital_id="H-0001",
              scheduled_date="2026-05-04", status="completed")

    assert v.doctor_id == "D-0002"
    assert v.hospital_id == "H-0001"
    assert v.scheduled_date == "2026-05-04"
    assert v.status == "completed"
    print("  ok  Visit carries doctor_id, hospital_id and status")


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
    """Row counts are what the integrity checker expects.

    Generated registries are checked against a floor rather than an exact
    number, because they are rebuilt from a seed by
    scripts/build_synthetic_registries.py and the totals move whenever
    that seed or a target changes. Pinning 600 would mean editing this
    test on every regeneration for no extra safety: the generator states
    its own totals, and the floor still catches a registry that has been
    emptied or truncated by accident.

    medicines.csv is the exception. It is written by hand and not
    generated, so an exact count is the honest assertion.
    """
    counts = {t: store.count_records(t) for t in store.RECORDS}

    # Hand-written, so exact.
    assert counts["medicines"] == 20, counts

    # Generated by scripts/build_synthetic_registries.py, so floors.
    for record_type in ("patients", "visits", "stores", "hospitals",
                        "doctors"):
        assert counts[record_type] >= 500, counts

    # The triage knowledge base, generated from ICD-10-CM.
    assert counts["diseases"] >= 90, counts

    # Generated from the Human Phenotype Ontology.
    assert counts["rare_conditions"] >= 10000, counts
    assert counts["hpo_symptoms"] >= 10000, counts

    print(f"  ok  seed row counts {counts}")


def test_declared_fields_match_every_csv_header():
    """Each registry's declared fields must equal its CSV header exactly.

    read_all keys rows off the declared field list, so a column the list
    omits is not an error, it is data that quietly disappears. That is how
    icd10_code and symptom_source went missing from every disease row after
    the knowledge base gained them: nothing failed, the fields were just
    gone.
    """
    for record_type, (filename, fields, _id_field) in store.RECORDS.items():
        path = os.path.join(store.DATA_DIR, filename)

        with open(path, newline="", encoding="utf-8") as f:
            header = next(csv.reader(f))

        assert header == fields, (
            f"{filename} header does not match {record_type} fields\n"
            f"  header: {header}\n"
            f"  declared: {fields}\n"
            f"  only in header: {[h for h in header if h not in fields]}\n"
            f"  only in declared: {[x for x in fields if x not in header]}"
        )

    print(f"  ok  all {len(store.RECORDS)} declared field lists match their CSV")


def test_every_registry_ends_with_a_newline():
    """A CSV without a trailing newline loses its last row on append.

    Opening a file in append mode and writing starts at the current end
    of file. If the last line has no newline, the new row is glued onto
    the old one and both become a single malformed record. Four of the
    seven registries were shipped this way before this test existed.
    """
    for record_type, (filename, _fields, _id_field) in store.RECORDS.items():
        path = os.path.join(store.DATA_DIR, filename)

        with open(path, "rb") as f:
            raw = f.read()

        assert raw != b"", f"{record_type} file is empty"
        assert raw.endswith(b"\n"), (
            f"{filename} has no trailing newline; the next append_row "
            f"will corrupt {record_type}"
        )
    print(f"  ok  all {len(store.RECORDS)} registries end with a newline")


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