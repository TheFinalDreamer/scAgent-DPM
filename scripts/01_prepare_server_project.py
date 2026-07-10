#!/usr/bin/env python
"""Prepare server project directory for scAgent-DPM.

Usage:
    python scripts/01_prepare_server_project.py --server-path /data/sc/scAgent_DPM
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description="Prepare scAgent-DPM server project")
    parser.add_argument("--server-path", default="/data/sc/scAgent_DPM",
                       help="Server project directory")
    parser.add_argument("--server-host", default=None,
                       help="SSH host for remote server (optional)")
    args = parser.parse_args()

    server_path = args.server_path
    print(f"Server path: {server_path}")
    print(f"Project root: {PROJECT_ROOT}")

    # Check local project
    required_files = ["main.py", "configs/demo.yaml", "src/__init__.py"]
    for f in required_files:
        if not (PROJECT_ROOT / f).exists():
            print(f"ERROR: Missing required file: {f}")
            return 1
    print("Local project structure: OK")

    # Generate server config
    server_config = {
        "server_path": server_path,
        "project_root": str(PROJECT_ROOT),
        "generated_at": datetime.now().isoformat(),
        "sync_commands": [],
        "setup_commands": [],
    }

    # Build commands
    server_config["sync_commands"].append(
        f"rsync -avz --exclude '.git' --exclude '__pycache__' --exclude '*.pyc' "
        f"--exclude '.idea' --exclude 'tmp/' --exclude 'logs/' "
        f"{PROJECT_ROOT}/ {server_path}/"
    )
    server_config["setup_commands"].extend([
        f"cd {server_path}",
        "conda env create -f environment.yml -n scagent-dpm 2>/dev/null || "
        "conda env update -f environment.yml -n scagent-dpm",
        "conda activate scagent-dpm",
        "pip install -r requirements.txt",
        "python main.py check-env",
    ])

    # Write preparation script
    script_path = PROJECT_ROOT / "scripts" / "generated_server_setup.sh"
    with open(script_path, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("# Auto-generated server setup script for scAgent-DPM\n")
        f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
        f.write(f"SERVER_PATH={server_path}\n\n")
        f.write("echo 'Creating server project directory...'\n")
        f.write(f"mkdir -p $SERVER_PATH\n\n")
        f.write("echo 'Syncing code...'\n")
        f.write(f"rsync -avz --exclude '.git' --exclude '__pycache__' --exclude '*.pyc' "
                f"--exclude '.idea' --exclude 'tmp/' --exclude 'logs/' "
                f"{PROJECT_ROOT}/ $SERVER_PATH/\n\n")
        f.write("echo 'Setting up conda environment...'\n")
        f.write("cd $SERVER_PATH\n")
        f.write("conda env create -f environment.yml -n scagent-dpm 2>/dev/null || "
                "conda env update -f environment.yml -n scagent-dpm\n")
        f.write("conda activate scagent-dpm\n")
        f.write("pip install -r requirements.txt\n\n")
        f.write("echo 'Running environment check...'\n")
        f.write("python main.py check-env\n\n")
        f.write("echo 'Server preparation complete.'\n")

    print(f"\nServer preparation script generated: {script_path}")
    print(f"\nServer config:")
    print(json.dumps(server_config, indent=2))

    print(f"\nTo deploy to server:")
    if args.server_host:
        print(f"  scp {script_path} {args.server_host}:~/")
        print(f"  ssh {args.server_host} 'bash ~/generated_server_setup.sh'")
    else:
        print(f"  1. Copy {script_path} to server")
        print(f"  2. Run: bash generated_server_setup.sh")
    print(f"\nManual setup:")
    for cmd in server_config["setup_commands"]:
        print(f"  {cmd}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
