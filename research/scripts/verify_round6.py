"""Round six: fix the World Bank pagination, check UCI id 9 and 917, and
pin down an openly downloadable Indian health dataset.

Research helper only. Nothing here is imported by the app.
"""

import io
import json

import pandas as pd
import requests

TIMEOUT = 240
UA = {"User-Agent": "meridian-dataset-research/1.0 (student project; non-commercial)"}


def show(label, url, **kw):
    r = requests.get(url, timeout=TIMEOUT, headers=UA, **kw)
    print(f"  {label}: {r.status_code} {r.headers.get('Content-Type','')[:34]} {len(r.content):,} bytes")
    return r


def world_bank_diagnose():
    print("=" * 100)
    print("WORLD BANK API - diagnose the per_page cap")
    print("=" * 100)
    base = "https://api.worldbank.org/v2/country/all/indicator/SH.DYN.LE00.M4"
    for per in (5, 500, 1000, 20000):
        url = f"{base}?format=json&per_page={per}&date=1990:2024"
        r = show(f"per_page={per:<6}", url)
        try:
            p = r.json()
        except Exception:
            print(f"      not json: {r.content[:160]!r}")
            continue
        if isinstance(p, list) and len(p) == 2:
            print(f"      total={p[0].get('total')}  pages={p[0].get('pages')}  rows_returned={len(p[1])}")
        else:
            print(f"      payload: {str(p)[:220]}")

    print("\n  -> now page properly and flatten to a real table")
    url = f"{base}?format=json&per_page=1000&date=1990:2024&page=1"
    r = requests.get(url, timeout=TIMEOUT, headers=UA)
    p = r.json()
    total, pages = p[0]["total"], p[0]["pages"]
    rows = list(p[1])
    for page in range(2, pages + 1):
        rr = requests.get(f"{base}?format=json&per_page=1000&date=1990:2024&page={page}",
                          timeout=TIMEOUT, headers=UA)
        rows.extend(rr.json()[1])
    df = pd.DataFrame(
        [{"country": x["country"]["value"], "iso3": x["countryiso3code"],
          "year": x["date"], "value": x["value"]} for x in rows]
    )
    print(f"  fetched {len(df):,} rows over {pages} pages (API total {total})")
    nn = df.dropna(subset=["value"])
    print(f"  non-null {len(nn):,} rows x {len(nn.columns)} cols")
    print(f"  countries {nn['iso3'].nunique()}   years {nn['year'].min()}-{nn['year'].max()}")
    ind = nn[nn["iso3"] == "IND"].sort_values("year")
    print(f"  INDIA: {len(ind)} rows; 2023 = {ind.iloc[-1]['value']} "
          f"(series {ind['year'].iloc[0]}-{ind['year'].iloc[-1]})")
    print(f"  INDIA decadal means: "
          f"{ {d: round(float(ind[ind['year'].astype(int).isin(range(d, d + 10))]['value'].mean()), 1) for d in (1990, 2000, 2010, 2020)} }")
    print("  VERDICT: anonymous, no key, JSON; ~" f"{len(nn):,} usable rows across {nn['iso3'].nunique()} countries")
    print()


def uci_ids():
    print("=" * 100)
    print("UCI id sanity check (API metadata vs what actually downloads)")
    print("=" * 100)
    for uid in (9, 45, 17, 917, 918, 944):
        try:
            d = requests.get(f"https://archive.ics.uci.edu/api/dataset?id={uid}",
                             timeout=60, headers=UA).json()
        except Exception as e:  # noqa: BLE001
            print(f"  id={uid}: ERR {type(e).__name__}")
            continue
        if "data" not in d:
            print(f"  id={uid}: {str(d)[:150]}")
            continue
        rec = d["data"]
        print(f"  id={uid:<5} {rec.get('name')}")
        print(f"        api says {rec.get('num_instances')} x {rec.get('num_features')}  "
              f"area={rec.get('area')}  doi={rec.get('dataset_doi')}")
        url = rec.get("data_url")
        if url:
            r = requests.get(url, timeout=TIMEOUT, headers=UA)
            if r.status_code == 200 and not r.content[:5].lower().startswith(b"<!doc"):
                df = pd.read_csv(io.BytesIO(r.content), low_memory=False)
                print(f"        DOWNLOADED {len(df):,} rows x {len(df.columns)} cols  "
                      f"cols={list(df.columns)[:9]}")
            else:
                print(f"        download status {r.status_code}")
    print()


def indian_sources():
    print("=" * 100)
    print("OPEN INDIAN HEALTH DATA - what is actually reachable with no login")
    print("=" * 100)
    cands = [
        ("World Bank IND life expectancy",
         "https://api.worldbank.org/v2/country/IND/indicator/SH.DYN.LE00.M4?format=json&per_page=100"),
        ("World Bank IND under-5 mortality",
         "https://api.worldbank.org/v2/country/IND/indicator/SH.DYN.MORT?format=json&per_page=100"),
        ("WHO GHO OData indicator sample",
         "https://ghoapi.azureedge.net/api/WHOSIS_000001?$top=3"),
        ("UCI ILPD (Indian Liver Patient Dataset)",
         "https://archive.ics.uci.edu/static/public/225/data.csv"),
    ]
    for label, url in cands:
        r = show(label, url)
        try:
            body = r.json()
        except Exception:
            try:
                df = pd.read_csv(io.BytesIO(r.content), low_memory=False)
                print(f"      csv: {len(df):,} rows x {len(df.columns)} cols  cols={list(df.columns)[:8]}")
            except Exception as e:  # noqa: BLE001
                print(f"      unparsed: {r.content[:120]!r} ({type(e).__name__})")
            continue
        if isinstance(body, dict) and "value" in body:
            print(f"      odata rows returned: {len(body['value'])}  next={body.get('@odata.nextLink','-')}")
            if body["value"]:
                print(f"      sample keys: {list(body['value'][0])[:10]}")
        elif isinstance(body, list) and len(body) == 2:
            print(f"      WB total={body[0].get('total')} rows={len(body[1])}")
            if body[1]:
                print(f"      sample: {json.dumps(body[1][0])[:200]}")
        print()


def main():
    world_bank_diagnose()
    uci_ids()
    indian_sources()


if __name__ == "__main__":
    main()
