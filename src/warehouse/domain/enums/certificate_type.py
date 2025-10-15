# src/warehouse/domain/enums/certificate_type.py

from enum import Enum
from typing import List, Optional


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

    @classmethod
    def from_form_key(cls, form_key: str) -> Optional['CertificateType']:
        """
        Mapped Form-Keys (deutsch oder englisch) zu CertificateType Enum.

        Diese Methode ermöglicht eine zentrale, typsichere Konvertierung von
        Formular-Feldnamen zu Domain-Enum-Werten. Unterstützt sowohl deutsche
        Keys (UI) als auch englische Keys (DB-Felder) für Kompatibilität.

        Args:
            form_key: Key aus Formulardaten (z.B. 'materialzeugnis', 'messprotokolle')
                     oder DB-Feldname (z.B. 'material_certificate', 'measurement_protocol')

        Returns:
            CertificateType Enum-Member oder None wenn Key unbekannt

        Beispiel:
            >>> CertificateType.from_form_key('materialzeugnis')
            <CertificateType.MATERIALZEUGNIS: 'Materialzeugnis'>
            >>> CertificateType.from_form_key('material_certificate')
            <CertificateType.MATERIALZEUGNIS: 'Materialzeugnis'>
        """
        mapping = {
            # Deutsche Form-Keys (UI)
            'materialzeugnis': cls.MATERIALZEUGNIS,
            'messprotokolle': cls.MESSPROTOKOLL,
            'messprotokoll': cls.MESSPROTOKOLL,
            'haertezeugnis': cls.HAERTEZEUGNIS,
            'härtezeugnis': cls.HAERTEZEUGNIS,  # Mit Umlaut
            'beschichtungszeugnis': cls.BESCHICHTUNGSZEUGNIS,
            'weitere_zeugnisse': cls.WEITERE_ZEUGNISSE,
            'etikett': cls.ETIKETT,
            'begleitschein': cls.BEGLEITSCHEIN,
            'lieferschein': cls.LIEFERSCHEIN,

            # Englische DB-Feldnamen (für Kompatibilität)
            'material_certificate': cls.MATERIALZEUGNIS,
            'measurement_protocol': cls.MESSPROTOKOLL,
            'hardness_certificate': cls.HAERTEZEUGNIS,
            'coating_certificate': cls.BESCHICHTUNGSZEUGNIS,
            'additional_certificates': cls.WEITERE_ZEUGNISSE,
            'label': cls.ETIKETT,
            'accompanying_document': cls.BEGLEITSCHEIN,
            'delivery_slip': cls.LIEFERSCHEIN,
        }
        return mapping.get(form_key.lower())

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
