"""
Unit tests for the Reservation System module.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from customer import Customer
from hotel import ConflictError, NotFoundError
from hotel import Hotel
from reservation import Reservation


class ReservationSystemTests(unittest.TestCase):
    """Unit test cases for the reservation system."""

    def setUp(self) -> None:
        """Create a temporary directory and seed JSON files for each test."""
        # In unittest, this pattern is correct: keep the temp dir for the test
        # and register cleanup.
        # pylint: disable=consider-using-with
        self._tmp_dir = TemporaryDirectory()
        self.addCleanup(self._tmp_dir.cleanup)
        self.data_dir = Path(self._tmp_dir.name)

        hotels_path = self.data_dir / "hotels.json"
        customers_path = self.data_dir / "customers.json"
        reservations_path = self.data_dir / "reservations.json"

        hotels_path.write_text(
            json.dumps(
                [
                    {
                        "hotel_id": "H1",
                        "name": "Hotel One",
                        "rooms_total": 5,
                        "rooms_available": 5,
                    }
                ],
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        customers_path.write_text(
            json.dumps(
                [
                    {
                        "customer_id": "C1",
                        "name": "Alice",
                        "email": "alice@example.com",
                    }
                ],
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        reservations_path.write_text(
            "[]\n",
            encoding="utf-8",
        )

    # No tearDown needed: addCleanup already handles it.

    def test_hotel_crud(self) -> None:
        """Hotel: create, display, modify, and delete."""
        created = Hotel.create_hotel(self.data_dir, "H2", "Hotel Two", 3)
        self.assertEqual(created.hotel_id, "H2")

        info = Hotel.display_hotel_information(self.data_dir, "H2")
        self.assertEqual(info["rooms_available"], 3)

        updated = Hotel.modify_hotel_information(
            self.data_dir,
            "H2",
            rooms_available=2,
        )
        self.assertEqual(updated.rooms_available, 2)

        Hotel.delete_hotel(self.data_dir, "H2")
        with self.assertRaises(NotFoundError):
            Hotel.display_hotel_information(self.data_dir, "H2")

    def test_customer_crud(self) -> None:
        """Customer: create, display, modify, and delete."""
        created = Customer.create_customer(
            self.data_dir,
            "C2",
            "Bob",
            "bob@example.com",
        )
        self.assertEqual(created.customer_id, "C2")

        info = Customer.display_customer_information(self.data_dir, "C2")
        self.assertEqual(info["name"], "Bob")

        updated = Customer.modify_customer_information(
            self.data_dir,
            "C2",
            name="Bobby",
        )
        self.assertEqual(updated.name, "Bobby")

        Customer.delete_customer(self.data_dir, "C2")
        with self.assertRaises(NotFoundError):
            Customer.display_customer_information(self.data_dir, "C2")

    def test_reservation_create_and_cancel_updates_inventory(self) -> None:
        """Reservation: create/cancel/ restore availability."""
        before = Hotel.display_hotel_information(
            self.data_dir, "H1"
        )["rooms_available"]

        res = Reservation.create_a_reservation(
            self.data_dir,
            "R1",
            "C1",
            "H1",
            room_count=2,
        )
        self.assertEqual(res.status, "ACTIVE")

        mid = Hotel.display_hotel_information(
            self.data_dir, "H1"
        )["rooms_available"]
        self.assertEqual(mid, before - 2)

        cancelled = Reservation.cancel_a_reservation(self.data_dir, "R1")
        self.assertEqual(cancelled.status, "CANCELLED")

        after = Hotel.display_hotel_information(
            self.data_dir, "H1"
        )["rooms_available"]
        self.assertEqual(after, before)

    def test_conflict_and_not_found_paths(self) -> None:
        """Exercise NotFoundError and ConflictError paths."""
        with self.assertRaises(NotFoundError):
            Hotel.display_hotel_information(self.data_dir, "NOPE")

        with self.assertRaises(NotFoundError):
            Reservation.create_a_reservation(
                self.data_dir,
                "R9",
                "NO_CUST",
                "H1",
                1,
            )

        with self.assertRaises(ConflictError):
            Reservation.create_a_reservation(
                self.data_dir,
                "R2",
                "C1",
                "H1",
                room_count=999,
            )

        _ = Reservation.create_a_reservation(
            self.data_dir,
            "R3",
            "C1",
            "H1",
            room_count=1,
        )

        with self.assertRaises(ConflictError):
            Reservation.create_a_reservation(
                self.data_dir,
                "R3",
                "C1",
                "H1",
                room_count=1,
            )

        _ = Reservation.cancel_a_reservation(self.data_dir, "R3")
        with self.assertRaises(ConflictError):
            Reservation.cancel_a_reservation(self.data_dir, "R3")

    def test_prevent_delete_if_active_reservation(self) -> None:
        """Cannot delete hotel/customer when an active reservation exists."""
        _ = Reservation.create_a_reservation(
            self.data_dir,
            "R10",
            "C1",
            "H1",
            room_count=1,
        )

        with self.assertRaises(ConflictError):
            Hotel.delete_hotel(self.data_dir, "H1")

        with self.assertRaises(ConflictError):
            Customer.delete_customer(self.data_dir, "C1")

    def test_invalid_json_prints_error_and_continues(self) -> None:
        """Invalid JSON should print an error and continue (no crash)."""
        hotels_path = self.data_dir / "hotels.json"
        hotels_path.write_text(
            "{ invalid json",
            encoding="utf-8",
        )

        with patch("builtins.print") as mocked_print:
            hotels = Hotel.load_all(self.data_dir)

        self.assertEqual(hotels, [])
        self.assertTrue(mocked_print.called)

    def test_invalid_rows_are_skipped(self) -> None:
        """Invalid rows should be skipped while valid ones are loaded."""
        customers_path = self.data_dir / "customers.json"
        customers_path.write_text(
            json.dumps(
                [
                    {
                        "customer_id": "C_OK",
                        "name": "Ok",
                        "email": "ok@example.com",
                    },
                    {
                        "customer_id": "C_BAD",
                        "name": "Bad",
                        "email": "not-an-email",
                    },
                ],
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        with patch("builtins.print") as mocked_print:
            customers = Customer.load_all(self.data_dir)

        ids = {c.customer_id for c in customers}
        self.assertIn("C_OK", ids)
        self.assertNotIn("C_BAD", ids)
        self.assertTrue(mocked_print.called)


if __name__ == "__main__":
    unittest.main()
