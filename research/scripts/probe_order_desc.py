"""Work out how to split the padded description in the ICD-10-CM order file.

The order file prints a long description, pads it to a fixed width, then
prints a short form. Splitting naively gives "Cholera      Cholera".
"""
import io
import re

PATH = "research/raw/icd10cm_order_2027.txt"
lines = [l for l in io.open(PATH, encoding="utf-8").read().splitlines() if l.strip()]

TWO_OR_MORE = re.compile(r" {2,}")


def extract(line):
    parts = line.split(None, 3)
    if len(parts) < 4:
        return None
    rest = parts[3]
    chunks = [c for c in TWO_OR_MORE.split(rest.strip()) if c]
    return parts[0], parts[1], parts[2], chunks


print("=== first 6 rows ===")
for line in lines[:6]:
    print(extract(line))

print()
print("=== headers we actually want to use ===")
wanted = {"J00", "J02", "J20", "J45", "E10", "E03", "I50", "R51", "R05",
          "K21", "K52", "H66", "H25", "M79", "G20", "N40", "L20", "R50",
          "R21", "F43", "G43", "K04", "K05", "R10", "M54", "A19", "A15",
          "B34", "A09", "A37", "I48", "I20", "E05", "E78", "E87", "E86",
          "M17", "M10", "M06", "G40", "G43", "G56", "N20", "N39", "N63",
          "N92", "N80", "N61", "L30", "L40", "L65", "J38", "H81", "J47",
          "F32", "F41", "K59", "K52", "K70", "R73", "H52", "H10", "N92"}
found = {}
for line in lines:
    got = extract(line)
    if got and got[1] in wanted:
        found[got[1]] = (got[2], got[3][-1] if got[3] else "")

missing = sorted(wanted - set(found))
print(f"headers found: {len(found)} of {len(wanted)}")
print(f"missing      : {missing}")
print()
for code in sorted(found):
    flag, desc = found[code]
    print(f"  {code:<6} flag={flag}  {desc[:64]}")