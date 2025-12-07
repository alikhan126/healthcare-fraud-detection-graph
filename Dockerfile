# Python Application Dockerfile
# Sets up the Python environment with all prerequisites for the healthcare fraud detection project

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p data/raw data/processed data/stats \
    outputs/results outputs/screenshots \
    queries documentation

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Set entrypoint (this will create venv and install deps on container start)
ENTRYPOINT ["/entrypoint.sh"]

# Default command (can be overridden)
CMD ["python", "--version"]

