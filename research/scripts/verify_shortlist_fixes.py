"""Tighten the three checks verify_shortlist.py got wrong, and re-run them.

Research helper only. Nothing here is imported by the app.

Fixes:
  * HTML sniff must search the first 512 bytes, not just the first 5 - the
    retired WHO payload starts with a blank line before <!DOCTYPE.
  * JSON must be detected by content-type / first char, not by hoping
    read_csv raises - World Bank JSON was being "parsed" as 11,006 columns.
  * Zip member count must exclude directory entries.
"""

import io
import json
import zipfile

import pandas as pd
import requests

TIMEOUT = 300
UA = {"User-Agent": "meridian-dataset-research/1.0 (student project; non-commercial)"}


def is_html(payload, ctype):
    head = payload[:512].lower()
    return b"<!doctype" in head or b"<html" in head or "text/html" in ctype.lower()


def main():
    print("=" * 96)
    print("A. Synthea zip: files vs directory entries")
    print("=" * 96)
    url = "https://raw.githubusercontent.com/synthetichealth/synthea-sample-data/main/downloads/10k_synthea_covid19_csv.zip"
    r = requests.get(url, timeout=TIMEOUT, headers=UA)
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        infos = z.infolist()
        files = [i for i in infos if not i.is_dir()]
        dirs = [i for i in infos if i.is_dir()]
    print(f"  namelist entries {len(infos)}  =  files {len(files)}  +  dir entries {len(dirs)}")
    print(f"  dir entries: {[i.filename for i in dirs]}")
    print(f"  => note should say {len(files)} files")

    print()
    print("=" * 96)
    print("B. World Bank page 1, parsed as JSON (not as CSV)")
    print("=" * 96)
    wb = ("https://api.worldbank.org/v2/country/all/indicator/SP.DYN.LE00.IN"
          "?format=json&source=2&per_page=1000&page=1")
    r = requests.get(wb, timeout=TIMEOUT, headers=UA)
    print(f"  {r.status_code}  {r.headers.get('Content-Type','')}  {len(r.content):,}B")
    payload = json.loads(r.content)
    meta, rows = payload[0], payload[1]
    print(f"  page {meta['page']} of {meta['pages']}   api total {meta['total']}   "
          f"source {meta['sourceid']}   lastupdated {meta['lastupdated']}")
    print(f"  rows on this page: {len(rows)}")
    print(f"  sample: {json.dumps(rows[0])[:170]}")
    df = pd.DataFrame([{"iso3": x["countryiso3code"], "year": x["date"], "value": x["value"]}
                       for x in rows]).dropna(subset=["value"])
    print(f"  non-null on page 1: {len(df):,}   countries {df['iso3'].nunique()}")
    print(f"  is_html? {is_html(r.content, r.headers.get('Content-Type',''))}")

    print()
    print("=" * 96)
    print("C. Retired WHO covid19.who.int CSV - confirm it is HTML despite the 200")
    print("=" * 96)
    dead = "https://covid19.who.int/WHO-COVID-19-global-daily-data.csv"
    r = requests.get(dead, timeout=TIMEOUT, headers=UA)
    print(f"  status {r.status_code}   content-type {r.headers.get('Content-Type','')}   "
          f"{len(r.content):,}B")
    print(f"  first 120 bytes: {r.content[:120]!r}")
    print(f"  is_html? {is_html(r.content, r.headers.get('Content-Type',''))}")
    print("  => a status-only check passes this; a content check catches it")

    print()
    print("=" * 96)
    print("D. Live WHO blob CSV - confirm it is NOT html")
    print("=" * 96)
    live = "https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/WHO-COVID-19-global-daily-data.csv"
    r = requests.get(live, timeout=TIMEOUT, headers=UA)
    print(f"  status {r.status_code}   content-type {r.headers.get('Content-Type','')}   "
          f"{len(r.content):,}B")
    print(f"  is_html? {is_html(r.content, r.headers.get('Content-Type',''))}")


if __name__ == "__main__":
    main()
