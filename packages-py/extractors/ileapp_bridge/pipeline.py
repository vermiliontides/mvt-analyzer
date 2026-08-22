#!/usr/bin/env python3
"""
Verichron Epoch - iLEAPP End-to-End Pipeline (Resilient & Restart-Safe)
"""

import argparse
import sys
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

from extractors.ileapp_bridge.bridge import run_ileapp_extraction
from extractors.ileapp_bridge.normalizer import parse_ileapp_outputs
from db.db_writer import insert_records, init_db

def run_pipeline(artifact_path: str, output_dir: str, db_path: str = None, clean_staging: bool = False) -> bool:
    print("==================================================")
    print("🚀 Verichron Epoch: Resilient Ingestion Pipeline")
    print("==================================================")

    out_path = Path(output_dir)
    if clean_staging and out_path.exists():
        print(f"[*] Cleaning previous staging directory: {out_path}")
        shutil.rmtree(out_path)

    # Phase 1: Extraction
    print("\n[Phase 1/3] Running iLEAPP Extraction...")
    extraction_res = run_ileapp_extraction(artifact_path, output_dir)
    
    if extraction_res.get("status") != "success":
        print("[-] Pipeline halted: Extraction phase failed.", file=sys.stderr)
        return False

    # Phase 2: Normalization
    print("\n[Phase 2/3] Normalizing Extraction Reports...")
    try:
        records = parse_ileapp_outputs(output_dir)
        if not records:
            print("[!] Warning: Extraction completed, but no records were found.")
            return True
    except Exception as e:
        print(f"[-] Pipeline halted: Normalization error: {e}", file=sys.stderr)
        return False

    # Phase 3: Database Persistence (Idempotent / Restart-Safe)
    print("\n[Phase 3/3] Persisting Records (Idempotent Mode)...")
    try:
        target_db = db_path if db_path else str(ROOT_DIR / "epoch_forensics.db")
        init_db(target_db)
        insert_records(records, db_path=target_db)
    except Exception as e:
        print(f"[-] Pipeline halted: Persistence error: {e}", file=sys.stderr)
        return False

    print("\n==================================================")
    print("[+] Pipeline Execution Complete Successfully.")
    print("==================================================")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verichron Resilient Ingestion Pipeline")
    parser.add_argument("--input", "-i", required=True, help="Path to target forensic artifact")
    parser.add_argument("--output", "-o", default="./ileapp_raw_output", help="Staging directory")
    parser.add_argument("--db", default=None, help="Optional custom database path")
    parser.add_argument("--clean", action="store_true", help="Clean staging directory before running")

    args = parser.parse_args()
    success = run_pipeline(args.input, args.output, args.db, args.clean)
    
    sys.exit(0 if success else 1)