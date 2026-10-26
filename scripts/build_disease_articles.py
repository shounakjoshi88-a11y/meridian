"""Build data/disease_articles.csv, the written half of the disease registry.

Why this is a separate file rather than more columns in diseases.csv:
diseases.csv is what the triage engine matches against. Changing it changes
ranking, and its schema is asserted by the seed checker and the tests. The
article is what a human reads. Keeping them apart means prose can be edited
and extended without touching the matching path, and it is honest about
which half is machine-derived and which half was written.

Every condition here has a real ICD-10-CM code verified against
data/icd10cm_codes.csv. The symptom vocabulary, medication, dose, usual age
range and contraindications all come from diseases.csv and are not repeated
in this file, so the two can never disagree.

The prose is written from general clinical knowledge, not copied from a
drug authority or a clinical guideline, because no such source is available
under a licence that permits redistribution. It is an educational summary to
help a reader understand a term, not clinical guidance, and every article
says so in its own footer. Nothing here should be used to treat anyone.

Run from the project root:  python scripts/build_disease_articles.py
"""

import csv
import io
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(HERE, "data", "disease_articles.csv")
DISEASES = os.path.join(HERE, "data", "diseases.csv")

FIELDS = ["disease_id", "summary", "red_flags", "refer_when",
         "medicine_ids", "provenance"]

PROVENANCE = ("Written for this project from general clinical knowledge. "
              "Educational summary, not clinical guidance.")

# disease_id -> (summary, red_flags, refer_when)
#
# red_flags are findings that mean the patient should not be managed as an
# outpatient at all. refer_when are the criteria for sending the patient to a
# specialist, which is a different and much lower bar.
ARTICLES = {
    "ICD-J00": (
        "A viral infection of the nose and throat, almost always caught from "
        "someone else. It runs its course over five to seven days and gets "
        "better on its own. The main job is comfort, and the main risk is "
        "treating it with something unnecessary.",
        "Breathlessness|confusion|duration beyond 10 days",
        "Persistent symptoms past 10 days|recurrent infection in an adult",
    ),
    "ICD-J02": (
        "Inflammation of the throat, usually viral. It causes the familiar "
        "sore throat and low fever. Antibiotics do nothing for it, because "
        "there is no bacterium to kill.",
        " drooling or inability to swallow|neck swelling|trouble breathing",
        "Symptoms past 3 weeks|suspected glandular fever",
    ),
    "ICD-J03": (
        "Infection of the tonsils. Viral in most cases, but a significant "
        "minority are bacterial, and those are the ones worth treating. The "
        "distinguishing sign is exudate on the tonsils with tender glands in "
        "the neck.",
        "Cannot swallow fluids|drooling|muffled voice|neck stiffness",
        "Recurrent tonsillitis|peritonsillar abscess|airway compromise",
    ),
    "ICD-J06": (
        "A catch-all for an infection somewhere in the upper airway when the "
        "exact site was not pinned down. Common, self-limiting, and treated "
        "with rest and fluids.",
        "Stridor|noisy breathing|neck swelling",
        "Symptoms beyond 7 days|recurrent or persistent",
    ),
    "ICD-J20": (
        "Inflammation of the large airways, usually following a viral "
        "infection. The cough lasts longer than the cold that caused it, "
        "which is what distinguishes it.",
        "Cough with blood|dyspnoea at rest|worsening rather than settling",
        "Cough persisting past 3 weeks|recurrent episodes|suspected asthma",
    ),
    "ICD-J21": (
        "A viral infection of the smallest airways, and the main reason "
        "infants are admitted to hospital. In children under two it causes "
        "wheezing and difficulty feeding.",
        "Pauses in breathing|cyanosis|difficulty feeding|less wet nappies",
        "Any infant under 1 year|Apnoea or pauses in breathing|poor feeding",
    ),
    "ICD-J18": (
        "Infection of the lung tissue itself, which is more serious than a "
        "bronchitis because the air spaces fill with fluid. It needs a "
        "clinical assessment, and bacterial causes need an antibiotic.",
        "Breathlessness at rest|confusion|blue lips|very high fever with "
        "rash|low blood oxygen",
        "Severe or rapidly progressing|immunocompromised|pregnancy|poor "
        "response to 48 hours of treatment",
    ),
    "ICD-J44": (
        "Long-standing lung disease with irreversible narrowing of the "
        "airways, almost always in smokers or people with long smoke "
        "exposure. It is progressive and managed rather than cured.",
        "Sudden change in breathlessness|cough with blood|ankle swelling",
        "Frequent exacerbations|respiratory failure|consideration of surgery",
    ),
    "ICD-J45": (
        "A long-term condition in which the airways narrow and tighten, "
        "reversibly. Attacks are triggered by allergens, cold air, infection "
        "or exercise. Inhalers work far better used early than late.",
        "Cannot finish a sentence|blue lips|silent chest|peak flow under 50% "
        "of usual",
        "New diagnosis in an adult|poor control on high-dose therapy|"
        "frequent reliever use",
    ),
    "ICD-J47": (
        "Permanent widening of the airways from damage or infection, leaving "
        "them unable to clear mucus. It is lifelong and needs regular airway "
        "clearance.",
        "Cough with large volumes of foul sputum|haemoptysis|recurrent "
        "infection",
        "Recurrent chest infection|declining function|suspected CF or "
        "immunodeficiency",
    ),
    "ICD-J38": (
        "Disorders of the voice box, most commonly laryngitis from "
        "overuse or infection. Voice rest resolves most of it.",
        "Difficulty breathing or swallowing|stridor|cough with blood",
        "Hoarseness beyond 3 weeks|lump or neck mass|professional voice user",
    ),
    "ICD-R05": (
        "A symptom, not a diagnosis. Cough lasting under three weeks is "
        "usually a viral infection; beyond three weeks it needs investigating.",
        "Cough with blood|weight loss|breathlessness at rest|night sweats",
        "Cough beyond 3 weeks|any red flag present|persistent in a smoker",
    ),
    "ICD-A09": (
        "Bowel infection causing watery diarrhoea, most often from "
        "contaminated food or water. Oral rehydration is the single most "
        "important treatment and is more effective than anything else.",
        "Blood in stool|severe dehydration|repeated vomiting|infant under 6 "
        "months|immunosuppression",
        "Diarrhoea beyond 5 days|blood in stool|recent foreign travel",
    ),
    "ICD-A15": (
        "Tuberculosis of the lungs, caused by a slowly growing bacterium. It "
        "is contagious and needs a multi-drug course lasting months. The "
        "combination of a long cough, weight loss, night sweats and drenching "
        "sweats is the classic presentation.",
        "Cough with blood|massive haemoptysis|severe breathlessness|confusion",
        "All cases, to a TB clinic|any suspected case for notification",
    ),
    "ICD-A19": (
        "Tuberculosis spread through the bloodstream, affecting many organs at "
        "once. It is rare and life-threatening, with high fever and marked "
        "systemic illness.",
        "High fever with rapid deterioration|breathlessness|confusion|"
        "immunosuppression",
        "All cases, immediately",
    ),
    "ICD-A37": (
        "A bacterial airway infection with bouts of coughing that can go on "
        "for weeks. Most common in unimmunised children. The cough has a "
        "characteristic whoop with a gasp at the end.",
        "Apnoea in an infant|cyanosis|seizure|severe coughing fits",
        "Infants under 6 months|unimmunised patients|respiratory arrest",
    ),
    "ICD-A90": (
        "A mosquito-borne viral illness with abrupt fever, severe aches and "
        "rash. Platelets fall and fluid can leak out of the vessels, which is "
        "what makes it dangerous. Paracetamol is the right analgesic; aspirin "
        "and ibuprofen are not, because of bleeding risk.",
        "Bleeding from gums or injection sites|bruising|severe abdominal pain|"
        "repeated vomiting|restlessness or drowsiness|dangerous "
        "haematocrit with low platelets",
        "Any warning sign present|platelet count below 50,000|warning signs "
        "at first review",
    ),
    "ICD-A91": (
        "Dengue with significant bleeding, the dangerous form of the same "
        "illness. Plasma leaks out of the vessels and the patient can go from "
        "apparently well to shock within hours.",
        "Shock|severe bleeding|unresponsive|dangerously low platelet count|"
        "haematocrit rising with platelets falling",
        "All cases, immediately to hospital",
    ),
    "ICD-B54": (
        "Malaria, a parasite carried by mosquitoes, presenting with cyclical "
        "fever, chills and sweats. The parasite can be confirmed on a blood "
        "film, which should be requested whenever the pattern fits.",
        "Confusion|seizures|breathlessness|jaundice|very low blood pressure|"
        "dark urine",
        "Severe or falciparum malaria|children and pregnancy|unable to take "
        "oral medication",
    ),
    "ICD-A01": (
        "A bacterial infection of the gut from contaminated food or water, "
        "with a persistent fever that is not the short fever of a stomach "
        "bug. Complications include intestinal perforation.",
        "Confusion|severe abdominal pain|blood in stool|very high fever",
        "Diagnosis suspected on clinical grounds|carriers|not responding to "
        "treatment",
    ),
    "ICD-A92": (
        "A group of other mosquito and tick-borne fevers, including chikungunya "
        "and Zika. They look similar to dengue and are distinguished by blood "
        "tests.",
        "Bleeding|severe joint pain|dehydration|new focal neurological signs",
        "Pregnancy|haemorrhage|immunosuppression|diagnostic uncertainty",
    ),
    "ICD-B05": (
        "A highly contagious viral illness causing fever, runny nose, cough "
        "and a spreading rash. Most people have immunity from the vaccine. "
        "It is notifiable and needs isolation.",
        "Breathlessness|pneumonia|seizure|immunosuppression|pregnancy",
        "All cases for notification|any complication|hospital or staff exposure",
    ),
    "ICD-B34": (
        "A viral infection where the site could not be pinned down. Treated "
        "supportively; the value of the category is mostly in ruling out "
        "something more specific.",
        "High fever persisting beyond 5 days|localised pain|lymphadenopathy",
        "Fever of unknown origin|immunocompromised|diagnostic uncertainty",
    ),
    "ICD-L08": (
        "A bacterial infection of the skin or the tissue under it, usually an "
        "infected cut or a boil. Antibiotics help but drainage and cleaning "
        "matter more.",
        "Cellulitis spreading rapidly|fever|redness extending past the lesion|"
        "diabetes or immunosuppression",
        "Deep infection|systemic upset|failure to improve after 48 hours",
    ),
    "ICD-B01": (
        "Chickenpox, a contagious viral illness with crops of itchy blisters "
        "at different stages. Adults tend to be more unwell than children. "
        "Aciclovir helps if started within 24 hours of the rash appearing.",
        "Breathlessness|confusion|vomiting|bleeding or petechiae|rapid "
        "spread|immunocompromised|pregnancy near term",
        "Complications|newly diagnosed adult|pregnancy|immunocompromised",
    ),
    "ICD-A60": (
        "A viral infection causing clusters of painful blisters, commonly on "
        "the lips or genitals. It reactivates and stays in the nerves, so it "
        "recurs.",
        "Eye involvement|urinary retention|immunocompromised|first episode "
        "in pregnancy",
        "First presentation|Ocular or urinary involvement|frequent recurrence",
    ),
    "ICD-E11": (
        "Diabetes caused by the body's resistance to insulin rather than a "
        "lack of it. Common, often silent for years, and treated with diet, "
        "exercise and metformin. The damage is to the small vessels of the "
        "eyes, kidneys, nerves and feet.",
        "Hyperglycaemic crisis|deteriorating vision|numb or ulcerated feet|"
        "persistent high readings",
        "Uncontrolled on metformin|renal impairment|annual eye and foot "
        "review",
    ),
    "ICD-E10": (
        "Diabetes caused by the body making little or no insulin, usually "
        "autoimmune. It presents with thirst, weight loss, frequent "
        "urination and ketones, and needs lifelong insulin.",
        "Vomiting|abdominal pain|deep rapid breathing|fruity breath|reduced "
        "consciousness",
        "All newly diagnosed children and adolescents|Diabetic ketoacidosis|"
        "any pregnancy in type 1 diabetes",
    ),
    "ICD-E03": (
        "An underactive thyroid gland, causing tiredness, weight gain, cold "
        "intolerance and dry skin. It is common, easily missed in women, and "
        "treated with a single daily tablet.",
        "Extreme drowsiness|low body temperature|slow heart rate|confusion|"
        "myxoedema",
        "Suspected pituitary cause|severe symptoms|pregnancy|"
        "unresponsive to replacement",
    ),
    "ICD-E05": (
        "An overactive thyroid gland, causing weight loss, palpitations, heat "
        "intolerance and tremor. It can also cause atrial fibrillation.",
        "Fever with fast pulse|confusion|heart failure|chest pain",
        "Pregnancy|significant cardiac effects|Thyroid storm|diagnostic "
        "uncertainty",
    ),
    "ICD-E66": (
        "Excess body weight, a long-term condition with real consequences "
        "rather than a cosmetic one. Treatment is diet, activity, and "
        "medication or surgery where warranted.",
        "None in itself|secondary complications of importance",
        "Body mass index over 35|significant comorbidity|adolescents",
    ),
    "ICD-E78": (
        "Abnormal blood fat levels. Usually silent, found on routine blood "
        "tests, and treated because of what it predicts for the heart and "
        "blood vessels rather than what it feels like.",
        "Chest pain|stroke symptoms|severe symptomatic hyperlipidaemia",
        "Very high cholesterol|familial hypercholesterolaemia|young patients "
        "with cardiovascular disease",
    ),
    "ICD-E86": (
        "Loss of body fluid, usually from vomiting or diarrhoea. The danger "
        "is not the loss itself but the salts that go with it, particularly "
        "sodium and potassium.",
        "No urine for 12 hours|confusion|dizziness on standing|very fast weak "
        "pulse|sunken eyes in a child",
        "Severe dehydration|inability to drink|infants and elderly|persistent "
        "loss",
    ),
    "ICD-E87": (
        "A disturbance in the body's salts and acid-base balance, detected on "
        "blood tests. The cause matters more than the number: it can be "
        "diarrhoea, kidney disease, or a drug.",
        "Irregular or absent pulse|confusion|seizure|weakness|arrhythmia",
        "Severe abnormality|on dialysis|unexplained electrolyte derangement",
    ),
    "ICD-R73": (
        "A raised blood sugar that does not meet the criteria for diabetes. "
        "It is a warning sign and needs repeating, not reassurance.",
        "Vomiting|abdominal pain|thirst with polyuria|visual change",
        "Fasting glucose above the diabetes threshold|any symptoms|repeat "
        "testing",
    ),
    "ICD-I10": (
        "Persistently raised blood pressure with no identifiable cause. It "
        "causes no symptoms at all, so it is found by measurement and treated "
        "to protect the heart, brain and kidneys over decades.",
        "Blood pressure over 180/120|chest pain|breathlessness|neurological "
        "symptoms",
        "Resistant hypertension|secondary cause suspected|renal impairment|"
        "pregnancy",
    ),
    "ICD-I20": (
        "Chest pain from narrowing of the heart's arteries. Pain on exertion "
        "that settles with rest is the classic pattern. It is a warning of a "
        "heart attack and needs assessment, not painkillers.",
        "Pain at rest|pain lasting over 20 minutes|sweating with chest pain|"
        "pain radiating to arm or jaw",
        "All new diagnoses|unstable angina|pain on minimal exertion|heart "
        "failure",
    ),
    "ICD-I21": (
        "A heart attack, caused by a blocked artery. Part of the heart dies. "
        "Time to treatment is what determines survival, and every minute "
        "counts.",
        "Any ongoing chest pain|sweating|pallor|collapse|cannot breathe",
        "All cases, emergency transfer immediately",
    ),
    "ICD-I48": (
        "An irregular heartbeat coming from the atria. It often causes no "
        "symptoms at all but greatly raises the risk of stroke, so "
        "anticoagulation is the main decision.",
        "Stroke symptoms|chest pain|heart failure|dizziness with palpitations",
        "Stroke risk score requiring anticoagulation|recent stroke|pregnancy|"
        "thyroid disease",
    ),
    "ICD-I50": (
        "A heart too weak to pump adequately, causing breathlessness, leg "
        "swelling and fatigue. Common after heart attacks and in longstanding "
        "hypertension.",
        "Breathlessness at rest|rapid deterioration|pink frothy sputum|"
        "confusion",
        "Hospital admission if breathless at rest|poor response to diuretics|"
        "newly diagnosed",
    ),
    "ICD-I95": (
        "Low blood pressure, standing or lying. It causes dizziness and "
        "blackouts, and is usually a drug effect or dehydration rather than a "
        "disease in itself.",
        "Syncope with injury|chest pain|confusion|persistently very low "
        "readings",
        "Fainting with exertion|recurrent syncope|severe and symptomatic",
    ),
    "ICD-H66": (
        "Infection of the middle ear, common in children after a cold. Pain "
        "and fever settle within days with pain relief; the antibiotic "
        "question is the part that gets debated.",
        "Swelling behind the ear|neck stiffness|headache|unwell in a child",
        "Recurrent otitis media|effusion persisting|hearing loss|very young "
        "infants",
    ),
    "ICD-H81": (
        "Disorders of the balance organs, causing vertigo. It often also "
        "causes nausea and vomiting. Physiognosis needs to exclude the "
        "serious causes first.",
        "Sudden vertigo with neurological signs|double vision|severe "
        "headache|persistent vomiting",
        "New vertigo|central neurological signs|episodic episodes|"
        "immunosuppressed",
    ),
    "ICD-H10": (
        "Inflammation of the conjunctiva, the white of the eye. Red and "
        "itchy, and highly contagious when viral. The important thing to "
        "exclude is something in the eye itself.",
        "Eye pain|reduced vision|light sensitivity|corneal opacity|trauma",
        "Any pain or vision change|neonates|contact lens wearers|"
        "immunosuppressed",
    ),
    "ICD-H25": (
        "Clouding of the lens of the eye with age, causing blurred and "
        "glared vision. Common, gradual, and one of the most surgically "
        "successful operations there is.",
        "Sudden vision loss|pain|redness|flash perception",
        "All progressive cases for cataract surgery|diabetics|after "
        "steroid use",
    ),
    "ICD-H52": (
        "Focusing errors of the eye: shortsightedness, longsightedness and "
        "presbyopia. Corrected with glasses or lenses, and presbyopia is "
        "normal ageing rather than a disease.",
        "Sudden vision change|pain|diplopia|floaters or flashes",
        "Sudden change in vision|diplopia|children with possible squint",
    ),
    "ICD-K21": (
        "Stomach acid flowing back into the gullet, causing heartburn and "
        "regurgitation. Common and treatable, and the treated outcome is good.",
        "Difficulty swallowing|weight loss|anaemia|black stool|vomiting blood",
        "Alarm features present|persistent symptoms despite treatment|"
        "Barrett's changes",
    ),
    "ICD-K30": (
        "Indigestion without an identifiable ulcer or reflux, with pain or "
        "discomfort centred on the upper abdomen. Common and often responds "
        "to simple measures.",
        "Weight loss|anaemia|dysphagia|night pain|gastrointestinal bleeding",
        "Over 50 with new symptoms|alarm features|persistent despite PPI",
    ),
    "ICD-K52": (
        "Inflammation of the bowel that is not infective and not "
        "inflammatory bowel disease, often mild and self-limiting. Needs to "
        "be distinguished from the other two.",
        "Blood in stool|weight loss|severe pain|systemic upset",
        "Persistent symptoms|to exclude inflammatory bowel disease|weight loss",
    ),
    "ICD-K58": (
        "A long-term disorder of gut function causing cramps, bloating, "
        "diarrhoea and constipation, without structural damage. Common, and "
        "managed by dietary change rather than medication.",
        "Rectal bleeding|weight loss|nocturnal symptoms|anaemia|palpable mass",
        "Red flags present|new onset after 50|suspected inflammatory bowel "
        "disease",
    ),
    "ICD-K59": (
        "Functional problems with defecation, usually constipation. Not a "
        "structural disease and often very responsive to fibre and activity.",
        "Rectal bleeding|vomiting|weight loss|abdominal mass|change in bowel "
        "habit after 50",
        "Red flags present|suspected outlet dysfunction|persistent despite "
        "simple measures",
    ),
    "ICD-K70": (
        "Liver damage caused by long-standing heavy alcohol use, from fatty "
        "liver through to cirrhosis. Stopping alcohol helps at every stage, "
        "and earlier is much better than later.",
        "Jaundice|vomiting blood|confusion|ascites|black stool",
        "All cases for specialist review|varices|coexisting liver disease|"
        "withdrawal risk",
    ),
    "ICD-K04": (
        "Disease of the pulp inside the tooth and the tissues around its root, "
        "usually decay or trauma. Irreversible pain needs root canal or "
        "extraction; the dentist decides.",
        "Facial swelling|fever|difficulty swallowing|trismus|spreading "
        "infection",
        "Dental pain with systemic upset|swelling|dental abscess",
    ),
    "ICD-K05": (
        "Gum disease, from bleeding on brushing through to loosening teeth. "
        "It is largely preventable and the first stage is reversible with "
        "better cleaning.",
        "Loose teeth|pus|bad taste|abscess|rapid progression",
        "Loose teeth|abscess|poor response to oral hygiene|systemic disease",
    ),
    "ICD-K80": (
        "Gallstones. Many are silent and found incidentally; they cause pain "
        "only when they block a duct. The characteristic pain is steady, "
        "epigastric, and lasts hours.",
        "Fever with jaundice|severe constant pain|vomiting|confusion",
        "Recurrent biliary colic|cholangitis|all symptomatic gallstones",
    ),
    "ICD-K922": (
        "Bleeding from the upper gut. Vomited blood or coffee-ground material "
        "with black stools is a medical emergency, whatever the apparent "
        "cause.",
        "Haematemesis|melaena|shock|confusion|severe tachycardia",
        "All cases, immediate hospital referral",
    ),
    "ICD-K920": (
        "Vomiting blood. It needs assessment regardless of the likely cause, "
        "because the amount that looks small can be misleading.",
        "Ongoing bleeding|shock|confusion|coagulopathy|alcohol use",
        "All cases, immediate hospital referral",
    ),
    "ICD-M54": (
        "Non-specific low back pain. Overwhelmingly mechanical and "
        "self-limiting, and imaging is rarely needed in the first six weeks.",
        "Saddle anaesthesia|urinary retention|new bowel or bladder "
        "incontinence|leg weakness|night pain|weight loss",
        "Red flags present|persistent over 6 weeks|recurrent disabling pain",
    ),
    "ICD-M17": (
        "Degenerative change of the knee joint, causing pain that worsens "
        "with activity and eases with rest. Exercise is more effective than "
        "any medication over the long term.",
        "Hot swollen joint with fever|locked knee|unable to bear weight",
        "Rapid progression|significant deformity|poor function after 6 "
        "months of therapy|considering replacement",
    ),
    "ICD-M10": (
        "Gout, from uric acid crystals in the joint. It comes on suddenly, "
        "with a joint that is red, hot and exquisitely tender, often after "
        "purine-rich food or alcohol.",
        "Hot red joint with fever|oliguria or blood in urine|confusion",
        "First attack with diagnostic uncertainty|recurrent attacks|renal "
        "impairment|allopurinol initiation with high urate",
    ),
    "ICD-M06": (
        "Inflammatory arthritis, where the immune system attacks the joint "
        "lining. It damages joints over time, so early specialist treatment "
        "changes the long-term outcome.",
        "Hot swollen joint with fever|multiple joints|systemic symptoms|"
        "interstitial lung disease",
        "All suspected cases to rheumatology|Rapid joint damage|extra-articular "
        "disease",
    ),
    "ICD-M79": (
        "Soft tissue problems such as fibromyalgia and muscular pain, without "
        "joint or bone damage. Common, miserable, and much better helped by "
        "graded activity than by analgesics.",
        "Night pain|systemic symptoms|true muscle weakness|weight loss",
        "Uncertain diagnosis|red flags present|failure of graded therapy",
    ),
    "ICD-M25": (
        "A joint problem that does not fit a more specific diagnosis. Often "
        "minor, but occasionally the first sign of something inflammatory or "
        "degenerative.",
        "Hot swollen joint with fever|locked joint|inability to bear weight",
        "Persistent symptoms|diagnostic uncertainty|hot swollen joint",
    ),
    "ICD-M62": (
        "Muscle problems, most often pain and weakness from overuse or strain. "
        "Rarely anything more serious once injury is excluded.",
        "True weakness|visible wasting|fever|myoglobin in urine",
        "Fever with muscle pain|weakness|immunosuppressed|raised creatine "
        "kinase",
    ),
    "ICD-F32": (
        "A depressive episode, from mild to severe, with low mood and loss of "
        "interest in things that used to matter. It is a medical condition, "
        "not a character flaw, and responds well to treatment.",
        "Thoughts of ending life|not eating or drinking|severe self-neglect|"
        "confusion or agitation",
        "Suicidal thoughts|psychotic symptoms|not responding to treatment|"
        "severe functional loss",
    ),
    "ICD-F41": (
        "Anxiety disorders, where fear is out of proportion to the actual "
        "threat and interferes with daily life. Cognitive therapy is as "
        "effective as medication for most types.",
        "Chest pain mimicking cardiac disease|suicidal thoughts|severe "
        "functional impairment|alcohol dependence",
        "Suicidal thoughts|poor response to first-line therapy|complicated by "
        "substance use",
    ),
    "ICD-F43": (
        "The effects of severe trauma or a major life change, appearing weeks "
        "to months later. They are common and improve with support and "
        "structured therapy.",
        "Suicidal thoughts|severe dissociation|abuse|dependence developing",
        "Suicidal thoughts|severe or persistent symptoms|children and "
        "adolescents",
    ),
    "ICD-G47": (
        "Sleep problems, either difficulty sleeping or sleeping too much. "
        "Usually best managed by changing habits rather than by tablets.",
        "Daytime sleepiness with driving risk|breathing pauses in sleep|"
        "mood effects of sleep loss",
        "Suspected sleep apnoea|severe insomnia persisting despite good "
        "habits|occupational risk",
    ),
    "ICD-G43": (
        "Recurrent headache, most often migraine, with throbbing pain and "
        "sometimes vomiting and visual disturbance. Treatable, and the "
        "trick is early medication rather than frequent.",
        "Thunderclap onset|fever with neck stiffness|new neurological signs|"
        "headache after 50|progressive worsening",
        "Thunderclap headache|new headache over 50|neurological signs|"
        "pregnancy|changing pattern",
    ),
    "ICD-G40": (
        "Epilepsy, a tendency to recurrent seizures from abnormal electrical "
        "activity in the brain. Diagnosis is clinical, and medication controls "
        "most people well.",
        "Seizure lasting over 5 minutes|repeated seizures without recovery|"
        "injury|breathing difficulty|first seizure",
        "First seizure|children|pregnancy|poor seizure control",
    ),
    "ICD-G20": (
        "Parkinson's disease, where brain cells that make dopamine are lost "
        "over years, causing tremor, slowness and stiffness. It progresses "
        "slowly and responds well to medication.",
        "Sudden onset|marked imbalance|falls|early autonomic failure",
        "Diagnosis uncertainty|poor response to levodopa|falls|swallowing "
        "difficulty",
    ),
    "ICD-G56": (
        "Nerve problems in a single limb, from compression or diabetes, "
        "causing numbness, tingling or weakness in a defined pattern.",
        "Rapidly progressive weakness|saddle anaesthesia|cauda equina features|"
        "systemic symptoms",
        "Weakness rather than numbness|corridor or saddle distribution|"
        "suspected compressive lesion",
    ),
    "ICD-N20": (
        "Stones in the kidney or ureter, causing severe colicky pain in the "
        "flank radiating to the groin, with nausea. Most pass on their own.",
        "Fever with flank pain|uncontrolled pain|vomiting|reduced urine|"
        "single kidney|severe obstruction",
        "Obstruction with infection|severe pain|renal impairment|stone in "
        "pregnancy",
    ),
    "ICD-N39": (
        "Other urinary problems, including recurrent infection and urinary "
        "incontinence. Common in older people and often easily improved.",
        "Fever with loin pain|retention|visible blood|acute kidney injury",
        "Recurrent infection|renal impairment|male with recurrent infection",
    ),
    "ICD-N40": (
        "Non-cancerous enlargement of the prostate, the most common cause of "
        "lower urinary tract symptoms in older men. Gradually progressive and "
        "treatable.",
        "Retention|visible blood|fever|renal impairment|back pain",
        "Retention|renal impairment|recurrent infection|haematuria",
    ),
    "ICD-N63": (
        "An unexplained lump in the breast. Most are benign, but a new lump "
        "must be assessed rather than assumed.",
        "Fixed hard lump|nipple discharge|skin dimpling|lymphadenopathy",
        "All new or changing lumps|hard or fixed lump|lymphadenopathy",
    ),
    "ICD-N04": (
        "A kidney disorder where the kidneys leak large amounts of protein and "
        "fluid, causing swelling and low albumin in the blood. It needs "
        "specialist investigation.",
        "Severe swelling|breathlessness|reduced urine|chest pain|infection",
        "All newly diagnosed adults|children|reduced renal function",
    ),
    "ICD-N92": (
        "Heavy, frequent or irregular periods, a common cause of iron "
        "deficiency anaemia and impaired quality of life. Treatable, and "
        "usually easily.",
        "Fainting|heavy bleeding with clots|severe pain|possible pregnancy",
        "Iron deficiency anaemia|postmenopausal bleeding|suspicion of "
        "structural cause",
    ),
    "ICD-D25": (
        "Fibroids in the uterus, causing heavy periods and pressure symptoms "
        "in a large proportion of women. Very common and usually managed "
        "without surgery.",
        "Sudden severe pain|heavy bleeding with dizziness|pressure on bladder "
        "or bowel",
        "Rapid growth after menopause|suspected malignancy|severe symptoms "
        "after failed medical treatment",
    ),
    "ICD-N80": (
        "Endometriosis, where uterine-type tissue grows outside the uterus, "
        "causing pain particularly around periods. Frequently missed for years "
        "before diagnosis.",
        "Severe pain refractory to analgesia|bowel or bladder involvement|"
        "infertility",
        "Severe or cyclical pelvic pain|bowel or bladder symptoms|adolescent "
        "presentation",
    ),
    "ICD-N61": (
        "Inflammation of the breast, most often mastitis from infection "
        "during breastfeeding, which needs prompt treatment so it does not "
        "abscess.",
        "Fever with breast pain|fluctuant mass|skin erythema|systemic upset",
        "Non-breastfeeding or non-lactational abscess|suspected malignancy|"
        "failure to resolve",
    ),
    "ICD-N91": (
        "Absent, infrequent or very light periods, from many causes including "
        "low weight, excessive exercise and hormonal contraception.",
        "None urgent in itself|severe pelvic pain|possible pregnancy",
        "Oligomenorrhoea with hyperandrogenism|adolescents|trying to conceive|"
        "palpable mass",
    ),
    "ICD-L20": (
        "Eczema, a relapsing itchy inflammation of the skin that runs in "
        "families. Dry skin is the main problem, and daily emollients do more "
        "than any prescribed steroid.",
        "Infected eczema|widespread|systemic upset|failure to thrive|"
        "difficulty sleeping",
        "Extensive or facial disease|children not thriving|suspected "
        "contact allergy|frequent flares",
    ),
    "ICD-L40": (
        "Psoriasis, a chronic condition with well-defined scaly plaques and "
        "sometimes nail and joint involvement. About a third of patients "
        "develop arthritis.",
        "Widespread erythroderma|pustules|joint pain and swelling|systemic "
        "upset",
        "Arthritis with psoriasis|extensive or pustular disease|failure of "
        "topical treatment|immunosuppression",
    ),
    "ICD-L30": (
        "A broad group of non-specific skin inflammation, often eczema-like. "
        "The general approach is to keep the skin dry or moisturised as "
        "appropriate and avoid irritants.",
        "Widespread|systemic upset|blistering|raw weeping over large areas",
        "Diagnostic uncertainty|widespread disease|children|not responding to "
        "simple treatment",
    ),
    "ICD-L70": (
        "Acne, caused by blocked hair follicles and excess oil, typically in "
        "teenagers. It can cause lasting scarring, so early treatment is worth "
        "it.",
        "Fever|widespread cystic acne|severe scarring|rapid onset in an adult",
        "Scarring|severe nodulocystic disease|topical treatment failure|"
        "pregnancy",
    ),
    "ICD-L65": (
        "Hair loss without scarring. Non-scarring loss often reverses, while "
        "scarring loss does not, so the distinction drives everything.",
        "Scarring|patchy loss|hair loss with skin inflammation|systemic signs",
        "Scarring alopecia|diagnosis uncertain|patchy loss in a child",
    ),
    "ICD-L53": (
        "Reddened skin conditions, most often rashes that do not fit a more "
        "specific diagnosis. Usually settle with simple treatment.",
        "Widespread|blistering|mucous membrane involvement|systemic upset|"
        "fever",
        "Mucous membrane involvement|widespread blistering|systemic illness|"
        "children",
    ),
    "ICD-R50": (
        "Fever with no identified cause. In adults it usually means "
        "investigation rather than watchful waiting, and blood tests are "
        "warranted.",
        "Rash that does not blanch|neck stiffness|confusion|immunosuppression|"
        "fever over 5 days",
        "Fever over 5 days|immunosuppressed|travel or exposure history|"
        "localised pain",
    ),
    "ICD-R51": (
        "Headache that is not classified further, most often tension type. "
        "Very common, and the treatment is usually simple.",
        "Thunderclap onset|neurological signs|fever with neck stiffness|headache "
        "after 50|severe and new pattern",
        "Red flags present|persistent daily headache|significant functional "
        "impact",
    ),
    "ICD-R53": (
        "Tiredness without a specific cause. It is a presentation rather than "
        "a diagnosis, and the useful response is to look for anaemia, thyroid "
        "disease and diabetes rather than to reassure.",
        "Chest pain|breathlessness|weight loss|palpable nodes|bleeding "
        "tendency",
        "Raised inflammatory markers|weight loss|immunosuppressed|"
        "unexplained and persistent",
    ),
    "ICD-R10": (
        "Abdominal pain that does not fit a more specific diagnosis. Location "
        "and character of the pain matter more than the fact that it hurts, "
        "and some patterns need surgery.",
        "Sudden severe pain|vomiting with distension|rigid abdomen|"
        "rectal bleeding|absolute silence on auscultation",
        "Any surgical abdomen|persistent unexplained pain|weight loss|age "
        "over 50",
    ),
    "ICD-R21": (
        "A non-specific rash. Common, self-limiting, and the useful question "
        "is whether it blanches on pressure, because a rash that does not is "
        "more urgent.",
        "Non-blanching petechiae|blistering|mucous membrane involvement|"
        "systemic upset|fever with rash",
        "Non-blanching rash|meningococcal features|extensive blistering|"
        "immunocompromised",
    ),
    "ICD-R31": (
        "Blood in the urine. It is never normal, is often painless, and "
        "always needs investigation to rule out a tumour.",
        "Visible clots|retention|severe pain|fever|weight loss",
        "All cases in adults|Painless haematuria|persistent haematuria",
    ),
    "ICD-R42": (
        "A sensation of spinning or unsteadiness, most often benign positional "
        "vertigo. Checking lying and standing blood pressure is the highest "
        "yield first step.",
        "Central neurological signs|severe headache at onset|new focal "
        "deficit|persistent vomiting",
        "New presentation|neurological signs|recurrent falls|unable to "
        "assess safely",
    ),
    "ICD-R55": (
        "Fainting from a temporary drop in blood flow to the brain. Common, "
        "often benign, but cardiac causes are the ones that matter and are "
        "excluded by history, examination and ECG.",
        "Syncope during exertion|injury|palpitations before loss of "
        "consciousness|seizure-like movements|recovery not prompt",
        "Exertional syncope|structural heart disease|recurrent syncope|"
        "suspected arrhythmia",
    ),
}


# Conditions whose first-line treatment is in data/medicines.csv, so the
# article can say where to get it.
#
# This is written out rather than derived. An earlier version tried to match
# the prose in the medication column against the catalogue, which found
# nothing, because the column reads "Paracetamol and oral fluids" and no
# medicine is called that. Parsing prose to recover a key is guessing; a
# column of ids is a fact.
#
# Most conditions are absent on purpose. The catalogue holds twenty medicines
# and the registry covers ninety-six conditions, so for most of them the
# honest answer is that the clinic does not dispense it, and the page says
# so rather than implying a pharmacy round the corner.
MEDICINES = {
    "ICD-J00": "M-01|M-02",
    "ICD-J02": "M-01|M-02",
    "ICD-J03": "",
    "ICD-J06": "M-01|M-02",
    "ICD-J20": "M-06",
    "ICD-J21": "M-10",
    "ICD-J18": "",
    "ICD-J44": "M-10",
    "ICD-J45": "M-10",
    "ICD-J47": "M-06",
    "ICD-J38": "M-01|M-02",
    "ICD-R05": "M-06",
    "ICD-A09": "M-11|M-12",
    "ICD-A15": "",
    "ICD-A19": "",
    "ICD-A37": "",
    "ICD-A90": "M-01|M-02",
    "ICD-A91": "",
    "ICD-B54": "M-18",
    "ICD-A01": "",
    "ICD-A92": "M-01|M-02",
    "ICD-B05": "M-01|M-02",
    "ICD-B34": "M-01|M-02",
    "ICD-L08": "",
    "ICD-B01": "",
    "ICD-A60": "",
    "ICD-E11": "M-03|M-04",
    "ICD-E10": "M-17",
    "ICD-E03": "M-09",
    "ICD-E05": "",
    "ICD-E66": "M-03",
    "ICD-E78": "",
    "ICD-E86": "M-11",
    "ICD-E87": "",
    "ICD-R73": "M-19",
    "ICD-I10": "M-07|M-08",
    "ICD-I20": "",
    "ICD-I21": "",
    "ICD-I48": "",
    "ICD-I50": "",
    "ICD-I95": "",
    "ICD-H66": "",
    "ICD-H81": "",
    "ICD-H10": "",
    "ICD-H25": "",
    "ICD-H52": "",
    "ICD-K21": "",
    "ICD-K30": "",
    "ICD-K52": "",
    "ICD-K58": "",
    "ICD-K59": "",
    "ICD-K70": "",
    "ICD-K04": "M-01|M-02",
    "ICD-K05": "",
    "ICD-K80": "M-01|M-02",
    "ICD-K922": "",
    "ICD-K920": "",
    "ICD-M54": "",
    "ICD-M17": "",
    "ICD-M10": "",
    "ICD-M06": "",
    "ICD-M79": "",
    "ICD-M25": "",
    "ICD-M62": "",
    "ICD-F32": "M-16",
    "ICD-F41": "M-16",
    "ICD-F43": "",
    "ICD-G47": "",
    "ICD-G43": "M-15",
    "ICD-G40": "",
    "ICD-G20": "",
    "ICD-G56": "",
    "ICD-N20": "",
    "ICD-N39": "M-13",
    "ICD-N40": "",
    "ICD-N63": "",
    "ICD-N04": "",
    "ICD-N92": "M-14",
    "ICD-D25": "",
    "ICD-N80": "",
    "ICD-N61": "",
    "ICD-N91": "",
    "ICD-L20": "",
    "ICD-L40": "",
    "ICD-L30": "",
    "ICD-L70": "",
    "ICD-L65": "",
    "ICD-L53": "",
    "ICD-R50": "M-01|M-02|M-20",
    "ICD-R51": "M-01|M-02",
    "ICD-R53": "",
    "ICD-R10": "M-01|M-02",
    "ICD-R21": "",
    "ICD-R31": "",
    "ICD-R42": "",
    "ICD-R55": "M-20",
}


def main():
    with io.open(DISEASES, encoding="utf-8", newline="") as f:
        known = {row["disease_id"] for row in csv.DictReader(f)}

    rows = []

    for disease_id in sorted(ARTICLES):
        summary, red_flags, refer_when = ARTICLES[disease_id]

        rows.append({
            "disease_id": disease_id,
            "summary": " ".join(summary.split()),
            # A leading space is how an empty field is spelled here. It is
            # written and stripped on read so the column can be left blank
            # rather than holding the word "none".
            "red_flags": "|".join(p.strip() for p in red_flags.split("|") if p.strip()),
            "refer_when": "|".join(p.strip() for p in refer_when.split("|") if p.strip()),
            "medicine_ids": MEDICINES.get(disease_id, ""),
            "provenance": PROVENANCE,
        })

    written = {r["disease_id"] for r in rows}

    with io.open(os.path.join(HERE, "data", "medicines.csv"),
                 encoding="utf-8", newline="") as f:
        stocked = {row["medicine_id"] for row in csv.DictReader(f)}

    unmapped = sorted(known - set(MEDICINES))
    dangling = sorted({m for ids in MEDICINES.values() for m in ids.split("|")
                       if m and m not in stocked})

    if unmapped:
        raise SystemExit(
            f"{len(unmapped)} conditions have no medicine mapping: "
            f"{', '.join(unmapped)}. Empty is a valid answer; absent is not.")
    if dangling:
        raise SystemExit(
            f"medicine ids that are not in the catalogue: "
            f"{', '.join(dangling)}")

    missing = sorted(known - written)
    extra = sorted(written - known)

    if extra:
        raise SystemExit(
            f"article written for a condition that is not in diseases.csv: "
            f"{', '.join(extra)}")
    if missing:
        raise SystemExit(
            f"{len(missing)} conditions have no article: {', '.join(missing)}")

    with io.open(TARGET, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    with_medicine = sum(1 for r in rows if r["medicine_ids"])

    print(f"wrote {TARGET}")
    print(f"  conditions          : {len(rows):,}")
    print(f"  articles complete   : yes, checked against diseases.csv")
    print(f"  medicine mapped     : {with_medicine} of {len(rows)}")
    print(f"  medicine ids real   : yes, checked against medicines.csv")


if __name__ == "__main__":
    main()