"""Verify the seed CSV files are internally consistent.

Taught concepts: file opening modes, loops, dictionaries, sets, string methods.
Run this after editing any file in data/.
"""

import csv
import os

DATA = "data"

EXPECTED = {
    "diseases.csv": ["disease_id", "icd10_code", "name", "severity", "symptoms",
                     "medication", "dosage", "age_range", "contraindications",
                     "symptom_source"],
    "medicines.csv": ["medicine_id", "name", "generic", "category", "form",
                      "strength", "otc", "rx_required", "storage", "price",
                      "manufacturer"],
    "stores.csv": ["store_id", "name", "type", "area", "city", "phone",
                   "hours", "rating", "stock_csv"],
    "patients.csv": ["patient_id", "name", "age", "gender", "phone", "email",
                     "blood_group", "address_line", "area", "pincode", "city",
                     "state", "emergency_contact", "emergency_phone",
                     "registered_on", "notes"],
    "visits.csv": ["visit_id", "patient_id", "doctor_id", "hospital_id",
                   "scheduled_date", "scheduled_time", "checked_in_at",
                   "duration_minutes", "reason", "symptoms", "diagnosis",
                   "severity", "vitals_bp", "vitals_pulse", "vitals_temp",
                   "vitals_spo2", "vitals_weight", "vitals_height",
                   "follow_up_days", "status", "notes"],
"hospitals.csv": ["hospital_id", "name", "type", "address_line", "area", "city",
                     "state", "pincode", "phone", "beds", "established_year",
                     "accreditation"],
    "rare_conditions.csv": ["condition_id", "mondo_id", "name", "symptom_count",
                           "symptoms", "hpo_ids", "inheritance_mode"],
    "hpo_symptoms.csv": ["hpo_id", "term", "lay_term", "has_lay_wording"],
    "doctors.csv": ["doctor_id", "name", "qualification", "specialisation",
                    "registration_no", "hospital_id", "department", "room_no",
                    "phone", "consultation_fee", "experience_years",
                    "languages", "availability"],
}

SEVERITIES = {"low", "moderate", "high", "severe"}
STATUSES = {"Active", "Resolved", "Pending", "Staged"}


def load(name):
    """Read one seed file into a list of dicts."""
    path = os.path.join(DATA, name)
    with open(path, "r", newline="") as f:
        return list(csv.DictReader(f))


def check(name):
    """Check one file for shape problems. Returns a list of problem strings."""
    problems = []
    rows = load(name)
    expected = EXPECTED[name]

    if not rows:
        return [f"{name}: no data rows"]

    actual = list(rows[0].keys())
    if actual != expected:
        problems.append(f"{name}: header mismatch\n    expected {expected}\n    got      {actual}")

    for i, row in enumerate(rows, start=2):
        if None in row or row.get(None):
            problems.append(f"{name} line {i}: wrong field count")
        for field in expected:
            if field not in row:
                problems.append(f"{name} line {i}: missing field {field}")

    return problems


def check_ids(name, key):
    """Ids must be unique within a file."""
    problems = []
    rows = load(name)
    seen = set()
    for row in rows:
        if row[key] in seen:
            problems.append(f"{name}: duplicate {key} {row[key]}")
        seen.add(row[key])
    return problems


def check_diseases():
    """Symptoms pipe-delimited, severity valid, age range parseable."""
    problems = []
    for row in load("diseases.csv"):
        did = row["disease_id"]

        if row["severity"] not in SEVERITIES:
            problems.append(f"diseases {did}: bad severity {row['severity']!r}")

        symptoms = row["symptoms"]
        if not symptoms:
            problems.append(f"diseases {did}: no symptoms")
            continue
        for s in symptoms.split("|"):
            if s != s.strip():
                problems.append(f"diseases {did}: symptom has whitespace {s!r}")
            if s == "":
                problems.append(f"diseases {did}: empty symptom between pipes")

        if row["age_range"]:
            parts = row["age_range"].split("-")
            if len(parts) != 2 or not all(p.isdigit() for p in parts):
                problems.append(f"diseases {did}: bad age_range {row['age_range']!r}")
            elif int(parts[0]) > int(parts[1]):
                problems.append(f"diseases {did}: age_range inverted")
    return problems


def check_stores_refer_to_medicines():
    """Every id in stock_csv must exist in medicines.csv."""
    problems = []
    med_ids = {m["medicine_id"] for m in load("medicines.csv")}
    for store in load("stores.csv"):
        stock = store["stock_csv"]
        if not stock:
            continue
        for mid in stock.split("|"):
            if mid not in med_ids:
                problems.append(f"stores {store['store_id']}: unknown medicine {mid}")
    return problems


def check_visits_refer_to_patients():
    """Every visit must name a real patient, doctor and hospital."""
    problems = []
    patients = load("patients.csv")
    visits = load("visits.csv")
    doctors = load("doctors.csv")
    hospitals = load("hospitals.csv")

    patient_ids = {p["patient_id"] for p in patients}
    doctor_ids = {d["doctor_id"] for d in doctors}
    hospital_ids = {h["hospital_id"] for h in hospitals}
    doctor_hospital = {d["doctor_id"]: d["hospital_id"] for d in doctors}

    seen = set()

    for v in visits:
        if v["patient_id"] not in patient_ids:
            problems.append(f"visits {v['visit_id']}: unknown patient {v['patient_id']}")
        seen.add(v["patient_id"])

        if v["doctor_id"] not in doctor_ids:
            problems.append(f"visits {v['visit_id']}: unknown doctor {v['doctor_id']}")

        if v["hospital_id"] not in hospital_ids:
            problems.append(f"visits {v['visit_id']}: unknown hospital {v['hospital_id']}")

        # A doctor practises at one hospital. A visit saying otherwise is
        # a data error, not a rounding difference.
        if v["doctor_id"] in doctor_ids and v["hospital_id"] in hospital_ids:
            if doctor_hospital[v["doctor_id"]] != v["hospital_id"]:
                problems.append(
                    f"visits {v['visit_id']}: doctor works at "
                    f"{doctor_hospital[v['doctor_id']]} but visit says {v['hospital_id']}")

    for p in patients:
        if p["patient_id"] not in seen:
            problems.append(f"patients {p['patient_id']}: has no visits")

    return problems


def check_doctors_refer_to_hospitals():
    """Every doctor must be attached to a real hospital."""
    problems = []
    hospital_ids = {h["hospital_id"] for h in load("hospitals.csv")}

    for d in load("doctors.csv"):
        if d["hospital_id"] not in hospital_ids:
            problems.append(f"doctors {d['doctor_id']}: unknown hospital {d['hospital_id']}")

    return problems


def check_vitals_are_plausible():
    """Vitals must fall inside ranges a living person could have."""
    problems = []

    for v in load("visits.csv"):
        vid = v["visit_id"]

        def num(field, low, high, label):
            raw = v[field]
            if raw == "":
                return
            try:
                value = float(raw)
            except ValueError:
                problems.append(f"visits {vid}: {label} not numeric {raw!r}")
                return
            if value < low or value > high:
                problems.append(
                    f"visits {vid}: {label} {value} outside {low}-{high}")

        bp = v["vitals_bp"]
        if bp:
            parts = bp.split("/")
            if len(parts) != 2 or not all(p.isdigit() for p in parts):
                problems.append(f"visits {vid}: bad blood pressure {bp!r}")
            else:
                systolic, diastolic = int(parts[0]), int(parts[1])
                if not (70 <= systolic <= 260):
                    problems.append(f"visits {vid}: systolic {systolic} implausible")
                if not (40 <= diastolic <= 150):
                    problems.append(f"visits {vid}: diastolic {diastolic} implausible")
                if diastolic >= systolic:
                    problems.append(
                        f"visits {vid}: diastolic {diastolic} >= systolic {systolic}")

        num("vitals_pulse", 30, 220, "pulse")
        num("vitals_temp", 90, 110, "temperature")
        num("vitals_spo2", 70, 100, "spo2")
        num("vitals_weight", 1.5, 250, "weight")
        num("vitals_height", 30, 250, "height")
        num("duration_minutes", 1, 240, "duration")
        num("follow_up_days", 0, 365, "follow up days")

    return problems


def check_pin_codes():
    """Nagpur pin codes are six digits starting 440."""
    problems = []

    for filename in ("patients.csv", "hospitals.csv"):
        for row in load(filename):
            pin = row["pincode"]
            label = row.get("name", "")
            if not pin.isdigit() or len(pin) != 6:
                problems.append(f"{filename} {label}: bad pincode {pin!r}")
            elif not pin.startswith("440"):
                problems.append(f"{filename} {label}: pincode {pin} outside Nagpur range")

    return problems


def check_visit_dates_and_times():
    """Dates must be real ISO dates and times real 24 hour clock times."""
    problems = []
    months = {"01": 31, "02": 29, "03": 31, "04": 30, "05": 31, "06": 30,
              "07": 31, "08": 31, "09": 30, "10": 31, "11": 30, "12": 31}

    for v in load("visits.csv"):
        vid = v["visit_id"]
        parts = v["scheduled_date"].split("-")

        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            problems.append(f"visits {vid}: bad date {v['scheduled_date']!r}")
        else:
            month = parts[1]
            if month not in months:
                problems.append(f"visits {vid}: bad month {month!r}")
            elif not (1 <= int(parts[2]) <= months[month]):
                problems.append(f"visits {vid}: day {parts[2]} out of range")

        for field in ("scheduled_time", "checked_in_at"):
            clock = v[field]
            bits = clock.split(":")
            if len(bits) != 2 or not all(b.isdigit() for b in bits):
                problems.append(f"visits {vid}: bad {field} {clock!r}")
                continue
            hour, minute = int(bits[0]), int(bits[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                problems.append(f"visits {vid}: {field} {clock!r} out of range")

        if v["status"] not in STATUSES:
            problems.append(f"visits {vid}: bad status {v['status']!r}")

    return problems


def check_diagnoses_refer_to_diseases():
    """Visit diagnoses should name a known condition or be a legitimate
    clinical note that is not in the triage knowledge base."""
    problems = []
    names = {d["name"].casefold() for d in load("diseases.csv")}

    # Diagnoses that appear in visits but are not triage candidates. They
    # are still valid clinical findings, just outside the symptom
    # knowledge base, so they are listed rather than rejected.
    outside = {
        "menstrual irregularity", "refractive error", "ankle sprain",
        "dermatitis",
    }

    for v in load("visits.csv"):
        diagnosis = v["diagnosis"].casefold()

        if diagnosis and diagnosis not in names and diagnosis not in outside:
            problems.append(f"visits {v['visit_id']}: unknown diagnosis {v['diagnosis']!r}")

        if v["severity"] not in SEVERITIES:
            problems.append(f"visits {v['visit_id']}: bad severity {v['severity']!r}")

        # Symptoms may be pipe delimited or a single value. What must never
        # appear is a comma, because that would split one symptom into two
        # when the cell is parsed.
        if "," in v["symptoms"]:
            problems.append(
                f"visits {v['visit_id']}: symptoms contain a comma")

    return problems


def check_patients():
    """Age numeric or blank, blood group blank or a valid group."""
    problems = []
    valid_bg = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
    valid_gender = {"male", "female", "other"}

    for p in load("patients.csv"):
        pid = p["patient_id"]

        if p["age"] == "":
            problems.append(f"patients {pid}: age required")
        elif not p["age"].isdigit():
            problems.append(f"patients {pid}: age not numeric {p['age']!r}")
        elif not (0 <= int(p["age"]) <= 120):
            problems.append(f"patients {pid}: age {p['age']} out of range")

        if p["blood_group"] and p["blood_group"] not in valid_bg:
            problems.append(f"patients {pid}: bad blood group {p['blood_group']!r}")

        if p["gender"] and p["gender"] not in valid_gender:
            problems.append(f"patients {pid}: bad gender {p['gender']!r}")

        # A registered patient needs a reachable number or an address.
        if not p["phone"] and not p["address_line"]:
            problems.append(f"patients {pid}: no phone and no address")

        if p["phone"] and not p["phone"].isdigit():
            problems.append(f"patients {pid}: phone not numeric {p['phone']!r}")

        if p["city"] and p["city"] != "Nagpur" and p["pincode"].startswith("440"):
            problems.append(f"patients {pid}: Naguru pincode with city {p['city']!r}")

    return problems


def check_rare_conditions():
    """The HPO registry must be internally consistent.

    Three things can go wrong when it is generated: a symptom word that
    does not line up with its HPO id, a symptom_count that disagrees with
    the list it counts, and an inheritance mode that leaked into the
    symptom column, which is the failure that made the raw file useless.
    """
    problems = []

    conditions = load("rare_conditions.csv")
    vocabulary = {v["hpo_id"]: v for v in load("hpo_symptoms.csv")}

    for row in conditions:
        cid = row["condition_id"]

        words = [w for w in row["symptoms"].split("|") if w]
        ids = [i for i in row["hpo_ids"].split("|") if i]

        if len(words) != len(ids):
            problems.append(
                f"{cid}: {len(words)} symptom words but {len(ids)} HPO ids")

        if row["symptom_count"] != str(len(words)):
            problems.append(
                f"{cid}: symptom_count {row['symptom_count']} "
                f"but {len(words)} symptoms listed")

        for hpo_id in ids:
            if hpo_id not in vocabulary:
                problems.append(f"{cid}: {hpo_id} is not in hpo_symptoms.csv")

        for word in words:
            if "inheritance" in word.lower():
                problems.append(
                    f"{cid}: inheritance mode {word!r} leaked into symptoms")

        if "|" in row["name"]:
            problems.append(f"{cid}: name contains a pipe")

    thin = [r for r in conditions if int(r["symptom_count"]) < 3]

    if thin:
        problems.append(f"{len(thin)} conditions have fewer than 3 findings")

    return problems


def main():
    checks = [
        ("file shapes", lambda: [p for n in EXPECTED for p in check(n)]),
        ("unique ids", lambda: check_ids("diseases.csv", "disease_id")
                               + check_ids("medicines.csv", "medicine_id")
                               + check_ids("stores.csv", "store_id")
                               + check_ids("patients.csv", "patient_id")
                               + check_ids("visits.csv", "visit_id")
                               + check_ids("hospitals.csv", "hospital_id")
                               + check_ids("doctors.csv", "doctor_id")
                               + check_ids("rare_conditions.csv",
                                           "condition_id")
                               + check_ids("hpo_symptoms.csv", "hpo_id")),
        ("disease fields", check_diseases),
        ("rare conditions", check_rare_conditions),
        ("store -> medicine", check_stores_refer_to_medicines),
        ("doctor -> hospital", check_doctors_refer_to_hospitals),
        ("visit -> patient/doctor/hospital", check_visits_refer_to_patients),
        ("visit -> disease", check_diagnoses_refer_to_diseases),
        ("vitals plausible", check_vitals_are_plausible),
        ("pin codes", check_pin_codes),
        ("dates and times", check_visit_dates_and_times),
        ("patient fields", check_patients),
    ]

    total = 0
    for label, fn in checks:
        problems = fn()
        total += len(problems)
        mark = "ok " if not problems else "FAIL"
        print(f"[{mark}] {label}")
        for p in problems:
            print(f"       {p}")

    print()
    if total == 0:
        counts = ", ".join(f"{n}={len(load(n))} rows" for n in EXPECTED)
        print(f"All checks passed. {counts}")
    else:
        print(f"{total} problems found")

    return 0 if total == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())