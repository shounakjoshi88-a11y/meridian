"""Find the offset that recovers the short description from an overrun row.

The order file prints a long description into a 62 character column and
then the short description. When the long form fills the column the two
run together with a single space and there is no gap to split on.

Test candidate offsets against the rows that show the symptom and report
which one yields text that starts cleanly and never starts mid-word.
"""
import io
import re

PATH = "research/raw/icd10cm_order_2027.txt"
PADDING = re.compile(r" {2,}")

lines = [l for l in io.open(PATH, encoding="utf-8").read().splitlines() if l.strip()]

suspects = []

for line in lines:
    parts = line.split(None, 3)
    if len(parts) < 4:
        continue
    lineno, code, flag, rest = parts
    if not lineno.isdigit() or flag != "0":
        continue
    chunks = [c for c in PADDING.split(rest.strip()) if c]
    if len(chunks) == 1 and len(chunks[0]) > 66:
        suspects.append((code, chunks[0]))

print(f"category headers with the overrun symptom: {len(suspects):,}")
print()

CANDIDATES = [60, 61, 62, 63, 64]

for offset in CANDIDATES:
    clean_starts = 0
    mid_word = 0
    empty = 0
    samples = []

    for code, text in suspects:
        tail = text[offset:].strip()
        if not tail:
            empty += 1
            continue
        # A clean short form starts with a capital letter.
        if tail[0].isupper():
            clean_starts += 1
            if len(samples) < 3:
                samples.append(f"{code}: {tail[:52]}")
        else:
            mid_word += 1

    print(f"offset {offset}: clean={clean_starts:>5}  "
          f"mid_word={mid_word:>5}  empty={empty:>4}")
    for s in samples[:2]:
        print(f"           {s}")

print()
print("=== what the long form looks like at the boundary ===")
for code, text in suspects[:4]:
    print(f"{code}:")
    print(f"   [0:62]  {text[:62]!r}")
    print(f"   [62:]   {text[62:].strip()[:60]!r}")