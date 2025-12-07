"""
Master Pipeline Script
Runs all scripts in the correct order
"""
import os
import sys
import subprocess

def run_script(script_name, description):
    """Run a Python script and handle errors"""
    print("\n" + "=" * 80)
    print(f"Running: {description}")
    print("=" * 80)
    
    script_path = os.path.join("scripts", script_name)
    
    if not os.path.exists(script_path):
        print(f"✗ Script not found: {script_path}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            capture_output=False
        )
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"✗ {description} failed: {e}")
        return False

def main():
    """Main execution function"""
    print("=" * 80)
    print("HEALTHCARE FRAUD DETECTION - COMPLETE PIPELINE")
    print("=" * 80)
    
    scripts = [
        ("01_data_cleansing.py", "Data Cleansing"),
        ("02_data_transformation.py", "Data Transformation"),
        ("03_neo4j_setup.py", "Neo4j Database Setup"),
        ("04_load_nodes.py", "Node Loading"),
        ("05_load_relationships.py", "Relationship Loading"),
        ("07_validation.py", "Data Validation"),
        ("06_queries.py", "Fraud Detection Queries"),
    ]
    
    failed_scripts = []
    
    for script_name, description in scripts:
        success = run_script(script_name, description)
        if not success:
            failed_scripts.append((script_name, description))
            response = input(f"\n{description} failed. Continue anyway? (y/N): ")
            if response.lower() != 'y':
                print("\nPipeline stopped by user.")
                sys.exit(1)
    
    print("\n" + "=" * 80)
    print("PIPELINE SUMMARY")
    print("=" * 80)
    
    if failed_scripts:
        print(f"\n⚠ {len(failed_scripts)} script(s) failed:")
        for script_name, description in failed_scripts:
            print(f"  - {description} ({script_name})")
    else:
        print("\n✓ All scripts completed successfully!")
    
    print("=" * 80)

if __name__ == "__main__":
    main()

