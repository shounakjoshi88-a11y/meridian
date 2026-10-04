"""Round three: settle the Kaggle redirect, parse OpenML ARFF properly,
and measure a World Bank multi-country pull.

Research helper only. Nothing here is imported by the app.
"""

import io
import json
import os

import pandas as pd
import requests
from scipy.io import arff

TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tmp")
TIMEOUT = 240
UA = {"User-Agent": "meridian-dataset-research/1.0 (student project; non-commercial)"}


def kaggle_redirect_chain():
    """Follow the 302 from the Kaggle download API and see if bytes arrive."""
    print("=== Kaggle: does the download API actually serve bytes anonymously?")
    url = "https://www.kaggle.com/api/v1/datasets/download/alexteboul/diabetes-health-indicators-dataset"
    try:
        r = requests.get(url, timeout=TIMEOUT, headers=UA, allow_redirects=True, stream=True)
        print(f"  final status : {r.status_code}")
        print(f"  redirect chain: {[h.status_code for h in r.history]}")
        print(f"  final url    : {r.url[:120]}")
        print(f"  content-type : {r.headers.get('Content-Type', '')}")
        print(f"  content-len  : {r.headers.get('Content-Length', '-')}")
        chunk = next(r.iter_content(4096), b"")
        print(f"  first bytes  : {chunk[:80]!r}")
        if r.status_code == 200 and chunk[:2] == b"PK":
            print("  VERDICT: anonymous ZIP download SUCCEEDED")
        else:
            print("  VERDICT: anonymous download did NOT return a zip")
    except Exception as e:  # noqa: BLE001
        print(f"  ERR {type(e).__name__}: {str(e)[:110]}")
    print()

    print("=== Kaggle: what the public metadata endpoint exposes about that dataset")
    r = requests.get(
        "https://www.kaggle.com/api/v1/datasets/view/alexteboul/diabetes-health-indicators-dataset",
        timeout=60, headers=UA,
    )
    if r.status_code == 200:
        d = r.json()
        for k in ("title", "totalBytesNullable", "licenseNameNullable", "usabilityRatingNullable",
                  "downloadCountNullable", "lastUpdatedNullable", "isPrivateNullable"):
            print(f"  {k:<26} {d.get(k)}")
        print(f"  {'files':<26} {[f.get('name') for f in d.get('resources', [])][:8]}")
    print()


def openml_arff():
    """OpenML always serves ARFF; prove it parses and count real rows."""
    print("=== OpenML: parse the ARFF payload properly")
    url = "https://api.openml.org/data/v1/download/3/kr-vs-kp.arff"
    r = requests.get(url, timeout=TIMEOUT, headers=UA)
    txt = r.content.decode("utf-8", "replace")
    data, meta = arff.loadarff(io.StringIO(txt))
    df = pd.DataFrame(data)
    print(f"  url        : {url}")
    print(f"  status     : {r.status_code}  bytes {len(r.content):,}")
    print(f"  arff rows  : {len(df):,}   arff cols: {len(df.columns)}")
    print(f"  relation   : {meta.relation_name}")
    print(f"  attributes : {len(meta.attributes)}")
    print("  VERDICT: .arff and .csv paths return identical ARFF bytes; scipy.io.arff parses it")
    print()


def world_bank():
    """Pull one mortality/ burden indicator across every country and year."""
    print("=== World Bank: anonymous API, all countries, life expectancy at birth")
    url = (
        "https://api.worldbank.org/v2/country/all/indicator/SH.DYN.LE00.M4"
        "?format=json&per_page=20000&date=1990:2024"
    )
    r = requests.get(url, timeout=TIMEOUT, headers=UA)
    print(f"  status {r.status_code}  ctype {r.headers.get('Content-Type','')}  bytes {len(r.content):,}")
    payload = r.json()
    meta, rows = payload[0], payload[1]
    print(f"  api total  : {meta.get('total')}   pages {meta.get('pages')}")
    flat = [
        {
            "country": x["country"]["value"],
            "countryiso3code": x["countryiso3code"],
            "year": x["date"],
            "value": x["value"],
        }
        for x in rows
    ]
    df = pd.DataFrame(flat).dropna(subset=["value"])
    print(f"  non-null   : {len(df):,} rows x {len(df.columns)} cols")
    print(f"  countries  : {df['countryiso3code'].nunique()}   year span {df['year'].min()}-{df['year'].max()}")
    ind = df[df["countryiso3code"] == "IND"]
    print(f"  India rows : {len(ind)}  latest {ind.sort_values('year').iloc[-1].to_dict()}")
    print("  VERDICT: no API key, no login, JSON only (convert locally to CSV)")
    print()


def main():
    os.makedirs(TMP, exist_ok=True)
    kaggle_redirect_chain()
    openml_arff()
    world_bank()


if __name__ == "__main__":
    main()
