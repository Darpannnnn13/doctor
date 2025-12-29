import pandas as pd
import re
import os

# Define base directory relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "mca", "AI")

COMBINED_COL = "Merit (Score)"

def split_merit_score(value):
    if pd.isna(value):
        return pd.Series([None, None])

    # extract integers and decimals
    numbers = re.findall(r"\d+\.\d+|\d+", str(value))

    if len(numbers) >= 2:
        merit_rank = int(numbers[0])
        score_percentile = float(numbers[1])
    elif len(numbers) == 1:
        merit_rank = int(numbers[0])
        score_percentile = None
    else:
        merit_rank, score_percentile = None, None

    return pd.Series([merit_rank, score_percentile])

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