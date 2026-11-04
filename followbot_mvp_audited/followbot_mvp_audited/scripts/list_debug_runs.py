#!/usr/bin/env python3
"""List and explore debug visual runs.

Usage:
    python scripts/list_debug_runs.py              # Show last 20 runs
    python scripts/list_debug_runs.py --limit 50   # Show last 50 runs
    python scripts/list_debug_runs.py --open <dir> # Open specific run directory
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Add project root to path so we can import src
sys.path.insert(0, str(Path(__file__).parent.parent))


def list_runs(limit: int = 20):
    """List all debug runs (most recent first)."""
    from src.followbot.debug import DebugRunManager
    
    runs = DebugRunManager.list_runs(limit=limit)
    
    if not runs:
        print("No debug runs found.")
        return
    
    print(f"\n📁 Last {len(runs)} debug runs (most recent first):\n")
    print(f"{'#':<4} {'Run Name':<50} {'Cycles':<10} {'Profile':<30}")
    print("─" * 95)
    
    for idx, run in enumerate(runs, 1):
        cycles = run.get("cycle_count", "?")
        profile = run.get("profile", "?")
        name = run["name"]
        print(f"{idx:<4} {name:<50} {cycles:<10} {profile:<30}")
    
    print(f"\nTo open a run:  python scripts/list_debug_runs.py --open <run_dir>")
    print(f"Or manually:    ls {DebugRunManager.BASE_DIR}/<run_name>/")


def open_run(run_dir: str):
    """Open run directory in file manager or terminal."""
    path = Path(run_dir)
    
    if not path.exists():
        print(f"❌ Directory not found: {path}")
        return
    
    if not path.is_dir():
        print(f"❌ Not a directory: {path}")
        return
    
    # List contents
    ppm_files = sorted(path.glob("cycle_*.ppm"))
    json_files = sorted(path.glob("cycle_*.json"))
    
    print(f"\n📁 Run directory: {path.resolve()}")
    print(f"✓ {len(ppm_files)} images (PPM)")
    print(f"✓ {len(json_files)} metadata files (JSON)")
    
    if ppm_files:
        print(f"\nFirst image: {ppm_files[0].name}")
        print(f"Last image:  {ppm_files[-1].name}")
    
    # Try to open in file manager
    try:
        subprocess.run(["xdg-open", str(path)], check=False, timeout=2)
        print(f"\n✓ Opened in file manager")
    except:
        print(f"\nTo view images, open: {path}")
    
    # Show sample metadata
    if json_files and len(json_files) > 0:
        try:
            with json_files[0].open() as f:
                metadata = json.load(f)
            print(f"\nSample metadata ({json_files[0].name}):")
            print(f"  Cycle: {metadata.get('cycle')}")
            print(f"  Detections: {len(metadata.get('detections', []))}")
            print(f"  Target: {metadata.get('target') is not None}")
            print(f"  Total time: {metadata.get('timings_ms', {}).get('total_ms')}ms")
        except:
            pass


def main():
    parser = argparse.ArgumentParser(
        description="List and explore debug visual runs"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of runs to list"
    )
    parser.add_argument(
        "--open",
        type=str,
        default=None,
        help="Open specific run directory"
    )
    
    args = parser.parse_args()
    
    if args.open:
        open_run(args.open)
    else:
        list_runs(limit=args.limit)


if __name__ == "__main__":
    main()
