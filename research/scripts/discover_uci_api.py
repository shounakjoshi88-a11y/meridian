"""Find a working machine-readable listing endpoint for the UCI repository.

Research helper only. Tries candidate API shapes and reports which ones return
real JSON, then prints the largest Health-and-Medicine datasets it can see.
Nothing here is imported by the app.
"""

import json
import urllib.error
import urllib.request

TIMEOUT = 40
UA = "meridian-dataset-research/1.0 (student project)"

# Shapes seen in the ucimlrepo front end / common Next.js data routes.
CANDIDATES = [
    "https://archive.ics.uci.edu/api/datasets?skip=0&take=20",
    "https://archive.ics.uci.edu/api/datasets/list",
    "https://archive.ics.uci.edu/api/dataset?skip=0&take=20",
    "https://archive.ics.uci.edu/datasets?skip=0&take=20",
    "https://archive.ics.uci.edu/static/public/",
    "https://archive.ics.uci.edu/api/datasets?skip=0&take=20&sort=desc&orderBy=NumInstances",
]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", "") if e.headers else "", b""
    except Exception as e:  # noqa: BLE001
        return "ERR", type(e).__name__, str(e).encode()


def main():
    for url in CANDIDATES:
        status, ctype, body = get(url)
        head = body[:180].decode("utf-8", "replace").replace("\n", " ")
        print(f"{str(status):>5}  {ctype:<34}  {url}")
        if status == 200 and "json" in ctype.lower():
            try:
                data = json.loads(body)
                print("      JSON keys:", list(data)[:10] if isinstance(data, dict) else type(data))
            except Exception:  # noqa: BLE001
                print("      not parseable as JSON")
        else:
            print(f"      {head}")


if __name__ == "__main__":
    main()
