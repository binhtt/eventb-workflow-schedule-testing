#!/usr/bin/env python3
"""Reproduce the study in a fresh workspace, preserving the recorded results."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run_step(workspace, log, label, arguments):
    print(f"Running {label}", flush=True)
    log.write(f"\n[{label}]\n")
    log.flush()
    subprocess.run(
        [sys.executable, *arguments],
        cwd=workspace,
        stdout=log,
        stderr=subprocess.STDOUT,
        check=True,
    )


def prepare_workspace(destination):
    if destination.exists():
        raise FileExistsError(f"Output directory already exists: {destination}")
    destination.mkdir(parents=True)
    workspace = destination / "workspace"
    workspace.mkdir()
    for name in ("code", "model", "proof"):
        shutil.copytree(
            ROOT / name,
            workspace / name,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    for name in ("plan.json", "frozen_generator.json"):
        shutil.copy2(ROOT / name, workspace / name)
    (workspace / "results").mkdir()
    return workspace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode", choices=("smoke", "full", "analysis"), default="smoke"
    )
    parser.add_argument("--output", type=Path, help="A new output directory")
    arguments = parser.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = (
        arguments.output or ROOT / "outputs" / f"{arguments.mode}-{stamp}"
    ).resolve()

    # Fail before creating a run if the source artifact has been changed.
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_artifact.py")],
        cwd=ROOT,
        check=True,
    )
    try:
        workspace = prepare_workspace(destination)
    except FileExistsError as error:
        parser.error(str(error))

    status = {"mode": arguments.mode, "status": "running"}
    status_path = destination / "run.json"
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")

    try:
        with (destination / "run.log").open("w", encoding="utf-8") as log:
            if arguments.mode == "analysis":
                shutil.copytree(ROOT / "results", workspace / "results", dirs_exist_ok=True)
                run_step(workspace, log, "analysis of recorded trials", ["code/analyse.py"])
            else:
                if arguments.mode == "smoke":
                    plan_path = workspace / "plan.json"
                    plan = json.loads(plan_path.read_text(encoding="utf-8"))
                    plan["configurations"] = [[2, 1], [4, 2]]
                    plan["seeds"] = 2
                    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

                run_step(workspace, log, "unit checks", ["-m", "unittest", "discover", "-v", "-s", "code", "-p", "checks.py"])
                run_step(workspace, log, "proof/source and schedule bridge", ["code/verify_bridge.py"])

                if arguments.mode == "full":
                    run_step(workspace, log, "complete finite conformance", ["code/validate_model.py"])
                else:
                    code = (
                        "import sys; sys.path.insert(0, 'code'); from validate_model import explore; "
                        "print(explore(1, 1)); print(explore(2, 1))"
                    )
                    run_step(workspace, log, "small finite conformance", ["-c", code])

                run_step(
                    workspace,
                    log,
                    "paired scheduling experiment",
                    ["code/experiment.py", "--proved-model", "proof/SharedWorkflow/Resource.bum"],
                )
                if arguments.mode == "full":
                    run_step(workspace, log, "statistical analysis", ["code/analyse.py"])
                    run_step(workspace, log, "standalone timing", ["code/benchmark_time.py"])

        if arguments.mode in ("analysis", "full"):
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "verify_artifact.py"),
                    "--generated",
                    str(workspace / "results"),
                    "--analysis-only" if arguments.mode == "analysis" else "--full",
                ],
                cwd=ROOT,
                check=True,
            )
        status["status"] = "passed"
    except Exception:
        status["status"] = "failed"
        raise
    finally:
        status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")

    print(f"Run passed. Generated files: {workspace / 'results'}")
    print(f"Full log: {destination / 'run.log'}")


if __name__ == "__main__":
    main()
