"""Extract real Nagpur-area facility rows from two verified government pages.

  ESIC Nagpur  : https://sronagpur.esic.gov.in/ro-sro-list-empanelled-centers
  NABH / CGHS  : https://portal.nabh.co/frmViewCGHSRecommend.aspx?Type=Hospital&cityID=100

Prints only rows present in the fetched HTML.

Usage: python in_facilities.py
"""

import re
import ssl
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

ESIC = "https://sronagpur.esic.gov.in/ro-sro-list-empanelled-centers"
NABH = "https://portal.nabh.co/frmViewCGHSRecommend.aspx?Type=Hospital&cityID=100"
NABH_DIAG = (
    "https://portal.nabh.co/frmViewCGHSRecommend.aspx?Type=Diagnostic%20Centre&cityID=100"
)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=180, context=CTX) as r:
        raw = r.read()
        print(f"GET {url}\n  status={r.status} bytes={len(raw):,}")
        return raw.decode("utf-8", "replace")


def strip(h):
    h = re.sub(r"<script.*?</script>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<style.*?</style>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<br\s*/?>", " | ", h, flags=re.I)
    h = re.sub(r"</t[dh]>", " | ", h, flags=re.I)
    h = re.sub(r"<[^>]+>", " ", h)
    h = h.replace("&amp;", "&").replace("&nbsp;", " ").replace("&quot;", '"')
    h = h.replace("&#39;", "'").replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"[ \t]+", " ", h)


def rows_of(html):
    out = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S | re.I):
        cells = [
            re.sub(r"\s+", " ", strip(c)).strip(" |").strip()
            for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)
        ]
        cells = [c for c in cells if c]
        if cells:
            out.append(cells)
    return out


def main():
    for label, url in (
        ("ESIC Nagpur empanelled centres", ESIC),
        ("NABH CGHS-recommended HOSPITALS, Nagpur", NABH),
        ("NABH CGHS-recommended DIAGNOSTIC CENTRES, Nagpur", NABH_DIAG),
    ):
        print("=" * 78)
        print(label)
        try:
            html = get(url)
        except Exception as e:  # noqa: BLE001
            print(f"  FAILED: {type(e).__name__}: {e}\n")
            continue
        rows = rows_of(html)
        # drop header-ish rows
        data = [
            r
            for r in rows
            if not any(
                k in " ".join(r).lower()
                for k in ("hospital name", "recommendation no", "s.n", "serial", "sr no")
            )
        ]
        print(f"  table rows: {len(rows)}  (data-ish: {len(data)})")
        for r in data[:40]:
            print("   " + " ~ ".join(r)[:230])
        print()
        sys.stdout.flush()


if __name__ == "__main__":
    main()