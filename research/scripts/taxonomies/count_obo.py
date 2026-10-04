"""count_obo.py - generic OBO/OWL downloader + measurer.

Usage: python count_obo.py URL [LABEL]

Reports observed HTTP status/type/length, then measures class counts and
prints the license declaration actually embedded in the file. Counts are
measured from downloaded bytes, never quoted.
"""

import collections
import gzip
import re
import ssl
import sys
import urllib.request

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300, context=CTX) as r:
        data = r.read()
        print("GET %s" % url)
        print("  http         : %s" % r.status)
        print("  content-type : %s" % r.headers.get("Content-Type"))
        print("  content-len  : %s bytes" % format(len(data), ","))
        print("  last-modified: %s" % r.headers.get("Last-Modified"))
        print("  final-url    : %s" % r.geturl())
    return data


def main():
    url = sys.argv[1]
    label = sys.argv[2] if len(sys.argv) > 2 else "?"
    raw = fetch(url)

    if url.endswith(".gz"):
        raw = gzip.decompress(raw)
        print("  (gunzipped)   : %s bytes" % format(len(raw), ","))

    txt = raw.decode("utf-8", errors="replace")
    obo = url.endswith((".obo", ".obo.gz")) or "<Term]" in txt[:5000]

    print("\n--- measured: %s ---" % label)
    if obo:
        terms = txt.count("\n[Term]\n") + (1 if txt.startswith("[Term]") else 0)
        print("[Term] stanzas         : %d" % terms)
        ids = set(re.findall(r"^id: (\S+)", txt, re.M))
        print("distinct id: values    : %d" % len(ids))
        print("is_obsolete: true      : %d" % txt.count("is_obsolete: true"))
        print("is_a:                  : %d" % len(re.findall(r"^is_a: ", txt, re.M)))
        print("alt_id:                : %d" % txt.count("alt_id:"))
        pref = collections.Counter(i.split(":")[0] for i in ids)
        print("id prefixes            : %s" % dict(pref.most_common(8)))
    else:
        print("owl:Class occurrences  : %d" % txt.count("owl:Class"))
        print("Class rdf:about        : %d" % txt.count("<Class rdf:about"))
        print("distinct subjects      : %d" % len(set(re.findall(r'rdf:about="([^"]+)"', txt))))
        print("rdfs:subClassOf        : %d" % txt.count("rdfs:subClassOf"))

    print("\n--- license / rights declared IN the file ---")
    for pat in [r"terms:license[^\n]*", r"dc:license[^\n]*",
                r"licenses?:\w+[^\n]*", r"license[^\n]{0,140}",
                r"rights[^\n]{0,140}", r"cc0[^\n]{0,140}",
                r"creativecommons\.org/[^\s\"<>]*"]:
        hits = re.findall(pat, txt, re.I)
        uniq = list(dict.fromkeys(h.strip() for h in hits))[:8]
        for h in uniq:
            print("  | %s" % h[:160])

    print("\n--- phenotype/symptom signal ---")
    for kw in ["HP:", "phenotype", "Phenotype", "symptom", "Symptom",
               "clinical finding", "Clinical finding", "sign or symptom"]:
        print("  %-20s %d" % (kw, txt.count(kw)))

    names = re.findall(r"^name: (.+)$", txt, re.M) or re.findall(r"<rdfs:label>([^<]+)</rdfs:label>", txt)
    print("  labels found        : %d" % len(names))


if __name__ == "__main__":
    main()