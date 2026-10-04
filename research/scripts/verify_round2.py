"""Round two: verify WHO, Synthea, OpenML and Kaggle with real requests.

Research helper only. Nothing here is imported by the app.

Round one proved a HEAD 200 is worthless (the retired WHO COVID URL served an
HTML page with a 200). So everything here does a real GET, sniffs the payload
magic, and only reports a row count if a parser actually produced one.
"""

import io
import json
import os
import zipfile

import pandas as pd
import requests

TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tmp")
TIMEOUT = 180
UA = {"User-Agent": "meridian-dataset-research/1.0 (student project; non-commercial)"}

CSV_URLS = [
    ("who_covid_daily", "WHO COVID-19 daily cases/deaths by country",
     "https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/WHO-COVID-19-global-daily-data.csv"),
    ("who_covid_weekly", "WHO COVID-19 weekly cases/deaths by country",
     "https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/WHO-COVID-19-global-data.csv"),
    ("who_covid_deaths_age", "WHO COVID-19 monthly deaths by age",
     "https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/WHO-COVID-19-global-monthly-death-by-age-data.csv"),
    ("who_covid_hosp_icu", "WHO COVID-19 hospitalisations and ICU admissions",
     "https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/WHO-COVID-19-global-hosp-icu-data.csv"),
]

ZIP_URLS = [
    ("synthea_covid10k", "Synthea COVID-19 10K synthetic patients (CSV)",
     "https://raw.githubusercontent.com/synthetichealth/synthea-sample-data/main/downloads/10k_synthea_covid19_csv.zip"),
]

ARFF_URLS = [
    ("openml_krkvp_arff", "OpenML kr-vs-kp as .arff",
     "https://api.openml.org/data/v1/download/3/kr-vs-kp.arff"),
    ("openml_krkvp_csv", "OpenML kr-vs-kp asking for .csv",
     "https://api.openml.org/data/v1/download/3/kr-vs-kp.csv"),
]


def report(tag, name, url, resp, payload):
    print(f"--- {tag}  {name}")
    print(f"    url         : {url}")
    print(f"    status      : {resp.status_code}")
    print(f"    content-type: {resp.headers.get('Content-Type', '')}")
    print(f"    bytes       : {len(payload):,}")

    magic = payload[:4]
    if magic[:2] == b"PK":
        print("    payload     : ZIP archive")
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            infos = [i for i in z.infolist() if not i.is_dir()]
            print(f"    members     : {len(infos)} files")
            for i in sorted(infos, key=lambda x: -x.file_size)[:14]:
                print(f"       {i.filename:<42} {i.file_size:>12,}")
            # try to parse the biggest tabular member
            cands = [i for i in infos if i.filename.lower().endswith(".csv")]
            if cands:
                biggest = max(cands, key=lambda i: i.file_size)
                with z.open(biggest) as fh:
                    df = pd.read_csv(fh, low_memory=False)
                print(f"    parsed      : {biggest} -> {len(df):,} rows x {len(df.columns)} cols")
                print(f"    columns     : {list(df.columns)[:14]}")
        return
    if magic[:5].lower() == b"@attr":
        print("    payload     : ARFF (attribute header detected)")
        text = payload.decode("utf-8", "replace")
        n = sum(1 for line in text.splitlines() if line and not line.startswith("@"))
        print(f"    data lines  : {n:,}")
        return
    try:
        df = pd.read_csv(io.BytesIO(payload), low_memory=False)
    except Exception as e:  # noqa: BLE001
        print(f"    PARSE FAIL  : {type(e).__name__}: {str(e)[:70]}")
        print(f"    first bytes : {payload[:140]!r}")
        return
    print(f"    parsed      : {len(df):,} rows x {len(df.columns)} cols")
    print(f"    columns     : {list(df.columns)[:14]}")


def fetch_and_report(tag, name, url):
    try:
        r = requests.get(url, timeout=TIMEOUT, headers=UA)
    except Exception as e:  # noqa: BLE001
        print(f"--- {tag}  {name}\n    REQUEST FAIL {type(e).__name__}: {str(e)[:90]}\n")
        return None
    report(tag, name, url, r, r.content)
    print()
    return r


def kaggle_probe():
    """Kaggle: confirm what an anonymous client can and cannot do."""
    print("--- kaggle  anonymous access probe")
    tests = [
        ("GET", "https://www.kaggle.com/api/v1/datasets/list?search=diabetes", None),
        ("GET", "https://www.kaggle.com/api/v1/datasets/view/alexteboul/diabetes-health-indicators-dataset", None),
        ("GET", "https://www.kaggle.com/api/v1/datasets/download/alexteboul/diabetes-health-indicators-dataset", None),
        ("GET", "https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset", None),
    ]
    for method, url, _ in tests:
        try:
            r = requests.get(url, timeout=90, headers=UA, allow_redirects=False)
            body = r.content[:160]
            print(f"    {r.status_code}  allow_redirect={r.headers.get('Location', '-')[:50]}")
            print(f"          ctype={r.headers.get('Content-Type', '')[:40]}  bytes={len(r.content):,}")
            print(f"          body={body!r}")
        except Exception as e:  # noqa: BLE001
            print(f"    ERR {type(e).__name__}: {str(e)[:70]}")
    print()


def synthea_listing():
    """Read the GitHub contents API for the sample-data downloads folder."""
    print("--- synthea  downloads folder listing (GitHub contents API, no login)")
    url = "https://api.github.com/repos/synthetichealth/synthea-sample-data/contents/downloads"
    r = requests.get(url, timeout=60, headers=UA)
    print(f"    status {r.status_code}")
    if r.status_code == 200:
        for item in r.json():
            if item["type"] == "file":
                print(f"    {item['name']:<48} {item['size']:>13,}")
    print()


def openml_medical():
    """Find the largest medical-tagged datasets OpenML exposes without a key."""
    print("--- openml  largest medical-tagged datasets")
    url = "https://api.openml.org/api/v1/json/data/list/tag/medical/limit/1000"
    r = requests.get(url, timeout=120, headers=UA)
    print(f"    list status {r.status_code}")
    if r.status_code != 200:
        print(f"    {r.content[:200]!r}\n")
        return
    rows = []
    for d in r.json()["data"]["dataset"]:
        q = {x["name"]: x["value"] for x in d.get("quality", [])}
        rows.append((int(float(q.get("NumberOfInstances", 0))), d["did"], d["name"], d.get("file_id"), d.get("format")))
    rows.sort(reverse=True)
    print(f"    {len(rows)} medical datasets; top 20 by row count:")
    for n, did, name, fid, fmt in rows[:20]:
        print(f"    {n:>9,}  did={did:<7} file_id={fid:<9} {fmt:<6} {name}")
    print(f"\n    download pattern: https://api.openml.org/data/v1/download/<file_id>/<name>.arff")
    with open(os.path.join(TMP, "openml_medical.json"), "w", encoding="utf-8") as f:
        json.dump([{"rows": n, "did": did, "name": nm, "file_id": fid, "format": fmt} for n, did, nm, fid, fmt in rows], f, indent=1)
    print()


def main():
    os.makedirs(TMP, exist_ok=True)
    for tag, name, url in CSV_URLS:
        fetch_and_report(tag, name, url)
    for tag, name, url in ZIP_URLS:
        fetch_and_report(tag, name, url)
    for tag, name, url in ARFF_URLS:
        fetch_and_report(tag, name, url)
    synthea_listing()
    openml_medical()
    kaggle_probe()


if __name__ == "__main__":
    main()
