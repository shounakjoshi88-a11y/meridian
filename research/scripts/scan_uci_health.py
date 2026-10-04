"""Enumerate every UCI dataset and report the large, natively-hosted health ones.

Research helper only. Nothing here is imported by the app.

Uses only endpoints that were observed to return real JSON:
  https://archive.ics.uci.edu/api/datasets/list   -> [{id, name}, ...]
  https://archive.ics.uci.edu/api/dataset?id=<n>  -> full record incl. num_instances,
                                                      area, data_url

For every Health-and-Medicine record above the row threshold it then probes
data_url so we can tell a real one-click CSV from a dead/external link.
"""

import json
import sys
import time
import urllib.error
import urllib.request

TIMEOUT = 40
UA = {"User-Agent": "meridian-dataset-research/1.0 (student project)"}
LIST_URL = "https://archive.ics.uci.edu/api/datasets/list"
DETAIL_URL = "https://archive.ics.uci.edu/api/dataset?id={}"
MIN_ROWS = int(sys.argv[1]) if len(sys.argv) > 1 else 10000


def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.load(r)


def head(url):
    """Return (status, content_type, content_length) without pulling the body."""
    req = urllib.request.Request(url, method="HEAD", headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.headers.get("Content-Type", ""), r.headers.get("Content-Length", "")
    except urllib.error.HTTPError as e:
        return e.code, "", ""
    except Exception as e:  # noqa: BLE001
        return type(e).__name__, "", ""


def main():
    names = get_json(LIST_URL)["data"]
    print(f"catalogue lists {len(names)} datasets; looking for Health and Medicine with > {MIN_ROWS} rows\n")

    found = []
    for entry in names:
        uid = entry["id"]
        try:
            rec = get_json(DETAIL_URL.format(uid))["data"]
        except Exception:  # noqa: BLE001
            continue

        if rec.get("area") != "Health and Medicine":
            continue
        rows = rec.get("num_instances") or 0
        if rows < MIN_ROWS:
            continue

        found.append(
            {
                "id": uid,
                "name": rec.get("name"),
                "rows": rows,
                "cols": rec.get("num_features"),
                "target": rec.get("target_col"),
                "doi": rec.get("dataset_doi"),
                "data_url": rec.get("data_url"),
                "landing": rec.get("repository_url"),
                "abstract": (rec.get("abstract") or "").strip().replace("\n", " ")[:150],
            }
        )
        time.sleep(0.15)

    found.sort(key=lambda r: -r["rows"])

    print(f"{len(found)} Health-and-Medicine datasets over {MIN_ROWS} rows\n")
    for r in found:
        status, ctype, clen = head(r["data_url"]) if r["data_url"] else ("-", "", "")
        live = "OK " if status == 200 else "DEAD"
        print(f"[{live} {str(status):>4}] {r['rows']:>8,} x {str(r['cols']):>4}  id={r['id']:<5} {r['name']}")
        print(f"          data_url : {r['data_url']}  ({ctype or '-'} {clen or '-'})")
        print(f"          doi      : {r['doi']}")
        print(f"          landing  : {r['landing']}")
        print()

    with open("uci_large_health.json", "w", encoding="utf-8") as f:
        json.dump(found, f, indent=1)
    print("wrote uci_large_health.json")


if __name__ == "__main__":
    main()
