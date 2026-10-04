"""Build the rare conditions registry from HPO and HPOA.

Sources
-------
hp.obo            Human Phenotype Ontology, OBO Foundry
phenotype.hpoa    disease to phenotype annotations, HPO project
mondo.obo         MONDO disease ontology, used only to attach a MONDO id

What this produces
------------------
data/rare_conditions.csv   one row per disease, with its phenotypic
                           findings as lay-typable symptom words
data/hpo_symptoms.csv      the symptom vocabulary itself, HPO term to
                           lay wording, so the words are traceable

Why the filters are there
-------------------------
HPOA annotates 12,880 diseases with 286,651 rows, and reading it raw is
useless for triage. Its most shared terms are Autosomal recessive
inheritance (4,265 diseases), Autosomal dominant inheritance (3,569) and
Global developmental delay (2,590). Nobody reports inheriting a gene
recessively at a clinic desk.

Three filters make the output usable:

1. Aspect. HPOA carries an aspect column. P is a phenotype, I is
   inheritance, C is a clinical modifier. Only P survives.

2. Ontology membership. A term must be a descendant of HP:0000118,
   Phenotypic abnormality, computed by walking is_a. Inheritance modes
   like HP:0000007 sit under HP:0000001 All instead and are excluded by
   this rather than by name matching.

3. Obsolete terms are dropped, along with any annotation pointing at one.

Wording comes from the layperson synonym scope where one exists, because
a patient says "tired", not "Fatigue". Where no lay synonym exists the
curator label is used and marked as such in the row.
"""
import csv
import io
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, "research", "raw")

HPO_OBO = os.path.join(RAW, "hp.obo")
HPOA = os.path.join(RAW, "phenotype.hpoa")
MONDO_OBO = os.path.join(RAW, "mondo.obo")

OUT_CONDITIONS = os.path.join(HERE, "data", "rare_conditions.csv")
OUT_SYMPTOMS = os.path.join(HERE, "data", "hpo_symptoms.csv")

PHENOTYPIC_ABNORMALITY = "HP:0000118"

# Below this many phenotypic findings a disease cannot be told apart from
# its neighbours by the symptoms alone.
MIN_SYMPTOMS = 3

# Above this, the row is dominated by a system-wide descriptor such as
# "Abnormality of the nervous system" rather than by findings.
MAX_SYMPTOMS = 40


def parse_obo(path):
    """Return {term_id: {...}} for a small OBO file.

    Reads stanza by stanza. Only the tags this build needs are kept.
    """
    terms = {}
    current = None

    with io.open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")

            if line.startswith("["):
                current = {"synonyms": [], "lay": [], "parents": [], "xrefs": [],
                           "obsolete": False}
                continue

            if current is None:
                continue

            if line.startswith("id: "):
                current["id"] = line[4:].strip()
            elif line.startswith("name: "):
                current["name"] = line[6:].strip()
            elif line.startswith("is_a: "):
                parent = line[6:].split("!")[0].strip()
                current["parents"].append(parent)
            elif line.startswith("xref: "):
                current["xrefs"].append(line[6:].split()[0])
            elif line.startswith("is_obsolete: "):
                current["obsolete"] = line[13:].strip() == "true"
            elif line.startswith("synonym: "):
                # synonym: "TEXT" SCOPE [refs]
                # The scope column holds one or more tokens, so layperson
                # is looked for anywhere in it rather than assumed to be
                # the first. Reading the first token gave "EXACT" every
                # time and reported zero lay terms in a file that has
                # nearly five thousand of them.
                body = line[9:]
                if '"' not in body:
                    continue
                text = body.split('"')[1]
                tokens = body.split('"')[2].strip().split()
                current["synonyms"].append((text, tokens[0] if tokens else ""))
                if "layperson" in tokens:
                    current["lay"].append(text)

            if not line.strip() and current.get("id"):
                terms[current["id"]] = current
                current = None

    if current and current.get("id"):
        terms[current["id"]] = current

    return terms


def descendants_of(root_id, terms):
    """Every term reachable from root_id by is_a, including itself."""
    children = {}

    for term_id, term in terms.items():
        for parent in term["parents"]:
            children.setdefault(parent, []).append(term_id)

    seen = set()
    stack = [root_id]

    while stack:
        node = stack.pop()

        if node in seen:
            continue

        seen.add(node)
        stack.extend(children.get(node, []))

    return seen


def parse_hpoa(path):
    """Return a list of (disease_id, disease_name, hpo_id, aspect, frequency)."""
    rows = []
    header = None

    with io.open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("#"):
                continue

            parts = line.rstrip("\n").split("\t")

            if header is None:
                header = parts
                index = {name: i for i, name in enumerate(header)}
                continue

            if len(parts) < len(header):
                continue

            rows.append((
                parts[index["database_id"]],
                parts[index["disease_name"]],
                parts[index["hpo_id"]],
                parts[index["aspect"]],
                parts[index["frequency"]],
            ))

    return rows


def normalise_source_id(source_id):
    """Put the two vocabularies' spellings of the same id in one key.

    HPOA writes Orphanet ids as ORPHA:12345 and MONDO writes the same id
    as Orphanet:12345. Compared literally they never match, which is why
    4,312 Orphanet diseases were left without an identifier.
    """
    if not source_id or ":" not in source_id:
        return source_id or ""

    prefix, _, number = source_id.partition(":")

    if prefix.upper() in {"ORPHA", "ORPHANET"}:
        return f"ORPHA:{number}"

    if prefix.upper() == "OMIM":
        return f"OMIM:{number}"

    return source_id


def mondo_index(mondo_terms):
    """Return {source_id: mondo_id} from MONDO's cross references.

    Built once as a dict. Scanning every MONDO term per disease was both
    wrong and slow: it matched only by accident of file order and left
    most Orphanet diseases without an identifier.
    """
    index = {}

    for mondo_id, term in mondo_terms.items():
        for xref in term["xrefs"]:
            # OMIMPS is a phenotypic series, a different entity from the
            # OMIM entry, so it is indexed but not aliased onto OMIM.
            if xref.upper().startswith("OMIMPS:"):
                index.setdefault(xref, mondo_id)
                continue

            index.setdefault(normalise_source_id(xref), mondo_id)

    return index


def main():
    for path in (HPO_OBO, HPOA, MONDO_OBO):
        if not os.path.exists(path):
            raise SystemExit(
                f"missing {path}\n"
                f"see research/notes/02-symptom-disease.md for the download URLs"
            )

    print("parsing hp.obo ...")
    hpo_terms = parse_obo(HPO_OBO)
    print(f"  {len(hpo_terms):,} terms")

    live = {tid: t for tid, t in hpo_terms.items() if not t["obsolete"]}
    phenotypic = descendants_of(PHENOTYPIC_ABNORMALITY, live)
    print(f"  {len(phenotypic):,} live phenotypic abnormality terms "
          f"(descendants of {PHENOTYPIC_ABNORMALITY})")

    print("parsing phenotype.hpoa ...")
    annotations = parse_hpoa(HPOA)
    print(f"  {len(annotations):,} annotations")

    kept = [a for a in annotations
            if a[3] == "P" and a[2] in phenotypic]
    print(f"  {len(kept):,} survive the aspect and ontology filters")

    # Inheritance is aspect I and was filtered out of the symptom list, so
    # it is collected here from the annotations that were dropped. Reading
    # it back out of the filtered set returns nothing for every disease.
    inheritance_by_disease = {}

    for source_id, _name, hpo_id, aspect, _frequency in annotations:
        if aspect != "I" or hpo_id in phenotypic:
            continue

        term = live.get(hpo_id)

        if not term:
            continue

        inheritance_by_disease.setdefault(source_id, set()).add(
            term["name"].lower())

    print("parsing mondo.obo ...")
    mondo_terms = parse_obo(MONDO_OBO)
    mondo_terms = {mid: t for mid, t in mondo_terms.items() if not t["obsolete"]}
    xref_to_mondo = mondo_index(mondo_terms)
    print(f"  {len(mondo_terms):,} live MONDO terms, "
          f"{len(xref_to_mondo):,} cross references")

    # disease_id -> {hpo_id: frequency}
    by_disease = {}
    names = {}

    for source_id, name, hpo_id, _aspect, frequency in kept:
        by_disease.setdefault(source_id, {})[hpo_id] = frequency
        names.setdefault(source_id, name)

    rows = []
    dropped_thin = 0
    no_mondo = 0

    for source_id in sorted(by_disease):
        found = by_disease[source_id]

        if len(found) < MIN_SYMPTOMS:
            dropped_thin += 1
            continue

        # Most frequent findings first, so truncating keeps the best ones.
        ordered = sorted(found.items(),
                         key=lambda kv: -frequency_rank(kv[1]))

        if len(ordered) > MAX_SYMPTOMS:
            ordered = ordered[:MAX_SYMPTOMS]

        words = []
        hpo_ids = []

        for hpo_id, _frequency in ordered:
            term = hpo_terms.get(hpo_id)

            if not term:
                continue

            word = (term["lay"][0] if term["lay"] else term["name"]).lower()

            if word not in words:
                words.append(word)
                hpo_ids.append(hpo_id)

        if len(words) < MIN_SYMPTOMS:
            dropped_thin += 1
            continue

        mondo_id = xref_to_mondo.get(normalise_source_id(source_id), "")

        if not mondo_id:
            no_mondo += 1

        rows.append({
            "condition_id": source_id.replace(":", "-"),
            "mondo_id": mondo_id,
            "name": names[source_id],
            "symptom_count": len(words),
            "symptoms": "|".join(words),
            "hpo_ids": "|".join(hpo_ids),
            "inheritance_mode": "|".join(
                sorted(inheritance_by_disease.get(source_id, set()))),
        })

    with io.open(OUT_CONDITIONS, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["condition_id", "mondo_id", "name", "symptom_count",
                        "symptoms", "hpo_ids", "inheritance_mode"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    # The vocabulary, so every word on screen is traceable to an HPO term.
    used = set()

    for row in rows:
        used |= set(row["hpo_ids"].split("|"))

    vocab = []

    for hpo_id in sorted(used):
        term = hpo_terms.get(hpo_id)

        if not term:
            continue

        vocab.append({
            "hpo_id": hpo_id,
            "term": term["name"],
            "lay_term": term["lay"][0] if term["lay"] else "",
            "has_lay_wording": "yes" if term["lay"] else "no",
        })

    with io.open(OUT_SYMPTOMS, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["hpo_id", "term", "lay_term", "has_lay_wording"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(vocab)

    with_lay = sum(1 for v in vocab if v["has_lay_wording"] == "yes")

    print()
    print(f"wrote {OUT_CONDITIONS}")
    print(f"  conditions          : {len(rows):,}")
    print(f"  with a MONDO id     : {len(rows) - no_mondo:,}")
    print(f"  dropped, too thin   : {dropped_thin:,}")
    print(f"wrote {OUT_SYMPTOMS}")
    print(f"  distinct HPO terms  : {len(vocab):,}")
    print(f"  with lay wording    : {with_lay:,}")


def frequency_rank(frequency):
    """Order annotations by how often the finding appears.

    HPOA frequency strings look like HP:0040283, where the trailing number
    is an ordered bucket. Anything unrecognised sorts last.
    """
    tail = frequency.rsplit(":", 1)[-1] if frequency else ""
    return int(tail) if tail.isdigit() else 0



if __name__ == "__main__":
    main()