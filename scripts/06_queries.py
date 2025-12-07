"""
Fraud Detection Queries Script
Executes all 12 required fraud detection queries
"""
import sys
import os
import pandas as pd
from neo4j import GraphDatabase

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.neo4j_config import get_neo4j_config

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "results")
QUERIES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "queries")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(QUERIES_DIR, exist_ok=True)

def execute_query(driver, config, query_name, cypher, description):
    """Execute a Cypher query and return results as DataFrame"""
    print(f"\n{'='*80}")
    print(f"Query: {query_name}")
    print(f"{'='*80}")
    print(f"Description: {description}")
    print(f"\nCypher Query:")
    print(cypher)
    print(f"\nExecuting query...")
    
    try:
        with driver.session(database=config['database']) as session:
            result = session.run(cypher)
            
            # Convert to list of records
            records = []
            for record in result:
                records.append(dict(record))
            
            if records:
                df = pd.DataFrame(records)
                print(f"✓ Query executed successfully")
                print(f"  Results: {len(df)} rows")
                print(f"\nFirst 10 results:")
                print(df.head(10).to_string())
                
                # Save to CSV
                output_path = os.path.join(OUTPUT_DIR, f"{query_name.lower().replace(' ', '_')}.csv")
                df.to_csv(output_path, index=False)
                print(f"\n  Results saved to: {output_path}")
                
                return df
            else:
                print("  No results returned")
                return pd.DataFrame()
                
    except Exception as e:
        print(f"✗ Query failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def query_1_spider_web(driver, config):
    """Query 1: Spider Web Pattern - Beneficiaries connected to 3+ fraud providers"""
    cypher = """
    MATCH (b:Beneficiary)-[:HAS_CLAIM]->(c:Claim)<-[:FILED]-(p:Provider)
    WHERE p.isFraud = 1
    WITH b, collect(DISTINCT p) as fraudProviders
    WHERE size(fraudProviders) >= 3
    RETURN b.id as beneficiary_id, 
           b.age as age,
           b.state as state,
           size(fraudProviders) as fraud_provider_count,
           [provider in fraudProviders | provider.id] as fraud_provider_ids
    ORDER BY fraud_provider_count DESC
    LIMIT 100
    """
    return execute_query(
        driver, config, 
        "Query 1: Spider Web Pattern",
        cypher,
        "Find beneficiaries connected to 3+ fraud providers - Identify victims of fraud rings"
    )

def query_2_shared_doctor_ring(driver, config):
    """Query 2: Shared Doctor Ring - Fraud providers sharing same physicians"""
    cypher = """
    MATCH (p1:Provider)-[:FILED]->(c1:Claim)-[:ATTENDED_BY]->(phys:Physician)<-[:ATTENDED_BY]-(c2:Claim)<-[:FILED]-(p2:Provider)
    WHERE p1.isFraud = 1 AND p2.isFraud = 1 AND p1.id <> p2.id
    WITH p1, p2, collect(DISTINCT phys) as sharedPhysicians
    WHERE size(sharedPhysicians) > 0
    RETURN p1.id as provider1_id,
           p2.id as provider2_id,
           size(sharedPhysicians) as shared_physician_count,
           [phys in sharedPhysicians | phys.id] as shared_physician_ids
    ORDER BY shared_physician_count DESC
    LIMIT 100
    """
    return execute_query(
        driver, config,
        "Query 2: Shared Doctor Ring",
        cypher,
        "Find fraud providers sharing same physicians - Detect physician collusion"
    )

def query_3_accomplice_physician(driver, config):
    """Query 3: Accomplice Physician - Physicians connected to both fraud and legitimate providers"""
    cypher = """
    MATCH (phys:Physician)<-[:ATTENDED_BY]-(c:Claim)<-[:FILED]-(p:Provider)
    WITH phys, 
         collect(DISTINCT CASE WHEN p.isFraud = 1 THEN p.id END) as fraudProviders,
         collect(DISTINCT CASE WHEN p.isFraud = 0 THEN p.id END) as legitProviders
    WHERE size([x in fraudProviders WHERE x IS NOT NULL]) > 0 
      AND size([x in legitProviders WHERE x IS NOT NULL]) > 0
    RETURN phys.id as physician_id,
           size([x in fraudProviders WHERE x IS NOT NULL]) as fraud_provider_count,
           size([x in legitProviders WHERE x IS NOT NULL]) as legit_provider_count,
           [x in fraudProviders WHERE x IS NOT NULL] as fraud_provider_ids,
           [x in legitProviders WHERE x IS NOT NULL] as legit_provider_ids
    ORDER BY fraud_provider_count DESC, legit_provider_count DESC
    LIMIT 100
    """
    return execute_query(
        driver, config,
        "Query 3: Accomplice Physician",
        cypher,
        "Find physicians connected to both fraud and legitimate providers - Identify suspicious physicians"
    )

def query_4_diagnosis_clusters(driver, config):
    """Query 4: Diagnosis Copy-Paste Clusters - Medical codes used >50 times by fraud providers"""
    cypher = """
    MATCH (m:MedicalCode)<-[:INCLUDES_CODE]-(c:Claim)<-[:FILED]-(p:Provider)
    WHERE p.isFraud = 1
    WITH m, count(DISTINCT c) as usageCount
    WHERE usageCount > 50
    RETURN m.code as medical_code,
           m.type as code_type,
           usageCount as usage_count
    ORDER BY usageCount DESC
    LIMIT 100
    """
    return execute_query(
        driver, config,
        "Query 4: Diagnosis Copy-Paste Clusters",
        cypher,
        "Find medical codes used >50 times by fraud providers - Detect diagnosis code abuse"
    )

def query_5_high_value_fraud(driver, config):
    """Query 5: High-Value Fraud Claims - Fraud provider claims with totalCost > 10000"""
    cypher = """
    MATCH (p:Provider)-[:FILED]->(c:Claim)-[:ATTENDED_BY]->(phys:Physician)
    WHERE p.isFraud = 1 AND c.totalCost > 10000
    RETURN p.id as provider_id,
           c.id as claim_id,
           c.type as claim_type,
           c.totalCost as total_cost,
           collect(DISTINCT phys.id) as physician_ids
    ORDER BY c.totalCost DESC
    LIMIT 100
    """
    return execute_query(
        driver, config,
        "Query 5: High-Value Fraud Claims",
        cypher,
        "Find fraud provider claims with totalCost > 10000 - Identify expensive fraudulent claims"
    )

def query_6_dead_patient_claims(driver, config):
    """Query 6: Dead Patient Claims - Claims filed for deceased beneficiaries"""
    cypher = """
    MATCH (b:Beneficiary)-[:HAS_CLAIM]->(c:Claim)<-[:FILED]-(p:Provider)
    WHERE b.isDeceased = 1
    RETURN b.id as beneficiary_id,
           b.age as age,
           c.id as claim_id,
           c.claimStartDate as claim_start_date,
           p.id as provider_id,
           p.isFraud as provider_is_fraud,
           c.totalCost as total_cost
    ORDER BY c.totalCost DESC
    LIMIT 100
    """
    return execute_query(
        driver, config,
        "Query 6: Dead Patient Claims",
        cypher,
        "Find claims filed for deceased beneficiaries - Detect billing for dead patients"
    )

def query_7_impossible_workload(driver, config):
    """Query 7: Impossible Workload Physicians - Physicians with >10 fraud claims"""
    cypher = """
    MATCH (phys:Physician)<-[:ATTENDED_BY]-(c:Claim)<-[:FILED]-(p:Provider)
    WHERE p.isFraud = 1
    WITH phys, count(DISTINCT c) as fraudClaimCount
    WHERE fraudClaimCount > 10
    RETURN phys.id as physician_id,
           fraudClaimCount as fraud_claim_count
    ORDER BY fraudClaimCount DESC
    LIMIT 100
    """
    return execute_query(
        driver, config,
        "Query 7: Impossible Workload Physicians",
        cypher,
        "Find physicians with >10 fraud claims - Identify overworked or complicit physicians"
    )

def query_8_total_fraud_exposure(driver, config):
    """Query 8: Total Fraud Exposure - SUM(totalCost) for all fraud provider claims"""
    cypher = """
    MATCH (p:Provider)-[:FILED]->(c:Claim)
    WHERE p.isFraud = 1
    RETURN sum(c.totalCost) as total_fraud_exposure,
           count(DISTINCT p) as fraud_provider_count,
           count(c) as total_fraud_claims,
           avg(c.totalCost) as avg_claim_cost,
           max(c.totalCost) as max_claim_cost,
           min(c.totalCost) as min_claim_cost
    """
    return execute_query(
        driver, config,
        "Query 8: Total Fraud Exposure",
        cypher,
        "Calculate total fraudulent amount - SUM(totalCost) for all fraud provider claims"
    )

def query_9_top_states_fraud(driver, config):
    """Query 9: Top 5 States with Fraud Activity"""
    cypher = """
    MATCH (b:Beneficiary)-[:HAS_CLAIM]->(c:Claim)<-[:FILED]-(p:Provider)
    WHERE p.isFraud = 1
    WITH b.state as state, count(c) as claim_count
    WHERE state IS NOT NULL AND state <> 'UNKNOWN'
    RETURN state,
           claim_count
    ORDER BY claim_count DESC
    LIMIT 5
    """
    return execute_query(
        driver, config,
        "Query 9: Top 5 States with Fraud Activity",
        cypher,
        "COUNT(claims) by Beneficiary.state for fraud providers - Geographic fraud analysis"
    )

def query_10_claim_type_split(driver, config):
    """Query 10: Outpatient vs Inpatient Fraud Split"""
    cypher = """
    MATCH (p:Provider)-[:FILED]->(c:Claim)
    WHERE p.isFraud = 1
    RETURN c.type as claim_type,
           count(c) as claim_count,
           sum(c.totalCost) as total_cost,
           avg(c.totalCost) as avg_cost
    ORDER BY claim_count DESC
    """
    return execute_query(
        driver, config,
        "Query 10: Outpatient vs Inpatient Fraud Split",
        cypher,
        "COUNT(claims) by Claim.type for fraud providers - Fraud distribution by claim type"
    )

def query_11_repeat_offender(driver, config):
    """Query 11: Repeat Offender Path - Beneficiaries with >3 claims from same fraud provider"""
    cypher = """
    MATCH (b:Beneficiary)-[:HAS_CLAIM]->(c:Claim)<-[:FILED]-(p:Provider)
    WHERE p.isFraud = 1
    WITH b, p, count(c) as claimCount
    WHERE claimCount > 3
    RETURN b.id as beneficiary_id,
           b.age as age,
           b.state as state,
           p.id as provider_id,
           claimCount as claim_count
    ORDER BY claimCount DESC
    LIMIT 100
    """
    return execute_query(
        driver, config,
        "Query 11: Repeat Offender Path",
        cypher,
        "Find beneficiaries with >3 claims from same fraud provider - Identify repeat fraud patterns"
    )

def query_12_elder_fraud(driver, config):
    """Query 12: Beneficiary Age Cluster - Fraud claims for beneficiaries age >85"""
    cypher = """
    MATCH (b:Beneficiary)-[:HAS_CLAIM]->(c:Claim)<-[:FILED]-(p:Provider)
    WHERE p.isFraud = 1 AND b.age > 85
    RETURN b.id as beneficiary_id,
           b.age as age,
           b.state as state,
           count(c) as claim_count,
           sum(c.totalCost) as total_cost,
           collect(DISTINCT p.id) as fraud_provider_ids
    ORDER BY total_cost DESC
    LIMIT 100
    """
    return execute_query(
        driver, config,
        "Query 12: Beneficiary Age Cluster",
        cypher,
        "Find fraud claims for beneficiaries age >85 - Elder fraud detection"
    )

def save_all_queries():
    """Save all Cypher queries to a file"""
    queries = {
        "Query 1: Spider Web Pattern": """
    MATCH (b:Beneficiary)-[:HAS_CLAIM]->(c:Claim)<-[:FILED]-(p:Provider)
    WHERE p.isFraud = 1
    WITH b, collect(DISTINCT p) as fraudProviders
    WHERE size(fraudProviders) >= 3
    RETURN b.id as beneficiary_id, 
           b.age as age,
           b.state as state,
           size(fraudProviders) as fraud_provider_count,
           [provider in fraudProviders | provider.id] as fraud_provider_ids
    ORDER BY fraud_provider_count DESC
    LIMIT 100
        """,
        "Query 2: Shared Doctor Ring": """
    MATCH (p1:Provider)-[:FILED]->(c1:Claim)-[:ATTENDED_BY]->(phys:Physician)<-[:ATTENDED_BY]-(c2:Claim)<-[:FILED]-(p2:Provider)
    WHERE p1.isFraud = 1 AND p2.isFraud = 1 AND p1.id <> p2.id
    WITH p1, p2, collect(DISTINCT phys) as sharedPhysicians
    WHERE size(sharedPhysicians) > 0
    RETURN p1.id as provider1_id,
           p2.id as provider2_id,
           size(sharedPhysicians) as shared_physician_count,
           [phys in sharedPhysicians | phys.id] as shared_physician_ids
    ORDER BY shared_physician_count DESC
    LIMIT 100
        """,
        "Query 3: Accomplice Physician": """
    MATCH (phys:Physician)<-[:ATTENDED_BY]-(c:Claim)<-[:FILED]-(p:Provider)
    WITH phys, 
         collect(DISTINCT CASE WHEN p.isFraud = 1 THEN p.id END) as fraudProviders,
         collect(DISTINCT CASE WHEN p.isFraud = 0 THEN p.id END) as legitProviders
    WHERE size([x in fraudProviders WHERE x IS NOT NULL]) > 0 
      AND size([x in legitProviders WHERE x IS NOT NULL]) > 0
    RETURN phys.id as physician_id,
           size([x in fraudProviders WHERE x IS NOT NULL]) as fraud_provider_count,
           size([x in legitProviders WHERE x IS NOT NULL]) as legit_provider_count,
           [x in fraudProviders WHERE x IS NOT NULL] as fraud_provider_ids,
           [x in legitProviders WHERE x IS NOT NULL] as legit_provider_ids
    ORDER BY fraud_provider_count DESC, legit_provider_count DESC
    LIMIT 100
        """,
        "Query 4: Diagnosis Copy-Paste Clusters": """
    MATCH (m:MedicalCode)<-[:INCLUDES_CODE]-(c:Claim)<-[:FILED]-(p:Provider)
    WHERE p.isFraud = 1
    WITH m, count(DISTINCT c) as usageCount
    WHERE usageCount > 50
    RETURN m.code as medical_code,
           m.type as code_type,
           usageCount as usage_count
    ORDER BY usageCount DESC
    LIMIT 100
        """,
        "Query 5: High-Value Fraud Claims": """
    MATCH (p:Provider)-[:FILED]->(c:Claim)-[:ATTENDED_BY]->(phys:Physician)
    WHERE p.isFraud = 1 AND c.totalCost > 10000
    RETURN p.id as provider_id,
           c.id as claim_id,
           c.type as claim_type,
           c.totalCost as total_cost,
           collect(DISTINCT phys.id) as physician_ids
    ORDER BY c.totalCost DESC
    LIMIT 100
        """,
        "Query 6: Dead Patient Claims": """
    MATCH (b:Beneficiary)-[:HAS_CLAIM]->(c:Claim)<-[:FILED]-(p:Provider)
    WHERE b.isDeceased = 1
    RETURN b.id as beneficiary_id,
           b.age as age,
           c.id as claim_id,
           c.claimStartDate as claim_start_date,
           p.id as provider_id,
           p.isFraud as provider_is_fraud,
           c.totalCost as total_cost
    ORDER BY c.totalCost DESC
    LIMIT 100
        """,
        "Query 7: Impossible Workload Physicians": """
    MATCH (phys:Physician)<-[:ATTENDED_BY]-(c:Claim)<-[:FILED]-(p:Provider)
    WHERE p.isFraud = 1
    WITH phys, count(DISTINCT c) as fraudClaimCount
    WHERE fraudClaimCount > 10
    RETURN phys.id as physician_id,
           fraudClaimCount as fraud_claim_count
    ORDER BY fraudClaimCount DESC
    LIMIT 100
        """,
        "Query 8: Total Fraud Exposure": """
    MATCH (p:Provider)-[:FILED]->(c:Claim)
    WHERE p.isFraud = 1
    RETURN sum(c.totalCost) as total_fraud_exposure,
           count(DISTINCT p) as fraud_provider_count,
           count(c) as total_fraud_claims,
           avg(c.totalCost) as avg_claim_cost,
           max(c.totalCost) as max_claim_cost,
           min(c.totalCost) as min_claim_cost
        """,
        "Query 9: Top 5 States with Fraud Activity": """
    MATCH (b:Beneficiary)-[:HAS_CLAIM]->(c:Claim)<-[:FILED]-(p:Provider)
    WHERE p.isFraud = 1
    WITH b.state as state, count(c) as claim_count
    WHERE state IS NOT NULL AND state <> 'UNKNOWN'
    RETURN state,
           claim_count
    ORDER BY claim_count DESC
    LIMIT 5
        """,
        "Query 10: Outpatient vs Inpatient Fraud Split": """
    MATCH (p:Provider)-[:FILED]->(c:Claim)
    WHERE p.isFraud = 1
    RETURN c.type as claim_type,
           count(c) as claim_count,
           sum(c.totalCost) as total_cost,
           avg(c.totalCost) as avg_cost
    ORDER BY claim_count DESC
        """,
        "Query 11: Repeat Offender Path": """
    MATCH (b:Beneficiary)-[:HAS_CLAIM]->(c:Claim)<-[:FILED]-(p:Provider)
    WHERE p.isFraud = 1
    WITH b, p, count(c) as claimCount
    WHERE claimCount > 3
    RETURN b.id as beneficiary_id,
           b.age as age,
           b.state as state,
           p.id as provider_id,
           claimCount as claim_count
    ORDER BY claimCount DESC
    LIMIT 100
        """,
        "Query 12: Beneficiary Age Cluster": """
    MATCH (b:Beneficiary)-[:HAS_CLAIM]->(c:Claim)<-[:FILED]-(p:Provider)
    WHERE p.isFraud = 1 AND b.age > 85
    RETURN b.id as beneficiary_id,
           b.age as age,
           b.state as state,
           count(c) as claim_count,
           sum(c.totalCost) as total_cost,
           collect(DISTINCT p.id) as fraud_provider_ids
    ORDER BY total_cost DESC
    LIMIT 100
        """
    }
    
    output_path = os.path.join(QUERIES_DIR, "fraud_patterns.cypher")
    with open(output_path, 'w') as f:
        f.write("-- Healthcare Fraud Detection Queries\n")
        f.write("-- CS 673 Scalable Databases - Fall 2025\n\n")
        
        for query_name, query in queries.items():
            f.write(f"-- {query_name}\n")
            f.write(query)
            f.write("\n\n")
    
    print(f"\nAll queries saved to: {output_path}")

def main():
    """Main execution function"""
    print("=" * 80)
    print("FRAUD DETECTION QUERIES")
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
        
        # Execute all queries
        results = {}
        results['query_1'] = query_1_spider_web(driver, config)
        results['query_2'] = query_2_shared_doctor_ring(driver, config)
        results['query_3'] = query_3_accomplice_physician(driver, config)
        results['query_4'] = query_4_diagnosis_clusters(driver, config)
        results['query_5'] = query_5_high_value_fraud(driver, config)
        results['query_6'] = query_6_dead_patient_claims(driver, config)
        results['query_7'] = query_7_impossible_workload(driver, config)
        results['query_8'] = query_8_total_fraud_exposure(driver, config)
        results['query_9'] = query_9_top_states_fraud(driver, config)
        results['query_10'] = query_10_claim_type_split(driver, config)
        results['query_11'] = query_11_repeat_offender(driver, config)
        results['query_12'] = query_12_elder_fraud(driver, config)
        
        # Save all queries to file
        save_all_queries()
        
        # Summary
        print("\n" + "=" * 80)
        print("QUERY EXECUTION SUMMARY")
        print("=" * 80)
        # Count successful queries (not None means query executed successfully, even if empty)
        successful = sum(1 for r in results.values() if r is not None)
        failed = sum(1 for r in results.values() if r is None)
        print(f"Queries executed: {len(results)}")
        print(f"Successful: {successful}")
        if failed > 0:
            print(f"Failed: {failed}")
            # Identify which queries failed
            failed_queries = [name for name, r in results.items() if r is None]
            print(f"Failed queries: {', '.join(failed_queries)}")
        print("=" * 80)
        
        driver.close()
        
    except Exception as e:
        print(f"\n✗ Query execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

