"""Download the two verified open PIN datasets and extract real Nagpur rows.

Both URLs were confirmed 200 with observed Content-Length before this script
was written. This script records the bytes it actually received and prints
only rows the files really contain, so locality names and PIN codes written
into the notes are observed rather than remembered.

Usage:
    python extract_nagpur.py
"""

import csv
import io
import ssl
import urllib.request

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
CTX = ssl.create_default_context()

# Confirmed 200 / text/plain before use.
SOURCES = {
    "thatisuday_indian-pincode-database": (
        "https://raw.githubusercontent.com/thatisuday/indian-pincode-database/"
        "master/res/all_india_pin_code.csv"
    ),
    "kishorek_India-Codes": (
        "https://raw.githubusercontent.com/kishorek/India-Codes/master/csv/pincodes.csv"
    ),
}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept": "*/*", "Accept-Encoding": "identity"}
    )
    with urllib.request.urlopen(req, timeout=180, context=CTX) as r:
        print(f"  GET {url}")
        print(f"      status={r.status} bytes={r.headers.get('Content-Length')}")
        return r.read()


def parse_loose(text: str):
    """Both files are delimiter=',' but thatisuday pads fields with spaces."""
    return csv.DictReader(io.StringIO(text))


def main() -> None:
    results = {}

    for name, url in SOURCES.items():
        print("=" * 78)
        print(name)
        raw = fetch(url)
        text = raw.decode("utf-8", "replace")
        reader = parse_loose(text)
        rows = list(reader)
        print(f"      total rows parsed: {len(rows)}")
        print(f"      columns: {reader.fieldnames}")

        hits = [
            r
            for r in rows
            if "nagpur" in " ".join(str(v) for v in r.values()).lower()
        ]
        print(f"      rows mentioning 'nagpur': {len(hits)}")
        results[name] = (reader.fieldnames, hits)

    # ------------------------------------------------------------------
    # thatisuday: the richest locality dataset -> full Nagpur listing
    # ------------------------------------------------------------------
    fields, hits = results["thatisuday_indian-pincode-database"]
    district_field = next((f for f in fields if f and "district" in f.lower()), None)
    state_field = next((f for f in fields if f and "state" in f.lower()), None)

    print("=" * 78)
    print("NAGPUR DISTRICT rows, thatisuday dataset (all localities)")
    if district_field:
        seen = set()
        nag = []
        for r in hits:
            if "nagpur" not in (r.get(district_field) or "").lower():
                continue
            key = (
                (r.get("pincode") or "").strip(),
                (r.get("officeName") or "").strip(),
                (r.get("taluk") or "").strip(),
            )
            if key in seen:
                continue
            seen.add(key)
            nag.append(r)
        nag.sort(key=lambda r: (r.get("pincode") or "", r.get("officeName") or ""))
        print(f"distinct Nagpur-district rows: {len(nag)}")
        pin_set = set()
        office_set = set()
        for r in nag:
            pin = (r.get("pincode") or "").strip()
            off = (r.get("officeName") or "").strip()
            tal = (r.get("taluk") or "").strip()
            if pin:
                pin_set.add(pin)
            if off:
                office_set.add(off)
            print(f"  {pin}  {off:<46} taluk={tal}")
        print(f"distinct NAGPUR PIN codes: {len(pin_set)}")
        print(f"distinct post office names: {len(office_set)}")
        print("PIN list: " + ", ".join(sorted(pin_set)))

        if state_field:
            states = {(r.get(state_field) or "").strip() for r in nag}
            print(f"state values seen: {states}")

    # ------------------------------------------------------------------
    # kishorek: independent second source -> cross-check PIN overlap
    # ------------------------------------------------------------------
    fields2, hits2 = results["kishorek_India-Codes"]
    dist2 = next((f for f in fields2 if f and "district" in f.lower()), None)
    pin2_field = next((f for f in fields2 if f and "pincode" in f.lower()), None)
    print("=" * 78)
    print("NAGPUR rows, kishorek dataset (cross-check)")
    if dist2 and pin2_field:
        nag2 = sorted(
            {
                (r.get(pin2_field) or "").strip()
                for r in hits2
                if "nagpur" in (r.get(dist2) or "").lower()
                and (r.get(pin2_field) or "").strip()
            }
        )
        print(f"distinct PIN codes: {len(nag2)}")
        print("PIN list: " + ", ".join(nag2))
        if district_field:
            a = {
                (r.get("pincode") or "").strip()
                for r in results["thatisuday_indian-pincode-database"][1]
                if "nagpur" in (r.get(district_field) or "").lower()
            }
            both = sorted(a & set(nag2))
            only_k = sorted(set(nag2) - a)
            only_t = sorted(a - set(nag2))
            print(f"agreed by BOTH datasets: {len(both)}")
            print(f"only in kishorek: {len(only_k)} -> {only_k}")
            print(f"only in thatisuday: {len(only_t)} -> {only_t}")


if __name__ == "__main__":
    main()