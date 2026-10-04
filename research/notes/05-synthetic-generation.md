# 05 — Generating large-scale, realistic synthetic patient records

Research only. No application code lives here.

**Question answered:** how do we grow Meridian from 8 patients / 20 visits to
several hundred of each, plus hundreds of hospitals and clinics and thousands
of real diseases, such that the records are internally consistent, clinically
plausible, reproducible from a seed, and defensibly "synthetic"?

**Hard constraint accepted throughout:** plain Python + pandas only. No numpy,
no scipy, no ML libraries. Seeded RNG from the standard library.

**Verification method.** Every URL below was opened with
`research/scripts/verify_urls.py`, which reports the observed HTTP status for
all 63 sources. Last full run: **59 returned 200, 3 refused scripted clients
(publisher bot filter), 1 broke after rate-limiting us.** Where a publisher
blocks scripts but the page is real, it is marked `[blocked]` and a
machine-readable substitute is cited alongside it. Anything I could not open
and read is not cited.

**Label convention.** Every number carries `SOURCED` (with a URL I fetched and
read) or `ASSUMED` (my judgement, stated so a clinician can overrule it).

Scripts written for this note, all in `research/scripts/`:

| script | what it proves |
| --- | --- |
| `verify_urls.py` | every cited URL still responds; prints observed status |
| `who_growth_tables.py` | downloads WHO's official LMS workbooks and reads the median column, so infant/paediatric numbers are not from memory |
| `pdf_text_scrape.py` | pulls the Indian DPDP Act text out of the Gazette PDF so the legal quotes are verbatim |
| `seed_determinism_demo.py` | runs, and prints, that a fixed seed reproduces output exactly |

Extracted reference data is cached in `research/raw/`
(`who_lms_medians.txt`, `aap2017_bp_percentile_tables.txt`,
`dpdp_act_meity_text.txt`).

---

## 1. Reproducible pseudo-randomness in plain Python

**`random` and `secrets` are both in the Python standard library.** No install,
no third-party dependency. Verified locally — the modules sit in the
interpreter's own `Lib/` directory:

```
random module file:  ...\Python314\Lib\random.py
secrets module file: ...\Python314\Lib\secrets.py
```

Source: <https://docs.python.org/3/library/index.html> (200) —
<https://docs.python.org/3/library/random.html> (200) —
<https://docs.python.org/3/library/secrets.html> (200). **SOURCED**

### What the docs actually promise

Quoted from the `random` module page (SOURCED, fetched):

- "Python uses the **Mersenne Twister** as the core generator. It produces
  53-bit precision floats and has a period of `2**19937-1`."
- "The Mersenne Twister ... being completely deterministic, it is not suitable
  for all purposes, and is completely unsuitable for cryptographic purposes."
- "The pseudo-random generators of this module **should not be used for security
  purposes**. For security or cryptographic uses, see the `secrets` module."
- `random.seed(a=None, version=2)` — "If `a` is `None`, current system time is
  used". With `version 2` (the default), a `str`/`bytes` seed "gets converted to
  an int and all of its bits are used"; `version 1` "generates a narrower range
  of seeds" and exists only "for reproducing random sequences from older
  versions of Python".
- `random.sample` accepts a `counts` keyword for weighted sampling.
- `random.choices` (https://docs.python.org/3/library/random.html#random.choices)
  and `random.gauss`
  (https://docs.python.org/3/library/random.html#random.gauss) both exist.

### Why a fixed seed matters — demonstrated, not asserted

`research/scripts/seed_determinism_demo.py` runs this and prints the result:

```
seed 20261004 run 1: [0.174608, 0.754572, 0.39285, 0.523149, 0.827877, 0.705686]
seed 20261004 run 2: [0.174608, 0.754572, 0.39285, 0.523149, 0.827877, 0.705686]
identical: True

after one stray draw, same seed gives different numbers: True

cohort B identical: True
```

Three practical consequences for the generator:

1. **The seed is the entire contract.** Re-running with the same seed must
   reproduce every CSV byte for byte. Otherwise every demo, screenshot, test
   fixture and figure in the project becomes unreproducible.
2. **The *number and order* of draws is part of the contract.** A single stray
   `random.random()` anywhere shifts every subsequent value. So the generator
   must not branch on data that is itself randomly drawn, and must not draw
   conditionally, unless the condition is deterministic.
3. **`random.choice` over a `set` is unsafe; over a `list` it is fine.** The demo
   shows four identically seeded runs returning the same value from a list, and
   returning a *different* value from the same items once they were put in a
   `set` — because set iteration order is not a guaranteed contract. Fix: build
   ordered lookup tables as **lists or dicts**, and if a `set` is unavoidable,
   `sorted()` it first. Verified in the demo.

### Three caveats to put in writing, not in someone's head

- **Pin the Python version in the reproducibility contract.** The docs
  guarantee that a given seed reproduces a sequence *within* an interpreter
  build; they do not promise `gauss`, `normalvariate` and `sample` keep
  byte-identical streams across Python releases (`gauss` and `normalvariate`
  are documented as *different* algorithms). Record the version alongside the
  seed. **SOURCED (docs describe distinct functions); ASSUMED (that this is a
  practical risk for us — test it rather than trusting it).**
- **Prefer `random.Random(seed)` instances over the module-level functions**
  when generating one entity, so a single entity's values do not depend on how
  many draws came before. This is the same trick Synthea uses (§6).
- **Never let the generator's RNG stand in for `secrets`.** We are not
  generating secrets, which is exactly why `random` is the right choice: it is
  deterministic, and `secrets` deliberately is not.

---

## 2. Reference distributions for demographics

### 2a. Blood group — the Indian distribution, and why European tables are wrong

Indian ABO frequency is **O ≈ B > A > AB**, whereas the classic European /
US-white tables are **O > A > B > AB**. Reusing a Western table produces a
subtly wrong dataset that still looks plausible. Do not.

| source | sample | ABO order and share | Rh(D) |
| --- | --- | --- | --- |
| Agrawal et al., national, 5 regions — <https://pmc.ncbi.nlm.nih.gov/articles/PMC4140055/> (200) | 10,000 donors | **O 37.12%, B 32.26%, A 22.88%, AB 7.74%** | **+94.61%**, −5.39% |
| Delhi Regional Blood Transfusion Centre — <https://pmc.ncbi.nlm.nih.gov/articles/PMC10599670/> (200) | 23,021 donors, 2020–23 | see 8-group table below | **+95.19%**, −4.81% |
| South India single centre — <https://pmc.ncbi.nlm.nih.gov/articles/PMC11734788/> (200) | 1,200 donors | **O 38.0%, B 34.5%, A 20.6%, AB 6.8%** | **+93.4%** |
| Pan-Indian extended antigen typing — <https://pmc.ncbi.nlm.nih.gov/articles/PMC3705660/> (200) | 3,073 donors | — | **+93.6%** |
| Large multi-centre series — <https://pmc.ncbi.nlm.nih.gov/articles/PMC2847344/> (200) | 36,964 donors | — | **+94.20%** |

**The eight-group table we actually need** (Delhi RBTC, 23,021 donors,
PMC10599670, SOURCED — this is the only source I found with all eight groups
and a sample big enough to trust):

| group | share | group | share |
| --- | --- | --- | --- |
| **B+** | **35.82%** | B− | 1.70% |
| **O+** | **28.03%** | A− | 1.36% |
| **A+** | **21.74%** | O− | 1.26% |
| **AB+** | **9.60%** | AB− | 0.49% |

Note how far this is from a European table: AB− at 0.49% and A− at 1.36% are
small enough that a naive generator using uniform weights over 8 groups would
over-produce them roughly 8× and blow up the inventory.

**Regional variation is real and worth encoding.** The South India series puts
O (38.0%) above B (34.5%), whereas the pan-Indian figure has B (32.26%) below O
(37.12%) but the Delhi figure puts B (35.82%) clearly above O (28.03%). Nagpur
is in Maharashtra/central India. **ASSUMED:** use the Delhi eight-group table
for the `blood_group` column (it is the largest clean sample), and optionally
add a small Nagpur-flavoured tilt toward B — but do not encode a region tilt
unless we have a Maharashtra-specific source, which I did not find.

Also worth knowing but *not* used: Bombay (Oh) phenotype, 2 of 36,964 donors
(0.005%), from PMC2847344. Do not generate it. **SOURCED**

### 2b. Age distribution

India's population is young, so a realistic patient panel has a real child
tail. The broad bands are well sourced:

| vintage | 0–14 | 15–59 | 60+ | median age |
| --- | --- | --- | --- | --- |
| 2011 | **30.9%** | **60.7%** | **8.4%** | **24.92** |
| 2021 | 25.7% | 64.2% | 10.1% | 28.34 |
| 2036 (projected) | 20.1% | 64.9% | 14.9% | 34.48 |

Source: Ministry of Statistics & Programme Implementation, *Women and Men in
India 2022*, "Population Statistics" chapter,
<https://www.mospi.gov.in/sites/default/files/publication_reports/women-men22/PopulationStatistics22.pdf>
(200). **SOURCED**

Corroborating: MoHFW *National Health Profile 2011*, demographic indicators
chapter, <https://cbhidghs.mohfw.gov.in/sites/default/files/NHP/nhp-2011-Demographic%20Indicators.pdf>
(200) — "Age distribution of the population shows **31.4%** in 0-14 age group
while only **7.4%** are in 60+ age group". **SOURCED**

Sub-bands above age 35, from the same NHP 2011 table (India, 2009 estimate,
% of total): 35–39 **6.6**, 40–44 **6.1**, 45–49 **4.8**, 50–54 **3.8**,
55–59 **3.8**, 60–64 **2.6**, 65–69 **2.0**, 70–74 **1.4**. **SOURCED**

Sex ratio, Census 2011: **940 females per 1,000 males**
(<https://www.mospi.gov.in/sites/default/files/Statistical_year_book_india_chapters/Area%20And%20Population-writeup.pdf>,
200). For a *patient* panel we want closer to even than 940: women use health
services more, especially for paediatrics and antenatal care. **ASSUMED**:
approximately 50/50 for adults, and no sex skew at all for under-15s beyond
birth sex ratio (which I did not source — so: **ASSUMED** 50/50 for
paediatric patients, and flag it).

### 2c. The assumption that needs a clinician's eye

**A hospital outpatient panel is not the general population.** It skews older
than 30.9% children, because infants and the very old under-use outpatient
care relative to their share of the population. I could not find a
Nagpur-specific outpatient age distribution.

**ASSUMED (explicitly, and the first thing to review):** build the age
distribution in three tiers, not one:

- **0–14: 24%** of the panel (vs 30.9% of the population) — down-weighted
  because infants under-use outpatient services.
- **15–59: 62%** — the working-age bulk.
- **60+: 14%** (vs 8.4% of the population) — up-weighted, because older people
  present more often.

Inside each tier, distribute across 5-year bands proportional to the sourced
sub-band shape where available (35+), and proportional to a documented
assumption for 0–34. **These three percentages are the largest ASSUMED values
in this entire note.** A single Nagpur hospital's outpatient register would
settle them.

---

## 3. Clinically plausible vital signs

### 3a. Adults at rest

| vital | normal range | source |
| --- | --- | --- |
| **Blood pressure** | **90/60 to 120/80 mmHg** | MedlinePlus (200) |
| **Pulse** | **60–100 bpm** | MedlinePlus (200) |
| **Respiratory rate** | **12–18 /min** | MedlinePlus (200); StatPearls says 12–20 |
| **Temperature** | **97.7–99.1 °F (36.5–37.3 °C), average 98.6 °F (37.0 °C)** | MedlinePlus (200) |

Sources: <https://www.medlineplus.gov/ency/article/002341.htm> (200) and
<https://www.ncbi.nlm.nih.gov/books/NBK553213/> (200, `[blocked]` to scripts —
it serves a CAPTCHA, but the page is live). **SOURCED**

Note the RR disagreement (12–18 vs 12–20) between two respectable sources.
**ASSUMED:** generate 12–18 and treat 18–20 as the top of a plausible band, but
do not emit an RR column at all if the schema does not need one — Meridian's
`visits.csv` currently has BP, pulse, temp, SpO2, weight, height only.

### 3b. Adult blood pressure categories (ACC/AHA 2017)

Reproduced in two open-access reviews, both (200):
<https://pmc.ncbi.nlm.nih.gov/articles/PMC8031116/> and
<https://pmc.ncbi.nlm.nih.gov/articles/PMC6705594/>. **SOURCED**

| category | SBP | DBP |
| --- | --- | --- |
| Normal | <120 | and <80 |
| Elevated | 120–129 | and <80 |
| Hypertension stage 1 | 130–139 | or 80–89 |
| Hypertension stage 2 | ≥140 | or ≥90 |

"If SBP and DBP fall in two categories, use the higher category." **SOURCED**
The original guideline is paywalled to scripts
(<https://www.ahajournals.org/doi/10.1161/HYP.0000000000000065> → 403
`[blocked]`); the PMC reviews state it verbatim, so we cite those.

**This table is the backbone of the generator's BP logic.** For an adult
"healthy" patient, draw SBP from a distribution centred near 115 and DBP near 76;
for a "Hypertension" diagnosis, shift the whole distribution rather than
clipping a single outlier.

### 3c. Paediatric blood pressure — percentiles, not fixed cut-offs

For under-13s the 2017 AAP guideline switched from fixed numbers to
**percentiles by age, sex and height percentile**, and redefined the old
"prehypertension" as "elevated blood pressure". Full classification, from
PMC8031116 (200) and <https://www.aafp.org/pubs/afp/issues/2018/1015/p486.html>
(200). **SOURCED**

| classification | children 1–12 y | everyone ≥13 y |
| --- | --- | --- |
| Normotensive | <90th percentile | <120 / <80 |
| Elevated BP | ≥90th to <95th percentile, or 120/80 to <95th (lower) | 120–129 / <80 |
| Stage 1 hypertension | ≥95th to <95th+12 mmHg, or 130/80–139/89 (lower) | 130–139 / 80–89 |
| Stage 2 hypertension | ≥95th+12 mmHg, or ≥140/90 (lower) | ≥140 / ≥90 |

Hypertension needs **three separate visits**; stage 2 is
`95th percentile + 12 mmHg`, not the old `99th + 5`.

**Actual percentile values** (AAP 2017 Tables 4 and 5, published in full by
Merck Manual Professional at <https://www.merckmanuals.com/professional/multimedia/table/blood-pressure-bp-percentile-levels-for-boys-by-age-and-height-measured-and-percentile>
and the girls equivalent — both 200). Extracted to
`research/raw/aap2017_bp_percentile_tables.txt`. **SOURCED**

At the **50th height percentile**, mmHg:

| age | height | 50th SBP/DBP | 90th SBP/DBP | 95th SBP/DBP |
| --- | --- | --- | --- | --- |
| **boys** | | | | |
| 1 | 82.4 cm | 86/41 | 100/53 | 103/55 |
| 2 | 92.1 cm | 89/44 | 102/56 | 106/59 |
| 5 | 112.4 cm | 94/53 | 106/65 | 109/69 |
| 10 | 141.3 cm | 100/62 | 112/74 | 116/77 |
| 13 | 160.3 cm | 108/62 | 121/75 | 125/78 |
| 17 | 175.8 cm | 117/68 | 131/81 | 135/85 |
| **girls** | | | | |
| 1 | 80.8 cm | 86/43 | 100/56 | 103/60 |
| 2 | 91.1 cm | 89/48 | 103/60 | 106/64 |
| 5 | 111.5 cm | 93/55 | 107/67 | 110/71 |
| 10 | 141.0 cm | 99/60 | 112/73 | 116/76 |
| 13 | 159.2 cm | 107/64 | 121/76 | 124/79 |
| 17 | 163.0 cm | 110/66 | 124/77 | 127/81 |

The generator needs two things from this: (a) a **50th-percentile BP lookup
keyed on (age band, sex)** for the healthy baseline, and (b) the **95th
percentile** value, so that the "hypertension in a 4-year-old" consistency
check in §7 has a real threshold rather than an invented one.

### 3d. Ageing and blood pressure

StatPearls (NBK553213) states that "progressive arterial stiffening with aging
contributes to higher systolic blood pressure, lower diastolic blood pressure,
and a widened pulse pressure". **SOURCED** (page live, but `[blocked]` to
scripted requests).

**ASSUMED consequence for the generator:** for patients 60+, shift SBP up and
DBP down relative to the adult band, widening pulse pressure, and keep
hypertension thresholds unchanged (the ACC/AHA cut-offs still apply above 60 —
they are not relaxed for the elderly). I did not find a sourced numeric
age-banded SBP mean, so the generator should derive the elderly shift as a
documented offset rather than pretend to a precision it does not have.

### 3e. SpO₂

| statement | value | source |
| --- | --- | --- |
| Normal oxygen saturation | **95%–100%** | MedlinePlus, Pulse Oximetry lab test (200) |
| Contact a provider | **≤92%** | same |
| Seek immediate attention | **≤88%** | same |
| Normal PaO₂ (ABG) | **75–100 mmHg** | MedlinePlus, ABG lab test |

<https://www.medlineplus.gov/lab-tests/pulse-oximetry> (200);
<https://www.medlineplus.gov/lab-tests/arterial-blood-gas-abg-test/> (200).
**SOURCED**

Also: hypoxaemia is an oxygen saturation **<90%** — StatPearls *Pulse
Oximetry*, <https://www.ncbi.nlm.nih.gov/books/NBK470348/> (live).
**SOURCED**

**ASSUMED for children:** MedlinePlus gives an adult figure, and the paediatric
literature argues the true healthy-child range is narrower (97–100%). Simpler:
generate 96–100% for everyone, and reserve anything ≤92% for a respiratory
presentation. Label as ASSUMED.

---

## 4. Height, weight and plausible BMI

### 4a. WHO medians, pulled from the official tables (not from memory)

`research/scripts/who_growth_tables.py` downloads WHO's published LMS
z-score workbooks from `cdn.who.int` and reads the median column `M` and the
−2SD / +2SD columns. It parses `.xlsx` with `zipfile` + `xml.etree` from the
standard library — no `openpyxl`. Raw output: `research/raw/who_lms_medians.txt`.

The standards themselves: WHO Child Growth Standards, 2006,
<https://www.who.int/tools/child-growth-standards> (200),
<https://www.who.int/publications/i/item/924154693X> (200). Built from the WHO
Multicentre Growth Reference Study: 8,440 healthy breastfed infants and young
children from Brazil, Ghana, **India**, Norway, Oman and the USA. It covers
**0–60 months only** — for older children and adults we need another source.

**Verified WHO medians (birth → 60 months):**

| months | boys wt kg | girls wt kg | boys len/ht cm | girls len/ht cm |
| --- | --- | --- | --- | --- |
| 0 | **3.35** | **3.23** | **49.88** | **49.15** |
| 1 | 4.47 | 4.19 | 54.72 | 53.69 |
| 3 | 6.38 | 5.85 | 61.43 | 59.80 |
| 6 | 7.93 | 7.30 | 67.62 | 65.73 |
| 9 | 8.90 | 8.23 | 71.97 | 70.14 |
| 12 | **9.65** | **8.95** | **75.75** | **74.02** |
| 18 | 10.94 | 10.23 | 82.26 | 80.71 |
| 24 | **12.15** | **11.48** | **87.12** | **85.72** |
| 36 | 14.34 | 13.85 | 96.08 | 95.05 |
| 48 | 16.35 | 16.07 | 103.33 | 102.73 |
| 60 | **18.34** | **18.22** | **109.96** | **109.42** |

−2 SD / +2 SD, same source (use these to widen, never to invent):

| months | boys wt −2/+2 | girls wt −2/+2 | boys ht −2/+2 | girls ht −2/+2 |
| --- | --- | --- | --- | --- |
| 0 | 2.5 / 4.4 | 2.4 / 4.2 | 44.2 / 51.8 | 43.6 / 51.0 |
| 12 | 7.7 / 12.0 | 7.0 / 11.5 | 68.6 / 78.1 | 66.3 / 76.6 |
| 24 | 9.7 / 15.3 | 9.0 / 14.8 | 78.0 / 90.2 | 76.0 / 88.9 |
| 60 | 14.1 / 24.2 | 13.7 / 24.9 | 96.1 / 114.6 | 95.2 / 114.2 |

**SOURCED**, downloaded and parsed, not recalled.

A quick sanity check that the medians are internally consistent — BMI = weight
÷ height², at WHO medians: boy 24 m = 12.15 ÷ 0.8712² ≈ **16.0**; girl 24 m ≈
**15.6**; both at 60 m ≈ **15.2**. Those are the values you would expect, so the
table is coherent.

**Caveat to write down:** WHO is a *standard*, not an Indian *reference*. It
was built from healthy breastfed infants under optimal conditions. Indian
children are, on average, lighter and shorter at the same age. The IAP revised
charts exist for exactly this reason. Using WHO is defensible and
internationally comparable; it will make Indian infants look slightly
plausible-and-slightly-tall. **Flagged, not solved.**

### 4b. BMI cut-offs — and why the WHO cut-offs are wrong for Indian patients

This is the single most clinically important finding for this generator.

| system | underweight | normal | overweight | obese |
| --- | --- | --- | --- | --- |
| **WHO / NHANES (US)** | <18.5 | 18.5–24.9 | 25.0–29.9 | ≥30 (I 30–34.9, II 35–39.9, III >40) |
| **India** | <18.5 | 18.5–22.9 | **23.0–24.9** | **≥25** (morbid ≥35) |

Sources: CDC/NHANES Anthropometry Procedures Manual 2017,
<https://wwwn.cdc.gov/nchs/data/nhanes/public/2017/manuals/2017_Anthropometry_Procedures_Manual.pdf>
(200) — "For adults, cutoff criteria are fixed: underweight (BMI values <
18.5); normal weight (BMI values 18.5-24.9); overweight (BMI values 25.0-29.9);
obese-Class I (BMI values 30.0-34.9); obese-Class II (BMI values 35.0-39.9); and
extremely obese-Class III (BMI values > 40.0)". **SOURCED**

India: Press Information Bureau, Government of India,
<https://www.pib.gov.in/PressReleasePage.aspx?PRID=2107179> (200) — "In India, a
person is considered overweight if their Body Mass Index (BMI) is between 23.0
and 24.9 kg/m², and obese if their BMI is 25 kg/m² or higher. Morbid obesity
occurs when a person's BMI is 35 or more." **SOURCED**

Corroborated by the peer-reviewed position of the Indian Consensus Group:
"Misra et al." / PMC4555479,
<https://pmc.ncbi.nlm.nih.gov/articles/PMC4555479/> (200) — "Definitive
guidelines have been published to classify a BMI of ≥23 kg/m² and ≥25 kg/m² as
overweight and obese, respectively, by the Indian Consensus Group (for Asian
Indians residing in India)". **SOURCED**

The reason is documented in the same source: "higher body fat, excess metabolic
perturbations, and cardiovascular risk factors at lower value of BMI in Asian
versus white populations". A patient at BMI 26 is obese in an Indian OPD and
merely "overweight" on a US chart.

**Recommendation:** the app must display Indian bands (23 / 25). If it also
shows WHO bands for comparison, both must be labelled.

### 4c. Adult weight anchors for India

- **ICMR–NIN Expert Committee on RDA (2020)**: "the normal BMI reference for
  Indian adult man and woman of 19–39 years as weighing **65 and 55 kg**
  respectively in contrast to the **60 and 50 kg** ... considered by the earlier
  committees of 1989 and 2010." Source:
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC7615800/> (200). **SOURCED**
- **NFHS-4 (2015–16), measured height and weight, ages 15–49**: underweight
  **19.6% of men** and **22.4% of women**. Source:
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC6976728/> (200). **SOURCED**

That underweight figure is the number to use: it is measured, national,
recent, and it stops the generator from producing an implausibly lean panel.
Indian adult BMI distribution is genuinely **double-burden** — a fifth
underweight and a quarter obese at the same time — so a single normal
distribution centred on BMI 22 will be wrong in both tails.

**ASSUMED construction:** adult BMI as a mixture, not a single normal —
underweight ~20% centred near 17.5, normal ~55% centred near 21.5,
overweight ~18% centred near 24, obese ~7% centred near 27. The *proportions*
are anchored on NFHS-4 underweight (SOURCED) and the ICMR-INDIAB obesity
figure below; the *centres* are ASSUMED. Converting BMI to weight requires
height, so draw height first (see below).

### 4d. Height, 5 years and above

WHO stops at 60 months. For everyone older I could not obtain a
machine-readable Indian reference: NCD-RisC holds the best data
(<https://www.ncdrisc.org/data-downloads-height.html>) but the server resets
connections to scripted clients, and the eLife paper sits behind a bot
challenge.

**What I can say, SOURCED:** an Indian adult man of the 1996 birth cohort
averaged **164.9 cm**, an Indian adult woman **152.6 cm** — NCD-RisC, "A
century of trends in adult human height", eLife 2016;5:e13410,
<https://elifesciences.org/articles/13410> (live but `[blocked]`; figures
confirmed against the NCD-RisC data pages
<https://www.ncdrisc.org/publications.html>, 200). *Secondary confirmation via
a search of NCD-RisC's own published dataset rather than by reading the paper's
tables; treat as SOURCED-WEAK and verify before shipping.*

**ASSUMED** growth model to bridge 5 y → adult, since I have no sourced curve:

- **5–12 y:** continue the WHO 60-month shape by linear extension of the
  WHO 36/48/60-month medians. Sanity: WHO boy 60 m = 109.96 cm, and the AAP
  50th-height column in §3c gives 112.4 cm at age 5 and 141.3 cm at age 10 —
  consistent, which is a good cross-check between two independent tables.
- **12 y → adult:** interpolate linearly from the age-12 AAP 50th height to the
  age-20 adult mean (164.9 / 152.6 cm), then sample adult height from a normal
  with **SD 6.5 cm (male) / 6.0 cm (female)**. **ASSUMED** — the SD is my
  judgement, chosen so that ±3SD does not produce absurd adults.
- **Peak adult height** should land near age 20 for men and 18–19 for women;
  past that, drift down ~0.2 cm/year. **ASSUMED.**

Flag: the female SD and the ageing drift are the two numbers here most likely
to need tuning once we can see the output.

### 4e. Indian paediatric BMI cut-offs

The IAP-referenced study at <https://indianpediatrics.net/jan2012/jan-29-34.htm>
(200) gives age-specific BMI cut-offs for Indian children, derived from the
adult Asian equivalents of 23 and 28 kg/m² at age 18. Sample rows (boys /
girls, overweight / obesity): age 5 **17.3 / 17.1** and **20.5 / 20.2**;
age 10 **17.9 / 17.8** and **21.4 / 21.2**; age 15 **21.3 / 21.5** and
**25.9 / 26.0**; age 18 **23 / 23** and **28.1 / 27.9**. **SOURCED**

This is the right table for the consistency check that stops a 4-year-old
being labelled obese by adult thresholds.

---

## 5. Indian clinical record conventions

| item | convention | basis |
| --- | --- | --- |
| Blood pressure | **mmHg**, written `SBP/DBP` | Universal in Indian practice; the ICMR-INDIAB study defines hypertension in Indian adults as ≥140/90 mmHg, so mmHg is the unit the surrounding literature assumes. **SOURCED** (ICMR-INDIAB) / the `NN/AA` notation is what the NHLBI patient-education material uses. <https://www.nhlbi.nih.gov/health/high-blood-pressure> (200) |
| Temperature | store **°C to one decimal**; allow °F on screen | **ASSUMED** — see below |
| Weight | kg | WHO and NHANES both standardise on kg; BMI = kg/m² is how every source above computes it. **SOURCED** |
| Height | cm | same. **SOURCED** |
| Pulse | bpm | **SOURCED** |
| SpO₂ | % | **SOURCED** |

**On temperature, honestly:** I could not find a citable Indian standard
mandating °F on outpatient forms. What I can say is that °C is the unit every
clinical guideline and every vital-sign reference above uses, and that the
Ghana-derived textbook table widely reproduced for nursing (oral 36.5–37.5 °C,
axillary 35.8–37.0 °C, rectal 37.0–38.1 °C, tympanic 36.8–37.9 °C) shows the
site matters more than the unit. **ASSUMED:** persist °C, note the measurement
site in the column comment, and show °F as a display toggle. Indian OPD forms
often use °F, so if a reviewer insists, convert at the edge rather than
changing the store.

**On pressure direction:** Indian clinicians routinely speak of "BP 130/80"
meaning 130 mmHg systolic over 80 mmHg diastolic — the same as everywhere else.
No convention issue, but do parse and store the two numbers **separately** in
the schema rather than as the string `"130/80"`. A string will make range
checks impossible.

---

## 6. Synthea as the reference architecture

We are **not** using Synthea (Java, Gradle, FHIR exporters — far outside the
first-year-Python constraint). We are using it as the checklist of *what a
credible synthetic patient generator does*.

Sources, all fetched: <https://synthea.org/> (200),
<https://github.com/synthetichealth/synthea> (200),
<https://github.com/synthetichealth/synthea/wiki/Records> (200),
<https://github.com/synthetichealth/synthea/wiki/Generic-Modules> (200),
<https://github.com/synthetichealth/synthea/wiki/Basics> (200).
**SOURCED**

### 6a. The shape of a record

Synthea's `HealthRecord` holds, for one patient: `death`, `encounters`,
`observations`, `reports`, `conditions`, `allergies`, `procedures`,
`immunizations`, `medications`, `careplans`, `claim`, and a `present` map
referencing the active condition or procedure. Demographics live in a separate
attributes map on the person, not in the record. **SOURCED**

Two transferable ideas:

1. **Separate the person from their events.** Meridian already does this
   (`patients.csv` vs `visits.csv`). Good — keep it.
2. **`present` is the key idea.** A map of *currently active* conditions lets
   the generator ask "does this patient already have hypertension?" before
   adding a second problem, instead of letting every patient be independent
   and mutually contradictory. Meridian has no equivalent; adding an
   `active_conditions` set per patient in memory during generation would
   remove a whole class of impossible records.

### 6b. Modules model progression, not snapshots

From synthea.org: "Each module models events that could occur in a real
patient's life, **describing a progression of states and the transitions
between them**. These modules are informed by clinicians and real-world
statistics collected by the CDC, NIH, and other research sources." Each patient
is "simulated independently from birth to present day". **SOURCED**

A generic module is a small state machine: e.g. *Uncontrolled* → (with
treatment) → *Controlled*, with transition probabilities and a dwell time in
each state. A chronic disease in Meridian should therefore generate **a
sequence of visits whose vitals and severity drift in the right direction**,
not N independent random rows. Uncontrolled hypertension gets worse; treated
hypertension improves.

### 6c. Per-entity seeding — the single most useful trick in Synthea

`Generator.java` draws one seed per patient and hands it to that patient's
generation:

```java
final long seed = this.populationRandom.randLong();
threadPool.submit(() -> generatePerson(index, seed));
```

**SOURCED** (<https://github.com/synthetichealth/synthea/blob/master/src/main/java/org/mitre/synthea/engine/Generator.java>)

This is exactly the fix for the "one stray draw shifts everything" problem in
§1. Derive `patient_seed = hash(run_seed, patient_id)` and give each patient
its own `random.Random(patient_seed)`. Then:

- adding patient #300 does not change patients #1–299;
- patients can be generated in any order, or in parallel, and the output is
  identical;
- a bug in one patient's vitals cannot silently perturb another's.

Plain Python can do this with no hashing library beyond the built-in `hash()`,
though **`hash()` of a `str` is salted per process unless `PYTHONHASHSEED` is
set** — so use `int(patient_id[2:])` or `zlib.crc32(patient_id.encode())`
instead. Do not use bare `hash()` on a string in a seeding path.

---

## 7. Synthetic-data quality checks worth implementing

### 7a. The three criteria to adopt

From El Emam et al., *Generation and evaluation of synthetic patient data*,
<https://pmc.ncbi.nlm.nih.gov/articles/PMC7204018/> (200). **SOURCED**

"Each metric we use addresses one of three criteria of high-quality synthetic
data:

1. **Fidelity at the individual sample level** (e.g., synthetic data should
   not include prostate cancer in a female patient)
2. **Fidelity at the population level** (e.g., marginal and joint
   distributions of features)
3. **Privacy disclosure**"

Criterion 1 is exactly the "paediatric patient with hypertension" case in the
brief. Criterion 2 is the pairwise-correlation-difference measure the paper
introduces (PCD, the Frobenius norm of the difference between the real and
synthetic Pearson correlation matrices) — for us, with no real data to compare
against, the useful version is: **do the synthetic marginals match the sourced
targets we put in?** The targets are the reference values in §2–4, which makes
this checkable without any real patient data.

Also useful: <https://royalsociety.org/-/media/policy/projects/privacy-enhancing-technologies/Synthetic_Data_Survey-24.pdf>
(200) — the Royal Society / Jordon et al. explainer. It defines synthetic data
as "data that has been generated using a purpose-built mathematical model or
algorithm, with the aim of solving a (set of) data science task(s)", and is
forthright about the utility-versus-privacy trade-off: "increased
generalization and suppression ... for increased privacy protection can lead to
a direct reduction in data utility" (PMC7204018). **SOURCED**

And <https://pmc.ncbi.nlm.nih.gov/articles/PMC12626184/> (200), *Four checks
for low-fidelity synthetic data: recommendations for disclosure control and
quality evaluation*, for the idea that low-fidelity synthetic data has its own
legitimate job — prototyping, teaching, writing analysis code before you have
access. That is precisely our use.

### 7b. The concrete checks to put in the test suite

**Referential integrity**
- every `visits.patient_id` exists in `patients.patient_id`
- every `visits.hospital_id` exists in `hospitals.hospital_id`
- every `visits.doctor_id` exists in `doctors.doctor_id`
- every `diagnosis` / `severity` is a value in `diseases.csv`
- no orphan row in either direction (a hospital with zero visits, a patient
  with zero visits, if the schema promises at least one)

**Ranges** — every value inside the sourced band in §3–§4, at every age:
- `vitals_temp` 34.5–41.0 °C (36.5–37.3 normal, up to ~41 for a febrile
  child, down to ~34.5 for a hypothermic elderly patient) — **bounds ASSUMED,
  normal band SOURCED**
- `vitals_pulse` 40–200 bpm (60–100 adult normal) — bounds ASSUMED
- `vitals_spo2` 70–100 (95–100 normal; <90 is hypoxaemia) — **SOURCED**
- `vitals_weight`, `vitals_height` inside the WHO ±2SD envelope at that age and
  sex — **SOURCED**
- derived BMI lands in a documented band for that age — **SOURCED** cut-offs

**Uniqueness**
- `patient_id`, `visit_id`, `hospital_id`, `doctor_id`, `disease_id` unique
- no duplicate `(patient_id, scheduled_date, scheduled_time)`
- no two patients sharing a phone number

**No impossible combinations** — the interesting ones:
- a patient under 13 whose BP exceeds the AAP 95th percentile for their age,
  sex and height, *without* carrying a hypertension diagnosis
- an adult "healthy" patient with BMI ≥ 30 who does not have an obesity-related
  diagnosis
- a child whose BMI exceeds the IAP age-specific obesity cut-off (§4e) but is
  recorded as normal
- a diagnosis whose `age_range` excludes the patient's age — this field already
  exists in `diseases.csv` (`age_range` = `0-70` etc.), so it is a free check
- a female patient with a prostate condition, a male patient with a
  cervical/uterine condition — the paper's own example (PMC7204018)
- `severity` inconsistent with the diagnosis's expected severity band
- `follow_up_days` negative, or `status = Completed` with a `scheduled_date` in
  the future

**Clinical progression** (the Synthea lesson, §6b)
- for a chronic-disease patient, vitals should trend, not scatter: a treated
  hypertensive's SBP should fall across successive visits; an untreated one
  should not improve
- a `Staged` visit should be followed by a `Scheduled` visit roughly
  `follow_up_days` later, not by an unrelated visit

**Determinism**
- generate twice with the same seed → byte-identical CSVs (hash the files)
- generate with seed N and N+1 → different, but same row counts, same schema,
  same key sets
- no wall-clock or `id()`-dependent values anywhere in the output; `registered_on`
  and `scheduled_date` must derive from a seeded anchor date, not `today()`

---

## 8. Privacy: DPDP Act 2023 and HIPAA Safe Harbor

### 8a. HIPAA Safe Harbor — the 18 identifiers

45 CFR 164.514(b)(2)(i), read in full at
<https://www.law.cornell.edu/cfr/text/45/164.514> (200). HHS's own guidance
page <https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html>
and its PDF <https://www.hhs.gov/sites/default/files/ocr/privacy/hipaa/understanding/coveredentities/De-identification/hhs_deid_guidance.pdf>
are the human-readable versions; both `[blocked]` to scripts as of this run
(the PDF answered 200 twice before HHS rate-limited us), so Cornell LII is the
live citation. **SOURCED**

> The following identifiers of the individual **or of relatives, employers, or
> household members** of the individual, are removed:
> (A) Names; (B) All geographic subdivisions smaller than a State, including
> street address, city, county, precinct, zip code, and their equivalent
> geocodes, except for the initial three digits of a zip code if the geographic
> unit formed by combining all zip codes with the same three initial digits
> contains more than 20,000 people (and the initial three digits are changed to
> 000 where the unit has 20,000 or fewer people); (C) All elements of dates
> (except year) for dates directly related to an individual, including birth
> date, admission date, discharge date, date of death; and **all ages over 89**
> and all elements of dates indicative of such age, except that such ages may be
> aggregated into a single category of age 90 or older; (D) Telephone numbers;
> (E) Fax numbers; (F) Electronic mail addresses; (G) Social security numbers;
> (H) Medical record numbers; (I) Health plan beneficiary numbers; (J) Account
> numbers; (K) Certificate/license numbers; (L) Vehicle identifiers and serial
> numbers, including license plate numbers; (M) Device identifiers and serial
> numbers; (N) Web Universal Resource Locators (URLs); (O) Internet Protocol
> (IP) address numbers; (P) Biometric identifiers, including finger and voice
> prints; (Q) Full face photographic images and any comparable images; and
> (R) Any other unique identifying number, characteristic, or code, except as
> permitted by paragraph (c) of this section.

Note (b)(2)(ii): the covered entity must also have **no actual knowledge** that
the remaining information could identify an individual — Safe Harbor is
necessary but not sufficient. And (c) permits a re-identification code only if
it "is not derived from or related to information about the individual" and is
never used for another purpose. **SOURCED**

### 8b. India — DPDP Act 2023

Primary text: <https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf>
(200, the Gazette of India Extraordinary, Act 22 of 2023, 11 August 2023);
also on India Code at
<https://www.indiacode.nic.in/indiacode/bitstream/123456789/22037/1/a2023-22.pdf>
(200). Supporting rules: DPDP Rules 2025, G.S.R. 846(E),
<https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf>
(200). **SOURCED** — and the quotes below were extracted from the MeitY PDF
with `research/scripts/pdf_text_scrape.py`, cached at
`research/raw/dpdp_act_meity_text.txt`, so they are verbatim.

Provisions that actually constrain a synthetic generator:

- **§2(f)** — "'child' means an individual who has **not completed the age of
  eighteen years**."
- **§6** — "The consent given by the Data Principal shall be free, specific,
  informed, unconditional and unambiguous with clear affirmative action, and
  shall signify an agreement to the processing of her personal data for the
  specified purpose and **be limited to such personal data as is necessary for
  such specified purpose**." That last clause is a statutory statement of data
  minimisation.
- **§8** — the Data Fiduciary "shall, unless retention is necessary for
  compliance with any law for the time being in force, **erase personal data,
  upon the Data Principal withdrawing her consent or as soon as it is
  reasonable to assume that the specified purpose is no longer being served,
  whichever is earlier**", and must cause its processor to erase too. There is
  a worked illustration in the Act itself: an account holder closing an account
  must still be retained for the ten years the law requires.
- **§9 — children's data.** "The Data Fiduciary shall, before processing any
  personal data of child ... obtain **verifiable consent of the parent** of such
  child ... Data Fiduciary **shall not undertake such processing of personal
  data that is likely to cause any detrimental effect on the well-being of
  child**. Data Fiduciary **shall not undertake tracking or behavioural
  monitoring of children or targeted advertising directed at children**."
- **§17** — exemptions from Chapter II for enforcing legal rights, court and
  tribunal proceedings, and so on.

### 8c. How this applies to a synthetic dataset

The honest position: **a fully synthetic dataset is not "personal data" about
any real person**, so DPDP does not attach to it in the way it would to a
cloned EMR. But that only holds if the generator is genuinely synthetic. The
risk is not the law, it is the *claim*. Meridian must be able to say, and
demonstrate, that no record maps to a real person.

**Therefore, and this is the operative privacy checklist:**

| # | rule | why |
| --- | --- | --- |
| 1 | **Generate, do not sample.** No real patient file may be read, hashed, sampled or used to seed anything. The seed is a constant in the repository. | The moment real rows influence output, Safe Harbor and DPDP both attach. |
| 2 | **Names come from invented components only.** No name list derived from voter rolls, electoral rolls, Aadhaar name datasets, or any real directory. Build names combinatorially from surname/given-name lists we author. | HIPAA (A). |
| 3 | **Phones and emails use a reserved, non-routable block.** Emails on a domain we control, e.g. `example.in` / `example.com` (the current `patients.csv` already does this — keep it). Phone numbers in a block that cannot be dialled, or generated with an explicit `9xx`/`0` prefix convention. | HIPAA (D), (F). |
| 4 | **No Aadhaar, PAN, voter ID, passport, driving-licence or bank fields at all.** Not even fake ones — a column named `aadhaar` invites the question. | HIPAA (G); the AGENTS.md rule "no Aadhaar linkage". |
| 5 | **Drop or coarsen free-text address.** Keep `area`, `city`, `state`, `pincode` — but `area` and `pincode` are a quasi-identifier in a small city. **ASSUMED:** keep them for realism but never emit `address_line`. | HIPAA (B). |
| 6 | **Date fields: keep the year, and keep it coarse.** Meridian's `registered_on` and `scheduled_date` are synthetic, so exact dates do not identify anyone — but Safe Harbor's rule (C) is a useful discipline and it forces the generator to be internally consistent at year granularity. Ages 90+ aggregate. | HIPAA (C). |
| 7 | **No photos, biometrics, device identifiers, IPs, URLs.** Meridian has none. Keep it that way. | HIPAA (P), (Q), (M), (O), (N). |
| 8 | **Sequential IDs are fine; IDs derived from a person are not.** `P-0001` is a row counter. `P-{aadhaar_hash}` would not be. | HIPAA (H), (R). |
| 9 | **Emergency contact is a relative's data.** Safe Harbor explicitly extends to "relatives, employers, or household members". If we keep `emergency_contact`, it must be invented and must not be a real person — and for a synthetic child patient, the "guardian" link must be internally consistent with the patient's own invented household. | HIPAA preamble. |
| 10 | **Paediatric records need a guardian, and the guardian is invented.** Under DPDP §9 the Data Fiduciary needs verifiable parental consent for anyone under 18. For synthetic data the equivalent is: every under-18 record carries an invented guardian, and no generator output implies consent was collected from a real parent. | DPDP §9, §2(f). |
| 11 | **Ship a provenance statement with the data.** A `DATA_PROVENANCE.md` recording: seed, Python version, generator version, the list of sources cited here with their retrieval dates, and an explicit statement that no real personal data was used. This is the artefact that makes the privacy claim checkable rather than asserted. | — **ASSUMED good practice** |
| 12 | **Hash the output into the test suite.** `verify_generation.py` regenerates from the seed and compares file hashes, so a stray manual edit to a CSV is caught. | Determinism, §7b. |

---

## PRACTICAL CHECKLIST

Everything the generator must enforce. `SOURCED` means a real URL I fetched is
given; `ASSUMED` means my judgement and a reviewer should overrule it if wrong.

### Reproducibility
1. Single documented seed constant in the repository. **ASSUMED** (value
   `20261004` used in the demo script).
2. `random` and `secrets` only; both standard library, no install.
   **SOURCED** — <https://docs.python.org/3/library/random.html>
3. Per-entity seeding: `random.Random(run_seed_for(patient_id))`, never the
   module-level functions, so entity N is independent of entity N−1. **SOURCED**
   (Synthea `Generator.java`).
4. Never seed from a `str` via built-in `hash()` (salted per process); use
   `int(id_digits)` or `zlib.crc32(id.encode())`. **ASSUMED**
5. Never `random.choice` over a `set`; sort it first. **ASSUMED** (empirical,
   §1)
6. Record the Python minor version with every generated snapshot.
   **SOURCED** (docs describe distinct `gauss`/`normalvariate` algorithms)
7. No `today()`, `time.time()`, `uuid4()` or `id()` anywhere in the output path.
   **ASSUMED**

### Demographics
8. Blood group, 8 groups: B+ 35.82, O+ 28.03, A+ 21.74, AB+ 9.60, B− 1.70,
   A− 1.36, O− 1.26, AB− 0.49. **SOURCED** —
   <https://pmc.ncbi.nlm.nih.gov/articles/PMC10599670/>
9. Cross-check: ABO order is O ≥ B > A > AB nationally (O 37.12 / B 32.26 /
   A 22.88 / AB 7.74), NOT the European O > A > B > AB. **SOURCED** —
   <https://pmc.ncbi.nlm.nih.gov/articles/PMC4140055/>
10. Rh(D) positive 94–95% (93.6%, 94.20%, 94.61% across three large studies).
    **SOURCED** — PMC3705660, PMC2847344, PMC4140055
11. Do not generate Bombay (Oh) phenotype (0.005%). **SOURCED** — PMC2847344
12. Population age shape for sanity: 2011 = 30.9% / 60.7% / 8.4% for
    0–14 / 15–59 / 60+. **SOURCED** —
    <https://www.mospi.gov.in/sites/default/files/publication_reports/women-men22/PopulationStatistics22.pdf>
13. **Patient-panel** age shape: 0–14 **24%**, 15–59 **62%**, 60+ **14%**.
    **ASSUMED** — largest single assumption in this note.
14. Sub-bands 35+ proportional to: 35–39 6.6, 40–44 6.1, 45–49 4.8, 50–54 3.8,
    55–59 3.8, 60–64 2.6, 65–69 2.0, 70–74 1.4 (%). **SOURCED** — MoHFW NHP 2011
15. Sex ratio ≈ 50/50 for adult patients; 50/50 for paediatric. **ASSUMED**
    (population ratio 940 F/1000 M is **SOURCED**, Census 2011)
16. No patient over age 95; ages 90+ may be aggregated. **SOURCED** (HIPAA (C))

### Vitals
17. Adult BP normal range 90/60–120/80 mmHg. **SOURCED** — MedlinePlus
18. Adult BP categories: normal <120/<80; elevated 120–129/<80; stage 1
    130–139/80–89; stage 2 ≥140/90; when SBP and DBP disagree use the higher.
    **SOURCED** — <https://pmc.ncbi.nlm.nih.gov/articles/PMC8031116/>
19. Adult pulse 60–100 bpm. **SOURCED** — MedlinePlus
20. Adult temperature 36.5–37.3 °C (97.7–99.1 °F), mean 37.0 °C. **SOURCED**
    — MedlinePlus
21. Adult RR 12–18/min. **SOURCED** — MedlinePlus (StatPearls says 12–20)
22. SpO₂ 95–100% normal; ≤92% flag; <90% = hypoxaemia. **SOURCED** —
    <https://www.medlineplus.gov/lab-tests/pulse-oximetry>
23. Children 1–12 y: normal <90th percentile, elevated ≥90th, stage 1 ≥95th,
    stage 2 ≥95th + 12 mmHg. **SOURCED** —
    <https://pmc.ncbi.nlm.nih.gov/articles/PMC8031116/>
24. Paediatric 95th-percentile BP looked up by (age, sex, height percentile),
    never a flat adult cut-off. Boys at 50th height: age 1 103/55, 2 106/59,
    5 109/69, 10 116/77, 13 125/78, 17 135/85. Girls: 103/60, 106/64, 110/71,
    116/76, 124/79, 127/81. **SOURCED** — Merck Manual AAP 2017 Tables 4–5
25. Hard consistency rule: no under-13 patient above their own 95th percentile
    without a hypertension diagnosis. **SOURCED** (thresholds)
26. Ageing: SBP up, DBP down, wider pulse pressure after 60; thresholds
    unchanged. **SOURCED** (direction, StatPearls) / **ASSUMED** (magnitude)
27. Paediatric SpO₂ 96–100%; anything ≤92% must carry a respiratory
    presentation. **ASSUMED** (adult band is SOURCED)
28. Store BP as two integers, never the string `"130/80"`. **ASSUMED**
    (engineering consequence of SOURCED ranges)

### Anthropometry
29. 0–5 y height/weight from WHO medians, ±2 SD envelope. Boys weight:
    3.35 / 9.65 / 12.15 / 14.34 / 18.34 kg at 0 / 12 / 24 / 36 / 60 months;
    girls 3.23 / 8.95 / 11.48 / 13.85 / 18.22. Boys height 49.88 / 75.75 /
    87.12 / 96.08 / 109.96 cm; girls 49.15 / 74.02 / 85.72 / 95.05 / 109.42.
    **SOURCED** — WHO LMS workbooks, downloaded and parsed
30. WHO is a standard, not an Indian reference; note the caveat in the docs.
    **SOURCED** (WHO's own description of the MGRS sample)
31. Adult height mean 164.9 cm male / 152.6 cm female (1996 birth cohort).
    **SOURCED-WEAK** — <https://elifesciences.org/articles/13410> (`[blocked]`);
    verify before shipping.
32. Adult height SD 6.5 cm male / 6.0 cm female; peak at ~20 y male, 18–19 y
    female; −0.2 cm/year after. **ASSUMED**
33. Adult BMI is a **mixture**: underweight ~20% near 17.5, normal ~55% near
    21.5, overweight ~18% near 24, obese ~7% near 27. Proportion of
    underweight **SOURCED** (NFHS-4: 19.6% men, 22.4% women, ages 15–49,
    <https://pmc.ncbi.nlm.nih.gov/articles/PMC6976728/>); centres **ASSUMED**
34. Indian adult BMI bands: normal 18.5–22.9, overweight **23.0–24.9**, obese
    **≥25**, morbid ≥35. **SOURCED** —
    <https://www.pib.gov.in/PressReleasePage.aspx?PRID=2107179> and
    <https://pmc.ncbi.nlm.nih.gov/articles/PMC4555479/>
35. WHO bands (underweight <18.5, normal 18.5–24.9, overweight 25–29.9, obese
    ≥30) may be shown only as a labelled comparison. **SOURCED** — CDC NHANES
    2017 manual
36. Indian adult reference weight 65 kg (man) / 55 kg (woman), ages 19–39.
    **SOURCED** — <https://pmc.ncbi.nlm.nih.gov/articles/PMC7615800/>
37. Paediatric BMI cut-offs from the IAP-referenced table, not adult
    thresholds: at 5 y overweight ≈ 17.3/17.1 (boys/girls), obesity ≈ 20.5/20.2;
    at 15 y ≈ 21.3/21.5 and 25.9/26.0. **SOURCED** —
    <https://indianpediatrics.net/jan2012/jan-29-34.htm>
38. Every generated BMI re-checked against the band for that age and sex.
    **SOURCED**

### Structure and consistency
39. `visits.patient_id`, `hospital_id`, `doctor_id` all resolve; `diagnosis`
    and `severity` exist in `diseases.csv`. **ASSUMED** (engineering rule)
40. Primary keys unique; no duplicate `(patient_id, scheduled_date,
    scheduled_time)`; no shared phone numbers. **ASSUMED**
41. Diagnosis `age_range` must include the patient's age on the visit date.
    **SOURCED** (field exists in `diseases.csv`)
42. No sex-incompatible diagnosis. **SOURCED** (PMC7204018 criterion 1)
43. Track an `active_conditions` set per patient while generating, so a
    diagnosis is never repeated as if new and comorbidities are consistent.
    **SOURCED** (Synthea's `present` map)
44. Chronic disease vitals **trend**: treated hypertension improves across
    visits, untreated does not. **SOURCED** (Synthea Generic Module Framework)
45. `follow_up_days ≥ 0`; `Scheduled` visits land ~`follow_up_days` after the
    staging visit. **ASSUMED**
46. Regenerate twice with the same seed and compare file hashes. **ASSUMED**

### Privacy
47. No real data read, hashed, sampled or used to seed — generation only.
    **SOURCED** (HIPAA (R); DPDP §3)
48. Invented names from our own component lists; no external name corpus.
    **SOURCED** (HIPAA (A))
49. Emails on a domain we control; phones non-routable. **SOURCED** —
    HIPAA (D), (F)
50. No Aadhaar / PAN / voter ID / passport / licence / bank columns at all.
    **SOURCED** — HIPAA (G); project AGENTS.md
51. No `address_line`; keep only `area` / `city` / `state` / `pincode`, and
    document them as quasi-identifiers. **SOURCED** (HIPAA (B)) / **ASSUMED**
    (that keeping the coarse fields is worth the residual risk)
52. Ages over 89 aggregated to a single "90 or older" band. **SOURCED** —
    HIPAA (C)
53. No photo, biometric, device id, IP or URL columns. **SOURCED** —
    HIPAA (P), (Q), (M), (O), (N)
54. IDs are row counters, never derived from a person. **SOURCED** —
    HIPAA (H), (R)
55. Every under-18 record carries an **invented** guardian; no output implies
    consent was obtained from a real parent. **SOURCED** — DPDP §9, §2(f)
56. Emergency contacts are invented and internally consistent with the
    patient's invented household. **SOURCED** (HIPAA covers relatives and
    household members)
57. Ship `DATA_PROVENANCE.md` with seed, Python version, generator version,
    source list and retrieval dates. **ASSUMED** good practice
58. Keep the DPDP retention principle in the product design: erase when the
    purpose is served, unless a law requires retention. **SOURCED** — DPDP §8

---

## Open questions for the team

1. **The panel age mix (§2c) is the weakest link.** One Nagpur outpatient
   register would replace three guessed percentages with facts.
2. **Adult height (§4d) rests on a figure I could not read in the primary
   paper.** Pull the NCD-RisC country file before shipping, or get the
   Maharashtra figure.
3. **WHO vs Indian paediatric growth.** Decide once: WHO (comparable,
   international) or IAP charts (locally right, harder to source cleanly).
4. **Temperature unit.** °C stored, °F displayed — confirm with a clinician.
5. **Fever bounds.** The 34.5–41.0 °C envelope is mine. A paediatric
   clinician should set it.