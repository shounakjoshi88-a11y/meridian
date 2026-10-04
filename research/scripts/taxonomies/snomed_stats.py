"""snomed_stats.py - pull official SNOMED CT active-concept statistics from
SNOMED International's own Confluence release-notes pages via the REST API,
and print only what the API actually returned."""

import json
import re
import ssl
import urllib.request

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

PAGES = {
    "US Edition Release Notes - March 2026": 550633600,
    "July 2026 International Edition": 972029981,
    "US Edition Release Notes - September 2026": 1107656851,
}


def get(page_id):
    url = ("https://conf.spaces.snomed.org/wiki/rest/api/content/%d"
           "?expand=body.storage" % page_id)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0",
                                                "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=180, context=CTX) as r:
        data = r.read()
        print("GET %s" % url)
        print("  http        : %s" % r.status)
        print("  content-type: %s" % r.headers.get("Content-Type"))
        print("  bytes       : %s" % format(len(data), ","))
        return r.status, json.loads(data.decode("utf-8", "replace"))


for label, pid in PAGES.items():
    print("=" * 78)
    print("PAGE: %s (id=%d)" % (label, pid))
    try:
        status, j = get(pid)
    except Exception as e:
        print("  FAILED: %s: %s" % (type(e).__name__, e))
        continue

    title = j.get("title")
    print("  title       : %s" % title)
    body = (j.get("body") or {}).get("storage", {}).get("value", "")
    text = re.sub(r"<[^>]+>", " ", body)
    text = re.sub(r"\s+", " ", text)

    # pull any "N,NNN,NNN" or 6-7 digit figure near a concept-count label
    for kw in ["Active Concept Count", "International Edition of SNOMED CT",
               "Concept Count"]:
        for m in re.finditer(re.escape(kw), text):
            seg = text[m.start():m.start() + 260]
            nums = re.findall(r"\b\d{1,3}(?:,\d{3})+\b|\b\d{5,7}\b", seg)
            if nums:
                print("  %-34s -> %s" % (kw[:34], nums[:4]))
    print()