"""Pull route/path literals out of an MMC portal lazy-loaded JS chunk.

Usage: python in_chunk.py <chunk-url> [keyword ...]
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


def main():
    url = sys.argv[1]
    kws = [k.lower() for k in sys.argv[2:]] or ["doctor", "search", "api"]
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=180, context=CTX) as r:
        js = r.read().decode("utf-8", "replace")
        print(f"GET {url}\n  status={r.status} bytes={len(js):,}\n")

    lits = set()
    for m in re.finditer(r'["\'`]([^"\'`\\\n]{2,120})["\'`]', js):
        s = m.group(1)
        if s.startswith("http") or s.startswith("assets/"):
            continue
        if not s.startswith("/") and " " in s:
            continue
        low = s.lower()
        if any(k in low for k in kws):
            lits.add(s)
    print(f"matching literals ({len(lits)}):")
    for s in sorted(lits):
        print("   " + s.encode("ascii", "replace").decode("ascii"))

    # axios-style calls: show 160 chars around each occurrence of the keywords
    print("\ncontext windows:")
    for kw in kws:
        for m in list(re.finditer(re.escape(kw), js, re.I))[:4]:
            a = max(0, m.start() - 130)
            frag = js[a:m.end() + 130].replace("\n", " ")
            print(f"   [{kw}] ..." + frag.encode("ascii", "replace").decode("ascii"))


if __name__ == "__main__":
    main()