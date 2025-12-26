from flask import Flask, render_template, session, redirect, url_for, request, flash, jsonify
from functools import wraps
import os
import base64
import io
from PIL import Image
import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --- Configuration ---
# Secret key is required to use sessions (keep it secure!)
app.config['SECRET_KEY'] = os.urandom(24).hex() 

# --- MongoDB Configuration ---
client = MongoClient('mongodb://localhost:27017/')
db = client['smart_health_db']
users_collection = db['users']
doctors_collection = db['doctors']
appointments_collection = db['appointments']
medicines_collection = db['medicines']
lab_tests_collection = db['lab_tests']
specialties_collection = db['specialties']
lab_bookings_collection = db['lab_bookings']

# --- Login Required Decorator ---
# Use this to protect routes that guests should not access
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # If not logged in, send them to the auth page
            return redirect(url_for('auth_page'))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# 1. PUBLIC ROUTES (Accessible to everyone)
# ==========================================

@app.route('/')
def dashboard():
    """Main homepage - visible to everyone."""
    logged_in = 'user_id' in session
    return render_template('dashboard.html', logged_in=logged_in)

@app.route('/auth')
def auth_page():
    """Single page containing both Login and Register forms."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('auth.html')

@app.route('/check_medicine_camera')
def check_medicine_camera():
    """Feature: Camera identification (Public)."""
    return render_template('medicine_check.html', logged_in='user_id' in session)

@app.route('/doctors')
def view_doctors():
    """Feature: View All Doctors with Filters."""
    # Get filter parameters
    specialty_filter = request.args.get('specialty')
    gender_filter = request.args.get('gender')
    experience_filter = request.args.get('experience')
    sort_price = request.args.get('sort_price')
    search_query = request.args.get('search')

    query = {}
    if specialty_filter:
        query['specialty'] = specialty_filter
    if search_query:
        query['name'] = {'$regex': search_query, '$options': 'i'}
        
    if gender_filter:
        query['gender'] = gender_filter
    
    if experience_filter:
        # Filter doctors with experience >= selected value
        query['experience_years'] = {'$gte': int(experience_filter)}

    # Fetch doctors
    doctors_cursor = doctors_collection.find(query)
    doctors_list = list(doctors_cursor)

    # Sorting by Price
    if sort_price == 'asc':
        doctors_list.sort(key=lambda x: x.get('consultation_fees', 0))
    elif sort_price == 'desc':
        doctors_list.sort(key=lambda x: x.get('consultation_fees', 0), reverse=True)

    # Get specialties for dropdown
    specialties = list(specialties_collection.find({}, {'name': 1, 'icon': 1, '_id': 0}))

    return render_template('doctors_list.html', 
                           doctors=doctors_list, 
                           specialties=specialties,
                           selected_specialty=specialty_filter,
                           selected_gender=gender_filter,
                           selected_experience=experience_filter,
                           selected_sort=sort_price,
                           logged_in='user_id' in session)

@app.route('/doctors/<path:specialty>')
def view_doctors_by_specialty(specialty):
    """Redirect old route to new filter route."""
    return redirect(url_for('view_doctors', specialty=specialty))

@app.route('/lab_tests')
def view_lab_tests():
    """Feature: Browse Lab Tests (Public)."""
    category_filter = request.args.get('category')
    query = {}
    if category_filter:
        query['category'] = category_filter
        
    tests = list(lab_tests_collection.find(query))
    categories = lab_tests_collection.distinct('category')
    
    return render_template('lab_tests.html', tests=tests, categories=categories, selected_category=category_filter, logged_in='user_id' in session)

@app.route('/book_lab_test/<test_name>', methods=['POST'])
@login_required
def book_lab_test(test_name):
    """Feature: Book a Lab Test (Login Required)."""
    lab_bookings_collection.insert_one({
        'user_id': session['user_id'],
        'test_name': test_name,
        'date': datetime.datetime.now().strftime("%Y-%m-%d"),
        'status': 'Confirmed'
    })
    flash(f"Successfully booked: {test_name}. Check your Inbox.", "success")
    return redirect(url_for('view_lab_tests'))

@app.route('/inbox')
@login_required
def inbox():
    """Inbox: Appointments, Labs, Notifications."""
    user_id = session['user_id']
    appointments = list(appointments_collection.find({'user_id': user_id}))
    lab_bookings = list(lab_bookings_collection.find({'user_id': user_id}))
    
    # Mock Notifications & Medicines for Inbox view
    notifications = [
        {"title": "Appointment Confirmed", "message": "Dr. Sharma has confirmed your slot.", "time": "2 hrs ago"},
        {"title": "Lab Report Ready", "message": "Your CBC report is ready for download.", "time": "1 day ago"}
    ]
    
    return render_template('inbox.html', 
                           appointments=appointments, 
                           lab_bookings=lab_bookings, 
                           notifications=notifications, 
                           logged_in=True)

@app.route('/medicines')
def view_medicines():
    """Feature: Browse Medicines with Search & Filter."""
    search_query = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    illness_filter = request.args.get('illness', '')

    # Build MongoDB Query
    query = {}
    if search_query:
        # Case-insensitive search for name
        query['name'] = {'$regex': search_query, '$options': 'i'}
    
    if category_filter:
        query['category'] = category_filter
        
    if illness_filter:
        query['illness'] = illness_filter

    # Fetch medicines based on query
    medicines = list(medicines_collection.find(query))
    
    # Get unique categories for the dropdown filter
    categories = medicines_collection.distinct('category')
    # Get unique illnesses for the dropdown filter
    illnesses = medicines_collection.distinct('illness')

    return render_template('medicines_list.html', 
                           medicines=medicines, 
                           categories=categories, 
                           illnesses=illnesses,
                           selected_category=category_filter,
                           selected_illness=illness_filter,
                           logged_in='user_id' in session)

@app.route('/medicine/<medicine_id>')
def medicine_detail(medicine_id):
    """Feature: View detailed information about a specific medicine."""
    medicine = medicines_collection.find_one({'_id': ObjectId(medicine_id)})
    if not medicine:
        flash("Medicine not found.", "error")
        return redirect(url_for('view_medicines'))
    return render_template('medicine_detail.html', medicine=medicine, logged_in='user_id' in session)

# ==========================================
# 2. AUTHENTICATION LOGIC
# ==========================================

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    # Verify credentials with MongoDB
    user = users_collection.find_one({'email': email})

    if user and check_password_hash(user['password'], password):
        session['user_id'] = str(user['_id'])
        session['username'] = user['username']
        flash("Logged in successfully! Welcome back.", "success")
        return redirect(url_for('dashboard'))
    else:
        flash("Login Failed! Please check your email or password.", "error")
        return redirect(url_for('auth_page'))

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    # Check if user already exists
    if users_collection.find_one({'email': email}):
        flash("Email already registered. Please login.", "error")
        return redirect(url_for('auth_page'))

    hashed_password = generate_password_hash(password)
    users_collection.insert_one({'username': username, 'email': email, 'password': hashed_password})

    flash("Registration successful! Please login.", "success")
    return redirect(url_for('auth_page'))

@app.route('/logout')
def logout():
    """Logs the user out and clears the session."""
    session.clear()
    return redirect(url_for('dashboard'))

# ==========================================
# 3. PROTECTED ROUTES (Login Required)
# ==========================================

@app.route('/book_appointment', methods=['GET', 'POST'])
@login_required
def book_appointment():
    """Booking is only for logged-in users."""
    if request.method == 'POST':
        doctor_name = request.form.get('doctor_name')
        date = request.form.get('date')
        symptoms = request.form.get('symptoms')
        
        # Check Doctor's Daily Limit
        doctor = doctors_collection.find_one({'name': doctor_name})
        if doctor:
            limit = doctor.get('daily_patient_limit', 20)
            current_count = appointments_collection.count_documents({'doctor_name': doctor_name, 'date': date})
            if current_count >= limit:
                flash(f"Sorry, Dr. {doctor_name} is fully booked for {date} (Limit: {limit}). Please choose another date.", "error")
                return redirect(url_for('book_appointment'))

        appointment = {
            "user_id": session['user_id'],
            "username": session['username'],
            "doctor_name": doctor_name,
            "date": date,
            "symptoms": symptoms,
            "created_at": datetime.datetime.now()
        }
        appointments_collection.insert_one(appointment)
        flash("Appointment request sent successfully!", "success")
        return redirect(url_for('dashboard'))

    # Fetch doctors for the dropdown list
    selected_doctor = request.args.get('doctor')
    doctors = list(doctors_collection.find({}, {'name': 1, 'specialty': 1, 'consultation_fees': 1, 'consultation_type': 1, 'clinic_address': 1}))
    return render_template('book_appointment.html', logged_in=True, doctors=doctors, selected_doctor=selected_doctor)

@app.route('/my_health_records')
@login_required
def health_records():
    """Health records are private and require login."""
    # Mock Data for demonstration (In real app, fetch from DB)
    reports = [
        {"name": "Blood_Test_Report_Dec24.pdf", "date": "2024-12-24", "type": "Lab Report"},
        {"name": "XRay_Chest.jpg", "date": "2024-11-10", "type": "Imaging"}
    ]
    
    medicines_schedule = [
        {"name": "Paracetamol 500mg", "dosage": "1 Tablet", "time": "After Lunch", "status": "Pending"},
        {"name": "Vitamin C", "dosage": "1 Tablet", "time": "Morning", "status": "Taken"}
    ]
    
    return render_template('health_records.html', 
                           reports=reports, 
                           medicines=medicines_schedule, 
                           logged_in=True)

# ==========================================
# 4. AI PROCESSING LOGIC (The Core Concepts)
# ==========================================

class MedicalAI:
    """
    Encapsulates the AI modules requested: CNN, YOLO, OCR, NLP, Classification.
    """
    
    @staticmethod
    def preprocess_image(image_data):
        """Decodes base64 image for processing."""
        header, encoded = image_data.split(",", 1)
        data = base64.b64decode(encoded)
        image = Image.open(io.BytesIO(data))
        return image

    @staticmethod
    def detect_objects_yolo(image):
        """
        Concept: YOLO (You Only Look Once)
        Task: Locate medicine strips/labels.
        """
        # TODO: Load your YOLO model here (e.g., torch.hub.load(...))
        # results = model(image)
        # return results.xyxy[0]  # Bounding boxes
        return {"detected": True, "object": "Medicine Strip", "confidence": 0.95}

    @staticmethod
    def recognize_medicine_cnn(image):
        """
        Concept: CNN (Convolutional Neural Networks)
        Task: Recognize visual patterns (shape, color) to identify medicine.
        """
        # TODO: Load Keras/TF model
        # prediction = cnn_model.predict(processed_image)
        return {"name": "Paracetamol 500mg", "type": "Tablet", "confidence": 0.92}

    @staticmethod
    def extract_text_ocr(image):
        """
        Concept: OCR (Optical Character Recognition)
        Task: Extract text like '500mg', 'Batch No'.
        """
        # TODO: Use pytesseract
        # text = pytesseract.image_to_string(image)
        return "Paracetamol IP 500mg Batch No. GH452"

    @staticmethod
    def classify_safety(medicine_name, user_conditions):
        """
        Concept: Classification Algorithms (Naive Bayes/Decision Tree)
        Task: Classify as Safe/Harmful based on user history.
        """
        # Mock logic for demonstration
        harmful_interactions = {"Aspirin": ["Ulcers"], "Sugar": ["Diabetes"]}
        
        status = "Safe"
        warning = None
        
        # Simple rule/classification logic
        if "Paracetamol" in medicine_name:
            status = "Safe"
        
        return {"status": status, "warning": warning}

    @staticmethod
    def generate_explanation_nlp(medicine_name, ocr_text):
        """
        Concept: NLP (Natural Language Processing)
        Task: Generate understandable explanations.
        """
        return f"{medicine_name} is commonly used for fever and mild pain relief."

    @staticmethod
    def recommend_dosage_rule_based(medicine_name):
        """
        Concept: Rule-Based Recommendation System
        Task: Suggest dosage schedules.
        """
        rules = {
            "Paracetamol 500mg": "Take 1 tablet every 4-6 hours as needed for fever.",
            "Vitamin C": "Take 1 tablet daily in the morning."
        }
        return rules.get(medicine_name, "Consult a doctor for dosage.")

@app.route('/identify_medicine', methods=['POST'])
def identify_medicine():
    """API Endpoint to process camera image."""
    try:
        data = request.json
        image_data = data.get('image')
        
        # 1. Preprocess
        img = MedicalAI.preprocess_image(image_data)
        
        # 2. Run AI Pipelines
        yolo_res = MedicalAI.detect_objects_yolo(img)
        cnn_res = MedicalAI.recognize_medicine_cnn(img)
        ocr_text = MedicalAI.extract_text_ocr(img)
        safety = MedicalAI.classify_safety(cnn_res['name'], []) # Pass user history here
        nlp_desc = MedicalAI.generate_explanation_nlp(cnn_res['name'], ocr_text)
        dosage = MedicalAI.recommend_dosage_rule_based(cnn_res['name'])

        # 3. Database Integration: Fetch details from MongoDB if available
        db_medicine = medicines_collection.find_one({"name": cnn_res['name']})
        
        db_details = {}
        if db_medicine:
            # Use DB description if available, otherwise keep NLP one
            if db_medicine.get('description'):
                nlp_desc = db_medicine.get('description')
            
            db_details = {
                "price": db_medicine.get('price'),
                "category": db_medicine.get('category'),
                "stock": db_medicine.get('stock_quantity')
            }

        return jsonify({
            "success": True,
            "medicine_name": cnn_res['name'],
            "confidence": cnn_res['confidence'],
            "ocr_text": ocr_text,
            "safety_status": safety['status'],
            "description": nlp_desc,
            "dosage_recommendation": dosage,
            "db_details": db_details
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"success": False, "error": str(e)})

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == '__main__':
    # Ensure templates folder exists to avoid errors
    if not os.path.exists('templates'):
        os.makedirs('templates')
        
    app.run(debug=True)