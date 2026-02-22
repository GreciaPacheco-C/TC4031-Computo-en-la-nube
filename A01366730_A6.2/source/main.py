from __future__ import annotations

from pathlib import Path

from source.customer import Customer
from source.hotel import Hotel
from source.reservation import Reservation


def main() -> int:
    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Ensure base files exist
    for filename in ("hotels.json", "customers.json", "reservations.json"):
        path = data_dir / filename
        if not path.exists():
            path.write_text("[]\n", encoding="utf-8")

    # Demo flow
    if not Hotel.load_all(data_dir):
        Hotel.create_hotel(data_dir, "H100", "Tec Hotel", 10, 10)

    if not Customer.load_all(data_dir):
        Customer.create_customer(data_dir, "C100", "Grecia", "grecia@example.com")

    existing_res_ids = {r.reservation_id for r in Reservation.load_all(data_dir)}
    if "R100" not in existing_res_ids:
        Reservation.create_a_reservation(data_dir, "R100", "C100", "H100", room_count=2)

    print("Hotels:", [h.to_dict() for h in Hotel.load_all(data_dir)])
    print("Customers:", [c.to_dict() for c in Customer.load_all(data_dir)])
    print("Reservations:", [r.to_dict() for r in Reservation.load_all(data_dir)])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())