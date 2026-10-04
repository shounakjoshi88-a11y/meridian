"""Download each candidate URL for real and report what pandas actually sees.

Research helper only. Nothing here is imported by the app.

A HEAD 200 is not proof. This script does a real GET, records the observed
status / content-type / bytes, writes the payload to research/tmp/, then tries
to parse it and prints real row and column counts. Anything that fails to
parse is reported as NOT USABLE rather than quietly passing.

Usage: python verify_downloads.py
"""

import io
import json
import os
import zipfile

import pandas as pd
import requests

TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tmp")
TIMEOUT = 120
UA = {"User-Agent": "meridian-dataset-research/1.0 (student project; non-commercial)"}

# Every URL here was read off a real landing page or a real API response first.
CANDIDATES = [
    {
        "key": "uci_296_diabetes130",
        "name": "Diabetes 130-US Hospitals for Years 1999-2008",
        "url": "https://archive.ics.uci.edu/static/public/296/data.csv",
    },
    {
        "key": "uci_827_sepsis",
        "name": "Sepsis Survival Minimal Clinical Records",
        "url": "https://archive.ics.uci.edu/static/public/827/data.csv",
    },
    {
        "key": "uci_891_cdc_diabetes",
        "name": "CDC Diabetes Health Indicators",
        "url": "https://archive.ics.uci.edu/static/public/891/data.csv",
    },
    {
        "key": "uci_760_gait",
        "name": "Multivariate Gait Data",
        "url": "https://archive.ics.uci.edu/static/public/760/data.csv",
    },
    {
        "key": "physionet_ptbxl",
        "name": "PTB-XL ptbxl_database.csv",
        "url": "https://physionet.org/files/ptb-xl/1.0.3/ptbxl_database.csv",
    },
    {
        "key": "physionet_ptbxl_s3",
        "name": "PTB-XL ptbxl_database.csv via open S3 bucket",
        "url": "https://physionet-open.s3.amazonaws.com/ptb-xl/1.0.3/ptbxl_database.csv",
    },
    {
        "key": "who_covid_daily",
        "name": "WHO COVID-19 global daily data",
        "url": "https://covid19.who.int/WHO-COVID-19-global-daily-data.csv",
    },
]


def parse(kind, payload):
    """Return (rows, cols, note). Never raises."""
    try:
        if kind == "zip":
            with zipfile.ZipFile(io.BytesIO(payload)) as z:
                names = [n for n in z.namelist() if not n.endswith("/")]
                biggest = max(names, key=lambda n: z.getinfo(n).file_size)
                with z.open(biggest) as fh:
                    df = pd.read_csv(fh, low_memory=False)
                return len(df), len(df.columns), f"zip member {biggest}"
        df = pd.read_csv(io.BytesIO(payload), low_memory=False)
        return len(df), len(df.columns), "csv"
    except Exception as e:  # noqa: BLE001
        return None, None, f"PARSE FAIL {type(e).__name__}: {str(e)[:70]}"


def main():
    os.makedirs(TMP, exist_ok=True)
    results = []

    for c in CANDIDATES:
        url = c["url"]
        print("=" * 100)
        print(c["name"])
        print(f"  {url}")
        row: dict[str, object] = {"key": c["key"], "name": c["name"], "url": url}

        try:
            r = requests.get(url, timeout=TIMEOUT, headers=UA, stream=True)
        except Exception as e:  # noqa: BLE001
            print(f"  REQUEST FAIL {type(e).__name__}: {str(e)[:100]}")
            row.update(status="REQFAIL", ctype="", nbytes=0, rows=None, cols=None, note=str(e)[:60])
            results.append(row)
            continue

        payload = r.content
        r.close()
        ctype = r.headers.get("Content-Type", "")
        print(f"  status      : {r.status_code}")
        print(f"  content-type: {ctype}")
        print(f"  bytes       : {len(payload):,}")
        row.update(status=r.status_code, ctype=ctype, nbytes=len(payload))

        # Is it actually a CSV, or an HTML error page served with 200?
        head = payload[:200].decode("utf-8", "replace")
        looks_html = "<!DOCTYPE" in head or "<html" in head
        if looks_html:
            print("  !! payload starts with HTML, not data")
            print("     " + head.replace("\n", " ")[:150])
            row.update(rows=None, cols=None, note="HTML page, not data")
            results.append(row)
            continue

        kind = "zip" if payload[:2] == b"PK" else "csv"
        nrows, ncols, note = parse(kind, payload)
        print(f"  format      : {kind}")
        print(f"  rows        : {nrows:,}" if nrows else f"  rows        : {note}")
        print(f"  columns     : {ncols}" if ncols else "")
        row.update(rows=nrows, cols=ncols, note=note)

        if nrows:
            df = pd.read_csv(io.BytesIO(payload), nrows=0, low_memory=False)
            names = list(df.columns)
            print(f"  col names   : {names[:12]}{' ...' if len(names) > 12 else ''}")
            row["columns_list"] = names
            path = os.path.join(TMP, f"{c['key']}.csv")
            with open(path, "wb") as f:
                f.write(payload)
            print(f"  saved       : {os.path.relpath(path, os.path.join(TMP, '..'))}")

        results.append(row)

    print("=" * 100)
    with open(os.path.join(TMP, "verify_results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1)
    print("wrote tmp/verify_results.json")


if __name__ == "__main__":
    main()
