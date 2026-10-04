"""Convert fixture visit temperatures from Fahrenheit to Celsius.

The original hand-written visits recorded temperature in Fahrenheit, 98.2
and 98.6. The generated rows record Celsius, 36.8. Keeping both in one
column would mean no single reading of the file is trustworthy, so the
fixtures are converted once, here, and the fixture set is regenerated from
the converted values from then on.

Run once. Safe to re-run: it is a no-op if the values are already Celsius.
"""
import csv
import io
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PATH = "data/fixtures/visits.csv"

with io.open(PATH, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
    fields = list(rows[0].keys())


def to_celsius(fahrenheit):
    return round((fahrenheit - 32) * 5 / 9, 1)


converted = 0

for row in rows:
    raw = row["vitals_temp"].strip()

    if not raw:
        continue

    # Already Celsius if it sits in a human range for a Celsius reading.
    if 33 <= float(raw) <= 43:
        continue

    row["vitals_temp"] = f"{to_celsius(float(raw)):.1f}"
    converted += 1

with io.open(PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)

temps = [r["vitals_temp"] for r in rows if r["vitals_temp"].strip()]
print(f"converted {converted} of {len(rows)} fixture visits")
print(f"range now {min(float(t) for t in temps)} to {max(float(t) for t in temps)} Celsius")