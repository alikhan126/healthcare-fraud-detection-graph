# Data Dictionary

## Node Types

### Provider
- **id** (string): Unique provider identifier
- **isFraud** (integer): Fraud flag (1 = fraud, 0 = legitimate)

### Beneficiary
- **id** (string): Unique beneficiary (patient) identifier
- **age** (integer): Age calculated from date of birth
- **State** (string): State of residence
- **County** (string): County of residence
- **Gender** (string): Gender (0/1/2)
- **Race** (integer): Race code
- **isDeceased** (integer): Deceased flag (1 = deceased, 0 = alive)
- **ChronicCond_Alzheimer** (integer): Alzheimer's chronic condition (0/1)
- **ChronicCond_Heartfailure** (integer): Heart failure chronic condition (0/1)
- **ChronicCond_KidneyDisease** (integer): Kidney disease chronic condition (0/1)
- **ChronicCond_Cancer** (integer): Cancer chronic condition (0/1)
- **ChronicCond_ObstrPulmonary** (integer): Obstructive pulmonary chronic condition (0/1)
- **ChronicCond_Depression** (integer): Depression chronic condition (0/1)
- **ChronicCond_Diabetes** (integer): Diabetes chronic condition (0/1)
- **ChronicCond_IschemicHeart** (integer): Ischemic heart chronic condition (0/1)
- **ChronicCond_Osteoporasis** (integer): Osteoporosis chronic condition (0/1)
- **ChronicCond_rheumatoidarthritis** (integer): Rheumatoid arthritis chronic condition (0/1)
- **ChronicCond_stroke** (integer): Stroke chronic condition (0/1)
- **RenalDiseaseIndicator** (string): Renal disease indicator (Y/N)

### Claim
- **id** (string): Unique claim identifier
- **type** (string): Claim type ("Inpatient" or "Outpatient")
- **totalCost** (float): Total cost (reimbursed + deductible)
- **claimStartDate** (date): Claim start date
- **claimEndDate** (date): Claim end date
- **admissionDate** (date): Admission date (inpatient only)
- **dischargeDate** (date): Discharge date (inpatient only)
- **reimbursedAmount** (float): Amount reimbursed by insurance
- **deductibleAmount** (float): Deductible amount paid

### Physician
- **id** (string): Unique physician identifier

### MedicalCode
- **code** (string): Medical code (diagnosis or procedure)
- **type** (string): Code type ("Diagnosis" or "Procedure")

## Relationship Types

### FILED
- **From**: Provider
- **To**: Claim
- **Description**: Provider filed a claim

### HAS_CLAIM
- **From**: Beneficiary
- **To**: Claim
- **Description**: Beneficiary has a claim

### ATTENDED_BY
- **From**: Claim
- **To**: Physician
- **Properties**:
  - **type** (string): Physician type ("Attending", "Operating", "Other")
- **Description**: Claim was attended by a physician

### INCLUDES_CODE
- **From**: Claim
- **To**: MedicalCode
- **Description**: Claim includes a medical code (diagnosis or procedure)

## Source Files

### Train_Beneficiarydata-1542865627584.csv
Contains beneficiary demographic and health information.

### Train_Inpatientdata-1542865627584.csv
Contains inpatient claim data with admission/discharge dates.

### Train_Outpatientdata-1542865627584.csv
Contains outpatient claim data without admission dates.

### Train-1542865627584.csv
Contains provider fraud labels (PotentialFraud: Yes/No).

