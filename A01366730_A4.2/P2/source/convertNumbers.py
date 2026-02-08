# pylint: disable=invalid-name
"""
P2 - Convert Numbers
Reads integers and converts each to binary and hexadecimal using manual algorithms
(no bin()/hex()).

Usage:
    python source/convertNumbers.py data/TC1.txt
Optional:
    python source/convertNumbers.py data --all
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


HEX_DIGITS = "0123456789ABCDEF"
RESULTS_FILENAME = "ConvertionResults.txt"


@dataclass(frozen=True)
class ConversionRow:
    """Represents a decimal number and its binary and hexadecimal conversions."""
    original: int
    binary: str
    hexa: str

def parse_integers(text: str) -> Tuple[List[int], int]:
    """Parse integers from text and count invalid tokens."""
    tokens = text.split()
    values: List[int] = []
    invalid = 0
    for tok in tokens:
        try:
            # Force integer only
            if tok.strip().startswith(("+", "-")):
                int(tok)
            values.append(int(tok))
        except ValueError:
            invalid += 1
    return values, invalid


def to_binary(n: int) -> str:
    """Convert an integer to its binary representation."""
    if n == 0:
        return "0"
    sign = "-" if n < 0 else ""
    n = abs(n)

    bits: List[str] = []
    while n > 0:
        bits.append(str(n % 2))
        n //= 2
    return sign + "".join(reversed(bits))


def to_hexadecimal(n: int) -> str:
    """Convert an integer to its hexadecimal representation."""
    if n == 0:
        return "0"
    sign = "-" if n < 0 else ""
    n = abs(n)

    digits: List[str] = []
    while n > 0:
        digits.append(HEX_DIGITS[n % 16])
        n //= 16
    return sign + "".join(reversed(digits))


def convert(values: List[int]) -> List[ConversionRow]:
    """Convert a list of integers to binary and hexadecimal."""
    rows: List[ConversionRow] = []
    for v in values:
        rows.append(ConversionRow(original=v, binary=to_binary(v), hexa=to_hexadecimal(v)))
    return rows


def write_results(output_path: Path, input_file: str, rows: List[ConversionRow],
                  invalid: int, elapsed: float) -> None:
    """Write conversion results to the output file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write("P2 - convertNumbers.py.py Results\n")
        f.write(f"Input file: {input_file}\n")
        f.write(f"Invalid tokens ignored: {invalid}\n")
        f.write(f"Elapsed time (seconds): {elapsed}\n\n")
        f.write("DECIMAL\tBINARY\tHEXADECIMAL\n")
        for row in rows:
            f.write(f"{row.original}\t{row.binary}\t{row.hexa}\n")


def run_single_case(input_path: Path, results_dir: Path) -> None:
    """Run the convert numbers for a single input file."""
    start = time.perf_counter()
    text = input_path.read_text(encoding="utf-8")
    values, invalid = parse_integers(text)
    rows = convert(values)
    elapsed = time.perf_counter() - start

    out_path = results_dir / RESULTS_FILENAME
    write_results(out_path, str(input_path), rows, invalid, elapsed)
    print(f"[OK] Results written to: {out_path}")


def run_all_cases(data_dir: Path, results_dir: Path) -> None:
    """Run the convert numbers for a all input files."""
    tc_files = sorted(data_dir.glob("TC*.txt"))
    if not tc_files:
        raise FileNotFoundError(f"No TC*.txt files found in: {data_dir}")

    results_dir.mkdir(parents=True, exist_ok=True)
    summary_path = results_dir / "batch_summary.txt"

    with summary_path.open("w", encoding="utf-8") as summary:
        summary.write("Batch summary for P2\n\n")
        for tc in tc_files:
            try:
                start = time.perf_counter()
                text = tc.read_text(encoding="utf-8")
                values, invalid = parse_integers(text)
                rows = convert(values)
                elapsed = time.perf_counter() - start

                case_out = results_dir / f"ConvertionResults_{tc.stem}.txt"
                write_results(case_out, str(tc), rows, invalid, elapsed)
                summary.write(f"{tc.name}: OK -> {case_out.name}\n")
            except OSError as exc:
                summary.write(f"{tc.name}: ERROR -> {exc}\n")

    print(f"[OK] Batch results written to: {results_dir}")
    print(f"[OK] Summary: {summary_path}")


def main() -> int:
    """Entry point for CLI usage."""
    # Expect to be executed from P2 folder:
    #   python source/convertNumbers.py data/TC1.txt
    # or:
    #   python source/convertNumbers.py data --all

    if len(sys.argv) < 2:
        print("Usage: python source/convertNumbers.py.py <input_file> OR <data_dir> --all")
        return 1

    base_dir = Path(__file__).resolve().parents[1]  # .../P2
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
