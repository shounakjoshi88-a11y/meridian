"""Round seven: find the exact World Bank query shape that returns real rows.

Research helper only. Nothing here is imported by the app.
The date-range parameter was rejected with id 120; this isolates which
parameter is at fault instead of guessing.
"""

import pandas as pd
import requests

TIMEOUT = 240
UA = {"User-Agent": "meridian-dataset-research/1.0 (student project; non-commercial)"}
BASE = "https://api.worldbank.org/v2/country/all/indicator/SH.DYN.LE00.M4"

VARIANTS = [
    "no params beyond format",
    "per_page=5",
    "per_page=5&date=1990:2023",
    "per_page=5&date=1990%3A2023",
    "per_page=5&mrnev=1",
    "per_page=5&page=1",
    "per_page=1000&mrnev=1",
    "per_page=1000&date=1990:2023&page=1",
]


def build(q):
    return f"{BASE}?format=json" + (f"&{q}" if q else "")


def main():
    print("=" * 100)
    print("WORLD BANK QUERY SHAPE ISOLATION")
    print("=" * 100)
    good_q = None
    for q in VARIANTS:
        url = build(q)
        r = requests.get(url, timeout=TIMEOUT, headers=UA)
        try:
            p = r.json()
        except Exception:  # noqa: BLE001
            print(f"  {q:<36} {r.status_code}  not json")
            continue
        if isinstance(p, list) and len(p) == 2 and isinstance(p[0], dict) and "total" in p[0]:
            print(f"  {q:<36} {r.status_code}  total={p[0]['total']}  pages={p[0]['pages']}  "
                  f"returned={len(p[1])}   <-- WORKS")
            good_q = q
        else:
            print(f"  {q:<36} {r.status_code}  {str(p)[:110]}")

    if good_q is None:
        print("\n  no working shape found")
        return

    print("\n  -> paging the working shape to build a real table")
    per = 1000 if "per_page=1000" in good_q else int(good_q.split("per_page=")[1].split("&")[0])
    first = requests.get(build(f"per_page={per}&mrnev=1"), timeout=TIMEOUT, headers=UA).json()
    pages = first[0]["pages"]
    rows = list(first[1])
    for page in range(2, pages + 1):
        rr = requests.get(build(f"per_page={per}&mrnev=1&page={page}"), timeout=TIMEOUT, headers=UA)
        rows.extend(rr.json()[1])

    df = pd.DataFrame(
        [{"country": x["country"]["value"], "iso3": x["countryiso3code"],
          "year": x["date"], "value": x["value"]} for x in rows]
    )
    nn = df.dropna(subset=["value"])
    print(f"  raw rows {len(df):,}   non-null {len(nn):,}   cols {list(nn.columns)}")
    print(f"  countries {nn['iso3'].nunique()}   years {nn['year'].min()}-{nn['year'].max()}")
    ind = nn[nn["iso3"] == "IND"].copy()
    ind["year"] = ind["year"].astype(int)
    ind = ind.sort_values("year")
    print(f"  INDIA rows {len(ind)}  range {ind['year'].min()}-{ind['year'].max()}")
    print(f"  INDIA 1990={ind[ind.year==1990]['value'].tolist()}  "
          f"2000={ind[ind.year==2000]['value'].tolist()}  "
          f"2010={ind[ind.year==2010]['value'].tolist()}  "
          f"latest({ind['year'].iloc[-1]})={ind['value'].iloc[-1]}")
    print(f"\n  VERDICT: World Bank needs no key and no login; JSON only; "
          f"{len(nn):,} real observations available for one indicator")


if __name__ == "__main__":
    main()
