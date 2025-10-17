# src/warehouse/infrastructure/database/mappers/base_mapper.py

"""
Einfacher Base Mapper ohne Over-Engineering.
Nur die absolut notwendigen Methoden.
"""

from abc import ABC, abstractmethod
from typing import TypeVar

DomainEntity = TypeVar("DomainEntity")
DatabaseModel = TypeVar("DatabaseModel")


class BaseMapper(ABC):
    """Einfacher Base Mapper für Domain ↔ Database Mapping."""

    @abstractmethod
    def to_domain(self, model: DatabaseModel) -> DomainEntity:
        """Database Model → Domain Entity."""

    @abstractmethod
    def to_model(self, entity: DomainEntity) -> DatabaseModel:
        """Domain Entity → Database Model."""
