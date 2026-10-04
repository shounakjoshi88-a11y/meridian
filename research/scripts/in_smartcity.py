"""List the dataset/resource titles embedded in the Smart Cities Nagpur page and
confirm the data.gov.in catalogue search page responds.

Both pages were confirmed 200 first. Titles are read out of the Nuxt payload.

Usage: python in_smartcity.py
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

NAGPUR = "https://smartcities.data.gov.in/cities/Nagpur"
DGI = "https://www.data.gov.in/catalogs?filters%5Bstate%5D=Maharashtra"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=180, context=CTX) as r:
        return r.status, r.headers.get("Content-Type"), r.read()


def main():
    st, ct, raw = get(NAGPUR)
    html = raw.decode("utf-8", "replace")
    print(f"GET {NAGPUR}\n  status={st} ctype={ct} bytes={len(raw):,}\n")

    # Nuxt embeds state as window.__NUXT__=(function(...){return {...}})
    titles = re.findall(r'"title"\s*:\s*"((?:[^"\\]|\\.){3,140})"', html)
    seen, out = set(), []
    for t in titles:
        t = t.encode().decode("unicode_escape", "replace")
        if t not in seen:
            seen.add(t)
            out.append(t)
    print(f"distinct \"title\" values ({len(out)}):")
    for t in out[:70]:
        print("   " + t.encode("ascii", "replace").decode("ascii"))

    ids = sorted(set(re.findall(r'"(?:resource_?id|catalog_?id|id)"\s*:\s*"([0-9a-f]{8}-[0-9a-f-]{27})"', html)))
    print(f"\nUUID-looking resource/catalog ids ({len(ids)}):")
    for i in ids[:25]:
        print("   " + i)

    lic = re.findall(r'"(?:license|licence)"\s*:\s*"([^"]{0,80})"', html)
    print(f"\nlicense strings: {sorted(set(lic))[:10]}")

    print("\n" + "=" * 78)
    st2, ct2, raw2 = get(DGI)
    print(f"GET {DGI}\n  status={st2} ctype={ct2} bytes={len(raw2):,}")
    h2 = raw2.decode("utf-8", "replace")
    m = re.search(r"of\s*<b>([\d,]+)</b>", h2)
    print(f"  catalogue count text: {m.group(0) if m else 'not found'}")
    ids2 = sorted(set(re.findall(r"/resource/([0-9a-f-]{36})", h2)))
    print(f"  resource uuid links on page ({len(ids2)}):")
    for i in ids2[:15]:
        print("   https://www.data.gov.in/resource/" + i)


if __name__ == "__main__":
    main()