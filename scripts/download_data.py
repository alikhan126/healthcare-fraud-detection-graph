"""
Kaggle Dataset Download Script
Downloads the healthcare fraud detection dataset from Kaggle
"""
import os
import sys
from kaggle.api.kaggle_api_extended import KaggleApi

# Define paths
RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")
os.makedirs(RAW_DATA_DIR, exist_ok=True)

def download_dataset():
    """Download dataset from Kaggle"""
    print("=" * 80)
    print("KAGGLE DATASET DOWNLOAD")
    print("=" * 80)
    
    # Initialize Kaggle API
    try:
        api = KaggleApi()
        api.authenticate()
        print("✓ Kaggle API authenticated")
    except Exception as e:
        print(f"✗ Failed to authenticate with Kaggle API: {e}")
        print("\nPlease ensure:")
        print("  1. Kaggle API credentials are set up (~/.kaggle/kaggle.json)")
        print("  2. KAGGLE_USERNAME and KAGGLE_KEY are set in .env file")
        return False
    
    # Dataset information
    dataset = "rohitrox/healthcare-provider-fraud-detection-analysis"
    
    print(f"\nDownloading dataset: {dataset}")
    print(f"Destination: {RAW_DATA_DIR}")
    
    try:
        # Download dataset files
        api.dataset_download_files(
            dataset,
            path=RAW_DATA_DIR,
            unzip=True
        )
        print("✓ Dataset downloaded and extracted successfully")
        
        # List downloaded files
        print("\nDownloaded files:")
        for file in os.listdir(RAW_DATA_DIR):
            if file.endswith('.csv'):
                filepath = os.path.join(RAW_DATA_DIR, file)
                size = os.path.getsize(filepath) / (1024 * 1024)  # Size in MB
                print(f"  {file} ({size:.2f} MB)")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to download dataset: {e}")
        return False

if __name__ == "__main__":
    success = download_dataset()
    sys.exit(0 if success else 1)

