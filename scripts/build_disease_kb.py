"""Build data/diseases.csv, the triage knowledge base.

Every ICD-10-CM code here is checked against data/icd10cm_codes.csv,
which is generated from the CDC/NCHS FY2027 release. If a code in this
file is not in that classification the build fails. That is the point:
the codes are real and cannot quietly rot.

What is real and what is not
----------------------------
The ICD-10-CM codes, the condition names and the chapter groupings are
real and citable: a US Government work in the public domain.

The symptom profiles are not. No open dataset publishes
symptom-to-disease links for common outpatient conditions.
research/README.md records why the obvious candidate, HPOA, was rejected
with measured counts: searching it for "cough" returns nothing, and its
top "symptoms" are inheritance modes such as Autosomal recessive
inheritance.

So the symptom lists are written by hand against standard clinical
presentations, and every row carries symptom_source=curated so nothing
downstream can mistake them for sourced data. The real code lets a reader
check the diagnosis against the classification while understanding that
the reasoning shown to the user is illustrative.

Teaches: functions, dicts, sets, list comprehensions, file handling,
f-strings, and set difference for validating the vocabulary.
"""
import csv
import io
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICD_CODES = os.path.join(HERE, "data", "icd10cm_codes.csv")
TARGET = os.path.join(HERE, "data", "diseases.csv")

# --------------------------------------------------------------- symptoms

# The controlled vocabulary. A condition may only use symptoms from this
# set, because triage is set intersection and an off-vocabulary term can
# never match anything a patient types.
#
# The wording is what a patient would say, not what a clinician writes.
VOCABULARY = {
    # general
    "fever", "high fever", "low-grade fever", "chills", "rigors",
    "fatigue", "weakness", "malaise", "weight loss", "weight gain",
    "loss of appetite", "night sweats", "sweating", "tremor",
    "pale skin", "pale stools", "bruising", "bleeding gums", "jaundice",
    # head and neck
    "headache", "headache with aura", "dizziness", "dizziness on standing",
    "fainting", "seizure", "confusion", "memory loss", "slurred speech",
    "weakness in one limb", "numbness", "tingling", "stiffness",
    # eyes
    "eye pain", "red eye", "itching", "watering eyes", "dry eyes",
    "blurred vision", "light sensitivity", "halos around lights",
    "double vision", "loss of vision",
    # ears and throat
    "ear pain", "hearing loss", "ear discharge", "ringing in ears",
    "sore throat", "swollen glands", "mouth ulcers", "bad breath",
    "gum bleeding", "toothache", "facial pain", "painful chewing",
    # nose and airway
    "runny nose", "nasal congestion", "sneezing", "nosebleed",
    "cough", "dry cough", "productive cough", "hoarseness",
    "breathlessness", "breathlessness on exertion", "wheezing",
    "shortness of breath on lying flat",
    # chest and cardiovascular
    "chest pain", "chest tightness", "palpitations", "swollen ankles",
    "swelling of feet", "cold sweat", "pain",
    # abdomen and digestion
    "abdominal pain", "upper abdominal pain", "lower abdominal pain",
    "nausea", "vomiting", "diarrhoea", "bloating", "constipation",
    "heartburn", "indigestion", "difficulty swallowing", "blood in stool",
    "mucus in stool", "jaundice",
    # urinary and reproductive
    "frequent urination", "painful urination", "passing blood in urine",
    "nocturia", "urinary urgency", "weak stream", "incontinence",
    "pelvic pain", "painful periods", "excessive periods",
    "irregular periods", "missed period", "breast pain", "breast lump",
    "low libido",
    # musculoskeletal
    "back pain", "lower back pain", "neck pain", "knee pain", "joint pain",
    "joint swelling", "muscle ache", "body ache", "crepitus",
    "morning stiffness", "tenderness", "hand pain", "night pain",
    "slowness of movement",
    # skin
    "rash", "itching", "redness", "skin scaling", "dry skin", "pimples",
    "bruising", "hair loss", "cold sores", "blisters", "discharge",
    # mental health and general neurology
    "anxiety", "low mood", "sleep disturbance", "poor concentration",
    "irritability", "restlessness", "depression",
    # metabolic
    "excessive thirst", "excessive hunger", "cold intolerance",
    "heat intolerance", "dizziness on standing",
    # paediatric
    "feeding difficulty", "failure to thrive", "irritability",
    # sensory
    "loss of smell", "loss of taste", "tingling",
}

# ------------------------------------------------------------- conditions
#
# Each entry is:
#   ICD-10-CM code, severity, symptoms, medication, dosage,
#   usual age range, contraindications
#
# Severity is triage urgency, not likelihood: how quickly this needs
# seeing. Most rows sit at moderate on purpose, because colouring
# everything communicates nothing.

CONDITIONS = [
    # --- respiratory and upper airway ---------------------------------
    ("J00", "low", "runny nose|sneezing|nasal congestion|sore throat|fatigue|headache|low-grade fever",
     "Paracetamol and rest", "500 mg as needed, maximum 4 g daily", "0-99", "liver disease"),
    ("J02", "moderate", "sore throat|fever|swollen glands|headache|difficulty swallowing",
     "Paracetamol and fluids", "500 mg four times daily", "3-99", "liver disease"),
    ("J03", "moderate", "sore throat|fever|swollen glands|difficulty swallowing|headache",
     "Phenoxymethylpenicillin", "500 mg three times daily for 7 days", "3-99", "penicillin allergy"),
    ("J06", "low", "runny nose|sore throat|cough|fever|fatigue|headache",
     "Paracetamol and rest", "500 mg as needed", "0-99", "liver disease"),
    ("J20", "moderate", "cough|productive cough|chest pain|fever|breathlessness|fatigue",
     "Amoxicillin", "500 mg three times daily for 5 days", "5-99", "penicillin allergy"),
    ("J21", "moderate", "wheezing|breathlessness|cough|fever|feeding difficulty",
     "Salbutamol inhaler", "two puffs four hourly", "0-2", ""),
    ("J18", "high", "fever|cough|productive cough|breathlessness|chest pain|fatigue|confusion",
     "Amoxicillin", "500 mg three times daily for 7 days", "0-99", "penicillin allergy"),
    ("J44", "moderate", "breathlessness on exertion|productive cough|wheezing|fatigue|cough",
     "Salbutamol and inhaled corticosteroid", "two puffs four hourly, plus preventer", "40-99", "pregnancy"),
    ("J45", "moderate", "wheezing|breathlessness|breathlessness on exertion|chest tightness|cough|sleep disturbance",
     "Salbutamol and inhaled corticosteroid", "two puffs as needed, plus preventer", "1-99", ""),
    ("J47", "moderate", "productive cough|breathlessness|fever|wheezing|fatigue",
     "Antibiotic only if infective", "amoxicillin 500 mg three times daily", "18-99", "penicillin allergy"),
    ("J38", "moderate", "sore throat|hoarseness|fever|ear pain|difficulty swallowing",
     "Paracetamol and voice rest", "500 mg four times daily", "5-99", "liver disease"),
    ("R05", "moderate", "cough|productive cough|dry cough|breathlessness|chest pain|fever",
     "Treat the cause, avoid routine antibiotic", "not indicated unless bacterial", "0-99", ""),

    # --- infectious ---------------------------------------------------
    ("A09", "moderate", "diarrhoea|abdominal pain|vomiting|nausea|fever|weakness",
     "ORS and zinc", "ORS after each loose stool, zinc 20 mg daily", "0-99", ""),
    ("A15", "high", "cough|productive cough|fever|weight loss|fatigue|night sweats|breathlessness",
     "Rifampicin, isoniazid, pyrazinamide", "weight-based regimen, directly observed", "0-99", "liver disease"),
    ("A19", "severe", "high fever|rigors|breathlessness|confusion|weight loss|night sweats",
     "Urgent admission", "inpatient management", "0-99", ""),
    ("A37", "moderate", "cough|vomiting|breathlessness|fever|fatigue|feeding difficulty",
     "Azithromycin", "500 mg daily for 5 days", "0-99", ""),
    ("A90", "high", "high fever|body ache|joint pain|headache|nausea|rash|vomiting",
     "Paracetamol and oral fluids", "500 mg four times daily, avoid NSAIDs", "0-99", "pregnancy"),
    ("A91", "severe", "high fever|vomiting|bleeding gums|bruising|nosebleed|rash|weakness",
     "Urgent admission, IV fluids", "inpatient management", "0-99", ""),
    ("B54", "high", "high fever|rigors|chills|headache|body ache|vomiting|nausea|fatigue",
     "Artemether-lumefantrine", "weight-based course over 3 days", "0-99", "pregnancy"),
    ("A01", "high", "high fever|body ache|headache|abdominal pain|constipation|vomiting|fatigue",
     "Azithromycin", "500 mg daily for 7 days", "0-99", ""),
    ("A92", "moderate", "high fever|joint pain|body ache|headache|rash|fatigue",
     "Paracetamol and rest", "500 mg four times daily", "0-99", "pregnancy"),
    ("B05", "moderate", "high fever|rash|runny nose|cough|red eye|irritability|fatigue",
     "Paracetamol, notify and isolate", "500 mg four times daily", "0-99", ""),
    ("B34", "low", "fever|body ache|fatigue|headache|runny nose|cough",
     "Paracetamol and rest", "500 mg as needed, maximum 4 g daily", "0-99", "liver disease"),
    ("L08", "low", "redness|itching|discharge|swelling of feet",
     "Topical antibiotic and hygiene", "mupirocin twice daily for 5 days", "0-99", ""),
    ("B01", "moderate", "fever|body ache|itching|blisters|pain|headache",
     "Aciclovir", "800 mg five times daily for 7 days", "0-99", "kidney disease"),
    ("A60", "moderate", "blisters|pain|itching|redness|discharge|fever",
     "Aciclovir and review", "200 mg five times daily", "13-99", "kidney disease"),

    # --- endocrine and metabolic --------------------------------------
    ("E11", "moderate", "excessive thirst|frequent urination|weight loss|fatigue|blurred vision|poor concentration|night sweats",
     "Metformin", "start 500 mg once daily with food, titrate", "18-99", "kidney disease"),
    ("E10", "high", "excessive thirst|frequent urination|weight loss|fatigue|nausea|vomiting|abdominal pain",
     "Insulin", "basal-bolus, dose titrated to readings", "1-99", ""),
    ("E03", "low", "fatigue|weight gain|cold intolerance|constipation|dry skin|hair loss|poor concentration|slurred speech",
     "Levothyroxine", "start 50 micrograms daily, titrate on TSH", "18-99", "adrenal crisis"),
    ("E05", "moderate", "weight loss|palpitations|heat intolerance|anxiety|sweating|tremor|sleep disturbance",
     "Carbimazole", "5 to 10 mg daily, titrate on thyroid function", "18-99", "pregnancy"),
    ("E66", "moderate", "weight gain|breathlessness on exertion|joint pain|sleep disturbance|poor concentration",
     "Weight management and metformin", "500 mg twice daily with meals", "18-99", "kidney disease"),
    ("E78", "moderate", "chest pain|fatigue|poor concentration|upper abdominal pain|joint pain",
     "Atorvastatin", "10 to 20 mg once daily", "18-99", "pregnancy"),
    ("E86", "moderate", "vomiting|diarrhoea|passing blood in urine|weakness|fainting|dizziness on standing",
     "Oral rehydration salts", "replace the measured deficit over 4 hours", "0-99", ""),
    ("E87", "high", "muscle ache|weakness|palpitations|fatigue|numbness|abdominal pain",
     "Potassium chloride", "replace per serum potassium", "0-99", "kidney disease"),
    ("R73", "moderate", "excessive thirst|frequent urination|weight loss|fatigue|poor concentration",
     "Fasting glucose, then refer", "screen for diabetes", "18-99", ""),

    # --- cardiovascular -------------------------------------------------
    ("I10", "moderate", "headache|dizziness|blurred vision|chest pain|breathlessness|palpitations",
     "Amlodipine and/or a thiazide", "amlodipine 5 mg daily", "18-99", "pregnancy"),
    ("I20", "high", "chest pain|breathlessness on exertion|fatigue|palpitations|cold sweat",
     "Aspirin, statin, beta blocker", "aspirin 75 mg daily, titrate statin", "30-99", "active bleeding"),
    ("I21", "severe", "chest pain|breathlessness|cold sweat|nausea|vomiting|fainting",
     "Aspirin and urgent transfer", "chew 300 mg, transfer immediately", "18-99", "active bleeding"),
    ("I48", "moderate", "palpitations|breathlessness|fatigue|dizziness|chest pain|poor concentration",
     "Rate control and anticoagulation", "dose adjusted to stroke risk", "18-99", "pregnancy"),
    ("I50", "high", "breathlessness|breathlessness on exertion|swollen ankles|fatigue|shortness of breath on lying flat",
     "Furosemide and ACE inhibitor", "furosemide 40 mg daily, titrate", "18-99", "pregnancy"),
    ("I95", "moderate", "dizziness on standing|fainting|fatigue|dizziness|weakness|poor concentration",
     "Review antihypertensives and fluids", "reduce dose and reassess", "18-99", ""),

    # --- ear, nose and throat ---------------------------------------------
    ("H66", "moderate", "ear pain|hearing loss|fever|ear discharge|irritability|sleep disturbance",
     "Amoxicillin", "500 mg three times daily for 7 days", "0-99", "penicillin allergy"),
    ("H81", "moderate", "ringing in ears|hearing loss|dizziness|nausea|vomiting|ear pain",
     "Short-course diuretic and refer", "symptom relief, ENT if persistent", "30-99", "pregnancy"),
    ("H10", "moderate", "red eye|eye pain|itching|watering eyes|blurred vision|light sensitivity",
     "Antihistamine drops", "lidoflazine drops", "0-99", ""),
    ("H25", "moderate", "blurred vision|eye pain|headache|halos around lights|light sensitivity",
     "Urgent ophthalmology referral", "same day review", "50-99", ""),
    ("H52", "low", "blurred vision|eye pain|fatigue|headache|dry eyes",
     "Corrective lenses and review", "refraction test", "18-99", ""),

    # --- digestive ---------------------------------------------------------
    ("K21", "moderate", "heartburn|indigestion|difficulty swallowing|upper abdominal pain|nausea|cough",
     "Pantoprazole", "40 mg once daily before food", "18-99", ""),
    ("K30", "moderate", "upper abdominal pain|indigestion|bloating|nausea|vomiting",
     "Pantoprazole and prokinetic", "pantoprazole 40 mg daily", "18-99", ""),
    ("K52", "low", "upper abdominal pain|nausea|bloating|heartburn|indigestion|diarrhoea",
     "Antacid and PPI", "pantoprazole 20 mg daily", "18-99", ""),
    ("K58", "moderate", "abdominal pain|bloating|diarrhoea|constipation|mucus in stool",
     "Fibre and antispasmodic", "dicyclomine 10 mg three times daily", "18-99", "glaucoma"),
    ("K59", "moderate", "constipation|abdominal pain|bloating|nausea",
     "Bulk laxative", "ispaghula husk with adequate fluid", "18-99", "bowel obstruction"),
    ("K70", "moderate", "nausea|vomiting|upper abdominal pain|jaundice|weight loss|swollen ankles",
     "Stop alcohol and refer", "nutritional support, hepatology referral", "30-99", ""),
    ("K04", "moderate", "toothache|facial pain|ear pain|fever|difficulty swallowing",
     "Analgesia then dental referral", "ibuprofen 400 mg three times daily", "5-99", "ulcer"),
    ("K05", "moderate", "gum bleeding|bad breath|painful chewing|toothache",
     "Scaling and oral hygiene", "chlorhexidine mouthwash", "18-99", ""),
    ("K80", "moderate", "upper abdominal pain|nausea|vomiting|fatigue|indigestion",
     "Analgesia and surgical review", "diclofenac 50 mg three times daily", "30-99", "ulcer"),
    ("K922", "high", "blood in stool|vomiting|dizziness on standing|fatigue|pale skin|weakness",
     "Urgent endoscopy, IV fluids", "admit if haemodynamic compromise", "18-99", ""),
    ("K920", "high", "vomiting|upper abdominal pain|weakness|dizziness on standing|fatigue",
     "Urgent endoscopy", "same day review", "18-99", ""),

    # --- musculoskeletal ------------------------------------------------------
    ("M54", "moderate", "lower back pain|back pain|stiffness|body ache|tingling|morning stiffness",
     "Physiotherapy and NSAID", "diclofenac 50 mg three times daily", "18-99", "kidney disease"),
    ("M17", "moderate", "knee pain|joint swelling|stiffness|joint pain|crepitus|morning stiffness",
     "Topical NSAID and physiotherapy", "diclofenac gel to the knee", "45-99", "ulcer"),
    ("M10", "high", "joint pain|joint swelling|redness|fever|tenderness",
     "Colchicine then allopurinol", "colchicine 500 micrograms three times daily", "30-99", "kidney disease"),
    ("M06", "moderate", "joint swelling|joint pain|stiffness|morning stiffness|fatigue|fever",
     "DMARD under rheumatology", "methotrexate with folic acid", "20-99", "pregnancy"),
    ("M79", "low", "muscle ache|body ache|joint pain|fatigue|headache|tenderness",
     "Rest, hydration, NSAID", "paracetamol 500 mg as needed", "18-99", "liver disease"),
    ("M25", "low", "joint pain|joint swelling|stiffness|tenderness|morning stiffness",
     "Physiotherapy and topical NSAID", "diclofenac gel", "18-99", "ulcer"),
    ("M62", "moderate", "muscle ache|weakness|fatigue|body ache|tenderness",
     "Physiotherapy and review", "stretching programme", "18-99", ""),

    # --- mental health ---------------------------------------------------------
    ("F32", "moderate", "low mood|anxiety|sleep disturbance|poor concentration|fatigue|loss of appetite",
     "Sertraline and cognitive therapy", "start 25 mg daily, titrate", "13-99", "pregnancy"),
    ("F41", "moderate", "anxiety|sleep disturbance|poor concentration|palpitations|muscle ache|dizziness|restlessness",
     "Cognitive therapy, SSRI if severe", "sertraline 25 mg daily", "13-99", ""),
    ("F43", "moderate", "anxiety|sleep disturbance|poor concentration|headache|chest pain|restlessness",
     "CBT and relaxation training", "no drug first line", "18-99", ""),
    ("G47", "moderate", "sleep disturbance|anxiety|fatigue|poor concentration|headache|irritability",
     "Sleep hygiene, short melatonin course", "melatonin 3 mg before bed", "18-99", ""),

    # --- neurology ---------------------------------------------------------------
    ("G43", "moderate", "headache|nausea|blurred vision|light sensitivity|neck pain|vomiting",
     "Sumatriptan and propranolol", "sumatriptan 50 mg at onset", "12-99", "heart disease"),
    ("G40", "moderate", "seizure|confusion|fainting|memory loss|headache|weakness in one limb",
     "Levetiracetam", "start 500 mg twice daily", "0-99", "kidney disease"),
    ("G20", "moderate", "tremor|slowness of movement|stiffness|poor concentration|depression|slurred speech",
     "Levodopa-carbidopa", "titrated to response", "50-99", "psychosis"),
    ("G56", "moderate", "numbness|tingling|hand pain|night pain|weakness in one limb",
     "Night splint then steroid injection", "splint at night", "30-99", ""),

    # --- renal and urinary -----------------------------------------------------------
    ("N20", "high", "upper abdominal pain|nausea|vomiting|fever|passing blood in urine|restlessness",
     "Analgesia, imaging and referral", "diclofenac 75 mg IM, admit if septic", "20-99", "kidney disease"),
    ("N39", "moderate", "painful urination|frequent urination|urinary urgency|lower abdominal pain|fever",
     "Nitrofurantoin", "100 mg twice daily for 7 days", "12-99", "kidney disease"),
    ("N40", "moderate", "frequent urination|nocturia|urinary urgency|weak stream|poor concentration",
     "Tamsulosin", "0.4 mg once daily at night", "50-99", "liver disease"),
    ("N63", "moderate", "pelvic pain|painful urination|frequent urination|fatigue|lower abdominal pain",
     "Antibiotic course and review", "doxycycline 100 mg twice daily", "30-99", "pregnancy"),
    ("N04", "moderate", "swelling of feet|swollen ankles|fatigue|nausea|itching|poor concentration",
     "Nephrology referral", "dietary sodium restriction", "18-99", ""),

    # --- women's health ---------------------------------------------------------------
    ("N92", "moderate", "excessive periods|fatigue|bruising|pale skin|dizziness on standing",
     "Iron salts and tranexamic acid", "ferrous sulphate with vitamin C", "12-55", ""),
    ("D25", "moderate", "excessive periods|pelvic pain|lower back pain|fatigue|painful periods",
     "NSAID and tranexamic acid", "mefenamic acid 500 mg three times daily", "18-55", "ulcer"),
    ("N80", "moderate", "pelvic pain|painful periods|painful urination|lower abdominal pain|bloating",
     "NSAID and hormonal therapy", "mefenamic acid during the period", "18-45", "ulcer"),
    ("N61", "moderate", "breast pain|breast lump|fever|redness|swelling of feet",
     "NSAID, antibiotics if infective", "paracetamol and review", "18-99", "ulcer"),
    ("N91", "moderate", "irregular periods|bleeding gums|bruising|fatigue|missed period",
     "Assess cycle, then hormonal therapy", "review after 3 cycles", "12-50", ""),

    # --- skin and soft tissue ------------------------------------------------------------
    ("L20", "moderate", "rash|itching|redness|skin scaling|dry skin|sleep disturbance",
     "Emollient and topical steroid", "moderate steroid twice daily, then wean", "0-99", "fungal infection"),
    ("L40", "low", "rash|skin scaling|redness|itching",
     "Topical steroid and vitamin D analogue", "calcipotriol with a potent steroid", "18-99", ""),
    ("L30", "moderate", "rash|itching|redness|skin scaling|dry skin",
     "Topical antifungal", "clotrimazole twice daily for 2 to 4 weeks", "0-99", "pregnancy"),
    ("L70", "low", "pimples|redness|itching",
     "Topical retinoid and benzoyl peroxide", "adapalene at night", "12-99", "pregnancy"),
    ("L65", "moderate", "hair loss|itching|redness|skin scaling",
     "Topical steroid, refer if scarring", "clobetasol scalp solution", "18-99", ""),
    ("L53", "low", "rash|redness|itching|skin scaling",
     "Emollient and antihistamine", "cetirizine 10 mg daily", "0-99", ""),

    # --- symptoms as the coded presentation -------------------------------------------------
    ("R50", "low", "fever|chills|body ache|fatigue|headache|nausea",
     "Paracetamol and fluids", "500 mg four times daily", "0-99", "liver disease"),
    ("R51", "moderate", "headache|nausea|dizziness|blurred vision|fatigue|neck pain",
     "Paracetamol, review if persistent", "500 mg four times daily", "0-99", "liver disease"),
    ("R53", "low", "fatigue|weakness|poor concentration|sleep disturbance|pale skin|palpitations",
     "Screen for anaemia, thyroid, diabetes", "investigate before treating", "0-99", ""),
    ("R10", "moderate", "lower abdominal pain|nausea|vomiting|diarrhoea|fever|abdominal pain",
     "Paracetamol, assess for surgical cause", "500 mg four times daily", "0-99", "liver disease"),
    ("R21", "low", "rash|itching|redness|fever",
     "Antihistamine and review", "cetirizine 10 mg daily", "0-99", ""),
    ("R31", "moderate", "passing blood in urine|painful urination|frequent urination|fatigue",
     "Urgent investigation", "same day review", "0-99", ""),
    ("R42", "moderate", "dizziness|fainting|chest pain|palpitations|fatigue",
     "Check lying and standing blood pressure", "orthostatic review", "0-99", ""),
    ("R55", "moderate", "dizziness on standing|fainting|weakness|poor concentration",
     "Review antihypertensives and hydration", "reduce dose and reassess", "18-99", ""),
]


def main():
    if not os.path.exists(ICD_CODES):
        raise SystemExit(
            f"missing {ICD_CODES}\n"
            f"build it first: python scripts/build_icd10cm_registry.py"
        )

    # Every code used must exist in the real classification.
    real_codes = set()

    with io.open(ICD_CODES, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            real_codes.add(row["code"])

    rows = []
    problems = []
    seen_codes = set()

    for code, severity, symptoms, medication, dosage, age_range, contraindications in CONDITIONS:
        if code not in real_codes:
            problems.append(f"{code} is not an ICD-10-CM code")

        if code in seen_codes:
            problems.append(f"{code} appears twice")

        seen_codes.add(code)

        used = {s.strip() for s in symptoms.split("|") if s.strip()}
        unknown = used - VOCABULARY

        if unknown:
            problems.append(f"{code} uses off-vocabulary symptoms: "
                            f"{', '.join(sorted(unknown))}")

        if len(used) < 3:
            problems.append(f"{code} has only {len(used)} symptoms, "
                            f"too few to be distinguishable")

        if severity not in {"low", "moderate", "elevated", "high", "severe"}:
            problems.append(f"{code} has unknown severity {severity!r}")

        rows.append({
            "disease_id": f"ICD-{code}",
            "icd10_code": code,
            "name": "",
            "severity": severity,
            "symptoms": symptoms,
            "medication": medication,
            "dosage": dosage,
            "age_range": age_range,
            "contraindications": contraindications,
            "symptom_source": "curated",
        })

    if problems:
        print("BUILD FAILED")
        for problem in problems:
            print(f"  - {problem}")
        raise SystemExit(1)

    # Take the condition name from the classification, not from this file,
    # so the name shown to the user is the official one.
    names = {}

    with io.open(ICD_CODES, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            names[row["code"]] = row["description"]

    for row in rows:
        row["name"] = names[row["icd10_code"]]

    fieldnames = ["disease_id", "icd10_code", "name", "severity", "symptoms",
                  "medication", "dosage", "age_range", "contraindications",
                  "symptom_source"]

    with io.open(TARGET, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    vocabulary_used = set()

    for row in rows:
        vocabulary_used |= {s.strip() for s in row["symptoms"].split("|") if s.strip()}

    print(f"wrote {TARGET}")
    print(f"  conditions          : {len(rows):,}")
    print(f"  distinct ICD codes  : {len(seen_codes):,}")
    print(f"  vocabulary in use   : {len(vocabulary_used)} of {len(VOCABULARY)}")
    print(f"  codes verified      : all against data/icd10cm_codes.csv")


if __name__ == "__main__":
    main()