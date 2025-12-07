-- Healthcare Fraud Detection Queries
-- CS 673 Scalable Databases - Fall 2025

-- Query 1: Spider Web Pattern

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
        

-- Query 2: Shared Doctor Ring

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
        

-- Query 3: Accomplice Physician

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
        

-- Query 4: Diagnosis Copy-Paste Clusters

    MATCH (m:MedicalCode)<-[:INCLUDES_CODE]-(c:Claim)<-[:FILED]-(p:Provider)
    WHERE p.isFraud = 1
    WITH m, count(DISTINCT c) as usageCount
    WHERE usageCount > 50
    RETURN m.code as medical_code,
           m.type as code_type,
           usageCount as usage_count
    ORDER BY usageCount DESC
    LIMIT 100
        

-- Query 5: High-Value Fraud Claims

    MATCH (p:Provider)-[:FILED]->(c:Claim)-[:ATTENDED_BY]->(phys:Physician)
    WHERE p.isFraud = 1 AND c.totalCost > 10000
    RETURN p.id as provider_id,
           c.id as claim_id,
           c.type as claim_type,
           c.totalCost as total_cost,
           collect(DISTINCT phys.id) as physician_ids
    ORDER BY c.totalCost DESC
    LIMIT 100
        

-- Query 6: Dead Patient Claims

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
        

-- Query 7: Impossible Workload Physicians

    MATCH (phys:Physician)<-[:ATTENDED_BY]-(c:Claim)<-[:FILED]-(p:Provider)
    WHERE p.isFraud = 1
    WITH phys, count(DISTINCT c) as fraudClaimCount
    WHERE fraudClaimCount > 10
    RETURN phys.id as physician_id,
           fraudClaimCount as fraud_claim_count
    ORDER BY fraudClaimCount DESC
    LIMIT 100
        

-- Query 8: Total Fraud Exposure

    MATCH (p:Provider)-[:FILED]->(c:Claim)
    WHERE p.isFraud = 1
    RETURN sum(c.totalCost) as total_fraud_exposure,
           count(DISTINCT p) as fraud_provider_count,
           count(c) as total_fraud_claims,
           avg(c.totalCost) as avg_claim_cost,
           max(c.totalCost) as max_claim_cost,
           min(c.totalCost) as min_claim_cost
        

-- Query 9: Top 5 States with Fraud Activity

    MATCH (b:Beneficiary)-[:HAS_CLAIM]->(c:Claim)<-[:FILED]-(p:Provider)
    WHERE p.isFraud = 1
    WITH b.state as state, count(c) as claim_count
    WHERE state IS NOT NULL AND state <> 'UNKNOWN'
    RETURN state,
           claim_count
    ORDER BY claim_count DESC
    LIMIT 5
        

-- Query 10: Outpatient vs Inpatient Fraud Split

    MATCH (p:Provider)-[:FILED]->(c:Claim)
    WHERE p.isFraud = 1
    RETURN c.type as claim_type,
           count(c) as claim_count,
           sum(c.totalCost) as total_cost,
           avg(c.totalCost) as avg_cost
    ORDER BY claim_count DESC
        

-- Query 11: Repeat Offender Path

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
        

-- Query 12: Beneficiary Age Cluster

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
        

