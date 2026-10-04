"""Final pass: real distributions from the shortlisted datasets, so the notes
can state what charts each one can actually support.

Research helper only. Nothing here is imported by the app.
Downloads Synthea once and caches it under research/tmp/.
"""

import io
import json
import os
import zipfile

import pandas as pd
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, "..", "tmp")
UA = {"User-Agent": "meridian-dataset-research/1.0 (student project; non-commercial)"}
TIMEOUT = 300

SYNTHEA_URL = "https://raw.githubusercontent.com/synthetichealth/synthea-sample-data/main/downloads/10k_synthea_covid19_csv.zip"
SYNTHEA_CACHE = os.path.join(TMP, "synthea_covid10k.zip")


def load(url):
    r = requests.get(url, timeout=TIMEOUT, headers=UA)
    r.raise_for_status()
    return io.BytesIO(r.content)


def synthea():
    print("=" * 100)
    print("SYNTHEA COVID-19 10K - real row counts per table")
    print("=" * 100)
    os.makedirs(TMP, exist_ok=True)
    if not os.path.exists(SYNTHEA_CACHE):
        r = requests.get(SYNTHEA_URL, timeout=TIMEOUT, headers=UA)
        with open(SYNTHEA_CACHE, "wb") as f:
            f.write(r.content)
    print(f"  cached archive: {os.path.getsize(SYNTHEA_CACHE):,} bytes")

    interesting = ["patients.csv", "encounters.csv", "conditions.csv", "observations.csv"]
    with zipfile.ZipFile(SYNTHEA_CACHE) as z:
        for member in interesting:
            name = next((n for n in z.namelist() if n.endswith("/" + member)), None)
            if not name:
                continue
            with z.open(name) as fh:
                n = sum(1 for _ in fh) - 1
            print(f"  {member:<20} {n:>10,} data rows")

        # Conditions breakdown is the most useful clinical summary.
        cond = next(n for n in z.namelist() if n.endswith("/conditions.csv"))
        with z.open(cond) as fh:
            df = pd.read_csv(fh, low_memory=False)
    print(f"\n  conditions.csv: {len(df):,} rows x {len(df.columns)} cols")
    print(f"  cols: {list(df.columns)}")
    print(f"  distinct conditions: {df['DESCRIPTION'].nunique():,}")
    print("\n  top 12 recorded conditions:")
    print(df["DESCRIPTION"].value_counts().head(12).to_string())
    pats = df["PATIENT"].nunique()
    print(f"\n  distinct patients with >=1 condition: {pats:,}")
    print(f"  COVID-19 condition rows: {int((df['DESCRIPTION'] == 'COVID-19').sum()):,}")
    print()

    pat_name = next(n for n in zipfile.ZipFile(SYNTHEA_CACHE).namelist()
                    if n.endswith("/patients.csv"))
    with zipfile.ZipFile(SYNTHEA_CACHE) as z, z.open(pat_name) as fh:
        p = pd.read_csv(fh, low_memory=False)
    print(f"  patients.csv: {len(p):,} rows x {len(p.columns)} cols")
    print(f"  cols: {list(p.columns)}")
    print(f"  gender counts: {p['GENDER'].value_counts().to_dict()}")
    print(f"  race counts  : {p['RACE'].value_counts().to_dict()}")
    print(f"  has BIRTHDATE (no AGE column): {'BIRTHDATE' in p.columns}")
    print(f"  deceased rows: {int(p['DEATHDATE'].notna().sum()):,}")
    print()


def ptbxl():
    print("=" * 100)
    print("PTB-XL - diagnostic superclass distribution (from scp_statements dictionary)")
    print("=" * 100)
    db = pd.read_csv(load("https://physionet.org/files/ptb-xl/1.0.3/ptbxl_database.csv"))
    scp = pd.read_csv(load("https://physionet.org/files/ptb-xl/1.0.3/scp_statements.csv"))
    print(f"  ptbxl_database.csv : {len(db):,} rows x {len(db.columns)} cols")
    print(f"  scp_statements.csv : {len(scp):,} rows x {len(scp.columns)} cols")
    print(f"  unique patients    : {db['patient_id'].nunique():,}")
    print(f"  sex: {db['sex'].value_counts().to_dict()}")
    diag = scp[scp["diagnostic"] == 1].copy()
    code2class = dict(zip(diag["Unnamed: 0"], diag["diagnostic_class"]))
    db["codes"] = db["scp_codes"].apply(lambda s: eval(s) if isinstance(s, str) else {})
    counts = {}
    for codes in db["codes"]:
        for c in codes:
            if c in code2class:
                counts[code2class[c]] = counts.get(code2class[c], 0) + 1
    print("\n  records per diagnostic superclass:")
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"    {str(k):<26} {v:>7,}")
    print(f"\n  age: min {pd.to_numeric(db['age'], errors='coerce').min()} "
          f"median {pd.to_numeric(db['age'], errors='coerce').median()} "
          f"max {pd.to_numeric(db['age'], errors='coerce').max()}")
    print(f"  strat_fold values: {sorted(db['strat_fold'].unique())}")
    print()


def uci296():
    print("=" * 100)
    print("UCI 296 Diabetes 130-US Hospitals - what the columns support")
    print("=" * 100)
    df = pd.read_csv(load("https://archive.ics.uci.edu/static/public/296/data.csv"), low_memory=False)
    print(f"  {len(df):,} rows x {len(df.columns)} cols")
    print(f"  unique patients: {df['patient_nbr'].nunique():,}  encounters: {df['encounter_id'].nunique():,}")
    print(f"  target 'readmitted': {df['readmitted'].value_counts().to_dict()}")
    print(f"  race: {df['race'].value_counts().to_dict()}")
    print(f"  age buckets: {sorted(df['age'].unique())[:6]} ... {sorted(df['age'].unique())[-2:]}")
    print(f"  time_in_hospital: min {df['time_in_hospital'].min()} median {df['time_in_hospital'].median()} max {df['time_in_hospital'].max()}")
    print(f"  missing cells: {int(df.isna().sum().sum()):,} "
          f"({100 * df.isna().sum().sum() / df.size:.1f}% of all cells)")
    top_na = df.isna().sum().sort_values(ascending=False).head(6)
    print(f"  worst columns for missingness: {top_na.to_dict()}")
    diag_codes = df['diag_1'].nunique()
    print(f"  distinct diag_1 codes: {diag_codes:,}  (ICD-9 like)")
    print(f"  distinct medical_specialty: {df['medical_specialty'].nunique():,}")
    print()


def who():
    print("=" * 100)
    print("WHO COVID-19 daily data - coverage")
    print("=" * 100)
    df = pd.read_csv(load("https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/WHO-COVID-19-global-daily-data.csv"))
    print(f"  {len(df):,} rows x {len(df.columns)} cols")
    print(f"  countries/areas: {df['Country'].nunique():,}   regions: {sorted(df['WHO_region'].dropna().unique())}")
    print(f"  date range: {df['Date_reported'].min()} -> {df['Date_reported'].max()}")
    print(f"  total reported deaths: {int(df['New_deaths'].fillna(0).sum()):,}")
    print(f"  top 8 countries by deaths:")
    top = df.groupby("Country")["New_deaths"].sum().sort_values(ascending=False).head(8)
    for k, v in top.items():
        print(f"    {k:<34} {int(v):>12,}")
    print()


def main():
    os.makedirs(TMP, exist_ok=True)
    synthea()
    ptbxl()
    uci296()
    who()


if __name__ == "__main__":
    main()
