"""do_links.py - extract the actual download links published on the DO and
Orphadata download pages. Only URLs present in the fetched HTML are printed."""

import re
import ssl
import sys
import urllib.request

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180, context=CTX) as r:
        body = r.read().decode("utf-8", "replace")
        print("GET %s" % url)
        print("  http        : %s" % r.status)
        print("  content-type: %s" % r.headers.get("Content-Type"))
        print("  bytes       : %s" % format(len(r.read() or b"") + len(body), ","))
        return body


for url in sys.argv[1:]:
    html = get(url)
    hrefs = re.findall(r'href="([^"]+)"', html)
    keep = [h for h in hrefs if re.search(r"\.(obo|owl|json|owl\.gz|obo\.gz)$|purl\.obolibrary|/data/ontologies|/releases/|LICENSE|license", h, re.I)]
    print("\n  --- candidate download/license links found in the page ---")
    seen = set()
    for h in keep:
        if h in seen:
            continue
        seen.add(h)
        print("   %s" % h)
    print()