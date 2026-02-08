# pylint: disable=invalid-name
"""
P3 - Word Count
Counts distinct words and their frequencies from an input text file.

Usage:
    python source/wordCount.py data/TC1.txt
Optional:
    python source/wordCount.py data --all
"""

from __future__ import annotations

import re
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


WORD_PATTERN = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9']+")
RESULTS_FILENAME = "WordCountResults.txt"


@dataclass(frozen=True)
class WordCountResult:
    """Holds word count summary and execution metadata."""
    total_words: int
    distinct_words: int
    frequencies: Dict[str, int]
    elapsed_seconds: float


def normalize_words(text: str) -> List[str]:
    """Extract and normalize words from text to lowercase."""
    words = WORD_PATTERN.findall(text)
    return [w.lower() for w in words if w.strip()]


def count_words(text: str, elapsed: float) -> WordCountResult:
    """Count distinct word frequencies from text input."""
    words = normalize_words(text)
    counter = Counter(words)
    return WordCountResult(
        total_words=sum(counter.values()),
        distinct_words=len(counter),
        frequencies=dict(counter),
        elapsed_seconds=elapsed,
    )


def write_results(output_path: Path, input_file: str, result: WordCountResult) -> None:
    """Write results to the output file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write("P3 - wordCount.py Results\n")
        f.write(f"Input file: {input_file}\n")
        f.write(f"Total words: {result.total_words}\n")
        f.write(f"Distinct words: {result.distinct_words}\n")
        f.write(f"Elapsed time (seconds): {result.elapsed_seconds}\n\n")
        f.write("WORD\tCOUNT\n")

        # Sort by count desc then alphabetically
        for word, cnt in sorted(result.frequencies.items(), key=lambda x: (-x[1], x[0])):
            f.write(f"{word}\t{cnt}\n")


def run_single_case(input_path: Path, results_dir: Path) -> None:
    """Run the word count for a single input file."""
    start = time.perf_counter()
    text = input_path.read_text(encoding="utf-8")
    elapsed = time.perf_counter() - start

    result = count_words(text, elapsed)
    out_path = results_dir / RESULTS_FILENAME
    write_results(out_path, str(input_path), result)
    print(f"[OK] Results written to: {out_path}")


def run_all_cases(data_dir: Path, results_dir: Path) -> None:
    """Run the word count for a all input files."""
    tc_files = sorted(data_dir.glob("TC*.txt"))
    if not tc_files:
        raise FileNotFoundError(f"No TC*.txt files found in: {data_dir}")

    results_dir.mkdir(parents=True, exist_ok=True)

    summary_path = results_dir / "batch_summary.txt"
    with summary_path.open("w", encoding="utf-8") as summary:
        summary.write("Batch summary for P3\n\n")
        for tc in tc_files:
            try:
                start = time.perf_counter()
                text = tc.read_text(encoding="utf-8")
                elapsed = time.perf_counter() - start

                result = count_words(text, elapsed)
                case_out = results_dir / f"WordCountResults_{tc.stem}.txt"
                write_results(case_out, str(tc), result)
                summary.write(f"{tc.name}: OK -> {case_out.name}\n")
            except OSError as exc:
                summary.write(f"{tc.name}: ERROR -> {exc}\n")

    print(f"[OK] Batch results written to: {results_dir}")
    print(f"[OK] Summary: {summary_path}")


def main() -> int:
    """Entry point for CLI usage."""
    # Expect to be executed from P3 folder:
    #   python source/wordCount.py data/TC1.txt
    # or:
    #   python source/wordCount.py data --all
    if len(sys.argv) < 2:
        print("Usage: python source/wordCount.py <input_file> OR <data_dir> --all")
        return 1

    base_dir = Path(__file__).resolve().parents[1]  # .../P3
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
