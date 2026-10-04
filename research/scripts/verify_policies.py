"""Round eleven: read the actual access-policy text for SEER and the
open-access PhysioNet demos, and confirm the World Bank licence wording.

Research helper only. Nothing here is imported by the app.
"""

import re

import requests

TIMEOUT = 120
UA = {"User-Agent": "meridian-dataset-research/1.0 (student project; non-commercial)"}

PAGES = [
    ("SEER data home", "https://seer.cancer.gov/data/"),
    ("SEER Research Data page", "https://seer.cancer.gov/data-research/"),
    ("SEER*Stat software", "https://seer.cancer.gov/seerstat/software/"),
    ("PhysioNet MIMIC-IV Clinical Database Demo", "https://physionet.org/content/mimic-iv-demo/2.2/"),
    ("PhysioNet eICU-CRD Demo", "https://physionet.org/content/eicu-crd-demo/2.0/"),
    ("PhysioNet cxr-cardiomegaly", "https://physionet.org/content/cxr-cardiomegaly/1.0.0/"),
    ("World Bank terms", "https://www.worldbank.org/en/about/legal/terms-and-conditions"),
]

KEYWORDS = [
    "data use agreement", "dua", "credentialed", "restricted", "public use",
    "freely available", "no charge", "requires", "must be", "seerstat",
    "license", "creative commons", "cc by", "attribution", "request",
    "open access", "citation",
]


def clean(html):
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text)


def main():
    for label, url in PAGES:
        print("=" * 100)
        print(f"{label}\n  {url}")
        try:
            r = requests.get(url, timeout=TIMEOUT, headers=UA)
        except Exception as e:  # noqa: BLE001
            print(f"  REQUEST FAIL {type(e).__name__}: {str(e)[:90]}\n")
            continue
        print(f"  status {r.status_code}  ctype {r.headers.get('Content-Type','')[:40]}  {len(r.content):,} bytes")
        text = clean(r.text)
        low = text.lower()
        seen = set()
        for kw in KEYWORDS:
            i = low.find(kw)
            if i == -1 or kw in seen:
                continue
            seen.add(kw)
            print(f"    [{kw}] ...{text[max(0, i-160):i+200].strip()}...")
        # PhysioNet file panels list direct download paths; capture them.
        for m in re.finditer(r'href="(/files/[^"]+)"', r.text):
            print(f"    FILE LINK: https://physionet.org{m.group(1)}")
        print()


if __name__ == "__main__":
    main()
