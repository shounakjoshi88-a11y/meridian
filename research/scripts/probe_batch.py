"""Probe one batch of candidate URLs and print observed HTTP facts.

Research helper only. Edit the URLS list, run it, read the table.
Usage: python probe_batch.py <name>
"""

import sys
import urllib.error
import urllib.request

TIMEOUT = 45
UA = {"User-Agent": "meridian-dataset-research/1.0 (student project)"}

BATCHES = {
    "openml": [
        "https://api.openml.org/data/v1/download/3/kr-vs-kp.arff",
        "https://api.openml.org/data/v1/download/3/kr-vs-kp.csv",
        "https://api.openml.org/api/v1/json/data/37",
        "https://api.openml.org/api/v1/json/data/list/tag/medical/limit/50",
        "https://www.openml.org/search?type=data&tag=medical",
    ],
    "synthea": [
        "https://synthea.mitre.org/downloads/",
        "https://synthea.mitre.org/",
        "https://github.com/synthetichealth/synthea",
        "https://raw.githubusercontent.com/synthetichealth/synthea/master/README.md",
    ],
    "who_wb": [
        "https://covid19.who.int/WHO-COVID-19-global-daily-data.csv",
        "https://api.worldbank.org/v2/country/IND/indicator/SH.DYN.LE00.M4?format=json&per_page=5",
        "https://ghoapi.azureedge.net/api/WHOSIS_000001",
        "https://xmart-api-public.who.int/FLAT_HUB/DimDimension",
    ],
    "seer": [
        "https://seer.cancer.gov/data/",
        "https://seer.cancer.gov/statistics/",
        "https://www.cdc.gov/united-states-cancer-statistics/",
    ],
    "kaggle": [
        "https://www.kaggle.com/api/v1/datasets/list?search=diabetes",
        "https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset",
    ],
    "uci_live": [
        "https://archive.ics.uci.edu/static/public/296/data.csv",
        "https://archive.ics.uci.edu/static/public/827/data.csv",
        "https://archive.ics.uci.edu/static/public/891/data.csv",
        "https://archive.ics.uci.edu/static/public/760/data.csv",
    ],
}


def probe(url):
    req = urllib.request.Request(url, method="HEAD", headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.headers.get("Content-Type", ""), r.headers.get("Content-Length", "")
    except urllib.error.HTTPError as e:
        return e.code, "", ""
    except Exception as e:  # noqa: BLE001
        return type(e).__name__, str(e)[:50], ""


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "openml"
    urls = BATCHES[which]
    print(f"=== {which} ===")
    for u in urls:
        status, ctype, clen = probe(u)
        print(f"{str(status):>6}  {ctype[:44]:<46} {clen or '-':>12}  {u}")


if __name__ == "__main__":
    main()
