# src/warehouse/domain/value_objects/batch_number.py

from dataclasses import dataclass


@dataclass(frozen=True)
class BatchNumber:
    """19-stellige Chargennummer (z.B. P-293520240528)."""

    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("Chargennummer darf nicht leer sein")
        
        # Strikte Validierung nur für vollständige P-Format Nummern
        # Erlaube auch einfachere Formate beim Import (ohne strikte Validation)
        if self.value.startswith("P-") and "-" in self.value[2:]:
            # Nur validieren wenn es das vollständige P-Format zu sein scheint
            parts = self.value.split("-")
            if len(parts) == 3:
                # Vollständige Validierung nur wenn alle Teile numerisch sind
                if parts[1].isdigit() and parts[2].isdigit():
                    # Prüfe ersten Teil (12 Ziffern nach P-)
                    if len(parts[1]) != 12:
                        raise ValueError("Nach 'P-' müssen genau 12 Ziffern folgen")
                    
                    # Prüfe zweiten Teil (4 oder 5 Ziffern)
                    if len(parts[2]) not in [4, 5]:
                        raise ValueError("Nach dem zweiten Bindestrich müssen 4 oder 5 Ziffern folgen")
        
        # Für alle anderen Formate: Nur grundlegende Validierung
        # (nicht leer, keine gefährlichen Zeichen)
        if len(self.value.strip()) != len(self.value):
            raise ValueError("Chargennummer darf keine führenden/nachfolgenden Leerzeichen haben")
    
    def is_complete_format(self) -> bool:
        """Prüft ob die Chargennummer das vollständige P-XXXXXXXXXXXX-XXXX Format hat"""
        if not self.value.startswith("P-"):
            return False
        
        parts = self.value.split("-")
        if len(parts) != 3:
            return False
        
        # Prüfe Format
        return (len(parts[1]) == 12 and parts[1].isdigit() and 
                len(parts[2]) in [4, 5] and parts[2].isdigit())
    
    def needs_completion(self) -> bool:
        """Prüft ob die Chargennummer noch vervollständigt werden muss"""
        return not self.is_complete_format()

    def __str__(self) -> str:
        return self.value
