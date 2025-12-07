"""
Export Query Results to JSON
Exports all query results to JSON format for additional documentation
"""
import sys
import os
import json
import pandas as pd
from neo4j import GraphDatabase

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.neo4j_config import get_neo4j_config

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "results")
JSON_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "results", "json")
os.makedirs(JSON_DIR, exist_ok=True)

def export_csv_to_json(csv_file, json_file):
    """Convert CSV file to JSON format"""
    try:
        df = pd.read_csv(csv_file)
        # Convert to list of dictionaries
        data = df.to_dict('records')
        
        # Create structured JSON
        result = {
            "query_name": os.path.basename(csv_file).replace('.csv', ''),
            "row_count": len(data),
            "columns": list(df.columns),
            "data": data
        }
        
        with open(json_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"  ✓ Exported {len(data)} rows to {json_file}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to export {csv_file}: {e}")
        return False

def main():
    """Main execution function"""
    print("=" * 80)
    print("EXPORTING QUERY RESULTS TO JSON")
    print("=" * 80)
    
    # Find all CSV files in results directory
    csv_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.csv')]
    
    if not csv_files:
        print("No CSV files found in outputs/results/")
        print("Run scripts/06_queries.py first to generate query results.")
        return
    
    print(f"\nFound {len(csv_files)} CSV files to convert\n")
    
    success_count = 0
    for csv_file in sorted(csv_files):
        csv_path = os.path.join(OUTPUT_DIR, csv_file)
        json_file = csv_file.replace('.csv', '.json')
        json_path = os.path.join(JSON_DIR, json_file)
        
        print(f"Converting: {csv_file}")
        if export_csv_to_json(csv_path, json_path):
            success_count += 1
    
    print("\n" + "=" * 80)
    print(f"EXPORT COMPLETE: {success_count}/{len(csv_files)} files converted")
    print("=" * 80)
    print(f"\nJSON files saved to: {JSON_DIR}")

if __name__ == "__main__":
    main()

