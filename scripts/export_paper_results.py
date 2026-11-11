#!/usr/bin/env python3
"""Export manuscript tables from recorded data without modifying that data."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
from analyse import eligible, found

RECORDED = ROOT / "results"
SUPPLEMENTAL = RECORDED / "supplemental"

METHODS = {
    "nominal": "Nominal",
    "random": "Random",
    "model_conflicts": "Model-derived",
    "canonical_independence": "Conservative sleep-set DFS",
}


def write_csv(folder, name, rows):
    with (folder / name).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def configuration_rows(plan, rows):
    for requests, capacity in plan["configurations"]:
        yield requests, capacity, [
            row for row in rows
            if (int(row["requests"]), int(row["capacity"])) == (requests, capacity)
        ]


def export_supplemental_tables(destination, plan, qualified):
    ablation = json.loads((SUPPLEMENTAL / "ablation.json").read_text())
    ablation_rows = []
    for method in ("model_conflicts", "random"):
        subset = [row for row in ablation if row["method"] == method and eligible(row, plan)]
        for budget in (1, 4, 8, 16):
            counts = {
                mode: sum(row[mode] is not None and row[mode] <= budget for row in subset)
                for mode in ("conformance", "audit", "combined")
            }
            ablation_rows.append({"method": METHODS[method], "budget": budget,
                                  "eligible_trials": len(subset), **counts})
    write_csv(destination, "table8_oracle_ablation.csv", ablation_rows)

    coverage = json.loads((SUPPLEMENTAL / "coverage.json").read_text())
    model_coverage = [row for row in coverage if row["method"] == "model_conflicts"]
    coverage_rows = []
    for requests, capacity, suites in configuration_rows(plan, model_coverage):
        candidates = {row["candidate_objectives"] for row in suites}
        distinct = {row["distinct"] for row in suites}
        assert len(candidates) == len(distinct) == 1
        pair_counts = {
            label: len({tuple(map(tuple, pair)) for row in suites for pair in row[key]})
            for label, key in (("feasible", "feasible_sample"), ("targeted", "targeted_pairs"))
        }
        coverage_rows.append({"requests": requests, "capacity": capacity,
                              "candidates": candidates.pop(), **pair_counts,
                              "distinct_schedules_per_suite": distinct.pop()})
    write_csv(destination, "table10_interference_coverage.csv", coverage_rows)

    elapsed_rows = []
    timing = read_csv(SUPPLEMENTAL / "timing.csv")
    for requests, capacity, group in configuration_rows(plan, timing):
        for method in ("model_conflicts", "random"):
            subset = [row for row in group if row["method"] == method]
            assert len(subset) == sum(
                int(row["requests"]) == requests and int(row["capacity"]) == capacity
                for row in qualified[method]
            )
            counts = {
                f"detected_by_{threshold}_ms": sum(
                    bool(row["schedule"]) and float(row["elapsed_ms"]) <= threshold
                    for row in subset
                )
                for threshold in (25, 50, 100)
            }
            elapsed_rows.append({"requests": requests, "capacity": capacity,
                                 "method": METHODS[method], "eligible_trials": len(subset),
                                 **counts})
    write_csv(destination, "table13_elapsed_detection.csv", elapsed_rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/paper-tables")
    args = parser.parse_args()
    destination = args.output.resolve()
    if destination.exists():
        parser.error(f"Output directory already exists: {destination}")

    plan = json.loads((ROOT / "plan.json").read_text())
    trials = read_csv(RECORDED / "trials.csv")
    destination.mkdir(parents=True)

    statuses = list(ET.parse(ROOT / "proof/SharedWorkflow/Resource.bps").getroot())
    kinds = Counter(row.attrib["name"].rsplit("/", 1)[-1] for row in statuses)
    write_csv(destination, "table4_proof_obligations.csv", [
        {"obligation": kind, "generated": kinds[kind], "discharged": sum(
            row.attrib["name"].endswith("/" + kind)
            and int(row.attrib["org.eventb.core.confidence"]) > 0
            for row in statuses)}
        for kind in ("INV", "THM", "WD")
    ])
    finite = json.loads((ROOT / "results/model_conformance.json").read_text())
    write_csv(destination, "table5_finite_conformance.csv", finite)

    faults = plan["development_faults"] + plan["evaluation_faults"]
    raw = []
    for index, fault in enumerate(faults):
        row = {"id": f"D{index+1}" if index < 3 else f"E{index-2}", "mutant": fault}
        for method, label in METHODS.items():
            subset = [r for r in trials if r["mutant"] == fault and r["method"] == method]
            row[label] = sum(found(r, 16) for r in subset)
            row[label + " denominator"] = len(subset)
        raw.append(row)
    write_csv(destination, "table6_raw_mutant_detections.csv", raw)

    qualified = {
        method: [row for row in trials if row["method"] == method and eligible(row, plan)]
        for method in METHODS
    }
    assert all(len(subset) == 550 for subset in qualified.values())

    curve = []
    for method, label in METHODS.items():
        subset = qualified[method]
        for budget in range(1, 17):
            detected = sum(found(r, budget) for r in subset)
            curve.append({"method": label, "budget": budget, "detected": detected,
                          "eligible_trials": len(subset), "percent": 100*detected/len(subset)})
    write_csv(destination, "figure4_detection_curve.csv", curve)

    summary = []
    for method in ("random", "model_conflicts"):
        subset = qualified[method]
        groups = list(configuration_rows(plan, subset))
        for requests, capacity, group in groups + [("Total", "", subset)]:
            summary.append({"requests": requests, "capacity": capacity,
                            "method": METHODS[method], "eligible_trials": len(group),
                            "budget4": sum(found(row, 4) for row in group),
                            "budget16": sum(found(row, 16) for row in group)})
    write_csv(destination, "table7_qualified_detection.csv", summary)
    export_supplemental_tables(destination, plan, qualified)
    witnesses = json.loads((ROOT / "results/witnesses.json").read_text())
    witness = next(w for w in witnesses if w["method"] == "model_conflicts"
                   and w["requests"] == 4 and w["capacity"] == 2
                   and w["mutant"] == "reserve_lost_update" and w["seed"] == 0)
    prefix = []
    for index, entry in enumerate(witness["log"], 1):
        state = entry["snapshot"]
        request, operation, phase = entry["hook"]
        prefix.append({"step": index, "request": request, "operation": operation,
                       "phase": phase, "free": state["free"], "held_count": len(state["held"]),
                       "free_plus_held": state["free"] + len(state["held"]),
                       "failures": ";".join(entry["failures"])})
        if entry["failures"]:
            break
    write_csv(destination, "table9_first_failing_prefix.csv", prefix)
    shutil.copy2(RECORDED / "paired_bootstrap.csv", destination / "table11_paired_bootstrap.csv")
    shutil.copy2(SUPPLEMENTAL / "primary_timing_summary_rerun.csv",
                 destination / "table12_suite_timing.csv")
    (destination / "README.md").write_text(
        "# Paper table exports\n\n"
        "Table numbers follow the manuscript identified in docs/MANUSCRIPT_MATCH.json.\n"
        "Tables 4 through 13 and Figure 4 are generated from the recorded evidence.\n"
        "See docs/PAPER_RESULTS.md for sources, modes, and denominators.\n"
        "Tables 12 and 13 use the archived timings for the machine described in the manuscript.\n",
        encoding="utf-8",
    )
    print(f"Exported paper tables and detection-curve data to {destination}")


if __name__ == "__main__":
    main()
