# src/warehouse/domain/events/base_event.py

"""
Base Domain Event für das Warehouse Management System.

Definiert die Grundstruktur für alle Domain Events im System.
Alle spezifischen Events erben von BaseDomainEvent.
"""

import uuid
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class BaseDomainEvent(ABC):
    """
    Abstrakte Basis-Klasse für alle Domain Events.

    Stellt gemeinsame Eigenschaften und Funktionalität für alle
    Events im Warehouse Management System bereit.
    """

    # === CORE EVENT PROPERTIES ===

    timestamp: datetime = field(default_factory=datetime.now)
    """Zeitpunkt wann das Event aufgetreten ist."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    """Eindeutige ID für dieses Event."""

    entity_type: str = ""
    """Typ der Entity die das Event ausgelöst hat (z.B. 'Item', 'Delivery')."""

    entity_id: str = ""
    """Eindeutige ID der Entity die das Event ausgelöst hat."""

    # === OPTIONAL METADATA ===

    correlation_id: Optional[str] = None
    """Korrelations-ID um zusammengehörige Events zu verknüpfen."""

    causation_id: Optional[str] = None
    """ID des Events das dieses Event verursacht hat."""

    version: int = 1
    """Event-Schema Version für Evolution."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Zusätzliche Metadaten für Event-Handling."""

    # === UTILITY PROPERTIES ===

    @property
    def event_name(self) -> str:
        """
        Gibt den Namen des Events zurück basierend auf der Klasse.

        Returns:
            Event-Name (z.B. 'ItemCreatedEvent')
        """
        return self.__class__.__name__

    @property
    def event_type(self) -> str:
        """
        Gibt den Event-Typ ohne 'Event' Suffix zurück.

        Returns:
            Event-Typ (z.B. 'ItemCreated')
        """
        name = self.event_name
        if name.endswith("Event"):
            return name[:-5]
        return name

    @property
    def age_seconds(self) -> float:
        """
        Berechnet das Alter des Events in Sekunden.

        Returns:
            Sekunden seit Event-Erstellung
        """
        return (datetime.now() - self.timestamp).total_seconds()

    @property
    def is_recent(self, threshold_seconds: int = 60) -> bool:
        """
        Prüft ob Event "recent" ist (jünger als Schwellenwert).

        Args:
            threshold_seconds: Schwellenwert in Sekunden (default: 60)

        Returns:
            True wenn Event jünger als Schwellenwert
        """
        return self.age_seconds <= threshold_seconds

    # === SERIALIZATION METHODS ===

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialisiert Event zu Dictionary für Persistierung oder Transport.

        Returns:
            Dictionary-Repräsentation des Events
        """
        result = {
            "event_name": self.event_name,
            "event_type": self.event_type,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "version": self.version,
        }

        # Optionale Felder nur wenn gesetzt
        if self.correlation_id:
            result["correlation_id"] = self.correlation_id

        if self.causation_id:
            result["causation_id"] = self.causation_id

        if self.metadata:
            result["metadata"] = self.metadata

        return result

    def to_json_string(self) -> str:
        """
        Serialisiert Event zu JSON-String.

        Returns:
            JSON-String-Repräsentation des Events
        """
        import json

        return json.dumps(self.to_dict(), default=str, ensure_ascii=False)

    # === CORRELATION & CAUSATION ===

    def with_correlation_id(self, correlation_id: str) -> "BaseDomainEvent":
        """
        Setzt Korrelations-ID für Event-Verkettung.

        Args:
            correlation_id: Korrelations-ID

        Returns:
            Self für Method-Chaining
        """
        self.correlation_id = correlation_id
        return self

    def with_causation_id(self, causation_id: str) -> "BaseDomainEvent":
        """
        Setzt Causation-ID für Event-Kausality.

        Args:
            causation_id: ID des verursachenden Events

        Returns:
            Self für Method-Chaining
        """
        self.causation_id = causation_id
        return self

    def add_metadata(self, key: str, value: Any) -> "BaseDomainEvent":
        """
        Fügt Metadaten zum Event hinzu.

        Args:
            key: Metadaten-Schlüssel
            value: Metadaten-Wert

        Returns:
            Self für Method-Chaining
        """
        self.metadata[key] = value
        return self

    # === UTILITY METHODS ===

    def __str__(self) -> str:
        """String-Repräsentation für Logging und Debugging."""
        return f"{self.event_name}(id={self.event_id[:8]}, entity={self.entity_type}:{self.entity_id}, timestamp={self.timestamp.strftime('%Y-%m-%d %H:%M:%S')})"

    def __repr__(self) -> str:
        """Debug-Repräsentation des Events."""
        return f"{self.event_name}(event_id='{self.event_id}', entity_type='{self.entity_type}', entity_id='{self.entity_id}', timestamp='{self.timestamp.isoformat()}')"
