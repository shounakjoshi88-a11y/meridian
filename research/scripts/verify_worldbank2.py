"""Round eight: the World Bank API rejects every shape tried so far.
Test the exact call that did return JSON earlier, print its body, and try
the documented alternates before concluding anything.

Research helper only. Nothing here is imported by the app.
"""

import requests

TIMEOUT = 120
UA = {"User-Agent": "meridian-dataset-research/1.0 (student project; non-commercial)"}

TESTS = [
    "https://api.worldbank.org/v2/country/IND/indicator/SH.DYN.LE00.M4?format=json&per_page=5",
    "https://api.worldbank.org/v2/country/IND/indicator/SH.DYN.LE00.M4?format=json",
    "https://api.worldbank.org/v2/country/ind?format=json",
    "https://api.worldbank.org/v2/country?format=json&per_page=5",
    "https://api.worldbank.org/v2/country/all/indicator/SH.DYN.LE00.M4?format=json",
    "https://api.worldbank.org/v2/country/all/indicator/SH.DYN.LE00.M4?format=json&per_page=1000&date=1990:2023",
    "https://api.worldbank.org/v2/en/indicator/SH.DYN.LE00.M4?format=json&per_page=5",
    "https://api.worldbank.org/v2/en/indicator/SH.DYN.LE00.M4?downloadformat=csv",
    "https://api.worldbank.org/v2/sources",
    "https://api.worldbank.org/v2/indicator/SH.DYN.LE00.M4?format=json",
]


def main():
    for url in TESTS:
        try:
            r = requests.get(url, timeout=TIMEOUT, headers=UA, allow_redirects=False)
        except Exception as e:  # noqa: BLE001
            print(f"ERR  {type(e).__name__}  {url}")
            continue
        body = r.content[:300]
        ctype = r.headers.get("Content-Type", "")
        print(f"{r.status_code}  {ctype[:40]:<42} {len(r.content):>9,}B  {url}")
        print(f"      {body!r}")
        if r.status_code in (301, 302, 307, 308):
            print(f"      -> Location: {r.headers.get('Location')}")
        print()


if __name__ == "__main__":
    main()
