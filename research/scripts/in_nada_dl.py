"""Extract real download/resource links from a Census NADA catalogue page.

NADA renders resource blocks as /catalog/<id>/download/<did>/<file> and also
exposes a metadata JSON. This prints every such href found in the fetched HTML
plus the resource rows, so download URLs in the notes are observed.

Usage: python in_nada_dl.py <catalog-id> [<catalog-id> ...]
"""

import re
import ssl
import sys
import urllib.request

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
BASE = "https://censusindia.gov.in/nada/index.php"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
        return r.status, r.read().decode("utf-8", "replace")


def main() -> None:
    for cid in sys.argv[1:]:
        url = f"{BASE}/catalog/{cid}"
        st, html = get(url)
        title = re.search(r"<title>(.*?)</title>", html, re.S)
        title = re.sub(r"\s+", " ", title.group(1)).strip() if title else "?"
        print("=" * 78)
        print(f"catalog/{cid}  status={st}  bytes={len(html):,}")
        print(f"title: {title[:180]}\n")

        dls = []
        for m in re.finditer(r'href="([^"]*?/catalog/\d+/download/\d+/[^"]+)"', html):
            dls.append(m.group(1))
        seen = set()
        for d in dls:
            if d in seen:
                continue
            seen.add(d)
            full = d if d.startswith("http") else ("https://censusindia.gov.in" + d)
            print(f"  DOWNLOAD {full}")

        rows = re.findall(
            r'<tr[^>]*>(.*?)</tr>', html, re.S
        )
        for r in rows:
            cells = [
                re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", c)).strip()
                for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)
            ]
            cells = [c for c in cells if c]
            if cells and any("Nagpur" in c or "Maharashtra" in c or ".xlsx" in c for c in cells):
                print("  ROW " + " | ".join(cells)[:260])
        sys.stdout.flush()


if __name__ == "__main__":
    main()