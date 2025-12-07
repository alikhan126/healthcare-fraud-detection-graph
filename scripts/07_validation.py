"""
Validation Script
Validates data and graph structure after loading
"""
import sys
import os
from neo4j import GraphDatabase

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.neo4j_config import get_neo4j_config

def validate_data(driver, config):
    """Validate data integrity"""
    print("=" * 80)
    print("DATA VALIDATION")
    print("=" * 80)
    
    with driver.session(database=config['database']) as session:
        # Check node counts
        print("\n1. Node Counts:")
        node_types = ["Provider", "Beneficiary", "Claim", "Physician", "MedicalCode"]
        for node_type in node_types:
            result = session.run(f"MATCH (n:{node_type}) RETURN count(n) AS count")
            count = result.single()['count']
            print(f"   {node_type}: {count}")
        
        # Check relationship counts
        print("\n2. Relationship Counts:")
        rel_types = ["FILED", "HAS_CLAIM", "ATTENDED_BY", "INCLUDES_CODE"]
        for rel_type in rel_types:
            result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS count")
            count = result.single()['count']
            print(f"   {rel_type}: {count}")
        
        # Check fraud providers
        print("\n3. Fraud Provider Validation:")
        result = session.run("""
            MATCH (p:Provider)
            RETURN 
                count(p) as total_providers,
                sum(p.isFraud) as fraud_providers,
                sum(CASE WHEN p.isFraud = 0 THEN 1 ELSE 0 END) as legit_providers
        """)
        record = result.single()
        print(f"   Total providers: {record['total_providers']}")
        print(f"   Fraud providers: {record['fraud_providers']}")
        print(f"   Legitimate providers: {record['legit_providers']}")
        
        # Check orphan claims
        print("\n4. Orphan Claim Check:")
        result = session.run("""
            MATCH (c:Claim)
            WHERE NOT (c)<-[:FILED]-()
            RETURN count(c) AS orphan_no_provider
        """)
        no_provider = result.single()['orphan_no_provider']
        
        result = session.run("""
            MATCH (c:Claim)
            WHERE NOT (c)<-[:HAS_CLAIM]-()
            RETURN count(c) AS orphan_no_beneficiary
        """)
        no_beneficiary = result.single()['orphan_no_beneficiary']
        
        print(f"   Claims without provider: {no_provider}")
        print(f"   Claims without beneficiary: {no_beneficiary}")
        
        if no_provider == 0 and no_beneficiary == 0:
            print("   ✓ No orphan claims found")
        else:
            print("   ⚠ Some orphan claims found")
        
        # Check duplicate relationships
        print("\n5. Duplicate Relationship Check:")
        result = session.run("""
            MATCH (p:Provider)-[r:FILED]->(c:Claim)
            WITH p, c, count(r) as rel_count
            WHERE rel_count > 1
            RETURN count(*) as duplicate_count
        """)
        duplicates = result.single()['duplicate_count']
        print(f"   Duplicate FILED relationships: {duplicates}")
        
        if duplicates == 0:
            print("   ✓ No duplicate relationships found")
        else:
            print("   ⚠ Some duplicate relationships found")
        
        # Check totalCost calculations
        print("\n6. Total Cost Validation:")
        result = session.run("""
            MATCH (c:Claim)
            WHERE c.totalCost IS NOT NULL 
              AND c.reimbursedAmount IS NOT NULL 
              AND c.deductibleAmount IS NOT NULL
            WITH c, 
                 abs(c.totalCost - (c.reimbursedAmount + c.deductibleAmount)) as diff
            WHERE diff > 0.01
            RETURN count(*) as mismatched_count
        """)
        mismatched = result.single()['mismatched_count']
        print(f"   Claims with cost mismatch: {mismatched}")
        
        if mismatched == 0:
            print("   ✓ All costs match")
        else:
            print("   ⚠ Some cost mismatches found")
        
        # Check deceased beneficiaries
        print("\n7. Deceased Beneficiary Check:")
        result = session.run("""
            MATCH (b:Beneficiary)
            RETURN 
                count(b) as total,
                sum(b.isDeceased) as deceased_count
        """)
        record = result.single()
        print(f"   Total beneficiaries: {record['total']}")
        print(f"   Deceased beneficiaries: {record['deceased_count']}")
        
        print("\n" + "=" * 80)
        print("VALIDATION COMPLETE")
        print("=" * 80)

def main():
    """Main execution function"""
    try:
        config = get_neo4j_config()
        driver = GraphDatabase.driver(
            config["uri"],
            auth=(config["user"], config["password"]),
            connection_timeout=config["connection_timeout"]
        )
        driver.verify_connectivity()
        print(f"✓ Connected to Neo4j at {config['uri']}\n")
        
        validate_data(driver, config)
        
        driver.close()
        
    except Exception as e:
        print(f"\n✗ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

