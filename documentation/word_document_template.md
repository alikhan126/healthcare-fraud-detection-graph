# Word Document Template Structure

This document outlines the required structure for the project Word document submission.

## Document Structure

### Title Page
- Project Title: Healthcare Fraud Detection Graph Database Implementation
- Course: CS 673 Scalable Databases
- Semester: Fall 2025
- Due Date: December 19, 2025
- Student Name: [Your Name]

---

## Section 1: Problem Definition (10 points)

### Content Required:
1. **Healthcare Fraud Statistics**
   - Current fraud statistics in healthcare
   - Financial impact of healthcare fraud
   - Why fraud detection matters

2. **Problem Statement**
   - What patterns we're detecting
   - Why traditional SQL approaches fail
   - Specific fraud patterns addressed:
     - Provider rings targeting same beneficiaries
     - Physician collusion networks
     - Diagnosis code clustering anomalies
     - Claims filed for deceased patients
     - Impossible physician workloads

3. **Dataset Overview**
   - Source: Kaggle - Healthcare Provider Fraud Detection Analysis
   - Data volume: ~138,556 beneficiaries, ~558,211 claims, ~5,410 providers
   - Fraud labels: ~506 fraudulent providers

**Length**: 2-3 pages

---

## Section 2: Graph Database Justification (10 points)

### Content Required:
1. **Why Graph DB over Relational DB**
   - Multi-hop relationship traversal
   - Pattern matching capabilities
   - Network analysis advantages
   - Query complexity comparison

2. **Specific Advantages for Fraud Detection**
   - Efficient relationship traversal
   - Natural representation of fraud networks
   - Complex pattern detection
   - Performance benefits

3. **Query Complexity Comparison**
   - Example: Finding beneficiaries connected to 3+ fraud providers
   - SQL: Multiple JOINs, subqueries, complex WHERE clauses
   - Cypher: Simple pattern matching

**Length**: 2-3 pages

---

## Section 3: Graph Model (10 points)

### Content Required:
1. **Node Type Diagram**
   - Visual diagram showing all 5 node types
   - Properties listed for each node type:
     - Provider: id, isFraud
     - Beneficiary: id, age, state, county, gender, race, isDeceased, chronic conditions
     - Claim: id, type, totalCost, dates, amounts
     - Physician: id
     - MedicalCode: code, type

2. **Relationship Type Diagram**
   - Visual diagram showing all 4 relationship types:
     - FILED: Provider → Claim
     - HAS_CLAIM: Beneficiary → Claim
     - ATTENDED_BY: Claim → Physician
     - INCLUDES_CODE: Claim → MedicalCode

3. **ER-Style Graph Schema Visual**
   - Complete graph schema diagram
   - Show all nodes and relationships
   - Include cardinality if applicable

**Length**: 2-3 pages with diagrams

---

## Section 4: Data Cleansing (10 points)

### Content Required:
1. **Null Value Handling Strategy**
   - Drop if null: Provider, BeneID, ClaimID
   - Keep as null: Optional physicians, diagnosis codes
   - Transform null: DOD → isDeceased, County/State → "UNKNOWN"

2. **Records Dropped and Why**
   - Total records dropped
   - Breakdown by dataset
   - Reasons for dropping

3. **Data Quality Metrics**
   - Before cleansing: record counts, null counts
   - After cleansing: record counts, null counts
   - Data quality report summary
   - Include screenshot or table from `data/stats/data_quality_report.txt`

**Length**: 2-3 pages

---

## Section 5: Data Transformation (10 points)

### Content Required:
1. **ETL Pipeline Description**
   - Step-by-step transformation process
   - Flow diagram of pipeline
   - Script execution order

2. **CSV → Graph Mapping**
   - How each CSV column maps to graph properties
   - Node creation process
   - Relationship creation process

3. **Derived Field Calculations**
   - age = (current_date - DOB) / 365.25
   - isDeceased = 1 if DOD exists else 0
   - totalCost = reimbursedAmount + deductibleAmount
   - claimDuration = (ClaimEndDt - ClaimStartDt).days

4. **Code Snippets**
   - Key transformation code snippets
   - Explanation of logic

**Length**: 2-3 pages

---

## Section 6: Aggregation Operations (10 points)

### Content Required:
1. **List All 10 Aggregations**
   - COUNT(DISTINCT providers) per beneficiary
   - SUM(totalCost) per provider
   - COUNT(claims) per physician
   - COUNT(claims) per medical code
   - COUNT(fraud claims) per state
   - AVG(age) of fraud victims
   - COUNT(claims) by claim type
   - MAX(totalCost) per provider
   - COUNT(deceased beneficiaries) with claims
   - COUNT(shared physicians) between fraud providers

2. **Business Purpose of Each**
   - Why each aggregation matters
   - What insights it provides
   - How it helps fraud detection

3. **Results Summary**
   - Key findings from each aggregation
   - Tables or charts showing results
   - Interpretation of results

**Length**: 3-4 pages

---

## Section 7: Query Analysis (10 points)

### Content Required:
For each of the 12 queries:

1. **Query Description**
   - What the query detects
   - Purpose and business value

2. **Cypher Query**
   - Full Cypher query code
   - Formatted for readability

3. **Screenshot**
   - Screenshot of query result from Neo4j Browser
   - Clear and labeled

4. **Insights**
   - What the results show
   - Key findings
   - Fraud patterns detected

**Queries to Include:**
1. Spider Web Pattern
2. Shared Doctor Ring
3. Accomplice Physician
4. Diagnosis Copy-Paste Clusters
5. High-Value Fraud Claims
6. Dead Patient Claims
7. Impossible Workload Physicians
8. Total Fraud Exposure
9. Top 5 States with Fraud
10. Outpatient vs Inpatient Fraud
11. Repeat Offender Path
12. Beneficiary Age Cluster

**Length**: 6-8 pages (0.5-1 page per query)

---

## Section 8: Node and Relationship Creation (30 points)

### Content Required:
1. **Total Counts**
   - Providers: [count]
   - Beneficiaries: [count]
   - Claims: [count]
   - Physicians: [count]
   - Medical Codes: [count]

2. **Total Relationship Counts by Type**
   - FILED: [count]
   - HAS_CLAIM: [count]
   - ATTENDED_BY: [count]
   - INCLUDES_CODE: [count]

3. **Code Snippets**
   - Cypher code for node creation (example)
   - Cypher code for relationship creation (example)
   - Batch loading approach explanation

4. **Screenshots of Graph Visualizations**
   - Sample graph visualization from Neo4j Browser
   - Show nodes and relationships
   - Label key elements
   - Multiple views if helpful

5. **Loading Statistics**
   - Time taken for each loading phase
   - Batch size used
   - Performance metrics

**Length**: 3-4 pages

---

## Additional Requirements

### Formatting:
- Professional formatting
- Clear section headings
- Page numbers
- Table of contents
- Consistent font and style

### Screenshots:
- All screenshots should be clear and readable
- Label screenshots with captions
- Include query results, graph visualizations, data quality reports

### Code:
- Format code blocks properly
- Use syntax highlighting
- Include comments where helpful

### Total Length:
- Minimum: 15 pages
- Target: 20-25 pages for comprehensive coverage

### Plagiarism:
- Ensure all content is original
- Cite sources if using external statistics
- Plagiarism must be <15%

---

## Submission Checklist

- [ ] All 8 sections complete
- [ ] All 12 queries with screenshots
- [ ] Graph model diagrams included
- [ ] Data quality report included
- [ ] Code snippets included
- [ ] Professional formatting
- [ ] Table of contents
- [ ] Page numbers
- [ ] Self-assessment rubric filled
- [ ] Plagiarism check completed

