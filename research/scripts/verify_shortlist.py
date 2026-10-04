"""Final gate: re-fetch every URL quoted in the shortlist of note 04, exactly as
written there, and confirm status + content-type + bytes + parsed shape.

Research helper only. Nothing here is imported by the app.
If this script and the note ever disagree, the note is wrong.
"""

import io
import zipfile

import pandas as pd
import requests

TIMEOUT = 300
UA = {"User-Agent": "meridian-dataset-research/1.0 (student project; non-commercial)"}

SHORTLIST = [
    ("1  Synthea COVID-19 10K zip",
     "https://raw.githubusercontent.com/synthetichealth/synthea-sample-data/main/downloads/10k_synthea_covid19_csv.zip"),
    ("2  UCI 296 Diabetes 130-US Hospitals",
     "https://archive.ics.uci.edu/static/public/296/data.csv"),
    ("3  WHO COVID-19 global daily data",
     "https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/WHO-COVID-19-global-daily-data.csv"),
    ("4  World Bank WDI life expectancy (code-validated)",
     "https://api.worldbank.org/v2/country/all/indicator/SP.DYN.LE00.IN?format=json&source=2&per_page=1000&page=1"),
    ("5a PTB-XL ptbxl_database.csv",
     "https://physionet.org/files/ptb-xl/1.0.3/ptbxl_database.csv"),
    ("5b PTB-XL scp_statements.csv",
     "https://physionet.org/files/ptb-xl/1.0.3/scp_statements.csv"),
    ("5c PTB-XL via open S3 bucket",
     "https://physionet-open.s3.amazonaws.com/ptb-xl/1.0.3/ptbxl_database.csv"),
]

WALLS = [
    ("MIMIC-III credential wall",
     "https://physionet.org/files/mimiciii/1.4/patients.csv"),
    ("Kaggle competition data",
     "https://www.kaggle.com/api/v1/competitions/data/download/titanic/train.csv"),
    ("Kaggle pima (anonymous 403 case)",
     "https://www.kaggle.com/api/v1/datasets/download/uciml/pima-indians-diabetes-database"),
]

DEAD = [
    ("retired WHO covid19.who.int CSV",
     "https://covid19.who.int/WHO-COVID-19-global-daily-data.csv"),
]


def main():
    print("=" * 96)
    print("SHORTLIST - must all be usable with no login")
    print("=" * 96)
    for label, url in SHORTLIST:
        try:
            r = requests.get(url, timeout=TIMEOUT, headers=UA)
        except Exception as e:  # noqa: BLE001
            print(f"FAIL {label}: {type(e).__name__}: {str(e)[:70]}")
            continue
        line = (f"  {r.status_code}  {r.headers.get('Content-Type','')[:30]:<32} "
                f"{len(r.content):>12,}B  {label}")
        print(line)
        payload = r.content
        if payload[:5].lower().startswith(b"<!doc"):
            print("       !! HTML payload, not data")
            continue
        if payload[:2] == b"PK":
            with zipfile.ZipFile(io.BytesIO(payload)) as z:
                names = z.namelist()
                print(f"       zip: {len(names)} members")
                for want in ("observations.csv", "conditions.csv", "patients.csv"):
                    hit = next((n for n in names if n.endswith("/" + want)), None)
                    if hit:
                        with z.open(hit) as fh:
                            n = sum(1 for _ in fh) - 1
                        print(f"       {want:<18} {n:>10,} data rows")
            continue
        try:
            df = pd.read_csv(io.BytesIO(payload), low_memory=False)
            print(f"       csv: {len(df):,} rows x {len(df.columns)} cols")
        except Exception:  # noqa: BLE001
            j = r.json()
            if isinstance(j, list) and len(j) == 2 and "total" in j[0]:
                print(f"       json: api total {j[0]['total']}, pages {j[0]['pages']}, "
                      f"{len(j[1])} rows in this page")
            else:
                print(f"       unparsed: {payload[:100]!r}")

    print()
    print("=" * 96)
    print("CREDENTIAL WALLS - must NOT return data anonymously")
    print("=" * 96)
    for label, url in WALLS:
        try:
            r = requests.get(url, timeout=TIMEOUT, headers=UA, allow_redirects=False)
            body = r.content[:110]
            gave_zip = body[:2] == b"PK"
            verdict = "LEAKED DATA" if (r.status_code == 200 and gave_zip) else "blocked"
            print(f"  {r.status_code}  {r.headers.get('Content-Type','')[:30]:<32} "
                  f"{verdict:<12} {label}")
            print(f"       {body!r}")
        except Exception as e:  # noqa: BLE001
            print(f"  ERR {type(e).__name__}  {label}")

    print()
    print("=" * 96)
    print("KNOWN DEAD - must be HTML or non-200, i.e. caught by a content check")
    print("=" * 96)
    for label, url in DEAD:
        try:
            r = requests.get(url, timeout=TIMEOUT, headers=UA)
            html = r.content[:5].lower().startswith(b"<!doc")
            print(f"  {r.status_code}  {r.headers.get('Content-Type','')[:40]:<42} "
                  f"html={html}  {label}")
        except Exception as e:  # noqa: BLE001
            print(f"  ERR {type(e).__name__}  {label}")


if __name__ == "__main__":
    main()
