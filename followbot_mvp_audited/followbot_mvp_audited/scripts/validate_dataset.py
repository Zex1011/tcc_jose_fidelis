#!/usr/bin/env python3
"""Validate and prepare datasets for benchmark testing.

Checks:
- Folder exists and contains images
- All images readable and have same format
- Images are loadable by OpenCV
- Dataset size and statistics

Usage:
    python scripts/validate_dataset.py --path datasets/sample
"""

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np


def validate_dataset(dataset_path: str) -> bool:
    """Validate dataset folder for FollowBot benchmarking.
    
    Returns True if valid, False otherwise.
    """
    path = Path(dataset_path)
    
    print(f"\n📁 Validating dataset: {path.resolve()}")
    
    # Check existence
    if not path.exists():
        print(f"❌ Path does not exist: {path}")
        return False
    
    if not path.is_dir():
        print(f"❌ Path is not a directory: {path}")
        return False
    
    # Find images
    image_extensions = {'.png', '.jpg', '.jpeg'}
    image_files = sorted([
        f for f in path.iterdir()
        if f.suffix.lower() in image_extensions
    ])
    
    if not image_files:
        print(f"❌ No images found in {path}")
        return False
    
    print(f"✓ Found {len(image_files)} image(s)")
    
    # Validate each image
    failed = []
    shapes = []
    
    for img_file in image_files:
        img = cv2.imread(str(img_file))
        if img is None:
            print(f"  ❌ Failed to read: {img_file.name}")
            failed.append(img_file.name)
        else:
            h, w = img.shape[:2]
            shapes.append((w, h))
            print(f"  ✓ {img_file.name:30s} {w:4d}x{h:4d}")
    
    if failed:
        print(f"\n❌ {len(failed)} image(s) failed to load")
        return False
    
    # Check consistency
    if len(set(shapes)) > 1:
        print(f"\n⚠️  Images have different resolutions:")
        for (w, h), img_file in zip(shapes, image_files):
            print(f"   {img_file.name:30s} {w:4d}x{h:4d}")
        print("   (Dataset backend will resize to target resolution, but prefer consistency)")
    else:
        w, h = shapes[0]
        print(f"\n✓ All images consistent: {w}x{h}")
    
    # Summary
    total_size = sum(f.stat().st_size for f in image_files)
    print(f"\n✓ Total dataset size: {total_size / (1024*1024):.1f} MB")
    print(f"✓ Dataset valid and ready for benchmarking")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Validate dataset for FollowBot benchmarking"
    )
    parser.add_argument(
        "--path",
        type=str,
        default="datasets/sample",
        help="Path to dataset folder"
    )
    
    args = parser.parse_args()
    
    if not validate_dataset(args.path):
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
