"""Flask API for Meridian.

Taught concepts: none new in this file. Flask is the only concept added
beyond the lab syllabus and it gets its own explainer in
docs/concepts/flask.md.

Layering rule from the spec: this module routes and nothing else. Every
handler calls functions in store, registry, triage or analytics and
returns their result. No business logic lives here.

Run from the project root:

    python backend/app.py

then the API is on http://127.0.0.1:8000
"""

import os
import sys

from flask import Flask, jsonify, request, send_from_directory

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import analytics
import registry
import store
import triage

# static_folder stays at the default backend/static so generated charts are
# served from /charts/<file>. static_url_path must NOT be "" because that
# makes Flask claim every unmatched path and the frontend route below
# never runs.
app = Flask(__name__)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

SEARCHABLE = ("patients", "medicines", "stores", "hospitals", "doctors",
              "rare_conditions")

# --------------------------------------------------------------- paging
#
# The registries hold 600 patients, 540 doctors and 520 hospitals. Serving
# every row on every page view meant /api/patients answered with 334 KB and
# /api/visits with 1.4 MB, which is the whole registry to draw a screen
# that shows fifty. Pagination is what lets the frontend show a count it
# can trust instead of a number it happened to receive.

PAGE_LIMIT_DEFAULT = 50
PAGE_LIMIT_MAX = 500


def page_args():
    """Read ?limit= and ?offset= as integers, clamped to sane bounds.

    A missing, negative or non-numeric value falls back to the default
    rather than raising, because this is a query string and a bad one
    should still render a page.
    """
    def whole(name, default, ceiling):
        raw = request.args.get(name)
        if raw is None or raw == "":
            return default

        try:
            value = int(raw)
        except ValueError:
            return default

        return max(0, min(value, ceiling))

    return (whole("limit", PAGE_LIMIT_DEFAULT, PAGE_LIMIT_MAX),
            whole("offset", 0, 10 ** 9))


def paged(records, key, skipped=None, facets=None):
    """Slice records to the requested page and report the true total.

    The window is clamped at both ends so an offset past the end returns
    an empty page rather than an error, which is what a user who was on
    page 9 when a record was deleted should see.
    """
    limit, offset = page_args()
    total = len(records)

    window = records[offset:offset + limit]

    body = {
        "count": len(window),
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": offset + len(window) < total,
        key: window,
    }

    if skipped is not None:
        body["skipped"] = skipped

    if facets is not None:
        body["facets"] = facets

    return jsonify(body)



# How many rows a search returns. The rare condition registry holds 11,655
# diseases and a single phrase like "low muscle tone" matches 7,559 of
# them, so returning everything is not an option. The total is reported
# alongside the page so the interface can say "showing 50 of 7,559"
# rather than implying the list is complete.
SEARCH_PAGE_SIZE = 50


def payload():
    """Return the request body as a dict, or an empty dict if absent."""
    return request.get_json(silent=True) or {}


def full_record(record_type, cleaned):
    """Return every column for a record type, blanks filled in.

    A create response must show the whole row, not just the fields the
    caller happened to send. Otherwise a client cannot tell the difference
    between "field is empty" and "field does not exist".
    """
    complete = {}

    for field in store.fields_for(record_type):
        complete[field] = cleaned.get(field, "")

    return complete


def error(message, status=400, **extra):
    """Build a JSON error response."""
    body = {"error": message}
    body.update(extra)
    return jsonify(body), status


# ------------------------------------------------------------- frontend

@app.get("/")
def index():
    """Serve the frontend shell."""
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/<path:filename>")
def frontend_assets(filename):
    """Serve a frontend asset.

    Only three file types are allowed, and the path is resolved and
    checked against the frontend directory so a crafted request cannot
    walk out of it.
    """
    allowed = (".html", ".css", ".js")

    if not filename.endswith(allowed):
        return error(f"{filename} is not a frontend asset", 404)

    target = os.path.normpath(os.path.join(FRONTEND_DIR, filename))

    if not target.startswith(os.path.normpath(FRONTEND_DIR)):
        return error("path outside the frontend directory", 404)

    if not os.path.exists(target):
        return error(f"no asset named {filename}", 404)

    return send_from_directory(FRONTEND_DIR, filename)


# ---------------------------------------------------------------- health

def registry_page(record_type, key, after=None):
    """Read a registry, apply ?flag=, then return one page of it.

    The facet is applied before the window is cut, otherwise total would
    report the size of the page rather than the size of the answer. A flag
    that no registry defines is a 400 rather than a silently ignored
    parameter, because a filter that does nothing is indistinguishable from
    one that matched everything.
    """
    records, skipped = store.read_all(record_type)

    if after is not None:
        after(records)

    flag = request.args.get("flag", "")
    records, available, unknown = store.apply_facet(records, record_type, flag)

    if unknown:
        return error(f"unknown flag {flag!r}", 400,
                     available=[f["flag"] for f in available])

    body = paged(records, key, skipped, available)

    return body



def attach_visit_counts(records):
    """Add visit_count to each patient row, in place.

    The browse list needs it to say who has never been seen without asking
    the reader to open 600 records to find out. Counting here rather than in
    the frontend also means the "no consultation on file" facet and the row
    beside it cannot disagree.
    """
    visits, _ = store.read_all("visits")
    counts = {}

    for visit in visits:
        pid = visit["patient_id"]
        counts[pid] = counts.get(pid, 0) + 1

    for record in records:
        record["visit_count"] = counts.get(record["patient_id"], 0)


@app.get("/api/health")
def health():
    """Report that the API is up, with record counts per registry."""
    counts = {}

    for record_type in store.RECORDS:
        try:
            counts[record_type] = store.count_records(record_type)
        except OSError:
            counts[record_type] = None

    return jsonify({
        "status": "ok",
        "counts": counts,
        "datasets": analytics.passing_datasets(),
    })


# -------------------------------------------------------------- patients

@app.get("/api/patients")
def list_patients():
    """Return one page of patient records, plus the true total."""
    return registry_page("patients", "patients", after=attach_visit_counts)


@app.post("/api/patients")
def create_patient():
    """Add a patient. Only name is required."""
    body = payload()
    cleaned, errors = registry.validate_record("patients", body)

    if errors:
        return error("validation failed", 400, errors=errors)

    cleaned["patient_id"] = store.next_id("patients", "P-")
    cleaned.setdefault("registered_on", "")
    stored = store.append_row("patients", cleaned)

    return jsonify({"created": full_record("patients", stored)}), 201


@app.get("/api/patients/<patient_id>")
def get_patient(patient_id):
    """Return one patient, their visit history, and who they saw.

    Each visit is enriched with its doctor and hospital so the client does
    not have to make three more round trips to render one record.
    """
    record = store.get_by_id("patients", patient_id)

    if record is None:
        return error(f"no patient with id {patient_id}", 404)

    visits = store.visits_for(patient_id)

    doctors, _ = store.read_all("doctors")
    hospitals, _ = store.read_all("hospitals")
    by_doctor = {d["doctor_id"]: d for d in doctors}
    by_hospital = {h["hospital_id"]: h for h in hospitals}

    for visit in visits:
        doctor = by_doctor.get(visit["doctor_id"], {})
        hospital = by_hospital.get(visit["hospital_id"], {})

        visit["doctor"] = {
            "doctor_id": doctor.get("doctor_id", ""),
            "name": doctor.get("name", ""),
            "specialisation": doctor.get("specialisation", ""),
            "qualification": doctor.get("qualification", ""),
            "department": doctor.get("department", ""),
            "room_no": doctor.get("room_no", ""),
            "consultation_fee": doctor.get("consultation_fee", ""),
        }
        visit["hospital"] = {
            "hospital_id": hospital.get("hospital_id", ""),
            "name": hospital.get("name", ""),
            "area": hospital.get("area", ""),
            "city": hospital.get("city", ""),
        }

    return jsonify({
        "patient": record,
        "visit_count": len(visits),
        "visits": visits,
    })


@app.patch("/api/patients/<patient_id>")
def update_patient(patient_id):
    """Change some fields of an existing patient.

    A partial update is not a create, so required-field checks do not
    apply. Sending only a city must not fail because no name was included.
    Field format checks still run, so age="old" is still rejected.
    """
    body = payload()

    if not body:
        return error("no fields to update")

    cleaned, errors = registry.validate_record("patients", body,
                                               require_required=False)

    if errors:
        return error("validation failed", 400, errors=errors)

    cleaned.pop("patient_id", None)

    if not cleaned:
        return error("no updatable fields supplied")

    updated = store.update_row("patients", "patient_id", patient_id, cleaned)

    if updated is None:
        return error(f"no patient with id {patient_id}", 404)

    return jsonify({"updated": updated})


@app.delete("/api/patients/<patient_id>")
def delete_patient(patient_id):
    """Remove a patient row."""
    if not store.delete_row("patients", "patient_id", patient_id):
        return error(f"no patient with id {patient_id}", 404)

    return jsonify({"deleted": patient_id})


# ---------------------------------------------------------------- visits

@app.get("/api/visits")
def list_visits():
    """Return visits, optionally filtered by patient_id."""
    records, skipped = store.read_all("visits")

    patient_id = request.args.get("patient_id")
    if patient_id:
        records = [r for r in records if r["patient_id"] == patient_id]

    return paged(records, "visits", skipped)


@app.post("/api/visits")
def create_visit():
    """Append a visit. Requires patient_id and visit_date."""
    body = payload()
    cleaned, errors = registry.validate_record("visits", body)

    for field in ("patient_id", "visit_date"):
        if not cleaned.get(field, ""):
            errors.append(f"{field} is required")

    if errors:
        return error("validation failed", 400, errors=errors)

    patient = store.get_by_id("patients", cleaned["patient_id"])
    if patient is None:
        return error(f"no patient with id {cleaned['patient_id']}", 404)

    cleaned["visit_id"] = store.next_id("visits", "V-")
    stored = store.append_row("visits", cleaned)

    return jsonify({"created": full_record("visits", stored)}), 201


# ------------------------------------------------------------- medicines

@app.get("/api/medicines")
def list_medicines():
    """Return one page of the medicine catalogue."""
    return registry_page("medicines", "medicines")


@app.post("/api/medicines")
def create_medicine():
    """Add a medicine to the catalogue."""
    body = payload()
    cleaned, errors = registry.validate_record("medicines", body)

    if errors:
        return error("validation failed", 400, errors=errors)

    cleaned["medicine_id"] = store.next_id("medicines", "M-")
    stored = store.append_row("medicines", cleaned)

    return jsonify({"created": full_record("medicines", stored)}), 201


@app.get("/api/medicines/<medicine_id>")
def get_medicine(medicine_id):
    """Return one medicine, with the stores stocking it."""
    record = store.get_by_id("medicines", medicine_id)

    if record is None:
        return error(f"no medicine with id {medicine_id}", 404)

    medicines, _ = store.read_all("medicines")
    stores, _ = store.read_all("stores")
    stocked = registry.stores_with_medicine(record["name"], medicines, stores)

    return jsonify({"medicine": record, "stocked_by": stocked})


@app.get("/api/medicines/<medicine_id>/stores")
def medicine_stores(medicine_id):
    """Return only the stores stocking a given medicine."""
    record = store.get_by_id("medicines", medicine_id)

    if record is None:
        return error(f"no medicine with id {medicine_id}", 404)

    medicines, _ = store.read_all("medicines")
    stores, _ = store.read_all("stores")
    stocked = registry.stores_with_medicine(record["name"], medicines, stores)

    return jsonify({"medicine_id": medicine_id, "name": record["name"],
                    "count": len(stocked), "stores": stocked})


# ---------------------------------------------------------------- stores

@app.get("/api/stores")
def list_stores():
    """Return one page of medical stores."""
    return registry_page("stores", "stores")


@app.post("/api/stores")
def create_store():
    """Add a medical store."""
    body = payload()
    cleaned, errors = registry.validate_record("stores", body)

    if errors:
        return error("validation failed", 400, errors=errors)

    cleaned["store_id"] = store.next_id("stores", "S-")
    stored = store.append_row("stores", cleaned)

    return jsonify({"created": full_record("stores", stored)}), 201


@app.get("/api/stores/<store_id>")
def get_store(store_id):
    """Return one store with the medicines it stocks resolved."""
    record = store.get_by_id("stores", store_id)

    if record is None:
        return error(f"no store with id {store_id}", 404)

    medicines, _ = store.read_all("medicines")
    held = registry.stock_set_for(record)
    stocked = [m for m in medicines if m["medicine_id"] in held]

    return jsonify({"store": record, "stock_count": len(stocked),
                    "medicines": stocked})


# ------------------------------------------------------------- hospitals

@app.get("/api/hospitals")
def list_hospitals():
    """Return one page of hospitals."""
    return registry_page("hospitals", "hospitals")


@app.post("/api/hospitals")
def create_hospital():
    """Add a hospital."""
    body = payload()
    cleaned, errors = registry.validate_record("hospitals", body)

    if errors:
        return error("validation failed", 400, errors=errors)

    cleaned["hospital_id"] = store.next_id("hospitals", "H-")
    stored = store.append_row("hospitals", cleaned)

    return jsonify({"created": full_record("hospitals", stored)}), 201


@app.get("/api/hospitals/<hospital_id>")
def get_hospital(hospital_id):
    """Return one hospital with the doctors practising there."""
    record = store.get_by_id("hospitals", hospital_id)

    if record is None:
        return error(f"no hospital with id {hospital_id}", 404)

    doctors = store.doctors_at(hospital_id)

    return jsonify({"hospital": record, "doctor_count": len(doctors),
                    "doctors": doctors})


# --------------------------------------------------------------- doctors

def attach_hospital(doctors):
    """Copy the hospital's name, area and city onto each doctor row.

    A doctor is only identified by the hospital they work at, so those
    three fields have to be present *before* the search runs. Joining
    afterwards means a query for a hospital or a locality can never match,
    even though the interface offers both.
    """
    hospitals, _ = store.read_all("hospitals")
    by_hospital = {h["hospital_id"]: h for h in hospitals}

    for row in doctors:
        hospital = by_hospital.get(row["hospital_id"], {})
        row["hospital_name"] = hospital.get("name", "")
        row["hospital_area"] = hospital.get("area", "")
        row["hospital_city"] = hospital.get("city", "")

    return doctors


@app.get("/api/doctors")
def list_doctors():
    """Return one page of doctors, with their hospital attached."""
    return registry_page("doctors", "doctors", after=attach_hospital)


@app.post("/api/doctors")
def create_doctor():
    """Add a doctor."""
    body = payload()
    cleaned, errors = registry.validate_record("doctors", body)

    if errors:
        return error("validation failed", 400, errors=errors)

    cleaned["doctor_id"] = store.next_id("doctors", "D-")
    stored = store.append_row("doctors", cleaned)

    return jsonify({"created": full_record("doctors", stored)}), 201


@app.get("/api/doctors/<doctor_id>")
def get_doctor(doctor_id):
    """Return one doctor, their hospital, and their recent consultations."""
    record = store.get_by_id("doctors", doctor_id)

    if record is None:
        return error(f"no doctor with id {doctor_id}", 404)

    hospital = store.get_by_id("hospitals", record["hospital_id"]) or {}

    visits = store.visits_for_doctor(doctor_id)
    patients, _ = store.read_all("patients")
    by_patient = {p["patient_id"]: p for p in patients}

    for visit in visits:
        patient = by_patient.get(visit["patient_id"], {})
        visit["patient_name"] = patient.get("name", "")

    return jsonify({
        "doctor": dict(record, hospital_name=hospital.get("name", "")),
        "hospital": hospital,
        "visit_count": len(visits),
        "visits": visits,
    })


# ------------------------------------------------------- rare conditions

@app.get("/api/rare-conditions")
def list_rare_conditions():
    """Summarise the HPO derived registry and return a first page.

    The registry is 11,655 diseases. A page that opens on an empty search
    box tells the reader nothing about a corpus that size, so this returns
    the shape of it: how many diseases, how many phenotypic findings, how
    many carry an inheritance mode, and the most common findings. The
    interface shows that instead of a prompt to type.
    """
    records, _ = store.read_all("rare_conditions")
    vocabulary, _ = store.read_all("hpo_symptoms")

    by_hpo = {}
    for row in records:
        for hpo_id in row["hpo_ids"].split("|"):
            if hpo_id:
                by_hpo[hpo_id] = by_hpo.get(hpo_id, 0) + 1

    lay = {v["hpo_id"]: (v["lay_term"] or v["term"]).lower()
           for v in vocabulary}

    common = []
    for hpo_id, count in sorted(by_hpo.items(),
                                key=lambda kv: -kv[1])[:12]:
        common.append({
            "hpo_id": hpo_id,
            "word": lay.get(hpo_id, hpo_id.lower()),
            "diseases": count,
        })

    inheritance = {}

    for row in records:
        for mode in row["inheritance_mode"].split("|"):
            if mode:
                inheritance[mode] = inheritance.get(mode, 0) + 1

    return jsonify({
        "total": len(records),
        "with_mondo": sum(1 for r in records if r["mondo_id"]),
        "with_inheritance": sum(1 for r in records if r["inheritance_mode"]),
        "distinct_findings": len(by_hpo),
        "lay_wording": sum(1 for v in vocabulary
                           if v["has_lay_wording"] == "yes"),
        "common_findings": common,
        "inheritance_modes": sorted(
            [{"mode": k, "diseases": v} for k, v in inheritance.items()],
            key=lambda x: -x["diseases"],
        )[:8],
        "results": records[:SEARCH_PAGE_SIZE],
    })


@app.get("/api/rare-conditions/<condition_id>")
def get_rare_condition(condition_id):
    """One rare disease, with its findings expanded into words."""
    record = store.get_by_id("rare_conditions", condition_id)

    if record is None:
        return error(f"no condition with id {condition_id}", 404)

    vocabulary, _ = store.read_all("hpo_symptoms")
    by_id = {v["hpo_id"]: v for v in vocabulary}

    findings = []

    for hpo_id, word in zip(record["hpo_ids"].split("|"),
                            record["symptoms"].split("|")):
        term = by_id.get(hpo_id, {})

        findings.append({
            "hpo_id": hpo_id,
            "word": word,
            "term": term.get("term", ""),
            "lay_term": term.get("lay_term", ""),
            "is_lay_wording": term.get("has_lay_wording") == "yes",
        })

    return jsonify({
        "condition": record,
        "findings": findings,
        "inheritance": [m for m in record["inheritance_mode"].split("|") if m],
    })


# ---------------------------------------------------------------- search

@app.get("/api/search/<record_type>")
def search(record_type):
    """Fuzzy search a registry. Returns everything scoring above zero.

    A query matching nothing is a 200 with count 0, not a 404. An empty
    query is a 400, since that is a malformed request rather than an
    honest negative result.
    """
    if record_type not in SEARCHABLE:
        return error(f"cannot search {record_type}", 404,
                     searchable=list(SEARCHABLE))

    query = request.args.get("q", "")

    if not query.strip():
        return error("query parameter q is required and cannot be blank")

    records, _ = store.read_all(record_type)

    # Joined before searching, not after. See attach_hospital.
    if record_type == "doctors":
        attach_hospital(records)

    results = registry.search_records(records, query, record_type)

    # Page size is honoured only when it would not hide a short result set.
    try:
        limit = int(request.args.get("limit", SEARCH_PAGE_SIZE))
    except ValueError:
        return error("limit must be a whole number")

    limit = max(1, min(limit, 500))

    total = len(results)
    page = results[:limit]

    return jsonify({
        "query": query,
        "record_type": record_type,
        "count": len(page),
        "total_matched": total,
        "truncated": total > len(page),
        "results": page,
    })


# ---------------------------------------------------------------- triage

@app.get("/api/diseases")
def list_diseases():
    """Return the triage knowledge base."""
    records, _ = store.read_all("diseases")

    for row in records:
        row["symptom_set"] = sorted(triage.normalise_symptoms(row["symptoms"]))

    return jsonify({"count": len(records), "diseases": records})


@app.post("/api/triage")
def run_triage():
    """Rank diseases for a set of reported symptoms.

    Requires at least one symptom. Optional conditions trigger
    contraindication warnings, and an optional age adds a range note.
    Neither is an error: the result is still a 200 with warnings.
    """
    body = payload()
    symptoms = body.get("symptoms", [])

    # normalise_symptoms already splits a pipe or comma delimited string,
    # so it must be passed straight through. Wrapping it in a list first
    # would turn the whole string into one bogus token.
    if not triage.normalise_symptoms(symptoms):
        return error("at least one symptom is required",
                     required_field="symptoms")

    conditions = body.get("conditions", []) or []
    age = body.get("age")

    results = triage.rank_diseases(symptoms, conditions=conditions, age=age)

    patient_ref = body.get("patient_id", "")
    patient = {}

    if patient_ref:
        found = store.get_by_id("patients", patient_ref)
        if found is not None:
            patient = found

    warnings = [w for r in results for w in r["warnings"]]

    return jsonify({
        "count": len(results),
        "results": results,
        "warnings": warnings,
        "patient": patient,
        "report": triage.render_report(patient or {"name": "anonymous"}, results,
                                       conditions),
        "disclaimer": triage.DISCLAIMER,
    })


# ------------------------------------------------------------- analytics

@app.get("/api/analytics")
def list_analytics():
    """Return the recorded profile of every dataset."""
    return jsonify({"datasets": analytics.list_datasets(),
                    "passing": analytics.passing_datasets()})


@app.get("/api/analytics/risk-bands")
def list_risk_band_options():
    """Return which dataset columns have risk bands defined."""
    options = {}

    for name in analytics.passing_datasets():
        options[name] = analytics.available_risk_bands(name)

    return jsonify({"options": options})


def dataset_or_404(name):
    """Return the dataset name if valid, or a 404 response tuple."""
    if name not in analytics.passing_datasets():
        return None, error(f"unknown dataset {name}", 404,
                           available=analytics.passing_datasets())
    return name, None


@app.get("/api/analytics/<name>")
def dataset_profile(name):
    """Return describe, groupby and value_counts for one dataset."""
    valid, failure = dataset_or_404(name)

    if failure:
        return failure

    return jsonify(analytics.profile(valid))


@app.get("/api/analytics/<name>/risk-bands")
def dataset_risk_bands(name):
    """Return risk band distributions for a dataset.

    With no column, returns every column that has thresholds defined.
    """
    valid, failure = dataset_or_404(name)

    if failure:
        return failure

    column = request.args.get("column")

    if not column:
        available = analytics.available_risk_bands(valid)

        if not available:
            return error(f"{valid} has no risk band columns defined", 404)

        return jsonify({"dataset": valid,
                        "columns": {c: analytics.risk_bands(valid, c)
                                    for c in available}})

    try:
        return jsonify(analytics.risk_bands(valid, column))
    except KeyError as e:
        return error(str(e), 404,
                     available=analytics.available_risk_bands(valid))


@app.get("/api/analytics/<name>/charts")
def dataset_charts(name):
    """Render charts and return the filenames written."""
    valid, failure = dataset_or_404(name)

    if failure:
        return failure

    written = analytics.save_charts(valid)
    return jsonify({"dataset": valid, "charts": written})


@app.get("/charts/<path:filename>")
def serve_chart(filename):
    """Serve a generated chart PNG."""
    directory = os.path.join(os.getcwd(), "static", "charts")

    if not os.path.exists(os.path.join(directory, filename)):
        return error(f"no chart named {filename}", 404)

    return send_from_directory(directory, filename)


# ---------------------------------------------------------------- backup

@app.post("/api/backup")
def run_backup():
    """Copy the five registry CSVs into a timestamped folder."""
    written = store.backup_all()
    return jsonify({"count": len(written), "files": written})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)