"""
Relationship Loading Script
Creates all relationship types in Neo4j
"""
import sys
import os
import pandas as pd
from neo4j import GraphDatabase

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.neo4j_config import get_neo4j_config

PROCESSED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed")

def load_relationships_batch(driver, config, rel_type, df, batch_size=1000):
    """Load relationships in batches using UNWIND"""
    if df is None or len(df) == 0:
        print(f"  No {rel_type} relationships to load")
        return 0
    
    print(f"\nLoading {rel_type} relationships...")
    print(f"  Total records: {len(df)}")
    
    total_loaded = 0
    num_batches = (len(df) + batch_size - 1) // batch_size
    
    with driver.session(database=config['database']) as session:
        for i in range(0, len(df), batch_size):
            batch = df[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            
            # Convert DataFrame to list of dictionaries
            records = batch.to_dict('records')
            
            # Build Cypher query based on relationship type
            if rel_type == "FILED":
                cypher = """
                UNWIND $records AS record
                MATCH (p:Provider {id: record.provider_id})
                MATCH (c:Claim {id: record.claim_id})
                CREATE (p)-[:FILED]->(c)
                """
            elif rel_type == "HAS_CLAIM":
                cypher = """
                UNWIND $records AS record
                MATCH (b:Beneficiary {id: record.beneficiary_id})
                MATCH (c:Claim {id: record.claim_id})
                CREATE (b)-[:HAS_CLAIM]->(c)
                """
            elif rel_type == "ATTENDED_BY":
                cypher = """
                UNWIND $records AS record
                MATCH (c:Claim {id: record.claim_id})
                MATCH (p:Physician {id: record.physician_id})
                CREATE (c)-[:ATTENDED_BY {type: record.physician_type}]->(p)
                """
            elif rel_type == "INCLUDES_CODE":
                cypher = """
                UNWIND $records AS record
                MATCH (c:Claim {id: record.claim_id})
                MATCH (m:MedicalCode {code: record.code})
                CREATE (c)-[:INCLUDES_CODE]->(m)
                """
            else:
                print(f"  Unknown relationship type: {rel_type}")
                return 0
            
            try:
                result = session.run(cypher, records=records)
                result.consume()  # Consume result to execute
                total_loaded += len(batch)
                print(f"  Batch {batch_num}/{num_batches}: Loaded {len(batch)} relationships (Total: {total_loaded})")
            except Exception as e:
                print(f"  ✗ Error loading batch {batch_num}: {e}")
                # Try to continue with next batch
                continue
    
    print(f"  ✓ Loaded {total_loaded} {rel_type} relationships")
    return total_loaded

def load_filed_relationships(driver, config):
    """Load FILED relationships (Provider -> Claim)"""
    filepath = os.path.join(PROCESSED_DATA_DIR, "filed_relationships.csv")
    if not os.path.exists(filepath):
        print(f"  File not found: {filepath}")
        return 0
    
    df = pd.read_csv(filepath)
    return load_relationships_batch(driver, config, "FILED", df)

def load_has_claim_relationships(driver, config):
    """Load HAS_CLAIM relationships (Beneficiary -> Claim)"""
    filepath = os.path.join(PROCESSED_DATA_DIR, "has_claim_relationships.csv")
    if not os.path.exists(filepath):
        print(f"  File not found: {filepath}")
        return 0
    
    df = pd.read_csv(filepath)
    return load_relationships_batch(driver, config, "HAS_CLAIM", df)

def load_attended_by_relationships(driver, config):
    """Load ATTENDED_BY relationships (Claim -> Physician)"""
    filepath = os.path.join(PROCESSED_DATA_DIR, "attended_by_relationships.csv")
    if not os.path.exists(filepath):
        print(f"  File not found: {filepath}")
        return 0
    
    df = pd.read_csv(filepath)
    # Convert physician_type to string if needed
    if 'physician_type' in df.columns:
        df['physician_type'] = df['physician_type'].astype(str)
    else:
        df['physician_type'] = 'Unknown'
    
    return load_relationships_batch(driver, config, "ATTENDED_BY", df)

def load_includes_code_relationships(driver, config):
    """Load INCLUDES_CODE relationships (Claim -> MedicalCode)"""
    filepath = os.path.join(PROCESSED_DATA_DIR, "includes_code_relationships.csv")
    if not os.path.exists(filepath):
        print(f"  File not found: {filepath}")
        return 0
    
    df = pd.read_csv(filepath)
    return load_relationships_batch(driver, config, "INCLUDES_CODE", df)

def verify_relationship_counts(driver, config):
    """Verify relationship counts in database"""
    print("\nVerifying relationship counts...")
    
    rel_types = ["FILED", "HAS_CLAIM", "ATTENDED_BY", "INCLUDES_CODE"]
    
    with driver.session(database=config['database']) as session:
        for rel_type in rel_types:
            cypher = f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS count"
            result = session.run(cypher)
            count = result.single()['count']
            print(f"  {rel_type}: {count} relationships")

def check_orphan_claims(driver, config):
    """Check for orphan claims (not connected to both provider and beneficiary)"""
    print("\nChecking for orphan claims...")
    
    with driver.session(database=config['database']) as session:
        # Claims without provider
        cypher = """
        MATCH (c:Claim)
        WHERE NOT (c)<-[:FILED]-()
        RETURN count(c) AS count
        """
        result = session.run(cypher)
        no_provider = result.single()['count']
        
        # Claims without beneficiary
        cypher = """
        MATCH (c:Claim)
        WHERE NOT (c)<-[:HAS_CLAIM]-()
        RETURN count(c) AS count
        """
        result = session.run(cypher)
        no_beneficiary = result.single()['count']
        
        print(f"  Claims without provider: {no_provider}")
        print(f"  Claims without beneficiary: {no_beneficiary}")
        
        if no_provider == 0 and no_beneficiary == 0:
            print("  ✓ No orphan claims found")
        else:
            print("  ⚠ Some orphan claims found")

def main():
    """Main execution function"""
    print("=" * 80)
    print("RELATIONSHIP LOADING PIPELINE")
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
        
        # Load relationships in order
        counts = {}
        counts['FILED'] = load_filed_relationships(driver, config)
        counts['HAS_CLAIM'] = load_has_claim_relationships(driver, config)
        counts['ATTENDED_BY'] = load_attended_by_relationships(driver, config)
        counts['INCLUDES_CODE'] = load_includes_code_relationships(driver, config)
        
        # Verify counts
        verify_relationship_counts(driver, config)
        
        # Check for orphan claims
        check_orphan_claims(driver, config)
        
        # Summary
        print("\n" + "=" * 80)
        print("RELATIONSHIP LOADING SUMMARY")
        print("=" * 80)
        total_rels = sum(counts.values())
        print(f"Total relationships loaded: {total_rels}")
        for rel_type, count in counts.items():
            print(f"  {rel_type}: {count}")
        print("=" * 80)
        
        driver.close()
        
    except Exception as e:
        print(f"\n✗ Relationship loading failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

