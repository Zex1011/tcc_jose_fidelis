#!/usr/bin/env python3
"""Prepare sample dataset for benchmarking.

Downloads a small set of images for testing detection and benchmarking.

Usage:
    python scripts/prepare_dataset.py --target datasets/sample

This downloads images from COCO val2017 dataset (publicly available).
Requires: ~100MB download, stores locally.
"""

import argparse
import sys
from pathlib import Path
from urllib.request import urlretrieve

import cv2
import numpy as np


# Sample images from COCO val2017 dataset (public, redistributable)
# These are representative real-world images with people
SAMPLE_URLS = [
    # Person in various contexts (COCO val2017 examples)
    "http://images.cocodataset.org/val2017/000000001268.jpg",
    "http://images.cocodataset.org/val2017/000000000139.jpg",
    "http://images.cocodataset.org/val2017/000000000632.jpg",
    "http://images.cocodataset.org/val2017/000000001000.jpg",
    "http://images.cocodataset.org/val2017/000000001581.jpg",
]


def prepare_dataset(target_dir: str, count: int = None) -> bool:
    """Download sample images for benchmarking.
    
    Returns True on success, False otherwise.
    """
    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📥 Preparing dataset in {target.resolve()}")
    
    urls_to_download = SAMPLE_URLS if count is None else SAMPLE_URLS[:count]
    
    for idx, url in enumerate(urls_to_download, 1):
        # Extract filename from URL
        filename = url.split('/')[-1]
        filepath = target / filename
        
        if filepath.exists():
            print(f"  ✓ {filename} already exists")
            continue
        
        print(f"  ⏳ Downloading ({idx}/{len(urls_to_download)}): {filename}...", end="", flush=True)
        try:
            urlretrieve(url, filepath)
            
            # Validate that file is readable image
            img = cv2.imread(str(filepath))
            if img is None:
                print(f" ❌ Downloaded file is not a valid image")
                filepath.unlink()
                return False
            
            h, w = img.shape[:2]
            print(f" ✓ ({w}x{h})")
        except Exception as e:
            print(f" ❌ Failed: {e}")
            if filepath.exists():
                filepath.unlink()
            return False
    
    # Validate dataset
    from pathlib import Path
    import subprocess
    result = subprocess.run(
        [sys.executable, "scripts/validate_dataset.py", "--path", str(target)],
        cwd=target.parent.parent,
        capture_output=False
    )
    
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description="Prepare sample dataset for FollowBot benchmarking"
    )
    parser.add_argument(
        "--target",
        type=str,
        default="datasets/sample",
        help="Target directory for dataset"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Number of images to download (default: all)"
    )
    
    args = parser.parse_args()
    
    if not prepare_dataset(args.target, args.count):
        print("\n❌ Dataset preparation failed")
        sys.exit(1)
    
    print("\n✓ Dataset ready for benchmarking!")
    print(f"  Run: python scripts/run_profile.py --config configs/profiles/dataset_ultralytics.toml --max-cycles 50")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
