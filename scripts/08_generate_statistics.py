"""
Statistics Generation Script
Generates comprehensive statistics report for Section 8 (Node and Relationship Creation)
"""
import sys
import os
import time
from datetime import datetime
from neo4j import GraphDatabase

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.neo4j_config import get_neo4j_config

STATS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "stats")
os.makedirs(STATS_DIR, exist_ok=True)

def generate_statistics_report(driver, config):
    """Generate comprehensive statistics report"""
    print("=" * 80)
    print("GENERATING STATISTICS REPORT")
    print("=" * 80)
    
    report = []
    report.append("=" * 80)
    report.append("NODE AND RELATIONSHIP STATISTICS REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    with driver.session(database=config['database']) as session:
        # Node Counts
        report.append("1. NODE COUNTS")
        report.append("-" * 80)
        
        node_types = ["Provider", "Beneficiary", "Claim", "Physician", "MedicalCode"]
        node_counts = {}
        
        for node_type in node_types:
            result = session.run(f"MATCH (n:{node_type}) RETURN count(n) AS count")
            count = result.single()['count']
            node_counts[node_type] = count
            report.append(f"   {node_type:15} : {count:,}")
        
        report.append(f"\n   Total Nodes: {sum(node_counts.values()):,}\n")
        
        # Relationship Counts
        report.append("2. RELATIONSHIP COUNTS")
        report.append("-" * 80)
        
        rel_types = ["FILED", "HAS_CLAIM", "ATTENDED_BY", "INCLUDES_CODE"]
        rel_counts = {}
        
        for rel_type in rel_types:
            result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS count")
            count = result.single()['count']
            rel_counts[rel_type] = count
            report.append(f"   {rel_type:15} : {count:,}")
        
        report.append(f"\n   Total Relationships: {sum(rel_counts.values()):,}\n")
        
        # Fraud Provider Statistics
        report.append("3. FRAUD PROVIDER STATISTICS")
        report.append("-" * 80)
        
        result = session.run("""
            MATCH (p:Provider)
            RETURN 
                count(p) as total_providers,
                sum(p.isFraud) as fraud_providers,
                sum(CASE WHEN p.isFraud = 0 THEN 1 ELSE 0 END) as legit_providers
        """)
        record = result.single()
        total_providers = record['total_providers']
        fraud_providers = record['fraud_providers']
        legit_providers = record['legit_providers']
        fraud_rate = (fraud_providers / total_providers * 100) if total_providers > 0 else 0
        
        report.append(f"   Total Providers: {total_providers:,}")
        report.append(f"   Fraud Providers: {fraud_providers:,} ({fraud_rate:.2f}%)")
        report.append(f"   Legitimate Providers: {legit_providers:,}\n")
        
        # Claim Statistics
        report.append("4. CLAIM STATISTICS")
        report.append("-" * 80)
        
        result = session.run("""
            MATCH (c:Claim)
            WITH c,
                 CASE WHEN c.type = 'Inpatient' THEN 1 ELSE 0 END as is_inpatient,
                 CASE WHEN c.type = 'Outpatient' THEN 1 ELSE 0 END as is_outpatient
            RETURN 
                count(c) as total_claims,
                sum(is_inpatient) as inpatient_claims,
                sum(is_outpatient) as outpatient_claims,
                sum(c.totalCost) as total_cost,
                avg(c.totalCost) as avg_cost,
                max(c.totalCost) as max_cost,
                min(c.totalCost) as min_cost
        """)
        record = result.single()
        
        if record:
            report.append(f"   Total Claims: {record['total_claims']:,}")
            report.append(f"   Inpatient Claims: {record['inpatient_claims']:,}")
            report.append(f"   Outpatient Claims: {record['outpatient_claims']:,}")
            report.append(f"   Total Cost: ${record['total_cost']:,.2f}" if record['total_cost'] else "   Total Cost: $0.00")
            report.append(f"   Average Cost: ${record['avg_cost']:,.2f}" if record['avg_cost'] else "   Average Cost: $0.00")
            report.append(f"   Max Cost: ${record['max_cost']:,.2f}" if record['max_cost'] else "   Max Cost: $0.00")
            report.append(f"   Min Cost: ${record['min_cost']:,.2f}" if record['min_cost'] else "   Min Cost: $0.00")
        report.append("")
        
        # Fraud Claim Statistics
        report.append("5. FRAUD CLAIM STATISTICS")
        report.append("-" * 80)
        
        result = session.run("""
            MATCH (p:Provider)-[:FILED]->(c:Claim)
            WHERE p.isFraud = 1
            RETURN 
                count(c) as fraud_claims,
                sum(c.totalCost) as fraud_total_cost,
                avg(c.totalCost) as fraud_avg_cost,
                max(c.totalCost) as fraud_max_cost
        """)
        record = result.single()
        
        report.append(f"   Fraud Claims: {record['fraud_claims']:,}")
        report.append(f"   Fraud Total Cost: ${record['fraud_total_cost']:,.2f}")
        report.append(f"   Fraud Average Cost: ${record['fraud_avg_cost']:,.2f}")
        report.append(f"   Fraud Max Cost: ${record['fraud_max_cost']:,.2f}\n")
        
        # Beneficiary Statistics
        report.append("6. BENEFICIARY STATISTICS")
        report.append("-" * 80)
        
        result = session.run("""
            MATCH (b:Beneficiary)
            RETURN 
                count(b) as total_beneficiaries,
                sum(b.isDeceased) as deceased_count,
                avg(b.age) as avg_age,
                min(b.age) as min_age,
                max(b.age) as max_age
        """)
        record = result.single()
        
        report.append(f"   Total Beneficiaries: {record['total_beneficiaries']:,}")
        report.append(f"   Deceased Beneficiaries: {record['deceased_count']:,}")
        report.append(f"   Average Age: {record['avg_age']:.1f}")
        report.append(f"   Min Age: {record['min_age']}")
        report.append(f"   Max Age: {record['max_age']}\n")
        
        # Physician Statistics
        report.append("7. PHYSICIAN STATISTICS")
        report.append("-" * 80)
        
        result = session.run("""
            MATCH (phys:Physician)
            RETURN count(phys) as total_physicians
        """)
        total_physicians = result.single()['total_physicians']
        
        result = session.run("""
            MATCH (phys:Physician)<-[:ATTENDED_BY]-(c:Claim)
            WITH phys, count(c) as claim_count
            RETURN 
                count(phys) as physicians_with_claims,
                avg(claim_count) as avg_claims_per_physician,
                max(claim_count) as max_claims_per_physician
        """)
        record = result.single()
        
        report.append(f"   Total Physicians: {total_physicians:,}")
        report.append(f"   Physicians with Claims: {record['physicians_with_claims']:,}")
        report.append(f"   Average Claims per Physician: {record['avg_claims_per_physician']:.1f}")
        report.append(f"   Max Claims per Physician: {record['max_claims_per_physician']:,}\n")
        
        # Medical Code Statistics
        report.append("8. MEDICAL CODE STATISTICS")
        report.append("-" * 80)
        
        result = session.run("""
            MATCH (m:MedicalCode)
            RETURN 
                count(m) as total_codes,
                count(CASE WHEN m.type = 'Diagnosis' THEN 1 END) as diagnosis_codes,
                count(CASE WHEN m.type = 'Procedure' THEN 1 END) as procedure_codes
        """)
        record = result.single()
        
        report.append(f"   Total Medical Codes: {record['total_codes']:,}")
        report.append(f"   Diagnosis Codes: {record['diagnosis_codes']:,}")
        report.append(f"   Procedure Codes: {record['procedure_codes']:,}\n")
        
        # Data Quality Checks
        report.append("9. DATA QUALITY CHECKS")
        report.append("-" * 80)
        
        # Orphan claims
        result = session.run("""
            MATCH (c:Claim)
            WHERE NOT (c)<-[:FILED]-()
            RETURN count(c) AS orphan_no_provider
        """)
        orphan_no_provider = result.single()['orphan_no_provider']
        
        result = session.run("""
            MATCH (c:Claim)
            WHERE NOT (c)<-[:HAS_CLAIM]-()
            RETURN count(c) AS orphan_no_beneficiary
        """)
        orphan_no_beneficiary = result.single()['orphan_no_beneficiary']
        
        report.append(f"   Claims without Provider: {orphan_no_provider}")
        report.append(f"   Claims without Beneficiary: {orphan_no_beneficiary}")
        
        if orphan_no_provider == 0 and orphan_no_beneficiary == 0:
            report.append("   ✓ No orphan claims found")
        else:
            report.append("   ⚠ Some orphan claims found")
        
        # Duplicate relationships
        result = session.run("""
            MATCH (p:Provider)-[r:FILED]->(c:Claim)
            WITH p, c, count(r) as rel_count
            WHERE rel_count > 1
            RETURN count(*) as duplicate_count
        """)
        duplicates = result.single()['duplicate_count']
        report.append(f"   Duplicate FILED relationships: {duplicates}")
        
        if duplicates == 0:
            report.append("   ✓ No duplicate relationships found")
        else:
            report.append("   ⚠ Some duplicate relationships found")
        
        report.append("")
        
        # Summary
        report.append("=" * 80)
        report.append("SUMMARY")
        report.append("=" * 80)
        report.append(f"Total Nodes: {sum(node_counts.values()):,}")
        report.append(f"Total Relationships: {sum(rel_counts.values()):,}")
        report.append(f"Fraud Providers: {fraud_providers:,} ({fraud_rate:.2f}%)")
        
        # Get claim summary again for summary section
        result = session.run("MATCH (c:Claim) RETURN count(c) as total_claims, sum(c.totalCost) as total_cost")
        summary_record = result.single()
        if summary_record:
            report.append(f"Total Claims: {summary_record['total_claims']:,}")
            report.append(f"Total Cost: ${summary_record['total_cost']:,.2f}" if summary_record['total_cost'] else "Total Cost: $0.00")
        report.append("=" * 80)
    
    # Write report to file
    report_text = "\n".join(report)
    report_path = os.path.join(STATS_DIR, "node_relationship_statistics.txt")
    
    with open(report_path, 'w') as f:
        f.write(report_text)
    
    print(report_text)
    print(f"\n✓ Statistics report saved to: {report_path}")
    
    return report_text

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
        
        generate_statistics_report(driver, config)
        
        driver.close()
        
    except Exception as e:
        print(f"\n✗ Statistics generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

