"""Data classes for Meridian records.

Taught concepts: classes, __init__, methods, self, default arguments,
static methods, list and dict handling.

Rule enforced here: an unfilled field is the empty string "" and never
"N/A", "unknown" or a made-up default. See spec section 4.2.
"""


class Patient:
    """One row of data/patients.csv."""

    FIELDS = [
        "patient_id", "name", "age", "gender", "phone", "email",
        "blood_group", "address_line", "area", "pincode", "city", "state",
        "emergency_contact", "emergency_phone", "registered_on", "notes",
    ]

    def __init__(self, patient_id, name, age="", gender="", phone="",
                 email="", blood_group="", address_line="", area="",
                 pincode="", city="", state="", emergency_contact="",
                 emergency_phone="", registered_on="", notes=""):
        """Create a patient. Only patient_id and name are required."""
        self.patient_id = patient_id
        self.name = name
        self.age = age
        self.gender = gender
        self.phone = phone
        self.email = email
        self.blood_group = blood_group
        self.address_line = address_line
        self.area = area
        self.pincode = pincode
        self.city = city
        self.state = state
        self.emergency_contact = emergency_contact
        self.emergency_phone = emergency_phone
        self.registered_on = registered_on
        self.notes = notes

    def to_row(self):
        """Return values in FIELDS order, ready for csv.DictWriter."""
        return [getattr(self, field) for field in self.FIELDS]

    def to_dict(self):
        """Return a plain dict for JSON responses."""
        return {field: getattr(self, field) for field in self.FIELDS}

    def address(self):
        """Return the address as one line, omitting anything unrecorded."""
        parts = [self.address_line, self.area,
                 f"{self.city} {self.pincode}".strip(), self.state]
        return ", ".join(p for p in parts if p)

    def summary(self):
        """Return a one-line description for list views."""
        parts = [self.patient_id, self.name]
        if self.age:
            parts.append(f"age {self.age}")
        if self.city:
            parts.append(self.city)
        return " - ".join(parts)

    @staticmethod
    def from_row(row):
        """Build a Patient from a dict read out of a CSV."""
        return Patient(**{k: row.get(k, "") for k in Patient.FIELDS})


class Visit:
    """One row of data/visits.csv. Append-only: never rewritten."""

    FIELDS = [
        "visit_id", "patient_id", "doctor_id", "hospital_id",
        "scheduled_date", "scheduled_time", "checked_in_at", "duration_minutes",
        "reason", "symptoms", "diagnosis", "severity",
        "vitals_bp", "vitals_pulse", "vitals_temp", "vitals_spo2",
        "vitals_weight", "vitals_height", "follow_up_days", "status", "notes",
    ]

    def __init__(self, visit_id, patient_id, doctor_id="", hospital_id="",
                 scheduled_date="", scheduled_time="", checked_in_at="",
                 duration_minutes="", reason="", symptoms="", diagnosis="",
                 severity="", vitals_bp="", vitals_pulse="", vitals_temp="",
                 vitals_spo2="", vitals_weight="", vitals_height="",
                 follow_up_days="", status="", notes=""):
        """Create a consultation record."""
        self.visit_id = visit_id
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.hospital_id = hospital_id
        self.scheduled_date = scheduled_date
        self.scheduled_time = scheduled_time
        self.checked_in_at = checked_in_at
        self.duration_minutes = duration_minutes
        self.reason = reason
        self.symptoms = symptoms
        self.diagnosis = diagnosis
        self.severity = severity
        self.vitals_bp = vitals_bp
        self.vitals_pulse = vitals_pulse
        self.vitals_temp = vitals_temp
        self.vitals_spo2 = vitals_spo2
        self.vitals_weight = vitals_weight
        self.vitals_height = vitals_height
        self.follow_up_days = follow_up_days
        self.status = status
        self.notes = notes

    def symptom_set(self):
        """Return reported symptoms as a set, split on pipes."""
        if not self.symptoms:
            return set()
        return {s.strip().casefold() for s in self.symptoms.split("|") if s.strip()}

    def bmi(self):
        """Return BMI from the recorded height and weight, or None.

        The Practical 1 categorisation problem applied to real records.
        Height is recorded in centimetres, so it is converted first.
        """
        try:
            weight = float(self.vitals_weight)
            height_cm = float(self.vitals_height)
        except (TypeError, ValueError):
            return None

        if not weight or not height_cm:
            return None

        metres = height_cm / 100.0
        return weight / (metres * metres)

    def waited_minutes(self):
        """Return how long after the slot the patient actually arrived."""
        if not (self.scheduled_time and self.checked_in_at):
            return None

        try:
            booked = [int(p) for p in self.scheduled_time.split(":")]
            arrived = [int(p) for p in self.checked_in_at.split(":")]
            return (arrived[0] * 60 + arrived[1]) - (booked[0] * 60 + booked[1])
        except (ValueError, IndexError):
            return None

    def to_row(self):
        """Return values in FIELDS order, ready for csv.DictWriter."""
        return [getattr(self, field) for field in self.FIELDS]

    def to_dict(self):
        """Return a plain dict for JSON responses."""
        return {field: getattr(self, field) for field in self.FIELDS}

    @staticmethod
    def from_row(row):
        """Build a Visit from a dict read out of a CSV."""
        return Visit(**{k: row.get(k, "") for k in Visit.FIELDS})