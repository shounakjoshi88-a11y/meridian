"""Search and validation across the Meridian registries.

Taught concepts: dict .get() .items() .keys(), list and set comprehensions,
sorted(key=lambda), string .strip() .casefold() .split(), if/elif chains,
nested loops, len(), isinstance().

Core rule from spec section 4.2: a blank cell means unknown. Blank fields
are skipped when scoring, never treated as a mismatch, because scoring a
missing value as wrong would push good records down the ranking.
"""

FIELD_WEIGHTS = {
    "medicines": {
        "name": 5, "generic": 4, "category": 3, "form": 2,
        "manufacturer": 2, "storage": 1, "strength": 2,
    },
    "stores": {
        "name": 5, "type": 3, "area": 2, "city": 2, "hours": 1,
    },
    "patients": {
        "name": 5, "area": 2, "city": 2, "blood_group": 2, "phone": 1,
        "gender": 1, "address_line": 1, "emergency_contact": 1,
    },
    "hospitals": {
        "name": 5, "type": 3, "area": 2, "city": 2,
        "address_line": 1, "speciality": 2,
    },
    "doctors": {
        "name": 5, "specialisation": 4, "department": 3, "hospital_id": 0,
        "qualification": 2, "room_no": 1, "languages": 2,
        "registration_no": 1,
    },
}

DEFAULT_WEIGHT = 1

# Never searched, and never allowed to contribute a point.
ID_SUFFIX = "_id"

REQUIRED_FIELDS = {
    "patients": ["name"],
    "medicines": ["name"],
    "stores": ["name"],
    "hospitals": ["name"],
    "doctors": ["name", "hospital_id"],
}

NUMERIC_FIELDS = {
    "patients": ["age"],
    "medicines": ["price"],
    "stores": ["rating"],
    "hospitals": ["beds", "established_year"],
    "doctors": ["consultation_fee", "experience_years"],
}

# Six digits. Not range checked here because a hospital may sit outside
# the city's own pin prefix; verify_seed_data.py covers that case.
PIN_FIELDS = {"pincode"}

VALID_BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}

# Spelled out rather than derived by trimming the last letter, which would
# break on any plural that is not simply singular plus an s.
ID_FIELDS = {
    "patients": "patient_id",
    "visits": "visit_id",
    "medicines": "medicine_id",
    "stores": "store_id",
    "diseases": "disease_id",
}


def normalise(text):
    """Lower case and strip a value so comparisons are reliable."""
    return str(text).strip().casefold()


def query_terms(query):
    """Split a search string into a list of normalised terms."""
    if not query:
        return []

    return [normalise(t) for t in query.replace(",", " ").split() if t.strip()]


def match_score(record, terms, weights):
    """Score one record against the search terms.

    Returns (score, matched_fields). Each field can contribute at most
    once no matter how many terms hit it, because the inner loop breaks.
    """
    score = 0
    matched_fields = []

    for field in record:
        if field.endswith(ID_SUFFIX):
            continue

        value = record[field]

        if value == "" or value is None:
            continue

        value = normalise(value)

        for term in terms:
            if term in value:
                score += weights.get(field, DEFAULT_WEIGHT)
                matched_fields.append(field)
                break

    return score, matched_fields


def search_records(records, query, record_type):
    """Return matching records sorted best first.

    Every record scoring above zero is returned. Nothing is discarded for
    being weak, because an empty result set reads as a broken search when
    the table simply holds three medicines and none is the one asked for.
    The caller decides what to dim.
    """
    terms = query_terms(query)

    if not terms:
        return []

    weights = FIELD_WEIGHTS.get(record_type, {})

    results = []

    for record in records:
        score, fields = match_score(record, terms, weights)

        if score > 0:
            enriched = dict(record)
            enriched["score"] = score
            enriched["matched_fields"] = fields
            results.append(enriched)

    results.sort(key=lambda r: r["score"], reverse=True)
    return results


def search_by_id(records, id_field, target):
    """Exact id lookup, the opposite of fuzzy search."""
    for record in records:
        if record[id_field] == target:
            return record
    return None


def stock_set_for(store):
    """Return the set of medicine ids a store holds.

    A blank stock cell means not recorded, not stocking nothing, so it
    returns an empty set and the caller skips the store.
    """
    raw = store.get("stock_csv", "")

    if not raw:
        return set()

    return {s.strip() for s in raw.split("|") if s.strip()}


def stores_with_medicine(medicine_name, medicines, stores):
    """Return every store stocking a medicine, matching name or generic."""
    target = normalise(medicine_name)

    if not target:
        return []

    wanted = set()

    for m in medicines:
        if target in normalise(m.get("name", "")) or \
           target in normalise(m.get("generic", "")):
            wanted.add(m["medicine_id"])

    if not wanted:
        return []

    matches = []

    for s in stores:
        held = stock_set_for(s)

        if not held:
            continue

        if held & wanted:
            matches.append(s)

    return matches


def medicines_for_disease(disease_name, medicines, diseases):
    """Return catalogue entries whose name matches a disease's medication."""
    target = normalise(disease_name)

    found = []
    seen = set()

    for d in diseases:
        if normalise(d["name"]) != target:
            continue

        med = d.get("medication", "")

        for m in medicines:
            key = m["medicine_id"]

            if key in seen:
                continue

            if normalise(m.get("name", "")).startswith(normalise(med)) or \
               normalise(med) in normalise(m.get("generic", "")):
                seen.add(key)
                found.append(m)

    return found


def validate_record(record_type, payload, require_required=True):
    """Check a record before writing it.

    Returns (cleaned, errors). cleaned is safe to store even when errors
    is non-empty, so one bad field does not block everything else.
    Every problem is reported at once rather than one per round trip.

    require_required is False for partial updates, where sending only a
    city must not fail because no name was included. Format checks always
    run, so age="old" is still caught either way.
    """
    errors = []
    cleaned = {}

    for key, value in payload.items():
        if value is None:
            cleaned[key] = ""
        elif isinstance(value, (int, float)):
            cleaned[key] = str(value)
        elif isinstance(value, (list, tuple)):
            cleaned[key] = "|".join(str(v).strip() for v in value if str(v).strip())
        else:
            cleaned[key] = str(value).strip()

    if require_required:
        for field in REQUIRED_FIELDS.get(record_type, []):
            if not cleaned.get(field, ""):
                errors.append(f"{field} is required")

    for field in NUMERIC_FIELDS.get(record_type, []):
        raw = cleaned.get(field, "")

        if raw == "":
            continue

        try:
            value = float(raw)
        except ValueError:
            errors.append(f"{field} must be a number, got {raw!r}")
            continue

        # Beds, fees and years have sensible floors. Rejecting a negative
        # bed count here is cheaper than finding it in a chart later.
        if value < 0:
            errors.append(f"{field} cannot be negative, got {raw!r}")

    for field in PIN_FIELDS:
        raw = cleaned.get(field, "")

        if raw and (not raw.isdigit() or len(raw) != 6):
            errors.append(f"{field} must be six digits, got {raw!r}")

    if record_type == "patients":
        blood = cleaned.get("blood_group", "")

        if blood and blood not in VALID_BLOOD_GROUPS:
            errors.append(
                f"blood_group must be one of {sorted(VALID_BLOOD_GROUPS)},"
                f" got {blood!r}"
            )

        gender = cleaned.get("gender", "").casefold()

        if gender and gender not in {"male", "female", "other"}:
            errors.append(f"gender must be male, female or other, got {gender!r}")

        age = cleaned.get("age", "")

        if age:
            try:
                if not (0 <= float(age) <= 120):
                    errors.append(f"age must be between 0 and 120, got {age!r}")
            except ValueError:
                pass

    if record_type == "medicines":
        for flag in ("otc", "rx_required"):
            raw = cleaned.get(flag, "").casefold()

            if raw and raw not in {"yes", "no"}:
                errors.append(f"{flag} must be yes or no, got {raw!r}")

    if record_type == "doctors":
        hospital = store_get_by_id("hospitals", cleaned.get("hospital_id", ""))

        if cleaned.get("hospital_id") and hospital is None:
            errors.append(
                f"hospital_id {cleaned['hospital_id']} does not exist")

        registration = cleaned.get("registration_no", "")

        if registration and not registration.upper().startswith("MMC-"):
            errors.append(
                f"registration_no should look like MMC-YYYY-NNNNNN,"
                f" got {registration!r}")

    if record_type == "stores":
        held = cleaned.get("stock_csv", "")

        if held:
            for mid in held.split("|"):
                if mid and not mid.startswith("M-"):
                    errors.append(
                        f"stock_csv must contain medicine ids like M-01, got {mid!r}"
                    )

    return cleaned, errors


def store_get_by_id(record_type, target):
    """Look a record up without importing store at module load time.

    store imports registry, so importing it here at the top would be
    circular. Resolved lazily instead.
    """
    if not target:
        return None

    import store

    return store.get_by_id(record_type, target)


def summarise_results(results, record_type):
    """Return a short label per result for list views."""
    id_field = ID_FIELDS.get(record_type, "id")

    lines = []

    for r in results:
        name = r.get("name", "(unnamed)")
        matched = ", ".join(r.get("matched_fields", []))
        lines.append(f"{r.get(id_field, '')} {name} [score {r['score']}] via {matched}")

    return lines