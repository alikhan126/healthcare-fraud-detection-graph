#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Healthcare Fraud Detection - Container Entrypoint ===${NC}"

# Virtual environment path
VENV_PATH="/app/.venv"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv "$VENV_PATH"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip --quiet

# Install/update requirements
if [ -f "/app/requirements.txt" ]; then
    echo -e "${YELLOW}Installing/updating Python dependencies from requirements.txt...${NC}"
    pip install --no-cache-dir -r /app/requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠ requirements.txt not found, skipping dependency installation${NC}"
fi

# Set Python path
export PYTHONPATH=/app
export PYTHONUNBUFFERED=1

# Print Python and pip versions
echo -e "${GREEN}Python version: $(python --version)${NC}"
echo -e "${GREEN}Pip version: $(pip --version)${NC}"

# Execute the command passed to the container
echo -e "${GREEN}=== Ready to execute command ===${NC}"
echo ""

# If no command provided, default to bash
if [ $# -eq 0 ]; then
    exec /bin/bash
else
    exec "$@"
fi

