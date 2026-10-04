"""Round twelve: verify the two remaining PhysioNet open CSVs and pull the
SEER data-request policy page linked from seer.cancer.gov/data/.

Research helper only. Nothing here is imported by the app.
"""

import io
import re

import pandas as pd
import requests

TIMEOUT = 180
UA = {"User-Agent": "meridian-dataset-research/1.0 (student project; non-commercial)"}

CSVS = [
    ("cxr-CTRs", "Image-derived cardiomegaly CTR values (96K CXRs)",
     "https://physionet.org/files/cxr-cardiomegaly/1.0.0/CTRs.csv"),
    ("cxr-CPARs", "Image-derived cardiomegaly CPAR values (96K CXRs)",
     "https://physionet.org/files/cxr-cardiomegaly/1.0.0/CPARs.csv"),
    ("mimic4demo_subjects", "MIMIC-IV Clinical Database Demo subject list",
     "https://physionet.org/files/mimic-iv-demo/2.2/demo_subject_id.csv"),
]


def verify_csvs():
    print("=" * 100)
    print("PHYSIONET OPEN-ACCESS CSVs, downloaded and parsed")
    print("=" * 100)
    for key, name, url in CSVS:
        try:
            r = requests.get(url, timeout=TIMEOUT, headers=UA)
        except Exception as e:  # noqa: BLE001
            print(f"  {name}: REQUEST FAIL {type(e).__name__}")
            continue
        print(f"  {name}")
        print(f"    {url}")
        print(f"    {r.status_code}  {r.headers.get('Content-Type','')}  {len(r.content):,} bytes")
        if r.status_code != 200 or r.content[:5].lower().startswith(b"<!doc"):
            print(f"    NOT USABLE  first={r.content[:80]!r}\n")
            continue
        df = pd.read_csv(io.BytesIO(r.content), low_memory=False)
        print(f"    {len(df):,} rows x {len(df.columns)} cols")
        print(f"    cols: {list(df.columns)[:14]}")
        print()


def seer_policy():
    print("=" * 100)
    print("SEER: follow the 'How to Request the Data' link and quote the restriction")
    print("=" * 100)
    r = requests.get("https://seer.cancer.gov/data/", timeout=TIMEOUT, headers=UA)
    links = sorted(set(re.findall(r'href="([^"]*(?:request|dataset|documentation|agreement)[^"]*)"',
                                  r.text, re.I)))
    print("  candidate links found on https://seer.cancer.gov/data/:")
    for l in links:
        print(f"    {l}")

    targets = [
        "https://seer.cancer.gov/data/how-to-request-the-data/",
        "https://seer.cancer.gov/data/documentation/",
        "https://seer.cancer.gov/seerstat/",
    ]
    for url in targets:
        try:
            rr = requests.get(url, timeout=TIMEOUT, headers=UA)
        except Exception as e:  # noqa: BLE001
            print(f"\n  {url}  ERR {type(e).__name__}")
            continue
        print(f"\n  {url}  -> {rr.status_code}, {len(rr.content):,} bytes")
        if rr.status_code != 200 or "Page Not Found" in rr.text:
            print("    (not a usable page)")
            continue
        text = re.sub(r"(?is)<(script|style).*?</\1>", " ", rr.text)
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text))
        low = text.lower()
        for kw in ["data use agreement", "dua", "sign", "agreement", "restricted",
                   "request", "free", "no cost", "not available", "apply",
                   "credentialed", "approved", "investigator"]:
            i = low.find(kw)
            if i == -1:
                continue
            print(f"    [{kw}] ...{text[max(0, i-200):i+280].strip()}...")


if __name__ == "__main__":
    verify_csvs()
    seer_policy()
