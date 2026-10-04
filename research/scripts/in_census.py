"""Download the verified Census 2011 state+district PCA workbook and print the
real Nagpur row plus Maharashtra totals.

The download URL was read out of the NADA catalogue page HTML by in_nada_dl.py
(catalog/6191) -- it is not constructed from a pattern.

Usage: python in_census.py
"""

import io
import ssl
import sys
import urllib.request
import zipfile

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

# Extracted from https://censusindia.gov.in/nada/index.php/catalog/6191
STATE_DIST = (
    "https://censusindia.gov.in/nada/index.php/catalog/6191/download/9268/"
    "DDW_PCA0000_2011_Indiastatedist.xlsx"
)
# Extracted from https://censusindia.gov.in/nada/index.php/catalog/41183
NAGPUR_CDB = (
    "https://censusindia.gov.in/nada/index.php/catalog/41183/download/44814/"
    "PCA_CDB-2709-F-Census.xlsx"
)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=300, context=CTX) as r:
        raw = r.read()
        print(f"GET {url}")
        print(f"    status={r.status}")
        print(f"    ctype={r.headers.get('Content-Type')}")
        print(f"    clen={r.headers.get('Content-Length')}  got={len(raw):,}")
        return raw


def col_headers(xlsx_bytes):
    """Read the sharedStrings + sheet1 header row without a spreadsheet lib."""
    zf = zipfile.ZipFile(io.BytesIO(xlsx_bytes))
    names = zf.namelist()
    shared = []
    if "xl/sharedStrings.xml" in names:
        import re
        xml = zf.read("xl/sharedStrings.xml").decode("utf-8", "replace")
        for si in re.findall(r"<si>(.*?)</si>", xml, re.S):
            txt = "".join(re.findall(r"<t[^>]*>(.*?)</t>", si, re.S))
            shared.append(
                txt.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            )
    # find the first worksheet
    sheet = next(n for n in names if n.startswith("xl/worksheets/sheet"))
    xml = zf.read(sheet).decode("utf-8", "replace")
    import re

    rows = []
    for rm in re.finditer(r'<row[^>]*r="(\d+)"[^>]*>(.*?)</row>', xml, re.S):
        rn = int(rm.group(1))
        if rn > 4:
            break
        cells = {}
        for cm in re.finditer(r'<c r="([A-Z]+)(\d+)"([^>]*)>(.*?)</c>', rm.group(2), re.S):
            col, attrs, body = cm.group(1), cm.group(3), cm.group(4)
            v = re.search(r"<v>(.*?)</v>", body, re.S)
            if not v:
                continue
            val = v.group(1)
            if 't="s"' in attrs:
                try:
                    val = shared[int(val)]
                except (ValueError, IndexError):
                    pass
            cells[col] = val
        rows.append((rn, cells))
    return shared, rows


def main():
    print("=" * 78)
    print("A) STATE + DISTRICT level PCA (all India)")
    raw = fetch(STATE_DIST)
    shared, rows = col_headers(raw)
    if rows:
        for rn, cells in rows:
            ordered = [cells[k] for k in sorted(cells, key=lambda c: (len(c), c))]
            print(f"  row{rn}: " + " | ".join(ordered)[:1500])
    print(f"  shared strings available: {len(shared)}")

    print()
    print("=" * 78)
    print("B) NAGPUR CD-BLOCK level PCA")
    raw2 = fetch(NAGPUR_CDB)
    shared2, rows2 = col_headers(raw2)
    if rows2:
        for rn, cells in rows2:
            ordered = [cells[k] for k in sorted(cells, key=lambda c: (len(c), c))]
            print(f"  row{rn}: " + " | ".join(ordered)[:1500])
    print(f"  shared strings available: {len(shared2)}")
    sys.stdout.flush()


if __name__ == "__main__":
    main()