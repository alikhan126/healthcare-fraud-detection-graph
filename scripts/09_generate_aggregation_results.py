"""
Aggregation Results Generation Script
Generates results for all 10 required aggregation operations
"""
import sys
import os
import pandas as pd
from neo4j import GraphDatabase

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.neo4j_config import get_neo4j_config

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "results")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def execute_aggregation(driver, config, agg_name, cypher, description):
    """Execute an aggregation query and return results"""
    print(f"\n{'='*80}")
    print(f"Aggregation: {agg_name}")
    print(f"{'='*80}")
    print(f"Description: {description}")
    print(f"\nCypher Query:")
    print(cypher)
    print(f"\nExecuting...")
    
    try:
        with driver.session(database=config['database']) as session:
            result = session.run(cypher)
            
            records = []
            for record in result:
                records.append(dict(record))
            
            if records:
                df = pd.DataFrame(records)
                print(f"✓ Aggregation executed successfully")
                print(f"  Results: {len(df)} rows")
                print(f"\nFirst 10 results:")
                print(df.head(10).to_string())
                
                # Save to CSV
                # Clean filename: remove periods, replace spaces with underscores
                clean_name = agg_name.lower().replace('.', '').replace(' ', '_').strip('_')
                output_path = os.path.join(OUTPUT_DIR, f"aggregation_{clean_name}.csv")
                df.to_csv(output_path, index=False)
                print(f"\n  Results saved to: {output_path}")
                
                return df
            else:
                print("  No results returned")
                return pd.DataFrame()
                
    except Exception as e:
        print(f"✗ Aggregation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def aggregation_1_providers_per_beneficiary(driver, config):
    """Aggregation 1: COUNT(DISTINCT providers) per beneficiary"""
    cypher = """
    MATCH (b:Beneficiary)-[:HAS_CLAIM]->(c:Claim)<-[:FILED]-(p:Provider)
    WITH b, collect(DISTINCT p) as providers
    RETURN b.id as beneficiary_id,
           size(providers) as provider_count
    ORDER BY provider_count DESC
    LIMIT 100
    """
    return execute_aggregation(
        driver, config,
        "1. Providers per Beneficiary",
        cypher,
        "COUNT(DISTINCT providers) per beneficiary - Victim analysis"
    )

def aggregation_2_total_cost_per_provider(driver, config):
    """Aggregation 2: SUM(totalCost) per provider"""
    cypher = """
    MATCH (p:Provider)-[:FILED]->(c:Claim)
    RETURN p.id as provider_id,
           p.isFraud as is_fraud,
           sum(c.totalCost) as total_cost,
           count(c) as claim_count,
           avg(c.totalCost) as avg_claim_cost
    ORDER BY total_cost DESC
    LIMIT 100
    """
    return execute_aggregation(
        driver, config,
        "2. Total Cost per Provider",
        cypher,
        "SUM(totalCost) per provider - Fraud exposure calculation"
    )

def aggregation_3_claims_per_physician(driver, config):
    """Aggregation 3: COUNT(claims) per physician"""
    cypher = """
    MATCH (phys:Physician)<-[:ATTENDED_BY]-(c:Claim)
    RETURN phys.id as physician_id,
           count(c) as claim_count
    ORDER BY claim_count DESC
    LIMIT 100
    """
    return execute_aggregation(
        driver, config,
        "3. Claims per Physician",
        cypher,
        "COUNT(claims) per physician - Workload analysis"
    )

def aggregation_4_claims_per_medical_code(driver, config):
    """Aggregation 4: COUNT(claims) per medical code"""
    cypher = """
    MATCH (m:MedicalCode)<-[:INCLUDES_CODE]-(c:Claim)
    RETURN m.code as medical_code,
           m.type as code_type,
           count(c) as usage_count
    ORDER BY usage_count DESC
    LIMIT 100
    """
    return execute_aggregation(
        driver, config,
        "4. Claims per Medical Code",
        cypher,
        "COUNT(claims) per medical code - Code usage frequency"
    )

def aggregation_5_fraud_claims_per_state(driver, config):
    """Aggregation 5: COUNT(fraud claims) per state"""
    cypher = """
    MATCH (b:Beneficiary)-[:HAS_CLAIM]->(c:Claim)<-[:FILED]-(p:Provider)
    WHERE p.isFraud = 1 AND b.State IS NOT NULL AND b.State <> 'UNKNOWN'
    RETURN b.State as state,
           count(c) as fraud_claim_count,
           count(DISTINCT b) as beneficiary_count,
           count(DISTINCT p) as provider_count
    ORDER BY fraud_claim_count DESC
    LIMIT 20
    """
    return execute_aggregation(
        driver, config,
        "5. Fraud Claims per State",
        cypher,
        "COUNT(fraud claims) per state - Geographic distribution"
    )

def aggregation_6_avg_age_fraud_victims(driver, config):
    """Aggregation 6: AVG(age) of fraud victims"""
    cypher = """
    MATCH (b:Beneficiary)-[:HAS_CLAIM]->(c:Claim)<-[:FILED]-(p:Provider)
    WHERE p.isFraud = 1
    RETURN avg(b.age) as avg_age,
           min(b.age) as min_age,
           max(b.age) as max_age,
           count(DISTINCT b) as fraud_victim_count
    """
    return execute_aggregation(
        driver, config,
        "6. Average Age of Fraud Victims",
        cypher,
        "AVG(age) of fraud victims - Demographic analysis"
    )

def aggregation_7_claims_by_claim_type(driver, config):
    """Aggregation 7: COUNT(claims) by claim type"""
    cypher = """
    MATCH (p:Provider)-[:FILED]->(c:Claim)
    WHERE p.isFraud = 1
    RETURN c.type as claim_type,
           count(c) as claim_count,
           sum(c.totalCost) as total_cost,
           avg(c.totalCost) as avg_cost
    ORDER BY claim_count DESC
    """
    return execute_aggregation(
        driver, config,
        "7. Claims by Claim Type",
        cypher,
        "COUNT(claims) by claim type - Claim type distribution"
    )

def aggregation_8_max_cost_per_provider(driver, config):
    """Aggregation 8: MAX(totalCost) per provider"""
    cypher = """
    MATCH (p:Provider)-[:FILED]->(c:Claim)
    WHERE p.isFraud = 1
    RETURN p.id as provider_id,
           max(c.totalCost) as max_claim_cost,
           min(c.totalCost) as min_claim_cost,
           avg(c.totalCost) as avg_claim_cost,
           count(c) as claim_count
    ORDER BY max_claim_cost DESC
    LIMIT 100
    """
    return execute_aggregation(
        driver, config,
        "8. Max Cost per Provider",
        cypher,
        "MAX(totalCost) per provider - Highest fraud claim identification"
    )

def aggregation_9_deceased_beneficiaries_with_claims(driver, config):
    """Aggregation 9: COUNT(deceased beneficiaries) with claims"""
    cypher = """
    MATCH (b:Beneficiary)-[:HAS_CLAIM]->(c:Claim)
    WHERE b.isDeceased = 1
    RETURN count(DISTINCT b) as deceased_beneficiaries_with_claims,
           count(c) as total_claims_for_deceased,
           sum(c.totalCost) as total_cost,
           avg(c.totalCost) as avg_cost
    """
    return execute_aggregation(
        driver, config,
        "9. Deceased Beneficiaries with Claims",
        cypher,
        "COUNT(deceased beneficiaries) with claims - Impossible billing detection"
    )

def aggregation_10_shared_physicians_fraud_providers(driver, config):
    """Aggregation 10: COUNT(shared physicians) between fraud providers"""
    cypher = """
    MATCH (p1:Provider)-[:FILED]->(c1:Claim)-[:ATTENDED_BY]->(phys:Physician)
          <-[:ATTENDED_BY]-(c2:Claim)<-[:FILED]-(p2:Provider)
    WHERE p1.isFraud = 1 AND p2.isFraud = 1 AND p1.id <> p2.id
    WITH p1, p2, collect(DISTINCT phys) as sharedPhysicians
    RETURN p1.id as provider1_id,
           p2.id as provider2_id,
           size(sharedPhysicians) as shared_physician_count,
           [phys in sharedPhysicians | phys.id] as shared_physician_ids
    ORDER BY shared_physician_count DESC
    LIMIT 100
    """
    return execute_aggregation(
        driver, config,
        "10. Shared Physicians Between Fraud Providers",
        cypher,
        "COUNT(shared physicians) between fraud providers - Collusion metric"
    )

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
        
        print("=" * 80)
        print("AGGREGATION OPERATIONS - RESULTS GENERATION")
        print("=" * 80)
        
        # Execute all aggregations
        aggregation_1_providers_per_beneficiary(driver, config)
        aggregation_2_total_cost_per_provider(driver, config)
        aggregation_3_claims_per_physician(driver, config)
        aggregation_4_claims_per_medical_code(driver, config)
        aggregation_5_fraud_claims_per_state(driver, config)
        aggregation_6_avg_age_fraud_victims(driver, config)
        aggregation_7_claims_by_claim_type(driver, config)
        aggregation_8_max_cost_per_provider(driver, config)
        aggregation_9_deceased_beneficiaries_with_claims(driver, config)
        aggregation_10_shared_physicians_fraud_providers(driver, config)
        
        print("\n" + "=" * 80)
        print("ALL AGGREGATIONS COMPLETE")
        print("=" * 80)
        print(f"\nResults saved to: {OUTPUT_DIR}")
        
        driver.close()
        
    except Exception as e:
        print(f"\n✗ Aggregation generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

