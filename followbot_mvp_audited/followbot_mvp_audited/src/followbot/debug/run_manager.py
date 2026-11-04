"""Debug visual run management with timestamped history."""

from datetime import datetime
from pathlib import Path
import json


class DebugRunManager:
    """Manages timestamped debug run directories."""
    
    BASE_DIR = Path("logs/visual_debug")
    
    @classmethod
    def create_run_dir(cls, profile_name: str) -> Path:
        """Create timestamped directory for this debug run.
        
        Returns path like: logs/visual_debug/2026-08-24_17-45-30_webcam_ultralytics_debug
        """
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_name = f"{now}_{profile_name}"
        run_dir = cls.BASE_DIR / run_name
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir
    
    @classmethod
    def list_runs(cls, limit: int = 20) -> list[dict]:
        """List all debug runs (most recent first)."""
        if not cls.BASE_DIR.exists():
            return []
        
        runs = []
        for run_dir in sorted(cls.BASE_DIR.iterdir(), reverse=True):
            if not run_dir.is_dir():
                continue
            
            # Try to load metadata
            metadata_file = run_dir / "_run_metadata.json"
            if metadata_file.exists():
                try:
                    with metadata_file.open() as f:
                        metadata = json.load(f)
                    runs.append({
                        "dir": str(run_dir),
                        "name": run_dir.name,
                        **metadata
                    })
                except:
                    pass
            else:
                # Fallback: infer from directory name
                runs.append({
                    "dir": str(run_dir),
                    "name": run_dir.name,
                    "cycle_count": len(list(run_dir.glob("cycle_*.ppm")))
                })
            
            if len(runs) >= limit:
                break
        
        return runs
    
    @classmethod
    def write_run_metadata(cls, run_dir: Path, profile: str, config: dict, cycles: int) -> None:
        """Write metadata about this debug run for cataloging."""
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "profile": profile,
            "config": config,
            "cycle_count": cycles,
        }
        metadata_file = run_dir / "_run_metadata.json"
        with metadata_file.open("w") as f:
            json.dump(metadata, f, indent=2)
