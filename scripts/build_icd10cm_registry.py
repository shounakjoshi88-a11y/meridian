"""Build data/icd10cm_codes.csv from the downloaded ICD-10-CM order file.

98,403 rows: every code in the FY2027 order, being 74,879 billable codes
plus the category headers above them. The names and codes are a US
Government work in the public domain, not invented, which is why this file
can be quoted in a README.

Category headers are kept because they are the codes clinicians actually
use: "J45 Asthma" and "I10 Hypertension" are category codes, and J45 in
particular has no billable form of its own.

Only concepts from the labs: opening a file, reading it line by line,
str.split, a list of chapter tuples, and list comprehensions.
"""
import csv
import io
import os
import re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, "research", "raw")
ORDER_SOURCE = os.path.join(RAW, "icd10cm_order_2027.txt")
CODES_SOURCE = os.path.join(RAW, "icd10cm_codes_2027.txt")
TARGET = os.path.join(HERE, "data", "icd10cm_codes.csv")

SOURCE_URL = ("https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Publications/"
              "ICD10CM/2027/icd10cm-code-descriptions-2027.zip")

# The order file pads its description column, so the same text can appear
# twice with a run of spaces between. Two or more spaces is the separator.
PADDING = re.compile(r" {2,}")

# Width of the abbreviated long-description column, measured against the
# file: research/scripts/probe_offset.py tested offsets 60 to 64 against
# all 1,361 rows showing the overrun symptom, and 61 was the only one
# that started every short description on a capital letter.
LONG_COLUMN_WIDTH = 61

# A single chunk longer than this must have overrun the column, because a
# padded row would have produced two chunks instead.
OVERFLOW_THRESHOLD = 66


def split_description(text):
    """Recover the short description from a padded description column.

    Three shapes occur in the source file.

    A description that fits is printed once, or twice with padding between
    the copies. Splitting on two or more spaces and taking the last chunk
    handles both.

    A description too long for the 61 character column overruns it and
    butts against the short description with a single space, so there is
    no gap to split on. Those rows are the only ones that stay a single
    chunk while exceeding OVERFLOW_THRESHOLD, and the short description
    begins at LONG_COLUMN_WIDTH.
    """
    chunks = [c for c in PADDING.split(text.strip()) if c]

    if not chunks:
        return ""

    if len(chunks) > 1:
        return chunks[-1]

    if len(chunks[0]) > OVERFLOW_THRESHOLD:
        return chunks[0][LONG_COLUMN_WIDTH:].strip()

    return chunks[0]

# ICD-10-CM chapters, as (low letter, high letter, name). A chapter either
# starts with one letter or spans a range, which is why the bounds are a
# pair rather than a set membership test.
CHAPTERS = [
    ("A", "B", "Infectious and parasitic diseases"),
    ("C", "D", "Neoplasms and blood disorders"),
    ("E", "E", "Endocrine, nutritional and metabolic diseases"),
    ("F", "F", "Mental, behavioural and neurodevelopmental disorders"),
    ("G", "G", "Nervous system diseases"),
    ("H", "H", "Diseases of the eye, ear and mastoid"),
    ("I", "I", "Cardiovascular diseases"),
    ("J", "J", "Respiratory diseases"),
    ("K", "K", "Digestive system diseases"),
    ("L", "L", "Skin and subcutaneous tissue diseases"),
    ("M", "M", "Musculoskeletal and connective tissue diseases"),
    ("N", "N", "Genitourinary system diseases"),
    ("O", "O", "Pregnancy, childbirth and puerperium"),
    ("P", "P", "Perinatal conditions"),
    ("Q", "Q", "Congenital malformations and chromosomal abnormalities"),
    ("R", "R", "Symptoms, signs and abnormal clinical findings"),
    ("S", "T", "Injury, poisoning and external causes"),
    ("V", "Y", "External causes of morbidity"),
    ("Z", "Z", "Factors influencing health status"),
]


def chapter_for(code):
    """Return the chapter name for a code, or '' if the letter is unknown."""
    if not code:
        return ""

    first = code[0].upper()

    for low, high, name in CHAPTERS:
        if low <= first <= high:
            return name

    return ""


def parse_order_file(path):
    """Yield (code, description, is_billable) for every row in the file.

    The order file is four whitespace-aligned columns: a line number, the
    code, a flag that is 1 for a billable code and 0 for a category
    header, then the padded description.

    Category header descriptions are short, so they appear twice with
    padding between the copies. Splitting on two or more spaces and taking
    the last chunk returns the text once.
    """
    with io.open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")

            if not line.strip():
                continue

            parts = line.split(None, 3)

            if len(parts) < 4:
                continue

            lineno, code, flag, rest = parts

            if not lineno.isdigit():
                continue

            yield code, split_description(rest), flag == "1"


def parse_codes_file(path):
    """Yield (code, description) for each billable code.

    This file has no fixed-width description column, just the code, some
    spaces, and the description. A long description is printed as a padded
    long form followed by a short form, so splitting on runs of two or
    more spaces and taking the last chunk recovers the short form.

    The overflow rule in split_description does not apply here. It exists
    because the order file has a 61 character column, and applying it
    here truncates every description longer than that.
    """
    with io.open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")

            if not line.strip():
                continue

            parts = line.split(None, 1)

            if len(parts) != 2:
                continue

            chunks = [c for c in PADDING.split(parts[1].strip()) if c]

            yield parts[0], chunks[-1] if chunks else ""


def main():
    for path in (ORDER_SOURCE, CODES_SOURCE):
        if not os.path.exists(path):
            raise SystemExit(
                f"missing {path}\n"
                f"download it first: python research/scripts/fetch_icd10cm.py"
            )

    rows = []
    seen = set()
    kinds = {}
    descriptions = {}

    # Billable descriptions come from the codes file, which stores them
    # once with no padding. The order file is only consulted for the
    # category headers it adds, because its padded long-and-short columns
    # cannot be split reliably once a description overruns the column.
    for code, description in parse_codes_file(CODES_SOURCE):
        if code in seen:
            continue

        seen.add(code)
        kinds[code] = "billable"
        descriptions[code] = description

    for code, description, billable in parse_order_file(ORDER_SOURCE):
        if billable or code in seen:
            continue

        seen.add(code)
        kinds[code] = "category"
        descriptions[code] = description

    for code in sorted(seen):
        rows.append({
            "code": code,
            "description": descriptions[code],
            "chapter": chapter_for(code),
            "code_kind": kinds[code],
            "is_symptom_code": "yes" if code[0].upper() == "R" else "no",
        })

    with io.open(TARGET, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["code", "description", "chapter", "code_kind",
                        "is_symptom_code"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    billable = sum(1 for r in rows if r["code_kind"] == "billable")
    categories = len(rows) - billable
    symptom_rows = sum(1 for r in rows if r["is_symptom_code"] == "yes")

    print(f"wrote {TARGET}")
    print(f"  rows               : {len(rows):,}")
    print(f"  billable codes     : {billable:,}")
    print(f"  category headers   : {categories:,}")
    print(f"  chapter R codes    : {symptom_rows:,}")
    print(f"  chapters covered   : "
          f"{len({r['chapter'] for r in rows if r['chapter']})}")
    print(f"  source             : {SOURCE_URL}")


if __name__ == "__main__":
    main()