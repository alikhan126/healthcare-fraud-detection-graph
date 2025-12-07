# ETL Pipeline Flow

This document describes the complete ETL (Extract, Transform, Load) pipeline for the healthcare fraud detection system.

## Pipeline Overview

The ETL pipeline transforms raw healthcare CSV files into a Neo4j graph database, enabling fraud detection through relationship analysis.

## Pipeline Stages

### Stage 1: Data Extraction
**Script:** `scripts/download_data.py` (optional)

**Input:** Kaggle dataset
**Output:** Raw CSV files in `data/raw/`

**Files:**
- `Train_Beneficiarydata-1542865627584.csv`
- `Train_Inpatientdata-1542865627584.csv`
- `Train_Outpatientdata-1542865627584.csv`
- `Train-1542865627584.csv`

---

### Stage 2: Data Cleansing
**Script:** `scripts/01_data_cleansing.py`

**Input:** Raw CSV files from `data/raw/`
**Output:** Cleaned CSV files in `data/processed/`

**Process:**
1. Load all 4 CSV files
2. Convert date columns to datetime format
3. Handle null values:
   - **Drop if null:** Provider, BeneID, ClaimID (critical fields)
   - **Keep as null:** Optional physicians, diagnosis codes
   - **Transform null:**
     - DOD → isDeceased (1 if DOD exists, else 0)
     - County/State → "UNKNOWN" if null
4. Calculate derived fields:
   - age = (current_date - DOB) / 365.25
   - isDeceased = 1 if DOD exists else 0
5. Generate data quality report
6. Save cleaned files:
   - `beneficiary_cleaned.csv`
   - `inpatient_cleaned.csv`
   - `outpatient_cleaned.csv`
   - `provider_cleaned.csv`

**Output Files:**
- Cleaned CSV files
- `data/stats/data_quality_report.txt`

---

### Stage 3: Data Transformation
**Script:** `scripts/02_data_transformation.py`

**Input:** Cleaned CSV files from `data/processed/`
**Output:** Graph-ready CSV files in `data/processed/`

**Process:**

#### 3.1 Merge Claims Data
- Merge inpatient and outpatient claims
- Add `type` field ("Inpatient" or "Outpatient")
- Combine into single claims dataset

#### 3.2 Prepare Node Files

**Provider Nodes:**
- Extract: Provider, isFraud
- Rename: Provider → id
- Output: `provider_nodes.csv`

**Beneficiary Nodes:**
- Extract all beneficiary fields
- Keep calculated fields (age, isDeceased)
- Output: `beneficiary_nodes.csv`

**Claim Nodes:**
- Extract claim fields
- Calculate: totalCost = reimbursedAmount + deductibleAmount
- Add type field
- Output: `claim_nodes.csv`

**Physician Nodes:**
- Extract unique physicians from:
  - AttendingPhysician
  - OperatingPhysician
  - OtherPhysician
- Output: `physician_nodes.csv`

**Medical Code Nodes:**
- Extract unique codes from:
  - Diagnosis codes (ClmDiagnosisCode_1 through _10)
  - Procedure codes (ClmProcedureCode_1 through _6)
- Add type field ("Diagnosis" or "Procedure")
- Output: `medical_code_nodes.csv`

#### 3.3 Prepare Relationship Files

**FILED Relationships:**
- Provider → Claim
- Extract: Provider, ClaimID
- Output: `filed_relationships.csv`

**HAS_CLAIM Relationships:**
- Beneficiary → Claim
- Extract: BeneID, ClaimID
- Output: `has_claim_relationships.csv`

**ATTENDED_BY Relationships:**
- Claim → Physician
- Extract: ClaimID, AttendingPhysician/OperatingPhysician/OtherPhysician
- Add type field (Attending, Operating, Other)
- Output: `attended_by_relationships.csv`

**INCLUDES_CODE Relationships:**
- Claim → MedicalCode
- Extract: ClaimID, diagnosis/procedure codes
- Output: `includes_code_relationships.csv`

**Output Files:**
- `provider_nodes.csv`
- `beneficiary_nodes.csv`
- `claim_nodes.csv`
- `physician_nodes.csv`
- `medical_code_nodes.csv`
- `filed_relationships.csv`
- `has_claim_relationships.csv`
- `attended_by_relationships.csv`
- `includes_code_relationships.csv`

---

### Stage 4: Neo4j Database Setup
**Script:** `scripts/03_neo4j_setup.py`

**Process:**
1. Connect to Neo4j
2. Create database (if supported)
3. Create indexes:
   - Provider.id
   - Beneficiary.id
   - Claim.id
   - Physician.id
   - MedicalCode.code
4. Create constraints:
   - Unique constraints on node IDs
5. Verify setup

**Output:** Neo4j database ready for data loading

---

### Stage 5: Node Loading
**Script:** `scripts/04_load_nodes.py`

**Input:** Node CSV files from `data/processed/`
**Output:** Nodes in Neo4j database

**Process:**
1. Load Provider nodes (batch size: 1000)
2. Load Beneficiary nodes (batch size: 1000)
3. Load Claim nodes (batch size: 1000)
4. Load Physician nodes (batch size: 1000)
5. Load MedicalCode nodes (batch size: 1000)

**Method:** Batch loading using UNWIND for performance

**Example Cypher:**
```cypher
UNWIND $records AS record
CREATE (p:Provider {
    id: record.id,
    isFraud: record.isFraud
})
```

**Output:** All nodes created in Neo4j

---

### Stage 6: Relationship Loading
**Script:** `scripts/05_load_relationships.py`

**Input:** Relationship CSV files from `data/processed/`
**Output:** Relationships in Neo4j database

**Process:**
1. Load FILED relationships (batch size: 1000)
2. Load HAS_CLAIM relationships (batch size: 1000)
3. Load ATTENDED_BY relationships (batch size: 1000)
4. Load INCLUDES_CODE relationships (batch size: 1000)

**Method:** Batch loading using UNWIND and MATCH

**Example Cypher:**
```cypher
UNWIND $records AS record
MATCH (p:Provider {id: record.provider_id})
MATCH (c:Claim {id: record.claim_id})
CREATE (p)-[:FILED]->(c)
```

**Output:** All relationships created in Neo4j

---

### Stage 7: Data Validation
**Script:** `scripts/07_validation.py`

**Process:**
1. Validate node counts
2. Validate relationship counts
3. Check for orphan claims
4. Validate fraud provider counts
5. Check for duplicate relationships
6. Validate totalCost calculations

**Output:** Validation report

---

### Stage 8: Query Execution
**Script:** `scripts/06_queries.py`

**Process:**
1. Execute all 12 fraud detection queries
2. Export results to CSV
3. Save queries to `queries/fraud_patterns.cypher`

**Output:**
- Query result CSV files in `outputs/results/`
- Query Cypher file in `queries/fraud_patterns.cypher`

---

## Complete Pipeline Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ETL PIPELINE FLOW                        │
└─────────────────────────────────────────────────────────────┘

1. EXTRACTION
   ┌──────────────┐
   │ Kaggle Dataset│
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │  Raw CSV     │
   │  Files       │
   └──────┬───────┘
          │
          ▼
2. CLEANSING
   ┌──────────────┐
   │ Data         │
   │ Cleansing    │
   │ Script       │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Cleaned CSV  │
   │ Files        │
   └──────┬───────┘
          │
          ▼
3. TRANSFORMATION
   ┌──────────────┐
   │ Data         │
   │ Transform    │
   │ Script       │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Node CSV     │
   │ Files        │
   └──────┬───────┘
          │
   ┌──────▼───────┐
   │ Relationship │
   │ CSV Files    │
   └──────┬───────┘
          │
          ▼
4. NEO4J SETUP
   ┌──────────────┐
   │ Database     │
   │ Setup        │
   │ Script       │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Neo4j DB     │
   │ (Indexes,    │
   │  Constraints)│
   └──────┬───────┘
          │
          ▼
5. NODE LOADING
   ┌──────────────┐
   │ Load Nodes   │
   │ Script       │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Nodes in     │
   │ Neo4j        │
   └──────┬───────┘
          │
          ▼
6. RELATIONSHIP LOADING
   ┌──────────────┐
   │ Load         │
   │ Relationships│
   │ Script       │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Relationships│
   │ in Neo4j     │
   └──────┬───────┘
          │
          ▼
7. VALIDATION
   ┌──────────────┐
   │ Validation   │
   │ Script       │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Validated    │
   │ Graph DB     │
   └──────┬───────┘
          │
          ▼
8. QUERY EXECUTION
   ┌──────────────┐
   │ Fraud        │
   │ Detection    │
   │ Queries      │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Query        │
   │ Results      │
   │ (CSV)        │
   └──────────────┘
```

## Execution Order

The complete pipeline can be run in two ways:

### Option 1: Automated Pipeline
```bash
python run_pipeline.py
```

This runs all scripts in the correct order:
1. `01_data_cleansing.py`
2. `02_data_transformation.py`
3. `03_neo4j_setup.py`
4. `04_load_nodes.py`
5. `05_load_relationships.py`
6. `07_validation.py`
7. `06_queries.py`

### Option 2: Manual Execution
```bash
# Step 1: Clean data
python scripts/01_data_cleansing.py

# Step 2: Transform data
python scripts/02_data_transformation.py

# Step 3: Setup Neo4j
python scripts/03_neo4j_setup.py

# Step 4: Load nodes
python scripts/04_load_nodes.py

# Step 5: Load relationships
python scripts/05_load_relationships.py

# Step 6: Validate
python scripts/07_validation.py

# Step 7: Execute queries
python scripts/06_queries.py
```

## Key Transformations

### Derived Fields

1. **age**
   - Formula: `(current_date - DOB) / 365.25`
   - Type: Integer
   - Purpose: Age calculation for demographic analysis

2. **isDeceased**
   - Formula: `1 if DOD exists else 0`
   - Type: Integer (0 or 1)
   - Purpose: Flag for deceased beneficiaries

3. **totalCost**
   - Formula: `reimbursedAmount + deductibleAmount`
   - Type: Float
   - Purpose: Total claim cost for fraud analysis

4. **claimDuration**
   - Formula: `(ClaimEndDt - ClaimStartDt).days`
   - Type: Integer
   - Purpose: Claim duration in days

### Data Type Conversions

- **Dates:** String → DateTime
- **Numbers:** String → Integer/Float
- **Booleans:** Y/N → 1/0
- **Nulls:** Various strategies (drop, keep, transform)

## Performance Considerations

### Batch Loading
- All loading operations use batch size of 1000
- Reduces memory usage
- Improves performance

### Indexes
- Indexes created on all node ID fields
- Speeds up relationship creation
- Improves query performance

### Constraints
- Unique constraints prevent duplicates
- Ensures data integrity
- Validates during loading

## Error Handling

Each script includes:
- Connection error handling
- Data validation
- Progress reporting
- Error logging

## Output Summary

**Files Created:**
- 5 node CSV files
- 4 relationship CSV files
- Data quality report
- Statistics report
- 12 query result CSV files

**Database:**
- ~700K+ nodes
- ~1M+ relationships
- Fully indexed and constrained

---

## Summary

The ETL pipeline transforms raw healthcare CSV data into a Neo4j graph database through:
1. **Extraction:** Download from Kaggle
2. **Cleansing:** Handle nulls, calculate derived fields
3. **Transformation:** Create node and relationship files
4. **Loading:** Batch load into Neo4j
5. **Validation:** Verify data integrity
6. **Querying:** Execute fraud detection queries

The pipeline is automated, efficient, and produces a fully functional graph database for fraud detection.

