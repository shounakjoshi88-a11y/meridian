"""Observed-HTTP-fact probe for research sources.

Every URL written into the notes must first be fetched by this script and
report a real status / content-type / content-length. Nothing is asserted
from memory.

Usage:
    python probe.py --head URL [URL ...]          # HEAD only, no body saved
    python probe.py --get  URL [URL ...]          # GET, stream to research/raw
    python probe.py --get URL --max-bytes 2000000 # GET but cap the download

Prints one TSV row per URL:
    status  final_url  content_type  content_length  bytes_read  secs
"""

from __future__ import annotations

import argparse
import os
import ssl
import sys
import time
import urllib.error
import urllib.request

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
RAW = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "raw")

CTX = ssl.create_default_context()


def probe(url: str, method: str = "HEAD", max_bytes: int = 0, timeout: int = 60):
    req = urllib.request.Request(
        url,
        method=method,
        headers={
            "User-Agent": UA,
            "Accept": "*/*",
            "Accept-Encoding": "identity",
        },
    )
    out = {
        "url": url,
        "status": "",
        "reason": "",
        "final_url": "",
        "content_type": "",
        "content_length": "",
        "bytes_read": 0,
        "secs": 0.0,
        "error": "",
        "saved": "",
    }
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            out["status"] = str(r.status)
            out["reason"] = r.reason or ""
            out["final_url"] = r.geturl()
            out["content_type"] = r.headers.get("Content-Type", "")
            cl = r.headers.get("Content-Length")
            out["content_length"] = cl if cl is not None else ""
            if method == "GET":
                os.makedirs(RAW, exist_ok=True)
                name = (
                    url.split("//", 1)[-1].split("/")[-1].split("?")[0] or "index.html"
                )
                name = "".join(c for c in name if c.isalnum() or c in "._-")
                dest = os.path.join(RAW, name)
                i = 1
                while os.path.exists(dest):
                    dest = os.path.join(RAW, f"{name}.{i}")
                    i += 1
                total = 0
                with open(dest, "wb") as fh:
                    while True:
                        chunk = r.read(65536)
                        if not chunk:
                            break
                        total += len(chunk)
                        fh.write(chunk)
                        if max_bytes and total >= max_bytes:
                            break
                out["bytes_read"] = total
                out["saved"] = dest
    except urllib.error.HTTPError as e:
        out["status"] = str(e.code)
        out["reason"] = e.reason or ""
        out["final_url"] = e.geturl() if hasattr(e, "geturl") else url
        out["content_type"] = e.headers.get("Content-Type", "") if e.headers else ""
        cl = e.headers.get("Content-Length") if e.headers else None
        out["content_length"] = cl if cl is not None else ""
        out["error"] = f"HTTPError {e.code}"
    except Exception as e:  # noqa: BLE001 - we want the reason text
        out["error"] = f"{type(e).__name__}: {e}"
    out["secs"] = round(time.time() - t0, 2)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--head", action="store_true")
    ap.add_argument("--get", dest="do_get", action="store_true")
    ap.add_argument("--max-bytes", type=int, default=0)
    ap.add_argument("--timeout", type=int, default=60)
    a = ap.parse_args()
    method = "GET" if a.do_get else "HEAD"

    print("status\treason\tcontent_type\tcontent_length\tbytes\tsecs\tfinal_url")
    for u in a.urls:
        o = probe(u, method, a.max_bytes, a.timeout)
        print(
            "\t".join(
                [
                    o["status"] or "-",
                    (o["reason"] or "-").replace("\t", " "),
                    (o["content_type"] or "-")[:60],
                    o["content_length"] or "-",
                    str(o["bytes_read"]) or "-",
                    str(o["secs"]),
                    o["final_url"],
                ]
            )
        )
        if o["error"]:
            print(f"    ERROR {o['error']}")
        if o["saved"]:
            print(f"    SAVED {o['saved']}")
        print(f"    FROM  {o['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())