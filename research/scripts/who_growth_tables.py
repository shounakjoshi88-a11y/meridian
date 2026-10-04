"""Pull exact WHO Child Growth Standards medians out of the published LMS tables.

Why bother: the notes need real numbers for infant and paediatric height and
weight. Quoting a median from memory is how wrong numbers get into a
generator, so instead we download the official WHO z-score workbooks, which
ship the LMS parameters, and read the median column M out of them.

An .xlsx file is a zip of XML parts. We only need
xl/worksheets/sheet1.xml plus xl/sharedStrings.xml, so zipfile and
xml.etree from the standard library are enough - no openpyxl, no pandas.

Taught concepts used: functions, lists, dicts, strings, loops, files, tuples
and imports (Lab 1-2). This is a research helper, not part of the app.

Run it:

    python research/scripts/who_growth_tables.py
"""

import io
import urllib.request
import zipfile
import xml.etree.ElementTree as ElementTree

# Direct downloads published on cdn.who.int. Each file is the WHO z-score
# table for one indicator and one sex, with columns L, M, S and the SD
# columns. Column M is the median for that age and sex.
WHO_FILES = {
    "wfa_boys": "https://cdn.who.int/media/docs/default-source/child-growth/"
                "child-growth-standards/indicators/weight-for-age/"
                "wfa_boys_0-to-5-years_zscores.xlsx",
    "wfa_girls": "https://cdn.who.int/media/docs/default-source/child-growth/"
                 "child-growth-standards/indicators/weight-for-age/"
                 "wfa_girls_0-to-5-years_zscores.xlsx",
    # length/height-for-age is published in two workbooks per sex,
    # 0-2 years and 2-5 years, so each sex needs both.
    "lhfa_boys_0_2": "https://cdn.who.int/media/docs/default-source/"
                      "child-growth/child-growth-standards/indicators/"
                      "length-height-for-age/"
                      "lhfa_boys_0-to-2-years_zscores.xlsx",
    "lhfa_boys_2_5": "https://cdn.who.int/media/docs/default-source/"
                      "child-growth/child-growth-standards/indicators/"
                      "length-height-for-age/"
                      "lhfa_boys_2-to-5-years_zscores.xlsx",
    "lhfa_girls_0_2": "https://cdn.who.int/media/docs/default-source/"
                      "child-growth/child-growth-standards/indicators/"
                      "length-height-for-age/"
                      "lhfa_girls_0-to-2-years_zscores.xlsx",
    "lhfa_girls_2_5": "https://cdn.who.int/media/docs/default-source/"
                      "child-growth/child-growth-standards/indicators/"
                      "length-height-for-age/"
                      "lhfa_girls_2-to-5-years_zscores.xlsx",
}

# Ages we care about, in completed months. WHO tables are monthly from
# birth, so these are exact lookups rather than interpolations.
MONTHS_OF_INTEREST = [0, 1, 3, 6, 9, 12, 18, 24, 36, 48, 60]

CELL_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
TIMEOUT = 60
USER_AGENT = "MeridianResearch/1.0 (research helper)"


def fetch_bytes(url):
    """GET a URL and return the raw bytes, or None on failure."""
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            print(f"  {response.status}  {url.split('/')[-1]}  "
                  f"{len(response.headers.get('Content-Length', '?'))} hdr bytes")
            return response.read()
    except Exception as error:  # noqa: BLE001 - report and keep going
        print(f"  FAIL  {url}\n        {type(error).__name__}: {error}")
        return None


def read_shared_strings(zf):
    """Return the workbook's shared string table as a list of strings."""
    try:
        raw = zf.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ElementTree.fromstring(raw)
    out = []
    for si in root.findall(f"{CELL_NS}si"):
        # a shared string is usually one <t>, but can be split into runs
        parts = [node.text or "" for node in si.iter(f"{CELL_NS}t")]
        out.append("".join(parts))
    return out


def column_index(ref):
    """Turn 'AB12' into 27 (A is 1). Column letters are base-26."""
    letters = ""
    for character in ref:
        if character.isalpha():
            letters += character
        else:
            break
    number = 0
    for character in letters:
        number = number * 26 + (ord(character.upper()) - ord("A") + 1)
    return number


def read_rows(zf, shared):
    """Return every row of sheet1 as a dict of column number -> string."""
    raw = zf.read("xl/worksheets/sheet1.xml")
    root = ElementTree.fromstring(raw)
    rows = {}
    for row in root.iter(f"{CELL_NS}row"):
        cells = {}
        for cell in row.findall(f"{CELL_NS}c"):
            ref = cell.get("r") or ""
            index = column_index(ref)
            kind = cell.get("t")
            value_node = cell.find(f"{CELL_NS}v")
            inline = cell.find(f"{CELL_NS}is")
            if inline is not None:
                text = "".join(
                    node.text or "" for node in inline.iter(f"{CELL_NS}t")
                )
            elif value_node is None:
                text = ""
            elif kind == "s":
                raw = value_node.text or "0"
                number = int(float(raw))
                text = shared[number] if number < len(shared) else ""
            else:
                text = value_node.text or ""
            cells[index] = text.strip()
        rows[int(row.get("r") or 0)] = cells
    return rows


def to_float(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def collect(table):
    """Turn one parsed workbook into {month: (median, -2SD, +2SD)}."""
    rows, median_column = table
    by_month = {}
    for cells in rows.values():
        month = to_float(cells.get(1))
        if month is None:
            continue
        median = to_float(cells.get(median_column))
        if median is None:
            continue
        by_month[month] = (
            median,
            to_float(cells.get(median_column + 3)),   # SD2neg
            to_float(cells.get(median_column + 7)),   # SD2
        )
    return by_month


def report(label, tables):
    """Print the months we care about, merged across one or more workbooks."""
    by_month = {}
    for table in tables:
        by_month.update(collect(table))

    print(f"\n=== {label} ===")
    print("month   median    -2SD     +2SD")
    for month in MONTHS_OF_INTEREST:
        hit = by_month.get(month)
        if hit is None:
            # WHO tables use a 30.4375-days-per-month convention at the top
            # of the range, so fall back to the closest available month
            candidates = [key for key in by_month if abs(key - month) < 0.75]
            if not candidates:
                continue
            hit = by_month[min(candidates, key=lambda k: abs(k - month))]
        median, low, high = hit
        low_text = f"{low:.1f}" if low is not None else "  -  "
        high_text = f"{high:.1f}" if high is not None else "  -  "
        print(f"{month:>5}   {median:>6.2f}  {low_text:>7} {high_text:>7}")


def load_table(label):
    """Download and parse one workbook. Return (rows, median_column) or None."""
    url = WHO_FILES[label]
    blob = fetch_bytes(url)
    if blob is None:
        return None
    try:
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            shared = read_shared_strings(zf)
            rows = read_rows(zf, shared)
    except Exception as error:  # noqa: BLE001
        print(f"  parse failed: {type(error).__name__}: {error}")
        return None

    # find the header row so we know which column holds M
    median_column = None
    for cells in rows.values():
        values = list(cells.values())
        if "M" in values and "L" in values and "S" in values:
            median_column = next(
                index for index, value in cells.items() if value == "M"
            )
            break
    if median_column is None:
        median_column = 3
        print("  no L/M/S header row; assuming M is column 3")
    else:
        print(f"  header row found; M is column {median_column}")
    return rows, median_column


def build(label, parts):
    """Load every part of one indicator and print the merged result."""
    tables = []
    for part in parts:
        print(f"\n--- {part} ---")
        table = load_table(part)
        if table:
            tables.append(table)
    if tables:
        report(label, tables)
    else:
        print(f"\n=== {label}: nothing downloaded, skipping ===")


def main():
    build("weight-for-age BOYS", ["wfa_boys"])
    build("weight-for-age GIRLS", ["wfa_girls"])
    build("length/height-for-age BOYS", ["lhfa_boys_0_2", "lhfa_boys_2_5"])
    build("length/height-for-age GIRLS", ["lhfa_girls_0_2", "lhfa_girls_2_5"])


if __name__ == "__main__":
    main()