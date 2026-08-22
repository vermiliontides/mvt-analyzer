#!/usr/bin/env python3
"""
Verichron Epoch - iLEAPP Extraction Bridge
Wraps iLEAPP execution with pre-flight validation and robust error handling.
"""

import sys
import subprocess
from pathlib import Path

def run_ileapp_extraction(artifact_path: str, output_dir: str) -> dict:
    """
    Validates target backup structure and executes iLEAPP extraction safely.
    """
    target_path = Path(artifact_path).resolve()
    out_path = Path(output_dir).resolve()

    if not target_path.exists():
        print(f"[-] Target forensic artifact not found: {target_path}", file=sys.stderr)
        return {"status": "error", "error": "Target path does not exist."}

    # --- Pre-flight Validation: Fail fast on invalid input ---
    # Check for iOS backup or filesystem markers (Manifest.db, Info.plist, etc.)
    has_manifest = list(target_path.glob("**/Manifest.db")) or (target_path / "Manifest.db").exists()
    has_plist = list(target_path.glob("**/Info.plist")) or (target_path / "Info.plist").exists()

    if not has_manifest and not has_plist:
        print(f"[-] Validation Error: '{target_path.name}' is not a valid iOS backup or extraction directory.", file=sys.stderr)
        print(f"[-] Missing required forensic markers (Manifest.db or Info.plist). Check your input path.", file=sys.stderr)
        return {
            "status": "error",
            "output_directory": str(out_path),
            "error": "Invalid iOS backup structure: missing Manifest.db or Info.plist."
        }
    # ---------------------------------------------------------

    print(f"[*] Executing iLEAPP extraction on: {target_path}")
    print(f"[*] Output destination: {out_path}")

    # Ensure output directory exists
    out_path.mkdir(parents=True, exist_ok=True)

    try:
        # Construct iLEAPP command invocation 
        # (Assuming iLEAPP is installed in the environment as 'ileapp' or callable via python module)
        cmd = [
            sys.executable, "-m", "ileapp",
            "-i", str(target_path),
            "-o", str(out_path),
            "-p", "none" # Disable GUI prompt/popups during automated runs
        ]

        # Execute iLEAPP process and stream/capture output
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )

        print("[+] iLEAPP execution completed successfully.")
        return {
            "status": "success",
            "output_directory": str(out_path),
            "stdout": result.stdout
        }

    except subprocess.CalledProcessError as e:
        print(f"[-] iLEAPP subprocess failed with exit code {e.returncode}:", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        return {
            "status": "error",
            "output_directory": str(out_path),
            "error": e.stderr
        }
    except Exception as e:
        print(f"[-] Unexpected error during iLEAPP execution: {e}", file=sys.stderr)
        return {
            "status": "error",
            "output_directory": str(out_path),
            "error": str(e)
        }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python bridge.py <path_to_backup> <output_dir>")
        sys.exit(1)
    
    res = run_ileapp_extraction(sys.argv[1], sys.argv[2])
    sys.exit(0 if res["status"] == "success" else 1)