"""
Reports Generation Script
Runs only the reporting scripts (statistics and aggregations)
Use this if you've already run the main pipeline
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
    print("HEALTHCARE FRAUD DETECTION - REPORTS GENERATION")
    print("=" * 80)
    print("This script generates statistics and aggregation reports.")
    print("Make sure Neo4j is running and data is loaded.\n")
    
    scripts = [
        ("08_generate_statistics.py", "Generate Statistics Report"),
        ("09_generate_aggregation_results.py", "Generate Aggregation Results"),
    ]
    
    failed_scripts = []
    
    for script_name, description in scripts:
        success = run_script(script_name, description)
        if not success:
            failed_scripts.append((script_name, description))
            response = input(f"\n{description} failed. Continue anyway? (y/N): ")
            if response.lower() != 'y':
                print("\nReports generation stopped by user.")
                sys.exit(1)
    
    print("\n" + "=" * 80)
    print("REPORTS GENERATION SUMMARY")
    print("=" * 80)
    
    if failed_scripts:
        print(f"\n⚠ {len(failed_scripts)} script(s) failed:")
        for script_name, description in failed_scripts:
            print(f"  - {description} ({script_name})")
    else:
        print("\n✓ All reports generated successfully!")
        print("\nGenerated files:")
        print("  - data/stats/node_relationship_statistics.txt")
        print("  - outputs/results/aggregation_*.csv")
    
    print("=" * 80)

if __name__ == "__main__":
    main()

