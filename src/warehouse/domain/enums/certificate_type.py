# src/warehouse/domain/enums/certificate_type.py

from enum import Enum
from typing import List


class CertificateType(Enum):
    """
    Enum für die verschiedenen Zertifikats- und Dokumenttypen
    bei Medizinprodukten im Wareneingang.

    Entspricht den typischen Qualitätsdokumenten, die bei
    medizinischen Implantaten und Instrumenten erforderlich sind.
    """

    # Qualitätszeugnisse
    MATERIALZEUGNIS = "Materialzeugnis"  # 3.1 Zeugnis nach DIN EN 10204
    MESSPROTOKOLL = "Messprotokoll"  # Maßprüfung/Dimensionsprüfung
    HAERTEZEUGNIS = "Härtezeugnis"  # Härteprüfung für metallische Werkstoffe
    BESCHICHTUNGSZEUGNIS = "Beschichtungszeugnis"  # Oberflächenbehandlung/Coating
    WEITERE_ZEUGNISSE = "Weitere Zeugnisse"  # Sonstige spezifische Zeugnisse

    # Produktdokumentation
    ETIKETT = "Etikett/Kennzeichnung"  # Produktkennzeichnung
    BEGLEITSCHEIN = "Begleitschein"  # Interne Begleitdokumentation
    LIEFERSCHEIN = "Lieferschein"  # Lieferantendokumentation

    def get_file_extensions(self) -> List[str]:
        """
        Gibt die typischen Dateierweiterungen für diesen Dokumenttyp zurück.

        Returns:
            Liste der typischen Dateierweiterungen
        """
        extension_mapping = {
            self.MATERIALZEUGNIS: [".pdf"],
            self.MESSPROTOKOLL: [".pdf"],
            self.HAERTEZEUGNIS: [".pdf"],
            self.BESCHICHTUNGSZEUGNIS: [".pdf"],
            self.WEITERE_ZEUGNISSE: [".pdf"],
            self.ETIKETT: [".jpg", ".png", ".pdf"],
            self.BEGLEITSCHEIN: [".pdf", ".docx"],
            self.LIEFERSCHEIN: [".pdf", ".docx"],
        }
        return extension_mapping.get(self.value, [".pdf"])

    def __str__(self) -> str:
        """String-Repräsentation für UI-Anzeige."""
        return self.value
