"""count_mesh.py - download MeSH desc2026.xml.gz and count descriptors.

Prints counts observed from the actual downloaded bytes, so entry counts in
the notes are measured, not quoted from marketing pages.
"""

import collections
import gzip
import os
import ssl
import sys
import urllib.request

URL = "https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc2026.gz"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def fetch(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180, context=CTX) as r:
        data = r.read()
        print("GET %s" % url)
        print("  http         : %s" % r.status)
        print("  content-type : %s" % r.headers.get("Content-Type"))
        print("  content-len  : %s" % format(len(data), ","))
        print("  last-modified: %s" % r.headers.get("Last-Modified"))
    with open(dest, "wb") as f:
        f.write(data)
    return data


def main():
    dest_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    gz = os.path.join(dest_dir, "desc2026.gz")
    data = fetch(URL, gz)
    xml = gzip.decompress(data).decode("utf-8", errors="replace")

    print("\n--- measured counts from desc2026.xml ---")
    print("bytes uncompressed : %s" % format(len(xml), ","))
    print("DescriptorRecord   : %d" % xml.count("<DescriptorRecord "))
    print("DescriptorIndexTerm: %d" % xml.count("<DescriptorIndexTerm "))
    print("TreeNumberList     : %d" % xml.count("<TreeNumberList>"))
    print("ConceptList        : %d" % xml.count("<ConceptList>"))
    print("PharmacologicTherapy: %d" % xml.count("<PharmacologicTherapy>"))

    # record-level category (the <Descriptor> heading's own TreeNumbers)
    cat = collections.Counter()
    for rec in xml.split("<DescriptorRecord ")[1:]:
        head = rec.split("</Descriptor>")[0]
        tn = head.count("<TreeNumber>")
        if "N" in head and "PHarmacologicTherapy" not in head:
            cat["descriptor_with_treenumbers"] += 1
        if "<DescriptorUI>" in head:
            cat["has_UI"] += 1
        cat["treenumbers_in_head"] += tn
    for k, v in sorted(cat.items()):
        print("%-30s: %d" % (k, v))

    # Sample a known disease to confirm symptoms exist as their own descriptors
    print("\n--- sample: does MeSH carry 'Signs and Symptoms' descriptors? ---")
    sn = [
        r for r in xml.split("<DescriptorRecord ")[1:]
        if "<DescriptorUI>D008963</DescriptorUI>" in r  # Signs and Symptoms (tree)
    ]
    print("records mentioning D008963 : %d" % len(sn))
    n_sym = sum(
        1 for r in xml.split("<DescriptorRecord ")[1:]
        if "<TreeNumber>C23.888</TreeNumber>" in r
    )
    print("records in C23.888 (Symptoms) : %d" % n_sym)


if __name__ == "__main__":
    main()