"""inspect_mesh.py - show a real MeSH descriptor record and count
symptom-related / phenotype-bearing content from the actual file."""

import collections
import gzip
import os
import re
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "desc2026.gz"

with gzip.open(SRC, "rt", encoding="utf-8", errors="replace") as f:
    xml = f.read()

recs = xml.split("<DescriptorRecord ")[1:]
print("records: %d" % len(recs))

print("\n===== SAMPLE RECORD (first) =====")
print(recs[0][:1800])

print("\n===== TAG FREQUENCY (top 25) =====")
tags = collections.Counter(re.findall(r"<([A-Za-z][A-Za-z0-9_.]*)[ >/]", xml))
for t, c in tags.most_common(25):
    print("  %-32s %d" % (t, c))

print("\n===== DISEASE vs SYMPTOM coverage =====")
# MeSH top-level tree ranges
disease_trees = ["C01", "C14", "C15", "C16", "C17", "C18", "C19", "C20",
                 "C21", "C22", "C23.1", "C23.2", "C23.3", "C23.4", "C23.5",
                 "C23.6", "C23.7", "C23.8", "C24", "C25", "C26", "C27", "C34",
                 "C50", "C51", "C53", "C54", "C55", "C56", "C57", "C58", "C60",
                 "C61", "C62", "C63", "C64", "C65", "C75", "C79", "C80", "C81",
                 "C83", "C88", "C90", "C91", "C92", "C93", "C94", "C96", "C97",
                 "C99"]
symptom_trees = ["C23.888", "C23.100", "F01", "F02", "F03", "G09", "R23"]


def tree_set(rec):
    # only trees listed under the record's own <Descriptor>/<TreeNumberList>
    head = rec.split("</Descriptor>")[0]
    return set(re.findall(r"<TreeNumber>([^<]+)</TreeNumber>", head))


n_dis = n_sym = n_both = n_no = 0
sym_examples = []
dis_examples = []
for r in recs:
    ts = tree_set(r)
    d = any(t.startswith(tuple(disease_trees)) for t in ts)
    s = any(t.startswith(tuple(symptom_trees)) for t in ts)
    name = ""
    m = re.search(r"<DescriptorName[^>]*>\s*<String>([^<]+)</String>", r)
    if m:
        name = m.group(1)
    if d and s:
        n_both += 1
    elif d:
        n_dis += 1
        if len(dis_examples) < 8:
            dis_examples.append(name)
    elif s:
        n_sym += 1
        if len(sym_examples) < 8:
            sym_examples.append(name)
    else:
        n_no += 1

print("disease-top-level only : %d" % n_dis)
print("symptom/sign  only     : %d" % n_sym)
print("both disease+symptom   : %d" % n_both)
print("neither                : %d" % n_no)
print("\nsymptom-only examples: %s" % ", ".join(sym_examples))
print("\ndisease-only examples: %s" % ", ".join(dis_examples))

print("\n===== does MeSH carry PHENOTYPE-ish annotations? =====")
for probe in ["<Qualifier>", "SeeAlso", "<RelatedNote>", "entry term",
              "<DescriptorClass>", "PreviousIndexing"]:
    print("  %-22s occurrences: %d" % (probe, xml.count(probe)))