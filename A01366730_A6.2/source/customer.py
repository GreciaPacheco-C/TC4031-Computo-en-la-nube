"""
Customer class + persistent behaviors (stored in files).

Req 2.2:
- Create/Delete/Display/Modify Customer
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional,TYPE_CHECKING

from storage import JsonStore
from hotel import ConflictError, NotFoundError

if TYPE_CHECKING:
    from reservation import Reservation

@dataclass(frozen=True)
class Customer:
    """Represents a customer."""
    customer_id: str
    name: str
    email: str

    @staticmethod
    def _store(data_dir: Path) -> JsonStore:
        return JsonStore(data_dir / "customers.json")

    @staticmethod
    def _from_dict(row: Dict[str, Any]) -> "Customer":
        customer_id = str(row["customer_id"])
        name = str(row["name"])
        email = str(row["email"])

        if "@" not in email or email.startswith("@") or email.endswith("@"):
            raise ValueError("Invalid email format.")

        return Customer(customer_id=customer_id, name=name, email=email)

    def to_dict(self) -> Dict[str, Any]:
        """Return a dic representation of customer"""
        return {
            "customer_id": self.customer_id,
            "name": self.name,
            "email": self.email
            }

    @classmethod
    def load_all(cls, data_dir: Path) -> List["Customer"]:
        """Load all customers from storage"""
        rows = cls._store(data_dir).load_list()
        customers: List[Customer] = []
        for idx, row in enumerate(rows):
            try:
                customers.append(cls._from_dict(row))
            except (KeyError, TypeError, ValueError) as exc:
                print(
                    f"[ERROR] Invalid customer record #{idx}:"
                    f"{exc}. Skipped."
                )
        return customers

    @classmethod
    def _save_all(cls, data_dir: Path, customers: List["Customer"]) -> None:
        cls._store(data_dir).save_list([c.to_dict() for c in customers])

    @classmethod
    def create_customer(
        cls, data_dir: Path, customer_id: str,
        name: str, email: str,
    ) -> "Customer":
        """Creates new costumer"""
        customer = cls._from_dict(
            {"customer_id": customer_id,
             "name": name,
             "email": email}
        )
        customers = cls.load_all(data_dir)
        if any(c.customer_id == customer.customer_id for c in customers):
            raise ConflictError(
                f"Customer already exists:"
                f" {customer.customer_id}"
            )
        customers.append(customer)
        cls._save_all(data_dir, customers)
        return customer

    @classmethod
    def delete_customer(cls, data_dir: Path, customer_id: str) -> None:
        """Delete a customer by ID."""
        customers = cls.load_all(data_dir)
        if not any(c.customer_id == customer_id for c in customers):
            raise NotFoundError(f"Customer not found: {customer_id}")

        from reservation import Reservation  # pylint: disable=import-outside-toplevel

        if Reservation.has_active_for_customer(data_dir, customer_id):
            raise ConflictError(
                "Cannot delete customer with active reservations."
            )

        customers = [c for c in customers if c.customer_id != customer_id]
        cls._save_all(data_dir, customers)

    @classmethod
    def display_customer_information(
        cls, data_dir: Path, customer_id: str
    ) -> Dict[str, Any]:
        """Loads customer information"""
        customers = cls.load_all(data_dir)
        for c in customers:
            if c.customer_id == customer_id:
                return c.to_dict()
        raise NotFoundError(f"Customer not found: {customer_id}")

    @classmethod
    def modify_customer_information(
        cls,
        data_dir: Path,
        customer_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> "Customer":
        """Aux to modify customer info"""
        customers = cls.load_all(data_dir)
        updated: List[Customer] = []
        found = False

        for c in customers:
            if c.customer_id != customer_id:
                updated.append(c)
                continue

            found = True
            new_customer = cls._from_dict(
                {
                    "customer_id": c.customer_id,
                    "name": c.name if name is None else str(name),
                    "email": c.email if email is None else str(email),
                }
            )
            updated.append(new_customer)

        if not found:
            raise NotFoundError(f"Customer not found: {customer_id}")

        cls._save_all(data_dir, updated)
        return next(c for c in updated if c.customer_id == customer_id)
