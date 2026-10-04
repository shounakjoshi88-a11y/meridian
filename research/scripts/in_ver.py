"""Nagpur / India health-data source probe (task-specific, unique name).

Prints observed HTTP status, content-type, content-length and a body prefix
for each URL given on the command line. Nothing is asserted from memory:
a URL only belongs in the notes if this script actually returned it.

Usage:
    python in_ver.py URL [URL ...]
    python in_ver.py --bytes URL [URL ...]   # also print total decoded size
"""

import ssl
import sys
import urllib.error
import urllib.request

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def one(url: str, full: bool) -> None:
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept": "*/*", "Accept-Encoding": "identity"}
    )
    print("=" * 78)
    print("URL        : " + url)
    try:
        with urllib.request.urlopen(req, timeout=60, context=CTX) as r:
            data = r.read() if full else r.read(700)
            print("status     : " + str(r.status))
            print("final_url  : " + r.geturl())
            print("ctype      : " + str(r.headers.get("Content-Type")))
            print("clen_hdr   : " + str(r.headers.get("Content-Length")))
            print("got_bytes  : " + format(len(data), ","))
            txt = data.decode("utf-8", "replace")
            for line in txt.replace("\r", "").split("\n")[:12]:
                print("  | " + line[:220])
    except urllib.error.HTTPError as e:
        print("status     : HTTPError " + str(e.code))
        print("final_url  : " + str(e.url))
        print("ctype      : " + str(e.headers.get("Content-Type") if e.headers else None))
        try:
            b = e.read(400)
            print("body       : " + b.decode("utf-8", "replace").replace("\n", " ")[:300])
        except Exception:
            pass
    except Exception as e:  # noqa: BLE001
        print("error      : " + type(e).__name__ + ": " + str(e))
    sys.stdout.flush()


def main() -> int:
    args = sys.argv[1:]
    full = "--bytes" in args
    urls = [a for a in args if not a.startswith("--")]
    if not urls:
        print(__doc__)
        return 2
    for u in urls:
        one(u.strip(), full)
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())