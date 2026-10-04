"""taxo_probe.py - verify URLs for the disease-taxonomy survey.

Every printed line is the result of an actual HTTP request made by this
script. No URL here is inferred or guessed.

    python taxo_probe.py URL [URL ...]
    python taxo_probe.py --file urls.txt
    python taxo_probe.py --head URL
    python taxo_probe.py --prefix 1200 URL
"""

import argparse
import ssl
import sys
import urllib.error
import urllib.request

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def probe(url, method="GET", timeout=60, show_prefix=0):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "*/*"})
    out = {"url": url, "method": method}
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            out["status"] = r.status
            out["ctype"] = r.headers.get("Content-Type", "")
            cl = r.headers.get("Content-Length")
            out["clen"] = int(cl) if cl and cl.isdigit() else None
            out["final"] = r.geturl()
            out["lm"] = r.headers.get("Last-Modified", "")
            if show_prefix:
                out["prefix"] = r.read(show_prefix).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        out["status"] = e.code
        out["ctype"] = (e.headers.get("Content-Type", "") if e.headers else "")
        cl = (e.headers.get("Content-Length") if e.headers else None)
        out["clen"] = int(cl) if cl and cl.isdigit() else None
        out["error"] = "HTTPError %s %s" % (e.code, e.reason)
        if show_prefix:
            try:
                out["prefix"] = e.read(show_prefix).decode("utf-8", "replace")
            except Exception:
                pass
    except Exception as e:
        out["status"] = None
        out["error"] = "%s: %s" % (type(e).__name__, e)
    return out


def report(o, want_prefix):
    print("=" * 78)
    print("%s %s" % (o["method"], o["url"]))
    print("  status       : %s" % o.get("status"))
    print("  content-type : %s" % o.get("ctype"))
    print("  content-len  : %s" % (
        format(o["clen"], ",") + " bytes" if o.get("clen") is not None else "(absent / chunked)"))
    if o.get("final") and o["final"] != o["url"]:
        print("  final-url    : %s" % o["final"])
    if o.get("lm"):
        print("  last-modified: %s" % o["lm"])
    if o.get("error"):
        print("  ERROR        : %s" % o["error"])
    if o.get("prefix"):
        print("  --- body prefix ---")
        for line in o["prefix"].replace("\r", "").split("\n")[:30]:
            print("  | %s" % line)
    sys.stdout.flush()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="*")
    ap.add_argument("--file")
    ap.add_argument("--head", action="store_true")
    ap.add_argument("--prefix", type=int, default=0)
    ap.add_argument("--timeout", type=int, default=60)
    a = ap.parse_args()

    urls = list(a.urls)
    if a.file:
        with open(a.file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)
    if not urls:
        print(__doc__)
        raise SystemExit(2)

    method = "HEAD" if a.head else "GET"
    for u in urls:
        report(probe(u, method=method, timeout=a.timeout, show_prefix=a.prefix), a.prefix)


if __name__ == "__main__":
    main()