# Docker Setup Guide

This guide explains how to set up and use Docker for the Healthcare Fraud Detection project.

## Architecture

- **Neo4j Service**: Runs Neo4j database in Docker (recommended)
- **Python App Service**: Optional - can run scripts in Docker or locally

## Quick Start

### Option 1: Neo4j in Docker, Scripts Locally (Recommended)

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

### Option 2: Everything in Docker

Run both Neo4j and Python scripts in Docker containers.

```bash
# 1. Create .env file
cp .env.example .env
# Edit .env and set NEO4J_PASSWORD

# 2. Build and start all services
docker-compose -f docker-compose.yml -f docker-compose.app.yml build
docker-compose -f docker-compose.yml -f docker-compose.app.yml up -d

# 3. Run scripts in container
docker-compose -f docker-compose.yml -f docker-compose.app.yml run app python scripts/01_data_cleansing.py
```

## Dockerfile Details

The `Dockerfile` sets up:

- **Base Image**: Python 3.11-slim
- **System Dependencies**: gcc, g++, curl, wget, bash (for building Python packages)
- **Entrypoint Script**: `entrypoint.sh` automatically:
  - Creates a Python virtual environment (`/app/venv`)
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

## Building the Image

```bash
# Build the Python application image
docker build -t healthcare-fraud-app .

# Or use docker-compose
docker-compose build app
```

## Running Scripts in Docker

### Single Script

```bash
docker-compose -f docker-compose.yml -f docker-compose.app.yml run app python scripts/01_data_cleansing.py
```

### Complete Pipeline

```bash
# Run all scripts sequentially
docker-compose -f docker-compose.yml -f docker-compose.app.yml run app python run_pipeline.py
```

### Interactive Shell

```bash
# Get a shell in the container
docker-compose -f docker-compose.yml -f docker-compose.app.yml run app /bin/bash

# Then run scripts normally
python scripts/01_data_cleansing.py
```

## Volume Mounts

The `docker-compose.app.yml` mounts:

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

## Network Configuration

Both services are on the `fraud-detection-network`:

- **Neo4j**: Accessible at `bolt://neo4j:7687` from within Docker network
- **App**: Can connect to Neo4j using service name `neo4j`

When running scripts locally, use `bolt://localhost:7687` (port mapping).

## Environment Variables

The `.env` file is mounted into the container. See [ENV_SETUP.md](ENV_SETUP.md) for details.

**Important**: When running in Docker, the app connects to Neo4j using:
- `NEO4J_URI=bolt://neo4j:7687` (service name, not localhost)

This is automatically set in `docker-compose.app.yml`.

## Troubleshooting

### "Cannot connect to Neo4j"

**If running scripts in Docker:**
- Ensure Neo4j service is running: `docker-compose ps`
- Check network: `docker network ls`
- Verify `NEO4J_URI=bolt://neo4j:7687` in container

**If running scripts locally:**
- Ensure Neo4j is running: `docker-compose ps neo4j`
- Verify `NEO4J_URI=bolt://localhost:7687` in `.env`
- Check port mapping: `docker-compose port neo4j 7687`

### "Module not found" errors

```bash
# Rebuild the image (entrypoint will reinstall dependencies)
docker-compose -f docker-compose.yml -f docker-compose.app.yml build app

# Or manually reinstall in running container
docker-compose -f docker-compose.yml -f docker-compose.app.yml run app bash -c "source /app/venv/bin/activate && pip install -r requirements.txt"
```

**Note**: The entrypoint script automatically installs dependencies on every container start, so rebuilding should fix most issues.

### Data not persisting

- Check volume mounts in `docker-compose.app.yml`
- Verify paths exist on host: `ls -la data/`
- Check container volumes: `docker-compose run app ls -la /app/data`

## Benefits of Docker

✅ **Consistent Environment**: Same Python version and packages everywhere  
✅ **Isolation**: No conflicts with system Python  
✅ **Reproducibility**: Works the same on any machine  
✅ **Easy Cleanup**: Remove container, keep data  

## When to Use Docker vs Local

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

## Next Steps

1. ✅ Review [ENV_SETUP.md](ENV_SETUP.md) for .env configuration
2. ✅ Choose your setup (Docker or local)
3. ✅ Start Neo4j: `docker-compose up -d neo4j`
4. ✅ Run pipeline: `python run_pipeline.py` (local) or use Docker commands above

