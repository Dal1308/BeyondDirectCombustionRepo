import os
import itertools
import argparse
from concurrent.futures import ProcessPoolExecutor
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from models.thermodynamic.brayton_heat_pump_architecture_space.core.physics_engine import PhysicsEngine, ModelStatus


_engine = None


def init_worker():
    global _engine
    _engine = PhysicsEngine()


def run_chunk(chunk):
    global _engine
    rows = []
    counts = Counter()

    for fuel_flow, t_source in chunk:
        try:
            result = _engine.perform_energy_audit(fuel_flow, t_source)
            status = result.get("status")
            counts[status.value if isinstance(status, ModelStatus) else str(status)] += 1

            if status == ModelStatus.VALID:
                metrics = result.get("metrics", {})
                rows.append(
                    {
                        "fuel_flow": fuel_flow,
                        "t_source": t_source,
                        "eta_sys": metrics.get("eta_effective"),
                        "t_sink": metrics.get("t_sink"),
                        "cop_hp": metrics.get("cop_hp"),
                        "status": ModelStatus.VALID.value,
                        "is_valid": True,
                    }
                )
        except Exception:
            # Count failed cases so the valid-only export keeps its denominator.
            counts["exception"] += 1
            continue

    return rows, dict(counts)


def run_serial(cases):
    init_worker()
    rows = []
    counts = Counter()
    for case in cases:
        chunk_rows, chunk_counts = run_chunk([case])
        rows.extend(chunk_rows)
        counts.update(chunk_counts)
    return rows, counts


def chunked_iterable(iterable, chunk_size):
    it = iter(iterable)
    while True:
        chunk = list(itertools.islice(it, chunk_size))
        if not chunk:
            break
        yield chunk


def analyze_efficiencies_high_res(full_run: bool = False):
    # Default: 10k cases (100×100) — fast enough for local development
    # --full-run: 1M cases (1000×1000) — high resolution, needs compute cluster
    if full_run:
        N_FUEL = 1000
        N_TEMP = 1000
        label = "FULL RUN (1M cases)"
    else:
        N_FUEL = 100
        N_TEMP = 100
        label = "default (10k cases)"
    print(f"[{label}] N_FUEL={N_FUEL}, N_TEMP={N_TEMP}")
    CHUNK_SIZE = 5000
    MAX_WORKERS = os.cpu_count() or 1

    fuel_flows = np.logspace(-10, 0, N_FUEL)
    source_temps = np.linspace(-30, 110, N_TEMP)

    total_cases = N_FUEL * N_TEMP
    print(f"Processing {total_cases:,} cases with {MAX_WORKERS} workers...")

    cases = itertools.product(fuel_flows, source_temps)

    all_rows = []
    status_counts = Counter()
    processed_chunks = 0

    try:
        with ProcessPoolExecutor(
            max_workers=MAX_WORKERS,
            initializer=init_worker,
        ) as executor:
            for rows, counts in executor.map(run_chunk, chunked_iterable(cases, CHUNK_SIZE), chunksize=1):
                all_rows.extend(rows)
                status_counts.update(counts)
                processed_chunks += 1
                if processed_chunks % 10 == 0:
                    print(
                        f"Processed {processed_chunks * CHUNK_SIZE:,} parameter combinations "
                        f"(approx., before filtering invalid cases)..."
                    )
    except (PermissionError, OSError) as exc:
        print(f"Falling back to serial execution: {exc}")
        all_rows, status_counts = run_serial(list(cases))

    df_eff = pd.DataFrame(all_rows)

    output_dir = Path(__file__).resolve().parents[1] / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = (
        "efficiency_distribution_high_res_full_run.csv"
        if full_run
        else "efficiency_distribution_high_res.csv"
    )
    output_path = output_dir / filename
    df_eff.to_csv(output_path, index=False)

    summary_path = output_dir / filename.replace(".csv", "_summary.csv")
    summary = {
        "total_cases": total_cases,
        "valid_cases": status_counts.get(ModelStatus.VALID.value, 0),
        "out_of_envelope_cases": status_counts.get(ModelStatus.OUT_OF_ENVELOPE.value, 0),
        "invalid_cases": status_counts.get(ModelStatus.INVALID.value, 0),
        "exception_cases": status_counts.get("exception", 0),
    }
    pd.DataFrame([summary]).to_csv(summary_path, index=False)

    print(f"Saved {len(df_eff):,} valid results to:")
    print(output_path)
    print("Validity accounting:")
    print(summary_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--full-run",
        action="store_true",
        help="Run the high-resolution 1M-case sweep and write a _full_run output.",
    )
    args = parser.parse_args()
    analyze_efficiencies_high_res(full_run=args.full_run)
