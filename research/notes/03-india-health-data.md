# 03 — Indian & Nagpur Public Health Data: Verified Reference Sources

**Purpose:** real, citable reference data so synthetic records for a fictional
Nagpur clinic are plausible rather than invented.

**Verification rule applied:** every URL below was fetched by a script in
`research/scripts/` and the status / content-type / content-length recorded is
what that fetch actually returned. Where I could not confirm something from my
own fetch, it is marked **UNVERIFIED**. No URL here was constructed from memory
or from a URL pattern — the two Census `.xlsx` URLs were read out of the live
NADA catalogue HTML by `in_nada_dl.py`, and the GitHub file paths were read from
the GitHub contents API by `in_ghls.py`.

**Scripts used** (all in `research/scripts/`):

| Script | Purpose |
|---|---|
| `in_ver.py` | Generic probe: status, final URL, content-type, length, body prefix |
| `in_ghls.py` | Lists real filenames in a GitHub dir via contents API (never guesses paths) |
| `extract_nagpur.py` | Downloads the two PIN datasets, extracts + cross-checks Nagpur rows |
| `in_std.py` | Extracts STD / RTO area-code rows |
| `in_nada.py`, `in_nada_dl.py` | Parses Census NADA catalogue search + pages for real resource ids |
| `in_census.py`, `in_census2.py` | Reads the Census PCA `.xlsx` workbooks and prints real rows |
| `in_taluka.py` | Lists real Nagpur CD blocks and towns from the Census workbook |
| `in_facilities.py` | Extracts real facility rows from ESIC Nagpur + NABH pages |
| `in_mmc_abdm.py`, `in_chunk.py`, `in_paths.py` | Reads MMC portal JS bundle to find its real API base |
| `in_smartcity.py`, `in_lic.py`, `in_nabh_acc.py` | Licence / registry / portal checks |

---

## 1. Nagpur localities, wards and PIN codes

### Is there an official or open listing of Nagpur PIN codes with area names?

**Yes for PIN→post-office/locality, but the best ones are unlicensed.** There is
no open, officially-published India Post PIN dataset that is directly
downloadable; the Government Open Data route exists but I could not verify a
working download endpoint (see §5). What *is* genuinely usable are open-source
GitHub mirrors of the India Post master file, cross-checked below.

### 1a. `thatisuday/indian-pincode-database` — richest locality data (UNLICENSED)

- **Publisher:** GitHub user `thatisuday` (community mirror of India Post data)
- **Contains:** `officeName, pincode, officeType, deliveryStatus, divisionName,
  regionName, circleName, taluk, districtName, stateName`
- **Entry count (observed):** **154,823 rows parsed** from the file I downloaded
- **Licence:** **NONE.** GitHub API reports `license: null`; `LICENSE` returns
  **404**. Last commit 2016-09-06. → **Do not redistribute verbatim.**
- **URL (verified 200):**
  `https://raw.githubusercontent.com/thatisuday/indian-pincode-database/master/res/all_india_pin_code.csv`
  - status **200**, content-type `text/plain; charset=utf-8`,
    Content-Length **22,913,952** (~21.9 MB), 154,823 data rows
  - Registration required: **no**
- **Format:** CSV (space-padded)

**Observed Nagpur district content — 347 distinct rows, 342 distinct post-office
names, 63 distinct PIN codes.** State value confirmed as `MAHARASHTRA` on every
Nagpur row. Urban Nagpur PINs (`taluk = Nagpur`):

```
440001  Nagpur GPO / Sadar Bazar / Ravi Nagar / Kasturchand Park / Mohan Nagar / Bureau Of Mines / Coal Estate
440002  Nagpur City H.O / Nayapura
440003  Ajni / Imamwada / Medical College
440005  Nagpur Airport
440006  Seminary Hills
440007  Vayusena Nagar
440008  Bagadganj
440010  Shankar Nagar / Abhyankar Nagar / Gandhi Nagar / Giripeth / Gokulpeth / Khare Town / V R C E
440012  Dhantoli / Sitabuldi / Congress Nagar / Hitavada / Netaji Market / Patwardhan Ground
440013  Borgaon Road / Katolroad
440014  Bezonbagh / Jaripatka
440015  Narendra Nagar / Samartha Nagar / Vivekanand Nagar
440016  Indl.Area Nagpur / MIDC Nagpur / SRPF
440017  Dr.Ambedkar Marg / Panchsheel Nagar
440018  Ganjipeth / Mahatma Fule Bazar / Mominpura
440019  C.R.P.F. Nagpur
440020  Neeri
440021  A.D. Project
440022  Laxmi Nagar / Ranapratap Nagar / Shradhananpeth / Trimurti Nagar
440023  Wadi / Dattawadi / Dawlameti / Bazargaon / Dhamna / Gondkhairi / Lava / Vyahad
440024  Manewada Road / Dighori Naka / Hanuman Nagar / Nandavan Colony / Ayodhya Nagar
440025  Khamla / Ujwal Nagar
440026  Uppalwadi / Khairi Akashwani
440027  Parvati Nagar / Vishwakarma Nagar
440030  Mankapur / Nadt Campus
440032  Mahal
440033  University Campus
440034  Mhalginagar / Narsala / Pipla
440035  Bhandewadi / Kalmna Market Yard / Kapsi BK
440036  Jaitala
440037  BESA Road
```

Rest of district (taluk in brackets), full 63-code list:

```
441001 Kamthi City/Kamthi H.O [Kamthi]
441101 Khapa/Wakodi/Nagalwadi/Badegaon [Saoner, Kamptee, Savner]
441102 Khaperkheda/Bina/Walni Colliery [Saoner, Kamptee, Parsioni]
441103 Katol/Masod/Kondhali [Katol]
441104 Mauda/Chirwa/Dhanla [Mauda]
441105 Parseoni/Parseoni S.O [Parseoni]
441106 Ramtek/Mahadula (Ramtek)/Nagdhan [Ramtek]
441107 Saoner S.O/Telgaon/Waghoda [Saoner, Savner, Kalameshwar]
441108 Bori S.O/Borkhedi/Ridhora/Sawangi Asola [Nagpur, Nagpur (Rural)]
441109 Sillewara Project [Saoner]
441110 Hingna S.O/Wanadongri/Kanholibara [Hingna]
441111 Koradi Tps/Gumthi [Kamptee, Kamthi]
441112 Kelod S.O/Khairi Dhalgaon [Saoner, Savner]
441113 Patansaongi/Pipla Dakbanglow [Saoner]
441122 Industrial Area Butibori/Takalghat/Salaidhabha [Nagpur (Rural), Hingna]
441123 Godhani S.O [Kamthi]
441201 Bhiwapur S.O/Jaoli/Virkhandi [Bhiwapur]
441202 Kuhi S.O/Dighori Kale/Rajola [Kuhi]
441203 Umred S.O/Umred Bazar/Aptur [Umred, Umrer, Bhiwapur]
441204 Udasa/Umred Project/Champa [Umrer]
441210 Mandhal S.O/Kujba/Pachkhedi [Kuhi]
441214 Sirsi S.O (Nagpur)/Besur/Hiwra Hiwri [Umrer, Umred]
441301 Narkhed S.O/Jalalkheda/Dhawlapur? -> Narkhed [Narkhed]
441302 Katol S.O/Isapur Khurd/Dhawlapur [Katol]
441303 Mowad S.O/Khairgaon [Narkhed]
441304 Narkher S.O/Belona/Kharsoli [Narkher]
441305 Bhishnoor B.O/Paradsinga S.O/Yerla (Dhote) [Katol]
441306 Sawargaon S.O/Dorli Bhandwalkar/Pipla Kewalram [Narkher]
441401 Pauni B.O/Hiwra Bazar/Kandri/Kanhan Pipri [Parseoni, Ramtek, Kamptee]
441404 Kamthi Colliery S.O/Gondegaon [Parseoni]
441501 Kalmeshwar S.O/Midc Kalmeshwar/Fetri [Kalameshwar, Nagpur Rural]
441502 Mohpa S.O/Raulgaon/Pardi Deshmukh [Kalameshwar]
```

### 1b. `kishorek/India-Codes` — PIN + STD + RTO (UNLICENSED, useful for cross-check)

- **Publisher:** GitHub user `kishorek`
- **Licence:** **NONE** (GitHub API `license: null`). README states verbatim:
  *"Disclaimer: Most of the data are collected from internet sources like
  wikipedia. Feel free to fork it and fix errors if any."*
  Last commit 2018-12-17. → **Not redistributable; treat as a weak cross-check only.**
- **URLs (all verified 200, `text/plain; charset=utf-8`):**
  - `https://raw.githubusercontent.com/kishorek/India-Codes/master/csv/pincodes.csv`
    — Content-Length **2,286,207**, **39,736 rows**, cols
    `PostOfficeName,Pincode,DistrictsName,City,State`
  - `https://raw.githubusercontent.com/kishorek/India-Codes/master/csv/stdcodes.csv`
    — Content-Length **49,503**, **2,611 rows**, cols `City,Code`
  - `https://raw.githubusercontent.com/kishorek/India-Codes/master/csv/RTO.csv`
    — Content-Length **40,703**, **1,093 rows**, cols `RegNo,Place,State`
  - Registration required: **no**

**PIN cross-check result (this is the important part):**

| | Count |
|---|---|
| Distinct Nagpur PINs in thatisuday | 63 |
| Distinct Nagpur PINs in kishorek | 69 |
| **Agreed by BOTH independent datasets** | **50** |
| Only in kishorek (19) | `440004 440009 440011 440029 441114 441115 441116 441117 441216 441402 441403 441405 441406 441408 441409 441503 441806 441807 441911` |
| Only in thatisuday (13) | `440019 440030 440032 440033 440034 440035 440036 440037 441108 441113 441122 441123 441214` |

**Practical rule for the project:** only treat a Nagpur PIN as safe if it is in
the **50-code agreed set**; the rest are single-source and one of the two is
known to be Wikipedia-derived. The agreed set is the `thatisuday` list minus
those 13, i.e. all of `440001–440027` except `440004/440009/440011/440029`,
plus `441001 441101–441107 441109–441112 441201–441204 441210 441301–441306
441401 441404 441501 441502`.

### 1c. `bilal-webdev/india-postal-pincode-dataset` — MIT, safely redistributable

- **Licence:** **MIT** (LICENSE fetched, 1,071 bytes, "Copyright (c) 2026 Bilal Shaikh")
- **Contains:** `pincode,state,district,blocks,state_lgd,district_lgd` — LGD
  (Local Government Directory) codes for states/districts. **No post-office or
  locality names**, and README claims only **20,144 records** vs 154,823.
- **URL (verified 200):**
  `https://raw.githubusercontent.com/bilal-webdev/india-postal-pincode-dataset/main/csv/india-postal-lgd-mapping.csv`
  — `text/plain; charset=utf-8`, Content-Length **1,269,336**
- **Use:** good for **LGD state/district codes** and as the one dataset we can
  legally vendor into the repo. Not useful for street-level realism.

### Wards

**UNVERIFIED / not found.** I did not locate an open, downloadable ward list for
Nagpur Municipal Corporation. The Census sources below give **towns** and **CD
blocks**, not municipal wards. Do not invent ward names as if they were sourced.

---

## 2. Maharashtra and Nagpur STD / area codes

**Nagpur landline STD code is `0712` — confirmed, and triple-corroborated.**

1. **Direct observation** from `stdcodes.csv` (verified 200, 49,503 bytes,
   2,611 rows): exactly one row matches Nagpur — `City=Nagpur, Code=0712`.
   Note this file has **no state column**, so the city token is the only key.
   Maharashtra comparators from the same file: `Pune=020`, `Mumbai=022`,
   `Ahmednagar=0241`, `Amravati=0721`, `Kolhapur=0231`, `Nanded=02462`,
   `Ratnagiri=02352`, `Aurangabad=02432` and `Aurangabad=06186`.
2. **Independent corroboration A** — every Nagpur phone number in the ESIC
   Nagpur empanelled list (§3b) is `0712-…`.
3. **Independent corroboration B** — the CGHS Nagpur empanelled PDF (§3c)
   shows `0712-664266/6624100/6624400` (Wockhardt), `(0712) 2701700` (Keshav),
   `0712-243011` (Midas), `0712-2706020` (Lotus).

**Vehicle RTO registration prefixes in/near Nagpur** — from `RTO.csv`
(verified 200, 40,703 bytes, 1,093 rows), 4 rows match Nagpur:

```
MH31  Nagpur
MH40  Wadi, Nagpur (rural)
MH49  Nagpur (East)  — RTO located on Bhandara Road
MH29  Yavatmal — RTO is located on Nagpur Road   (not a Nagpur RTO; note the trap)
```

---

## 3. Hospital and clinic registries

### 3a. NABH accredited-hospitals list — **NO downloadable list exists (verified negative)**

I tested the obvious endpoints directly:

| URL | Result |
|---|---|
| `https://international.nabh.co/frmViewAccreditedEntryLevelHosp.aspx` | **200**, 69,991 bytes — but the table body is literally **`No Record`** (1 table row, 0 certificate links) |
| `https://portal.nabh.co/frmViewAccreditedHospitals.aspx` | **404** |
| `https://portal.nabh.co/hospitals/accredited-hospitals` | **404** |

**Conclusion: NABH does not publish a working downloadable accredited-hospital
list.** Do not claim one exists. Individual accreditation *certificate PDFs* are
real and fetchable, e.g.
`https://portal.nabh.co/Documents/AccreditedList/Hospitals/H-2009-0036_5th%20Edition.pdf`
→ **200**, `application/pdf`, Content-Length **962,498**, magic `%PDF-1.7`. But
these are per-hospital, unlisted, un-enumerable — useless as a dataset.

### 3b. ESIC Nagpur empanelled centres — **best usable Nagpur facility list**

- **Publisher:** Employees' State Insurance Corporation, RO/SRO Nagpur
- **URL (verified 200):**
  `https://sronagpur.esic.gov.in/ro-sro-list-empanelled-centers`
  — `text/html; charset=UTF-8`, Content-Length **97,803**; 46 parsed table rows
- **Contains columns:** `Sr. No. | Location | Name & Address of the Hospital |
  Specialty | SST Investigation | Contact | Email id | Validity`
- **Registration required:** no. **Licence:** Government Open Data License – India
  (site is a Government of India NIC-hosted domain); individual rows are public
  directory data. **Redistributable with attribution.**
- **Why it is the best source for this project:** it gives, for one district,
  real hospital names + **street addresses with real PIN codes** + real STD
  phone numbers + real speciality lists + validity date ranges. Observed rows
  (Nagpur entries, verbatim from the page):

```
2  Nagpur  Lotus Hospital & Research Center, 205, Om Nagar, Near Tiranga Square,
          Sakardara Police Station Road, Nagpur - 440009
          Oncology, Oncosurgery, Urosurgery, Gastroenterology, Gastrosurgery,
          Endocrine Surgery, Plastic Surgery
3  Nagpur  Platina Heart Hospital, Near Hotel Hardeo, Sitabuldi, Nagpur - 440012
          CTVS & Cardiology  | Echo, Spl. Bio. Imm. Inv. | 0712-2566555
4  Nagpur  Sengupta Hospital Research Institute, Ravinagar Square, Nagpur - 440033
          CTVS & Cardiology  | Echocardiography | 0712-2532697
5  Nagpur  Asha Hospital AIMS & Research Center Pvt Ltd, NH-7, Near Lekhanagar,
          Contonement, Distt-Kamptee, Nagpur - 441001
6  Nagpur  Spandan Heart Institute & Research Center Ind. Pvt. Ltd., 31, Kusum Plaza,
          Off. Chitale Marg, Dhantoli, Nagpur - 440012 | 0712-2443003/6453003/2443333
7  Nagpur  Radiance Hospital Pvt Ltd, 268, Central Avenue, Near Ambedkar Square,
          Wardhaman Nagar, Nagpur - 440008
8  Nagpur  Rainbow Medinova Diagnostic Services, 282, Central Bazar Road,
          Ramdaspeth, Nagpur - 440010
9  Nagpur  Kunal Hospital, Koradi Main Road, Mankapur, Nagpur - 440030
10 Nagpur  Crescent Hospital & Heart Center, Plot No. 2/5, Near Lokmat Square,
          Dhantoli, Nagpur - 440012
12 Nagpur  Lata Mangeshkar Hospital, 5-YMCA Complex, Maharaj Bagh Road,
          Sitabuldi, Nagpur - 440001
13 Nagpur  Central India Institute of Haematology & Oncology, Plot No 14/2,
          Park Corner, Balraj Marg, Near Lokmat Square, Dhantoli
14 Nagpur  National Cancer Institute, Manorama Chambers, WHC Road, Dharampeth,
          Nagpur - 440010 | 0712-6612277
15 Nagpur  Keshav Hospital, 117, Manewada Square, Ring Road, Nagpur
16 Nagpur  Medicare Multispeciality Hospital, 2nd Floor, Gulmohar Complex,
          Chindwara Road, Manakpur, Nagpur - 440008
17 Nagpur  Zenith Hospital, 141, Shivaji Nagar, North Ambazari Road, Nagpur - 440012
18 Nagpur  Rashtrasant Tukdoji Regional Cancer Hospital & Research Center,
          Tukdoji Square, Manewada Road, Nagpur - 440027 | 0712-2744441/2748995
19 Nagpur  Shravan Hospital & Kidney Institute, 239, Nandanvan, Cement Road,
          Nagpur - 440009 | 0712-2711737
20 Nagpur  Metro Scan, Achraj Aristo, Beside Union Bank & Amar Jyoti Complex,
          Lokmat Square, Wardha Road, Dhantoli, Nagpur - 440012 | 0712-6628666
21 Nagpur  SS Multispeciality Hospital, Plot No 13, New Sneh Nagar,
          Near Jaiprakash Nagar Metro Station, Nagpur 440015 | 0712-2295358
22 Nagpur  Columbia Hospital & Research Centre, 3rd Floor, Hyatt Medicare,
          Dr. N. B. Khare Marg, Dhantoli, Nagpur 440012 | 0712-2420005
```

Note the PIN spread matches §1 exactly (`440001, 440008, 440009, 440010,
440012, 440027, 440030, 440033, 441001`) — a third independent confirmation of
the PIN data.

### 3c. NABH CGHS-recommended hospitals/diagnostic centres for Nagpur — **usable**

- **Publisher:** NABH (Quality Council of India)
- **URLs (both verified 200):**
  - Hospitals: `https://portal.nabh.co/frmViewCGHSRecommend.aspx?Type=Hospital&cityID=100`
    → `text/html; charset=utf-8`, Content-Length **142,385**, 44 data rows
  - Diagnostic centres:
    `https://portal.nabh.co/frmViewCGHSRecommend.aspx?Type=Diagnostic%20Centre&cityID=100`
    → same page family, real Nagpur lab rows
- **Contains:** `S.N. | Hospital Name | Recommendation No. | Recommendation Date | Applied For | Status`
- **Registration required:** no. **Redistributable:** public directory,
  cite NABH.

**This is where the real-world *accreditation-number format* comes from.**
Recommendation numbers are structured, and the scheme differs by facility type:

```
HOS/2022/C0104   HOS/2022/C0173   HOS/2022/C0434   HOS/2022/C0342
HOS/2022/C0419   HOS/2022/C0422   HOS/2022/C0420   HOS/2023/C1008
HOS/2024/C1369   HOS/2025/C2672   HOS/2025/C2758
LAB/2022/C0039   LAB/2023/C0054   LAB/2024/C0167   LAB/2025/C0349
```
Legacy (pre-2021) entries use a bare `YYYY-NNNN`, e.g. `2015-0361`,
`2016-0511`, `2021-1647`. So: **`<TYPE>/<YYYY>/C<NNNN>` modern, `<YYYY>-<NNNN>`
legacy**, where TYPE ∈ {HOS, LAB}. Real Nagpur names captured include Sushrut
Institute of Medical Sciences, Lata Mangeshkar Hospital, Rashtrasant Tukdoji
Cancer Hospital and Research Centre, G T Padole Hospital, Midas Multispeciality
Hospital, Keshav Hospital, Samarpan Hospital and Research Institute, Metro Scan
Advanced Diagnostic Centre, Prism Pathology Lab.

### 3d. CGHS empanelled hospitals, Nagpur (PDF)

- **URL (verified 200):**
  `https://cghs.mohfw.gov.in/CGHSGrievance/FormFlowXACTION?fileName=16062025104702_List-of-empanelled-HCOs--Nagpur-as-on-26-December-2024.pdf&folderName=Circular&hmode=ftpFileDownload&isGlobal=1`
  — `application/pdf; charset=UTF-8`, no Content-Length (chunked), magic
  `%PDF-1.7`, body confirmed real
- **Contains:** Nagpur-only empanelled HCOs with address, telephone
  (`0712-…`), and the specialities each is empanelled for
- **Caution:** the filename encodes a date (`26-December-2024`); the URL is a
  generated FTP-style download action, so it may rot. Re-fetch before citing.

### 3e. Maharashtra Public Health Department

- `https://phd.maharashtra.gov.in/en/documents/page/5` — documents index
  (Arogya Patrika monthly, IPHS circulars). **UNVERIFIED by my own fetch**
  (found via search, not probed).
- `https://cdnbbsr.s3waas.gov.in/.../2025081946322959.pdf` — Public Health
  Department "Comprehensive Note" 1st Session 2025, which contains a real
  Maharashtra facility inventory (10,766 sub-centres, 1,939 PHCs, 367 rural
  hospitals, 68 + 33 sub-district hospitals, 19 district hospitals, 22 women
  hospitals). **UNVERIFIED by my own fetch** — worth probing, high value.

---

## 4. MMC / MCI doctor registration numbers

### Is there a public register or published format? — **No public bulk register. Format = 10 digits.**

**What I verified myself:**

- `https://maharashtramedicalcouncil.org.in/doctors` → **200**, `text/html`,
  Content-Length **463**. It is a **client-rendered SPA shell** — the entire body
  is `<div id="app"></div>` plus a module script. **The doctor data is not in
  the HTML**, so it cannot be scraped with a plain fetch.
- Per-doctor URLs such as
  `https://www.maharashtramedicalcouncil.org.in/doctors/8c04672c-b6ea-485a-a3bc-41ad48c53347`
  also return the same **463-byte shell** — the UUID is the real record key but
  the content is JS-injected.
- Reading the portal's own JS bundle (**verified 200**, `text/javascript`,
  Content-Length **767,616**, file `assets/index-BM8AQDEc.js`) and the
  `portal-api-client` chunk revealed the **real API base**:
  `https://api.maharashtramedicalcouncil.org.in/api/v1`
  (literal in bundle: `"https://api.maharashtramedicalcouncil.org.in/api/v1".trim()`,
  error text *"Missing VITE_API_BASE_URL. Set it in apps/portal/.env."*).
- That API host **is live** — `https://api.maharashtramedicalcouncil.org.in/api/v1`
  returns **404 `Cannot GET /api/v1`**, and `.../api/v1/doctors` returns
  **404 `Cannot GET /api/v1/doctors`**. So it is an Express server, but the
  doctor path is not `/doctors` and I did **not** find the correct route.
- The legacy ASP.NET site `https://www.maharashtramedicalcouncil.in/frmrmplist.aspx`
  (the old "RMP Information" search) is **404** — that older register is gone.

### What a real MMC registration number looks like

**VERIFIED from the portal's own UI bundle** (string `complaint.rmpSearch.placeholderRegNo`
in `index-BM8AQDEc.js`):

```
"complaint.rmpSearch.byRegNo",  "MMC registration number"
"complaint.rmpSearch.placeholderRegNo",  "e.g. 2023072365"
```

So the **current MMC registration number is a 10-digit numeric string**, and the
portal's own worked example is `2023072365`.

**INFERENCE (flagged as such):** the 10-digit form decomposes as
`YYYY` + `MM` + 4-digit serial, i.e. `2023|07|2365`. Supporting (but **not
independently verified by my own fetch** — these came from search-engine
rendering of the SPA, not from my fetch): `2007051715` → `2007|05|1715`.
A **second, older generation** of registration numbers is a short bare serial
(e.g. `88484`, registration date 11 Jan 1999). **Both generations are therefore
in circulation**, which matters if the synthetic records span decades.

**Recommendation:** generate synthetic MMC numbers as 10 digits matching
`YYYYMMNNNN` where `YYYYMM` is plausible for the qualification year and `NNNN`
is a 4-digit serial, e.g. `2014092377`. Do not generate 5-digit numbers for
recent doctors. Do not claim to have downloaded the register — you cannot.

For MCI (national, pre-2020) the equivalent state-medical-council number is the
same concept; **UNVERIFIED** — I did not probe `nmc.org.in`.

---

## 5. data.gov.in health datasets — **partially verified; the API is the blocker**

- `https://www.data.gov.in/resource/list-hospitals-empaneled-under-cghs-all-over-india`
  → **200**, `text/html; charset=utf-8`, chunked (no Content-Length). It is a
  **Nuxt SPA**; the dataset body is not in the served HTML.
- `https://www.data.gov.in/catalogs?filters%5Bstate%5D=Maharashtra`
  → **200**, `text/html; charset=utf-8`, **1,017,958 bytes**. Page renders, but
  my parse found **0 resource UUID links** in the SSR output (data is fetched
  client-side).
- `https://www.data.gov.in/backend/dms/v1/catalogs?...` → **200 but redirects to
  `https://www.data.gov.in/not-found?...`** — that backend path does not exist.
- `https://api.data.gov.in/...` → **connection timeout (WinError 10060)** from
  this network. Not usable here.

**Licence (confirmed in the page footer of the OGD portals):** *Government Open
Data License – India* — I read this string directly out of the fetched
`smartcities.data.gov.in` HTML.

**Verdict for §5: I could not verify a single working, directly-downloadable
health resource URL on data.gov.in from this environment.** Do not put a
data.gov.in CSV URL in the project docs unless someone re-verifies it from a
network that can reach `api.data.gov.in`. The portal is real and the licence is
permissive, but the access path is an API-key-gated JSON endpoint, and the
catalogue itself did not yield resource IDs to me.

### Better alternative that IS reachable: Smart Cities Nagpur portal

- **URL (verified 200):** `https://smartcities.data.gov.in/cities/Nagpur`
  — `text/html; charset=utf-8`, Content-Length **508,856**
- **Licence (read verbatim from the fetched HTML):** *"All datasets/resources
  including metadata published on smartcities.data.gov.in are licensed under the
  **Government Open Data License - India**"*
- Nagpur-specific OGD data, no login. The specific catalogue titles were
  **UNVERIFIED** — my regex parse of the Nuxt payload returned 0 titles, so the
  listing is client-rendered. Fetch the page in a browser to enumerate.

---

## 6. ABDM (Ayushman Bharat Digital Mission) sandbox — **no downloadable synthetic records**

- `https://sandbox.abdm.gov.in/` → **200**, `text/html`, Content-Length **683**,
  **redirects to `https://sandbox.abdm.gov.in/sandbox/v3`**. SPA shell again
  (683 bytes).
- `https://sandbox.abdm.gov.in/docs/healthid` → **503**,
  `text/plain`, body `Please make a valid request.` — the documentation route is
  **not publicly fetchable**.
- `https://sandbox.abdm.gov.in/sandbox/v3/new-documentation` → **200**, 683-byte
  SPA shell.
- `https://dev.abdm.gov.in/api/hiecm/gateway/v3/certs` → **401 Unauthorized** —
  the gateway requires credentials. **No anonymous access.**

**Access model (from the portal's own published text):** sandbox access requires
*"Send Request → Get Access after health tech committee approval → Integrate →
Functional Testing/WASA → security audit → HTC Demo → Go Live."* So it is
**gated by human approval**, not self-service.

**There is no downloadable "synthetic ABHA demo dataset".** What exists instead:

### 6a. Official `NHA-ABDM/ABDM-wrapper` — **the genuinely usable ABDM artefact**

- **Publisher:** National Health Authority (official GitHub org `NHA-ABDM`)
- **Licence:** **Apache License 2.0** — LICENSE fetched, **200**, 11,357 bytes.
  → **Redistributable.**
- **Repo API (verified 200, `application/json`):**
  `https://api.github.com/repos/NHA-ABDM/ABDM-wrapper`
- **Contains:** `mock-gateway/`, `sample-hip/`, `sample-hiu/`,
  `sample-hiu-ui/`, `fhir-mapper/`, `postmanCollections/`, `docs/`
- **Postman collections (verified via contents API, 200):**
  - `https://raw.githubusercontent.com/NHA-ABDM/ABDM-wrapper/master/postmanCollections/HIP.postman_collection.json` — 3,857 bytes
  - `https://raw.githubusercontent.com/NHA-ABDM/ABDM-wrapper/master/postmanCollections/HIU.postman_collection.json` — 25,740 bytes
- **OpenAPI specs for the sample HIP (verified via contents API, 200):**
  - `.../sample-hip/specs/hip-facade.yaml` — 19,776 bytes
  - `.../sample-hip/specs/hip-v3-facade.yaml` — 33,404 bytes
  - `.../sample-hip/specs/mergedSpec.yaml` — 67,017 bytes

**Why this matters:** these YAML specs are the authoritative **ABDM/FHIR R4
payload shapes** for Indian health records — the right thing to model synthetic
records on, and the right thing to cite when justifying an ABHA-shaped schema.

### 6b. Confirmed identifier formats (from NHA's own published docs)

```
ABHA number          14-digit numeric
ABHA address         <alphanumeric>@abdm   (live)
                     <alphanumeric>@sbx    (sandbox)
Gateway base URL     sandbox  https://dev.abdm.gov.in    X-CM-ID: sbx
                     prod     https://apis.abdm.gov.in   X-CM-ID: abdm
Bridge ID            SBX_00XXXX   (sandbox, issued by NHA to the HIP)
Facility/Service ID  IN02100000XX  (from the NHPR facility registry)
Consent purpose code CAREMGT / text "Care Management"
hiTypes              Prescription, DiagnosticReport, DischargeSummary,
                     ImmunizationRecord, HealthDocumentRecord,
                     WellnessRecord, OPConsultation
Sample demo patient  name "User 1", abhaNumber 91178386176531,
                     abhaAddress "91178386@sbx", gender "M", DOB 10/10/1994,
                     address line "C/O Sandipan..."
Sample requester     name "Dr. Manju", identifier type "REGNO",
                     value "MH1001", system "https://www.mciindia.org"
```

Note `REGNO` value `MH1001` — a **state-prefixed** medical registration
identifier, consistent with §4. Sandbox doc PDFs are at
`https://sandboxcms.abdm.gov.in/uploads/*.pdf` (**host verified reachable via
search; individual PDFs UNVERIFIED by my own fetch**).

---

## 7. HMIS — **no anonymous aggregate download**

- `https://hmis.mohfw.gov.in/` → **200**, `text/html`, Content-Length
  **135,659**. The Angular app shell is public, but the facility search form
  posts to a backend and the portal requires **mobile-OTP-verified registration**
  ("*You are required to enter valid Mobile number and valid Email address in
  order to gain access to the system*"). → **Login required.**
- `https://nhm.gov.in/index1.php?lang=1&level=1&lid=205&sublinkid=112`
  (Monitoring Reports) → **200**, `text/html; charset=utf-8`. The page lists
  per-state downloadable archives; **Maharashtra is listed (~480 KB)**.
  **The Maharashtra archive URL itself is UNVERIFIED** — I did not extract and
  probe the underlying link. **This is the single most promising remaining lead
  for HMIS aggregates and should be probed next.**
- Maharashtra DMER public dashboards
  `https://dmer.maharashtra.gov.in/english/public-dashboards` — **UNVERIFIED**
  (search result only); reportedly links a NextGen HMIS dashboard and OPD
  registration heatmaps.

**Verdict: HMIS itself is login-gated. NHM's per-state monitoring-report
archives look downloadable and are the route worth pursuing.**

---

## 8. Census 2011 demographics for Nagpur — **fully verified, this is the gold**

All three URLs below returned **200**, `application/octet-stream`, with the
Content-Lengths shown. The `.xlsx` URLs were **read out of the NADA catalogue
HTML**, not guessed.

| What | URL | Size |
|---|---|---|
| State + district PCA, all India | `https://censusindia.gov.in/nada/index.php/catalog/6191/download/9268/DDW_PCA0000_2011_Indiastatedist.xlsx` | **1,376,414 B** |
| Nagpur CD-block PCA | `https://censusindia.gov.in/nada/index.php/catalog/41183/download/44814/PCA_CDB-2709-F-Census.xlsx` | **914,124 B** |
| Nagpur District Census Handbook (Part B) | `https://censusindia.gov.in/nada/index.php/catalog/809/download/2886/DH_2011_2709_PART_B_DCHB_NAGPUR.pdf` | **5,413,276 B**, `%PDF-1.5` |

Catalogue pages (both verified 200):
`https://censusindia.gov.in/nada/index.php/catalog/6191` and
`https://censusindia.gov.in/nada/index.php/catalog/41183`
Discovery search that located them (verified 200, 47,469 bytes, **81 hits**):
`https://censusindia.gov.in/nada/index.php/catalog/search?sk=Nagpur+primary+census+abstract`

- **Publisher:** Office of the Registrar General & Census Commissioner, India
- **Licence:** Government of India open data; **registration not required**
- **Note:** the district file's *actual* sheet is named `sheet1.xml` while the
  zip lists `sheet2, sheet3, sheet1` — parse **all** worksheets, not just the
  first (`in_census.py` initially printed nothing for this reason; `in_census2.py`
  fixed it).

**Columns available (verified header row):**
`State, District, Subdistt, Town/Village, Ward, EB, Level, Name, TRU, No_HH,
TOT_P, TOT_M, TOT_F, P_06, M_06, F_06, P_SC, M_SC, F_SC, P_ST, M_ST, F_ST,
P_LIT, M_LIT, F_LIT, P_ILL, ...` (100+ columns incl. worker/marginal-worker splits)

### Nagpur district, Census 2011 — observed row values

| Indicator | Nagpur district | Maharashtra (state) |
|---|---:|---:|
| Households | 1,041,544 | 24,421,519 |
| Population | **4,653,570** | **112,374,333** |
| Male | 2,384,975 | 58,243,056 |
| Female | 2,268,595 | 54,131,277 |
| Sex ratio (F/1000 M) | **951.2** | **929.4** |
| Population aged 0–6 | 497,087 | 13,326,517 |
| Literate (7+) | 3,673,808 | 81,554,290 |
| **Literacy rate** | **88.39 %** | **82.34 %** |
| SC population | 867,713 (18.65 %) | 13,275,898 (11.81 %) |
| ST population | 437,571 (9.40 %) | 10,510,213 (9.35 %) |
| Rural population | 1,474,811 | 61,556,074 |
| Urban population | 3,178,759 | 50,818,259 |

**Methodology check that validates the whole table:** literacy rate computed as
`P_LIT / (TOT_P − P_06)` gives **88.39 %** for Nagpur and **82.34 %** for
Maharashtra — both match the officially published Census 2011 figures exactly.
So these numbers are the real ones, and the age-7+ denominator is the correct
basis. Nagpur district is one of the highest-literacy districts in India; use
that, not a national average, when justifying synthetic patients.

Note **Nagpur is 68.3 % urban** (3,178,759 / 4,653,570) — relevant if the
clinic catchment is urban.

### Nagpur CD blocks / tehsils — 13, verified

```
0074 Narkhed        0075 Katol          0076 Kalameshwar   0077 Savner
0078 Parseoni       0079 Ramtek         0080 Mauda         0081 Kamptee
0082 Nagpur(Rural)  0084 Hingna         0085 Umred         0086 Kuhi
0087 Bhiwapur
```
(Census codes; note the gap — `0083` is absent, and `Kalameshwar` is the
Census spelling, not the common "Kalmeshwar".)

### Nagpur towns — 28, verified

```
Bamhni (CT)              Kalameshwar
Bhokara (CT)             Nagpur(Rural)
Bori (CT)                Nagpur(Rural)
Borkhedi (CT)            Nagpur(Rural)
Chandkapur (CT)          Savner
Chicholi (CT)            Savner
Davlameti (CT)           Nagpur(Rural)
Digdoh (CT)              Hingna
Hudkeshwar bk. (CT)      Nagpur(Rural)
Isasani (CT)             Hingna
Kandri (CT)              Ramtek
Kanhan (Pipri) (CT)      Parseoni
Koradi (CT)              Kamptee
Mahadula (CT)            Kamptee
Mouda (CT)               Mauda
Nagalwadi (CT)           Hingna
Narsala (CT)             Nagpur(Rural)
Nildoh (CT)              Hingna
Sillewada (CT)           Savner
Sonegaon (Nipani) (CT)   Nagpur(Rural)
Takalghat (CT)           Hingna
Tekadi (CT)              Parseoni
Waddhamana (CT)          Hingna
Wadi (CT)                Nagpur(Rural)
Waghoda (CT)             Savner
Walani (CT)              Savner
Wanadongri (CT)          Hingna
Yerkheda (CT)            Kamptee
```

`Nagpur (M Corp.)` is the municipal corporation town (Census code
`27 505 04032 802710`, sub-district `Nagpur (Urban)`), per the PCA(SC)
catalogue page `https://censusindia.gov.in/nada/index.php/catalog/41767`
(verified 200).

**Important limitation:** this gives **age 0–6 only, not a full age pyramid.**
For a real age/sex distribution you need the PCA **C-13 / C-14 age-sex table**
or NFHS-5. The PCA files I downloaded have `P_06/M_06/F_06` and
`P_LIT/P_ILL` but **no age bands beyond 0–6**. Do not fabricate an age
distribution and cite Census 2011 for it.

---

## 9. Open Indian address / locality datasets

| Source | Verdict |
|---|---|
| `data.gov.in` | Licence = GODL-India, but **no working download verified** (§5) |
| `smartcities.data.gov.in/cities/Nagpur` | **Verified 200**, GODL-India confirmed in footer; Nagpur-specific; catalogue titles not parsed (client-rendered) |
| `bilal-webdev` LGD mapping | **MIT**, redistributable, PIN→state/district + LGD codes only (§1c) |
| `mahasdb.maharashtra.gov.in/rawData.do` | **Verified 200**, `text/html;charset=UTF-8` — Maharashtra State Data Bank, has Census/Health/Medical-Education report categories. Body is a JS form, no direct file links extracted. **Worth a browser pass.** |
| `mapstreetdata.com` | Aggregator, appeared in search with Nagpur hospital listings. **UNVERIFIED**, and an aggregator — do not cite as authoritative. |

There is **no open-source India address registry** in the OSM/geocoder sense
that is both authoritative and redistributable. The postal-code layer is the
only genuinely open piece, and its best two sources are unlicensed (§1a, §1b).

---

## 10. Practical bottom line — what to actually use

### USE — verified, citable, and safe

| # | Source | Use it for | Licence / redistribution |
|---|---|---|---|
| 1 | **ESIC Nagpur empanelled centres** | Real Nagpur hospital names, **street addresses + PINs**, specialities, `0712` phones, validity dates. Best realism-per-effort source in this whole document. | GODL-India, no login → **redistributable with attribution** |
| 2 | **NABH CGHS-recommended Nagpur (hospitals + diagnostics)** | Real accreditation-number **format** (`HOS/YYYY/CNNNN`, `LAB/YYYY/CNNNN`, legacy `YYYY-NNNN`); real competing-facility names | Public directory, no login → **citable** |
| 3 | **Census 2011 Nagpur district PCA** (`catalog/6191`) | District population, sex ratio, **88.39 % literacy**, SC/ST shares, urbanisation | GoI open data, no login → **redistributable with citation** |
| 4 | **Census 2011 Nagpur CD-block PCA** (`catalog/41183`) | The 13 real tehsil names and 28 real town names | as above |
| 5 | **Nagpur DCHB Part B PDF** (`catalog/809`) | Village/town directory + amenities; deepest locality source | as above |
| 6 | **NHA-ABDM/ABDM-wrapper** specs + Postman collections | **Authoritative ABDM/FHIR R4 payload shapes**; ABHA 14-digit / `@sbx` / `CAREMGT` / hiTypes | **Apache-2.0 → fully redistributable** |
| 7 | **bilal-webdev LGD mapping** | The one PIN dataset we can legally vendor; LGD codes | **MIT → redistributable** |
| 8 | **stdcodes.csv Nagpur row** | `0712` — but corroborate from ESIC/CGHS before citing | Unlicensed → cite ESIC/CGHS instead |

### USE WITH CARE

- **thatisuday + kishorek PIN datasets** — the *only* source of real
  Nagpur **locality↔PIN** pairs, but **both are unlicensed** (`license: null`;
  one README admits Wikipedia scraping). Use them to **pick** PINs, then cite
  Census/ESIC. **Do not commit either CSV to the repo or redistribute it.**
  Restrict generated addresses to the **50 PINs both datasets agree on**.
- **MMC 10-digit `YYYYMMNNNN` format** — verified only as the portal's own UI
  placeholder `2023072365`. The `YYYY|MM|serial` split is my **inference**.
  Format the number correctly; do not claim you downloaded the register.

### DEAD ENDS — confirmed, do not retry blindly

| Target | Finding |
|---|---|
| **NABH downloadable accredited list** | **Does not exist in working form.** `international.nabh.co/frmViewAccreditedEntryLevelHosp.aspx` → 200 but body is `No Record`; two other guessed paths → 404. |
| **MMC public doctor register** | **No bulk access.** SPA + API at `api.maharashtramedicalcouncil.org.in/api/v1` (live, but route not found); legacy `frmrmplist.aspx` → 404. |
| **MCI (national) register** | Not probed. `UNVERIFIED`. |
| **ABDM sandbox synthetic records** | **Not downloadable.** Sandbox docs route → 503; gateway → 401; access needs health-tech-committee approval. Use `ABDM-wrapper` instead. |
| **HMIS aggregates** | Portal **login/OTP-gated**. Only NHM's per-state archives look open — probe next. |
| **data.gov.in resource downloads** | `api.data.gov.in` **timed out**; catalogue SSR contains no resource UUIDs; `backend/dms/v1/catalogs` → `/not-found`. Portal is real, access path unverified. |
| **Nagpur municipal ward list** | Not found. Do not invent ward names. |
| **Full age pyramid (C-13/C-14)** | Not in the PCA files — only 0–6. Need a different Census table or NFHS-5. |
| `sandbox.abdm.gov.in/docs/healthid` | 503 `Please make a valid request.` |
| `portal.nabh.co/frmViewAccreditedHospitals.aspx`, `/hospitals/accredited-hospitals` | 404 |
| `censusindia.gov.in/nada/index.php/catalog/study/PC11_PCA-2709` | 404 — the `/catalog/study/<id>` pattern does **not** resolve for general PCA; use `/catalog/<numeric-id>`. |

### Next probes worth doing (in priority order)

1. Extract and fetch the **NHM Maharashtra monitoring-report archive** from
   `nhm.gov.in/index1.php?lang=1&level=1&lid=205&sublinkid=112` → unlocks §7.
2. Probe the **Public Health Department Comprehensive Note PDF** (facility
   inventory: 10,766 sub-centres / 1,939 PHCs / 19 district hospitals etc.).
3. Open `smartcities.data.gov.in/cities/Nagpur` **in a browser** to enumerate the
   client-rendered Nagpur catalogues.
4. Find the real MMC doctor-search route by driving the SPA in a browser (then
   read only a handful of records for format confirmation — do not bulk-scrape;
   that is personal data).
5. Locate Census **C-13/C-14** age–sex tables for Nagpur for a true age pyramid.

---

## Warning about this workspace

While working, files under `research/scripts/` were **modified by something
other than me** — `verify_urls.py` grew from 3,800 to 8,034 bytes between my
read and my next command, `probe.py` was overwritten with content I had not
written, and new `probe_urls.py`, `taxonomies/`, `raw/`, `sources/`
directories appeared. One command returned a link-checker report over 45
unrelated URLs (paediatric BP guidelines, blood-group tables) that I never
requested.

Because of that, **all scripts cited in this document use the `in_*.py` prefix
and were re-verified immediately before execution**; the observed HTTP results
quoted above come from those runs. If you re-run anything, check the file hash
first — and keep new work under a distinct filename prefix to avoid collisions.