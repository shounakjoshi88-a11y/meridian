import ssl
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36"

CANDIDATES = [
    "https://api.github.com/repos/thatisuday/indian-pincode-database",
    "https://api.github.com/repos/kishorek/India-Codes",
    "https://api.github.com/repos/bilal-webdev/india-postal-pincode-dataset",
    "https://raw.githubusercontent.com/thatisuday/indian-pincode-database/master/LICENSE",
    "https://raw.githubusercontent.com/thatisuday/indian-pincode-database/master/README.md",
    "https://raw.githubusercontent.com/kishorek/India-Codes/master/README.md",
    "https://raw.githubusercontent.com/bilal-webdev/india-postal-pincode-dataset/main/LICENSE",
]

for u in CANDIDATES:
    print("=" * 72)
    print("URL:", u)
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(u, headers={"User-Agent": UA}), timeout=90, context=CTX
        )
        b = r.read()
        print("  status", r.status, "| ctype", r.headers.get("Content-Type"),
              "| clen", r.headers.get("Content-Length"))
        if u.startswith("https://api.github.com"):
            import json
            d = json.loads(b.decode("utf-8", "replace"))
            lic = d.get("license") or {}
            print("  license:", lic.get("spdx_id"), "|", lic.get("name"))
            print("  stars:", d.get("stargazers_count"), "| pushed:", d.get("pushed_at"))
            print("  archived:", d.get("archived"), "| desc:", (d.get("description") or "")[:110])
        else:
            txt = b.decode("utf-8", "replace")
            for line in txt.split("\n")[:14]:
                if line.strip():
                    print("  |", line.strip()[:150])
    except Exception as e:  # noqa: BLE001
        print("  ERR", type(e).__name__, e)