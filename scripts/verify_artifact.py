#!/usr/bin/env python3
"""Audit source checksums, native proof artifacts and recorded study counts."""
import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
from analyse import eligible, found
from eventb import Model, NS
from proof_bridge import assert_same_core, load_proved


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def check_checksums():
    checksum_path = ROOT / "SOURCE_SHA256.json"
    if not checksum_path.exists():
        raise AssertionError("Missing SOURCE_SHA256.json")
    for name, expected in json.loads(checksum_path.read_text(encoding="utf-8")).items():
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT), f"Invalid checksum path: {name}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name

    frozen = json.loads((ROOT / "frozen_generator.json").read_text(encoding="utf-8"))
    for name, expected in frozen.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name


def check_proofs():
    folder = ROOT / "proof" / "SharedWorkflow"
    statuses = list(ET.parse(folder / "Resource.bps").getroot())
    sequents = ET.parse(folder / "Resource.bpo").getroot().findall(NS + "poSequent")
    proof_trees = ET.parse(folder / "Resource.bpr").getroot().findall(NS + "prProof")
    assert len(statuses) == len(sequents) == len(proof_trees) == 24
    names = {item.attrib["name"] for item in statuses}
    assert names == {item.attrib["name"] for item in sequents}
    assert names == {item.attrib["name"] for item in proof_trees}
    assert Counter(name.rsplit("/", 1)[-1] for name in names) == {
        "INV": 15, "THM": 6, "WD": 3
    }
    for item in statuses:
        assert int(item.attrib[NS + "confidence"]) > 0
        assert item.attrib[NS + "psManual"] == "false"
    for item in proof_trees:
        assert int(item.attrib[NS + "confidence"]) > 0
    for filename in ("Resource.bcm", "Pool.bcc"):
        for item in ET.parse(folder / filename).getroot().iter():
            assert item.attrib.get(NS + "accurate") != "false"
    source = Model(ROOT / "model" / "SharedWorkflow" / "Resource.bum")
    proved, _ = load_proved(folder / "Resource.bum")
    assert_same_core(source, proved)
    assert (folder / "Pool.buc").read_bytes() == (
        ROOT / "model" / "SharedWorkflow" / "Pool.buc"
    ).read_bytes()


def check_recorded():
    plan = json.loads((ROOT / "plan.json").read_text(encoding="utf-8"))
    trials = read_csv(ROOT / "results" / "trials.csv")
    costs = read_csv(ROOT / "results" / "costs.csv")
    assert len(trials) == 5400 and len(costs) == 600

    mutants = plan["development_faults"] + plan["evaluation_faults"]
    expected = {
        (str(size), str(capacity), method, str(seed), mutant)
        for size, capacity in plan["configurations"]
        for method in plan["methods"]
        for seed in range(plan["seeds"])
        for mutant in mutants
    }
    keys = [
        (r["requests"], r["capacity"], r["method"], r["seed"], r["mutant"])
        for r in trials
    ]
    assert len(set(keys)) == len(keys) and set(keys) == expected
    for row in trials:
        assert not row["first_detection"] or 1 <= int(row["first_detection"]) <= 16

    expected_counts = {
        "nominal": (0, 0),
        "random": (480, 546),
        "model_conflicts": (485, 550),
        "canonical_independence": (269, 269),
    }
    for method, counts in expected_counts.items():
        qualified = [r for r in trials if r["method"] == method and eligible(r, plan)]
        assert len(qualified) == 550
        assert tuple(sum(found(r, b) for r in qualified) for b in (4, 16)) == counts

    summary = json.loads((ROOT / "results" / "run_summary.json").read_text(encoding="utf-8"))
    assert summary["clean_replays"] == 9600
    assert summary["mutant_replays"] == 86400
    finite = json.loads((ROOT / "results" / "model_conformance.json").read_text(encoding="utf-8"))
    assert all(row["complete"] for row in finite)
    assert sum(row["states"] for row in finite) == 2127
    assert sum(row["all_attempts"] for row in finite) == 49776


def compare_csv(generated, filename):
    recorded = read_csv(ROOT / "results" / filename)
    fresh = read_csv(generated / filename)
    assert len(recorded) == len(fresh), filename
    for old, new in zip(recorded, fresh):
        assert old.keys() == new.keys(), filename
        for key in old:
            if old[key] == new[key]:
                continue
            try:
                close = math.isclose(float(old[key]), float(new[key]), abs_tol=1e-9, rel_tol=1e-12)
            except ValueError:
                close = False
            assert close, (filename, key, old[key], new[key])


def check_generated(folder, analysis_only):
    for filename in (
        "qualified_summary.csv", "per_mutant.csv", "paired_bootstrap.csv"
    ):
        compare_csv(folder, filename)
    if analysis_only:
        return
    compare_csv(folder, "trials.csv")
    recorded = json.loads((ROOT / "results" / "model_conformance.json").read_text(encoding="utf-8"))
    generated = json.loads((folder / "model_conformance.json").read_text(encoding="utf-8"))
    without_time = lambda rows: [{k: v for k, v in row.items() if k != "seconds"} for row in rows]
    assert without_time(recorded) == without_time(generated)
    expected_bridge = json.loads((ROOT / "results" / "proof_bridge.json").read_text(encoding="utf-8"))
    actual_bridge = json.loads((folder / "proof_bridge.json").read_text(encoding="utf-8"))
    assert expected_bridge == actual_bridge
    summary = json.loads((folder / "run_summary.json").read_text(encoding="utf-8"))
    assert summary["clean_replays"] == 9600 and summary["mutant_replays"] == 86400


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated", type=Path)
    parser.add_argument("--analysis-only", action="store_true")
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()
    check_checksums()
    check_proofs()
    check_recorded()
    if args.generated:
        check_generated(args.generated.resolve(), args.analysis_only)
    print("Artifact audit passed: source hashes, 24 native proof statuses, and recorded study counts.")
    if args.generated:
        print("Generated deterministic results match the recorded results.")
    print("Native Rodin proof replay is a separate command; this audit inspects the saved proof artifacts.")


if __name__ == "__main__":
    main()
