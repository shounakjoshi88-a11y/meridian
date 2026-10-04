# Research index

Everything here was verified by fetching, not by reading documentation.
Counts below are measured from the downloaded files, not quoted from a
publisher's page. Scripts that produced each claim are named.

Start with `notes/05-plan.md` for what we decided to build and why.

## Layout

```
notes/     one file per research question, written by one agent each
raw/       the actual downloaded source files
scripts/   the fetch and verification scripts
tmp/       disposable caches, gitignored
```

## Measured source files

| File | Size | What it is | Rows measured by |
|---|---|---|---|
| `raw/icd10cm_order_2027.txt` | 4.4 MB | ICD-10-CM FY2027 order file | `scripts/fetch_icd10cm.py` |
| `raw/phenotype.hpoa` | 34.2 MB | HPO disease-to-phenotype annotations | `scripts/check_raw.py` |
| `raw/hp.obo` | 10.4 MB | Human Phenotype Ontology | `scripts/check_raw.py` |
| `raw/mondo.obo` | 50.7 MB | MONDO disease ontology | `scripts/check_raw.py` |
| `raw/en_product4.xml.1` | 45.7 MB | Orphanet product 4 | agent 01 |
| `raw/MedGen_HPO_Mapping.txt.gz` | 0.4 MB | MedGen HPO mapping | agent 02 |
| `raw/world_bank_health_panel.csv` | 2.7 MB | World Bank indicator panel | agent 04 |

## Measured counts

| Source | Count | Measured by |
|---|---|---|
| ICD-10-CM FY2027 billable codes | **74,879** | `fetch_icd10cm.py` |
| ICD-10-CM Chapter R symptom/sign rows | **963** | `fetch_icd10cm.py` |
| HPOA annotation rows | **286,651** | `check_raw.py` |
| HPOA distinct diseases | **12,880** | `check_raw.py` |
| HPOA distinct HPO terms | **11,658** | `check_common_diseases.py` |
| MONDO terms | **63,278** | `check_raw.py` |
| HPO terms | **20,482** | `check_raw.py` |

## Licence decisions

Ruled **usable**:

| Source | Licence | Note |
|---|---|---|
| ICD-10-CM | US Government work, public domain | 17 USC 105. Section 105 is territorial, so it is public domain in the US; outside the US the WHO retains ICD-10 rights. Acceptable for a student repo, stated plainly. |
| Disease Ontology | CC0 1.0 | No obligations at all. |
| MONDO | CC BY 4.0 | Attribution required. Carries ICD-11 cross-references. |
| Orphanet ORDO / product4 | CC BY 4.0 | Licence embedded in the XML. |
| MeSH | Public domain | NLM. But only ~3.7k of 31,110 descriptors are diseases or symptoms. |
| Census 2011 (NADA) | Government open data | Abhinav IndicatoR, verified download. |
| ESIC Nagpur centre list | GODL-India | 46 real facilities with addresses and PIN codes. |
| Synthea sample data | Apache-2.0 / CC0 | Regenerable locally, so we prefer to regenerate. |
| UCI Diabetes 130-US Hospitals | CC BY 4.0 | |
| WHO COVID-19 daily data | CC BY 4.0 | |
| PTB-XL | CC BY 4.0 | PhysioNet open access. |

Ruled **unusable**, and why:

| Source | Blocker |
|---|---|
| WHO ICD-11 | **CC BY-ND 3.0 IGO. NoDerivatives.** We may not publish a derived dataset. The API also returns 401 without OAuth client credentials. |
| SNOMED CT | Affiliate Licence forbids modification. Category 4 in UMLS, US members only. |
| UMLS | Clause 3 forbids redistributing the Metathesaurus "or subsets of it". Requires an account, click-through, and an annual report. |
| HPO | Custom licence says neither content nor relationships may be altered. Its own `hpo.jax.org/app/license` returns **404**, so the terms could not be confirmed. Treated as unusable until proven otherwise. |
| DisGeNET | Explicitly forbids redistribution. |
| MIMIC-III / IV / eICU / SEER | Credentialed plus signed DUA. `mimiciii/1.4/patients.csv` returns 403. |

Two traps worth remembering, both found the hard way:

- `asciimesh/d2026.bin` returns **HTTP 200 with an HTML error page**. A status-only check passes it.
- `covid19.who.int/WHO-COVID-19-global-daily-data.csv` does the same. World Bank likewise returns 200 with an error object for an invalid indicator code.

So `fetch_datasets.py` must assert on content, not on status.

## The finding that changed the plan

HPOA has 12,880 diseases and 286,651 annotations, which looks ideal. It is
not usable for outpatient triage. Measured with
`scripts/check_common_diseases.py`:

| Search term | Hits | What the top hit actually is |
|---|---|---|
| cough | **0** | |
| depression | **0** | |
| COPD | **0** | |
| bronchitis | **0** | |
| anaemia | **0** | |
| influenza | 1 | Avian influenza |
| asthma | 3 | Asthma, nasal polyps, and aspirin intolerance |
| pneumonia | 7 | Lymphoid interstitial pneumonia |
| diabetes | 62 | Maturity-onset diabetes of the young, type 8 |
| hypertension | 23 | Ischiocoxopodopatellar syndrome with pulmonary... |

It is a rare-disease corpus. Its most shared terms are inheritance modes
and developmental descriptors, not things a patient reports:

| HPO term | Diseases | Term |
|---|---|---|
| HP:0000007 | 4,265 | Autosomal recessive inheritance |
| HP:0000006 | 3,569 | Autosomal dominant inheritance |
| HP:0001263 | 2,590 | Global developmental delay |

A user typing "fever and cough" would get nothing useful. Shipping it as
the triage knowledge base would make the demo worse while looking more
impressive in a README.

**Therefore the disease spine is ICD-10-CM, and triage associations are
curated and each carry a real ICD-10-CM code.** HPOA is kept, honestly
labelled, as a rare-conditions dataset.

## Reproducing

```
python research/scripts/check_raw.py
python research/scripts/check_common_diseases.py
python research/scripts/fetch_icd10cm.py
```

`fetch_icd10cm.py` downloads 2.2 MB and writes
`raw/icd10cm_order_2027.txt`. The other two read what is already there.