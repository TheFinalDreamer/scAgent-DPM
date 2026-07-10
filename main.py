#!/usr/bin/env python
"""scAgent-DPM: single-cell Agent for Drug Perturbation Mechanism discovery.

Usage:
    python main.py check-env
    python main.py init-project
    python main.py run-demo --config configs/demo.yaml
    python main.py run-pipeline --config configs/default.yaml
    python main.py collect-results --input results/ --output reports/
    python main.py generate-report --run-dir results/demo/
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def cmd_check_env(args):
    """Check Python environment and dependencies."""
    print("=" * 60)
    print("  scAgent-DPM Environment Check")
    print("=" * 60)

    from src.utils.system import (
        check_gpu, check_disk_space, check_conda,
        check_python_packages, get_python_version, get_platform,
    )

    print(f"\nPython: {get_python_version()}")
    print(f"Platform: {get_platform()}")

    print("\n--- GPU ---")
    for k, v in check_gpu().items():
        print(f"  {k}: {v}")

    print("\n--- Disk ---")
    for k, v in check_disk_space(PROJECT_ROOT).items():
        print(f"  {k}: {v}")

    conda = check_conda()
    print(f"\nConda: {conda or 'not found'}")

    print("\n--- Required Packages ---")
    required = [
        "numpy", "scipy", "pandas", "anndata", "scanpy",
        "sklearn", "matplotlib", "yaml", "h5py",
    ]
    for pkg, ok in check_python_packages(required).items():
        status = "OK" if ok else "MISSING"
        print(f"  {pkg}: {status}")

    optional = ["torch", "celltypist", "gseapy", "scrublet"]
    print("\n--- Optional Packages ---")
    for pkg, ok in check_python_packages(optional).items():
        status = "OK" if ok else "not installed"
        print(f"  {pkg}: {status}")

    print("\nEnvironment check complete.")
    return 0


def cmd_init_project(args):
    """Initialize project structure and validate configs."""
    print("Initializing scAgent-DPM project...")

    required_dirs = [
        "configs", "src", "scripts", "tests", "docs",
        "experiments", "results", "reports", "logs", "tmp",
        "manuscript_assets/figures", "manuscript_assets/tables", "manuscript_assets/captions",
    ]

    for d in required_dirs:
        path = PROJECT_ROOT / d
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {d}")
        else:
            print(f"  Exists: {d}")

    # Validate configs
    import yaml
    config_dir = PROJECT_ROOT / "configs"
    for cfg_file in config_dir.glob("*.yaml"):
        try:
            with open(cfg_file) as f:
                yaml.safe_load(f)
            print(f"  Config OK: {cfg_file.name}")
        except Exception as e:
            print(f"  Config ERROR: {cfg_file.name} - {e}")

    print("Project initialization complete.")
    return 0


def cmd_run_demo(args):
    """Run demo pipeline with synthetic data."""
    from src.utils.config import load_config
    from src.utils.logger import PipelineLogger
    from src.agent.executor import PipelineExecutor

    config_path = args.config or "configs/demo.yaml"
    print(f"Loading config: {config_path}")
    config = load_config(config_path).to_dict()

    output_dir = config.get("output_dir", "results/demo")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"{output_dir}/{timestamp}"

    plog = PipelineLogger(log_dir="logs", run_name=f"demo_{timestamp}")
    plog.log_section("scAgent-DPM Demo Pipeline")
    plog.log_config(config)

    executor = PipelineExecutor(config, output_dir)
    result = executor.run()

    print(f"\nDemo pipeline complete.")
    print(f"  Output: {output_dir}")
    print(f"  Manifest: {result.get('manifest_path')}")
    print(f"  Summary: {result.get('summary')}")
    return 0


def cmd_run_pipeline(args):
    """Run full pipeline."""
    from src.utils.config import load_config
    from src.utils.logger import PipelineLogger
    from src.agent.executor import PipelineExecutor

    config_path = args.config or "configs/default.yaml"
    print(f"Loading config: {config_path}")
    config = load_config(config_path).to_dict()

    if not config.get("input_path"):
        print("WARNING: No input_path in config. Synthetic data will be used.")
        print("Set input_path in the config file to run on real data.")

    output_dir = config.get("output_dir", "results/pipeline_run")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"{output_dir}/{timestamp}"

    plog = PipelineLogger(log_dir="logs", run_name=f"pipeline_{timestamp}")
    plog.log_section("scAgent-DPM Full Pipeline")
    plog.log_config(config)

    executor = PipelineExecutor(config, output_dir)
    result = executor.run()

    print(f"\nPipeline complete.")
    print(f"  Output: {output_dir}")
    print(f"  Manifest: {result.get('manifest_path')}")
    print(f"  Summary: {result.get('summary')}")
    return 0


def cmd_collect_results(args):
    """Collect results from multiple run directories into a summary."""
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifests = list(input_dir.rglob("run_manifest.json"))
    if not manifests:
        print("No run manifests found.")
        return 1

    collection = {
        "collected_at": datetime.now().isoformat(),
        "n_runs": len(manifests),
        "runs": [],
    }

    for mf_path in manifests:
        with open(mf_path) as f:
            manifest = json.load(f)
        collection["runs"].append({
            "path": str(mf_path.parent),
            "run_name": manifest.get("run_name"),
            "summary": manifest.get("status_summary"),
            "start_time": manifest.get("start_time"),
        })

    output_path = output_dir / "collected_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(collection, f, indent=2, ensure_ascii=False, default=str)

    print(f"Collected {len(manifests)} run manifests -> {output_path}")
    for run in collection["runs"]:
        print(f"  {run['run_name']}: {run['summary']}")
    return 0


def cmd_generate_report(args):
    """Generate final report from a run directory."""
    from src.reporting.markdown_report import generate_markdown_report
    from src.reporting.html_report import generate_html_report

    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        print(f"Error: run directory not found: {run_dir}")
        return 1

    # Load results from the run directory
    results = {}
    for json_file in run_dir.glob("*.json"):
        try:
            with open(json_file) as f:
                results[json_file.stem] = json.load(f)
        except Exception:
            pass

    md_path = generate_markdown_report(results, str(run_dir))
    html_path = generate_html_report(results, str(run_dir))

    print(f"Reports generated:")
    print(f"  Markdown: {md_path}")
    print(f"  HTML:     {html_path}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="scAgent-DPM: single-cell Agent for Drug Perturbation Mechanism discovery",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    p_check = subparsers.add_parser("check-env", help="Check environment and dependencies")
    p_check.set_defaults(func=cmd_check_env)

    p_init = subparsers.add_parser("init-project", help="Initialize project structure")
    p_init.set_defaults(func=cmd_init_project)

    p_demo = subparsers.add_parser("run-demo", help="Run demo pipeline")
    p_demo.add_argument("--config", default="configs/demo.yaml")
    p_demo.set_defaults(func=cmd_run_demo)

    p_run = subparsers.add_parser("run-pipeline", help="Run full pipeline")
    p_run.add_argument("--config", default="configs/default.yaml")
    p_run.set_defaults(func=cmd_run_pipeline)

    p_collect = subparsers.add_parser("collect-results", help="Collect results from runs")
    p_collect.add_argument("--input", default="results/")
    p_collect.add_argument("--output", default="reports/")
    p_collect.set_defaults(func=cmd_collect_results)

    p_report = subparsers.add_parser("generate-report", help="Generate report from run dir")
    p_report.add_argument("--run-dir", required=True)
    p_report.set_defaults(func=cmd_generate_report)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
