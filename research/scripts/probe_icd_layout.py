import io

PATH = "research/raw/icd10cm_order_2027.txt"
lines = [l for l in io.open(PATH, encoding="utf-8").read().splitlines() if l.strip()]

print("=== column layout, first 3 lines with ruler ===")
print("0123456789" * 6)
for l in lines[:3]:
    print(l[:100])
print()

# Where does the description start and is there a trailing column?
first = lines[0]
print("line len:", len(first))
for probe in ("A00", "E11", "R50", "J45"):
    for l in lines:
        parts = l.split(None, 3)
        if len(parts) >= 4 and parts[1].startswith(probe):
            print(f"{probe}: lineno={parts[0]!r} code={parts[1]!r} flag={parts[2]!r}")
            print(f"     rest={parts[3][:96]!r}")
            break

print()
print("=== is the description padded to a fixed column? ===")
for l in lines[:2]:
    # find the run of 2+ spaces after the flag
    parts = l.split(None, 3)
    rest = parts[3]
    # the description block appears to be 78 wide, then a short form
    print(f"  desc starts at col {l.find(parts[3])}")
    if len(rest) > 78:
        print(f"  tail after col 78: {rest[78:][:40]!r}")