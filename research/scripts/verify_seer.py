"""Round thirteen: read the real SEER access pages found in the nav.

Research helper only. Nothing here is imported by the app.
"""

import re

import requests

TIMEOUT = 120
UA = {"User-Agent": "meridian-dataset-research/1.0 (student project; non-commercial)"}

PAGES = [
    "https://seer.cancer.gov/data/agreements.html",
    "https://seer.cancer.gov/data-software/datasets.html",
    "https://seer.cancer.gov/data-software/documentation/seerstat/",
]

KEYWORDS = [
    "data use agreement", "dua", "signed", "sign the", "agreement", "restricted",
    "request", "no cost", "free of charge", "not available", "apply",
    "credentialed", "approved", "investigator", "download", "public use",
    "residual", "contact",
]


def text_of(html):
    t = re.sub(r"(?is)<(script|style|nav).*?</\1>", " ", html)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))


def main():
    for url in PAGES:
        r = requests.get(url, timeout=TIMEOUT, headers=UA)
        print("=" * 100)
        print(f"{url}  -> {r.status_code}, {len(r.content):,} bytes")
        if r.status_code != 200:
            print()
            continue
        text = text_of(r.text)
        low = text.lower()
        # The nav is repeated on every page; skip it by starting after the
        # first occurrence of a content-specific phrase.
        seen = set()
        for kw in KEYWORDS:
            i = low.find(kw)
            if i == -1 or kw in seen:
                continue
            seen.add(kw)
            print(f"  [{kw}] ...{text[max(0, i-230):i+320].strip()}...")
        print()


if __name__ == "__main__":
    main()
