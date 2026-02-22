"""
JSON storage helpers with graceful error handling.

Req 5: invalid data -> print error and continue execution.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True)
class JsonStore:
    """Stores a list[dict] in a JSON file."""
    path: Path

    def load_list(self) -> List[Dict[str, Any]]:
        """Load a list of dicts. On error, prints and returns []."""
        try:
            text = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            print(f"[WARN] File not found: {self.path}. Using empty list.")
            return []
        except OSError as exc:
            print(f"[ERROR] Could not read {self.path}: {exc}. Using empty list.")
            return []

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            print(f"[ERROR] Invalid JSON in {self.path}: {exc}. Using empty list.")
            return []

        if not isinstance(data, list):
            print(f"[ERROR] Expected a list in {self.path}. Using empty list.")
            return []

        clean: List[Dict[str, Any]] = []
        for idx, item in enumerate(data):
            if isinstance(item, dict):
                clean.append(item)
            else:
                print(f"[ERROR] Item #{idx} in {self.path} is not an object; skipped.")
        return clean

    def save_list(self, rows: List[Dict[str, Any]]) -> None:
        """Save a list of dicts."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(rows, indent=2, ensure_ascii=False)
        self.path.write_text(payload + "\n", encoding="utf-8")