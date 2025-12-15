# src/warehouse/infrastructure/security/password_hasher.py

import bcrypt
from typing import Optional


class PasswordHasher:
    """
    Sichere Passwort-Hash-Verwaltung mit bcrypt.

    Verwendet bcrypt mit automatischem Salting für maximale Sicherheit.
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Erstellt einen sicheren Hash aus dem Passwort.

        Args:
            password: Klartext-Passwort

        Returns:
            Bcrypt-Hash als String

        Raises:
            ValueError: Wenn Passwort leer ist
        """
        if not password or not password.strip():
            raise ValueError("Passwort darf nicht leer sein")

        # Bcrypt mit 12 Runden (guter Balance zwischen Sicherheit und Performance)
        salt = bcrypt.gensalt(rounds=12)
        password_bytes = password.encode("utf-8")
        hash_bytes = bcrypt.hashpw(password_bytes, salt)

        return hash_bytes.decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verifiziert ein Passwort gegen einen Hash.

        Args:
            password: Klartext-Passwort
            password_hash: Gespeicherter Hash

        Returns:
            True wenn Passwort korrekt, sonst False
        """
        if not password or not password_hash:
            return False

        try:
            password_bytes = password.encode("utf-8")
            hash_bytes = password_hash.encode("utf-8")
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception:
            return False

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
        """
        Validiert Passwort-Stärke.

        Args:
            password: Zu prüfendes Passwort

        Returns:
            Tuple (is_valid, error_message)
        """
        if not password:
            return False, "Passwort darf nicht leer sein"

        if len(password) < 8:
            return False, "Passwort muss mindestens 8 Zeichen lang sein"

        if len(password) > 128:
            return False, "Passwort darf maximal 128 Zeichen lang sein"

        # Mindestens ein Großbuchstabe, ein Kleinbuchstabe und eine Zahl
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)

        if not (has_upper and has_lower and has_digit):
            return False, "Passwort muss Groß-, Kleinbuchstaben und Zahlen enthalten"

        return True, None
