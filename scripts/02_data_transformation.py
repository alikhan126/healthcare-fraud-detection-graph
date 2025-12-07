"""
Data Transformation Script
Transforms cleaned data into graph model format ready for Neo4j loading
"""
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Define paths
PROCESSED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed")

def load_cleaned_data():
    """Load cleaned CSV files"""
    print("Loading cleaned data files...")
    
    files = {
        'beneficiary': 'beneficiary_cleaned.csv',
        'inpatient': 'inpatient_cleaned.csv',
        'outpatient': 'outpatient_cleaned.csv',
        'provider': 'provider_cleaned.csv'
    }
    
    dataframes = {}
    for key, filename in files.items():
        filepath = os.path.join(PROCESSED_DATA_DIR, filename)
        if os.path.exists(filepath):
            print(f"  Loading {filename}...")
            dataframes[key] = pd.read_csv(filepath, parse_dates=True, low_memory=False)
            print(f"    Loaded {len(dataframes[key])} records")
        else:
            print(f"  WARNING: {filename} not found at {filepath}")
            dataframes[key] = None
    
    return dataframes

def merge_claims_data(inpatient_df, outpatient_df):
    """Merge inpatient and outpatient claims"""
    print("\nMerging claims data...")
    
    if inpatient_df is None and outpatient_df is None:
        return None
    
    claims_list = []
    
    if inpatient_df is not None:
        print(f"  Processing {len(inpatient_df)} inpatient claims...")
        inpatient_df['type'] = 'Inpatient'
        claims_list.append(inpatient_df)
    
    if outpatient_df is not None:
        print(f"  Processing {len(outpatient_df)} outpatient claims...")
        outpatient_df['type'] = 'Outpatient'
        claims_list.append(outpatient_df)
    
    if claims_list:
        merged_claims = pd.concat(claims_list, ignore_index=True, sort=False)
        print(f"  Total merged claims: {len(merged_claims)}")
        return merged_claims
    
    return None

def prepare_provider_nodes(provider_df):
    """Prepare Provider nodes for Neo4j"""
    if provider_df is None:
        return None
    
    print("\nPreparing Provider nodes...")
    
    # Select relevant columns
    provider_nodes = provider_df[['Provider', 'isFraud']].copy()
    provider_nodes = provider_nodes.rename(columns={'Provider': 'id'})
    provider_nodes = provider_nodes.drop_duplicates(subset=['id'])
    
    print(f"  Total unique providers: {len(provider_nodes)}")
    print(f"  Fraud providers: {provider_nodes['isFraud'].sum()}")
    print(f"  Legitimate providers: {(provider_nodes['isFraud'] == 0).sum()}")
    
    return provider_nodes

def prepare_beneficiary_nodes(beneficiary_df):
    """Prepare Beneficiary nodes for Neo4j"""
    if beneficiary_df is None:
        return None
    
    print("\nPreparing Beneficiary nodes...")
    
    # Select relevant columns
    cols = ['BeneID', 'age', 'State', 'County', 'Gender', 'Race', 'isDeceased']
    
    # Add chronic condition columns
    chronic_cols = [col for col in beneficiary_df.columns 
                   if 'ChronicCond' in col or 'RenalDiseaseIndicator' in col]
    cols.extend(chronic_cols)
    
    # Filter to existing columns
    existing_cols = [col for col in cols if col in beneficiary_df.columns]
    beneficiary_nodes = beneficiary_df[existing_cols].copy()
    beneficiary_nodes = beneficiary_nodes.rename(columns={'BeneID': 'id'})
    beneficiary_nodes = beneficiary_nodes.drop_duplicates(subset=['id'])
    
    print(f"  Total unique beneficiaries: {len(beneficiary_nodes)}")
    print(f"  Deceased beneficiaries: {beneficiary_nodes['isDeceased'].sum()}")
    
    return beneficiary_nodes

def prepare_claim_nodes(claims_df):
    """Prepare Claim nodes for Neo4j"""
    if claims_df is None:
        return None
    
    print("\nPreparing Claim nodes...")
    
    # Select relevant columns
    claim_cols = ['ClaimID', 'type', 'totalCost', 'ClaimStartDt', 'ClaimEndDt', 
                  'AdmissionDt', 'DischargeDt', 'InscClaimAmtReimbursed', 'DeductibleAmtPaid']
    
    # Filter to existing columns
    existing_cols = [col for col in claim_cols if col in claims_df.columns]
    claim_nodes = claims_df[existing_cols].copy()
    
    # Rename columns for Neo4j
    rename_map = {
        'ClaimID': 'id',
        'ClaimStartDt': 'claimStartDate',
        'ClaimEndDt': 'claimEndDate',
        'AdmissionDt': 'admissionDate',
        'DischargeDt': 'dischargeDate',
        'InscClaimAmtReimbursed': 'reimbursedAmount',
        'DeductibleAmtPaid': 'deductibleAmount'
    }
    
    claim_nodes = claim_nodes.rename(columns=rename_map)
    claim_nodes = claim_nodes.drop_duplicates(subset=['id'])
    
    # Fill NaN values appropriately
    claim_nodes['totalCost'] = claim_nodes['totalCost'].fillna(0)
    claim_nodes['reimbursedAmount'] = claim_nodes['reimbursedAmount'].fillna(0)
    claim_nodes['deductibleAmount'] = claim_nodes['deductibleAmount'].fillna(0)
    
    print(f"  Total unique claims: {len(claim_nodes)}")
    print(f"  Inpatient claims: {(claim_nodes['type'] == 'Inpatient').sum()}")
    print(f"  Outpatient claims: {(claim_nodes['type'] == 'Outpatient').sum()}")
    
    return claim_nodes

def extract_physician_nodes(claims_df):
    """Extract unique Physician nodes from claims data"""
    if claims_df is None:
        return None
    
    print("\nExtracting Physician nodes...")
    
    physician_columns = ['AttendingPhysician', 'OperatingPhysician', 'OtherPhysician']
    existing_physician_cols = [col for col in physician_columns if col in claims_df.columns]
    
    if not existing_physician_cols:
        print("  No physician columns found")
        return None
    
    # Collect all unique physician IDs
    physicians = set()
    for col in existing_physician_cols:
        unique_physicians = claims_df[col].dropna().unique()
        physicians.update(unique_physicians)
    
    # Create DataFrame
    physician_nodes = pd.DataFrame({'id': list(physicians)})
    physician_nodes = physician_nodes.sort_values('id').reset_index(drop=True)
    
    print(f"  Total unique physicians: {len(physician_nodes)}")
    
    return physician_nodes

def extract_medical_code_nodes(claims_df):
    """Extract unique MedicalCode nodes from claims data"""
    if claims_df is None:
        return None
    
    print("\nExtracting MedicalCode nodes...")
    
    # Diagnosis codes
    diagnosis_cols = [f'ClmDiagnosisCode_{i}' for i in range(1, 11)]
    existing_diagnosis = [col for col in diagnosis_cols if col in claims_df.columns]
    
    # Procedure codes
    procedure_cols = [f'ClmProcedureCode_{i}' for i in range(1, 7)]
    existing_procedure = [col for col in procedure_cols if col in claims_df.columns]
    
    codes = []
    
    # Collect diagnosis codes
    for col in existing_diagnosis:
        unique_codes = claims_df[col].dropna().unique()
        for code in unique_codes:
            # Convert to string to handle mixed types (numeric and alphanumeric codes)
            codes.append({'code': str(code), 'type': 'Diagnosis'})
    
    # Collect procedure codes
    for col in existing_procedure:
        unique_codes = claims_df[col].dropna().unique()
        for code in unique_codes:
            # Convert to string to handle mixed types (numeric and alphanumeric codes)
            codes.append({'code': str(code), 'type': 'Procedure'})
    
    # Create DataFrame and remove duplicates
    if codes:
        code_nodes = pd.DataFrame(codes)
        code_nodes = code_nodes.drop_duplicates(subset=['code'])
        # Ensure code column is string type before sorting
        code_nodes['code'] = code_nodes['code'].astype(str)
        code_nodes = code_nodes.sort_values('code').reset_index(drop=True)
        
        print(f"  Total unique medical codes: {len(code_nodes)}")
        print(f"  Diagnosis codes: {(code_nodes['type'] == 'Diagnosis').sum()}")
        print(f"  Procedure codes: {(code_nodes['type'] == 'Procedure').sum()}")
        
        return code_nodes
    
    return None

def create_relationship_mappings(claims_df, provider_df, beneficiary_df):
    """Create relationship mapping DataFrames"""
    print("\nCreating relationship mappings...")
    
    relationships = {}
    
    if claims_df is not None:
        # FILED: Provider -> Claim
        if 'Provider' in claims_df.columns and 'ClaimID' in claims_df.columns:
            filed = claims_df[['Provider', 'ClaimID']].copy()
            filed = filed.dropna()
            filed = filed.rename(columns={'Provider': 'provider_id', 'ClaimID': 'claim_id'})
            relationships['FILED'] = filed
            print(f"  FILED relationships: {len(filed)}")
        
        # HAS_CLAIM: Beneficiary -> Claim
        if 'BeneID' in claims_df.columns and 'ClaimID' in claims_df.columns:
            has_claim = claims_df[['BeneID', 'ClaimID']].copy()
            has_claim = has_claim.dropna()
            has_claim = has_claim.rename(columns={'BeneID': 'beneficiary_id', 'ClaimID': 'claim_id'})
            relationships['HAS_CLAIM'] = has_claim
            print(f"  HAS_CLAIM relationships: {len(has_claim)}")
        
        # ATTENDED_BY: Claim -> Physician
        physician_cols = ['AttendingPhysician', 'OperatingPhysician', 'OtherPhysician']
        existing_physician_cols = [col for col in physician_cols if col in claims_df.columns]
        
        if existing_physician_cols and 'ClaimID' in claims_df.columns:
            attended_by_list = []
            for col in existing_physician_cols:
                attended = claims_df[['ClaimID', col]].copy()
                attended = attended.dropna(subset=[col])
                attended = attended.rename(columns={'ClaimID': 'claim_id', col: 'physician_id'})
                attended['physician_type'] = col.replace('Physician', '').strip()
                attended_by_list.append(attended)
            
            if attended_by_list:
                attended_by = pd.concat(attended_by_list, ignore_index=True)
                relationships['ATTENDED_BY'] = attended_by
                print(f"  ATTENDED_BY relationships: {len(attended_by)}")
        
        # INCLUDES_CODE: Claim -> MedicalCode
        code_relationships = []
        
        # Diagnosis codes
        diagnosis_cols = [f'ClmDiagnosisCode_{i}' for i in range(1, 11)]
        existing_diagnosis = [col for col in diagnosis_cols if col in claims_df.columns]
        
        for col in existing_diagnosis:
            if 'ClaimID' in claims_df.columns:
                code_rel = claims_df[['ClaimID', col]].copy()
                code_rel = code_rel.dropna(subset=[col])
                code_rel = code_rel.rename(columns={'ClaimID': 'claim_id', col: 'code'})
                code_rel['code_type'] = 'Diagnosis'
                code_relationships.append(code_rel)
        
        # Procedure codes
        procedure_cols = [f'ClmProcedureCode_{i}' for i in range(1, 7)]
        existing_procedure = [col for col in procedure_cols if col in claims_df.columns]
        
        for col in existing_procedure:
            if 'ClaimID' in claims_df.columns:
                code_rel = claims_df[['ClaimID', col]].copy()
                code_rel = code_rel.dropna(subset=[col])
                code_rel = code_rel.rename(columns={'ClaimID': 'claim_id', col: 'code'})
                code_rel['code_type'] = 'Procedure'
                code_relationships.append(code_rel)
        
        if code_relationships:
            includes_code = pd.concat(code_relationships, ignore_index=True)
            relationships['INCLUDES_CODE'] = includes_code
            print(f"  INCLUDES_CODE relationships: {len(includes_code)}")
    
    return relationships

def save_transformed_data(provider_nodes, beneficiary_nodes, claim_nodes, 
                         physician_nodes, code_nodes, relationships):
    """Save all transformed data to CSV files"""
    print("\nSaving transformed data...")
    
    # Save nodes
    if provider_nodes is not None:
        path = os.path.join(OUTPUT_DIR, "provider_nodes.csv")
        provider_nodes.to_csv(path, index=False)
        print(f"  Saved provider nodes to {path}")
    
    if beneficiary_nodes is not None:
        path = os.path.join(OUTPUT_DIR, "beneficiary_nodes.csv")
        beneficiary_nodes.to_csv(path, index=False)
        print(f"  Saved beneficiary nodes to {path}")
    
    if claim_nodes is not None:
        path = os.path.join(OUTPUT_DIR, "claim_nodes.csv")
        claim_nodes.to_csv(path, index=False)
        print(f"  Saved claim nodes to {path}")
    
    if physician_nodes is not None:
        path = os.path.join(OUTPUT_DIR, "physician_nodes.csv")
        physician_nodes.to_csv(path, index=False)
        print(f"  Saved physician nodes to {path}")
    
    if code_nodes is not None:
        path = os.path.join(OUTPUT_DIR, "medical_code_nodes.csv")
        code_nodes.to_csv(path, index=False)
        print(f"  Saved medical code nodes to {path}")
    
    # Save relationships
    for rel_name, rel_df in relationships.items():
        if rel_df is not None:
            path = os.path.join(OUTPUT_DIR, f"{rel_name.lower()}_relationships.csv")
            rel_df.to_csv(path, index=False)
            print(f"  Saved {rel_name} relationships to {path}")

def main():
    """Main execution function"""
    print("=" * 80)
    print("DATA TRANSFORMATION PIPELINE")
    print("=" * 80)
    
    # Load cleaned data
    dfs = load_cleaned_data()
    
    # Merge claims data
    merged_claims = merge_claims_data(dfs.get('inpatient'), dfs.get('outpatient'))
    
    # Prepare nodes
    provider_nodes = prepare_provider_nodes(dfs.get('provider'))
    beneficiary_nodes = prepare_beneficiary_nodes(dfs.get('beneficiary'))
    claim_nodes = prepare_claim_nodes(merged_claims)
    physician_nodes = extract_physician_nodes(merged_claims)
    code_nodes = extract_medical_code_nodes(merged_claims)
    
    # Create relationship mappings
    relationships = create_relationship_mappings(merged_claims, provider_nodes, beneficiary_nodes)
    
    # Save transformed data
    save_transformed_data(provider_nodes, beneficiary_nodes, claim_nodes, 
                         physician_nodes, code_nodes, relationships)
    
    print("\n" + "=" * 80)
    print("DATA TRANSFORMATION COMPLETE")
    print("=" * 80)
    print("\nSummary:")
    print(f"  Provider nodes: {len(provider_nodes) if provider_nodes is not None else 0}")
    print(f"  Beneficiary nodes: {len(beneficiary_nodes) if beneficiary_nodes is not None else 0}")
    print(f"  Claim nodes: {len(claim_nodes) if claim_nodes is not None else 0}")
    print(f"  Physician nodes: {len(physician_nodes) if physician_nodes is not None else 0}")
    print(f"  Medical code nodes: {len(code_nodes) if code_nodes is not None else 0}")
    print(f"  Relationship types: {len(relationships)}")

if __name__ == "__main__":
    main()

