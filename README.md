# Healthcare Fraud Detection Graph Database

CS 673 Scalable Databases - Fall 2025 Final Project

## Project Overview

This project implements a healthcare fraud detection system using Neo4j graph database to identify fraud patterns through relationship analysis of Medicare claims data. The system processes healthcare provider data, beneficiary information, medical claims, and physician relationships to detect various fraud patterns using graph-based queries.

## Prerequisites

- **Docker and Docker Compose** (required for Neo4j, optional for Python scripts)
- **Python 3.8+** (if running scripts locally)
- **Kaggle API credentials** (optional - for automated dataset download)

## Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env and set your Neo4j password (REQUIRED)
nano .env
```

**Minimum required in .env:**
```bash
NEO4J_PASSWORD=your_secure_password_here
```

Other values have defaults:
- `NEO4J_USERNAME=neo4j` (default)
- `NEO4J_URI=bolt://localhost:7687` (default)
- `NEO4J_DATABASE=healthproject` (default)

### 2. Start Neo4j

```bash
# Start Neo4j container
docker-compose up -d neo4j

# Verify Neo4j is running
docker-compose ps

# Access Neo4j Browser at http://localhost:7474
# Login: neo4j / (your password from .env)
```

### 3. Install Python Dependencies

**Option A: Local Installation (Recommended for development)**
```bash
pip install -r requirements.txt
```

**Option B: Use Docker (see Docker Setup section below)**

### 4. Download Dataset

**Option A: Manual Download (Recommended)**
1. Visit: https://www.kaggle.com/datasets/rohitrox/healthcare-provider-fraud-detection-analysis
2. Download and extract CSV files to `data/raw/`:
   - `Train_Beneficiarydata-1542865627584.csv`
   - `Train_Inpatientdata-1542865627584.csv`
   - `Train_Outpatientdata-1542865627584.csv`
   - `Train-1542865627584.csv`

**Option B: Using Kaggle API**
```bash
# Add to .env:
# KAGGLE_USERNAME=your_username
# KAGGLE_KEY=your_api_key

python scripts/download_data.py
```

### 5. Run Data Pipeline

**Option A: Run complete pipeline automatically**
```bash
python run_pipeline.py
```

**Option B: Run scripts individually**
```bash
# 1. Clean and validate data
python scripts/01_data_cleansing.py

# 2. Transform data for graph model
python scripts/02_data_transformation.py

# 3. Setup Neo4j database, indexes, constraints
python scripts/03_neo4j_setup.py

# 4. Load nodes
python scripts/04_load_nodes.py

# 5. Load relationships
python scripts/05_load_relationships.py

# 6. Validate data (optional)
python scripts/07_validation.py

# 7. Execute fraud detection queries
python scripts/06_queries.py
```

## Graph Model

### Node Types
- **Provider**: Healthcare providers with fraud labels (id, isFraud)
- **Beneficiary**: Patients with demographics and chronic conditions (id, age, state, county, gender, race, isDeceased, chronic conditions)
- **Claim**: Inpatient/Outpatient claims (id, type, totalCost, dates, amounts)
- **Physician**: Attending, operating, and other physicians (id)
- **MedicalCode**: Diagnosis and procedure codes (code, type)

### Relationship Types
- **FILED**: Provider → Claim
- **HAS_CLAIM**: Beneficiary → Claim
- **ATTENDED_BY**: Claim → Physician
- **INCLUDES_CODE**: Claim → MedicalCode

## Fraud Detection Queries

12 fraud detection queries are implemented in `scripts/06_queries.py`:

1. **Spider Web Pattern** - Beneficiaries connected to 3+ fraud providers
2. **Shared Doctor Ring** - Fraud providers sharing same physicians
3. **Accomplice Physician** - Physicians connected to both fraud and legitimate providers
4. **Diagnosis Copy-Paste Clusters** - Medical codes used >50 times by fraud providers
5. **High-Value Fraud Claims** - Fraud provider claims with totalCost > 10000
6. **Dead Patient Claims** - Claims filed for deceased beneficiaries
7. **Impossible Workload Physicians** - Physicians with >10 fraud claims
8. **Total Fraud Exposure** - SUM(totalCost) for all fraud provider claims
9. **Top 5 States with Fraud** - COUNT(claims) by Beneficiary.state
10. **Outpatient vs Inpatient Fraud** - COUNT(claims) by Claim.type
11. **Repeat Offender Path** - Beneficiaries with >3 claims from same fraud provider
12. **Beneficiary Age Cluster** - Fraud claims for beneficiaries age >85

Query results are exported to `outputs/results/` and queries are saved to `queries/fraud_patterns.cypher`.

## Project Structure

```
scalable-db/
├── config/
│   └── neo4j_config.py          # Neo4j connection configuration
├── data/
│   ├── raw/                      # Original CSV files (not in git)
│   ├── processed/                # Cleaned and transformed CSV files
│   └── stats/                    # Data quality reports
├── scripts/
│   ├── 01_data_cleansing.py      # Data cleaning and validation
│   ├── 02_data_transformation.py # Transform to graph model format
│   ├── 03_neo4j_setup.py         # Database setup, indexes, constraints
│   ├── 04_load_nodes.py          # Load node data
│   ├── 05_load_relationships.py  # Load relationship data
│   ├── 06_queries.py             # Execute fraud detection queries
│   ├── 07_validation.py           # Validate loaded data
│   ├── 08_generate_statistics.py  # Generate node/relationship statistics
│   ├── 09_generate_aggregation_results.py  # Generate aggregation results
│   └── download_data.py          # Kaggle dataset download (optional)
├── queries/
│   └── fraud_patterns.cypher     # Cypher queries for fraud detection
├── outputs/
│   ├── results/                  # CSV exports of query results
│   └── screenshots/              # Query result screenshots
├── documentation/                # Project documentation
│   ├── problem_definition.md     # Section 1: Problem definition
│   ├── graph_justification.md    # Section 2: Graph DB justification
│   ├── graph_model_diagrams.md   # Section 3: Graph model diagrams
│   ├── data_dictionary.md         # Graph model data dictionary
│   ├── aggregations.md            # Section 6: Aggregation operations
│   ├── etl_pipeline_flow.md       # Section 5: ETL pipeline description
│   └── word_document_template.md  # Word document structure template
├── docker-compose.yml            # Neo4j and app services
├── docker-compose.app.yml        # Optional app service override
├── Dockerfile                    # Python application container
├── entrypoint.sh                 # Container entrypoint script
├── requirements.txt              # Python dependencies
├── run_pipeline.py               # Master pipeline script
├── .env.example                  # Environment variables template
└── README.md                     # This file
```

## Docker Setup

This project includes comprehensive Docker support for both Neo4j and Python application. You can choose to run everything in Docker or use a hybrid approach.

### Architecture

- **Neo4j Service**: Runs Neo4j database in Docker (recommended)
- **Python App Service**: Optional - can run scripts in Docker or locally

### Setup Options

#### Option 1: Neo4j in Docker, Scripts Locally (Recommended)

This is the simplest setup - Neo4j runs in Docker, but you run Python scripts on your local machine.

```bash
# 1. Create .env file
cp .env.example .env
# Edit .env and set NEO4J_PASSWORD

# 2. Start only Neo4j
docker-compose up -d neo4j

# 3. Install Python dependencies locally
pip install -r requirements.txt

# 4. Run scripts locally
python run_pipeline.py
```

#### Option 2: Everything in Docker

Run both Neo4j and Python scripts in Docker containers.

```bash
# 1. Create .env file
cp .env.example .env
# Edit .env and set NEO4J_PASSWORD

# 2. Build and start all services
docker-compose build
docker-compose up -d

# 3. Run scripts in container
docker-compose run app python run_pipeline.py
```

### Dockerfile Details

The `Dockerfile` sets up:

- **Base Image**: Python 3.11-slim
- **System Dependencies**: gcc, g++, curl, wget, bash (for building Python packages)
- **Entrypoint Script**: `entrypoint.sh` automatically:
  - Creates a Python virtual environment (`/app/.venv`)
  - Activates the virtual environment
  - Installs/updates all dependencies from `requirements.txt`
  - Then executes your command
- **Python Packages**: All from `requirements.txt`
  - neo4j (database driver)
  - pandas (data processing)
  - numpy (numerical operations)
  - python-dotenv (environment variables)
  - kaggle (dataset download)

**Note**: The virtual environment is created automatically on container startup, so dependencies are always up-to-date with your `requirements.txt`.

### Building the Image

```bash
# Build the Python application image
docker build -t healthcare-fraud-app .

# Or use docker-compose
docker-compose build app
```

### Running Scripts in Docker

#### Single Script

```bash
docker-compose run app python scripts/01_data_cleansing.py
```

#### Complete Pipeline

```bash
# Run all scripts sequentially
docker-compose run app python run_pipeline.py
```

#### Interactive Shell

```bash
# Get a shell in the container
docker-compose run app /bin/bash

# Then run scripts normally
python scripts/01_data_cleansing.py
```

### Volume Mounts

The Docker setup mounts the following directories:

- `./data` → `/app/data` - Data files (raw, processed, stats)
- `./outputs` → `/app/outputs` - Query results and screenshots
- `./queries` → `/app/queries` - Cypher query files
- `./scripts` → `/app/scripts` - Python scripts
- `./config` → `/app/config` - Configuration files
- `./.env` → `/app/.env:ro` - Environment variables (read-only)

This ensures:
- ✅ Data persists on your host machine
- ✅ Scripts can be edited without rebuilding
- ✅ Results are saved to your local filesystem

### Network Configuration

Both services are on the `fraud-detection-network`:

- **Neo4j**: Accessible at `bolt://neo4j:7687` from within Docker network
- **App**: Can connect to Neo4j using service name `neo4j`

When running scripts locally, use `bolt://localhost:7687` (port mapping).

**Important**: When running in Docker, the app connects to Neo4j using:
- `NEO4J_URI=bolt://neo4j:7687` (service name, not localhost)

This is automatically set in `docker-compose.yml`.

### Benefits of Docker

✅ **Consistent Environment**: Same Python version and packages everywhere  
✅ **Isolation**: No conflicts with system Python  
✅ **Reproducibility**: Works the same on any machine  
✅ **Easy Cleanup**: Remove container, keep data  

### When to Use Docker vs Local

**Use Docker for scripts if:**
- You have Python version conflicts
- You want complete isolation
- You're deploying to production
- You want consistent CI/CD

**Use local Python if:**
- You prefer faster iteration
- You want to debug easily
- You have a clean Python environment
- You're comfortable with virtual environments

## Verification

### Check Neo4j Connection
```bash
python -c "from config.neo4j_config import get_neo4j_config; print(get_neo4j_config())"
```

### Access Neo4j Browser
1. Open: http://localhost:7474
2. Login with credentials from `.env`
3. Run test query:
```cypher
MATCH (n) RETURN count(n) as total_nodes
```

### Verify Data Loaded
```bash
python scripts/07_validation.py
```

## Troubleshooting

### Neo4j Connection Issues

**If running scripts in Docker:**
```bash
# Ensure Neo4j service is running
docker-compose ps

# Check network connectivity
docker network ls
docker network inspect scalable-db_fraud-detection-network

# Verify NEO4J_URI=bolt://neo4j:7687 in container
docker-compose run app env | grep NEO4J
```

**If running scripts locally:**
```bash
# Check if Neo4j is running
docker-compose ps neo4j

# Verify port mapping
docker-compose port neo4j 7687

# Verify NEO4J_URI=bolt://localhost:7687 in .env
cat .env | grep NEO4J_URI
```

**General Neo4j troubleshooting:**
```bash
# Restart Neo4j
docker-compose restart neo4j

# View logs
docker-compose logs neo4j

# Check Neo4j health
docker-compose exec neo4j wget --no-verbose --tries=1 --spider http://localhost:7474

# Reset Neo4j (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d neo4j
```

### Python Import Errors

**Local installation:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Or use virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Docker installation:**
```bash
# Rebuild the image (entrypoint will reinstall dependencies)
docker-compose build app

# Or manually reinstall in running container
docker-compose run app bash -c "source /app/.venv/bin/activate && pip install -r requirements.txt"
```

**Note**: The entrypoint script automatically installs dependencies on every container start, so rebuilding should fix most issues.

### Data File Not Found
- Ensure CSV files are in `data/raw/` directory
- Check file names match exactly (case-sensitive)
- Verify file permissions: `ls -la data/raw/`
- If using Docker, check volume mounts: `docker-compose run app ls -la /app/data/raw`

### Memory Issues

If you encounter memory errors:

1. **Reduce batch size** in `config/neo4j_config.py`:
   ```python
   BATCH_SIZE = 500  # Instead of 1000
   ```

2. **Increase Neo4j memory** in `docker-compose.yml`:
   ```yaml
   environment:
     - NEO4J_dbms_memory_heap_max__size=4G
     - NEO4J_dbms_memory_pagecache_size=2G
   ```

3. **Check system resources:**
   ```bash
   # Check Docker memory usage
   docker stats
   
   # Check available disk space
   df -h
   ```

### Data Not Persisting (Docker)

- Check volume mounts in `docker-compose.yml`
- Verify paths exist on host: `ls -la data/`
- Check container volumes: `docker-compose run app ls -la /app/data`
- Verify volume is not being removed: `docker volume ls`

### Container Won't Start

```bash
# Check container logs
docker-compose logs app

# Check if image exists
docker images | grep healthcare-fraud

# Rebuild from scratch
docker-compose build --no-cache app
```

## Stopping Neo4j

```bash
# Stop Neo4j container
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```

## Environment Variables

The `.env` file contains all configuration. Copy `.env.example` to `.env` and update with your values.

### Required Variables

- `NEO4J_PASSWORD` - **REQUIRED** - Set a strong password for Neo4j authentication

### Optional Variables (have defaults)

**Neo4j Configuration:**
- `NEO4J_USERNAME` - Default: `neo4j`
- `NEO4J_URI` - Default: `bolt://localhost:7687` (use `bolt://neo4j:7687` when running in Docker)
- `NEO4J_DATABASE` - Default: `healthproject`

**Kaggle API (Optional - only if using automated download):**
- `KAGGLE_USERNAME` - Your Kaggle username
- `KAGGLE_KEY` - Your Kaggle API key (get from https://www.kaggle.com/settings)

### Environment File Setup

```bash
# Copy the example file
cp .env.example .env

# Edit with your preferred editor
nano .env
# or
vim .env
```

**Important Notes:**
- When running scripts locally, use `NEO4J_URI=bolt://localhost:7687`
- When running scripts in Docker, the URI is automatically set to `bolt://neo4j:7687`
- Never commit `.env` to version control (it's in `.gitignore`)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Educational project for CS 673 Scalable Databases - Fall 2025
