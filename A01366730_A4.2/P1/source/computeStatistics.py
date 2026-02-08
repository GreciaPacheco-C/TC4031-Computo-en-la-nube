# pylint: disable=invalid-name
"""
P1 - Compute Statistics
Reads a text file containing numbers and computes:
mean, median, mode, variance, and standard deviation.

Usage (from P1 folder):
    python source/computeStatistics.py data/TC1.txt
Optional:
    python source/computeStatistics.py data --all
"""

from __future__ import annotations

import math
import re
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


NUMBER_PATTERN = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")
RESULTS_FILENAME = "StatisticsResults.txt"


@dataclass(frozen=True)
class StatsResult: # pylint: disable=too-many-instance-attributes
    """Container for computed statistics"""
    count: int
    mean: float
    median: float
    mode: str
    variance: float
    std_dev: float
    invalid_tokens: int
    elapsed_seconds: float


def extract_numbers_from_text(text: str) -> Tuple[List[float], int]:
    """
    Extract numeric tokens from a text blob. Anything that isn't parseable
    as a number is considered invalid.

    Returns:
        (numbers, invalid_count)
    """
    tokens = re.split(r"\s+", text.strip()) if text.strip() else []
    numbers: List[float] = []
    invalid = 0

    for tok in tokens:
        if not tok:
            continue
        # We accept tokens that match a number pattern fully
        if NUMBER_PATTERN.fullmatch(tok):
            numbers.append(float(tok))
        else:
            invalid += 1

    return numbers, invalid


def compute_statistics(numbers: List[float], invalid_tokens: int, elapsed: float) -> StatsResult:
    """Compute summary statistics for the list of numbers."""
    if not numbers:
        raise ValueError("No valid numeric values were found in the input file.")

    mean_val = statistics.fmean(numbers)
    median_val = statistics.median(numbers)

    # Mode: may be multiple or none; handle gracefully
    mode_str: str
    try:
        mode_val = statistics.mode(numbers)
        mode_str = str(mode_val)
    except statistics.StatisticsError:
        # Use multimode to report all modes if tie or no unique mode
        modes = statistics.multimode(numbers)
        mode_str = ", ".join(str(m) for m in modes) if modes else "No mode"

    variance_val = statistics.pvariance(numbers)
    std_val = math.sqrt(variance_val)

    return StatsResult(
        count=len(numbers),
        mean=mean_val,
        median=median_val,
        mode=mode_str,
        variance=variance_val,
        std_dev=std_val,
        invalid_tokens=invalid_tokens,
        elapsed_seconds=elapsed,
    )


def write_results(output_path: Path, input_file: str, result: StatsResult) -> None:
    """Write the computed statistics to the output results file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write("P1 - computeStatistics.py Results\n")
        f.write(f"Input file: {input_file}\n")
        f.write(f"Valid count: {result.count}\n")
        f.write(f"Invalid tokens ignored: {result.invalid_tokens}\n\n")
        f.write(f"Mean: {result.mean}\n")
        f.write(f"Median: {result.median}\n")
        f.write(f"Mode: {result.mode}\n")
        f.write(f"Variance (population): {result.variance}\n")
        f.write(f"Standard deviation: {result.std_dev}\n\n")
        f.write(f"Elapsed time (seconds): {result.elapsed_seconds}\n")


def run_single_case(input_path: Path, results_dir: Path) -> None:
    """Run the statistics computation for a single input file."""
    start = time.perf_counter()
    text = input_path.read_text(encoding="utf-8")
    numbers, invalid = extract_numbers_from_text(text)
    elapsed = time.perf_counter() - start

    result = compute_statistics(numbers, invalid, elapsed)

    output_path = results_dir / RESULTS_FILENAME
    write_results(output_path, str(input_path), result)

    print(f"[OK] Results written to: {output_path}")


def run_all_cases(data_dir: Path, results_dir: Path) -> None:
    """Run the statistics computation for all input files."""
    tc_files = sorted(data_dir.glob("TC*.txt"))
    if not tc_files:
        raise FileNotFoundError(f"No TC*.txt files found in: {data_dir}")

    results_dir.mkdir(parents=True, exist_ok=True)

    summary_path = results_dir / "batch_summary.txt"
    with summary_path.open("w", encoding="utf-8") as summary:
        summary.write("Batch summary for P1\n\n")
        for tc in tc_files:
            try:
                start = time.perf_counter()
                text = tc.read_text(encoding="utf-8")
                numbers, invalid = extract_numbers_from_text(text)
                elapsed = time.perf_counter() - start
                result = compute_statistics(numbers, invalid, elapsed)

                case_out = results_dir / f"StatisticsResults_{tc.stem}.txt"
                write_results(case_out, str(tc), result)
                summary.write(f"{tc.name}: OK -> {case_out.name}\n")
            except (ValueError, OSError) as exc:
                summary.write(f"{tc.name}: ERROR -> {exc}\n")

    print(f"[OK] Batch results written to: {results_dir}")
    print(f"[OK] Summary: {summary_path}")


def main() -> int:
    """Entry point for CLI usage."""
    # Expect to be executed from P1 folder:
    #   python source/computeStatistics.py data/TC1.txt
    # or:
    #   python source/computeStatistics.py data --all

    if len(sys.argv) < 2:
        print("Usage: python source/computeStatistics.py <input_file> OR <data_dir> --all")
        return 1

    base_dir = Path(__file__).resolve().parents[1]  # .../P1
    results_dir = base_dir / "results"

    arg1 = Path(sys.argv[1])
    if len(sys.argv) >= 3 and sys.argv[2] == "--all":
        data_dir = arg1 if arg1.is_absolute() else (base_dir / arg1)
        run_all_cases(data_dir, results_dir)
        return 0

    input_path = arg1 if arg1.is_absolute() else (base_dir / arg1)
    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}")
        return 1

    run_single_case(input_path, results_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
