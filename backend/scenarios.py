"""
Synthetic demo patients (judge item #5): every name starts with "Test Patient" so nobody mistakes
the demo for real health information. Family medicine only (judge item #1).

The first three are the prototype's cases. Two more show the safety screen:
  chest  -> red flag (emergency path, AI never runs)
  heart  -> vague wording ("my heart feels weird"), our answer to the team's open question
"""

SCENARIOS = {
    "ear": {
        "label": "Sinus & Ear Pain",
        "emoji": "🤒",
        "intake": {
            "name": "Test Patient Maya",
            "insurance": "ppo",
            "symptoms": "My right ear has been throbbing for 4 days, I had a low fever last night around 100.8, "
                        "and my face feels super congested and heavy when I bend over.",
            "duration": "4-7 days",
            "severity": 6,
            "meds": "Ibuprofen 200mg as needed",
            "allergies": "No known drug allergies",
        },
        "outcome": {
            "diagnosis": "Acute Sinusitis & Right Otitis Media",
            "rx_generic": "Amoxicillin 500mg (Generic, 10-day course)",
            "rx_brand": "Augmentin 875mg (Brand, 10-day course)",
            "notes": "Start Amoxicillin 500mg PO TID x10d. Warm compress to R ear x10 min PRN. "
                     "Hydration + OTC saline nasal spray. Return if temp >102F or symptoms worsen after 48h.",
            "visit_fee": 145, "test_name": "Ear Exam & Tympanometry Check", "test_fee": 45,
            "rx_generic_price": 14, "rx_brand_price": 78,
        },
    },
    "bp": {
        "label": "BP Refill & Dizziness",
        "emoji": "💊",
        "intake": {
            "name": "Test Patient Robert",
            "insurance": "hmo",
            "symptoms": "I ran out of my blood pressure pills 3 days ago and I feel a little lightheaded when I stand up fast. "
                        "Also had a mild headache this morning.",
            "duration": "2-3 days",
            "severity": 5,
            "meds": "Lisinopril 10mg (out of refills)",
            "allergies": "Sulfa drugs",
        },
        "outcome": {
            "diagnosis": "Uncontrolled Essential Hypertension (Medication Gap)",
            "rx_generic": "Lisinopril 10mg (Generic, 90-day supply)",
            "rx_brand": "Zestril 10mg (Brand, 90-day supply)",
            "notes": "BP 148/92. Renew Lisinopril 10mg PO daily #90. Orthostatic precautions. "
                     "Recheck BP at pharmacy kiosk in 1 wk. RTC if CP, SOB, severe HA or syncope.",
            "visit_fee": 130, "test_name": "In-Clinic BP & Orthostatic Vitals Panel", "test_fee": 35,
            "rx_generic_price": 12, "rx_brand_price": 95,
        },
    },
    "ankle": {
        "label": "Ankle Sprain",
        "emoji": "🩹",
        "intake": {
            "name": "Test Patient Jordan",
            "insurance": "self",
            "symptoms": "I rolled my left ankle playing basketball yesterday evening. It is swollen on the outside and hurts "
                        "to put full weight on it, but I can still hobble.",
            "duration": "Today (under 24 hours)",
            "severity": 7,
            "meds": "None",
            "allergies": "No known allergies",
        },
        "outcome": {
            "diagnosis": "Grade 1-2 Left Lateral Ankle Sprain (No Fracture)",
            "rx_generic": "Naproxen 500mg + Compression Wrap (Generic)",
            "rx_brand": "Naprosyn 500mg + Brace Kit (Brand)",
            "notes": "Ottawa ankle rules negative, no X-ray needed. RICE x72h. Naproxen 500mg PO BID w/ food PRN pain. "
                     "F/u in 10 days if still unable to bear weight. Return if numbness, cold toes or rapidly spreading swelling.",
            "visit_fee": 110, "test_name": "Ottawa Ankle Rule Stability Exam", "test_fee": 25,
            "rx_generic_price": 15, "rx_brand_price": 64,
        },
    },
    "heart": {
        "label": "Vague: \"heart feels weird\"",
        "emoji": "💓",
        "intake": {
            "name": "Test Patient Rosa",
            "insurance": "ppo",
            "symptoms": "My heart feels weird on and off since yesterday, like it skips, and I've been more tired than usual.",
            "duration": "2-3 days",
            "severity": 4,
            "meds": "Multivitamin",
            "allergies": "Penicillin",
        },
        "outcome": {
            "diagnosis": "Benign Palpitations (Normal In-Clinic ECG)",
            "rx_generic": "",
            "rx_brand": "",
            "notes": "ECG NSR, HR 88. Pt reports 4-5 energy drinks/day. Reduce caffeine. "
                     "Holter monitor if sx persist >2 wk. Go to ED if CP, SOB or syncope.",
            "visit_fee": 130, "test_name": "12-Lead ECG", "test_fee": 60,
            "rx_generic_price": 0, "rx_brand_price": 0,
        },
    },
    "chest": {
        "label": "Red flag: chest pain",
        "emoji": "🚨",
        "intake": {
            "name": "Test Patient Alex",
            "insurance": "hmo",
            "symptoms": "I've had chest pressure since this morning that goes down my left arm, and I feel sweaty and sick to my stomach.",
            "duration": "Today (under 24 hours)",
            "severity": 8,
            "meds": "Atorvastatin 20mg",
            "allergies": "No known drug allergies",
        },
        "outcome": None,   # sent to emergency care, no clinic visit
    },
}


def public_list():
    return [{"id": k, "label": v["label"], "emoji": v["emoji"], "intake": v["intake"], "outcome": v["outcome"]}
            for k, v in SCENARIOS.items()]
