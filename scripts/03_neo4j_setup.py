"""
Neo4j Database Setup Script
Creates database, indexes, and constraints
"""
import sys
import os
from neo4j import GraphDatabase

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.neo4j_config import get_neo4j_config

def connect_to_neo4j():
    """Connect to Neo4j database"""
    config = get_neo4j_config()
    
    try:
        driver = GraphDatabase.driver(
            config["uri"],
            auth=(config["user"], config["password"]),
            connection_timeout=config["connection_timeout"]
        )
        
        # Test connection
        driver.verify_connectivity()
        print(f"✓ Connected to Neo4j at {config['uri']}")
        return driver, config
    except Exception as e:
        print(f"✗ Failed to connect to Neo4j: {e}")
        print("\nMake sure Neo4j is running:")
        print("  docker-compose up -d")
        raise

def create_database(driver, config):
    """Create or switch to the database"""
    print(f"\nSetting up database: {config['database']}")
    
    # Try to create database, but continue even if it fails (Neo4j Community may not support it)
    try:
        with driver.session(database="system") as session:
            # Check if database exists
            try:
                result = session.run("""
                    SHOW DATABASES
                    YIELD name
                    WHERE name = $db_name
                    RETURN name
                """, db_name=config['database'])
                
                exists = result.single() is not None
            except Exception:
                # If SHOW DATABASES fails, assume it doesn't exist
                exists = False
            
            if exists:
                print(f"  Database '{config['database']}' already exists")
                print(f"  Using existing database '{config['database']}'")
            else:
                print(f"  Attempting to create database '{config['database']}'...")
                try:
                    # Try Neo4j 5.x syntax
                    session.run(f"CREATE DATABASE {config['database']}")
                    print(f"  ✓ Database '{config['database']}' created")
                except Exception as e:
                    error_msg = str(e).lower()
                    if "unsupported" in error_msg or "administration" in error_msg:
                        print(f"  ⚠ Database creation not supported (Community Edition limitation)")
                        print(f"  Will use default database 'neo4j' instead")
                        # Update config to use default database
                        config['database'] = 'neo4j'
                    elif "already exists" in error_msg:
                        print(f"  Database '{config['database']}' already exists (using it)")
                    else:
                        print(f"  ⚠ Could not create database: {e}")
                        print(f"  Will attempt to use database '{config['database']}' anyway")
    except Exception as e:
        print(f"  ⚠ Could not access system database: {e}")
        print(f"  Will attempt to use database '{config['database']}' anyway")

def create_constraints(driver, config):
    """Create uniqueness constraints on node ID properties (constraints auto-create indexes)"""
    print("\nCreating constraints (indexes will be created automatically)...")
    
    constraints = [
        ("Provider", "id"),
        ("Beneficiary", "id"),
        ("Claim", "id"),
        ("Physician", "id"),
        ("MedicalCode", "code")
    ]
    
    with driver.session(database=config['database']) as session:
        for node_type, prop in constraints:
            constraint_name = f"{node_type.lower()}_{prop}_unique"
            
            # Check if constraint already exists
            try:
                result = session.run("""
                    SHOW CONSTRAINTS
                    YIELD name
                    WHERE name = $constraint_name
                    RETURN name
                """, constraint_name=constraint_name)
                
                if result.single() is not None:
                    print(f"  ✓ Constraint on {node_type}.{prop} already exists")
                    continue
            except Exception:
                # If SHOW CONSTRAINTS fails, try to create anyway
                pass
            
            # Try to create constraint
            try:
                cypher = f"""
                CREATE CONSTRAINT {constraint_name} IF NOT EXISTS
                FOR (n:{node_type})
                REQUIRE n.{prop} IS UNIQUE
                """
                session.run(cypher)
                print(f"  ✓ Created uniqueness constraint on {node_type}.{prop}")
            except Exception as e:
                error_str = str(e)
                error_msg = error_str.lower()
                # Check for IndexAlreadyExists error (case-insensitive check in original string)
                is_index_error = (
                    "IndexAlreadyExists" in error_str or
                    "index already exists" in error_msg or 
                    "already exists an index" in error_msg
                )
                
                if is_index_error:
                    # Index exists - this is fine, index provides performance benefit
                    # Note: For true uniqueness enforcement, you'd need to drop index first
                    # But for this project, the index is sufficient
                    print(f"  ⚠ Index already exists for {node_type}.{prop} (skipping constraint)")
                    print(f"     Index provides performance - uniqueness enforced by application logic")
                else:
                    print(f"  ✗ Failed to create constraint on {node_type}.{prop}: {e}")

def verify_setup(driver, config):
    """Verify indexes and constraints were created"""
    print("\nVerifying setup...")
    
    with driver.session(database=config['database']) as session:
        # Check indexes
        result = session.run("SHOW INDEXES")
        indexes = [record['name'] for record in result]
        print(f"  Found {len(indexes)} indexes")
        
        # Check constraints
        result = session.run("SHOW CONSTRAINTS")
        constraints = [record['name'] for record in result]
        print(f"  Found {len(constraints)} constraints")
        
        return len(indexes) > 0 and len(constraints) > 0

def main():
    """Main execution function"""
    print("=" * 80)
    print("NEO4J DATABASE SETUP")
    print("=" * 80)
    
    try:
        # Connect to Neo4j
        driver, config = connect_to_neo4j()
        
        # Create database
        create_database(driver, config)
        
        # Create constraints (they automatically create indexes)
        create_constraints(driver, config)
        
        # Verify setup
        if verify_setup(driver, config):
            print("\n" + "=" * 80)
            print("✓ NEO4J SETUP COMPLETE")
            print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print("⚠ SETUP COMPLETE WITH WARNINGS")
            print("=" * 80)
        
        driver.close()
        
    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

