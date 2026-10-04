"""Extract real Nagpur / Maharashtra district totals + literacy from the
verified Census 2011 state+district PCA workbook.

Reads every worksheet in the xlsx (no spreadsheet library needed) and prints
the header row plus any row whose state/district cells mention Maharashtra or
Nagpur. Numbers printed are exactly what the workbook contains.

Usage: python in_census2.py
"""

import io
import re
import ssl
import urllib.request
import zipfile

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

# URL read out of https://censusindia.gov.in/nada/index.php/catalog/6191
STATE_DIST = (
    "https://censusindia.gov.in/nada/index.php/catalog/6191/download/9268/"
    "DDW_PCA0000_2011_Indiastatedist.xlsx"
)


def unescape(s):
    return (
        s.replace("&lt;", "<").replace("&gt;", ">")
        .replace("&quot;", '"').replace("&apos;", "'").replace("&amp;", "&")
    )


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=300, context=CTX) as r:
        raw = r.read()
        print(f"GET {url}\n    status={r.status} ctype={r.headers.get('Content-Type')}"
              f" clen={r.headers.get('Content-Length')} got={len(raw):,}")
        return raw


def load(raw):
    zf = zipfile.ZipFile(io.BytesIO(raw))
    names = zf.namelist()

    shared = []
    if "xl/sharedStrings.xml" in names:
        xml = zf.read("xl/sharedStrings.xml").decode("utf-8", "replace")
        for si in re.findall(r"<si>(.*?)</si>", xml, re.S):
            shared.append(unescape("".join(re.findall(r"<t[^>]*>(.*?)</t>", si, re.S))))

    print(f"  worksheets: {[n for n in names if 'worksheets' in n]}")
    sheets = {}
    for n in sorted(x for x in names if re.match(r"xl/worksheets/sheet\d+\.xml$", x)):
        xml = zf.read(n).decode("utf-8", "replace")
        rows = {}
        for rm in re.finditer(r'<row[^>]*?r="(\d+)"[^>]*>(.*?)</row>', xml, re.S):
            rn = int(rm.group(1))
            cells = {}
            for cm in re.finditer(r'<c r="([A-Z]+)\d+"([^>]*)(?:/>|>(.*?)</c>)',
                                  rm.group(2), re.S):
                col, attrs, body = cm.group(1), cm.group(2), cm.group(3) or ""
                v = re.search(r"<v>(.*?)</v>", body, re.S)
                if not v:
                    continue
                val = v.group(1)
                if 't="s"' in attrs:
                    try:
                        val = shared[int(val)]
                    except (ValueError, IndexError):
                        pass
                cells[col] = unescape(val)
            rows[rn] = cells
        sheets[n] = rows
    return sheets


def colkey(c):
    """A..Z, AA.. so sorting is spreadsheet order not string order."""
    n = 0
    for ch in c:
        n = n * 26 + (ord(ch) - 64)
    return n


def main():
    raw = fetch(STATE_DIST)
    sheets = load(raw)

    for name, rows in sheets.items():
        if not rows:
            continue
        print("=" * 78)
        print(f"{name}: {len(rows)} rows")
        header = rows.get(1, {})
        hdr = [header[k] for k in sorted(header, key=colkey)]
        print("  HEADER: " + " | ".join(hdr))

        hits = []
        for rn, cells in rows.items():
            if rn == 1:
                continue
            joined = " ".join(str(v) for v in cells.values()).lower()
            if "nagpur" in joined or "maharashtra" in joined:
                hits.append((rn, cells))
        print(f"  rows mentioning Maharashtra/Nagpur: {len(hits)}")
        for rn, cells in hits[:14]:
            ordered = [cells[k] for k in sorted(cells, key=colkey)]
            print(f"   r{rn}: " + " | ".join(ordered)[:900])
        print()
        sys.stdout.flush()


import sys  # noqa: E402  (used above)


if __name__ == "__main__":
    main()