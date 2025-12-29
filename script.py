import pandas as pd
import re
import os

# Define base directory relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "bca", "AI")

COMBINED_COL = "All India Merit"

def split_merit_score(value):
    if pd.isna(value):
        return pd.Series([None, None])

    # extract integers and decimals
    numbers = re.findall(r"\d+\.\d+|\d+", str(value))

    if len(numbers) >= 2:
        # Value outside bracket is Merit Score (Rank), Value inside is Percentile
        # e.g. 1234(98.5) -> numbers=['1234', '98.5']
        try:
            merit_rank = int(numbers[0])
            score_percentile = float(numbers[1])
        except ValueError:
            merit_rank, score_percentile = None, None
    elif len(numbers) == 1:
        try:
            merit_rank = int(numbers[0])
            score_percentile = None
        except ValueError:
            merit_rank, score_percentile = None, None
    else:
        merit_rank, score_percentile = None, None

    return pd.Series([merit_rank, score_percentile])

<<<<<<< HEAD
# Process CAP rounds 1 to 4
for i in range(1, 5):
    input_filename = f"PG_MCA_Diploma_CAP{i}_AI_Cutoff_2025_26_colab_extracted.csv"
    file_path = os.path.join(DATA_DIR, input_filename)

    if os.path.exists(file_path):
        print(f"Processing: {input_filename}")
        df = pd.read_csv(file_path)
        
        # Apply split and name columns 'rank' and 'percentile' for app.py compatibility
        df[["rank", "percentile"]] = df[COMBINED_COL].apply(split_merit_score)
        # Handle different column formats
        if COMBINED_COL in df.columns:
            # Old format: Split "Merit (Score)"
            df[["rank", "percentile"]] = df[COMBINED_COL].apply(split_merit_score)
        else:
            # New format: Rename existing columns if present
            if 'merit_score' in df.columns:
                df.rename(columns={'merit_score': 'rank'}, inplace=True)
            if 'marks_percentile' in df.columns:
                df.rename(columns={'marks_percentile': 'percentile'}, inplace=True)

        output_filename = f"PG_MCA_Diploma_CAP{i}_AI_Cutoff_2025_26_cleaned.csv"
        output_path = os.path.join(DATA_DIR, output_filename)
        try:
            df.to_csv(output_path, index=False)
            print(f"✅ Saved: {output_filename}")
        except PermissionError:
            print(f"❌ Permission denied: {output_filename} is open. Please close it.")
    else:
        print(f"⚠️ File not found: {input_filename}")

# Process MTech CAP rounds
DATA_DIR_MTECH = os.path.join(BASE_DIR, "data", "MTECH_ME")
for i in range(1, 5):
    input_filename = f"cap{i}.csv"
    file_path = os.path.join(DATA_DIR_MTECH, input_filename)

    if os.path.exists(file_path):
        print(f"Processing MTech: {input_filename}")
        df = pd.read_csv(file_path)
        
        # Clean columns if needed
        if COMBINED_COL in df.columns:
            df[["rank", "percentile"]] = df[COMBINED_COL].apply(split_merit_score)
        
        # Ensure rank/percentile exist
        if 'merit_score' in df.columns and 'rank' not in df.columns:
             df.rename(columns={'merit_score': 'rank'}, inplace=True)

        output_filename = f"cap{i}.csv"
        output_path = os.path.join(DATA_DIR_MTECH, output_filename)
        try:
            df.to_csv(output_path, index=False)
            print(f"✅ Saved: {output_filename}")
        except PermissionError:
            print(f"❌ Permission denied: {output_filename} is open.")
=======
# Process all CSV files in the BCA AI directory
if os.path.exists(DATA_DIR):
    for filename in os.listdir(DATA_DIR):
        # Match cap1.csv, cap2.csv etc. or other patterns
        if filename.endswith(".csv") and "cleaned" not in filename and "cap" in filename.lower():
            file_path = os.path.join(DATA_DIR, filename)
            print(f"Processing: {filename}")
            
            try:
                df = pd.read_csv(file_path)
                
                if COMBINED_COL in df.columns:
                    print(f"Found column '{COMBINED_COL}', splitting...")
                    df[["rank", "percentile"]] = df[COMBINED_COL].apply(split_merit_score)
                    
                    output_filename = filename.replace(".csv", "_cleaned.csv")
                    output_path = os.path.join(DATA_DIR, output_filename)
                    df.to_csv(output_path, index=False)
                    print(f"✅ Saved: {output_filename}")
                else:
                    print(f"⚠️ Column '{COMBINED_COL}' not found in {filename}")
            
            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")
else:
    print(f"Directory not found: {DATA_DIR}")
>>>>>>> daafe13 (bca)
