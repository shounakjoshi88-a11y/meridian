"""snomed_probe.py - POST FHIR $count to the public Snowstorm demo server to
measure SNOMED CT concept counts anonymously (no API key)."""

import json
import ssl
import urllib.request

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

BASE = "https://snowstorm.snomedtools.org/fhir"


def post_count(url):
    body = json.dumps({"resourceType": "Parameters", "parameter": [
        {"name": "url", "valueUri": url}]}).encode()
    req = urllib.request.Request(
        BASE + "/CodeSystem/$count", data=body, method="POST",
        headers={"Content-Type": "application/fhir+json",
                 "Accept": "application/fhir+json",
                 "User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=90, context=CTX) as r:
            data = r.read().decode("utf-8", "replace")
            print("POST %s  url=%s" % (BASE + "/CodeSystem/$count", url))
            print("  http        : %s" % r.status)
            print("  content-type: %s" % r.headers.get("Content-Type"))
            print("  body        : %s" % data[:400])
            return data
    except Exception as e:
        print("POST failed url=%s -> %s: %s" % (url, type(e).__name__, e))
        return None


def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/fhir+json",
                                               "User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=90, context=CTX) as r:
            data = r.read().decode("utf-8", "replace")
            print("GET %s" % url)
            print("  http        : %s" % r.status)
            print("  body        : %s" % data[:400])
            return data
    except Exception as e:
        print("GET failed %s -> %s: %s" % (url, type(e).__name__, e))
        return None


if __name__ == "__main__":
    for u in ["http://snomed.info/sct",
              "http://snomed.info/sct/731000124108",
              "http://snomed.info/sct/83801003"]:
        post_count(u)
    # clinical finding / finding of body structure counts (symptom axis check)
    get(BASE + "/CodeSystem?url=http%3A%2F%2Fsnomed.info%2Fsct")
    get(BASE + "/Concept?system=http%3A%2F%2Fsnomed.info%2Fsct"
              "&code=271649007&count=1")  # Tiredness - a symptom