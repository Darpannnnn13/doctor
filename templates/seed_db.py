from pymongo import MongoClient
from werkzeug.security import generate_password_hash
import datetime
import random

# --- Configuration ---
# Connect to the same MongoDB instance as app.py
client = MongoClient('mongodb://localhost:27017/')
db = client['smart_health_db']

def seed_database():
    print("🌱 Starting Database Seeding...")

    # 1. Seed Specialties
    db.specialties.delete_many({})
    specialties_data = [
        {"name": "General Physician", "description": "Common health issues and checkups", "icon": "🩺"},
        {"name": "Dermatology", "description": "Skin, hair, and nail treatments", "icon": "🧴"},
        {"name": "Obstetrics & Gynecology", "description": "Women's reproductive health", "icon": "👩‍⚕️"},
        {"name": "Orthopaedics", "description": "Bones, joints, and muscles", "icon": "🦴"},
        {"name": "ENT (Ear, Nose, Throat)", "description": "Ear, Nose, and Throat conditions", "icon": "👂"},
        {"name": "Neurology", "description": "Brain and nervous system disorders", "icon": "🧠"},
        {"name": "Cardiology", "description": "Heart and cardiovascular health", "icon": "❤️"},
        {"name": "Urology", "description": "Urinary tract & male reproductive system", "icon": "🚽"},
        {"name": "Gastroenterology / GI", "description": "Digestive system health", "icon": "🍎"},
        {"name": "Psychiatry", "description": "Mental health and disorders", "icon": "🧘"},
        {"name": "Paediatrics", "description": "Medical care for infants and children", "icon": "👶"},
        {"name": "Pulmonology", "description": "Respiratory system health", "icon": "🫁"},
        {"name": "Endocrinology", "description": "Hormone and metabolic disorders", "icon": "🧬"},
        {"name": "Nephrology", "description": "Kidney care and diseases", "icon": "💧"},
        {"name": "Neurosurgery", "description": "Surgery of the nervous system", "icon": "🏥"},
        {"name": "Rheumatology", "description": "Joints and autoimmune diseases", "icon": "🦵"},
        {"name": "Ophthalmology", "description": "Eye care and surgery", "icon": "👁️"},
        {"name": "Surgical Gastroenterology", "description": "Surgery of the digestive system", "icon": "🔪"},
        {"name": "Infectious Disease", "description": "Infections and viral diseases", "icon": "🦠"},
        {"name": "General & Laparoscopic Surgery", "description": "General surgical procedures", "icon": "✂️"},
        {"name": "Psychology", "description": "Mental well-being and therapy", "icon": "🧠"},
        {"name": "Medical Oncology", "description": "Cancer treatment and care", "icon": "🎗️"},
        {"name": "Diabetology", "description": "Diabetes management", "icon": "🩸"},
        {"name": "Dentistry", "description": "Dental and oral health", "icon": "🦷"}
    ]
    db.specialties.insert_many(specialties_data)
    print(f"✅ Inserted {len(specialties_data)} specialties.")

    # 2. Seed Doctors (Dynamic Generation)
    db.doctors.delete_many({})
    
    male_names = ["Aarav", "Vihaan", "Aditya", "Sai", "Arjun", "Reyansh", "Muhammad", "Rohan", "Krishna", "Ishaan", "Shaurya", "Atharva", "Kabir", "Ayaan", "Dhruv", "Ryan", "Ansh", "Kian", "Viraj", "Aaryan"]
    female_names = ["Aadhya", "Diya", "Saanvi", "Ananya", "Kiara", "Pari", "Riya", "Anvi", "Myra", "Aarohi", "Avni", "Amaira", "Anaisha", "Prisha", "Mishka", "Ira", "Shanaya", "Siya", "Vanya", "Kyra"]
    last_names = ["Sharma", "Verma", "Patil", "Mehta", "Gupta", "Malhotra", "Singh", "Kumar", "Reddy", "Nair", "Iyer", "Chatterjee", "Das", "Joshi", "Desai", "Jain", "Chopra", "Khanna", "Saxena", "Bhat"]

    clinic_addresses = [
        "Life Care Clinic, 123 Health St, Mumbai",
        "City Hospital, 45 Wellness Ave, Delhi",
        "Ortho Care Center, 789 Bone Rd, Bangalore",
        "Heart Institute, 101 Pulse Ln, Chennai",
        "Skin & Glow Clinic, 55 Derma Way, Pune"
    ]

    doctors_data = []

    for spec in specialties_data:
        # Generate between 6 and 8 doctors per specialty
        num_docs = random.randint(6, 8)
        
        for _ in range(num_docs):
            is_male = random.choice([True, False])
            gender = "Male" if is_male else "Female"
            first_name = random.choice(male_names) if is_male else random.choice(female_names)
            last_name = random.choice(last_names)
            full_name = f"Dr. {first_name} {last_name}"
            
            # Generate random image URL
            gender_folder = "men" if is_male else "women"
            img_id = random.randint(1, 99)
            image_url = f"https://randomuser.me/api/portraits/{gender_folder}/{img_id}.jpg"
            
            exp = random.randint(3, 25)
            fees = random.choice([500, 800, 1000, 1200, 1500, 2000])
            status = random.choices(["Available", "Busy", "On Leave"], weights=[0.7, 0.2, 0.1])[0]
            
            consultation_type = random.choice(["In-Clinic", "Online", "Online & Clinic"])
            address = random.choice(clinic_addresses) if "Clinic" in consultation_type else "Online Only"
            daily_limit = random.randint(10, 25)
            
            # Determine qualification based on specialty
            qual = "MBBS, MD"
            if "Dentistry" in spec['name']: qual = "BDS, MDS"
            elif "Surgery" in spec['name'] or "Ortho" in spec['name']: qual = "MBBS, MS"
            
            doctors_data.append({
                "name": full_name,
                "specialty": spec['name'],
                "qualification": qual,
                "experience_years": exp,
                "experience": f"{exp}+ Yrs",
                "consultation_type": consultation_type,
                "status": status,
                "gender": gender,
                "consultation_fees": fees,
                "clinic_address": address,
                "daily_patient_limit": daily_limit,
                "image": image_url
            })

    db.doctors.insert_many(doctors_data)
    print(f"✅ Inserted {len(doctors_data)} doctors into 'doctors' collection.")

    # 3. Seed Lab Tests
    db.lab_tests.delete_many({})
    lab_tests_list = [
        ("Complete Blood Count (CBC)", "Blood Tests", "Hemoglobin, RBC, WBC, Platelets", 299, "6 Hours"),
        ("Full Body Checkup", "Full Body Checkups", "70+ Parameters (Blood, Urine, Liver, Kidney)", 1499, "24 Hours"),
        ("Thyroid Profile (Total)", "Blood Tests", "T3, T4, TSH", 499, "12 Hours"),
        ("Diabetes Screening (HbA1c)", "Blood Tests", "Average Blood Sugar (Past 3 months)", 399, "8 Hours"),
        ("Liver Function Test (LFT)", "Blood Tests", "Bilirubin, SGOT, SGPT, Albumin", 599, "12 Hours"),
        ("Kidney Function Test (KFT)", "Blood Tests", "Creatinine, Urea, Uric Acid", 599, "12 Hours"),
        ("Lipid Profile", "Blood Tests", "Cholesterol, Triglycerides, HDL, LDL", 699, "12 Hours"),
        ("Urine Routine & Microscopy", "Urine Tests", "Physical, Chemical, Microscopic Exam", 199, "6 Hours"),
        ("Vitamin D Total", "Vitamin Tests", "25-OH Vitamin D", 999, "24 Hours"),
        ("Vitamin B12", "Vitamin Tests", "Cyanocobalamin levels", 899, "24 Hours"),
        ("Iron Studies", "Blood Tests", "Iron, TIBC, Transferrin", 750, "12 Hours"),
        ("Calcium", "Blood Tests", "Serum Calcium", 250, "6 Hours"),
        ("Electrolytes", "Blood Tests", "Sodium, Potassium, Chloride", 350, "6 Hours"),
        ("C-Reactive Protein (CRP)", "Blood Tests", "Inflammation Marker", 450, "6 Hours"),
        ("Erythrocyte Sedimentation Rate (ESR)", "Blood Tests", "Inflammation", 150, "4 Hours"),
        ("H. Pylori Antigen", "Stool/Breath", "Helicobacter Pylori", 1200, "24 Hours"),
        ("Dengue NS1 Antigen", "Fever Tests", "Dengue Virus", 800, "6 Hours"),
        ("Malaria Antigen", "Fever Tests", "Plasmodium Vivax/Falciparum", 400, "4 Hours"),
        ("Typhoid Widal", "Fever Tests", "Salmonella Typhi", 300, "6 Hours"),
        ("HIV Duo Test", "STD Tests", "p24 Antigen + Antibodies", 1500, "24 Hours"),
        ("Hepatitis B Surface Antigen", "Infection Tests", "HBsAg", 600, "12 Hours"),
        ("Hepatitis C Antibody", "Infection Tests", "Anti-HCV", 800, "12 Hours"),
        ("Syphilis (VDRL)", "STD Tests", "Treponema Pallidum", 300, "6 Hours"),
        ("Blood Group & Rh", "Blood Tests", "ABO & Rh Factor", 150, "2 Hours"),
        ("Coagulation Profile", "Blood Tests", "PT, INR, APTT", 1200, "12 Hours"),
        ("Pancreatic Profile", "Blood Tests", "Amylase, Lipase", 1500, "24 Hours"),
        ("Arthritis Profile", "Blood Tests", "RA Factor, Anti-CCP", 2000, "24 Hours"),
        ("Allergy Panel (Food)", "Allergy Tests", "Common Food Allergens", 3500, "48 Hours"),
        ("Beta HCG", "Hormone Tests", "Pregnancy Hormone", 600, "6 Hours"),
        ("COVID-19 RT-PCR", "COVID", "SARS-CoV-2 Detection", 600, "12-24 Hours")
    ]
    
    lab_tests_data = []
    for name, cat, params, price, time in lab_tests_list:
        lab_tests_data.append({
            "name": name,
            "category": cat,
            "parameters": params,
            "price": price,
            "delivery_time": time
        })
        
    db.lab_tests.insert_many(lab_tests_data)
    print(f"✅ Inserted {len(lab_tests_data)} lab tests.")

    # 4. Seed Medicines
    db.medicines.delete_many({})
    
    illness_map = {
        "Fever": ["Paracetamol", "Ibuprofen", "Aspirin", "Mefenamic Acid"],
        "Cold": ["Cetirizine", "Chlorpheniramine", "Phenylephrine", "Levocetirizine"],
        "Cough": ["Dextromethorphan", "Ambroxol", "Guaifenesin", "Codeine Syrup"],
        "Headache": ["Saridon", "Disprin", "Naproxen", "Migraine Relief"],
        "Body Pain": ["Diclofenac", "Aceclofenac", "Tramadol", "Piroxicam"],
        "Infection": ["Amoxicillin", "Azithromycin", "Ciprofloxacin", "Doxycycline", "Ofloxacin"],
        "Acidity": ["Omeprazole", "Pantoprazole", "Ranitidine", "Esomeprazole", "Antacid Gel"],
        "Diabetes": ["Metformin", "Glimepiride", "Sitagliptin", "Insulin", "Vildagliptin"],
        "Hypertension": ["Amlodipine", "Telmisartan", "Losartan", "Enalapril", "Atenolol"],
        "Skin Infection": ["Clotrimazole", "Miconazole", "Fusidic Acid", "Ketoconazole"],
        "Vitamin Deficiency": ["Vitamin C", "Vitamin B12", "Vitamin D3", "Multivitamin", "Calcium + D3"],
        "Anxiety": ["Alprazolam", "Clonazepam", "Escitalopram", "Sertraline"],
        "Asthma": ["Salbutamol", "Montelukast", "Budesonide", "Formoterol"],
        "Allergy": ["Fexofenadine", "Loratadine", "Desloratadine", "Bilastine"],
        "Diarrhea": ["Loperamide", "ORS", "Probiotics", "Racecadotril"]
    }
    
    medicines_data = []
    brands = ["Pharma", "Care", "Health", "Life", "Cure", "Med", "Well", "Gen", "Bio", "Sun"]
    
    for illness, drugs in illness_map.items():
        for drug in drugs:
            # Create variations to reach high count
            for dosage in ["250mg", "500mg", "650mg", "10mg", "20mg", "5ml", "10ml"]:
                # Skip unrealistic dosages for some (simplified logic)
                if "ml" in dosage and "Syrup" not in drug and "Gel" not in drug: continue
                if "mg" in dosage and ("Syrup" in drug or "Gel" in drug): continue
                
                for brand_suffix in brands[:3]: # Use 3 brands per drug/dosage combo
                    # Randomize price and stock
                    price = random.randint(2, 50) * 10 - 1 # e.g. 19, 29...
                    stock = random.randint(10, 200)
                    
                    full_name = f"{drug} {dosage} ({brand_suffix})"
                    
                    # Determine category roughly
                    category = "General"
                    if illness in ["Fever", "Headache", "Body Pain"]: category = "Pain Relief"
                    elif illness in ["Cold", "Cough", "Allergy", "Asthma"]: category = "Respiratory"
                    elif illness == "Infection": category = "Antibiotics"
                    elif illness == "Acidity": category = "Gastrointestinal"
                    elif illness == "Diabetes": category = "Diabetes Care"
                    elif illness == "Hypertension": category = "Cardiology"
                    elif illness == "Skin Infection": category = "Dermatology"
                    elif illness == "Vitamin Deficiency": category = "Supplements"
                    
                    medicines_data.append({
                        "name": full_name,
                        "category": category,
                        "price": f"{price}.00",
                        "description": f"Used for {illness}. {drug} based medication.",
                        "stock_quantity": stock,
                        "age_advice": "Consult Doctor",
                        "dosage": "As prescribed",
                        "illness": illness,
                        "side_effects": "Consult Doctor",
                        "manufacturer": f"{brand_suffix} Pharmaceuticals"
                    })
    
    db.medicines.insert_many(medicines_data)
    print(f"✅ Inserted {len(medicines_data)} medicines.")

    # 5. Seed Test User (Optional)
    if db.users.count_documents({'email': 'test@example.com'}) == 0:
        test_user = {
            "username": "Test Patient",
            "email": "test@example.com",
            "password": generate_password_hash("password123"), # Always hash passwords!
            "created_at": datetime.datetime.now()
        }
        db.users.insert_one(test_user)
        print("✅ Inserted test user: test@example.com / password123")
    else:
        print("ℹ️  Test user already exists.")

    print("\n🎉 Database seeded successfully!")

if __name__ == "__main__":
    seed_database()