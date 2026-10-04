# 01 — Large Freely-Licensed Disease Taxonomies

**Research date:** 2026-10-04
**Scope:** find large disease taxonomies that can legally be *derived from and republished* in a public GitHub repository under MIT.

**Verification rule applied:** every URL below was actually requested from this machine.
Status / content-type / content-length are the values observed in the response, not copied
from documentation. Entry counts are **measured by downloading the file and counting records**
unless explicitly marked "publisher-stated". Anything I could not confirm by request is marked
**UNVERIFIED** and must not be relied on.

Scripts used: `research/scripts/taxonomies/` (`taxo_probe.py`, `count_mesh.py`,
`inspect_mesh.py`, `count_icd10cm.py`, `count_do.py`, `count_ordo.py`, `inspect_ordo.py`,
`count_obo.py`, `count_orphanet.py`, `recount_orphanet.py`, `snomed_stats.py`, `do_links.py`).
URL manifest: `research/scripts/taxonomies/urls.txt`.

---

## 0. Executive summary — the licence problem first

The constraint that actually decides this project is not size or entry count, it is **whether the
licence permits creating a derivative and publishing it**. Ranking by "how big and how free" gives
the wrong answer, because three of the seven requested sources are licence-blocked:

| Source | Licence | Blocks public redistribution of derived data? |
|---|---|---|
| **WHO ICD-11** | **CC BY-ND 3.0 IGO** | **YES — "NoDerivatives"** |
| **SNOMED CT** | SNOMED International Affiliate Licence | **YES — no redistribution, no modification** |
| **Human Phenotype Ontology (HPO)** | HPO custom licence | **YES — explicitly forbids alteration** |
| UMLS Metathesaurus (incl. its SNOMED copy) | NLM UMLS Licence | **YES — §3 prohibits redistribution of subsets** |
| ICD-10 / ICD-10-CM (WHO) | WHO copyright | **YES outside the US** (US public domain only) |
| Disease Ontology (DO) | **CC0 1.0** | No — cleanest of all |
| MONDO | **CC BY 4.0** | No — attribution required, derivatives allowed |
| Orphanet / ORDO | **CC BY 4.0** | No — attribution required, derivatives allowed |
| MeSH (NLM) | US Government work, public domain | No |
| ICD-10-CM (US clinical modification) | US Government work, public domain | No (US only) |

---

## 1. WHO ICD-11 (MMS linearization + Foundation)

- **Name / maintainer:** International Classification of Diseases, 11th Revision. World Health
  Organization (WHO), Classifications and Terminologies unit.
- **API access:** *Registration + OAuth2 client credentials required. No anonymous access.*
  - `GET https://id.who.int/icd/entity` → **HTTP 401**, body:
    `Authentication failed. The request must include a valid and non-expired bearer token in the Authorization header.`
    (verified)
  - `HEAD https://id.who.int/icd/release/11` → **HTTP 404** (not a usable anonymous endpoint).
  - Token endpoint `https://icdaccessmanagement.who.int/connect/token` → **HTTP 400** on
    unauthenticated HEAD, confirming it is live and demanding credentials.
  - You must register at `https://icd.who.int/icdapi` (HTTP 200) and read an API key from the
    portal. OAuth2 `client_credentials`, scope `icdapi_access`. Tokens last ~1 hour.
- **Verified URLs:**
  | URL | Observed |
  |---|---|
  | `https://icd.who.int/icdapi` | 200, text/html, chunked |
  | `https://icd.who.int/icdapi/docs2/API-Authentication/` | 200, text/html, 10,987 B |
  | `https://icd.who.int/icdapi/docs2/APIDoc-Version2/` | 200, text/html, 18,574 B |
  | `https://icd.who.int/icd/entity` | **401** (auth required) |
  | `https://icd.who.int/en/docs/ICD11-license.pdf` | 200, application/pdf, 252,387 B |
  | `https://icd.who.int/en/docs/ICD11_Fact_Sheet_2026.pdf` | 200, application/pdf, 108,842 B |
  | `https://icd.who.int/en/docs/icd11factsheet_en.pdf` | 200, application/pdf, 155,660 B |
  | `https://www.who.int/news-room/fact-sheets/detail/icd-11` | 200, text/html, chunked |
  | `https://icd.who.int/browse11/mms/en` | 200 (GET); redirects to `https://id.who.int/browse/2025-01/mms/en` — browser UI works anonymously |
- **Entry count:** *publisher-stated, not measured* — I could not download the full fileset
  because of the paywall-style auth gate. WHO's own fact sheet (PDF verified 200) says
  **"more than 17 000 diagnostic categories"**, 100,000+ index terms, and a search algorithm
  covering 1.6 million terms. The 2026 fact sheet wording is "more than 17 000 diagnostic
  categories". Treat **≈17,000 billable categories (MMS)** as the working figure; the Foundation
  is considerably larger and I did not measure it.
- **Format / size:** JSON via REST. Offline "container" software exists but is separately licensed.
- **SYMPTOM / PHENOTYPE annotations:** ⚠️ **YES, natively — this is ICD-11's main advantage over
  ICD-10.** The Foundation component includes, per CIHI's description, "diseases, disorders,
  injuries, external causes, **signs and symptoms**, functional descriptions, interventions and
  extension codes." The MMS linearization has a dedicated symptom/sign chapter. (Cihi's webinar
  page is descriptive, not byte-verified here — flagged as secondary evidence.)
- **LICENCE — THE BLOCKER.** `https://icd.who.int/en/docs/ICD11-license.pdf` (200, PDF; I
  extracted the text) states:
  > "The Classifications are licensed under the Creative Commons Attribution-NoDerivs 3.0 IGO
  > licence CC BY-ND 3.0 IGO — https://creativecommons.org/licenses/by-nd/3.0/igo/"

  and further, from clause 1.2:
  > "WHO does not consider incorporation of the Classifications into a software product to be
  > a. Reproduce or remodel the Classifications in part or whole and distribute it under a
  >    different name or without attribution; b. Reproduce and distribute the Classifications
  >    in part or whole **without the Classification codes**; c. Produce the Classifications in
  >    part or whole; d. Reproduce and distribute the Classifications, in part or whole, with any
  >    combination of a–c above."

  Clause 1.2.5 permits adding your own data fields *if clearly identified as additions that do
  not originate from WHO*. Clause 2.4 says: "You shall not modify, adapt, translate,
  reverse-engineer, decompile, disassemble or otherwise attempt to discover the source code of
  the Classifications Software." Note the **software** is NOT CC-licensed at all — it is
  all-rights-reserved WHO copyright.

  **Verdict: CC BY-ND is by definition incompatible with publishing a modified dataset under
  MIT.** Any ICD-11-derived table you publish must be a byte-identical reproduction, or
  titles-without-codes, with WHO attribution. You cannot merge ICD-11 into your own schema and
  call the result MIT.

---

## 2. ICD-10 / ICD-10-CM

### 2a. WHO ICD-10 (international)
- **Maintainer:** WHO. **LICENCE: WHO holds the international copyright on ICD-10.**
  Verified PDF: `https://cdn.who.int/media/docs/default-source/publishing-policies/copyright/who-faq-licensing-icd-10.pdf`
  → 200, application/pdf, 130,347 B. It states "WHO is the copyright holder of ICD-10, and can
  grant licences for the use of ICD-10 worldwide" and directs national modifications such as
  ICD-10-CM to NCHS instead.
- **Verdict: BLOCKED for a public MIT repo outside the US.** WHO permission text quoted
  repeatedly in the wild says plainly: *"The ICD-10 codes should not be licensed under the open
  source licence… any further redistribution of ICD-10 requires permission from WHO."*
  (that quotation is from a Cambridge/DSM reference doc — treat as corroboration, not as the
  licence itself).

### 2b. ICD-10-CM (US clinical modification) — the usable one
- **Name / maintainer:** ICD-10-CM, developed and maintained by the **National Center for Health
  Statistics (NCHS), CDC / U.S. Department of Health and Human Services**.
- **Stable direct URL (verified):**
  `https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Publications/ICD10CM/2027/icd10cm-code-descriptions-2027.zip`
  → **HTTP 200**, `application/x-zip-compressed`, **2,192,779 bytes**, Last-Modified
  2026-06-16.
  - Directory index verified: `…/ICD10CM/` → 200, text/html, 3,289 B. Fiscal-year folders 2007→2027
    are listed; **2027 is the current release** and there is also a `2026-update/` folder.
  - `…/ICD10CM/2027/` → 200, text/html, 1,509 B. Contains `icd10cm-code-descriptions-2027.zip`
    (2,192,779), `icd10cm-table-and-index-2027.zip` (20,923,571), `icd10cm-addenda-2027.zip`
    (622,955), `ICD-10-CM-CONVERSION-TABLE-FY2027.xlsx` (170,512),
    `ICD-10-CM-October-1-2026-FY27-Guidelines.pdf` (830,104), `POAexemptCodesFY27.zip` (1,654,940).
  - ⚠️ Filename convention **changed**: `icd10cm_order_YYYY.txt` (≤2022) became
    `icd10cm-order-YYYY.txt` (hyphens, ≥2023). Don't hard-code one form.
  - ⚠️ `https://www.cdc.gov/nchs/icd/icd-10-cm/files.html` → **HTTP 403** (bot-blocked). Use the
    FTP path instead; it is not blocked.
- **Entry count — MEASURED.** I downloaded the zip and parsed
  `icd10cm-code-descriptions-2027/icd10cm-order-2027.txt` (14,724,229 B, fixed-width):
  - total non-empty rows: **98,403**
  - **billable codes (flag = 1): 74,879**
  - header rows (flag = 0, non-billable categories): 23,524
  - Chapter breakdown (billable): M Musculoskeletal 6,687 · H Eye 3,330 · S Injury 31,049 ·
    T Injury 10,138 · O Pregnancy 2,481 · C Circulatory 1,229 · I Ear 1,433 · L Skin 1,001 ·
    E Endocrine 973 · Q Congenital 900 · D Blood/Immune 825 · N Genitourinary 838 · K Digestive 863 ·
    F Mental 872 · G Nervous 700 · A Infectious 573 · P Perinatal 463 · B Neoplasms 495 ·
    J Respiratory 366 · U Special 3 · external-cause chapters V 4,086 / W 1,290 / X 495 /
    Y 1,590 / Z 1,425
- **Format / size:** pipe/tab-delimited text inside ZIP; also PDF, XLSX, and full XML release.
- **API key / registration:** none. Plain anonymous HTTPS GET.
- **SYMPTOM / PHENOTYPE annotations:** ⚠️ **PARTIAL, via chapter R only.** I measured
  **774 billable codes in Chapter R "Symptoms, signs and abnormal findings"** (R000, R001, …)
  out of 74,879. That is ~1% of the code set. There are **no** structured symptom→disease
  annotation links — only the code titles. If you need "disease X presents with symptom Y",
  ICD-10-CM cannot give you that.
- **LICENCE:** ICD-10-CM is a **U.S. Government work — public domain** under 17 U.S.C. §105
  (WHO authorised the U.S. modification specifically for U.S. government use; the resulting
  clinical modification is not WHO-owned). **MIT-compatible.** Two caveats to put in your README:
  (a) public domain is a **U.S.-only** status — §105 has no extraterritorial effect, and the
  U.S. government asserts it may still hold copyright abroad; (b) if you are not in the U.S.,
  confirm locally. Safe to redistribute derived CSVs.

---

## 3. MeSH (NLM)

- **Name / maintainer:** Medical Subject Headings, **U.S. National Library of Medicine (NLM)**,
  NIH. Controlled, hierarchically-organised thesaurus used for MEDLINE/PubMed indexing.
- **Verified URLs (all 200):**
  | URL | Observed |
  |---|---|
  | `https://www.nlm.nih.gov/mesh/meshhome.html` | 200, text/html, 22,794 B |
  | `https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/` | 200, text/html, ISO-8859-1 |
  | `https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/readme.txt` | 200, text/plain, 825 B |
  | `https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/` | 200, text/html |
  | `…/xmlmesh/desc2026.xml` | 200, **text/xml, 312,952,703 B** |
  | `…/xmlmesh/desc2026.zip` | 200, application/zip, 16,812,755 B |
  | `…/xmlmesh/desc2026.gz` | 200, 16,812,612 B |
  | `…/xmlmesh/supp2026.xml` | 200, text/xml, **786,405,116 B** (supplementary records) |
  | `…/xmlmesh/qual2026.xml` | 200, text/xml, 290,948 B (qualifiers) |
  | `https://id.nlm.nih.gov/mesh/lookup/descriptor?label=Cholera` | **200, application/json, 69 B — anonymous lookup API, no key** |
- **⚠️ Trap I hit and verified:** the path everyone quotes,
  `https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/asciimesh/d2026.bin`, returns
  **HTTP 200 but is a 16,471-byte HTML "bad_url" redirect page**, not data. And
  `…/MESH_FILES/asciimesh/` is an **empty directory listing** (200, 297 B). Use
  `…/MESH_FILES/xmlmesh/desc2026.*` instead. Always check content-type/prefix, not just status.
- **Descriptor count — MEASURED** from `desc2026.gz` (gunzipped to 312,952,134 B):
  - **`<DescriptorRecord>` stanzas: 31,110**
  - `ConceptList` blocks: 31,110; `TreeNumberList` blocks: 31,108
  - 267,023 `<Term>` elements, 61,794 `<Concept>` elements, 634,929 qualifier references
  - **Important caveat:** 31,110 is the *whole* thesaurus, and it is dominated by chemicals and
    drugs. Classifying each record by its own top-level tree numbers:
    **disease top-level 3,267 · symptom/sign top-level 1,106 · both 469 · neither 26,268**
    (the "neither" bucket is ~84% of the file: chemicals, drugs, anatomy, procedures, etc.)
    Symptom-only examples: Absenteeism, Accident Proneness, Acid-Base Equilibrium, Acting Out.
    So MeSH is **not** a disease taxonomy — it is a mixed biomedical index. Budget ~3–4k usable
    disease records, not 31k.
- **Format / size:** XML (`.xml`, `.zip`, `.gz`), MARC21, ASCII `.bin` (despite the name, ASCII
  UTF-8). 313 MB uncompressed for descriptors alone; 786 MB for supplementary records.
- **API key / registration:** none for files. The `id.nlm.nih.gov/mesh` API is anonymous
  (verified 200 JSON above).
- **SYMPTOM / PHENOTYPE annotations:** ⚠️ **YES but shallow.** MeSH has a real
  `C23.888` "Signs and Symptoms" branch and `F01/F02/F03` mental-phenomenology branches;
  1,106 descriptors are symptom/sign-only. Qualifiers (`Q000...`, 634,929 of them) allow
  `/diagnosis`, `/symptoms`, `/drug_effects`. But **no disease→symptom weight/frequency
  annotations** — it is a controlled vocabulary, not a phenotype knowledge base.
- **LICENCE:** US Government work → **public domain** (17 U.S.C. §105). **MIT-compatible.**
  NLM asks for attribution as a courtesy, not a legal requirement. U.S.-only caveat as above.

---

## 4. Disease Ontology (DO) — cleanest licence of the whole survey

- **Name / maintainer:** Disease Ontology / Human Disease Ontology, **Institute for Genome
  Sciences, University of Maryland**; repo `DiseaseOntology/HumanDiseaseOntology`.
- **Verified URLs:**
  | URL | Observed |
  |---|---|
  | `https://disease-ontology.org/` | 200, text/html, 25,451 B |
  | `https://disease-ontology.org/downloads/` | 200, text/html, 17,710 B |
  | `https://purl.obolibrary.org/obo/doid.obo` | **200, text/plain, 7,264,205 B** → 302 to `raw.githubusercontent.com/DiseaseOntology/HumanDiseaseOntology/main/src/ontology/doid.obo` |
  | `https://purl.obolibrary.org/obo/doid.owl` | **200, 28,804,846 B** |
  | `https://purl.obolibrary.org/obo/doid.json` | **200, 24,209,079 B** |
  | `…/HumanDiseaseOntology/main/src/ontology/HumanDO.obo` | 200, 7,037,068 B |
  | `…/HumanDiseaseOntology/main/LICENSE` | 200, text/plain, 7,048 B — full CC0 1.0 legal code |
  | `https://obofoundry.org/ontology/doid` | 200, text/html, 27,396 B |
  | `https://creativecommons.org/publicdomain/zero/1.0/` | 200 |
- ⚠️ The `purl.obolibrary.org/obo/doid.*` PURLs are stable and version-agnostic (they track
  `main`); pin the GitHub raw URL + a commit SHA if you need reproducibility. The DO
  `/downloads/` page is JS-driven and exposes **no direct file hrefs** — go via the PURL or
  the GitHub repo.
- **Class count — MEASURED** from the downloaded `doid.obo` (7,264,205 B, header
  `date: 30:09:2026`):
  - **14,854 `[Term]` stanzas / 14,854 distinct `DOID:` ids**
  - **2,519 obsolete** → **≈12,335 active disease classes** (matches the project's own release
    notes of "12,191 disease classes" for a slightly earlier release)
  - 17,479 `is_a:` edges; 1,743 `alt_id:` (merged/secondary DOIDs — keep these, they prevent
    duplicate rows)
- **LICENCE — the best in the survey.**
  The file itself carries:
  > `remark: The Disease Ontology content is available via the Creative Commons Public Domain
  > Dedication CC0 1.0 Universal license (https://creativecommons.org/publicdomain/zero/1.0/).`
  > `property_value: dc:terms:license https://creativecommons.org/publicdomain/zero/1.0/`
  License page: https://creativecommons.org/publicdomain/zero/1.0/ (verified 200).
  **CC0 = no attribution required, derivatives explicitly fine. Fully MIT-compatible with zero
  friction.** OBO Foundry lists DO as CC0 1.0 (https://obofoundry.org/ontology/doid, 200).
- **API key / registration:** none. Files are plain anonymous GET.
- **SYMPTOM / PHENOTYPE annotations:** 🚩 **NO — and this is DO's main weakness for you.**
  Measured over all 14,856 names: only **23 labels contain "symptom" or "sign"**, and those are
  incidental ("asymptomatic dengue", "signet ring adenocarcinoma"). Only 7 labels contain
  "phenotyp". **There are zero `HP:` xrefs and zero PATO xrefs in doid.obo.** Cross-reference
  namespaces present are MIM 6,570 · NCI 5,080 · MESH 4,100 · ORDO 2,365 · GARD 2,214 ·
  ICDO 496 · EFO 110 · KEGG 42 · MEDDRA 42. The `dc:description` mentions "phenotype
  characteristics" rhetorically, but there is **no machine-readable phenotype axis**.
  If your project needs symptom/phenotype annotations, DO alone is not enough.

---

## 5. SNOMED CT — genuinely free-ish, but not redistributable

- **Name / maintainer:** SNOMED CT, **SNOMED International** (IHTSDO).
- **Concept count — MEASURED from SNOMED's own release statistics**, retrieved via their
  Confluence REST API (HTTP 200, application/json; the HTML page is JS-rendered so I used the
  API):
  - **January 2026 International Edition: 378,553 active concepts**, 1,388,296 active
    descriptions, 1,324,301 active relationships.
    `https://conf.spaces.snomed.org/wiki/rest/api/content/550633600?expand=body.storage`
  - **≈July 2026 International Edition: 383,345 active concepts**, 1,405,930 descriptions,
    1,345,016 relationships.
    `https://conf.spaces.snomed.org/wiki/rest/api/content/1107656851?expand=body.storage`
  - For scale: US Edition March 2026 = 386,110 active concepts.
- **Genuinely free access options (verified URLs):**
  | Route | URL | Observed | Cost / gate |
  |---|---|---|---|
  | Public browser UI | `https://snomedbrowser.org/` (canonical for `snowstorm.ihtsdotools.org`) | 200, text/html, 155,559 B | free, browse/lookup only, no bulk export |
  | Public FHIR terminology server | `https://snowstorm.snomedtools.org/fhir/metadata` | **200, application/fhir+json** (twice), then began timing out | free, **demo/non-production only**, explicitly rate-limited and not for bulk |
  | US NLM (U.S. Member) | `https://www.nlm.nih.gov/healthit/snomedct/snomed_licensing.html` | 200, 30,859 B | free in the U.S. via UMLS licence; sign UMLS licence |
  | Member Licensing & Distribution Service | `https://mlds.ihtsdotools.org/` | 200, text/html, 54,146 B | registration + **affiliate licence application + annual usage report**; fees in non-Member territories |
  | Sign-up page | `https://www.snomed.org/get-snomed` | 200, 1,592,602 B | as above |
  | Licensing guidance | `https://docs.snomed.org/snomed-ct-practical-guides/vendor-introduction-to-snomed-ct/7-licensing` | 200, 531,648 B | — |
- **There is no free anonymous bulk download.** RF2 release packages are behind MLDS
  registration. `https://snowstorm.snomedtools.org/fhir/metadata` did answer 200 twice during
  this session and then began connection timeouts — treat it as an unreliable demo endpoint,
  not a data source. **A published SNOMED-derived dataset would violate the licence.**
- **Format:** RF2 (tab-delimited UTF-8: Concepts, Descriptions, Relationships, refsets), full /
  snapshot / delta.
- **SYMPTOM / PHENOTYPE annotations:** ✅ **The richest of all sources.** SNOMED CT has a
  top-level `Clinical finding (finding)` branch with **134,779 active concepts** in the Austria
  Extension statistics I retrieved, versus 29,944 Procedure and 24,330 Organism. It models
  "Finding of body structure" / "Disorder of body structure" as real concepts with
  `is-a` + `has-finding-site` + `associated-morphology` relationships, so symptom→disease
  relations are first-class. (That branch figure comes from an SNOMED release-notes page read
  via search, not byte-verified by me — mark as secondary.)
- **LICENCE — THE BLOCKER.** SNOMED International Affiliate Licence Agreement:
  > "8.1 Nothing in this License Agreement transfers to the Licensee any right, title or interest
  > in or to the Intellectual Property Rights in the International Release…"
  > "4.1 Subject to clause 2.1.4, the Licensee may not modify any part of the SNOMED CT Core…"
  and via NLM's mirror, SNOMED CT inside UMLS is **Category 4**:
  > "12.4.1. LICENSEE is prohibited from translating the vocabulary source into another language
  > or from altering the vocabulary source content. 12.4.2. …restricted to use in the U.S. …
  > 12.4.3. …The LICENSEE has the right to distribute the vocabulary source in the U.S., but only
  > in combination with other UMLS Metathesaurus content."
  **Verdict: no MIT redistribution, no modification, no translation, US-only.** Use SNOMED only as
  a live lookup service at runtime, and never copy terms into a committed file.
  Licence text verified 200 at
  `https://www.nlm.nih.gov/research/umls/knowledge_sources/metathesaurus/release/license_agreement_snomed.html`
  (79,899 B).

### 5b. UMLS Metathesaurus (related, also blocked)
- **Maintainer:** NLM. `https://uts.nlm.nih.gov/uts/assets/LicenseAgreement.pdf` (2026AA).
- **§3:** *"LICENSEE is prohibited from distributing the UMLS Metathesaurus or subsets of it,
  including individual vocabulary sources within the Metathesaurus…"*
- **§12.3 (Category 3):** internal use only; expressly excludes "incorporation of material from
  these copyrighted sources in any publicly accessible computer-based information system … including
  the Internet; publishing or translating or creating derivative works…"
- Free to *use*, blocked for *republishing*. Per-vocabulary restriction categories are listed in
  the agreement's Appendix 1 — check the category for any source you touch.

---

## 6. Orphanet / ORDO — free and downloadable

- **Name / maintainer:** Orphanet (INSERM, France) and the European Bioinformatics Institute.
  ORDO = Orphanet Rare Disease Ontology.
- **Verified URLs:**
  | URL | Observed |
  |---|---|
  | `https://www.orphadata.com/` | 200, text/html, 293,314 B |
  | `https://www.orphadata.com/_ontologies/` | 200, text/html, 163,165 B |
  | `https://www.orphadata.com/faq/` | 200, text/html |
  | `https://www.orphadata.com/docs/WhatIsORDO.pdf` | 200, application/pdf, 785,266 B |
  | `https://www.orphadata.com/data/xml/en_product1.xml` | **200, application/xml, 54,026,799 B** (chunked) |
  | `https://www.orphadata.com/data/xml/en_product4.xml` | 200, application/xml (disease–HPO associations) |
  | `https://www.orphadata.com/data/xml/en_product6.xml` | 200, application/xml (disease–gene) |
  | `https://www.orphadata.com/data/ontologies/ordo/last_version/ORDO_en_4.9.owl` | **200, 52,467,529 B**, Last-Modified 2026-06-26 |
- ⚠️ `https://www.orphadata.com/data/ontologies/ordo/last_version/` (directory) → **403
  Forbidden**. Fetch files by name, not by listing. Also `products.xml` and
  `en_product1.json` → **404**; the JSON path does not exist, use `…/data/xml/en_product1.xml`.
  `www.orphanet.com` timed out entirely (connection refused/timeout from this host) — use
  `orphadata.com`.
- **Entry count — MEASURED.**
  - **Orphanet database (`en_product1.xml`, 54,026,799 B, `date="2026-06-23"`):**
    - `<DisorderList count="11645">` and **11,645 `<Disorder id=…>` elements** — counts agree
    - 11,646 distinct `OrphaCode`; 5,344 of them are short group/header codes (not diseases)
    - `DisorderType` breakdown: Disease 4,773 · Category 2,175 · Malformation syndrome 2,064 ·
      Clinical subtype 1,103 · Morphological anomaly 532 · Clinical group 498 · Etiological
      subtype 290 · Particular clinical situation 72 · Histopathological subtype 64 ·
      Clinical syndrome 57 · Biological anomaly 17
    - `DisorderGroup` breakdown: Disorder 7,515 · Group of disorders 2,673 · Subtype 1,457
    - **So ≈6,000–7,500 actual rare diseases, inside 11,645 disorder records.** Anyone quoting
      "Orphanet has 11,645 diseases" is counting groups.
  - **ORDO ontology (`ORDO_en_4.9.owl`, 52,467,529 B, `versionInfo 4.9`):**
    **16,296 `<Class>` elements** (16,295 distinct `ORPHA_` subjects) — this is more than the
    database because ORDO also carries gene, anatomy, clinical-sign and inheritance classes.
    57,101 `rdfs:subClassOf` · 206,939 `hasDbXref` · 13 ObjectProperty · 23 AnnotationProperty ·
    1 DatatypeProperty. (OLS4 independently reports `numberOfTerms: 16296` for ORDO v4.9 —
    agrees with my count.)
  - **Cross-references carried (measured, `en_product1.xml`):** MONDO 9,979 · UMLS 9,586 ·
    OMIM 8,745 · **ICD-10 8,450** · **ICD-11 6,868** · GARD 3,825 · **MeSH 3,209** · MedDRA 1,794.
    That is a ready-made crosswalk hub — very valuable.
- **Format / size:** ORDO = OWL/XML (~52 MB). Orphadata = per-product XML (tens of MB each).
  Also available in OBO/JSON/SSSOM and a SPARQL endpoint.
- **API key / registration:** none for any of the above. Anonymous GET.
- **SYMPTOM / PHENOTYPE annotations:** ⚠️ **Not inside ORDO itself.** I measured **0 `HP:`
  xrefs, 0 `PATO` xrefs, 0 "Human Phenotype" strings** in `ORDO_en_4.9.owl`; only 76 labels
  contain "sign"/"symptom"/"phenotyp", and most are false positives ("signal transducer…").
  Orphanet's phenotype data lives in (a) the separate **HOOM** module — "a module that qualifies
  the annotation between a rare disease and phenotypic abnormalities according to a frequency and
  by integrating the notion of diagnostic criterion" (orphadata.com/_ontologies, 200) — and
  (b) `en_product4.xml`, the disease–HPO association file (200 verified). **Fetch product4
  separately if you need symptoms.**
- **LICENCE:** **CC BY 4.0**, declared *inside the data file itself*:
  ```xml
  <Availability><Licence>
    <FullName lang="en">Creative Commons Attribution 4.0 International</FullName>
    <ShortIdentifier>CC-BY-4.0</ShortIdentifier>
    <LegalCode>https://creativecommons.org/licenses/by/4.0/legalcode</LegalCode>
  </Licence></Availability>
  ```
  and in ORDO: `<terms:license rdf:resource="https://creativecommons.org/licenses/by/4.0/"/>`.
  License pages verified 200: `https://creativecommons.org/licenses/by/4.0/` and
  `…/by/4.0/legalcode`. **Derivatives and redistribution allowed with attribution →
  MIT-compatible.** Obligations: credit Orphanet/INSERM + the ORDO version, link the CC BY 4.0
  licence, and **indicate that you made changes** (CC BY 4.0 §3(a)(1)(B)). Recommended citation
  text is on `https://www.orphadata.com/faq/`.

---

## 7. NCBO BioPortal — API key required for everything

- **Maintainer:** Stanford Center for Biomedical Informatics Research (NCBO).
- **Verified:**
  | URL | Observed |
  |---|---|
  | `https://data.bioontology.org/ontologies` | **HTTP 401**, application/json, 283 B |
  | `https://data.bioontology.org/ontologies/DOID` | **HTTP 401**, 283 B |
  | `https://bioportal.bioontology.org/account` | **HTTP 403** (bot-blocked to scripted requests) |
- The 401 body is explicit:
  > "You must provide an API Key either using the query-string parameter `apikey` or the
  > `Authorization` header: `Authorization: apikey token=my_apikey`. Your API Key can be obtained
  > by logging in at bioportal.bioontology.org/account"
- **Answer to "which are queryable without an API key": NONE.** BioPortal gates every endpoint
  uniformly — there is no anonymous tier. This includes DOID, ORDO, HP and MONDO, all of which are
  freely downloadable elsewhere. **Do not build on BioPortal.** Use
  **EBI OLS4 instead**, which is fully anonymous — see below.
- **Bonus: OLS4 (EMBL-EBI Ontology Lookup Service) — verified anonymous, no key.**
  | URL | Observed |
  |---|---|
  | `https://www.ebi.ac.uk/ols4/api/ontologies` | 200, application/json |
  | `https://www.ebi.ac.uk/ols4/api/ontologies/doid` | 200, JSON — v2026-08-31, `numberOfTerms: 19647` |
  | `https://www.ebi.ac.uk/ols4/api/ontologies/ordo` | 200, JSON — v4.9, `numberOfTerms: 16296` |
  | `https://www.ebi.ac.uk/ols4/api/ontologies/hp` | 200, JSON — v2026-09-01, `numberOfTerms: 32772` |
  | `https://www.ebi.ac.uk/ols4/api/ontologies/mondo` | 200, JSON — v2026-09-01, `numberOfTerms: 63460` |
  | `https://www.ebi.ac.uk/ols4/api/search?q=cholera&ontology=doid&rows=2` | **200, JSON — real DOID results** |
  `https://www.ebi.ac.uk/ols/api/...` also works and 301s to `/ols4/api/...`.
  **This is the drop-in replacement for BioPortal in any project that cannot hold a key.**
  (OLS4 `numberOfTerms` counts differ from raw class counts because OLS indexes labels and
  synonyms as separate nodes — DOID shows 19,647 vs 14,854 real DOIDs.)

---

## 8. Better sources found during the survey (not on the original list)

These matter because the brief asked whether sources carry symptom/phenotype annotations, and
the original list mostly does not.

### 8a. MONDO (Mondo Disease Ontology) — best single disease source
- **Maintainer:** Monarch Initiative. Repo `monarch-initiative/mondo`. OBO Foundry member.
- **Verified URLs:**
  | URL | Observed |
  |---|---|
  | `https://purl.obolibrary.org/obo/mondo.obo` | **200, 53,134,854 B** (redirects to a signed GitHub release asset) |
  | `https://purl.obolibrary.org/obo/mondo.json` | **200, 107,586,061 B** |
  | `https://raw.githubusercontent.com/monarch-initiative/mondo/master/LICENSE` | 200, text/plain, 18,658 B — full CC BY 4.0 legal code |
  | `https://obofoundry.org/ontology/mondo` | 200, text/html, 30,696 B — "License CC BY 4.0" |
  | `https://mondo.monarchinitiative.org/` | 200, 16,634 B — publisher statistics page |
- **Entry count — MEASURED** from the downloaded `mondo.obo` (53,134,854 B):
  - **63,278 `[Term]` stanzas / 63,560 distinct `id:` values**
  - **36,017 of those carry a native `MONDO:` id**; the rest are imported from UBERON (5,360),
    HP (4,859), GO (4,142), NCBITaxon (2,227), CHEBI (1,269), CL (1,225)
  - 4,618 obsolete · 81,863 `is_a` · 74 `alt_id`
  - Publisher's own site states 29,315 total diseases (23,214 human, 4,737 cancer, 1,079
    infectious, 11,801 Mendelian, 16,378 rare). The `mondo-simple.owl` / `mondo-rare.owl` /
    `mondo-international.owl` releases exist if you want a disease-only subset.
- **LICENCE: CC BY 4.0**, embedded in the file as `terms:license http://creativecommons.org/licenses/by/4.0/`
  and confirmed by the repo LICENSE (fetched 200) and OBO Foundry (fetched 200).
  **MIT-compatible with attribution.** MONDO also curates precise equivalence axioms to DOID,
  OMIM, Orphanet, EFO, NCIt and ICD-11 — meaning one MONDO download gives you the crosswalk
  that would otherwise need BioPortal/UMLS.
- **API key / registration:** none.
- **SYMPTOM / PHENOTYPE annotations:** ⚠️ **No native symptom axis, but it imports HPO.** I
  measured 4,859 `HP:` terms and 14,176 `HP:` string occurrences inside mondo.obo — the HPO
  phenotype classes are present as part of the axiomatisation. ⚠️ **That means the HPO licence
  (section 8b) propagates into your MONDO-derived artefact.** If you publish only the
  `MONDO:` disease terms and their disease-to-disease hierarchy, you are fine under CC BY 4.0.
  If you publish HPO phenotype classes lifted out of MONDO, you inherit the HPO restriction.

### 8b. Human Phenotype Ontology (HPO) — the phenotype answer, and a licence trap
- **Maintainer:** HPO Consortium / Monarch Initiative, Jackson Laboratory (HPO.jax.org).
- **Verified URLs:**
  | URL | Observed |
  |---|---|
  | `https://purl.obolibrary.org/obo/hp.obo` | **200, 10,863,613 B** |
  | `https://purl.obolibrary.org/obo/hp.owl` | **200, 76,854,086 B** |
  | `https://purl.obolibrary.org/obo/hp/phenotype.hpoa` | **200, 35,816,037 B** (disease↔phenotype annotations) |
  | `https://human-phenotype-ontology.github.io/downloads.html` | 200, 10,642 B |
  | `https://obofoundry.org/ontology/hp` | 200, 33,712 B |
  | **`https://hpo.jax.org/app/license`** | **HTTP 404 — the licence URL that HPO itself publishes inside `hp.obo` is DEAD** |
  | **`https://hpo.jax.org/app/citation`** | **HTTP 404 — also dead** |
  | `https://raw.githubusercontent.com/obophenotype/human-phenotype-ontology/master/LICENSE` | **404** (and `LICENSE.txt` also 404) |
- **Entry count — MEASURED** from the downloaded `hp.obo` (10,863,613 B, version 2026-09-01):
  **20,482 `[Term]` stanzas / 20,485 distinct ids, all `HP:`**; 588 obsolete → **≈19,894 active
  HPO terms**; 24,436 `is_a`; 3,974 `alt_id`.
- **This is by far the best SYMPTOM/PHENOTYPE source in the survey:** it *is* a standardised
  vocabulary of phenotypic abnormalities and clinical features, with an "Organ: Phenotypic
  abnormality" / "Clinical modifier" / "Clinical course" / "Frequency" / "Mode of inheritance"
  facet structure, and `phenotype.hpoa` supplies disease→phenotype annotations with **frequency,
  onset and negative assertions** (35.8 MB). Measured: 49,543 `HP:` occurrences, 599 "symptom",
  119 "sign or symptom", 3,974 alt_ids.
- **LICENCE — THE BLOCKER.** HPO is **not** CC0 and **not** CC BY. `hp.obo` declares
  `terms:license https://hpo.jax.org/app/license` — a URL that now 404s — and OBO Foundry flags
  the registry licence as *"not a valid open license"*, having changed the wording in March 2026
  to *"License used is not one of the two open licenses approved by the OBO Foundry in Principle 1:
  CC0 and CC-BY"*. The licence text (preserved by HL7 THO at
  `https://terminology.hl7.org/en/NamingSystem-HPO.html`, and quoted in the OBO Foundry issue
  thread) grants free use under three conditions, the third being fatal:
  > "**Neither the content of the HPO file(s) nor the logical relationships embedded within the
  > HPO file(s) be altered in any way.** (Content additions and modifications have to be
  > suggested using our issue tracker.)"

  **Verdict: you may reproduce HPO verbatim with attribution, but you may not create and
  publish an HPO-derived dataset under MIT.** If your project's value depends on
  phenotype/symptom annotations, HPO is legally the wrong source for a public repo. Either
  (a) query HPO live at runtime and publish only *your own* disease-level conclusions, or
  (b) get written permission from the HPO consortium, or (c) substitute sources whose symptom
  coverage you can legally carry. **This is the single most consequential licensing finding in
  this survey after ICD-11.**

---

## 9. Side-by-side summary

| Source | Measured entries | Format / size | Key required | Symptom/phenotype axis | Licence | MIT-redistributable? |
|---|---|---|---|---|---|---|
| **DO** | 14,854 terms (2,519 obsolete → ~12,335 active) | OBO 7.3 MB / OWL 28.8 MB / JSON 24.2 MB | No | ❌ none (0 HP: xrefs) | **CC0 1.0** | ✅ **yes, no conditions** |
| **MONDO** | 63,278 terms; 36,017 native MONDO ids; ~29,315 diseases | OBO 53 MB / JSON 108 MB | No | ⚠️ HPO imported (licence carries) | **CC BY 4.0** | ✅ **yes, with attribution** |
| **ORDO** | 16,296 classes; DB = 11,645 disorders (~7k real diseases) | OWL 52.5 MB | No | ❌ not in ORDO; see `en_product4.xml` | **CC BY 4.0** | ✅ **yes, with attribution** |
| **Orphanet DB** | 11,645 disorders (incl. groups) | XML 54 MB | No | ⚠️ in product4, not product1 | **CC BY 4.0** | ✅ **yes, with attribution** |
| **ICD-10-CM** | 74,879 billable (+23,524 headers) | TXT in ZIP, 2.2 MB | No | ⚠️ Ch. R only, 774 codes (~1%) | US public domain (§105) | ✅ **yes (US-only status)** |
| **MeSH** | 31,110 descriptors, but only ~3.7k disease/symptom | XML 313 MB (+786 MB supp.) | No | ⚠️ C23.888 branch, 1,106 terms, no weights | US public domain (§105) | ✅ **yes (US-only status)** |
| **SNOMED CT** | 378,553 active (Jan-2026 IE); 383,345 (Jul-2026) | RF2 | **Yes** — affiliate licence/MLDS | ✅ **best** (Clinical finding, 134,779 concepts) | Affiliate Licence, no redistribution | ❌ **NO** |
| **HPO** | 20,482 terms (588 obsolete → ~19,894 active) | OBO 10.9 MB / OWL 76.9 MB / hpoa 35.8 MB | No | ✅ **the phenotype ontology** | custom, **forbids alteration** | ❌ **NO for derivatives** |
| **ICD-11** | ~17,000 categories (publisher-stated, not measured) | JSON REST / container | **Yes** — OAuth2 registration | ✅ native (signs & symptoms in Foundation) | **CC BY-ND 3.0 IGO** | ❌ **NO — NoDerivatives** |
| **UMLS** | n/a (umbrella) | MRREL/RRF | Yes — licence click-through | varies per source | §3 forbids subset redistribution | ❌ **NO** |
| **BioPortal** | n/a (aggregator) | REST | **Yes — 401 on every endpoint** | — | aggregator of the above | n/a — don't use |

---

## 10. RECOMMENDED — top 3 for a student project publishing derived data publicly under MIT

### 🥇 1. Disease Ontology (DO) — `doid.obo` / `doid.owl` / `doid.json`
**12,335 active disease classes** (14,854 terms incl. obsolete) — verified 200 at
`https://purl.obolibrary.org/obo/doid.obo` (7,264,205 B).

*Why #1:* **CC0 1.0 is the only licence here with zero obligations.** No attribution clause to
satisfy, no share-alike, no "indicate changes", no ND clause to work around. You can rename
columns, merge in your own scores, nest your triage categories, and ship the whole thing MIT
without a single legal caveat. For a student project whose #1 risk is shipping something a
grader or a maintainer flags as a licence violation, that is decisive.
Second: 7.3 MB OBO / 24 MB JSON — small enough to vendor into a repo, so your pipeline is
reproducible offline and in CI with no network at all.
Third: a genuinely curated `is_a` disease hierarchy with 1,743 `alt_id` entries for
de-duplication and rich definitions, plus xrefs to MIM/NCI/MeSH/ORDO/GARD/ICDO.
*Cost:* **no symptom/phenotype axis.** If your project needs symptom mapping you must get it
elsewhere (see #2) or from your own data. Use `alt_id` carefully or you will ship duplicate
diseases.

### 🥈 2. MONDO — `mondo.obo` (or `mondo-simple.obo` for a disease-only cut)
**63,278 terms; 36,017 native MONDO ids; ~29,315 diseases** — verified 200 at
`https://purl.obolibrary.org/obo/mondo.obo` (53,134,854 B).

*Why #2:* It is the **crosswalk hub**. Because MONDO curates OWL equivalence axioms to DOID,
OMIM, Orphanet, EFO, NCIt and ICD-11, one 53 MB file replaces BioPortal, UMLS and a pile of
manual mapping — and it does it under **CC BY 4.0**, which *explicitly permits derivatives and
redistribution*. The CC BY obligation is small and mechanical: name Monarch Initiative, link
`https://creativecommons.org/licenses/by/4.0/`, state the version, and say you made changes.
Put a `LICENSES.md` + per-file header and you are compliant.
Second: 2.5× DO's disease coverage and it subsumes DO, so migrating up later is a superset
operation rather than a merge.
*Cost:* 53 MB is chunky to vendor — consider a build step that commits only your derived CSVs
plus a pinned URL+SHA of mondo.obo rather than the OBO itself. ⚠️ **Trim carefully:** publish
only `MONDO:` disease terms and disease-to-disease edges. The 4,859 imported `HP:` terms carry
the HPO licence (§8b) — shipping those under MIT would be the mistake that sinks the project.

### 🥉 3. ICD-10-CM FY2027 — `icd10cm-code-descriptions-2027.zip`
**74,879 billable codes** (+23,524 non-billable headers) — verified 200 at
`https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Publications/ICD10CM/2027/icd10cm-code-descriptions-2027.zip`
(2,192,779 B).

*Why #3:* It is the **only large source with an unambiguous public-domain status** (17 U.S.C.
§105) that is also the *actual billing vocabulary* a healthcare-records system will need — real
codes, real short/long descriptions, real tabular hierarchy, in a 2.2 MB zip that is trivially
vendored. Every one of the 74,879 codes and titles is free of restriction, so a derived
`code → description → chapter → our_triage_class` table is unambiguously MIT-publishable.
Chapter R gives you 774 genuine symptom/sign codes, which is a real (if small) symptom foothold
that DO/MONDO/ORDO cannot give you at all.
*Cost:* ⚠️ Public domain is **territorial** — §105 has no extraterritorial effect. Say so in the
README. ⚠️ It is flat + categorised, not a deep ontology: no synonym model beyond one short and
one long description, and no symptom→disease edges. ⚠️ The CDC filename convention changed
(`icd10cm_order_YYYY.txt` → `icd10cm-order-YYYY.txt` at FY2023) and `www.cdc.gov/…/files.html`
is 403 to scripted requests, so pin the FTP path and parse by zip member name, not by
constructing a filename. Skip the plain WHO ICD-10 entirely — WHO owns that copyright.

**Honourable mention — Orphanet / ORDO (CC BY 4.0, verified 200).** 16,296 ORDO classes and an
11,645-disorder database with ready-made xrefs to MONDO, UMLS, OMIM, ICD-10, ICD-11, MeSH and
GARD. Use it if your project is about **rare** disease. Same CC BY 4.0 mechanics as MONDO, so
it slots into the same compliance pattern. But it is ~40% of MONDO's disease count, and its
phenotype data is not in ORDO at all — it is in the separate HOOM module and
`en_product4.xml`.

---

## 11. 🚫 LICENSE BLOCKERS — sources that PREVENT public redistribution of derived data

Do **not** build derived-data artifacts on any of these if the deliverable is a public
MIT-licensed GitHub repository. Each is technically free to *read or query*; each forbids the
specific act of "repackage a modified version and publish it".

| # | Source | Blocker | Exact language / evidence | Licence page (verified) |
|---|---|---|---|---|
| 1 | **WHO ICD-11** | **CC BY-**ND** 3.0 IGO — "NoDerivatives" | WHO licence PDF clause 1.2: *"WHO does not consider incorporation of the Classifications into a software product to be… Reproduce or remodel the Classifications in part or whole and distribute it under a different name or without attribution"*. §2.4: *"You shall not modify, adapt, translate, reverse-engineer… the Classifications Software."* | `https://icd.who.int/en/docs/ICD11-license.pdf` (200, PDF, 252,387 B) → `https://creativecommons.org/licenses/by-nd/3.0/igo/` (200) |
| 2 | **SNOMED CT** | Affiliate Licence — no redistribution, no modification, US-only via UMLS | Affiliate Agreement §4.1 *"the Licensee may not modify any part of the SNOMED CT Core"*; §8.1 *"Nothing in this License Agreement transfers to the Licensee any right, title or interest in or to the Intellectual Property Rights."* Via UMLS it is **Category 4**: *"prohibited from translating the vocabulary source into another language or from altering the vocabulary source content"*; distribution *"in the U.S., but only in combination with other UMLS Metathesaurus content."* | `https://www.nlm.nih.gov/research/umls/knowledge_sources/metathesaurus/release/license_agreement_snomed.html` (200, 79,899 B); `https://docs.snomed.org/snomed-ct-practical-guides/vendor-introduction-to-snomed-ct/7-licensing` (200) |
| 3 | **Human Phenotype Ontology (HPO)** | Custom licence — **forbids alteration of content or logical relationships** | *"Neither the content of the HPO file(s) nor the logical relationships embedded within the HPO file(s) be altered in any way."* OBO Foundry: *"License used is not one of the two open licenses approved by the OBO Foundry in Principle 1: CC0 and CC-BY."* ⚠️ And `https://hpo.jax.org/app/license` — the URL HPO publishes inside its own `hp.obo` — **currently 404s**. | Primary URL is **dead** (404). Preserved text: `https://obofoundry.org/ontology/hp` (200, shows the warning) and `https://terminology.hl7.org/en/NamingSystem-HPO.html` (mirrors the full licence text). OBO Foundry discussion: `https://github.com/OBOFoundry/OBOFoundry.github.io/issues/2864` |
| 4 | **UMLS Metathesaurus** (incl. its SNOMED CT copy) | §3 forbids distributing the Metathesaurus **or subsets**; Category 3 sources are internal-use only | §3: *"LICENSEE is prohibited from distributing the UMLS Metathesaurus or subsets of it, including individual vocabulary sources within the Metathesaurus…"* §12.3 expressly excludes *"incorporation of material from these copyrighted sources in any publicly accessible computer-based information system … including the Internet; publishing or translating or creating derivative works…"* | `https://uts.nlm.nih.gov/uts/assets/LicenseAgreement.pdf` (2026AA) |
| 5 | **WHO ICD-10 (international, non-US)** | WHO holds international copyright | WHO FAQ: *"WHO is the copyright holder of ICD-10, and can grant licences for the use of ICD-10 worldwide."* Corroborating WHO permission text in circulation: *"The ICD-10 codes should not be licensed under the open source licence. The copyright in ICD-10 should be clearly attributed WHO and any further redistribution of ICD-10 requires permission from WHO."* | `https://cdn.who.int/media/docs/default-source/publishing-policies/copyright/who-faq-licensing-icd-10.pdf` (200, PDF, 130,347 B) |

### Two partial / conditional cases — read the fine print

- **ICD-10-CM and MeSH are US Government works.** Public domain under 17 U.S.C. §105, so
  MIT-compatible **for US-based redistribution**. But §105 is *territorial*: the U.S. government
  itself asserts it may still hold copyright in these works **outside the U.S.**, and §105(a)
  protects "a work prepared by an officer or employee… as part of that person's official duties"
  — so third-party/vendor-contributed components could differ. Safe in practice, but state the
  jurisdiction assumption in your README rather than claiming blanket worldwide public domain.
- **MONDO imports HPO.** MONDO's own licence is clean CC BY 4.0, but 4,859 HPO terms sit inside
  `mondo.obo`. Publishing disease-to-disease MONDO content is fine; **publishing the imported
  HPO phenotype classes is not.** Filter by ID prefix before you commit anything.

### Two traps that cost me time — worth pre-empting
1. **`https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/asciimesh/d2026.bin` returns HTTP 200
   and is still garbage** — a 16,471-byte HTML `bad_url` redirect page. `asciimesh/` is an empty
   listing. Use `…/MESH_FILES/xmlmesh/desc2026.{xml,zip,gz}`. **Always inspect content-type and
   a body prefix; never trust a bare 200.**
2. **`https://id.who.int/icd/release/11` is 404** and `https://www.cdc.gov/nchs/icd/icd-10-cm/files.html`
   is **403** to scripted requests, as is `https://www.orphadata.com/data/ontologies/ordo/last_version/`
   (directory). In all three cases a sibling path works. When a URL 403s, check whether it's
   bot-filtering (retry in a browser) or a genuinely dead path (find the parent index) — the two
   need opposite responses.

---

## 12. UNVERIFIED — flagged, do not rely on without checking

- **ICD-11 entry count** (≈17,000 categories, 100k index terms, 1.6M search terms). I verified
  the PDFs that *state* this are real and downloadable, but I could not authenticate to the API
  and therefore never counted the codes myself.
- **ICD-11 Foundation size.** Never measured. Foundation is documented as much larger than the
  17,000 MMS categories, but I have no number.
- **SNOMED `Clinical finding` branch = 134,779 active concepts.** Read from an SNOMED
  release-notes page via search-engine extraction, not byte-verified by me (the page is
  JS-rendered; I successfully byte-verified only the two concept-count tables via the Confluence
  REST API).
- **Cihi's claim that ICD-11's Foundation includes a "signs and symptoms" entity category.**
  Consistent with ICD-11 documentation, but I verified it from a secondary webinar description,
  not from WHO directly.
- **"ICD-10-CM is public domain" as an explicit NLM/CDC sentence.** I verified §105 reasoning
  and HL7's statement that *"WHO has authorized the development of an adaptation of ICD-9 and
  ICD-10 to ICD-9-CM to ICD-10-CM for use in the United States for U.S. government purposes"*,
  but **I did not find a plain-English "no copyright" statement on a cdc.gov page** (the relevant
  CDC page is 403 to scripted requests). The §105 basis is sound; the explicit endorsement is
  unconfirmed. Worth one manual browser check before you rely on it in a published README.
- **`mondo.monarchinitiative.org` statistics** (29,315 diseases / 23,214 human / 4,737 cancer /
  1,079 infectious / 11,801 Mendelian / 16,378 rare). Page verified 200, but I did not scrape
  the figures out of it; my own count found 36,017 native `MONDO:` ids, which is a different
  (and larger) measure. Reconcile these two definitions before quoting a disease count.
- **Orphanet/ORDO: no registered account was required** for anything I fetched. I did not test
  whether Orphadata throttles or rate-limits heavy scripted use; be polite.