# 02 — Symptom-to-disease data sources for Meridian triage

**Status:** research + verification only. No application code changed.
**Verified:** 2026-10-04, by running `research/scripts/verify_all_urls.py` and the
`analyse_*.py` scripts against real downloads.
**Rule applied:** every URL below was actually fetched. HTTP status, content-type and
content-length are observed, not remembered. Anything not confirmed is tagged
**UNVERIFIED**.

**Current state being replaced:** `data/diseases.csv` holds 15 hand-written diseases with
pipe-separated symptoms; `backend/triage.py` scores them with exact-match set algebra after
`str.strip().casefold()`. Two consequences run through everything below:

1. Any replacement knowledge base must emit **plain-English symptom strings**, because
   matching is exact string equality.
2. A knowledge base is only useful if a user typing "fever, cough" hits the right disease.
   Section 7 measures how well real data satisfies that.

---

## Verification table

Run of `verify_all_urls.py` at 2026-10-04 18:33. **34 of 35 URLs returned 200.** The one
failure is a finding, not a typo (see §1.4).

| Source | URL | Method | Status | Bytes | Content-Type |
|---|---|---|---|---|---|
| HPO ontology | `https://purl.obolibrary.org/obo/hp.obo` | HEAD | 200 | 10,863,613 | application/octet-stream |
| HPO ontology (same bytes) | `https://github.com/obophenotype/human-phenotype-ontology/releases/latest/download/hp.obo` | HEAD | 200 | 10,863,613 | application/octet-stream |
| HPO ontology (OWL) | `https://purl.obolibrary.org/obo/hp.owl` | HEAD | 200 | 76,854,086 | application/octet-stream |
| HPOA annotations | `https://github.com/obophenotype/human-phenotype-ontology/releases/latest/download/phenotype.hpoa` | HEAD | 200 | 35,816,037 | application/octet-stream |
| HPOA gene xref | `.../releases/latest/download/genes_to_phenotype.txt` | HEAD | 200 | 20,821,704 | application/octet-stream |
| HPOA phenotype xref | `.../releases/latest/download/phenotype_to_genes.txt` | HEAD | 200 | 67,246,520 | application/octet-stream |
| HPO licence URL cited in-file | `https://hpo.jax.org/app/license` | HEAD | **404** | 60,203 | text/html |
| HPO homepage | `http://www.human-phenotype-ontology.org` | HEAD | 200 | 60,203 | text/html |
| HPO repo LICENSE.md | `https://raw.githubusercontent.com/obophenotype/human-phenotype-ontology/master/LICENSE.md` | HEAD | 200 | 90 | text/plain |
| OBO Foundry HPO entry | `http://obofoundry.org/ontology/hp.html` | HEAD | 200 | 33,712 | text/html |
| Open Targets licence table | `https://platform-docs.opentargets.org/licence.md` | HEAD | 200 | 12,081 | text/markdown |
| Monarch v3 entity | `https://api.monarchinitiative.org/v3/api/entity/MONDO:0005148` | **GET** | 200 | 18,512 | application/json |
| Monarch v3 associations | `https://api.monarchinitiative.org/v3/api/association?category=biolink:DiseaseToPhenotypicFeatureAssociation&limit=1` | **GET** | 200 | 9,074 | application/json |
| MONDO ontology | `https://purl.obolibrary.org/obo/mondo.obo` | HEAD | 200 | 53,134,854 | application/octet-stream |
| MedGen FTP root | `https://ftp.ncbi.nlm.nih.gov/pub/medgen/` | HEAD | 200 | — | text/html;charset=UTF-8 |
| MedGen sources list | `https://ftp.ncbi.nlm.nih.gov/pub/medgen/MedGen_Sources.txt` | HEAD | 200 | 10,294 | text/plain |
| MedGen README | `https://ftp.ncbi.nlm.nih.gov/pub/medgen/README.txt` | HEAD | 200 | 17,286 | text/plain |
| MedGen HPO↔CUI | `.../MedGen_HPO_Mapping.txt.gz` | HEAD | 200 | 398,282 | application/x-gzip |
| MedGen HPO↔OMIM | `.../MedGen_HPO_OMIM_Mapping.txt.gz` | HEAD | 200 | 4,271,791 | application/x-gzip |
| MedGen ID mappings | `.../MedGenIDMappings.txt.gz` | HEAD | 200 | 5,806,282 | application/x-gzip |
| NCBI policies | `https://www.ncbi.nlm.nih.gov/home/about/policies/` | HEAD | 200 | — | text/html |
| Orphadata | `https://www.orphadata.com` | HEAD | 200 | 293,314 | text/html |
| Orphadata Science | `https://sciences.orphadata.com/orphanet-scientific-knowledge-files` | HEAD | 200 | — | text/html |
| Orphanet phenos (real bytes) | `https://media.githubusercontent.com/media/Orphanet/Orphadata_aggregated/master/Rare%20diseases%20with%20associated%20phenotypes/en_product4.xml` | HEAD | 200 | 47,893,357 | application/octet-stream |
| Orphanet phenos (LFS pointer) | `https://raw.githubusercontent.com/Orphanet/Orphadata_aggregated/master/Rare%20diseases%20with%20associated%20phenotypes/en_product4.xml` | HEAD | 200 | **133** | text/plain |
| Orphanet HOOM | `https://raw.githubusercontent.com/Orphanet/Orphadata_aggregated/refs/heads/master/Orphanet%20Ontologies/HOOM/hoom_orphanet_2.5..zip` | HEAD | 200 | 4,746,267 | application/zip |
| Orphanet repo | `https://github.com/Orphanet/Orphadata_aggregated` | HEAD | 200 | — | text/html |
| UMLS licence (HTML) | `https://www.nlm.nih.gov/research/umls/knowledge_sources/metathesaurus/release/license_agreement.html` | HEAD | 200 | 34,928 | text/html |
| UMLS licence (2026AA PDF) | `https://uts.nlm.nih.gov/uts/assets/LicenseAgreement.pdf` | HEAD | 200 | 311,203 | application/pdf |
| UMLS how to access | `https://www.nlm.nih.gov/databases/umls.html` | HEAD | 200 | 25,147 | text/html |
| UMLS UTS (login) | `https://uts.nlm.nih.gov/uts/` | HEAD | 200 | 4,596 | text/html |
| DisGeNET plans | `https://disgenet.com/plans` | HEAD | 200 | 12,572 | text/html |
| DisGeNET legal | `https://disgenet.com/Legal` | HEAD | 200 | 12,572 | text/html |
| DisGeNET redistribution FAQ | `https://support.disgenet.com/support/solutions/articles/202000087487-do-i-need-a-commercial-license-can-i-use-disgenet-data-in-my-product-` | HEAD | 200 | — | text/html |

Two mechanics worth recording because they will bite an implementer:

- **`raw.githubusercontent.com` silently serves a 133-byte Git-LFS pointer, not the XML**,
  for Orphanet's `*.xml` products. A naive fetch "succeeds" (200) and yields three lines of
  `version https://git-lfs.github.com/spec/v1`. Use `media.githubusercontent.com/media/...`.
- **Monarch's API returns `405 Method Not Allowed` to `HEAD`** and `200` to `GET`. Health
  checks written with HEAD will report the API as down.

---

## 1. Human Phenotype Ontology (HPO)

**Maintainer:** Human Phenotype Ontology Consortium (Peter Robinson, Sebastian Köhler) with
the Monarch Initiative. Repo: `obophenotype/human-phenotype-ontology`.
**Format:** OBO flat file (`hp.obo`), also OWL (`hp.owl`, 73.3 MB) and OBO Foundry JSON.
**Size:** 10,863,613 bytes (10.4 MB).
**API key / click-through:** none. Anonymous HTTP GET.
**Distinct diseases obtainable:** 0 on its own — HPO is a phenotype vocabulary with no
disease axis. It is the symptom dictionary, not the disease dictionary.

### 1.1 Entry count (computed from the downloaded file, `analyse_hpo.py`)

```
total [Term] stanzas          : 20,482
obsolete (excluded)          :    588
live terms                   : 19,894
live terms under HP:0000118  : 19,144
distinct terms used in HPOA  : 11,658   (all 11,658 resolve into hp.obo)
```

`data-version: hp/releases/2026-09-01`, `owl:versionInfo "2026-09-01"`.

### 1.2 Which terms are actual phenotypic abnormalities

This is the one modelling decision that matters, and it is **not** a namespace filter.

**`hp.obo` contains no `namespace:` lines at all.** I parsed all 19,894 live terms and every
namespace counter came back empty. The classic OBO idiom
(`namespace: phenotypic_abnormality`) does not work on the current file, so any pipeline
that filters HPO by namespace will silently select zero terms.

The working test is `is_a` ancestry to the root abnormality term:

- `HP:0000118` = *Phenotypic abnormality*
- 23 terms sit **directly** under it
- **19,144** live terms are *transitively* under it

Those 19,144 are the usable symptom vocabulary. The ~750 terms outside that subtree are
modes of inheritance (`HP:0000005`), clinical modifiers, clinical courses, inheritance
modes and similar — those are disease metadata, not patient-reported symptoms, and must be
excluded or they pollute set-algebra scoring.

Also exclude `is_obsolete: true` terms (588 of them).

### 1.3 Plain-English labels and `layperson` synonyms

HPO labels are already English and mostly 1–3 words: **10,006** of the 19,144 in-scope terms
have 1–3 word labels. Better, HPO has an explicit synonym scope
`synonymtypedef: layperson "layperson term"`, used as
`synonym: "Throwing up" EXACT layperson`.

- **4,899** live HPO terms carry at least one `layperson`-scoped synonym
- **3,512** of the 11,658 HPOA-annotated terms do (30.1%)

Verified examples (from `hp.obo`):

| HP ID | Label | layperson synonym(s) |
|---|---|---|
| HP:0001945 | Fever | Fever |
| HP:0012735 | Cough | Cough, Coughing |
| HP:0002315 | Headache | Headache, Headaches |
| HP:0002013 | Vomiting | Throwing up |
| HP:0002014 | Diarrhea | Diarrhoea (uk_spelling) |
| HP:0002094 | Dyspnea | Breathing difficulty |
| HP:0012378 | Fatigue | Tired |
| HP:0001250 | Seizure | Epilepsy |
| HP:0012531 | Pain | Pain |

This is the answer to research question 7: **HPO itself carries the plain-English bridge.**
No external vocabulary is needed to translate "tired" → Fatigue.

### 1.4 Licence — read this before redistributing

The licence is **not cleanly established from a primary source right now.** Observed:

- `hp.obo` declares `property_value: terms:license https://hpo.jax.org/app/license`.
  **That URL returns HTTP 404.**
- `LICENSE.md` in the HPO repo is 90 bytes and says only: *"Please read the license
  explanation at the [HPO website](https://hpo.jax.org/app/license)"* — the same dead URL.
- The OBO Foundry entry for HPO lists the licence as a link to
  `http://www.human-phenotype-ontology.org`, which resolves to the HPO site root — circular,
  no licence text.
- `dc:rights` in `hp.obo` names rights holders only
  ("Peter Robinson, Sebastian Koehler, The Human Phenotype Ontology Consortium, and The
  Monarch Initiative") and states no grant.
- GitHub's API reports the repo licence as `NOASSERTION` / "Other".
- There is no license page in the HPO `mkdocs.yaml` nav.

Third-party corroboration: the Open Targets published data-source licence table
(`https://platform-docs.opentargets.org/licence.md`, verified 200) lists **`HPO | CC0 1.0`**,
and `MONDO | CC-BY 4.0`, `Orphanet | CC-BY 4.0`.

**Verdict:** treat HPO as **CC0 1.0 per Open Targets**, which is the most permissive and most
likely correct reading, but mark the *primary-source* licence **UNVERIFIED**. Before shipping
a redistributed artefact, either (a) re-check `hpo.jax.org` for a restored licence page, or
(b) email the consortium. CC0 places no obligation on us either way, which is why this is
low-risk, but do not assert "CC0" in a NOTICE file on my authority alone.

---

## 2. HPO annotations to diseases (HPOA) — the key dataset

**Maintainer:** same consortium; released as GitHub release assets from the HPO repo.
Curated from OMIM, Orphanet and DECIPHER.
**File:** `phenotype.hpoa`, tab-separated, 12 columns.
**Size:** 35,816,037 bytes (34.2 MB).
**API key / click-through:** none.
**Distinct diseases: 12,880. Distinct symptoms: 11,658.**

### 2.1 Counts (computed, `analyse_hpo.py`)

```
#description: "HPO annotations for rare diseases [8478: OMIM; 47: DECIPHER; 4357 ORPHANET]"
#version: 2026-09-02

annotation rows                 : 286,651
distinct database_id (diseases) : 12,880
distinct HPO terms used         : 11,658
by prefix  : OMIM 8,478 | ORPHA 4,355 | DECIPHER 47
qualifiers : blank 285,918 | NOT 733
```

The file's own header advertises 4,357 Orphanet diseases; the file actually contains **4,355**
distinct `ORPHA:` ids. Trust the data, not the header.

### 2.2 The yield curve that answers the planning question

```
diseases with >= 3 distinct HPO terms : 12,307
diseases with >= 5 distinct HPO terms : 11,277
diseases with >=10 distinct HPO terms :  8,983
diseases with >=15 distinct HPO terms :  7,213
diseases with >=20 distinct HPO terms :  5,658
```

**11,277 diseases with ≥5 symptoms, unfiltered.** The 500–2,000 target is met by a factor of
5.6 at the top of the range and 22× at the bottom, from this one file.

Top annotations reach 233 terms for a single disease (OMIM:618505, Stolerman
neurodevelopmental syndrome), so the long tail is not the constraint.

### 2.3 Format gotchas

Columns: `database_id, disease_name, qualifier, hpo_id, reference, evidence, onset,
frequency, sex, modifier, aspect, biocuration`.

- **Drop `qualifier == "NOT"`** (733 rows). Those assert the phenotype is *absent*; including
  them inverts the clinical meaning.
- `database_id` is `OMIM:` / `ORPHA:` / `DECIPHER:` — three namespaces, no MONDO.
- `frequency` is often populated (e.g. `1/2`) and is a genuine clinical signal that the
  current pipe-separated format throws away. Worth keeping.
- `aspect` is uniformly `P` (phenotype).

---

## 3. Monarch Initiative API

**Base URL:** `https://api.monarchinitiative.org/v3/api/`

**No API key required.** Confirmed by anonymous GET with no auth header:
`/v3/api/entity/MONDO:0005148` → **200**, `application/json`, 18,512 bytes, returning type 2
diabetes mellitus. No registration, no click-through.

Disease→phenotype query works keyless:

```
/v3/api/association?subject=MONDO:0005148
    &category=biolink:DiseaseToPhenotypicFeatureAssociation&limit=100
→ 200, total = 4, objects = Insulin resistance, Increased waist to hip ratio,
  Type II diabetes mellitus
```

Items carry `subject`, `object` (HP ID), `subject_label`, `object_label`, `predicate`
(`biolink:has_phenotype`), `negated`, `publications`, `knowledge_level`.

Scale: `.../association?category=biolink:DiseaseToPhenotypicFeatureAssociation&limit=1`
returns **`total: 267,890`**.

### 3.1 Monarch is NOT a substitute for HPOA — important

- `?subject=OMIM:619340&category=biolink:DiseaseToPhenotypicFeatureAssociation` returns
  **`total: 0`**. OMIM:619340 has 7 rows in `phenotype.hpoa`. Monarch simply does not ingest
  the HPOA OMIM disease annotations; it is indexed on MONDO identifiers.
- Monarch's own total (267,890) is close to HPOA's row count (286,651), which makes the gap
  easy to miss. It is not the same data.

**Use:** good for a small live demo or spot-checking; bad as the bulk source. It is also
rate-limited and would need 12,880 requests to replicate HPOA.

---

## 4. NCBI MedGen and its disease-concept source

**Maintainer:** NCBI / NLM.
**Root:** `https://ftp.ncbi.nlm.nih.gov/pub/medgen/` — verified 200. Updated weekly
(Wednesdays). No key, no click-through, plain anonymous FTP-over-HTTPS.

Directory contents (observed sizes, 2026-10-03 build):

| File | Size | Purpose |
|---|---|---|
| `README.txt` | 17 KB | authoritative column docs |
| `MedGen_Sources.txt` | 10 KB | **the disease-concept source list** |
| `MedGen_HPO_Mapping.txt.gz` | 389 KB | HPO term ↔ CUI |
| `MedGen_HPO_OMIM_Mapping.txt.gz` | 4.1 MB | OMIM ↔ HPO ↔ CUI |
| `MedGenIDMappings.txt.gz` | 5.5 MB | CUI ↔ source IDs |
| `MGCONSO.RRF.gz` | 15 MB | concept names + sources |
| `MGDEF.RRF.gz` | 5.1 MB | definitions |
| `MGREL.RRF.gz` | 15 MB | relationships |
| `csv/` | — | same content, `.csv.gz` instead of pipe-delimited `.RRF` |

### 4.1 The disease-concept source

`MedGen_Sources.txt` is exactly the requested artefact: **123 source vocabularies** MedGen
aligns, with abbreviation, description and URL. Includes `HPO`, `MONDO`, `ORDO`, `ORPHANET`,
`OMIM`, `ICD10CM`, `MSH` (MeSH), `SNOMEDCT`, `GO`, `ClinVar`, `GTR`.

### 4.2 Measured yield

`MedGen_HPO_Mapping.txt.gz` — 20,484 rows, **19,643** distinct CUIs, 19,643 distinct HPO IDs.
Delimiter is `|`, not tab (the README does not say so).

`MedGen_HPO_OMIM_Mapping.txt.gz` — 211,400 rows, 10,621 distinct MIM numbers, 9,973 distinct
HPO IDs. Relationship column values:

```
manifestation_of 179,184 | inheritance_type_of 11,748 | related_to 10,788
mapped_from 3,903 | (blank) 2,246 | disease_has_associated_gene 1,034
```

Filtering to `relationship == manifestation_of` (the only clean phenotype edge):

```
rows                              : 179,184
distinct MIM                      :  8,583
  with >=3 HPO terms              :  7,447
  with >=5 HPO terms              :  6,583
  with >=10 HPO terms             :  4,977
  with >=20 HPO terms             :  3,054
distinct HPO terms used           :  9,663
```

This is a genuinely independent NCBI-maintained copy of the HPO→disease mapping, with MedGen
CUIs attached. Useful as a cross-check on HPOA and as a bridge to MeSH/ICD names.

### 4.3 Licence

NCBI's copyright page (`https://www.ncbi.nlm.nih.gov/home/about/policies/`, verified 200)
states verbatim:

> "Information that is created by or for the US government on this site is within the public
> domain. Public domain information on the National Library of Medicine (NLM) Web pages may be
> freely distributed and copied. However, it is requested that in any subsequent use of this
> work, NLM be given appropriate acknowledgment."

That establishes public-domain status for NLM-authored MedGen files, with attribution
requested.

**But the same page carries the caveat that decides the risk:** *"this site contains
resources which incorporate material contributed or licensed by third parties."* MedGen CUIs,
definitions and many names are inherited from the UMLS Metathesaurus, which is **not**
public domain (§5). So:

- `MedGen_HPO_OMIM_Mapping.txt.gz` restricted to the `manifestation_of` rows, keeping only
  HPO IDs and OMIM/MEDGEN names, is safe: those are HPO + OMIM identifiers, both
  separately licensed.
- `MGDEF.RRF.gz` / `MGCONSO.RRF.gz` string columns must be treated as **UMLS-tainted**. Do not
  redistribute them without reading the UMLS terms.

---

## 5. UMLS

**Maintainer:** NLM.

### 5.1 What is actually required (all three URLs verified 200)

1. **A UTS account**, created via an identity provider at `https://uts.nlm.nih.gov/uts/`
   (verified 200; the page is an Angular SPA — the login itself is not scriptable).
2. **A signed licence request form.** Per `https://www.nlm.nih.gov/databases/umls.html`
   (verified 200): *"UMLS licenses are issued only to individuals and not to groups or
   organizations."* NLM approves by email within ~5 business days.
3. **Click-through acceptance** of the Metathesaurus License, current version
   `2026AA`, at `https://uts.nlm.nih.gov/uts/assets/LicenseAgreement.pdf` (verified 200,
   311,203 bytes). An HTML copy of an earlier agreement is at
   `https://www.nlm.nih.gov/research/umls/knowledge_sources/metathesaurus/release/license_agreement.html`.
4. **An annual usage report**, due every January, completed via the UTS profile.
5. For API access, a single API key from the UTS profile page.

So: no fee, but account + individual licence + annual paperwork.

### 5.2 Is redistribution permitted? **No.**

Clause 3 of the licence, quoted from the verified HTML agreement:

> "LICENSEE is prohibited from distributing the UMLS Metathesaurus or subsets of it,
> including individual vocabulary sources within the Metathesaurus, except (a) as an integral
> part of computer applications developed by LICENSEE for a purpose other than redistribution
> of vocabulary sources contained in the UMLS Metathesaurus and (b) if permitted by paragraph
> 12 of this agreement."

Note "**or subsets of it, including individual vocabulary sources**" — that closes the obvious
loophole of extracting just the parts we want. Clause 4 additionally requires informing NLM
before distributing an application that uses the Metathesaurus. Appendix 1 vocabularies carry
extra restrictions and Appendix 2 covers SNOMED CT, which has its own fee structure outside
IHTSDO member countries.

**Verdict: hard blocker for a redistributable knowledge base.** A Meridian KB that ships
UMLS-derived strings would breach clause 3. Use UMLS internally for lookup if at all; never
bake its strings into a redistributed artefact. Note also that MedGen's own strings derive
from UMLS, which is why §4.3 restricts us to HPO and OMIM identifiers from MedGen.

---

## 6. Other open disease–phenotype files

### 6.1 Orphanet / ORPHADATA — usable, CC BY 4.0

**Maintainer:** Orphanet, coordinated by INSERM US14, Paris.

`https://www.orphadata.com` (verified 200) is the commercial front end. The open section is
**Orphadata Science**, at `https://sciences.orphadata.com/orphanet-scientific-knowledge-files`
(verified 200), "made available for download below via the CC BY 4.0 licence and bi-annually
released in July and December". The catalogue PDF states Product 1 (Orphadata Science) is
"no fee, no contract, CC BY 4.0 licence … There is no fee, and no need to sign an
agreement/contract to access Orphadata Science files, but the licence terms must be
followed."

Crucially, the files are mirrored in a public GitHub repo under CC BY 4.0, which means
**anonymous download with no registration**: `https://github.com/Orphanet/Orphadata_aggregated`
(verified 200; GitHub API reports the licence as CC BY 4.0).

**a) `en_product4.xml` — rare diseases with associated phenotypes**

Verified URL (real bytes, 47,893,357):
`https://media.githubusercontent.com/media/Orphanet/Orphadata_aggregated/master/Rare%20diseases%20with%20associated%20phenotypes/en_product4.xml`

The licence is not merely asserted on a website — it is **embedded in the file**:

```xml
<Availability><Licence>
  <FullName lang="en">Creative Commons Attribution 4.0 International</FullName>
  <ShortIdentifier>CC-BY-4.0</ShortIdentifier>
  <LegalCode>https://creativecommons.org/licenses/by/4.0/legalcode</LegalCode>
</Licence></Availability>
<HPODisorderSetStatusList count="4357">
```

Structure is `Disorder` → `OrphaCode` → `HPODisorderAssociationList` →
`HPODisorderAssociation` → `HPO/HPOId`, `HPO/HPOTerm`, `HPOFrequency/Name`.

Measured (`analyse_orphanet_p4.py`):

```
<Disorder> elements            : 4,357
disorders with >=1 HPO term    : 4,355
  >=5  distinct HPO terms      : 4,184
  >=10 distinct HPO terms      : 3,692
  >=20 distinct HPO terms      : 2,481
  >=50 distinct HPO terms      :   508
distinct HPO ids used          : 8,758
distinct HPOTerm strings       : 8,757   (5,774 are 1-3 words)
frequency qualifiers: Occasional 43,064 | Frequent 39,975 | Very frequent 25,662
                    | Very rare 6,602 | Excluded 733 | Obligate 628
```

**b) HOOM — the HPO-ORDO Ontological Module**

Verified URL (4,746,267 bytes, `application/zip`):
`https://raw.githubusercontent.com/Orphanet/Orphadata_aggregated/refs/heads/master/Orphanet%20Ontologies/HOOM/hoom_orphanet_2.5..zip`

Contains a single 195.8 MB OWL/XML file. It is OWL, not OBO, and it **reifies each
assertion into its own `owl:Class`** whose IRI encodes the triple:

```
#Orpha:2632_HP:0000218_Freq:VF
```

Parsing those IRIs (`analyse_hoom.py`):

```
owl:Class stanzas                            : 963,548
assertions carrying ORPHA+HP in the IRI      : 115,305
distinct ORPHA diseases with >=1 HPO term    :   4,340
  >=5  distinct HPO terms                    :   4,160
  >=10 distinct HPO terms                    :   3,663
distinct HPO terms used                      :   8,676
frequency qualifiers: OC 128,235 | F 117,726 | VF 76,362 | VR 19,584
```

Note OWL/XML uses a bare `IRI=` attribute for these nodes, not `rdf:about`; a parser that
only looks at `rdf:about` finds nothing.

**c) Relationship to HPOA — additive, but small**

Orphanet's 4,355 HPO-annotated disorders are the *same* disorders as HPOA's 4,355 `ORPHA:`
rows. Orphanet adds **value, not reach**: (i) explicit frequency buckets, (ii) its own
curation independent of HPOA, (iii) a primary-source CC BY 4.0 grant. HOOM reaches only
4,340 of the 4,355.

### 6.2 MONDO — the disease-ID bridge (CC BY 4.0 per Open Targets)

**Maintainer:** Monarch Initiative.
**Verified URL:** `https://purl.obolibrary.org/obo/mondo.obo` — 200, 53,134,854 bytes (50.7 MB),
`data-version: releases/2026-09-01`. No key.
**Measured:** 36,015 `[Term]` stanzas, 3,906 obsolete, **32,109 live classes**.
**Distinct diseases obtainable: 32,109** — 2.5× HPOA's 12,880, and it covers the common
conditions HPOA lacks.

Crosswalk reach against HPOA (`analyse_mondo.py`):

```
MONDO terms xref OMIM        :  9,807
MONDO terms xref Orphanet    :  9,051   (written "Orphanet:", not "ORPHA:")
MONDO terms xref MEDGEN      : 21,661

HPOA OMIM  diseases resolvable into MONDO : 8,386 / 8,478  (98.9%)
HPOA ORPHA diseases resolvable into MONDO : 4,321 / 4,355  (99.2%)
unresolved                               :   173
HPOA diseases mapped to MONDO             : 12,707
  of those with >=5 HPO symptoms          : 11,186
distinct MONDO ids implied               : 10,579
```

So MONDO converts HPOA into one consistent disease namespace with a 98.9% success rate.

It also supplies the common conditions HPOA never annotates. Exact name hits in MONDO:
influenza, common cold, asthma, gastroenteritis, urinary tract infection, depressive disorder,
malaria, pneumonia, tuberculosis, chikungunya, otitis media, conjunctivitis (12 of 20 probes).
Absent as exact names: migraine, hypertension, iron deficiency, dengue, coronavirus.

Parsing gotcha: MONDO xrefs carry a trailing qualifier block —
`xref: OMIM:125853 {source="MONDO:equivalentTo", source="DOID:9352"}` — so you must split on
`{` before matching the prefix.

### 6.3 DisGeNET — **exclude**

**Maintainer:** disgenet.com (the legacy `disgenet.org` now redirects there;
`data.disgenet.org` **fails DNS resolution** — `getaddrinfo failed`).

Reasons to rule it out:

1. **Wrong axis.** DisGeNET is gene–disease and variant–disease, not phenotype–disease. Even
   its 4.0 figures (429,036 GDAs over 15,093 diseases) are molecular, so it cannot supply
   symptom lists.
2. **No redistribution.** The verified support article
   `.../202000087487-do-i-need-a-commercial-license-can-i-use-disgenet-data-in-my-product-`
   states: *"Our standard licenses do not allow redistributing or reselling the entire
   database or a portion of it. This applies to both the whole dataset and any part of it."*
   And: *"our licenses do not allow using or incorporating the DISGENET database, or any part
   of it, in products for resale."*
3. **Gated.** `https://disgenet.com/plans` (verified 200) offers a free Academic plan by
   application form, with Standard and Advanced both "Contact us for pricing".

---

## 7. Does any source map phenotypes to plain-English symptom words?

**Yes — HPO does this natively, via the `layperson` synonym scope.** This is the single most
useful finding for Meridian, because it means no external terming layer is needed.

- 4,899 live HPO terms carry a `layperson`-scoped synonym; 3,512 of the 11,658 HPOA-annotated
  terms do.
- Orphanet contributes 8,757 `HPOTerm` strings, 5,774 of them 1–3 words, independently
  curated and CC BY 4.0.

### 7.1 How badly does HPO fit the *existing* 15-disease vocabulary?

I tested all 53 distinct symptoms currently in `data/diseases.csv` against the HPOA-annotated
HPO vocabulary, matching on exact label then on synonym (`plan_combination.py`):

```
seed symptoms matching an HPO label exactly : 23 / 53
matchable only via an HPO synonym           : 15 / 53
no HPO term at all                          : 15 / 53
```

Synonym-rescued examples — all one-directional misses that a naive swap would break. IDs
below were resolved from `hp.obo` by `verify_synonym_ids.py`, not written from memory:

| Seed symptom | HPO label | HP ID (verified) | matching HPO synonym |
|---|---|---|---|
| runny nose | Rhinorrhea | HP:0031417 | `Runny Nose` |
| sore throat | Pharyngalgia | HP:0033050 | `Sore throat`, `Throat discomfort` |
| frequent urination | Pollakisuria | HP:0100515 | `Frequent urination` |
| rash | Skin rash | HP:0000988 | `Rash`, `Skin rash` |
| joint pain | Arthralgia | HP:0002829 | `Joint pain`, `Joint pains` |
| bleeding gums | Gingival bleeding | HP:0000225 | `Bleeding gums` |
| sweating | Hyperhidrosis | HP:0000975 | `Excessive sweating` |
| muscle pain | Myalgia | HP:0003326 | `Muscle ache`, `Muscle pain` |
| dizziness | Vertigo | HP:0002321 | `Dizziness`, `Dizzy spell` |
| shortness of breath | Dyspnea | HP:0002094 | `Breathing difficulty` |
| irregular heartbeat | Arrhythmia | HP:0011675 | `Abnormal heart rate` |
| weight gain | Increased body weight | HP:0004324 | `Weight gain` |
| hair loss | Alopecia | HP:0001596 | `Hair loss` |
| diarrhoea | Diarrhea | HP:0002014 | `Watery stool` |
| loss of smell | Anosmia | HP:0000458 | `Lost smell` |

All 15 were confirmed to match a real HPO synonym, not merely to have a same-named term
somewhere in the file.

With **no** HPO term at all (15): `sneezing`, `mild fatigue`, `excessive thirst`,
`increased hunger`, `burning urination`, `cloudy urine`, `pale skin`, `fast heartbeat`,
`severe headache`, `sensitivity to light`, `sensitivity to sound`, `visual disturbance`,
`persistent worry`, `difficulty concentrating`, `loss of taste`.

**Implication:** `triage.py`'s exact-string set algebra cannot consume HPO labels directly.
38 of 53 existing symptoms would silently stop matching, and triage would degrade to
"weak evidence" on everything. Any HPO-backed KB needs a **symptom-normalisation layer**:
canonical HPO label + all synonyms + a small hand-curated supplement for the handful of
genuinely absent concepts (polydipsia, photophobia, phonophobia...). This supplement is small
precisely *because* HPO covers the rest — that is the payoff.

### 7.2 The honest limitation: HPOA is a rare-disease resource

Frequency of a term across HPOA's 12,880 diseases (how many diseases carry it):

```
1-1 diseases :  2,904 terms      100-199 :   349 terms
2-4          :  3,293                 200-499 :   179
5-9          :  1,829                 500-999 :    46
10-24        :  1,685                 1000+  :    20
25-49        :    828
50-99        :    515
```

The most-annotated terms are congenital rare-disease descriptors, not acute complaints:

```
4,265  Autosomal recessive inheritance      (not a symptom)
3,569  Autosomal dominant inheritance       (not a symptom)
2,583  Global developmental delay           lay: none
2,544  Seizure                              lay: 'Epilepsy'
2,480  Intellectual disability               lay: 'Low intelligence'
1,875  Short stature
1,863  Hypotonia                            lay: 'Low muscle tone'
```

Meanwhile the everyday words in a triage demo are thin or absent:

| Term | HPO ID | Diseases carrying it |
|---|---|---|
| Fever | HP:0001945 | 409 |
| Vomiting | HP:0002013 | 416 |
| Fatigue | HP:0012378 | 406 |
| Diarrhea | HP:0002014 | 374 |
| Headache | HP:0002315 | 317 |
| Abdominal pain | HP:0002027 | 329 |
| Dyspnea | HP:0002094 | 268 |
| Cough | HP:0012735 | 165 |
| Skin rash | HP:0000988 | 167 |
| Nausea | HP:0002018 | 136 |
| Pain | HP:0012531 | 88 |
| Anosmia | HP:0000458 | 56 |
| **Ageusia** (loss of taste) | HP:0041051 | **0 — absent from HPOA** |

**HPOA cannot triage influenza vs COVID-19 vs dengue.** All three are common infectious
diseases that MONDO names but HPOA never annotates with fever/cough/anosmia patterns. Any
demo that promises "type fever and cough, get your likely conditions" needs the current 15
diseases *retained alongside* HPOA, not replaced by it.

---

## 8. Practical answer: which combination builds ≥500–2,000 diseases with ≥5 symptoms, redistributably?

### 8.1 Yield under a "lay-reportable" filter

The raw 11,277 figure is flattered by specialist terms. To measure what survives a realistic
symptom-typing interface, I filtered the vocabulary by *how many diseases carry the term* —
an objective, data-driven criterion with no hand-picked list (`plan_combination.py`):

| Term must appear in ≥N diseases | Vocabulary size | Diseases with ≥5 such symptoms | ≥10 | ≥15 |
|---|---|---|---|---|
| 1 | 11,558 | 10,611 | 8,467 | 6,730 |
| 10 | 3,575 | 10,212 | 8,013 | 6,209 |
| 25 | 1,900 | 9,751 | 7,413 | 5,596 |
| 50 | 1,080 | 9,147 | 6,695 | 4,927 |
| **100** | **572** | **8,237** | 5,748 | 3,917 |
| 200 | 232 | 6,707 | 4,146 | 2,492 |
| 500 | 58 | 4,341 | 1,822 | 683 |
| **1000** | **15** | **1,878** | 157 | 2 |

At the ≥100-disease cut: **8,237 diseases** (OMIM 4,733 / ORPHA 3,486 / DECIPHER 18) using a
572-word vocabulary that a non-expert could plausibly type.

**The 500–2,000 target is reachable at every filter setting.** Even the extreme 1,000-disease
cut — a 15-word vocabulary — yields 1,878 diseases with ≥5 symptoms, landing inside the
requested band. Practical estimate: **comfortably 8,000–11,000 diseases with ≥5 symptoms**
from HPOA alone, with ~600–1,000 realistically typeable symptom words.

### 8.2 Recommended combination

| Role | Source | Licence | Gate |
|---|---|---|---|
| **Symptom vocabulary** | `hp.obo` (10.4 MB) | CC0 1.0 per Open Targets; primary page 404 → **UNVERIFIED** | none |
| **Disease → symptoms** | `phenotype.hpoa` (34.2 MB) | same as HPO | none |
| **Disease IDs + names** | `mondo.obo` (50.7 MB) | CC BY 4.0 | none |
| **Corroboration / frequency** | Orphanet `en_product4.xml` (45.7 MB) | **CC BY 4.0, embedded in the file** | none |
| **Cross-check + CUIs** | MedGen `MedGen_HPO_OMIM_Mapping.txt.gz` (4.1 MB) | public domain (attribution requested); restrict to `manifestation_of` | none |

Total download **~145 MB**, all anonymous HTTP GET, no registration, no click-through, no
API key. Every one of these permits redistribution with attribution (CC BY 4.0 / CC0 /
US-Government public domain).

**Two independent paths to the same 500–2,000+ target:**

- **Path A (recommended):** HPOA → MONDO crosswalk. 12,707 of 12,880 diseases mapped
  (98.7%), **11,186 with ≥5 symptoms**, 10,579 distinct MONDO IDs. Gives one consistent
  disease namespace and a name for every disease.
- **Path B (CC BY 4.0 only, if HPO's licence cannot be confirmed):** Orphanet
  `en_product4.xml` → **4,184 diseases with ≥5 symptoms**, entirely under a licence asserted
  *inside the file itself*. Comfortably exceeds the 2,000 target. Combine with HOOM
  (4,160 with ≥5) for cross-validation.

Path B is the licence-risk hedge and needs no HPO at all — though you would still need
`hp.obo` to turn 8,758 HP IDs into readable English labels.

### 8.3 Licence blockers, ranked

1. **UMLS — hard no.** Clause 3 forbids redistributing the Metathesaurus *or subsets of it*.
   This also taints MedGen's `MGDEF`/`MGCONSO` string columns, since MedGen inherits UMLS
   concepts. Use HPO and OMIM identifiers from MedGen; do not ship UMLS-derived strings.
2. **DisGeNET — hard no.** "Do not allow redistributing … any part of it", commercial licence
   required even for free products, and wrong data axis regardless.
3. **HPO — soft, needs one confirmation.** `hpo.jax.org/app/license` 404s and the repo's
   LICENSE.md just points back at it. Open Targets records CC0 1.0. Low risk because CC0
   obliges nothing, but do not assert CC0 in a NOTICE file without re-checking. If in doubt,
   Path B (Orphanet CC BY 4.0) reaches the target on its own.
4. **Monarch API — not a blocker but not a source either.** Keyless and free, yet returns
   `total: 0` for OMIM diseases that HPOA annotates richly. Fine for spot checks; do not build
   on it.

---

## 9. Reproduction

```
research/scripts/probe.py             HTTP probe; prints status/content-type/length, GET saves to research/raw/
research/scripts/verify_all_urls.py   re-probes every URL cited above; must report 1 non-200
research/scripts/analyse_hpo.py       hp.obo term counts + phenotype.hpoa annotation counts + seed coverage
research/scripts/analyse_mondo.py     MONDO size, xref crosswalk, HPOA->MONDO resolution rate
research/scripts/analyse_hoom.py      HOOM OWL reified-assertion parse
research/scripts/analyse_orphanet_p4.py  Orphanet product4 licence block + disease counts
research/scripts/plan_combination.py  the lay-vocabulary filter yield table (§8.1)
research/scripts/verify_synonym_ids.py   resolves every HP ID asserted in §7.1 against hp.obo
```

Downloads cached in `research/raw/` (hp.obo 10.4 MB, phenotype.hpoa 34.2 MB, mondo.obo
50.7 MB, en_product4.xml 45.7 MB, hoom zip 4.5 MB, MedGen mappings).

**Parser and ID bugs hit and fixed while verifying** — recorded because each produced
plausible but wrong numbers or wrong IDs: `hp.obo` has no `[Typedef]` section, so a parser
that flushes terms on section change silently keeps only the last of 20,482; `hp.obo` has no
`namespace:` lines at all, so namespace-based filtering returns zero; OWL/XML reified nodes
use a bare `IRI=` attribute, not `rdf:about`; MONDO xrefs carry trailing `{source=...}`
qualifiers; MONDO writes `Orphanet:` where HPOA writes `ORPHA:`; MedGen files are
pipe-delimited, not tab-delimited. Separately, 8 of 17 HP IDs first drafted into §7.1 from
memory were wrong (e.g. `Arthralgia` is HP:0002829, not HP:0001367) — `verify_synonym_ids.py`
now resolves every one against the ontology rather than trusting recall.