"""Probe candidate dataset URLs and report observed HTTP facts.

Research helper only. Nothing here is imported by the app.

For each URL it reports:
  status      HTTP status code actually returned
  ctype       Content-Type header
  clen        Content-Length header (or measured byte count of a ranged GET)
  method      HEAD if HEAD was allowed, else ranged GET
  note        short verdict

Usage:
    python probe_urls.py            # probe the built-in list
    python probe_urls.py urls.txt   # probe one URL per line, # comments ok
"""

import sys
import urllib.error
import urllib.request

TIMEOUT = 45
USER_AGENT = "meridian-dataset-research/1.0 (student project; contact: local)"

# Only URLs that were shown to us on a real landing page or in a real API
# response. Never hand-write a path that was not confirmed somewhere.
BUILTIN = [
    # --- PhysioNet open access -------------------------------------------
    "https://physionet.org/files/ptb-xl/1.0.3/ptbxl_database.csv",
    "https://physionet.org/files/ptb-xl/1.0.3/scp_statements.csv",
    "https://physionet-open.s3.amazonaws.com/ptb-xl/1.0.3/ptbxl_database.csv",
    # --- Credential walls (expect 401/403/404) ----------------------------
    "https://physionet.org/files/mimic-iv/2.2/csv/patients.csv.gz",
    "https://physionet.org/files/mimiciii/1.4/patients.csv",
]


def probe(url):
    """Return a dict of observed facts about one URL. Never raises."""
    row = {"url": url, "status": None, "ctype": "", "clen": "", "method": "", "note": ""}

    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            row["status"] = resp.status
            row["ctype"] = resp.headers.get("Content-Type", "")
            row["clen"] = resp.headers.get("Content-Length", "")
            row["method"] = "HEAD"
            return row
    except urllib.error.HTTPError as e:
        # Some hosts answer HEAD with 403 but serve GET fine. Fall through.
        row["head_status"] = e.code
    except Exception as e:  # noqa: BLE001 - research script, report anything
        row["head_status"] = type(e).__name__

    # Fall back to a ranged GET so we can read the real status and headers
    # without pulling the whole body.
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Range": "bytes=0-2047"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read()
            row["status"] = resp.status
            row["ctype"] = resp.headers.get("Content-Type", "")
            row["clen"] = resp.headers.get("Content-Length", "") or f"range-got {len(body)}B"
            row["method"] = "GET(range)"
            return row
    except urllib.error.HTTPError as e:
        row["status"] = e.code
        row["ctype"] = e.headers.get("Content-Type", "") if e.headers else ""
        row["clen"] = e.headers.get("Content-Length", "") if e.headers else ""
        row["method"] = "GET(range)"
        row["note"] = (e.reason or "")[:60]
        return row
    except Exception as e:  # noqa: BLE001
        row["status"] = "ERR"
        row["note"] = f"{type(e).__name__}: {e}"[:90]
        return row


def main(argv):
    if len(argv) > 1:
        with open(argv[1], encoding="utf-8") as f:
            urls = [
                ln.strip()
                for ln in f
                if ln.strip() and not ln.strip().startswith("#")
            ]
    else:
        urls = BUILTIN

    print(f"{'status':>7}  {'method':<10} {'clen':>14}  ctype / url")
    print("-" * 100)

    for url in urls:
        r = probe(url)
        head_only = r.get("head_status", "")
        extra = f"  [HEAD was {head_only}]" if head_only else ""
        extra += f"  {r['note']}" if r["note"] else ""
        clen = r["clen"] or "-"
        print(f"{str(r['status']):>7}  {r['method']:<10} {clen:>14}  {r['ctype']}")
        print(f"{'':>34}  {url}{extra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
