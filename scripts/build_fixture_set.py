import csv
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

PREFIXES = ("H", "D", "S", "P", "V")
WIDTH = 4


def widen(value):
    """H-01 -> H-0001, leaving already-wide ids and blanks alone."""
    value = (value or "").strip()

    if "-" not in value:
        return value

    prefix, _, digits = value.partition("-")

    if prefix not in PREFIXES or not digits.isdigit():
        return value

    if len(digits) >= WIDTH:
        return value

    return f"{prefix}-{digits.zfill(WIDTH)}"


os.makedirs("data/fixtures", exist_ok=True)

for name in ("patients", "visits", "hospitals", "doctors", "stores"):
    src = f"data/{name}.bak.csv"
    with io.open(src, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        fields = list(rows[0].keys())

    id_field = f"{name[:-1]}_id" if not name.endswith("s") else None
    id_field = {"hospitals": "hospital_id", "doctors": "doctor_id",
                "stores": "store_id", "patients": "patient_id",
                "visits": "visit_id"}[name]

    renamed = 0
    for row in rows:
        before = row[id_field]
        after = widen(before)
        row[id_field] = after
        renamed += before != after

        for field in ("doctor_id", "hospital_id", "patient_id"):
            if field in row and field != id_field:
                row[field] = widen(row[field])

    out = f"data/fixtures/{name}.csv"
    with io.open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"{name:10} rows={len(rows):3}  ids renamed={renamed}")

print()
for name in ("hospitals", "doctors", "stores"):
    with io.open(f"data/fixtures/{name}.csv", newline="", encoding="utf-8") as f:
        ids = [r[f"{name[:-1]}_id"] for r in csv.DictReader(f)]
    print(f"{name:10} {ids[0]} .. {ids[-1]}")