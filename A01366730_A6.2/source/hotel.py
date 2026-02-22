"""
Hotel class + persistent behaviors (stored in files).

Req 2.1:
- Create/Delete/Display/Modify Hotel
- Reserve a Room
- Cancel a Reservation (delegates to Reservation)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from storage import JsonStore
from reservation import Reservation  # local import to avoid cycles

class NotFoundError(ValueError):
    """Entity not found."""


class ConflictError(ValueError):
    """Operation conflicts with current state."""


@dataclass(frozen=True)
class Hotel:
    """Represents a hotel with room inventory."""
    hotel_id: str
    name: str
    rooms_total: int
    rooms_available: int

    @staticmethod
    def _store(data_dir: Path) -> JsonStore:
        return JsonStore(data_dir / "hotels.json")

    @staticmethod
    def _from_dict(row: Dict[str, Any]) -> "Hotel":
        hotel_id = str(row["hotel_id"])
        name = str(row["name"])
        rooms_total = int(row["rooms_total"])
        rooms_available = int(row["rooms_available"])

        if rooms_total < 0 or rooms_available < 0:
            raise ValueError("Room counts must be non-negative.")
        if rooms_available > rooms_total:
            raise ValueError("rooms_available cannot exceed rooms_total.")

        return Hotel(
            hotel_id=hotel_id,
            name=name,
            rooms_total=rooms_total,
            rooms_available=rooms_available,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "hotel_id": self.hotel_id,
            "name": self.name,
            "rooms_total": self.rooms_total,
            "rooms_available": self.rooms_available,
        }

    # -------- Persistent behaviors --------

    @classmethod
    def load_all(cls, data_dir: Path) -> List["Hotel"]:
        """Load all hotels, skipping invalid rows."""
        rows = cls._store(data_dir).load_list()
        hotels: List[Hotel] = []
        for idx, row in enumerate(rows):
            try:
                hotels.append(cls._from_dict(row))
            except (KeyError, TypeError, ValueError) as exc:
                print(f"[ERROR] Invalid hotel record #{idx}: {exc}. Skipped.")
        return hotels

    @classmethod
    def _save_all(cls, data_dir: Path, hotels: List["Hotel"]) -> None:
        cls._store(data_dir).save_list([h.to_dict() for h in hotels])

    @classmethod
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments
    def create_hotel(
        cls,
        data_dir: Path,
        hotel_id: str,
        name: str,
        rooms_total: int,
        rooms_available: Optional[int] = None,
    ) -> "Hotel":
        """Create a hotel and store it."""
        if rooms_available is None:
            rooms_available = rooms_total

        new_hotel = cls._from_dict(
            {
                "hotel_id": hotel_id,
                "name": name,
                "rooms_total": rooms_total,
                "rooms_available": rooms_available,
            }
        )

        hotels = cls.load_all(data_dir)
        if any(h.hotel_id == new_hotel.hotel_id for h in hotels):
            raise ConflictError(f"Hotel already exists: {new_hotel.hotel_id}")

        hotels.append(new_hotel)
        cls._save_all(data_dir, hotels)
        return new_hotel

    @classmethod
    def delete_hotel(cls, data_dir: Path, hotel_id: str) -> None:
        """Delete a hotel by id."""
        hotels = cls.load_all(data_dir)
        if not any(h.hotel_id == hotel_id for h in hotels):
            raise NotFoundError(f"Hotel not found: {hotel_id}")

        # Optional rule: do not delete if active reservation exists
        if Reservation.has_active_for_hotel(data_dir, hotel_id):
            raise ConflictError(
                "Cannot delete hotel with active reservations."
            )

        hotels = [h for h in hotels if h.hotel_id != hotel_id]
        cls._save_all(data_dir, hotels)

    @classmethod
    def display_hotel_information(
        cls, data_dir: Path, hotel_id: str
    ) -> Dict[str, Any]:
        """Return hotel info dict."""
        hotels = cls.load_all(data_dir)
        for h in hotels:
            if h.hotel_id == hotel_id:
                return h.to_dict()
        raise NotFoundError(f"Hotel not found: {hotel_id}")

    @classmethod
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments
    def modify_hotel_information(
        cls,
        data_dir: Path,
        hotel_id: str,
        name: Optional[str] = None,
        rooms_total: Optional[int] = None,
        rooms_available: Optional[int] = None,
    ) -> "Hotel":
        """Modify hotel attributes and persist."""
        hotels = cls.load_all(data_dir)
        found = False
        updated_hotels: List[Hotel] = []

        for h in hotels:
            if h.hotel_id != hotel_id:
                updated_hotels.append(h)
                continue

            found = True

            new_name = h.name if name is None else str(name)

            new_rooms_total = (
                h.rooms_total
                if rooms_total is None
                else int(rooms_total)
            )

            new_rooms_available = (
                h.rooms_available
                if rooms_available is None
                else int(rooms_available)
            )

            new_hotel = cls._from_dict(
                {
                    "hotel_id": h.hotel_id,
                    "name": new_name,
                    "rooms_total": new_rooms_total,
                    "rooms_available": new_rooms_available,
                }
            )

            updated_hotels.append(new_hotel)

        if not found:
            raise NotFoundError(f"Hotel not found: {hotel_id}")

        cls._save_all(data_dir, updated_hotels)
        return next(h for h in updated_hotels if h.hotel_id == hotel_id)

    @classmethod
    def reserve_a_room(
        cls,
        data_dir: Path,
        hotel_id: str,
        room_count: int = 1,
    ) -> "Hotel":
        """Reserve rooms (decrement availability)."""
        if room_count <= 0:
            raise ValueError("room_count must be positive.")

        hotels = cls.load_all(data_dir)
        updated: List[Hotel] = []
        found = False

        for h in hotels:
            if h.hotel_id != hotel_id:
                updated.append(h)
                continue

            found = True
            if h.rooms_available < room_count:
                raise ConflictError("Not enough rooms available.")

            new_hotel = cls._from_dict(
                {
                    "hotel_id": h.hotel_id,
                    "name": h.name,
                    "rooms_total": h.rooms_total,
                    "rooms_available": h.rooms_available - room_count,
                }
            )
            updated.append(new_hotel)

        if not found:
            raise NotFoundError(f"Hotel not found: {hotel_id}")

        cls._save_all(data_dir, updated)
        return next(h for h in updated if h.hotel_id == hotel_id)
