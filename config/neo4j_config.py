"""
Neo4j Database Configuration
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Neo4j Connection Settings
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "healthproject")

# Batch Processing Settings
BATCH_SIZE = 1000

# Timeout Settings (in seconds)
CONNECTION_TIMEOUT = 30
QUERY_TIMEOUT = 300

def get_neo4j_config():
    """Return Neo4j configuration dictionary"""
    return {
        "uri": NEO4J_URI,
        "user": NEO4J_USERNAME,
        "password": NEO4J_PASSWORD,
        "database": NEO4J_DATABASE,
        "batch_size": BATCH_SIZE,
        "connection_timeout": CONNECTION_TIMEOUT,
        "query_timeout": QUERY_TIMEOUT
    }

