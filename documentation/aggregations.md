# Aggregation Operations

This document describes all 10 required aggregation operations performed on the healthcare fraud detection graph database.

## 1. COUNT(DISTINCT providers) per beneficiary

**Purpose**: Victim analysis - Identify beneficiaries who have been treated by multiple providers

**Cypher Query**:
```cypher
MATCH (b:Beneficiary)-[:HAS_CLAIM]->(c:Claim)<-[:FILED]-(p:Provider)
WITH b, collect(DISTINCT p) as providers
RETURN b.id, size(providers) as provider_count
ORDER BY provider_count DESC
```

**Business Value**: Helps identify beneficiaries who may be victims of fraud rings involving multiple providers.

---

## 2. SUM(totalCost) per provider

**Purpose**: Fraud exposure calculation - Calculate total cost of claims per provider

**Cypher Query**:
```cypher
MATCH (p:Provider)-[:FILED]->(c:Claim)
RETURN p.id, sum(c.totalCost) as total_cost
ORDER BY total_cost DESC
```

**Business Value**: Identifies providers with highest financial impact, helping prioritize fraud investigations.

---

## 3. COUNT(claims) per physician

**Purpose**: Workload analysis - Identify physicians with high claim volumes

**Cypher Query**:
```cypher
MATCH (phys:Physician)<-[:ATTENDED_BY]-(c:Claim)
RETURN phys.id, count(c) as claim_count
ORDER BY claim_count DESC
```

**Business Value**: Detects physicians with impossible workloads, which may indicate fraudulent activity.

---

## 4. COUNT(claims) per medical code

**Purpose**: Code usage frequency - Identify most commonly used diagnosis and procedure codes

**Cypher Query**:
```cypher
MATCH (m:MedicalCode)<-[:INCLUDES_CODE]-(c:Claim)
RETURN m.code, m.type, count(c) as usage_count
ORDER BY usage_count DESC
```

**Business Value**: Helps identify code abuse patterns, especially when combined with fraud provider filtering.

---

## 5. COUNT(fraud claims) per state

**Purpose**: Geographic distribution - Identify states with highest fraud activity

**Cypher Query**:
```cypher
MATCH (b:Beneficiary)-[:HAS_CLAIM]->(c:Claim)<-[:FILED]-(p:Provider)
WHERE p.isFraud = 1
RETURN b.state, count(c) as fraud_claim_count
ORDER BY fraud_claim_count DESC
```

**Business Value**: Enables geographic targeting of fraud prevention efforts.

---

## 6. AVG(age) of fraud victims

**Purpose**: Demographic analysis - Understand age distribution of fraud victims

**Cypher Query**:
```cypher
MATCH (b:Beneficiary)-[:HAS_CLAIM]->(c:Claim)<-[:FILED]-(p:Provider)
WHERE p.isFraud = 1
RETURN avg(b.age) as avg_age, 
       min(b.age) as min_age, 
       max(b.age) as max_age
```

**Business Value**: Identifies vulnerable demographics that may be targeted by fraud schemes.

---

## 7. COUNT(claims) by claim type

**Purpose**: Claim type distribution - Compare inpatient vs outpatient fraud patterns

**Cypher Query**:
```cypher
MATCH (p:Provider)-[:FILED]->(c:Claim)
WHERE p.isFraud = 1
RETURN c.type, count(c) as claim_count
ORDER BY claim_count DESC
```

**Business Value**: Helps understand which claim types are more susceptible to fraud.

---

## 8. MAX(totalCost) per provider

**Purpose**: Highest fraud claim identification - Find the most expensive individual claims per provider

**Cypher Query**:
```cypher
MATCH (p:Provider)-[:FILED]->(c:Claim)
WHERE p.isFraud = 1
RETURN p.id, max(c.totalCost) as max_claim_cost
ORDER BY max_claim_cost DESC
```

**Business Value**: Identifies providers with unusually high-value claims that warrant investigation.

---

## 9. COUNT(deceased beneficiaries) with claims

**Purpose**: Impossible billing detection - Find claims filed for deceased beneficiaries

**Cypher Query**:
```cypher
MATCH (b:Beneficiary)-[:HAS_CLAIM]->(c:Claim)
WHERE b.isDeceased = 1
RETURN count(DISTINCT b) as deceased_beneficiaries_with_claims,
       count(c) as total_claims_for_deceased
```

**Business Value**: Detects clear fraud cases where providers bill for services to deceased patients.

---

## 10. COUNT(shared physicians) between fraud providers

**Purpose**: Collusion metric - Identify physician networks connecting fraud providers

**Cypher Query**:
```cypher
MATCH (p1:Provider)-[:FILED]->(c1:Claim)-[:ATTENDED_BY]->(phys:Physician)
      <-[:ATTENDED_BY]-(c2:Claim)<-[:FILED]-(p2:Provider)
WHERE p1.isFraud = 1 AND p2.isFraud = 1 AND p1.id <> p2.id
WITH p1, p2, collect(DISTINCT phys) as sharedPhysicians
RETURN p1.id, p2.id, size(sharedPhysicians) as shared_physician_count
ORDER BY shared_physician_count DESC
```

**Business Value**: Identifies collusion networks where multiple fraud providers share the same physicians.

---

## Summary

These aggregations provide comprehensive insights into:
- **Victim patterns**: Who is being targeted
- **Financial impact**: How much money is involved
- **Geographic distribution**: Where fraud occurs
- **Demographic targeting**: Who is vulnerable
- **Provider networks**: How fraud providers are connected
- **Impossible scenarios**: Clear fraud indicators

All aggregations can be combined with fraud provider filters to focus analysis on confirmed fraudulent activity.

