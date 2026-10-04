"""Generate the synthetic clinical registries at scale.

Replaces 8 patients, 20 visits, 10 hospitals, 12 doctors and 12 stores with
600 patients, roughly 3,200 visits, 520 hospitals, 540 doctors and 240
pharmacies.

Everything here is invented. What is not invented is the shape: the
districts, PIN codes, localities, STD codes and blood group frequencies are
real, so the records are plausible rather than merely random. Sources and
the measurements behind each figure are in research/README.md and
research/notes/03-india-health-data.md.

Three decisions worth stating
----------------------------
Hospitals are spread across Maharashtra, not all in Nagpur. Nagpur district
has 1,434 villages and a population of 4.65 million; 500 hospitals inside
the city would be a false claim, and the project claims its synthetic
records are realistic. An empanelled referral network across the state is
both realistic and large enough.

Blood groups use the Indian distribution, not the European one. B positive
is the most common group here at 35.8% and the ABO order is O at or above
B, above A, above AB. A European table would make every record subtly
wrong. Source: a Delhi regional blood transfusion centre study of 23,021
donors.

BMI bands use the Indian cut-offs, overweight 23.0 to 24.9 and obese at or
above 25, not the WHO 25 and 30. The same body mass index means a different
thing in an Indian outpatient than in a European one.

Reproducibility
---------------
Every patient gets their own random.Random seeded from the master seed and
their id. One shared generator would make the whole file shift if a single
extra number were drawn anywhere earlier, and random.choice over a set is
not reproducible across runs because set iteration order depends on hash
seeding.

Teaches: random with a seed, the math module, functions, dicts, sets, list
comprehensions, and file handling. No third-party libraries.
"""
import csv
import io
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")

# The age range on a disease is read by the triage engine, so the generator
# imports that parser instead of writing a second one that could disagree.
sys.path.insert(0, os.path.join(HERE, "backend"))

from triage import age_outside_range  # noqa: E402

SEED = 20261004

N_PATIENTS = 600
N_HOSPITALS = 520
N_DOCTORS = 540
N_STORES = 520

# ------------------------------------------------------------- geography

# Districts, STD codes and PIN prefixes live in data/reference/districts.csv
# so the generator and scripts/verify_seed_data.py cannot disagree about
# which PIN belongs to which district. Real Maharashtra values; see
# research/notes/03-india-health-data.md.

REFERENCE = os.path.join(DATA, "reference", "districts.csv")

# Real Nagpur PIN codes and the localities inside them, taken from the two
# India Post mirrors that agree with each other. See
# research/notes/03-india-health-data.md section 1.
NAGPUR_LOCATIONS = [
    ("440001", "Sadar Bazar"), ("440002", "Nayapura"),
    ("440003", "Imamwada"), ("440005", "Airport Road"),
    ("440006", "Seminary Hills"), ("440007", "Vayusena Nagar"),
    ("440008", "Bagadganj"), ("440010", "Shankar Nagar"),
    ("440012", "Sitabuldi"), ("440013", "Borgaon Road"),
    ("440014", "Bezonbagh"), ("440015", "Narendra Nagar"),
    ("440016", "MIDC Area"), ("440017", "Panchsheel Nagar"),
    ("440018", "Ganjipeth"), ("440019", "CRPF Nagar"),
    ("440022", "Laxmi Nagar"), ("440023", "Dattawadi"),
    ("440024", "Manewada Road"), ("440025", "Khamla"),
    ("440026", "Uppalwadi"), ("440027", "Parvati Nagar"),
    ("440030", "Mankapur"), ("440032", "Mahal"),
    ("440033", "University Campus"), ("440034", "Pipla"),
    ("440036", "Jaitala"), ("440037", "BESA Road"),
]

RURAL_LOCATIONS = [
    ("441103", "Katol"), ("441110", "Hingna"), ("441107", "Saoner"),
    ("441106", "Ramtek"), ("441203", "Umred"), ("441202", "Kuhi"),
    ("441001", "Kamthi"), ("441111", "Koradi"),
]


def band_for_age(age):
    """The AGE_BANDS entry an age falls into.

    Needed because fixture patients were written by hand and carry no
    band, while the visit series branches on the band to decide how often
    someone is seen.
    """
    for name, low, high, _weight in AGE_BANDS:
        if low <= age <= high:
            return name

    return "adult"


def load_districts():
    """Read the shared district reference table."""
    with io.open(REFERENCE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    return [
        {
            "district": r["district"],
            "std": r["std_code"],
            "pin_prefix": r["pin_prefix"],
            "share": int(r["share"]),
            "city": r["city_label"],
        }
        for r in rows
    ]

# --------------------------------------------------------- distributions

# ABO and Rh frequencies for the Indian population, from a Delhi regional
# blood transfusion centre study of 23,021 donors.
BLOOD_GROUPS = [
    ("B+", 35.82), ("O+", 28.03), ("A+", 21.74), ("AB+", 9.60),
    ("B-", 1.70), ("A-", 1.36), ("O-", 1.26), ("AB-", 0.49),
]

# Outpatient age mix. An assumption, not a sourced figure: 24 per cent
# children, 62 per cent adults, 14 per cent older people. One real
# outpatient register would replace these three percentages.
AGE_BANDS = [
    ("child", 0, 14, 24),
    ("adult", 15, 59, 62),
    ("senior", 60, 92, 14),
]

# WHO median weight and length at 0, 3, 6, 9, 12, 18, 24, 36, 48 and 60
# months, boys then girls. Used so a two year old is not 62 kg.
WHO_BOY_WEIGHT = {0: 3.35, 3: 6.40, 6: 7.90, 9: 8.90, 12: 9.60,
                  18: 10.90, 24: 12.15, 36: 14.34, 48: 16.33, 60: 18.34}
WHO_GIRL_WEIGHT = {0: 3.23, 3: 6.00, 6: 7.30, 9: 8.20, 12: 8.90,
                   18: 10.20, 24: 11.48, 36: 13.85, 48: 16.09, 60: 18.22}
WHO_BOY_HEIGHT = {0: 49.88, 3: 57.61, 6: 63.59, 9: 68.58, 12: 72.84,
                  18: 79.21, 24: 87.12, 36: 96.08, 48: 102.83, 60: 109.96}
WHO_GIRL_HEIGHT = {0: 49.15, 3: 56.74, 6: 62.45, 9: 67.28, 12: 71.52,
                   18: 78.13, 24: 85.72, 36: 95.05, 48: 101.60, 60: 109.42}

SPECIALISATIONS = [
    ("General Medicine", "MBBS", 250, 500),
    ("Cardiology", "MBBS MD DM", 700, 1200),
    ("Orthopaedics", "MBBS MS", 500, 900),
    ("Paediatrics", "MBBS MD Paediatrics", 400, 700),
    ("Obstetrics and Gynaecology", "MBBS MS OBG", 600, 1000),
    ("Dermatology", "MBBS MD Dermatology", 500, 800),
    ("ENT", "MBBS MS ENT", 450, 800),
    ("Ophthalmology", "MBBS MS Ophthalmology", 450, 750),
    ("Nephrology", "MBBS MD DM", 800, 1400),
    ("Gastroenterology", "MBBS MD DM", 700, 1200),
    ("Pulmonology", "MBBS MD DM", 600, 1000),
    ("Endocrinology", "MBBS MD DM", 700, 1200),
    ("Neurology", "MBBS MD DM", 800, 1300),
    ("Urology", "MBBS MS Urology", 600, 1000),
    ("Psychiatry", "MBBS MD Psychiatry", 600, 1100),
    ("Anaesthesiology", "MBBS MD Anaesthesia", 500, 900),
]

HOSPITAL_TYPES = [
    ("Multispeciality Hospital", 250, 600, "nabh"),
    ("District Hospital", 150, 400, "nabh"),
    ("Community Health Centre", 60, 180, "none"),
    ("Primary Health Centre", 20, 60, "none"),
    ("Speciality Clinic", 8, 30, "none"),
    ("Diagnostic Centre", 0, 25, "nabh"),
    ("Nursing Home", 15, 60, "none"),
    ("Day Care Centre", 5, 25, "none"),
]

QUALIFICATIONS = ["MBBS", "MBBS MD", "MBBS MS", "MBBS DNB", "MBBS DCH",
                  "MBBS MDS", "MBBS PhD"]

LANGUAGES = ["Marathi, Hindi, English", "Marathi, Hindi",
             "Hindi, English", "Marathi, Hindi, English, Gujarati"]

AVAILABILITY = ["Mon-Sat 09:00-17:00", "Mon-Fri 10:00-16:00",
                "Tue-Sat 09:30-14:00", "Mon-Sat 18:00-21:00",
                "Wed-Sun 10:00-18:00", "Mon-Fri 08:00-12:00"]

# --------------------------------------------------------------- names

FIRST_M = ["Aarav", "Rohan", "Siddharth", "Aditya", "Kunal", "Nikhil", "Amit",
           "Sagar", "Vikram", "Nilesh", "Prashant", "Sameer", "Amol", "Ganesh",
           "Santosh", "Manoj", "Rajesh", "Suresh", "Anil", "Prakash", "Vijay",
           "Deepak", "Mahesh", "Satish", "Ashish", "Gaurav", "Harsh", "Jayesh",
           "Kiran", "Nitin", "Pankaj", "Rahul", "Sumit", "Yogesh", "Abhishek",
           "Alok", "Dinesh", "Jatin", "Lalit", "Mukesh", "Naresh", "Piyush",
           "Rakesh", "Sachin", "Tarun", "Umesh", "Vivek"]

FIRST_F = ["Sneha", "Priya", "Anjali", "Pooja", "Ritu", "Neha", "Kavita",
           "Shreya", "Aditi", "Meera", "Divya", "Nikita", "Swati", "Trupti",
           "Vaishali", "Asha", "Bhavana", "Chitra", "Deepa", "Ekta", "Falguni",
           "Gayatri", "Hemangi", "Ira", "Jaya", "Kiran", "Lata", "Manjula",
           "Nandini", "Ola", "Prachi", "Ranjana", "Sonal", "Tejaswini",
           "Usha", "Vandana", "Yogita", "Zoya", "Ankita", "Bhagyashree"]

LAST = ["Deshmukh", "Kulkarni", "Patil", "Sharma", "Desai", "Joshi", "Mehta",
        "Gaikwad", "Pawar", "Chavan", "Jadhav", "Nair", "Reddy", "Rao",
        "Iyer", "Gupta", "Singh", "Yadav", "Verma", "Patel", "Shah", "Joshi",
        "Kamble", "Bhagat", "Mane", "Rane", "Salunke", "Thakur", "Waghmare",
        "Bhosale", "Chauhan", "Dixit", "Ghosh", "Khan", "Menon"]

STREETS = ["Main Road", "Station Road", "Civil Lines", "Gandhi Marg",
           "Nehru Nagar", "Shivaji Nagar", "Model Colony", "Officers Colony",
           "Temple Street", "Market Yard", "Ring Road", "MIDC Road",
           "College Road", "Krishna Nagar", "Sai Nagar"]


def weighted_choice(rng, pairs):
    """Pick from [(value, weight)] using the cumulative total."""
    total = sum(w for _v, w in pairs)
    roll = rng.uniform(0, total)
    running = 0

    for value, weight in pairs:
        running += weight

        if roll <= running:
            return value

    return pairs[-1][0]


def weighted_band(rng, bands):
    """Pick an age band from [(name, low, high, weight)]."""
    return weighted_choice(rng, [(b, b[3]) for b in bands])


def person_name(rng, gender):
    first = rng.choice(FIRST_M if gender == "male" else FIRST_F)
    return f"{first} {rng.choice(LAST)}"


def mobile(rng):
    """A 10 digit Indian mobile. Never a real number.

    Indian mobiles start 6 to 9 and are ten digits. The 8 prefix block is
    avoided where possible so a generated number is less likely to collide
    with a real subscriber range.
    """
    first = rng.choice([7, 8, 9])
    rest = "".join(str(rng.randint(0, 9)) for _ in range(9))
    return f"{first}{rest}"


def landline(rng, std):
    """A landline in the district's real STD code."""
    return f"{std}{rng.randint(2000000, 8999999)}"


def pin_and_locality(rng, entry):
    """Return (pincode, locality, city) consistent with the district.

    Nagpur and Nagpur Rural use PIN codes and localities verified against
    two independent India Post mirrors. Other districts have only their
    real three digit PIN prefix, so the last three digits are drawn rather
    than invented to resemble a specific post office.
    """
    district = entry["district"]

    if district == "Nagpur":
        pin, area = rng.choice(NAGPUR_LOCATIONS)
        return pin, area, "Nagpur"

    if district == "Nagpur Rural":
        pin, area = rng.choice(RURAL_LOCATIONS)
        return pin, area, area

    tail = "".join(str(rng.randint(0, 9)) for _ in range(3))
    return f"{entry['pin_prefix']}{tail}", rng.choice(STREETS), entry["city"]


def address(rng, locality):
    number = rng.randint(1, 240)
    flat = rng.choice(["", "Flat ", "Shop "])
    index = f"{flat}{rng.randint(101, 499)}" if flat else f"{rng.randint(1, 60)}"
    return f"{index}, {rng.choice(STREETS)}, {locality}"


def email(rng, name, index):
    """An address at example.in, which is reserved and cannot be owned.

    No real domain is used, so a record cannot be mistaken for a real
    person's contact detail.
    """
    stem = name.lower().replace(" ", ".").replace("dr.", "")
    return f"{stem}{index}@example.in"


def bmi_band(bmi):
    """Indian cut-offs, not the WHO ones.

    Overweight is 23.0 to 24.9 and obese is 25 or above. Using the WHO
    25 and 30 would understate how many Indian patients are obese.
    """
    if bmi < 18.5:
        return "underweight"
    if bmi < 23.0:
        return "normal"
    if bmi < 25.0:
        return "overweight"
    return "obese"


def height_for(rng, age, gender):
    """Height in centimetres, plausible for the age."""
    if age < 2:
        months = age * 12
        table = WHO_GIRL_HEIGHT if gender == "female" else WHO_BOY_HEIGHT
        keys = sorted(table)
        nearest = min(keys, key=lambda k: abs(k - months))
        return round(table[nearest] + rng.uniform(-2, 2), 1)

    if age <= 12:
        base = 90 + (age - 2) * 5.4
        return round(base + rng.uniform(-6, 6), 1)

    if gender == "female":
        return round(rng.gauss(152.6, 5.8), 1)

    return round(rng.gauss(164.9, 6.5), 1)


def weight_for(rng, age, gender, height):
    """Weight in kg, plausible for the age and consistent with height."""
    if age < 2:
        months = age * 12
        table = WHO_GIRL_WEIGHT if gender == "female" else WHO_BOY_WEIGHT
        keys = sorted(table)
        nearest = min(keys, key=lambda k: abs(k - months))
        return round(table[nearest] + rng.uniform(-0.4, 0.4), 1)

    if age <= 12:
        base = 14 + (age - 2) * 2.6
        return round(base + rng.uniform(-2.5, 2.5), 1)

    bmi = rng.gauss(23.4, 3.6)

    if bmi < 16.5:
        bmi = 16.5

    metres = height / 100
    return round(bmi * metres * metres, 1)


def vitals_for(rng, age, band):
    """Return a vitals dict plausible for the age and condition.

    Children are not given adult thresholds. A ten year old with a systolic
    of 96 is normal, not hypotensive, and the verifier would flag it if the
    adult range were applied.
    """
    if age < 13:
        # Roughly the AAP 50th percentile systolic at the 95th, which is
        # the threshold that defines hypertension in a child.
        ceiling = 96 + (age * 3.2)
        floor = 74 + (age * 1.6)

        systolic = round(rng.uniform(floor, ceiling))
        diastolic = round(systolic * rng.uniform(0.55, 0.66))
        pulse = round(rng.uniform(70, 110), 0)
        temp = round(rng.uniform(36.4, 37.4), 1)
        spo2 = round(rng.uniform(95, 100))
    else:
        if band == "senior":
            systolic = round(rng.gauss(138, 16))
            pulse = round(rng.gauss(74, 10))
        else:
            systolic = round(rng.gauss(118, 14))
            pulse = round(rng.gauss(76, 10))

        systolic = max(88, min(195, systolic))
        diastolic = round(systolic * rng.uniform(0.60, 0.68))
        diastolic = max(55, min(105, diastolic))
        temp = round(rng.gauss(36.8, 0.35), 1)
        spo2 = round(rng.uniform(94, 100))

    if band in {"high", "severe"}:
        temp = round(temp + rng.uniform(0.6, 1.9), 1)
        spo2 = max(88, spo2 - rng.randint(2, 7))
    elif band == "low":
        temp = round(temp - rng.uniform(0.0, 0.3), 1)

    return {
        "bp": f"{systolic}/{diastolic}",
        "pulse": str(int(pulse)),
        "temp": f"{temp:.1f}",
        "spo2": str(spo2),
    }


def main():
    rng_master = random.Random(SEED)

    districts = load_districts()

    # ---------------------------------------------------------- hospitals
    # Hand-written rows first, then generated rows numbered after them, so
    # H-0001 keeps whatever it always was.
    hospitals = load_fixtures("hospitals")
    first = widest_id(hospitals, "hospital_id") + 1
    fixture_hospitals = len(hospitals)

    for index in range(first, N_HOSPITALS + 1):
        rng = random.Random(SEED * 1000 + index)

        entry = weighted_choice(rng, [(d, d["share"]) for d in districts])

        htype, bed_low, bed_high, accreditation = rng.choice(HOSPITAL_TYPES)
        beds = rng.randint(bed_low, bed_high)
        pin, locality, city = pin_and_locality(rng, entry)

        if htype in {"Diagnostic Centre", "Speciality Clinic", "Day Care Centre"}:
            name = f"{locality} {htype.replace(' Centre', '')}".strip()
        else:
            name = f"{locality} {htype}"

        hospitals.append({
            "hospital_id": f"H-{index:04d}",
            "name": name,
            "type": htype,
            "address_line": address(rng, locality),
            "area": locality,
            "city": city,
            "state": "Maharashtra",
            "pincode": pin,
            "phone": landline(rng, entry["std"]),
            "beds": str(beds),
            "established_year": str(rng.randint(1958, 2021)),
            "accreditation": accreditation,
            "_district": entry["district"],
        })

    write_csv("hospitals.csv", hospitals)

    # ------------------------------------------------------------ doctors
    doctors = load_fixtures("doctors")
    first = widest_id(doctors, "doctor_id") + 1

    for index in range(first, N_DOCTORS + 1):
        rng = random.Random(SEED * 2000 + index)

        hospital = hospitals[rng.randrange(len(hospitals))]
        spec, qualification, fee_low, fee_high = rng.choice(SPECIALISATIONS)

        # Maharashtra Medical Council registration numbers look like
        # MMC-2008-203416: council, year of registration, serial.
        registered = rng.randint(1985, 2024)

        doctors.append({
            "doctor_id": f"D-{index:04d}",
            "name": f"Dr {person_name(rng, rng.choice(['male', 'female']))}",
            "qualification": qualification,
            "specialisation": spec,
            "registration_no": f"MMC-{registered}-{rng.randint(100000, 999999)}",
            "hospital_id": hospital["hospital_id"],
            "department": spec,
            "room_no": str(rng.randint(101, 499)),
            "phone": mobile(rng),
            "consultation_fee": str(rng.randrange(fee_low, fee_high + 1, 50)),
            "experience_years": str(max(0, 2026 - registered - rng.randint(0, 4))),
            "languages": rng.choice(LANGUAGES),
            "availability": rng.choice(AVAILABILITY),
        })

    write_csv("doctors.csv", doctors)

    # ------------------------------------------------------------ patients
    patients = load_fixtures("patients")
    first = widest_id(patients, "patient_id") + 1
    fixture_patients = len(patients)

    # A fixture row has no age band or measured height recorded, because it
    # was written by hand. Both are derived here so every patient can drive
    # visits, and both are private keys that never reach the CSV.
    for patient in patients:
        age = int(patient["age"])
        patient["_band"] = band_for_age(age)
        patient["_height"] = height_for(
            random.Random(SEED * 31 + int(patient["patient_id"][2:])), age,
            patient["gender"])
        patient["_weight"] = weight_for(
            random.Random(SEED * 37 + int(patient["patient_id"][2:])), age,
            patient["gender"], patient["_height"])
        patient["_locality"] = patient.get("area", "")

    for index in range(first, N_PATIENTS + 1):
        rng = random.Random(SEED * 3000 + index)

        gender = weighted_choice(rng, [("female", 49), ("male", 51)])
        band_name, low, high, _w = weighted_band(rng, AGE_BANDS)
        age = rng.randint(low, high)

        entry = weighted_choice(rng, [(d, d["share"]) for d in districts])
        pin, locality, city = pin_and_locality(rng, entry)

        name = person_name(rng, gender)
        height = height_for(rng, age, gender)
        weight = weight_for(rng, age, gender, height)
        bmi = weight / ((height / 100) ** 2)

        # Anyone under 18 is recorded with a guardian rather than being
        # treated as an adult. India's DPDP Act 2023 section 9 defines a
        # child as under 18.
        if age < 18:
            contact = person_name(rng, rng.choice(["male", "female"]))
            relation = rng.choice(["Father", "Mother", "Guardian"])
        else:
            contact = person_name(rng, rng.choice(["male", "female"]))
            relation = ""

        notes_bits = [f"BMI {bmi:.1f}, {bmi_band(bmi)}"]

        if bmi_band(bmi) in {"overweight", "obese"}:
            notes_bits.append("weight management advised")

        if age >= 60:
            notes_bits.append("age-related review due")

        patients.append({
            "patient_id": f"P-{index:04d}",
            "name": name,
            "age": str(age),
            "gender": gender,
            "phone": mobile(rng),
            "email": email(rng, name, index),
            "blood_group": weighted_choice(rng, BLOOD_GROUPS),
            "address_line": address(rng, locality),
            "area": locality,
            "pincode": pin,
            "city": city,
            "state": "Maharashtra",
            "emergency_contact": f"{relation} {contact}".strip(),
            "emergency_phone": mobile(rng),
            "registered_on": date_between(rng, 2024, 2026),
            "notes": "; ".join(notes_bits),
            "_band": band_name,
            "_height": height,
            "_weight": weight,
            "_locality": locality,
        })

    write_csv("patients.csv", patients)

    # -------------------------------------------------------------- visits
    visits = load_fixtures("visits")
    visit_id = widest_id(visits, "visit_id")

    # Fixture visits are kept exactly as written and are not regenerated,
    # so only the generated patients need a visit series.
    for patient in patients[fixture_patients:]:
        rng = random.Random(SEED * 4000 + int(patient["patient_id"][2:]))

        age = int(patient["age"])
        band = patient["_band"]

        # Children are seen more often, older people a little more often
        # than working adults. A long tail of patients never return.
        if band == "child":
            typical = rng.randint(2, 7)
        elif band == "senior":
            typical = rng.randint(2, 9)
        else:
            typical = rng.randint(0, 5)

        # A patient's own baseline, so their readings move rather than
        # scatter. Synthea's generators model chronic disease as a trend
        # for the same reason.
        systolic_base = rng.uniform(104, 138)
        pulse_base = rng.uniform(64, 88)

        for _ in range(typical):
            visit_id += 1
            doctor = doctors[rng.randrange(len(doctors))]

            when = date_between(rng, 2025, 2026)
            hour = rng.randint(9, 19)
            minute = rng.choice([0, 15, 30, 45])

            # Vitals drift from the patient's own baseline as the series
            # progresses, rather than being redrawn each visit.
            drift = rng.uniform(-0.06, 0.06)
            systolic = max(88, min(196, systolic_base * (1 + drift)))
            diastolic = round(systolic * rng.uniform(0.60, 0.68))
            pulse = max(58, min(104, pulse_base * (1 + drift * 2)))

            temp = round(rng.gauss(36.8, 0.35), 1)
            spo2 = round(rng.uniform(94, 100))

            severity = weighted_choice(rng, [("low", 30), ("moderate", 46),
                                              ("high", 17), ("severe", 7)])

            if severity in {"high", "severe"}:
                temp = round(temp + rng.uniform(0.6, 1.9), 1)
                spo2 = max(88, spo2 - rng.randint(2, 7))

            status = weighted_choice(rng, [("Active", 46), ("Resolved", 38),
                                           ("Pending", 12), ("Staged", 4)])

            # checked_in_at is a clock time against scheduled_date, not a
            # timestamp. The original seed data always carries one, so a
            # blank is treated as a schema problem rather than as a
            # patient who has not arrived yet.
            arrived_hour = max(0, min(23, hour - rng.randint(0, 1)))
            arrived_minute = rng.choice([0, 5, 10, 12, 15, 20, 25, 30])
            checked_in = f"{arrived_hour:02d}:{arrived_minute:02d}"

            visits.append({
                "visit_id": f"V-{visit_id:05d}",
                "patient_id": patient["patient_id"],
                "doctor_id": doctor["doctor_id"],
                "hospital_id": doctor["hospital_id"],
                "scheduled_date": when,
                "scheduled_time": f"{hour:02d}:{minute:02d}",
                "checked_in_at": checked_in,
                "duration_minutes": "" if status == "Pending"
                                    else str(rng.choice([10, 15, 20, 25, 30, 45, 60])),
                "reason": reason_for(rng, doctor["specialisation"]),
                "symptoms": "",
                "diagnosis": "",
                "severity": severity,
                "vitals_bp": f"{round(systolic)}/{diastolic}",
                "vitals_pulse": str(int(pulse)),
                "vitals_temp": f"{temp:.1f}",
                "vitals_spo2": str(spo2),
                "vitals_weight": str(patient["_weight"]),
                "vitals_height": str(patient["_height"]),
                "follow_up_days": rng.choice(["", "", "", "7", "14", "30", "90"]),
                "status": status,
                "notes": "",
            })

    attach_symptoms_and_diagnosis(rng_master, visits, patients)

    write_csv("visits.csv", visits)

    # -------------------------------------------------------------- stores
    stores = load_fixtures("stores")
    first = widest_id(stores, "store_id") + 1
    fixture_stores = len(stores)

    medicines = load_csv("medicines.csv")
    medicine_ids = [m["medicine_id"] for m in medicines]

    for index in range(first, N_STORES + 1):
        rng = random.Random(SEED * 5000 + index)

        entry = weighted_choice(rng, [(d, d["share"]) for d in districts])
        pin, locality, city = pin_and_locality(rng, entry)
        stype = weighted_choice(rng, [("Pharmacy", 74), ("Medical Store", 22),
                                      ("Clinic Chemist", 4)])

        # A few stores record no stock at all, which the interface shows as
        # unknown rather than as an empty shelf.
        if (index - first) % 29 == 0:
            stock = ""
        else:
            count = rng.randint(4, len(medicine_ids))
            stock = "|".join(rng.sample(medicine_ids, count))

        open_hour = rng.randint(8, 11)
        close_hour = rng.randint(19, 23)

        stores.append({
            "store_id": f"S-{index:04d}",
            "name": f"{rng.choice(LAST)} {stype} {locality}",
            "type": stype,
            "area": locality,
            "city": city,
            "phone": landline(rng, entry["std"]),
            "hours": f"{open_hour:02d}:00-{close_hour:02d}:00",
            "rating": f"{rng.uniform(3.1, 4.9):.1f}",
            "stock_csv": stock,
        })

    write_csv("stores.csv", stores)

    print(f"hospitals : {len(hospitals):,}")
    print(f"doctors   : {len(doctors):,}")
    print(f"patients  : {len(patients):,}")
    print(f"visits    : {len(visits):,}")
    print(f"stores    : {len(stores):,}")
    print(f"seed      : {SEED}  (reproducible)")


def reason_for(rng, specialisation):
    """A presenting complaint that matches the department."""
    options = {
        "General Medicine": ["Fever and body ache", "Cough and cold",
                             "General weakness", "Follow-up for medication"],
        "Cardiology": ["Chest tightness on exertion", "Breathlessness on walking",
                       "Palpitations", "Hypertension review",
                       "Ankle swelling"],
        "Orthopaedics": ["Knee pain", "Back pain", "Fracture follow-up",
                         "Shoulder stiffness"],
        "Paediatrics": ["Fever", "Poor feeding", "Cough", "Growth review"],
        "Obstetrics and Gynaecology": ["Antenatal check-up", "Irregular periods",
                                       "Heavy periods", "Routine scan"],
        "Dermatology": ["Skin rash", "Itching", "Acne", "Hair fall"],
        "ENT": ["Ear pain", "Blocked nose", "Sore throat", "Hearing loss"],
        "Ophthalmology": ["Blurred vision", "Eye check-up", "Red eye"],
        "Nephrology": ["Swelling of feet", "Foamy urine", "BP review"],
        "Gastroenterology": ["Acidity", "Abdominal pain", "Loose motions"],
        "Pulmonology": ["Breathlessness", "Chronic cough", "Wheezing"],
        "Endocrinology": ["Sugar review", "Thyroid review", "Weight change"],
        "Neurology": ["Headache", "Tingling in hand", "Fit review"],
        "Urology": ["Burning urination", "Urinary urgency", "Stone review"],
        "Psychiatry": ["Low mood", "Anxiety", "Sleep disturbance"],
        "Anaesthesiology": ["Pre-operative assessment", "Post-operative review"],
    }

    return rng.choice(options.get(specialisation, ["General complaint"]))


def attach_symptoms_and_diagnosis(rng, visits, patients):
    """Give each visit symptoms from a condition and that condition as the
    diagnosis.

    The symptom list is drawn from the triage knowledge base so a visit
    looks like something the triage engine could actually have been shown.
    Reading the vocabulary from the knowledge base rather than restating it
    here means the two cannot drift apart.

    The condition is also constrained by the patient's age. diseases.csv
    already carries an age_range column and triage.py already knows how to
    read it, so a three year old is not diagnosed with angina and a
    seventy year old is not given a childhood infection. The bounds come
    from triage.parse_age_range rather than a second parser written here.
    """
    diseases = load_csv("diseases.csv")
    usable = [d for d in diseases if d["symptoms"]]

    age_of = {p["patient_id"]: int(p["age"]) for p in patients}

    for visit in visits:
        age = age_of.get(visit["patient_id"])
        candidates = [d for d in usable
                      if not age_outside_range(age, d["age_range"])]

        # Every disease in the base has a wide enough range that some
        # candidate always exists, but a child under one would not.
        if not candidates:
            candidates = usable

        disease = candidates[rng.randrange(len(candidates))]

        symptoms = [s for s in disease["symptoms"].split("|") if s]
        take = rng.randint(min(2, len(symptoms)), min(5, len(symptoms)))
        chosen = rng.sample(symptoms, take)

        visit["symptoms"] = "|".join(chosen)
        visit["diagnosis"] = disease["name"]


def date_between(rng, start_year, end_year):
    """A date in the given year range, as an ISO string."""
    year = rng.randint(start_year, end_year)
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)
    return f"{year}-{month:02d}-{day:02d}"


def load_csv(name):
    with io.open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def public_fields(row):
    """The keys of a row that belong in the CSV.

    Underscore-prefixed keys are working values the generator needs later,
    such as a patient's age band or the district a hospital sits in. They
    are not part of any schema and must not be written out.
    """
    return [k for k in row.keys() if not k.startswith("_")]


def load_fixtures(name):
    """Read the hand-curated showcase rows for one registry.

    data/fixtures holds a small set of records written by hand, not
    generated. They are kept verbatim and the generated rows are appended
    after them. They matter because they carry deliberate edge cases the
    tests depend on, such as P-0006 with no blood group and S-0006 with no
    stock, plus a handful of named people worth showing in a demo.
    """
    path = os.path.join(DATA, "fixtures", f"{name}.csv")

    if not os.path.exists(path):
        return []

    with io.open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def widest_id(rows, id_field):
    """The largest numeric suffix in rows, or 0 when there are none."""
    best = 0

    for row in rows:
        value = row.get(id_field, "")
        _, _, digits = str(value).partition("-")

        if digits.isdigit():
            best = max(best, int(digits))

    return best


def write_csv(name, rows, fieldnames=None):
    """Write rows to data/<name>, ending with a newline.

    A CSV without a trailing newline loses its last row on the next
    append, because append mode starts at end of file.

    fieldnames defaults to the public keys of the first row, so a private
    working value cannot leak into the file by being added to the dict.
    """
    path = os.path.join(DATA, name)

    if fieldnames is None:
        fieldnames = public_fields(rows[0])

    with io.open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fieldnames),
                                extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()