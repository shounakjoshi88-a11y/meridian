"""Round four: is Kaggle really blocked, or does the REST download work anonymously?

Research helper only. Nothing here is imported by the app.

The brief assumed Kaggle needs an account and an API token. A single probe
disagreed, so this tries several datasets, both documented and undocumented
endpoint shapes, with and without a bogus credential, and reports what an
anonymous client can actually retrieve.
"""

import io
import zipfile

import pandas as pd
import requests

TIMEOUT = 180
UA = {"User-Agent": "meridian-dataset-research/1.0 (student project; non-commercial)"}

# Public, widely-referenced Kaggle health datasets. owner/slug only - never guessed paths.
DATASETS = [
    ("alexteboul", "diabetes-health-indicators-dataset"),
    ("uciml", "pima-indians-diabetes-database"),
    ("andrewmvd", "fetal-health-classification"),
    ("pravallika", "diabetes-dataset"),
    ("uciml", "iris"),
]

ENDPOINTS = [
    ("download api  ", "https://www.kaggle.com/api/v1/datasets/download/{o}/{s}"),
    ("download v1   ", "https://www.kaggle.com/api/v1/datasets/download/{o}/{s}/dataset.csv"),
    ("legacy download", "https://www.kaggle.com/api/v1/datasets/download/{o}/{s}?datasetVersionNumber=1"),
]


def try_get(url, headers=None):
    h = dict(UA)
    if headers:
        h.update(headers)
    try:
        r = requests.get(url, timeout=TIMEOUT, headers=h, allow_redirects=True, stream=True)
    except Exception as e:  # noqa: BLE001
        return None, f"ERR {type(e).__name__}: {str(e)[:60]}"
    chunk = next(r.iter_content(8192), b"")
    r.close()
    return (r, chunk), None


def main():
    print("=" * 100)
    print("KAGGLE ANONYMOUS ACCESS MATRIX")
    print("=" * 100)

    for owner, slug in DATASETS:
        print(f"\n### {owner}/{slug}")
        for label, tmpl in ENDPOINTS:
            url = tmpl.format(o=owner, s=slug)
            got, err = try_get(url)
            if err:
                print(f"  {label}  {err}")
                continue
            r, chunk = got
            kind = "ZIP" if chunk[:2] == b"PK" else ("CSV" if b"," in chunk[:400] else "other")
            print(f"  {label}  {r.status_code}  ctype={r.headers.get('Content-Type','')[:26]:<26} "
                  f"len={r.headers.get('Content-Length','-'):>10}  payload={kind}")
            if kind == "ZIP" and r.status_code == 200:
                # read the central directory only, then stream just one member
                pass

        # metadata endpoint
        meta_url = f"https://www.kaggle.com/api/v1/datasets/view/{owner}/{slug}"
        try:
            mr = requests.get(meta_url, timeout=TIMEOUT, headers=UA)
        except Exception as e:  # noqa: BLE001
            print(f"  metadata     ERR {type(e).__name__}: {str(e)[:60]}")
            continue
        if mr.status_code == 200:
            d = mr.json()
            print(f"  metadata     200  license={d.get('licenseNameNullable')}  "
                  f"bytes={d.get('totalBytesNullable')}  title={str(d.get('title'))[:48]}")
        else:
            print(f"  metadata     {mr.status_code}")

    print("\n" + "=" * 100)
    print("CONTROL: does a bogus credential change anything, and does a private slug fail?")
    print("=" * 100)
    for label, url, hdr in [
        ("anonymous        ", "https://www.kaggle.com/api/v1/datasets/download/uciml/iris", None),
        ("bogus basic auth ", "https://www.kaggle.com/api/v1/datasets/download/uciml/iris",
         {"Authorization": "Basic " + "aDpmaWdlbmNlbnNlY3JldDpkZWFkYmVlZg=="}),
        ("nonexistent slug ", "https://www.kaggle.com/api/v1/datasets/download/uciml/definitely-not-real-xyz", None),
        ("competition file ", "https://www.kaggle.com/api/v1/competitions/data/download/titanic/train.csv", None),
    ]:
        got, err = try_get(url, hdr)
        if err:
            print(f"  {label}  {err}")
            continue
        r, chunk = got
        print(f"  {label}  {r.status_code}  ctype={r.headers.get('Content-Type','')[:30]:<30} "
              f"first={chunk[:44]!r}")

    print("\n" + "=" * 100)
    print("ACTUAL PARSE of the anonymous BRFSS zip (what a student would really get)")
    print("=" * 100)
    url = "https://www.kaggle.com/api/v1/datasets/download/alexteboul/diabetes-health-indicators-dataset"
    r = requests.get(url, timeout=TIMEOUT, headers=UA, allow_redirects=True)
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        for i in z.infolist():
            print(f"  member {i.filename:<52} {i.file_size:>12,}")
        biggest = max(z.infolist(), key=lambda i: i.file_size)
        with z.open(biggest) as fh:
            df = pd.read_csv(fh, low_memory=False)
    print(f"  parsed {biggest.filename}: {len(df):,} rows x {len(df.columns)} cols")
    print(f"  columns: {list(df.columns)}")


if __name__ == "__main__":
    main()
