#!/usr/bin/env python3
"""
computeSales.py

Computes the total cost for all sales in a sales record JSON file, using a
price catalogue JSON file.

Expect to be executed from A01366730_A5.2 folder
Usage:

py source/computeSales.py data/TC1/TC1.ProductList.json data/TC1/TC1.Sales.json


"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

RESULTS_DIR = "results"
RESULTS_FILENAME = "_SalesResults.txt"


@dataclass(frozen=True)
class SaleLine:
    """A normalized sale line: product name and quantity."""
    product: str
    quantity: Decimal


def eprint(message: str) -> None:
    """Print errors to stderr."""
    print(message, file=sys.stderr)


def read_json_file(path: Path) -> Optional[Any]:
    """Read JSON file and return the parsed object. """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        eprint(f"[ERROR] Cannot read file '{path}': {exc}")
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        eprint(f"[ERROR] Invalid JSON in '{path}': {exc}")
        return None


def to_decimal(value: Any, *, context: str) -> Optional[Decimal]:
    """Convert a value to Decimal. """
    try:
        if isinstance(value, bool):
            raise InvalidOperation("bool is not a valid numeric type")
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        eprint(f"[ERROR] Invalid number for {context}: {value!r} ({exc})")
        return None


def _validate_price(price_val: Any, name: str) -> Optional[Decimal]:
    """Validate price and return Decimal if valid."""
    price = to_decimal(price_val, context=f"catalogue price for '{name}'")

    if price is None:
        return None

    if price < 0:
        eprint(f"[ERROR] Negative price for '{name}': {price}")
        return None

    return price


def _normalize_catalogue_list(raw: List[Any]) -> Dict[str, Decimal]:
    """Handle catalogue when JSON root is a list."""
    catalogue: Dict[str, Decimal] = {}

    for idx, entry in enumerate(raw, start=1):
        if not isinstance(entry, dict):
            eprint(
                f"[ERROR] Catalogue entry #{idx} "
                f"is not an object: {entry!r}"
            )
            continue

        name = (
            entry.get("title")
            or entry.get("product")
            or entry.get("name")
            or entry.get("Product")
        )

        price_val = (
            entry.get("price")
            or entry.get("Price")
            or entry.get("cost")
        )

        if not isinstance(name, str) or not name.strip():
            eprint(
                f"[ERROR] Catalogue entry #{idx} "
                "missing product name."
            )
            continue

        price = _validate_price(price_val, name)
        if price is not None:
            catalogue[name] = price

    return catalogue


def _normalize_direct_mapping(raw: Dict[str, Any]) -> Dict[str, Decimal]:
    """Handle simple {product: price} mapping."""
    catalogue: Dict[str, Decimal] = {}

    for name, price_val in raw.items():
        price = _validate_price(price_val, name)
        if price is not None:
            catalogue[name] = price

    return catalogue


def _normalize_catalogue_dict(raw: Dict[str, Any]) -> Dict[str, Decimal]:
    """Handle catalogue when JSON root is a dictionary."""
    # Direct mapping case
    if all(isinstance(k, str) for k in raw.keys()):
        return _normalize_direct_mapping(raw)

    # Nested list under known keys
    for key in ("catalogue", "products", "items"):
        if key in raw and isinstance(raw[key], list):
            return _normalize_catalogue_list(raw[key])

    eprint("[ERROR] Unrecognized catalogue dictionary structure.")
    return {}


def normalize_catalogue(raw: Any) -> Dict[str, Decimal]:
    """Normalize catalogue input into {product: price}"""
    if raw is None:
        return {}

    if isinstance(raw, dict):
        return _normalize_catalogue_dict(raw)

    if isinstance(raw, list):
        return _normalize_catalogue_list(raw)

    eprint("[ERROR] Unrecognized catalogue JSON structure.")
    return {}


def extract_sale_lines_from_obj(obj: Any) -> List[SaleLine]:
    """Extract SaleLine entries from a sale-like object."""
    lines: List[SaleLine] = []

    def parse_line(line_obj: Any, *, ctx: str) -> None:
        if not isinstance(line_obj, dict):
            eprint(f"[ERROR] Invalid sale line in {ctx}: {line_obj!r}")
            return

        product = (
            line_obj.get("product")
            or line_obj.get("title")
            or line_obj.get("name")
            or line_obj.get("Product")
        )
        qty_val = (
            line_obj.get("quantity")
            or line_obj.get("qty")
            or line_obj.get("Quantity")
        )

        if not isinstance(product, str) or not product.strip():
            eprint(f"[ERROR] Missing product name in {ctx}.")
            return

        qty = to_decimal(qty_val, context=f"quantity for '{product}' in {ctx}")
        if qty is None:
            return
        if qty <= 0:
            eprint(
                f"[ERROR] Non-positive quantity for '{product}'"
                f"in {ctx}: {qty}"
            )
            return

        lines.append(SaleLine(product=product, quantity=qty))

    if obj is None:
        return lines

    # If it's a list, treat as list of line objects
    if isinstance(obj, list):
        for i, line_obj in enumerate(obj, start=1):
            parse_line(line_obj, ctx=f"sale list line #{i}")
        return lines

    if isinstance(obj, dict):
        # Container keys
        for key in ("items", "products", "lines"):
            if key in obj and isinstance(obj[key], list):
                for i, line_obj in enumerate(obj[key], start=1):
                    parse_line(line_obj, ctx=f"sale '{key}' line #{i}")
                return lines

        # Single-line sale dict
        if any(k in obj for k in ("product", "Product", "title", "name")):
            parse_line(obj, ctx="single-line sale object")
            return lines

        eprint("[ERROR] Unrecognized sale object structure (dict).")
        return lines

    eprint("[ERROR] Unrecognized sale structure (not list/dict).")
    return lines


def normalize_sales(raw: Any) -> List[List[SaleLine]]:
    """ Normalize sales record into a list of sales"""
    sales: List[List[SaleLine]] = []

    if raw is None:
        return sales

    if isinstance(raw, dict):
        for key in ("sales", "record", "data"):
            if key in raw and isinstance(raw[key], list):
                return normalize_sales(raw[key])

        # Maybe single sale dict
        lines = extract_sale_lines_from_obj(raw)
        if lines:
            sales.append(lines)
        else:
            eprint("[ERROR] No valid sale lines found in sales dict.")
        return sales

    if isinstance(raw, list):
        # Could be list of sales OR list of lines for a single sale.
        if raw and all(isinstance(x, dict) for x in raw):
            looks_like_lines = sum(
                1 for x in raw
                if any(k in x for k in ("product", "Product", "title", "name"))
                and any(k in x for k in ("quantity", "Quantity", "qty"))
            )
            if looks_like_lines >= max(1, len(raw) // 2):
                sales.append(extract_sale_lines_from_obj(raw))
                return sales

        # Otherwise treat as list of sale objects
        for idx, sale_obj in enumerate(raw, start=1):
            lines = extract_sale_lines_from_obj(sale_obj)
            if not lines:
                eprint(f"[ERROR] Sale #{idx} has no valid lines; skipped.")
                continue
            sales.append(lines)
        return sales

    eprint("[ERROR] Unrecognized sales JSON structure (not list/dict).")
    return sales


def money(value: Decimal) -> str:
    """Format Decimal as money with 2 decimals."""
    return f"${value.quantize(Decimal('0.01'))}"


def compute_totals(
    catalogue: Dict[str, Decimal],
    sales: List[List[SaleLine]],
) -> Tuple[Decimal, List[str], List[str]]:
    """Compute totals."""
    report: List[str] = []
    errors_for_file: List[str] = []

    grand_total = Decimal("0")

    report.append("SALES REPORT")
    report.append("=" * 60)
    report.append(f"Catalogue items loaded: {len(catalogue)}")
    report.append(f"Sales loaded: {len(sales)}")
    report.append("")

    for sale_idx, sale_lines in enumerate(sales, start=1):
        report.append(f"Sale #{sale_idx}")
        report.append("-" * 60)

        sale_total = Decimal("0")
        valid_lines = 0

        for line in sale_lines:
            price = catalogue.get(line.product)
            if price is None:
                msg = (
                    f"[ERROR] Unknown product '{line.product}'"
                    f"in Sale #{sale_idx}."
                )
                eprint(msg)
                errors_for_file.append(msg)
                continue

            line_total = price * line.quantity
            sale_total += line_total
            valid_lines += 1

            report.append(
                f"  - {line.product} | qty={line.quantity} | "
                f"unit={money(price)} | line={money(line_total)}"
            )

        report.append(f"  Valid lines: {valid_lines}/{len(sale_lines)}")
        report.append(f"  Sale total: {money(sale_total)}")
        report.append("")

        grand_total += sale_total

    report.append("=" * 60)
    report.append(f"GRAND TOTAL: {money(grand_total)}")

    return grand_total, report, errors_for_file


def write_results_file(
    path: Path,
    report_lines: Iterable[str],
    error_lines: Iterable[str],
    elapsed_seconds: float,
) -> None:
    """Write results to SalesResults.txt."""
    lines: List[str] = list(report_lines)
    lines.append("")
    lines.append(f"Elapsed time: {elapsed_seconds:.6f} seconds")

    err_list = list(error_lines)
    if err_list:
        lines.append("")
        lines.append("ERRORS (execution continued):")
        lines.append("-" * 60)
        lines.extend(err_list)

    try:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError as exc:
        eprint(f"[ERROR] Cannot write results file '{path}': {exc}")


def build_results_path(sales_path: Path) -> Path:
    """Build the output path for the results file based on test case folder."""
    results_dir = Path(RESULTS_DIR)
    results_dir.mkdir(parents=True, exist_ok=True)

    test_case_name = sales_path.parent.name
    results_filename = f"{test_case_name}{RESULTS_FILENAME}"
    return results_dir / results_filename


def run_app(catalogue_path: Path, sales_path: Path) -> None:
    """Run the application end-to-end."""
    start = time.perf_counter()

    raw_catalogue = read_json_file(catalogue_path)
    raw_sales = read_json_file(sales_path)

    catalogue = normalize_catalogue(raw_catalogue)
    sales = normalize_sales(raw_sales)

    _grand_total, report_lines, error_lines = compute_totals(catalogue, sales)

    elapsed = time.perf_counter() - start

    for line in report_lines:
        print(line)
    print(f"Elapsed time: {elapsed:.6f} seconds")

    results_path = build_results_path(sales_path)
    write_results_file(results_path, report_lines, error_lines, elapsed)


def main(argv: List[str]) -> int:
    """CLI entrypoint."""
    if len(argv) != 3:
        eprint(
            "Usage:\n"
            "  python source/computeSales.py "
            "priceCatalogue.json salesRecord.json"
        )
        return 2

    run_app(Path(argv[1]), Path(argv[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
