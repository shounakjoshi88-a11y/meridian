"""Extract API base URLs / routes from the MMC portal JS bundle, and list the
ABDM sample-hip spec files.

Both are read from bytes actually fetched; nothing is assumed.

Usage: python in_mmc_abdm.py
"""

import json
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

MMC_JS = "https://www.maharashtramedicalcouncil.org.in/assets/index-BM8AQDEc.js"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=180, context=CTX) as r:
        return r.status, r.headers.get("Content-Type"), r.read()


def main():
    print("=" * 78)
    print("MMC portal JS bundle")
    st, ct, raw = get(MMC_JS)
    js = raw.decode("utf-8", "replace")
    print(f"  status={st} ctype={ct} bytes={len(raw):,}")

    hosts = sorted(set(re.findall(r'https?://[A-Za-z0-9.\-]*maharashtramedicalcouncil[A-Za-z0-9.\-]*', js)))
    print(f"\n  MMC hosts referenced ({len(hosts)}):")
    for h in hosts:
        print("    " + h)

    paths = sorted(set(re.findall(r'"(/api/[A-Za-z0-9_\-/{}\.]+)"', js)))
    print(f"\n  /api/ paths ({len(paths)}):")
    for p in paths[:60]:
        print("    " + p)

    # any route-looking strings around 'doctor'
    doc = sorted(set(re.findall(r'["\'`](/[A-Za-z0-9_\-/]*doctor[A-Za-z0-9_\-/]*)["\'`]', js, re.I)))
    print(f"\n  doctor-related routes ({len(doc)}):")
    for d in doc[:40]:
        print("    " + d)

    for kw in ("registration", "regNo", "regno", "MMC Reg", "mmc_reg"):
        if kw.lower() in js.lower():
            print(f"\n  keyword present in bundle: {kw!r}")
            for m in list(re.finditer(re.escape(kw), js, re.I))[:3]:
                s = max(0, m.start() - 90)
                frag = js[s:m.end() + 90].replace("\n", " ")
                print("    ..." + frag.encode("ascii", "replace").decode("ascii"))

    # concrete endpoint paths: any string literal that looks like an api route
    print("\n  candidate endpoint literals containing 'doctor':")
    cands = set()
    for m in re.finditer(r'["\'`]([^"\'`]{4,90})["\'`]', js):
        s = m.group(1)
        low = s.lower()
        if "doctor" in low and ("/" in s) and not s.startswith("http"):
            cands.add(s)
    for c in sorted(cands)[:60]:
        print("    " + c)

    print("\n  candidate endpoint literals containing 'search' or 'register':")
    cands2 = set()
    for m in re.finditer(r'["\'`]([^"\'`]{4,90})["\'`]', js):
        s = m.group(1)
        low = s.lower()
        if any(k in low for k in ("search", "register", "rmp")) and "/" in s and not s.startswith("http"):
            cands2.add(s)
    for c in sorted(cands2)[:60]:
        print("    " + c)

    print()
    print("=" * 78)
    print("ABDM sample-hip specs")
    st2, ct2, raw2 = get(
        "https://api.github.com/repos/NHA-ABDM/ABDM-wrapper/contents/sample-hip/specs"
    )
    data = json.loads(raw2.decode("utf-8", "replace"))
    print(f"  status={st2} entries={len(data)}")
    for e in data:
        print(f"    {e['name']:<40} {e['size']:>8,}  {e.get('download_url')}")


if __name__ == "__main__":
    main()