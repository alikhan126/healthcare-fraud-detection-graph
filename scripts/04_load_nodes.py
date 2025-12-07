"""
Node Loading Script
Loads all node types into Neo4j in batches
"""
import sys
import os
import pandas as pd
import numpy as np
from neo4j import GraphDatabase

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.neo4j_config import get_neo4j_config

PROCESSED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed")

def load_nodes_batch(driver, config, node_type, df, batch_size=1000):
    """Load nodes in batches using UNWIND"""
    if df is None or len(df) == 0:
        print(f"  No {node_type} nodes to load")
        return 0
    
    print(f"\nLoading {node_type} nodes...")
    print(f"  Total records: {len(df)}")
    
    total_loaded = 0
    num_batches = (len(df) + batch_size - 1) // batch_size
    
    with driver.session(database=config['database']) as session:
        for i in range(0, len(df), batch_size):
            batch = df[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            
            # Convert DataFrame to list of dictionaries
            records = batch.to_dict('records')
            
            # Build Cypher query based on node type
            if node_type == "Provider":
                cypher = """
                UNWIND $records AS record
                CREATE (p:Provider {
                    id: record.id,
                    isFraud: record.isFraud
                })
                """
            elif node_type == "Beneficiary":
                # Process records to handle NaN values and types
                processed_records = []
                for rec in records:
                    processed = {}
                    for key, value in rec.items():
                        if pd.isna(value):
                            processed[key] = None
                        elif isinstance(value, (pd.Timestamp, pd.Timedelta)):
                            processed[key] = str(value)
                        elif isinstance(value, (np.integer, np.floating)):
                            processed[key] = value.item()
                        else:
                            processed[key] = value
                    processed_records.append(processed)
                records = processed_records
                
                cypher = """
                UNWIND $records AS record
                CREATE (b:Beneficiary)
                SET b = record
                """
            elif node_type == "Claim":
                cypher = """
                UNWIND $records AS record
                CREATE (c:Claim {
                    id: record.id,
                    type: record.type,
                    totalCost: toFloat(record.totalCost),
                    claimStartDate: record.claimStartDate,
                    claimEndDate: record.claimEndDate,
                    admissionDate: record.admissionDate,
                    dischargeDate: record.dischargeDate,
                    reimbursedAmount: toFloat(record.reimbursedAmount),
                    deductibleAmount: toFloat(record.deductibleAmount)
                })
                """
            elif node_type == "Physician":
                cypher = """
                UNWIND $records AS record
                CREATE (p:Physician {
                    id: record.id
                })
                """
            elif node_type == "MedicalCode":
                cypher = """
                UNWIND $records AS record
                CREATE (m:MedicalCode {
                    code: record.code,
                    type: record.type
                })
                """
            else:
                print(f"  Unknown node type: {node_type}")
                return 0
            
            try:
                result = session.run(cypher, records=records)
                result.consume()  # Consume result to execute
                total_loaded += len(batch)
                print(f"  Batch {batch_num}/{num_batches}: Loaded {len(batch)} nodes (Total: {total_loaded})")
            except Exception as e:
                print(f"  ✗ Error loading batch {batch_num}: {e}")
                # Try to continue with next batch
                continue
    
    print(f"  ✓ Loaded {total_loaded} {node_type} nodes")
    return total_loaded

def load_provider_nodes(driver, config):
    """Load Provider nodes"""
    filepath = os.path.join(PROCESSED_DATA_DIR, "provider_nodes.csv")
    if not os.path.exists(filepath):
        print(f"  File not found: {filepath}")
        return 0
    
    df = pd.read_csv(filepath)
    # Ensure isFraud is integer
    df['isFraud'] = df['isFraud'].astype(int)
    return load_nodes_batch(driver, config, "Provider", df)

def load_beneficiary_nodes(driver, config):
    """Load Beneficiary nodes"""
    filepath = os.path.join(PROCESSED_DATA_DIR, "beneficiary_nodes.csv")
    if not os.path.exists(filepath):
        print(f"  File not found: {filepath}")
        return 0
    
    df = pd.read_csv(filepath)
    # Convert date columns if they exist
    date_cols = ['DOB', 'DOD']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Fill NaN values appropriately
    df = df.fillna({'State': 'UNKNOWN', 'County': 'UNKNOWN'})
    
    return load_nodes_batch(driver, config, "Beneficiary", df)

def load_claim_nodes(driver, config):
    """Load Claim nodes"""
    filepath = os.path.join(PROCESSED_DATA_DIR, "claim_nodes.csv")
    if not os.path.exists(filepath):
        print(f"  File not found: {filepath}")
        return 0
    
    df = pd.read_csv(filepath, parse_dates=True, low_memory=False)
    # Convert date columns
    date_cols = ['claimStartDate', 'claimEndDate', 'admissionDate', 'dischargeDate']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Fill NaN numeric values
    numeric_cols = ['totalCost', 'reimbursedAmount', 'deductibleAmount']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return load_nodes_batch(driver, config, "Claim", df)

def load_physician_nodes(driver, config):
    """Load Physician nodes"""
    filepath = os.path.join(PROCESSED_DATA_DIR, "physician_nodes.csv")
    if not os.path.exists(filepath):
        print(f"  File not found: {filepath}")
        return 0
    
    df = pd.read_csv(filepath)
    return load_nodes_batch(driver, config, "Physician", df)

def load_medical_code_nodes(driver, config):
    """Load MedicalCode nodes"""
    filepath = os.path.join(PROCESSED_DATA_DIR, "medical_code_nodes.csv")
    if not os.path.exists(filepath):
        print(f"  File not found: {filepath}")
        return 0
    
    df = pd.read_csv(filepath)
    return load_nodes_batch(driver, config, "MedicalCode", df)

def verify_node_counts(driver, config):
    """Verify node counts in database"""
    print("\nVerifying node counts...")
    
    node_types = ["Provider", "Beneficiary", "Claim", "Physician", "MedicalCode"]
    
    with driver.session(database=config['database']) as session:
        for node_type in node_types:
            cypher = f"MATCH (n:{node_type}) RETURN count(n) AS count"
            result = session.run(cypher)
            count = result.single()['count']
            print(f"  {node_type}: {count} nodes")

def main():
    """Main execution function"""
    print("=" * 80)
    print("NODE LOADING PIPELINE")
    print("=" * 80)
    
    try:
        # Connect to Neo4j
        config = get_neo4j_config()
        driver = GraphDatabase.driver(
            config["uri"],
            auth=(config["user"], config["password"]),
            connection_timeout=config["connection_timeout"]
        )
        driver.verify_connectivity()
        print(f"✓ Connected to Neo4j at {config['uri']}\n")
        
        # Load nodes in order
        counts = {}
        counts['Provider'] = load_provider_nodes(driver, config)
        counts['Beneficiary'] = load_beneficiary_nodes(driver, config)
        counts['Claim'] = load_claim_nodes(driver, config)
        counts['Physician'] = load_physician_nodes(driver, config)
        counts['MedicalCode'] = load_medical_code_nodes(driver, config)
        
        # Verify counts
        verify_node_counts(driver, config)
        
        # Summary
        print("\n" + "=" * 80)
        print("NODE LOADING SUMMARY")
        print("=" * 80)
        total_nodes = sum(counts.values())
        print(f"Total nodes loaded: {total_nodes}")
        for node_type, count in counts.items():
            print(f"  {node_type}: {count}")
        print("=" * 80)
        
        driver.close()
        
    except Exception as e:
        print(f"\n✗ Node loading failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

