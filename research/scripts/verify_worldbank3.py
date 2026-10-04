"""Round nine: the World Bank /indicator/ path errors for every shape.
Try the documented source= parameter and a couple of alternates.

Research helper only. Nothing here is imported by the app.
"""

import requests

TIMEOUT = 120
UA = {"User-Agent": "meridian-dataset-research/1.0 (student project; non-commercial)"}

TESTS = [
    "https://api.worldbank.org/v2/country/IND/indicator/SH.DYN.LE00.M4?format=json&source=2",
    "https://api.worldbank.org/v2/country/IND/indicator/SH.DYN.LE00.M4?format=json&source=2&per_page=5",
    "https://api.worldbank.org/v2/country/all/indicator/SH.DYN.LE00.M4?format=json&source=2&per_page=5",
    "https://api.worldbank.org/v2/country/IND/indicator/SP.DYN.LE00.IN?format=json&source=2&per_page=5",
    "https://api.worldbank.org/v2/country/IND/indicator/SH.DYN.LE00.M4?format=json&source=2&mrnev=1",
    "https://api.worldbank.org/v2/en/indicator/SH.DYN.LE00.M4?format=json&source=2&per_page=5",
    "https://api.worldbank.org/v2/country/IND/indicator/SH.DYN.LE00.M4?format=json&source=2&date=1990:2023",
]


def main():
    for url in TESTS:
        try:
            r = requests.get(url, timeout=TIMEOUT, headers=UA)
        except Exception as e:  # noqa: BLE001
            print(f"ERR {type(e).__name__}  {url}")
            continue
        ok = b'"total"' in r.content[:200]
        print(f"{r.status_code}  ok={ok}  {len(r.content):>9,}B  {url}")
        print(f"      {r.content[:260]!r}")
        print()


if __name__ == "__main__":
    main()
