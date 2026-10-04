"""Pull verified STD / area-code rows for Maharashtra + Nagpur.

Reads the two GitHub raw files whose exact paths were discovered from the
GitHub contents API (not guessed), then prints only what the bytes contain.

Usage:  python in_std.py
"""

import csv
import io
import ssl
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) research/1.0"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

STD_URL = "https://raw.githubusercontent.com/kishorek/India-Codes/master/csv/stdcodes.csv"
RTO_URL = "https://raw.githubusercontent.com/kishorek/India-Codes/master/csv/RTO.csv"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
        raw = r.read()
        print(f"GET {url}\n    status={r.status} ctype={r.headers.get('Content-Type')} "
              f"clen={r.headers.get('Content-Length')} got={len(raw)}")
        return raw.decode("utf-8", "replace")


def main():
    print("=" * 78)
    print("STD.csv -- all Maharashtra / Nagpur rows")
    text = get(STD_URL)
    reader = csv.DictReader(io.StringIO(text))
    print("    columns:", reader.fieldnames)
    rows = list(reader)
    print("    total rows:", len(rows))
    # stdcodes.csv carries only City + Code, so match on the city token itself.
    nag = [r for r in rows if "nagpur" in str(r.get("City", "")).lower()]
    print(f"    rows whose City contains 'nagpur': {len(nag)}")
    for r in nag:
        print("      " + " | ".join(f"{k}={str(v).strip()}" for k, v in r.items()))

    mh_cities = [
        r for r in rows
        if str(r.get("City", "")).strip().lower() in {
            "mumbai", "pune", "nagpur", "nashik", "aurangabad", "solapur",
            "kolhapur", "amravati", "nanded", "thane", "ratnagiri", "ahmednagar",
        }
    ]
    print(f"    reference rows for major Maharashtra cities: {len(mh_cities)}")
    for r in mh_cities:
        print("      " + " | ".join(f"{k}={str(v).strip()}" for k, v in r.items()))

    print("=" * 78)
    print("RTO.csv -- Nagpur rows")
    text2 = get(RTO_URL)
    reader2 = csv.DictReader(io.StringIO(text2))
    print("    columns:", reader2.fieldnames)
    rows2 = list(reader2)
    print("    total rows:", len(rows2))
    nag2 = [
        r for r in rows2 if any("nagpur" in str(v).lower() for v in r.values())
    ]
    print(f"    rows mentioning Nagpur: {len(nag2)}")
    for r in nag2[:40]:
        print("      " + " | ".join(f"{k}={str(v).strip()}" for k, v in r.items()))


if __name__ == "__main__":
    main()