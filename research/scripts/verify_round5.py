"""Round five: SEER policy text, extra open PhysioNet tables, World Bank, and the
small UCI sets Meridian already uses (for an honest before/after comparison).

Research helper only. Nothing here is imported by the app.
"""

import io
import json
import re
import zipfile

import pandas as pd
import requests

TIMEOUT = 240
UA = {"User-Agent": "meridian-dataset-research/1.0 (student project; non-commercial)"}

# Landing pages read earlier; file paths below were taken from their file panels.
PHYSIONET_CSVS = [
    ("ptbxl_meta", "PTB-XL metadata", "https://physionet.org/files/ptb-xl/1.0.3/ptbxl_database.csv"),
    ("ptbxl_scp", "PTB-XL SCP-ECG dictionary", "https://physionet.org/files/ptb-xl/1.0.3/scp_statements.csv"),
]

# The datasets Meridian currently ships, plus the classic comparison sets.
UCI_KNOWN = [
    ("heart_disease_45", "Heart Disease", 45),
    ("breast_cancer_wdbc_17", "Breast Cancer Wisconsin (Diagnostic)", 17),
    ("pima_diabetes_9", "Diabetes (Pima)", 9),
    ("ilpd_225", "ILPD Indian Liver Patient Dataset", 225),
    ("framingham_917", "Personal Key Indicators of Heart Disease", 917),
    ("cdc_diabetes_891", "CDC Diabetes Health Indicators", 891),
    ("sepsis_827", "Sepsis Survival Minimal Clinical Records", 827),
    ("diabetes130_296", "Diabetes 130-US Hospitals", 296),
]


def physionet():
    print("=" * 100)
    print("PHYSIONET OPEN-ACCESS CSV FILES")
    print("=" * 100)
    for key, name, url in PHYSIONET_CSVS:
        r = requests.get(url, timeout=TIMEOUT, headers=UA)
        df = pd.read_csv(io.BytesIO(r.content), low_memory=False)
        print(f"  {name}")
        print(f"    {url}")
        print(f"    {r.status_code}  {r.headers.get('Content-Type','')}  {len(r.content):,} bytes")
        print(f"    {len(df):,} rows x {len(df.columns)} cols")
        print(f"    cols: {list(df.columns)}")
        print()


def uci_known():
    print("=" * 100)
    print("UCI REFERENCE SETS (row counts from the live API, plus a real download where offered)")
    print("=" * 100)
    for key, name, uid in UCI_KNOWN:
        url = f"https://archive.ics.uci.edu/api/dataset?id={uid}"
        try:
            d = requests.get(url, timeout=60, headers=UA).json()["data"]
        except Exception as e:  # noqa: BLE001
            print(f"  {name:<44} API ERR {type(e).__name__}")
            continue
        rows = d.get("num_instances")
        cols = d.get("num_features")
        doi = d.get("dataset_doi")
        data_url = d.get("data_url")
        area = d.get("area")
        print(f"  {name:<44} id={uid:<5} {str(rows):>9} x {str(cols):<5} {area:<20} doi={doi}")
        print(f"      data_url: {data_url}")
        if data_url:
            try:
                r = requests.get(data_url, timeout=TIMEOUT, headers=UA)
                if r.status_code == 200 and not r.content[:5].lower().startswith(b"<!doc"):
                    df = pd.read_csv(io.BytesIO(r.content), low_memory=False)
                    print(f"      VERIFIED download: {len(df):,} rows x {len(df.columns)} cols "
                          f"({len(r.content):,} bytes)")
                else:
                    print(f"      download status {r.status_code} (not plain csv)")
            except Exception as e:  # noqa: BLE001
                print(f"      download ERR {type(e).__name__}: {str(e)[:50]}")
        print()


def world_bank():
    print("=" * 100)
    print("WORLD BANK API (anonymous) - all countries, life expectancy 1990-2024")
    print("=" * 100)
    url = ("https://api.worldbank.org/v2/country/all/indicator/SH.DYN.LE00.M4"
           "?format=json&per_page=20000&date=1990:2024")
    r = requests.get(url, timeout=TIMEOUT, headers=UA)
    print(f"  {r.status_code}  {r.headers.get('Content-Type','')}  {len(r.content):,} bytes")
    payload = r.json()
    print(f"  total reported: {payload[0].get('total')}  pages {payload[0].get('pages')}")
    df = pd.DataFrame(
        [{"country": x["country"]["value"], "iso3": x["countryiso3code"],
          "year": x["date"], "value": x["value"]} for x in payload[1]]
    ).dropna(subset=["value"])
    print(f"  non-null: {len(df):,} rows x {len(df.columns)} cols")
    print(f"  countries {df['iso3'].nunique()}  years {df['year'].min()}-{df['year'].max()}")
    ind = df[df["iso3"] == "IND"].sort_values("year")
    print(f"  INDIA rows {len(ind)}; latest = {ind.iloc[-1].to_dict()}")

    # second indicator: cause-of-death style, under-5 mortality
    url2 = ("https://api.worldbank.org/v2/country/all/indicator/SH.DYN.MORT"
            "?format=json&per_page=20000&date=1990:2024")
    r2 = requests.get(url2, timeout=TIMEOUT, headers=UA)
    p2 = r2.json()
    df2 = pd.DataFrame(
        [{"country": x["country"]["value"], "iso3": x["countryiso3code"],
          "year": x["date"], "value": x["value"]} for x in p2[1]]
    ).dropna(subset=["value"])
    print(f"  under-5 mortality SH.DYN.MORT: {len(df2):,} non-null rows, "
          f"{df2['iso3'].nunique()} countries")
    print(f"  VERDICT: no key, no login, JSON only -> flatten locally")
    print()


def seer():
    print("=" * 100)
    print("SEER / cancer.gov - what the page actually says about access")
    print("=" * 100)
    for url in ["https://seer.cancer.gov/data/",
                "https://seer.cancer.gov/statistics/"]:
        r = requests.get(url, timeout=90, headers=UA)
        text = re.sub(r"<[^>]+>", " ", r.text)
        text = re.sub(r"\s+", " ", text)
        print(f"  {url}  -> {r.status_code}, {len(r.content):,} bytes")
        for kw in ["Data Use Agreement", "DUA", "require", "SEER\\*Stat", " freely",
                   "available", "request", "agreement", "restricted", "public use",
                   "Research Data"]:
            for m in re.finditer(kw, text, re.I):
                seg = text[max(0, m.start() - 130): m.start() + 170].strip()
                print(f"     [{kw}] ...{seg}...")
                break
        print()


def main():
    physionet()
    uci_known()
    world_bank()
    seer()


if __name__ == "__main__":
    main()
