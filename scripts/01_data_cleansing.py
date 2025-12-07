"""
Data Cleansing Script
Handles null values, drops invalid records, and generates data quality reports
"""
import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Define paths
RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")
PROCESSED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed")
STATS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "stats")

# Create output directories if they don't exist
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
os.makedirs(STATS_DIR, exist_ok=True)

def load_csv_files():
    """Load all 4 CSV files into pandas DataFrames"""
    print("Loading CSV files...")
    
    files = {
        'beneficiary': 'Train_Beneficiarydata-1542865627584.csv',
        'inpatient': 'Train_Inpatientdata-1542865627584.csv',
        'outpatient': 'Train_Outpatientdata-1542865627584.csv',
        'provider': 'Train-1542865627584.csv'
    }
    
    dataframes = {}
    for key, filename in files.items():
        filepath = os.path.join(RAW_DATA_DIR, filename)
        if os.path.exists(filepath):
            print(f"  Loading {filename}...")
            dataframes[key] = pd.read_csv(filepath)
            print(f"    Loaded {len(dataframes[key])} records")
        else:
            print(f"  WARNING: {filename} not found at {filepath}")
            dataframes[key] = None
    
    return dataframes

def convert_dates(df, date_columns):
    """Convert date columns to datetime"""
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce', format='%Y-%m-%d')
    return df

def generate_initial_report(dfs):
    """Generate initial data quality report"""
    report = []
    report.append("=" * 80)
    report.append("INITIAL DATA QUALITY REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    for name, df in dfs.items():
        if df is not None:
            report.append(f"\n{name.upper()} Dataset")
            report.append("-" * 80)
            report.append(f"Total Records: {len(df)}")
            report.append(f"Total Columns: {len(df.columns)}")
            report.append("\nNull Counts:")
            null_counts = df.isnull().sum()
            for col, count in null_counts[null_counts > 0].items():
                pct = (count / len(df)) * 100
                report.append(f"  {col}: {count} ({pct:.2f}%)")
    
    return "\n".join(report)

def clean_beneficiary_data(df):
    """Clean beneficiary data"""
    if df is None:
        return None
    
    print("\nCleaning beneficiary data...")
    initial_count = len(df)
    
    # Convert dates
    date_cols = ['DOB', 'DOD']
    df = convert_dates(df, date_cols)
    
    # Transform nulls
    # DOD: null means alive, set isDeceased = 0
    df['isDeceased'] = df['DOD'].notna().astype(int)
    
    # County and State: Replace null with "UNKNOWN"
    df['County'] = df['County'].fillna('UNKNOWN')
    df['State'] = df['State'].fillna('UNKNOWN')
    
    # Calculate age from DOB
    current_date = pd.Timestamp.now()
    df['age'] = ((current_date - df['DOB']) / pd.Timedelta(days=365.25)).round().astype('Int64')
    
    # Keep chronic condition columns as boolean (convert Y/N to 1/0)
    chronic_cols = [col for col in df.columns if 'ChronicCond' in col or 'RenalDiseaseIndicator' in col]
    for col in chronic_cols:
        if col in df.columns:
            # Handle Y/N values: Y -> 1, N -> 0, null -> 0
            df[col] = df[col].replace({'Y': 1, 'N': 0, 'y': 1, 'n': 0})
            df[col] = df[col].fillna(0).astype(int)
    
    print(f"  Processed {len(df)} records (dropped {initial_count - len(df)})")
    return df

def clean_provider_data(df):
    """Clean provider data"""
    if df is None:
        return None
    
    print("\nCleaning provider data...")
    initial_count = len(df)
    
    # Drop records with null Provider
    df = df.dropna(subset=['Provider'])
    
    # Set isFraud flag
    df['isFraud'] = (df['PotentialFraud'] == 'Yes').astype(int)
    
    print(f"  Processed {len(df)} records (dropped {initial_count - len(df)})")
    return df

def clean_claims_data(inpatient_df, outpatient_df):
    """Clean claims data (inpatient and outpatient)"""
    print("\nCleaning claims data...")
    
    cleaned_dfs = {}
    
    for name, df in [('inpatient', inpatient_df), ('outpatient', outpatient_df)]:
        if df is None:
            continue
        
        print(f"  Processing {name} data...")
        initial_count = len(df)
        
        # Drop records with null Provider, BeneID, or ClaimID
        critical_cols = ['Provider', 'BeneID', 'ClaimID']
        existing_critical = [col for col in critical_cols if col in df.columns]
        df = df.dropna(subset=existing_critical)
        
        # Convert dates
        date_cols = ['ClaimStartDt', 'ClaimEndDt', 'AdmissionDt', 'DischargeDt']
        existing_dates = [col for col in date_cols if col in df.columns]
        df = convert_dates(df, existing_dates)
        
        # Calculate totalCost
        if 'InscClaimAmtReimbursed' in df.columns and 'DeductibleAmtPaid' in df.columns:
            df['totalCost'] = df['InscClaimAmtReimbursed'].fillna(0) + df['DeductibleAmtPaid'].fillna(0)
        else:
            df['totalCost'] = 0
        
        # Calculate claimDuration
        if 'ClaimStartDt' in df.columns and 'ClaimEndDt' in df.columns:
            df['claimDuration'] = (df['ClaimEndDt'] - df['ClaimStartDt']).dt.days
        else:
            df['claimDuration'] = None
        
        print(f"    Processed {len(df)} records (dropped {initial_count - len(df)})")
        cleaned_dfs[name] = df
    
    return cleaned_dfs

def generate_final_report(dfs_initial, dfs_cleaned):
    """Generate final data quality report"""
    report = []
    report.append("=" * 80)
    report.append("FINAL DATA QUALITY REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    for name in dfs_initial.keys():
        if name in dfs_cleaned and dfs_cleaned[name] is not None:
            initial = dfs_initial[name]
            cleaned = dfs_cleaned[name]
            
            if initial is not None:
                report.append(f"\n{name.upper()} Dataset")
                report.append("-" * 80)
                report.append(f"Initial Records: {len(initial)}")
                report.append(f"Final Records: {len(cleaned)}")
                report.append(f"Records Dropped: {len(initial) - len(cleaned)}")
                report.append(f"Drop Rate: {((len(initial) - len(cleaned)) / len(initial) * 100):.2f}%")
    
    return "\n".join(report)

def main():
    """Main execution function"""
    print("=" * 80)
    print("DATA CLEANSING PIPELINE")
    print("=" * 80)
    
    # Load CSV files
    dfs_initial = load_csv_files()
    
    # Generate initial report
    initial_report = generate_initial_report(dfs_initial)
    print("\n" + initial_report)
    
    # Save initial report
    report_path = os.path.join(STATS_DIR, "data_quality_report.txt")
    with open(report_path, 'w') as f:
        f.write(initial_report)
    print(f"\nInitial report saved to {report_path}")
    
    # Clean data
    dfs_cleaned = {}
    
    if 'beneficiary' in dfs_initial:
        dfs_cleaned['beneficiary'] = clean_beneficiary_data(dfs_initial['beneficiary'])
    
    if 'provider' in dfs_initial:
        dfs_cleaned['provider'] = clean_provider_data(dfs_initial['provider'])
    
    if 'inpatient' in dfs_initial or 'outpatient' in dfs_initial:
        cleaned_claims = clean_claims_data(
            dfs_initial.get('inpatient'),
            dfs_initial.get('outpatient')
        )
        dfs_cleaned.update(cleaned_claims)
    
    # Generate final report
    final_report = generate_final_report(dfs_initial, dfs_cleaned)
    print("\n" + final_report)
    
    # Append final report to file
    with open(report_path, 'a') as f:
        f.write("\n\n" + final_report)
    
    # Save cleaned CSVs
    print("\nSaving cleaned CSV files...")
    for name, df in dfs_cleaned.items():
        if df is not None:
            output_path = os.path.join(PROCESSED_DATA_DIR, f"{name}_cleaned.csv")
            df.to_csv(output_path, index=False)
            print(f"  Saved {name} to {output_path}")
    
    print("\n" + "=" * 80)
    print("DATA CLEANSING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()

