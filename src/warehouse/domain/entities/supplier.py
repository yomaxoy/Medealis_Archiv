# src/warehouse/domain/entities/supplier.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class Supplier:
    """
    Basic Supplier Entity für das Warehouse Management System.

    Minimale Implementierung mit ID und Name.
    TODO (Iteration 2): Supplier-spezifische Validierung für ArticleNumber/BatchNumber
    """

    supplier_id: str
    name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    notes: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

        # Basis-Validierung
        if not self.supplier_id or not self.supplier_id.strip():
            raise ValueError("Supplier ID ist erforderlich")

        if not self.name or not self.name.strip():
            raise ValueError("Supplier Name ist erforderlich")

        # Normalisierung
        self.supplier_id = self.supplier_id.strip()
        self.name = self.name.strip()

    def update_name(self, new_name: str) -> None:
        """Aktualisiert den Supplier-Namen."""
        if not new_name or not new_name.strip():
            raise ValueError("Supplier Name darf nicht leer sein")

        self.name = new_name.strip()
        if self.updated_at is not None:
            self.updated_at = datetime.now()

    def add_notes(self, notes: str) -> None:
        """Fügt Notizen zum Supplier hinzu."""
        self.notes = notes
        if self.updated_at is not None:
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialisierung für Persistierung."""
        return {
            "supplier_id": self.supplier_id,
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Supplier":
        """Deserialisierung aus Dict."""
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        updated_at = None
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])

        return cls(
            supplier_id=data["supplier_id"],
            name=data["name"],
            created_at=created_at,
            updated_at=updated_at,
            notes=data.get("notes"),
        )

    def __str__(self) -> str:
        """String-Repräsentation für UI-Anzeige."""
        return f"{self.name} ({self.supplier_id})"

    def __repr__(self) -> str:
        """Debug-Repräsentation."""
        return f"Supplier(supplier_id='{self.supplier_id}', name='{self.name}')"
