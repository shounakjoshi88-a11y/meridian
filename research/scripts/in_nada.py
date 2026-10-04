"""Parse a Census NADA catalogue search page for real table entries + downloads.

Prints only hrefs and titles actually present in the fetched HTML, so any
resource id written into the notes is observed rather than guessed.

Usage: python in_nada.py <nada-search-url>
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


def main() -> None:
    url = sys.argv[1]
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
        html = r.read().decode("utf-8", "replace")
        print(f"GET {url}\n  status={r.status} bytes={len(html):,}\n")

    # catalog/<id> links carry the resource ids
    ids = sorted(set(re.findall(r"/catalog/(\d+)", html)), key=int)
    print(f"catalog ids on page ({len(ids)}): {', '.join(ids)}\n")

    # study links carry the ORGI table identifiers (e.g. PC11_PCA-SCST-SC-2709)
    studies = sorted(set(re.findall(r"/catalog/study/([A-Za-z0-9_\-]+)", html)))
    print(f"study ids on page ({len(studies)}):")
    for s in studies:
        print("   " + s)

    # any direct download hrefs
    dl = sorted(set(re.findall(r'href="([^"]*/download/[^"]+)"', html)))
    print(f"\ndirect download hrefs ({len(dl)}):")
    for d in dl[:60]:
        print("   " + d)

    # titles: pair each catalog id with the nearest heading text
    print("\nsearch result titles:")
    for m in re.finditer(
        r'<a[^>]+href="([^"]*/catalog/(\d+)[^"]*)"[^>]*>(.*?)</a>', html, re.S
    ):
        title = re.sub(r"<[^>]+>", "", m.group(3))
        title = re.sub(r"\s+", " ", title).strip()
        if title:
            print(f"   [{m.group(2)}] {title[:150]}")


if __name__ == "__main__":
    main()