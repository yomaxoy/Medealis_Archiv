# src/warehouse/infrastructure/security/login_rate_limiter.py

"""
Login Rate Limiter — Brute-Force-Schutz für Login-Versuche.

Sperrt einen Benutzernamen nach zu vielen fehlgeschlagenen Login-Versuchen
für eine konfigurierbare Zeitspanne.

Limitierungen:
    - In-Memory: Bei Container/Prozess-Restart wird der Zähler zurückgesetzt.
    - Für Produktionsumgebung mittelfristig auf Redis/DB-basiert umstellen.
"""

import logging
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict

logger = logging.getLogger(__name__)

# Konfiguration
MAX_ATTEMPTS = 5  # Max fehlgeschlagene Versuche
LOCKOUT_DURATION_MINUTES = 15  # Sperrzeit in Minuten
CLEANUP_THRESHOLD = 100  # Cleanup ab dieser Anzahl Einträge


@dataclass
class LoginAttemptRecord:
    """Speichert fehlgeschlagene Login-Versuche für einen Benutzernamen."""

    failed_attempts: int = 0
    locked_until: datetime = field(default_factory=lambda: datetime.min)
    last_attempt: datetime = field(default_factory=datetime.now)


class LoginRateLimiter:
    """
    Rate Limiter für Login-Versuche (In-Memory).

    Thread-safe durch Lock.
    """

    def __init__(
        self,
        max_attempts: int = MAX_ATTEMPTS,
        lockout_minutes: int = LOCKOUT_DURATION_MINUTES,
    ):
        self._max_attempts = max_attempts
        self._lockout_duration = timedelta(minutes=lockout_minutes)
        self._attempts: Dict[str, LoginAttemptRecord] = {}
        self._lock = threading.Lock()

    def is_locked(self, username: str) -> bool:
        """Prüft ob ein Benutzername gesperrt ist."""
        with self._lock:
            record = self._attempts.get(username)
            if not record:
                return False

            if record.locked_until > datetime.now():
                return True

            # Sperre abgelaufen — Zähler zurücksetzen
            if record.locked_until != datetime.min:
                record.failed_attempts = 0
                record.locked_until = datetime.min

            return False

    def get_remaining_lockout_seconds(self, username: str) -> int:
        """Gibt die verbleibende Sperrzeit in Sekunden zurück (0 wenn nicht gesperrt)."""
        with self._lock:
            record = self._attempts.get(username)
            if not record:
                return 0

            remaining = (record.locked_until - datetime.now()).total_seconds()
            return max(0, int(remaining))

    def record_failed_attempt(self, username: str) -> bool:
        """
        Registriert einen fehlgeschlagenen Login-Versuch.

        Returns:
            True wenn der Account jetzt gesperrt wurde
        """
        with self._lock:
            if username not in self._attempts:
                self._attempts[username] = LoginAttemptRecord()

            record = self._attempts[username]
            record.failed_attempts += 1
            record.last_attempt = datetime.now()

            if record.failed_attempts >= self._max_attempts:
                record.locked_until = datetime.now() + self._lockout_duration
                logger.warning(
                    f"Account gesperrt wegen zu vieler Fehlversuche: {username} "
                    f"({record.failed_attempts} Versuche, "
                    f"gesperrt bis {record.locked_until.strftime('%H:%M:%S')})"
                )
                return True

            logger.info(
                f"Fehlgeschlagener Login-Versuch für {username}: "
                f"{record.failed_attempts}/{self._max_attempts}"
            )

            # Periodisches Cleanup
            if len(self._attempts) > CLEANUP_THRESHOLD:
                self._cleanup_expired()

            return False

    def record_successful_login(self, username: str) -> None:
        """Setzt den Zähler nach erfolgreichem Login zurück."""
        with self._lock:
            if username in self._attempts:
                del self._attempts[username]

    def _cleanup_expired(self) -> None:
        """Entfernt abgelaufene Einträge (bereits innerhalb Lock aufgerufen)."""
        now = datetime.now()
        expired = [
            username
            for username, record in self._attempts.items()
            if record.locked_until != datetime.min
            and record.locked_until < now
            and (now - record.last_attempt).total_seconds() > 3600
        ]
        for username in expired:
            del self._attempts[username]


# Singleton-Instanz (wiederverwendbar über die gesamte Applikation)
_rate_limiter_instance = None
_instance_lock = threading.Lock()


def get_login_rate_limiter() -> LoginRateLimiter:
    """Gibt die Singleton-Instanz des LoginRateLimiters zurück."""
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        with _instance_lock:
            if _rate_limiter_instance is None:
                _rate_limiter_instance = LoginRateLimiter()
    return _rate_limiter_instance
