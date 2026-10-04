"""Remove any rows created by a previous test run.

The seed files are hand written, so a test run that failed midway can
leave rows behind. This trims each registry back to its seeded ids.
"""

import csv
import os
import sys

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

import store  # noqa: E402

# The highest id present in the committed seed data for each registry.
SEEDED_MAX = {
    "patients": 8,
    "visits": 12,
    "medicines": 20,
    "stores": 6,
    "diseases": 15,
}


def trim(record_type):
    """Delete rows whose id number is above the seeded maximum."""
    id_field = store.RECORDS[record_type][2]
    path = store.path_for(record_type)
    fields = store.fields_for(record_type)

    with open(path, "r", newline="") as f:
        rows = list(csv.DictReader(f))

    kept = []
    removed = []

    for row in rows:
        raw = row[id_field]
        suffix = raw.split("-")[-1]

        if suffix.isdigit() and int(suffix) <= SEEDED_MAX[record_type]:
            kept.append(row)
        else:
            removed.append(raw)

    if not removed:
        return []

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in kept:
            writer.writerow(row)

    return removed


def main():
    total = 0

    for record_type in store.RECORDS:
        removed = trim(record_type)

        if removed:
            print(f"{record_type}: removed {len(removed)} -> {', '.join(removed)}")
            total += len(removed)

    if total == 0:
        print("nothing to trim, seed data already at its baseline")
    else:
        print(f"\nremoved {total} stray rows")

    for record_type in store.RECORDS:
        print(f"  {record_type}: {store.count_records(record_type)} rows")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())