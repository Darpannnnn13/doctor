from flask import Flask, render_template, request
import pandas as pd
import os
import re

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
            csv_filename = f'PG_MCA_Diploma_CAP{round_filter}_AI_Cutoff_2025_26_cleaned.csv'
        else:
            subfolder = 'MH'
            # Try both spellings for Cutoff/Cuttoff
            filenames_to_try = [
                f'PG_MCA_CAP{round_filter}_Cuttoff_data.csv',
                f'PG_MCA_CAP{round_filter}_Cutoff_data.csv'
            ]
            
            # Check which file exists
            csv_filename = filenames_to_try[0] # Default
            for fname in filenames_to_try:
                if os.path.exists(os.path.join(base_dir, 'data', 'mca', subfolder, fname)):
                    csv_filename = fname
                    break
            
        csv_path = os.path.join(base_dir, 'data', 'mca', subfolder, csv_filename)
    elif dept_filter == 'MBA':
        if location_filter == 'AI':
            subfolder = 'AI'
            csv_filename = f'MBA_CAP{round_filter}_AI - MBA_CAP{round_filter}_AI.csv'  # Assuming similar naming
        else:
            subfolder = 'MH'
            csv_filename = f'MBA_CAP{round_filter}_MHCutOff_2023_24 - MBA_CAP{round_filter}_MHCutOff_2023_24.csv'
            
        csv_path = os.path.join(base_dir, 'data', 'mba', subfolder, csv_filename)
    elif dept_filter == 'MTECH':
        # Only load data if round is explicitly selected
        if request.args.get('round') is None:
            csv_path = ""
        else:
            csv_filename = f'cap{round_filter}.csv'
            csv_path = os.path.join(base_dir, 'data', 'MTECH_ME', csv_filename)
    elif dept_filter == 'BCA':
        if location_filter == 'AI':
            subfolder = 'AI'
        else:
            subfolder = 'MH'
            
        search_dir = os.path.join(base_dir, 'data', 'bca', subfolder)
        csv_filename = f'cap{round_filter}.csv' # Default fallback for AI
        
        if os.path.exists(search_dir):
            # Try to find file matching CAP round
            for fname in os.listdir(search_dir):
                # Match 'cap1', 'CAP1', 'BCA_CAP1', etc.
                if fname.endswith('.csv') and f'cap{round_filter}' in fname.lower():
                    csv_filename = fname
                    break
            
            # Fallback: If specific round file not found, take the first CSV found
            if not os.path.exists(os.path.join(search_dir, csv_filename)):
                for fname in os.listdir(search_dir):
                    if fname.endswith('.csv'):
                        csv_filename = fname
                        break
        
        csv_path = os.path.join(search_dir, csv_filename)
    else:
        csv_filename = f'polytechnic_cutoff_data_cap_{round_filter}.csv'
        csv_path = os.path.join(base_dir, 'data', 'polytechnic', csv_filename)
        
    print(f"DEBUG: Attempting to load CSV from: {csv_path}")
    
    # Initialize empty list and specialties
    filtered_doctors = []
    specialties = []
    categories = []
    seat_types = []
    universities = []
    quotas = []
    areas = []
    
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(csv_path, encoding='cp1252')
            
        # Normalize columns (lowercase, remove spaces) to match code expectations
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('-', '_')
        print(f"DEBUG: Columns found: {df.columns.tolist()}")
        
        # Handle 'All India Merit' specifically for BCA AI (e.g. "1234(98.5)")
        if 'all_india_merit' in df.columns:
            def parse_merit(val):
                s = str(val)
                nums = re.findall(r"[\d\.]+", s)
                if len(nums) >= 2:
                    return int(nums[0]), float(nums[1]) # Rank, Percentile
                elif len(nums) == 1:
                    return int(nums[0]), 0.0
                return 0, 0.0
            
            # Apply parsing
            parsed_data = df['all_india_merit'].apply(lambda x: pd.Series(parse_merit(x)))
            df['rank'] = parsed_data[0]
            df['percentile'] = parsed_data[1]

        # Handle AI file specific column names for cutoff score (Merit Marks/Score -> Percentile)
        if 'percentile' not in df.columns:
            if 'merit_marks' in df.columns:
                df['percentile'] = df['merit_marks']
            elif 'score' in df.columns:
                df['percentile'] = df['score']
            elif 'merit' in df.columns:
                df['percentile'] = df['merit']
            elif 'marks_percentile' in df.columns:
                df['percentile'] = df['marks_percentile']
            elif 'hsc_percentage' in df.columns:
                df['percentile'] = df['hsc_percentage']
            elif 'percentage' in df.columns:
                df['percentile'] = df['percentage']
            elif 'hsc_marks' in df.columns:
                df['percentile'] = df['hsc_marks']
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
            elif 'merit_score' in df.columns:
                df['rank'] = df['merit_score']

        # Handle Institution Name aliases (AI files)
        if 'institute_name' not in df.columns and 'institution_name' in df.columns:
            df['institute_name'] = df['institution_name']
        
        # Handle MH file specific column names
        if 'institute_name' not in df.columns:
            if 'name_of_institute' in df.columns:
                df['institute_name'] = df['name_of_institute']
            elif 'college_name' in df.columns:
                df['institute_name'] = df['college_name']
            elif 'institute' in df.columns:
                df['institute_name'] = df['institute']
            elif 'name' in df.columns:
                df['institute_name'] = df['name']
            elif 'college_name' in df.columns:
                df['institute_name'] = df['college_name']
        
        # Handle Course Name aliases (Common in BCA files)
        if 'course_name' not in df.columns:
            if 'branch' in df.columns:
                df['course_name'] = df['branch']
            elif 'course' in df.columns:
                df['course_name'] = df['course']
            elif 'subject' in df.columns:
                df['course_name'] = df['subject']

        # Handle Seat Type aliases (AI files)
        if 'seat_type' not in df.columns and 'type' in df.columns:
            df['seat_type'] = df['type']
            
        # Handle Choice Code as Institute Code (User specified)
        if 'institute_code' not in df.columns and 'choice_code' in df.columns:
            df['institute_code'] = df['choice_code']
            
        # Handle Branch Code alias
        if 'choice_code' not in df.columns and 'branch_code' in df.columns:
            df['choice_code'] = df['branch_code']

        # Handle Category alias (e.g. category1)
        if 'category' not in df.columns and 'category1' in df.columns:
            df['category'] = df['category1']

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
        
        # Get unique universities (for MH)
        if 'university' in df.columns:
            unis = sorted(df['university'].dropna().unique().tolist())
            if unis:
                universities = unis
        
        # Get unique quotas
        if 'quota' in df.columns:
            qs = sorted(df['quota'].dropna().unique().tolist())
            if qs:
                quotas = qs
        
        # Extract Area from Institute Name (Format: "Name, Area")
        if 'institute_name' in df.columns:
            # Split by comma and take the last part as Area
            df['area'] = df['institute_name'].astype(str).apply(lambda x: x.split(',')[-1].strip() if ',' in x else 'Others')
            unique_areas = sorted(df['area'].unique().tolist())
            
            # Move 'Others' to the end
            if 'Others' in unique_areas:
                unique_areas.remove('Others')
                unique_areas.append('Others')

            if unique_areas:
                areas = unique_areas
    else:
        print("DEBUG: CSV file not found!")
        df = pd.DataFrame()
    
    # Filtering Logic
    search_query = request.args.get('search', '').lower()
    specialty_filter = request.args.get('specialty', '')
    cutoff_filter = request.args.get('experience', '') or request.args.get('percentile', '') # Using experience field for Cutoff
    rank_filter = request.args.get('rank', '') or request.args.get('merit_score', '')
    min_rank_filter = request.args.get('min_rank', '')
    max_rank_filter = request.args.get('max_rank', '')
    category_filter = request.args.get('category', '')
    seat_type_filter = request.args.get('seat_type', '')
    university_filter = request.args.get('university', '')
    area_filter = request.args.get('area', '')

    # Determine if we should load data (MCA and MBA allow loading without specialty)
    is_mca_or_mba = (dept_filter in ['MCA', 'MBA', 'BCA'])
    
    if (specialty_filter or is_mca_or_mba) and not df.empty:
        # Filter by Branch (Exact Match)
        temp_df = df
        if specialty_filter:
            temp_df = temp_df[temp_df['course_name'] == specialty_filter]

        # Filter by Search (Institute Name)
        if search_query and 'institute_name' in temp_df.columns:
            temp_df = temp_df[temp_df['institute_name'].str.lower().str.contains(search_query, na=False)]
            
        # Filter by Area
        if area_filter and 'area' in temp_df.columns:
            temp_df = temp_df[temp_df['area'] == area_filter]

        # Enforce Rank Range selection for MCA MH and MBA MH (Don't show colleges until Rank Range is selected)
        if ((dept_filter == 'MCA' and location_filter != 'AI') or (dept_filter == 'MBA' and location_filter != 'AI') or (dept_filter == 'BCA' and location_filter != 'AI')) and not (request.args.get('min_rank') and request.args.get('max_rank')):
            temp_df = temp_df.iloc[0:0]

        # Filter by Quota (Location)
        # Ignore 'MH' as it is used for file selection, not row filtering
        # For BCA AI, skip strict quota filtering to ensure data shows from the AI file
        if location_filter and location_filter != 'MH' and 'quota' in temp_df.columns and not (dept_filter == 'BCA' and location_filter == 'AI'):
            if location_filter == 'AI':
                # Match 'AI', 'All India', etc. case-insensitive
                temp_df = temp_df[temp_df['quota'].str.contains(r'AI|All India', case=False, na=False)]
            else:
                temp_df = temp_df[temp_df['quota'].str.contains(location_filter, na=False)]

        # Filter by Cutoff (Percentile)
        if cutoff_filter:
            try:
                user_marks = float(cutoff_filter)
                # Show colleges where cutoff is <= user marks
                temp_df = temp_df[temp_df['percentile'] <= user_marks]
            except ValueError:
                pass

        # Filter by Rank (Single Value)
        if rank_filter and 'rank' in temp_df.columns:
            try:
                user_rank = float(rank_filter)
                # Show colleges where cutoff rank >= user rank (User eligible)
                temp_df = temp_df[temp_df['rank'] >= user_rank]
            except ValueError:
                pass
        
        # Filter by Rank Range
        if min_rank_filter and max_rank_filter:
            try:
                min_rank = float(min_rank_filter)
                max_rank = float(max_rank_filter)
                if 'rank' in temp_df.columns:
                    temp_df = temp_df[(temp_df['rank'] >= min_rank) & (temp_df['rank'] <= max_rank)]
            except ValueError:
                pass
        
        # Filter by Single Rank (My Rank) - Show colleges where cutoff rank is higher (easier) than user rank
        if rank_filter and not (min_rank_filter or max_rank_filter):
            try:
                user_rank = float(rank_filter)
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
        
        # Filter by University
        if university_filter and 'university' in temp_df.columns:
            temp_df = temp_df[temp_df['university'] == university_filter]
        
        # Sort by percentile descending
        if 'percentile' in temp_df.columns:
            temp_df = temp_df.sort_values(by='percentile', ascending=False)

        # Convert to dictionary list for template
        for _, row in temp_df.iterrows():
            doc_dict = row.to_dict()
            # Clean NaNs for JSON serialization
            for k, v in doc_dict.items():
                if pd.isna(v):
                    doc_dict[k] = None
            
            doc_dict.update({
                "institute_code": row.get('institute_code', 'N/A'),
                "choice_code": row.get('choice_code', 'N/A'),
                "name": row.get('institute_name', 'Unknown Institute'),
                "specialty": row.get('course_name', 'BCA' if dept_filter == 'BCA' else 'MTECH' if dept_filter == 'MTECH' else 'MBA' if dept_filter == 'MBA' else 'MCA' if dept_filter == 'MCA' else 'N/A'),
                "experience": row.get('percentile', 0),      # Cutoff
                "gender": row.get('quota', location_filter if location_filter else 'N/A'), # Quota/Location
                "qualification": row.get('category', 'N/A'),     # Category
                "consultation_type": row.get('seat_type', 'N/A'),# Seat Type
                "rank": row.get('rank', 'N/A'),
                "stage": row.get('stage', 'N/A'),
                "image": "", # Placeholder
                "percentile": row.get('percentile', 'N/A'),
                "merit_score": row.get('rank', 'N/A'),
                "university": row.get('university', 'N/A'),
                "status": row.get('status', 'N/A')
            })
            filtered_doctors.append(doc_dict)

    # Render specific template for MCA/MBA AI/MH, otherwise standard template
    if dept_filter == 'MCA':
        if location_filter == 'AI':
            template_name = 'mca_ai.html'
        else:
            template_name = 'mca_mh.html'
    elif dept_filter == 'MBA':
        if location_filter == 'AI':
            template_name = 'mba_ai.html'
        else:
            template_name = 'mba_mh.html'
    elif dept_filter == 'MTECH':
        template_name = 'mtech.html'
        
        # Grouping Logic for MTech (Group by College)
        grouped = {}
        for doc in filtered_doctors:
            code = doc['institute_code']
            if code not in grouped:
                grouped[code] = doc.copy()
                grouped[code]['cutoffs'] = []
            grouped[code]['cutoffs'].append(doc)
        filtered_doctors = list(grouped.values())
    elif dept_filter == 'BCA':
        if location_filter == 'AI':
            template_name = 'bca_ai.html'
        else:
            template_name = 'bca_mh.html'
    else:
        template_name = 'doctors.html'

    return render_template(template_name, 
                           doctors=filtered_doctors, 
                           specialties=specialties,
                           categories=categories,
                           seat_types=seat_types,
                           universities=universities,
                           quotas=quotas,
                           areas=areas,
                           selected_specialty=specialty_filter,
                           selected_department=dept_filter,
                           selected_gender=location_filter,
                           selected_experience=cutoff_filter,
                           selected_rank=rank_filter,
                           selected_min_rank=min_rank_filter,
                           selected_max_rank=max_rank_filter,
                           selected_category=category_filter,
                           selected_seat_type=seat_type_filter,
                           selected_university=university_filter,
                           selected_area=area_filter,
                           selected_round=request.args.get('round') if dept_filter == 'MTECH' else round_filter)

@app.route('/details')
def details():
    dept_filter = request.args.get('department', 'MCA')
    round_filter = request.args.get('round', '1')
    location_filter = request.args.get('gender', '')
    institute_code = request.args.get('code')

    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    if dept_filter == 'MCA':
        if location_filter == 'AI':
            subfolder = 'AI'
            csv_filename = f'PG_MCA_Diploma_CAP{round_filter}_AI_Cutoff_2025_26_cleaned.csv'
        else:
            subfolder = 'MH'
            # Try both spellings for Cutoff/Cuttoff
            filenames_to_try = [
                f'PG_MCA_CAP{round_filter}_Cuttoff_data.csv',
                f'PG_MCA_CAP{round_filter}_Cutoff_data.csv'
            ]
            
            # Check which file exists
            csv_filename = filenames_to_try[0] # Default
            for fname in filenames_to_try:
                if os.path.exists(os.path.join(base_dir, 'data', 'mca', subfolder, fname)):
                    csv_filename = fname
                    break
        csv_path = os.path.join(base_dir, 'data', 'mca', subfolder, csv_filename)
    elif dept_filter == 'MTECH':
        csv_filename = f'cap{round_filter}.csv'
        csv_path = os.path.join(base_dir, 'data', 'MTECH_ME', csv_filename)
    elif dept_filter == 'MBA':
        if location_filter == 'AI':
            subfolder = 'AI'
            csv_filename = f'MBA_CAP{round_filter}_AI - MBA_CAP{round_filter}_AI.csv'
        else:
            subfolder = 'MH'
            csv_filename = f'MBA_CAP{round_filter}_MHCutOff_2023_24 - MBA_CAP{round_filter}_MHCutOff_2023_24.csv'
        csv_path = os.path.join(base_dir, 'data', 'mba', subfolder, csv_filename)
    elif dept_filter == 'BCA':
        if location_filter == 'AI':
            subfolder = 'AI'
        else:
            subfolder = 'MH'
            
        search_dir = os.path.join(base_dir, 'data', 'bca', subfolder)
        csv_filename = f'BCA_CAP{round_filter}_{subfolder}.csv'
        
        if os.path.exists(search_dir):
            # Try to find file matching CAP round
            for fname in os.listdir(search_dir):
                if fname.endswith('.csv') and f'CAP{round_filter}' in fname:
                    csv_filename = fname
                    break
            # Fallback
            if not os.path.exists(os.path.join(search_dir, csv_filename)):
                for fname in os.listdir(search_dir):
                    if fname.endswith('.csv'):
                        csv_filename = fname
                        break
        csv_path = os.path.join(search_dir, csv_filename)
    else:
        csv_filename = f'polytechnic_cutoff_data_cap_{round_filter}.csv'
        csv_path = os.path.join(base_dir, 'data', 'polytechnic', csv_filename)

    college_details = []
    college_info = {}

    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(csv_path, encoding='cp1252')

        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('-', '_')
        
        # Handle Aliases
        if 'institute_code' not in df.columns and 'choice_code' in df.columns:
            df['institute_code'] = df['choice_code']
        
        if 'percentile' not in df.columns:
            if 'merit_marks' in df.columns: df['percentile'] = df['merit_marks']
            elif 'score' in df.columns: df['percentile'] = df['score']
            elif 'marks_percentile' in df.columns: df['percentile'] = df['marks_percentile']
            
        if 'rank' not in df.columns:
            if 'merit_no' in df.columns: df['rank'] = df['merit_no']
            elif 'merit_score' in df.columns: df['rank'] = df['merit_score']

        if 'institute_code' in df.columns and institute_code:
            df['institute_code'] = df['institute_code'].astype(str).str.replace(r'\.0$', '', regex=True)
            match = df[df['institute_code'] == str(institute_code)]
            
            if not match.empty:
                college_details = match.to_dict('records')
                first_row = match.iloc[0]
                college_info = {
                    "code": first_row.get('institute_code'),
                    "name": first_row.get('institute_name', first_row.get('institution_name', 'Unknown')),
                    "university": first_row.get('university', 'N/A')
                }

    return render_template('details.html', info=college_info, cutoffs=college_details)

if __name__ == '__main__':
    app.run(debug=True)