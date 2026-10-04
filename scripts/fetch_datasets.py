"""Download the candidate clinical datasets for Meridian.

Taught concepts used: os (Lab 4), requests (syllabus, web scraping line).

Two kinds of source are handled:

  flat   a plain .csv over HTTP, saved as-is
  zip    a .zip archive whose member file has no header row, extracted and
         saved as raw/<name>.csv

Every URL here was verified to respond. Hardcoded URLs rot, so main()
reports a summary and the profile script is the real gate on quality.
No authentication is needed for any of these.
"""

import os
import zipfile

import requests

import io

RAW_DIR = os.path.join("data", "datasets", "raw")

# Flat CSVs, downloaded as-is. The Plotly copy of the Pima data already
# carries a header, which is why it is preferred over the jbrownlee copy.
FLAT_SOURCES = {
    "pima_diabetes_local.csv":
        "https://raw.githubusercontent.com/plotly/datasets/master/diabetes.csv",
}

# UCI archives. The member file inside has no header row, so
# stage_datasets.py attaches the real column names from the official
# .names documentation afterwards.
ZIP_SOURCES = {
    "heart_disease_processed.csv": {
        "url": "https://archive.ics.uci.edu/static/public/45/heart+disease.zip",
        "member": "processed.cleveland.data",
    },
    "mammographic_masses.csv": {
        "url": "https://archive.ics.uci.edu/static/public/161/mammographic+mass.zip",
        "member": "mammographic_masses.data",
    },
    "parkinsons.csv": {
        "url": "https://archive.ics.uci.edu/static/public/174/parkinsons.zip",
        "member": "parkinsons.data",
    },
}

TIMEOUT = 30


def fetch(url):
    """GET a URL and return the response, or None if it did not work."""
    try:
        response = requests.get(url, timeout=TIMEOUT)
    except requests.RequestException as e:
        print(f"  FAIL  {url}  {type(e).__name__}: {e}")
        return None

    if response.status_code != 200:
        print(f"  FAIL  {url}  HTTP {response.status_code}")
        return None

    return response


def save_flat(filename, url):
    """Download a plain CSV into the raw folder."""
    path = os.path.join(RAW_DIR, filename)

    if os.path.exists(path):
        print(f"  skip  {filename}  (already here, {os.path.getsize(path)} bytes)")
        return True

    response = fetch(url)

    if response is None:
        return False

    with open(path, "w", newline="") as f:
        f.write(response.text)

    print(f"  ok    {filename}  {os.path.getsize(path)} bytes")
    return True


def save_from_zip(filename, url, member):
    """Download a zip archive and save one member as a flat CSV."""
    path = os.path.join(RAW_DIR, filename)

    if os.path.exists(path):
        print(f"  skip  {filename}  (already here, {os.path.getsize(path)} bytes)")
        return True

    response = fetch(url)

    if response is None:
        return False

    # BytesIO wraps the downloaded bytes so zipfile can read them without
    # writing the archive to disk first.
    archive = zipfile.ZipFile(io.BytesIO(response.content))

    if member not in archive.namelist():
        print(f"  FAIL  {filename}  archive has no {member}")
        print(f"        members are: {', '.join(archive.namelist()[:6])}")
        return False

    with open(path, "wb") as f:
        f.write(archive.read(member))

    print(f"  ok    {filename}  {os.path.getsize(path)} bytes  (from {member})")
    return True


def main():
    if not os.path.exists(RAW_DIR):
        os.makedirs(RAW_DIR)

    print(f"Downloading into {RAW_DIR}")
    results = []

    for filename in FLAT_SOURCES:
        results.append(save_flat(filename, FLAT_SOURCES[filename]))

    for filename, spec in ZIP_SOURCES.items():
        results.append(save_from_zip(filename, spec["url"], spec["member"]))

    ok = results.count(True)
    total = len(results)

    print(f"\n{ok} of {total} datasets ready")

    if ok < total:
        print("\nSome sources failed. The pipeline can still run on whatever is")
        print("present, but check profile_dataset.py output before trusting it.")

    return 0 if ok == total else 1


if __name__ == "__main__":
    raise SystemExit(main())