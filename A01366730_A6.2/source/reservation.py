"""
Reservation class + persistent behaviors (stored in files).

Req 2.3:
- Create Reservation (Customer, Hotel)
- Cancel Reservation

Also supports Hotel.reserve_a_room and cancel restoring inventory.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from typing import TYPE_CHECKING

from hotel import ConflictError, NotFoundError
from storage import JsonStore


if TYPE_CHECKING:
    from hotel import Hotel
    from customer import Customer


@dataclass(frozen=True)
class Reservation:
    """Represents a reservation."""
    reservation_id: str
    customer_id: str
    hotel_id: str
    room_count: int
    status: str
    created_at: str

    @staticmethod
    def _store(data_dir: Path) -> JsonStore:
        return JsonStore(data_dir / "reservations.json")

    @staticmethod
    def _from_dict(row: Dict[str, Any]) -> "Reservation":
        reservation_id = str(row["reservation_id"])
        customer_id = str(row["customer_id"])
        hotel_id = str(row["hotel_id"])
        room_count = int(row["room_count"])
        status = str(row["status"])
        created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

        if room_count <= 0:
            raise ValueError("room_count must be positive.")
        if status not in {"ACTIVE", "CANCELLED"}:
            raise ValueError("status must be ACTIVE or CANCELLED.")

        return Reservation(
            reservation_id=reservation_id,
            customer_id=customer_id,
            hotel_id=hotel_id,
            room_count=room_count,
            status=status,
            created_at=created_at,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Returns dic of reservation"""
        return {
            "reservation_id": self.reservation_id,
            "customer_id": self.customer_id,
            "hotel_id": self.hotel_id,
            "room_count": self.room_count,
            "status": self.status,
            "created_at": self.created_at,
        }

    @classmethod
    def load_all(cls, data_dir: Path) -> List["Reservation"]:
        """Load reservation details"""
        rows = cls._store(data_dir).load_list()
        reservations: List[Reservation] = []
        for idx, row in enumerate(rows):
            try:
                reservations.append(cls._from_dict(row))
            except (KeyError, TypeError, ValueError) as exc:
                print(
                    f"[ERROR] Invalid reservation record #{idx}:"
                    f" {exc}. Skipped."
                )
        return reservations

    @classmethod
    def _save_all(
        cls, data_dir: Path, reservations: List["Reservation"]
    ) -> None:
        cls._store(data_dir).save_list([r.to_dict() for r in reservations])

    @classmethod
    def has_active_for_hotel(cls, data_dir: Path, hotel_id: str) -> bool:
        """Reviews if there's active reservation"""
        reservations = cls.load_all(data_dir)
        return any(
            r.hotel_id == hotel_id and r.status == "ACTIVE"
            for r in reservations
        )

    @classmethod
    def has_active_for_customer(cls, data_dir: Path, customer_id: str) -> bool:
        """Reviews if there's active reservation"""
        return any(
            r.customer_id == customer_id and r.status == "ACTIVE"
            for r in cls.load_all(data_dir)
        )

    @classmethod
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments
    def create_a_reservation(
        cls,
        data_dir: Path,
        reservation_id: str,
        customer_id: str,
        hotel_id: str,
        room_count: int = 1,
    ) -> "Reservation":
        """Create reservation and persist."""
        # Validate customer exists
        customers = Customer.load_all(data_dir)
        if not any(c.customer_id == customer_id for c in customers):
            raise NotFoundError(f"Customer not found: {customer_id}")

        # Validate hotel exists and has availability (and persist decrement)
        _ = Hotel.display_hotel_information(data_dir, hotel_id)
        _ = Hotel.reserve_a_room(data_dir, hotel_id, room_count=room_count)

        reservations = cls.load_all(data_dir)
        if any(r.reservation_id == reservation_id for r in reservations):
            # rollback hotel decrement
            raise ConflictError(
                f"Reservation already exists: {reservation_id}"
            )

        created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        reservation = cls._from_dict(
            {
                "reservation_id": reservation_id,
                "customer_id": customer_id,
                "hotel_id": hotel_id,
                "room_count": room_count,
                "status": "ACTIVE",
                "created_at": created_at,
            }
        )

        reservations.append(reservation)
        cls._save_all(data_dir, reservations)
        return reservation

    @classmethod
    def cancel_a_reservation(
        cls, data_dir: Path, reservation_id: str
    ) -> "Reservation":
        """Cancel reservation and restore hotel availability."""
        from hotel import Hotel  # pylint: disable=import-outside-toplevel
        reservations = cls.load_all(data_dir)
        found = False
        updated: List[Reservation] = []
        cancelled_res: Reservation | None = None

        for r in reservations:
            if r.reservation_id != reservation_id:
                updated.append(r)
                continue

            found = True
            if r.status == "CANCELLED":
                raise ConflictError("Reservation already cancelled.")

            # restore hotel availability
            hotel_info = Hotel.display_hotel_information(data_dir, r.hotel_id)

            current_available = int(hotel_info["rooms_available"])
            rooms_to_restore = int(r.room_count)
            new_rooms_available = current_available + rooms_to_restore

            Hotel.modify_hotel_information(
                data_dir,
                r.hotel_id,
                rooms_available=new_rooms_available
            )

            cancelled_res = cls._from_dict(
                {
                    "reservation_id": r.reservation_id,
                    "customer_id": r.customer_id,
                    "hotel_id": r.hotel_id,
                    "room_count": r.room_count,
                    "status": "CANCELLED",
                    "created_at": r.created_at,
                }
            )
            updated.append(cancelled_res)

        if not found:
            raise NotFoundError(f"Reservation not found: {reservation_id}")
        assert cancelled_res is not None  # for type checkers

        cls._save_all(data_dir, updated)
        return cancelled_res
