"""List real filenames in a GitHub directory via the contents API, then probe.

No path is guessed: filenames come from the API response itself.

Usage: python in_ghls.py <owner/repo> <dir>
"""

import json
import ssl
import sys
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) research/1.0"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90, context=CTX) as r:
        return r.status, r.read().decode("utf-8", "replace")


def main():
    repo, path = sys.argv[1], sys.argv[2]
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    st, body = get(url)
    print(f"GET {url}\n  status={st}")
    data = json.loads(body)
    print(f"  entries: {len(data)}\n")
    print(f"  {'name':<34} {'size':>9}  download_url")
    for e in data:
        print(f"  {e['name']:<34} {e['size']:>9,}  {e.get('download_url')}")
    sys.stdout.flush()


if __name__ == "__main__":
    main()