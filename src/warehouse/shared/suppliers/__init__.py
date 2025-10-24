"""
Supplier-spezifische Parser-Regeln und Konfigurationen.
"""

from .terrats_medical_parser import TerratsMedicalParser
from .primec_parser import PrimecParser

__all__ = ["TerratsMedicalParser", "PrimecParser"]
