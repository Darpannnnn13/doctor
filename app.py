from flask import Flask, render_template, request
import pandas as pd
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('departments.html')

@app.route('/colleges')
def colleges():
    # Get Request Parameters
    dept_filter = request.args.get('department', 'Polytechnic')
    round_filter = request.args.get('round', '1')
    location_filter = request.args.get('gender', '') 
    
    # Load CSV Data
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    if dept_filter == 'MCA':
        if location_filter == 'AI':
            subfolder = 'AI'
            csv_filename = f'PG_MCA_Diploma_CAP{round_filter}_AI_Cutoff_2025_26_colab_extracted.csv'
        else:
            subfolder = 'MH'
            csv_filename = f'PG_MCA_CAP{round_filter}_Cuttoff_data.csv'
        csv_path = os.path.join(base_dir, 'data', 'mca', subfolder, csv_filename)
    else:
        csv_filename = f'polytechnic_cutoff_data_cap_{round_filter}.csv'
        csv_path = os.path.join(base_dir, 'data', 'polytechnic', csv_filename)
        
    print(f"DEBUG: Attempting to load CSV from: {csv_path}")
    
    # Initialize empty list and specialties
    filtered_doctors = []
    specialties = []
    categories = []
    seat_types = []
    
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(csv_path, encoding='cp1252')
            
        # Normalize columns (lowercase, remove spaces) to match code expectations
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('-', '_')
        print(f"DEBUG: Columns found: {df.columns.tolist()}")
        
        # Handle AI file specific column names for cutoff score (Merit Marks/Score -> Percentile)
        if 'percentile' not in df.columns:
            if 'merit_marks' in df.columns:
                df['percentile'] = df['merit_marks']
            elif 'score' in df.columns:
                df['percentile'] = df['score']
            elif 'merit' in df.columns:
                df['percentile'] = df['merit']
            else:
                df['percentile'] = 0.0 # Fallback to prevent KeyError

        # Extract score from brackets if present (e.g. "(50.5)")
        if 'percentile' in df.columns and df['percentile'].dtype == 'object':
            extracted = df['percentile'].astype(str).str.extract(r'\(([\d\.]+)\)')[0]
            df['percentile'] = extracted.fillna(df['percentile'])

        # Handle Rank aliases
        if 'rank' not in df.columns:
            if 'merit_no' in df.columns:
                df['rank'] = df['merit_no']
            elif 'merit_rank' in df.columns:
                df['rank'] = df['merit_rank']

        # Handle Institution Name aliases (AI files)
        if 'institute_name' not in df.columns and 'institution_name' in df.columns:
            df['institute_name'] = df['institution_name']

        # Handle Seat Type aliases (AI files)
        if 'seat_type' not in df.columns and 'type' in df.columns:
            df['seat_type'] = df['type']
            
        # Handle Choice Code as Institute Code (User specified)
        if 'institute_code' not in df.columns and 'choice_code' in df.columns:
            df['institute_code'] = df['choice_code']

        # Ensure numeric columns are actually numbers
        if 'percentile' in df.columns:
            df['percentile'] = pd.to_numeric(df['percentile'], errors='coerce')
        if 'rank' in df.columns:
            df['rank'] = pd.to_numeric(df['rank'], errors='coerce')
        
        # Get unique courses for the dropdown from CSV
        if 'course_name' in df.columns:
            courses = sorted(df['course_name'].dropna().unique().tolist())
            if courses:
                specialties = [{"name": c, "icon": "🎓"} for c in courses]
        
        # Get unique categories and seat types
        if 'category' in df.columns:
            cats = sorted(df['category'].dropna().unique().tolist())
            if cats:
                categories = cats
        if 'seat_type' in df.columns:
            seats = sorted(df['seat_type'].dropna().unique().tolist())
            if seats:
                seat_types = seats
    else:
        print("DEBUG: CSV file not found!")
        df = pd.DataFrame()
    
    # Filtering Logic
    search_query = request.args.get('search', '').lower()
    specialty_filter = request.args.get('specialty', '')
    cutoff_filter = request.args.get('experience', '') # Using experience field for Cutoff
    rank_filter = request.args.get('rank', '')
    category_filter = request.args.get('category', '')
    seat_type_filter = request.args.get('seat_type', '')

    # Determine if we should load data (MCA AI allows loading without specialty)
    is_mca_ai = (dept_filter == 'MCA' and location_filter == 'AI')
    
    if (specialty_filter or is_mca_ai) and not df.empty:
        # Filter by Branch (Exact Match)
        temp_df = df
        if specialty_filter:
            temp_df = temp_df[temp_df['course_name'] == specialty_filter]

        # Filter by Search (Institute Name)
        if search_query:
            temp_df = temp_df[temp_df['institute_name'].str.lower().str.contains(search_query, na=False)]

        # Filter by Quota (Location)
        if location_filter and 'quota' in temp_df.columns:
            temp_df = temp_df[temp_df['quota'].str.contains(location_filter, na=False)]

        # Filter by Cutoff (Percentile)
        if cutoff_filter:
            try:
                user_marks = float(cutoff_filter)
                # Show colleges where cutoff is <= user marks
                temp_df = temp_df[temp_df['percentile'] <= user_marks]
            except ValueError:
                pass
        
        # Filter by Rank
        if rank_filter:
            try:
                user_rank = float(rank_filter)
                # Show colleges where cutoff rank >= user rank (meaning user qualifies)
                if 'rank' in temp_df.columns:
                    temp_df = temp_df[temp_df['rank'] >= user_rank]
            except ValueError:
                pass

        # Filter by Category
        if category_filter and 'category' in temp_df.columns:
            temp_df = temp_df[temp_df['category'] == category_filter]

        # Filter by Seat Type
        if seat_type_filter and 'seat_type' in temp_df.columns:
            temp_df = temp_df[temp_df['seat_type'] == seat_type_filter]
        
        # Sort by percentile descending
        if 'percentile' in temp_df.columns:
            temp_df = temp_df.sort_values(by='percentile', ascending=False)

        # Convert to dictionary list for template
        for _, row in temp_df.iterrows():
            filtered_doctors.append({
                "institute_code": row.get('institute_code', 'N/A'),
                "choice_code": row.get('choice_code', 'N/A'),
                "name": row.get('institute_name', 'Unknown Institute'),
                "specialty": row.get('course_name', 'MCA' if dept_filter == 'MCA' else 'N/A'),
                "experience": row.get('percentile', 0),      # Cutoff
                "gender": row.get('quota', location_filter if location_filter else 'N/A'), # Quota/Location
                "qualification": row.get('category', 'N/A'),     # Category
                "consultation_type": row.get('seat_type', 'N/A'),# Seat Type
                "status": row.get('status', 'N/A'),
                "rank": row.get('rank', 'N/A'),
                "stage": row.get('stage', 'N/A'),
                "image": "" # Placeholder
            })

    # Render specific template for MCA AI, otherwise standard template
    if dept_filter == 'MCA' and location_filter == 'AI':
        template_name = 'mca_ai.html'
    else:
        template_name = 'doctors.html'

    return render_template(template_name, 
                           doctors=filtered_doctors, 
                           specialties=specialties,
                           categories=categories,
                           seat_types=seat_types,
                           selected_specialty=specialty_filter,
                           selected_department=dept_filter,
                           selected_gender=location_filter,
                           selected_experience=cutoff_filter,
                           selected_rank=rank_filter,
                           selected_category=category_filter,
                           selected_seat_type=seat_type_filter,
                           selected_round=round_filter)

if __name__ == '__main__':
    app.run(debug=True)