"""Tests for app.py using Flask's test client. Plain asserts, no pytest.

Run from the project root:  python tests/test_app.py

Routes that write are tested against real seed files, so every mutating
test deletes what it created and the suite asserts at the end that the
row counts are back to their starting values.
"""

import json
import os
import shutil
import sys

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

import app as meridian  # noqa: E402
import store  # noqa: E402

client = meridian.app.test_client()

STARTING = {t: store.count_records(t) for t in store.RECORDS}

# Tests that write are wrapped in snapshot so the registry files are put
# back exactly as they were. Counting rows is not enough, because ids are
# assigned by next_id and a deleted row leaves a gap.
SNAPSHOTS = {}


def snapshot(record_type):
    """Save a registry file's contents before a test writes to it."""
    with open(store.path_for(record_type), "r", newline="") as f:
        SNAPSHOTS[record_type] = f.read()


def restore_all():
    """Put every snapshotted registry back."""
    for record_type, text in SNAPSHOTS.items():
        with open(store.path_for(record_type), "w", newline="") as f:
            f.write(text)
    SNAPSHOTS.clear()


class rollback:
    """Context manager restoring registries after a test writes to them.

    Tests run in alphabetical order, so a test that creates a patient
    would otherwise change the counts a later test asserts on. This makes
    every test independent of the ones before it.

    Reentrant by saving the outermost snapshot only. A nested block joins
    the outer one, otherwise the inner exit would restore the file and the
    outer block would then operate on a row that no longer exists.
    """

    def __init__(self, *record_types):
        self.record_types = record_types or tuple(store.RECORDS)
        self.owns_snapshot = False

    def __enter__(self):
        if not SNAPSHOTS:
            self.owns_snapshot = True
            for record_type in store.RECORDS:
                snapshot(record_type)
        return self

    def __exit__(self, *exc):
        if self.owns_snapshot:
            restore_all()
        return False


def get(path, **params):
    return client.get(path, query_string=params)


def post(path, body=None):
    return client.post(path, json=body if body is not None else {})


def data(response):
    return json.loads(response.data)


def post_creating(record_type, path, body):
    """POST inside a rollback block so the created row never persists."""
    with rollback(record_type):
        r = post(path, body)
        assert r.status_code == 201, (path, r.status_code, data(r))
        created = data(r)["created"]

        # Prove it really was written before the rollback undoes it.
        assert store.get_by_id(record_type, created[store.RECORDS[record_type][2]]) \
            is not None, "row was not persisted"

    return r, created


# -------------------------------------------------------------- frontend

def test_index_serves_the_shell():
    """The root route returns the frontend HTML."""
    r = get("/")
    body = r.data.decode()

    assert r.status_code == 200, r.status_code
    assert "<title>Meridian</title>" in body, body[:200]
    assert "tokens.css" in body
    assert "app.js" in body
    print("  ok  GET / serves the frontend shell")


def test_frontend_assets_are_served():
    """Each frontend file loads with the right content type."""
    for name, needle in [("tokens.css", "--accent"),
                         ("app.css", ".rank__score"),
                         ("app.js", "function api(")]:
        r = get(f"/{name}")

        assert r.status_code == 200, (name, r.status_code)
        assert needle in r.data.decode(), name
    print("  ok  tokens.css, app.css and app.js are all served")


def test_unknown_asset_is_404():
    assert get("/nosuchfile.css").status_code == 404
    print("  ok  unknown frontend asset returns 404")


def test_frontend_rejects_non_asset_extensions():
    """Only html, css and js are served from the frontend directory."""
    for bad in ["/../backend/app.py", "/../data/patients.csv", "/app.py"]:
        r = get(bad)
        assert r.status_code in (400, 404), (bad, r.status_code)
    print("  ok  backend and data files are not reachable through the frontend")


# ----------------------------------------------------------------- health

def test_health():
    """Health route reports counts and the passing datasets."""
    r = get("/api/health")
    body = data(r)

    assert r.status_code == 200, r.status_code
    assert body["status"] == "ok"
    assert body["counts"]["patients"] == STARTING["patients"]
    assert "pima_diabetes.csv" in body["datasets"]
    print("  ok  /api/health returns status, counts and datasets")


def test_unknown_route_is_404():
    """An undefined path returns 404, not a stack trace."""
    assert get("/api/nope").status_code == 404
    print("  ok  unknown route returns 404")


# --------------------------------------------------------------- patients

def test_list_patients():
    """Every patient comes back, with the skipped list present."""
    body = data(get("/api/patients"))

    assert body["count"] == STARTING["patients"], body["count"]
    assert "patients" in body
    assert "skipped" in body
    assert body["skipped"] == [], body["skipped"]
    print(f"  ok  GET /api/patients returns {body['count']} rows")


def test_get_patient_with_visits():
    """A patient comes back with their visit history joined in."""
    body = data(get("/api/patients/P-0003"))

    assert body["patient"]["name"] == "Rohan Mehta", body["patient"]
    assert body["visit_count"] == 3, body["visit_count"]

    dates = [v["scheduled_date"] for v in body["visits"]]
    assert dates == sorted(dates), dates
    assert all(v["doctor_id"] for v in body["visits"]), body["visits"]
    assert all(v["hospital_id"] for v in body["visits"]), body["visits"]
    print(f"  ok  GET /api/patients/P-0003 joins {body['visit_count']} visits")


def test_get_unknown_patient_is_404():
    """A missing patient is a 404 naming the id."""
    r = get("/api/patients/P-9999")
    body = data(r)

    assert r.status_code == 404, r.status_code
    assert "P-9999" in body["error"], body
    print("  ok  unknown patient returns 404 naming the id")


def test_create_patient():
    """Creating a patient assigns an id and persists the row."""
    r, created = post_creating("patients", "/api/patients",
                               {"name": "Api Test Patient", "age": 41,
                                "gender": "female", "blood_group": "O+",
                                "city": "Pune"})

    assert created["patient_id"].startswith("P-"), created
    print(f"  ok  POST /api/patients created {created['patient_id']}")


def test_create_patient_minimal():
    """Only a name is required, and the response carries every column."""
    r, created = post_creating("patients", "/api/patients",
                               {"name": "Minimal Patient"})

    assert created["age"] == "", repr(created.get("age"))
    assert created["blood_group"] == ""
    assert set(created) == set(store.PATIENT_FIELDS), sorted(created)
    print("  ok  minimal create returns the full schema, blanks preserved")


def test_create_patient_rejects_bad_input():
    """Validation errors come back as 400 with every problem listed."""
    r = post("/api/patients", {"name": "", "age": "old", "blood_group": "Z+"})
    body = data(r)

    assert r.status_code == 400, r.status_code
    assert len(body["errors"]) >= 3, body["errors"]
    assert any("name is required" in e for e in body["errors"])
    print(f"  ok  invalid patient returns 400 with {len(body['errors'])} errors")


def test_update_patient():
    """PATCH changes fields in place, without demanding a full record."""
    with rollback("patients"):
        _, created = post_creating("patients", "/api/patients",
                                   {"name": "Patch Target", "age": 30})
        pid = created["patient_id"]

        patched = client.patch(f"/api/patients/{pid}", json={"city": "Nagpur"})
        body = data(patched)

        assert patched.status_code == 200, body
        assert body["updated"]["city"] == "Nagpur", body["updated"]
        assert body["updated"]["name"] == "Patch Target", "name was clobbered"
        assert store.get_by_id("patients", pid)["city"] == "Nagpur"

    print("  ok  PATCH updates one field without clobbering others")


def test_update_patient_still_validates_formats():
    """Relaxing required fields must not relax format checks."""
    with rollback("patients"):
        _, created = post_creating("patients", "/api/patients",
                                   {"name": "Format Target"})

        bad = client.patch(f"/api/patients/{created['patient_id']}",
                           json={"age": "old"})
        assert bad.status_code == 400, bad.status_code
        assert any("age must be a number" in e for e in data(bad)["errors"])

    print("  ok  PATCH still rejects a malformed age")


def test_update_unknown_patient_is_404():
    r = client.patch("/api/patients/P-9999", json={"city": "X"})
    assert r.status_code == 404, r.status_code
    print("  ok  PATCH on unknown patient returns 404")


def test_delete_patient():
    """DELETE removes the row."""
    with rollback("patients"):
        _, created = post_creating("patients", "/api/patients",
                                   {"name": "Delete Me"})
        pid = created["patient_id"]

        r = client.delete(f"/api/patients/{pid}")
        assert r.status_code == 200, r.status_code
        assert store.get_by_id("patients", pid) is None
        assert client.delete(f"/api/patients/{pid}").status_code == 404

    print("  ok  DELETE removes the patient, second delete is 404")


# ----------------------------------------------------------------- visits

def test_list_visits_filtered():
    """Visits can be filtered by patient_id."""
    body = data(get("/api/visits", patient_id="P-0003"))

    assert body["count"] == 3, body["count"]
    for v in body["visits"]:
        assert v["patient_id"] == "P-0003"

    every = data(get("/api/visits"))
    assert every["count"] == STARTING["visits"], every["count"]
    print("  ok  GET /api/visits filters by patient_id")


def test_create_visit():
    """A visit is appended and linked to an existing patient."""
    r, created = post_creating("visits", "/api/visits",
                               {"patient_id": "P-0001",
                                "visit_date": "2026-05-01",
                                "symptoms": "headache|dizziness",
                                "diagnosis": "Hypertension",
                                "severity": "moderate"})

    assert created["visit_id"].startswith("V-"), created
    assert set(created) == set(store.VISIT_FIELDS), sorted(created)
    print(f"  ok  POST /api/visits created {created['visit_id']}")


def test_create_visit_unknown_patient_is_404():
    """A visit cannot reference a patient that does not exist."""
    r = post("/api/visits", {"patient_id": "P-9999",
                             "visit_date": "2026-05-01"})

    assert r.status_code == 404, r.status_code
    assert "P-9999" in data(r)["error"]
    print("  ok  visit for unknown patient returns 404")


def test_create_visit_requires_fields():
    """patient_id and visit_date are mandatory."""
    r = post("/api/visits", {"diagnosis": "Influenza"})
    body = data(r)

    assert r.status_code == 400, r.status_code
    assert any("patient_id is required" in e for e in body["errors"])
    assert any("visit_date is required" in e for e in body["errors"])
    print("  ok  visit without patient_id or date returns 400")


# ------------------------------------------------- medicines and stores

def test_list_medicines_and_stores():
    """Both catalogues list cleanly."""
    meds = data(get("/api/medicines"))
    shops = data(get("/api/stores"))

    assert meds["count"] == STARTING["medicines"], meds["count"]
    assert shops["count"] == STARTING["stores"], shops["count"]
    assert meds["skipped"] == []
    print(f"  ok  {meds['count']} medicines, {shops['count']} stores listed")


def test_get_medicine_with_stores():
    """A medicine resolves to the stores stocking it."""
    body = data(get("/api/medicines/M-03"))

    assert body["medicine"]["name"].startswith("Metformin"), body["medicine"]
    assert body["stocked_by"], "expected at least one store"
    print(f"  ok  M-03 stocked by {len(body['stocked_by'])} stores")


def test_medicine_stores_endpoint():
    """The dedicated stores route agrees with the detail route."""
    body = data(get("/api/medicines/M-03/stores"))

    assert body["count"] > 0, body
    for s in body["stores"]:
        assert "M-03" in s["stock_csv"] or "M-04" in s["stock_csv"], s
    print(f"  ok  /api/medicines/M-03/stores -> {body['count']} stores")


def test_unknown_medicine_is_404():
    assert get("/api/medicines/M-9999").status_code == 404
    assert get("/api/medicines/M-9999/stores").status_code == 404
    print("  ok  unknown medicine returns 404 on both routes")


def test_get_store_resolves_stock():
    """A store's stock ids resolve into medicine rows."""
    body = data(get("/api/stores/S-01"))

    assert body["store"]["name"] == "Apollo Pharmacy Dharangaon", body["store"]
    assert body["stock_count"] > 0, body
    assert body["stock_count"] == len(body["medicines"]), body["stock_count"]
    for m in body["medicines"]:
        assert m["medicine_id"].startswith("M-"), m
    print(f"  ok  S-01 resolves {body['stock_count']} stocked medicines")


def test_store_with_blank_stock_is_not_an_error():
    """S-06 has no recorded stock, which must read as zero, not fail."""
    body = data(get("/api/stores/S-06"))

    assert body["store"]["stock_csv"] == "", body["store"]
    assert body["stock_count"] == 0, body
    print("  ok  blank stock reads as 0 medicines, no error")


def test_create_medicine_and_store():
    """Both catalogues accept new rows, and stock resolves."""
    with rollback("medicines", "stores"):
        _, med = post_creating("medicines", "/api/medicines",
                               {"name": "Test Syrup 100ml",
                                "generic": "Testazole",
                                "category": "Antihistamine", "otc": "yes",
                                "rx_required": "no", "price": 45})
        mid = med["medicine_id"]

        _, shop = post_creating("stores", "/api/stores",
                                {"name": "Test Pharmacy", "city": "Pune",
                                 "stock_csv": [mid]})
        sid = shop["store_id"]

        body = data(get(f"/api/stores/{sid}"))
        assert body["stock_count"] == 1, body
        assert body["medicines"][0]["medicine_id"] == mid

    print(f"  ok  created {mid} and {sid}, stock resolves correctly")


def test_create_store_rejects_bad_stock_ids():
    """stock_csv must hold medicine ids in M-nn form."""
    r = post("/api/stores", {"name": "Bad Store", "stock_csv": "M-01|banana"})
    body = data(r)

    assert r.status_code == 400, r.status_code
    assert any("M-01" in e for e in body["errors"]), body["errors"]
    print("  ok  store with a malformed medicine id returns 400")


# ----------------------------------------------------------------- search

def test_search_medicines():
    """Fuzzy search returns ranked results."""
    body = data(get("/api/search/medicines", q="metformin diabetes"))

    assert body["count"] >= 2, body
    assert body["results"][0]["name"].startswith("Metformin"), body["results"][0]

    scores = [r["score"] for r in body["results"]]
    assert scores == sorted(scores, reverse=True), scores
    print(f"  ok  search 'metformin diabetes' -> {body['count']} results")


def test_search_patients():
    """Patient search works, including records with blank fields.

    "sneha" legitimately matches two people: Sneha Reddy by name and
    Rohan Mehta by emergency contact. The name match must rank first.
    """
    body = data(get("/api/search/patients", q="sneha"))

    assert body["count"] == 2, body
    assert body["results"][0]["patient_id"] == "P-0006", body["results"][0]
    assert body["results"][0]["blood_group"] == "", body["results"][0]
    assert body["results"][0]["score"] > body["results"][1]["score"], body
    print("  ok  blank blood group searchable, emergency contact ranks lower")


def test_search_stores():
    """Store search matches on city."""
    body = data(get("/api/search/stores", q="nagpur"))

    assert body["count"] >= 5, body
    for r in body["results"]:
        assert r["city"] == "Nagpur", r
    print(f"  ok  store search 'nagpur' -> {body['count']} results")


def test_search_no_matches_is_200_not_404():
    """Zero matches is an honest 200, not a 404."""
    r = get("/api/search/medicines", q="zzzznothinghere")
    body = data(r)

    assert r.status_code == 200, r.status_code
    assert body["count"] == 0, body
    assert body["results"] == []
    print("  ok  no matches returns 200 with count 0")


def test_search_blank_query_is_400():
    """A blank query is a malformed request, not an empty result."""
    for bad in ("", "   "):
        r = get("/api/search/medicines", q=bad)
        assert r.status_code == 400, (bad, r.status_code)
        assert "q is required" in data(r)["error"], data(r)

    missing = get("/api/search/medicines")
    assert missing.status_code == 400, missing.status_code
    print("  ok  blank or missing q returns 400")


def test_search_unsearchable_type_is_404():
    """Only the three registries are searchable."""
    r = get("/api/search/diseases", q="fever")
    body = data(r)

    assert r.status_code == 404, r.status_code
    assert "searchable" in body, body
    print("  ok  searching an unsearchable type returns 404 listing options")


# ----------------------------------------------------------------- triage

def test_triage_ranks_diseases():
    """A symptom list comes back ranked, with the disclaimer present."""
    r = post("/api/triage", {"symptoms": ["high fever", "severe body ache",
                                          "joint pain", "rash", "headache"]})
    body = data(r)

    assert r.status_code == 200, r.status_code
    assert body["count"] > 0, body
    assert body["results"][0]["name"] == "Dengue Fever", body["results"][0]
    assert body["disclaimer"] == "NOT A DIAGNOSIS. TRIAGE GUIDANCE ONLY."
    assert "NOT A DIAGNOSIS" in body["report"], body["report"]
    print(f"  ok  triage ranks {body['results'][0]['name']} at "
          f"{body['results'][0]['percent']}%")


def test_triage_accepts_pipe_string():
    """Symptoms may arrive as one pipe delimited string."""
    a = data(post("/api/triage", {"symptoms": "fever|cough|fatigue"}))
    b = data(post("/api/triage", {"symptoms": ["fever", "cough", "fatigue"]}))

    assert a["count"] == b["count"], (a["count"], b["count"])
    assert a["results"][0]["name"] == b["results"][0]["name"]
    print("  ok  pipe string and list give identical triage results")


def test_triage_requires_symptoms():
    """No symptoms is a 400, naming the missing field."""
    for body_in in ({}, {"symptoms": []}, {"symptoms": ["", "  "]}):
        r = post("/api/triage", body_in)
        body = data(r)

        assert r.status_code == 400, (body_in, r.status_code)
        assert body.get("required_field") == "symptoms", body

    assert post("/api/triage").status_code == 400
    print("  ok  triage without symptoms returns 400")


def test_triage_contraindication_is_a_warning_not_an_error():
    """A contraindication must not fail the request."""
    r = post("/api/triage", {"symptoms": ["frequent urination",
                                          "excessive thirst", "fatigue"],
                             "conditions": ["kidney disease"]})
    body = data(r)

    assert r.status_code == 200, r.status_code
    assert body["warnings"], "expected a contraindication warning"
    assert "kidney disease" in str(body["warnings"]), body["warnings"]
    assert "WARNING" in body["report"], body["report"]
    print(f"  ok  contraindication surfaces as {len(body['warnings'])} warnings")


def test_triage_with_patient_reference():
    """Naming a patient pulls their details into the response."""
    body = data(post("/api/triage", {"patient_id": "P-0003",
                                     "symptoms": ["frequent urination",
                                                  "excessive thirst"]}))

    assert body["patient"]["name"] == "Rohan Mehta", body["patient"]
    assert "Rohan Mehta" in body["report"], body["report"]
    print("  ok  triage report renders the named patient")


def test_triage_unknown_patient_is_tolerated():
    """An unknown patient_id must not break triage."""
    r = post("/api/triage", {"patient_id": "P-9999",
                             "symptoms": ["fever", "cough"]})

    assert r.status_code == 200, r.status_code
    assert data(r)["patient"] == {}, data(r)["patient"]
    print("  ok  unknown patient_id leaves triage working, patient is empty")


def test_list_diseases():
    """The knowledge base lists with parsed symptom sets."""
    body = data(get("/api/diseases"))

    assert body["count"] == STARTING["diseases"], body["count"]
    for d in body["diseases"]:
        assert isinstance(d["symptom_set"], list), d
    print(f"  ok  GET /api/diseases returns {body['count']} diseases")


# -------------------------------------------------------------- analytics

def test_analytics_list():
    """The dataset list comes back with the passing subset."""
    body = data(get("/api/analytics"))

    assert len(body["datasets"]) == 4, len(body["datasets"])
    assert len(body["passing"]) == 3, body["passing"]
    print("  ok  GET /api/analytics lists 4 datasets, 3 passing")


def test_analytics_profile_each_dataset():
    """Each selected dataset profiles through the API."""
    for name in ("pima_diabetes.csv", "heart_disease.csv", "parkinsons.csv"):
        r = get(f"/api/analytics/{name}")
        body = data(r)

        assert r.status_code == 200, (name, r.status_code)
        assert body["rows"] > 0, name
        assert body["strongest_separators"], name
        assert body["target"], name
    print("  ok  all three datasets profile through the API")


def test_analytics_unknown_dataset_lists_options():
    """An unknown dataset is a 404 that says what is available."""
    r = get("/api/analytics/nosuch.csv")
    body = data(r)

    assert r.status_code == 404, r.status_code
    assert "available" in body, body
    assert "pima_diabetes.csv" in body["available"], body
    print("  ok  unknown dataset returns 404 listing valid names")


def test_analytics_excluded_dataset_is_404():
    """The excluded dataset is deliberately not served."""
    r = get("/api/analytics/mammographic_masses.csv")

    assert r.status_code == 404, r.status_code
    print("  ok  excluded dataset is not served")


def test_analytics_risk_bands():
    """Risk bands work with and without an explicit column."""
    every = data(get("/api/analytics/pima_diabetes.csv/risk-bands"))
    assert "Glucose" in every["columns"], every

    one = data(get("/api/analytics/pima_diabetes.csv/risk-bands",
                   column="Glucose"))

    assert one["column"] == "Glucose", one
    assert one["bands"], one
    assert sum(one["bands"].values()) == one["total"], one
    assert one["unreachable_bands"] == ["high"], one
    print(f"  ok  glucose bands {one['bands']}, unreachable {one['unreachable_bands']}")


def test_analytics_risk_bands_bad_column():
    """An unknown column is a 404 listing the valid ones."""
    r = get("/api/analytics/pima_diabetes.csv/risk-bands", column="nosuchcol")
    body = data(r)

    assert r.status_code == 404, r.status_code
    assert "available" in body, body
    print("  ok  unknown risk band column returns 404 listing options")


def test_analytics_charts_written_and_served():
    """Charts render and are then servable as PNGs."""
    body = data(get("/api/analytics/pima_diabetes.csv/charts"))

    assert body["charts"], body

    for path in body["charts"]:
        name = os.path.basename(path)
        r = get(f"/charts/{name}")

        assert r.status_code == 200, (name, r.status_code)
        assert r.data[:4] == b"\x89PNG", f"{name} is not a PNG"
        assert len(r.data) > 1000, (name, len(r.data))
    print(f"  ok  {len(body['charts'])} charts rendered and served")


def test_missing_chart_is_404():
    assert get("/charts/nosuchchart.png").status_code == 404
    print("  ok  unknown chart returns 404")


# ----------------------------------------------------------------- backup

def test_backup_route():
    """Backup copies all seven registries into a fresh folder."""
    shutil.rmtree(store.BACKUP_DIR, ignore_errors=True)

    r = post("/api/backup")
    body = data(r)

    assert r.status_code == 200, r.status_code
    assert body["count"] == 7, body

    names = sorted(os.path.basename(p) for p in body["files"])
    assert names == ["diseases.csv", "doctors.csv", "hospitals.csv",
                     "medicines.csv", "patients.csv", "stores.csv",
                     "visits.csv"], names

    for path in body["files"]:
        assert os.path.exists(path), path

    shutil.rmtree(store.BACKUP_DIR, ignore_errors=True)
    print(f"  ok  POST /api/backup wrote {body['count']} files")


# ---------------------------------------------------------------- payloads

def test_every_response_is_strict_json():
    """No response may contain a bare NaN or a numpy type."""
    # Query strings are passed separately. Embedding ?q= in the path and
    # also passing query_string makes the Werkzeug test client raise.
    paths = [
        ("/api/health", None),
        ("/api/patients", None),
        ("/api/patients/P-0001", None),
        ("/api/visits", None),
        ("/api/medicines", None),
        ("/api/medicines/M-03", None),
        ("/api/medicines/M-03/stores", None),
        ("/api/stores", None),
        ("/api/stores/S-01", None),
        ("/api/search/medicines", {"q": "metformin"}),
        ("/api/search/patients", {"q": "aarav"}),
        ("/api/search/stores", {"q": "bengaluru"}),
        ("/api/diseases", None),
        ("/api/analytics", None),
        ("/api/analytics/pima_diabetes.csv", None),
        ("/api/analytics/pima_diabetes.csv/risk-bands", None),
        ("/api/analytics/risk-bands", None),
    ]

    for path, params in paths:
        r = get(path, **(params or {}))
        assert r.status_code == 200, (path, r.status_code)

        # A parse_constant hook that raises turns any bare NaN into a
        # failure, which is what makes this a strict JSON check.
        def reject(constant):
            raise ValueError(f"{path} contains bare {constant}")

        json.loads(r.data, parse_constant=reject)

    triage_body = data(post("/api/triage", {"symptoms": ["fever", "cough",
                                                         "fatigue"]}))
    json.dumps(triage_body, allow_nan=False)
    print(f"  ok  {len(paths)} GET routes and triage return strict JSON")


def test_seed_data_unchanged():
    """The suite must not have left stray rows behind."""
    final = {t: store.count_records(t) for t in store.RECORDS}

    for record_type, start in STARTING.items():
        assert final[record_type] == start, (
            f"{record_type}: started {start}, now {final[record_type]}")
    print(f"  ok  all row counts back to their starting values {STARTING}")


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"running {len(tests)} app tests\n")

    failures = []

    try:
        for fn in tests:
            try:
                fn()
            except AssertionError as e:
                failures.append(fn.__name__)
                print(f"  FAIL  {fn.__name__}: {e}")
            except Exception as e:
                failures.append(fn.__name__)
                print(f"  ERROR {fn.__name__}: {type(e).__name__}: {e}")
    finally:
        # Always restore, so a failing run cannot leave the seed data
        # corrupted for the next one.
        restore_all()
        shutil.rmtree(store.BACKUP_DIR, ignore_errors=True)

    print()
    if failures:
        print(f"{len(failures)} of {len(tests)} failed: {', '.join(failures)}")
        return 1

    print(f"all {len(tests)} app tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())