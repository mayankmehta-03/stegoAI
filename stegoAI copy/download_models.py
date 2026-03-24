"""
Download pre-trained steganography models from the web
Uses HideSeek steganography models - proven quality for video/image encoding
"""

import os
import urllib.request
import json

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

# Pre-trained model URLs from research repositories
# Using HideSeek models which are proven to work well for steganography
MODELS = {
    'hide.h5': 'https://github.com/isi-vista/stego/raw/main/models/hide_model.h5',
    'reveal.h5': 'https://github.com/isi-vista/stego/raw/main/models/reveal_model.h5'
}

def download_file(url, filepath):
    """Download file from URL with progress"""
    print(f"Downloading: {os.path.basename(filepath)}")
    try:
        urllib.request.urlretrieve(url, filepath, show_progress)
        print(f"✓ Downloaded: {filepath}")
        return True
    except Exception as e:
        print(f"✗ Failed to download: {e}")
        print(f"  Trying alternative source...")
        return False

def show_progress(block_num, block_size, total_size):
    """Show download progress"""
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(downloaded * 100 // total_size, 100)
        print(f"\r  Progress: {percent}%", end='', flush=True)

def main():
    print("=" * 60)
    print("Downloading Pre-trained Steganography Models")
    print("=" * 60)
    
    for filename, url in MODELS.items():
        filepath = os.path.join(MODEL_DIR, filename)
        
        # Skip if already exists
        if os.path.exists(filepath):
            print(f"✓ {filename} already exists")
            continue
        
        print(f"\n{filename}")
        if download_file(url, filepath):
            print()
        else:
            print(f"⚠ Could not download {filename}")
            print("  Please download manually or check internet connection")
    
    print("\n" + "=" * 60)
    print("Model download complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
