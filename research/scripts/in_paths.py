"""Find template-literal API paths (${base}/...) in the MMC portal bundle.

Usage: python in_paths.py
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

BUNDLE = "https://www.maharashtramedicalcouncil.org.in/assets/index-BM8AQDEc.js"


def main():
    req = urllib.request.Request(BUNDLE, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=180, context=CTX) as r:
        js = r.read().decode("utf-8", "replace")
    print(f"GET {BUNDLE}  bytes={len(js):,}\n")

    # template literals that interpolate a base and start a path
    tmpl = set()
    for m in re.finditer(r'`\$\{[^}]+\}([^`]{0,90})`', js):
        frag = m.group(1)
        if "/" in frag:
            tmpl.add("/" + frag.lstrip("/"))
    print(f"interpolated paths ({len(tmpl)}):")
    for t in sorted(tmpl):
        print("   " + t.encode("ascii", "replace").decode("ascii"))

    print("\nplain path literals starting with /doctor or /rmp or /search:")
    for m in re.finditer(r'["\'`](/(?:doctor|rmp|search|public)[A-Za-z0-9_\-/${}]*)["\'`]', js):
        print("   " + m.group(1))


if __name__ == "__main__":
    main()