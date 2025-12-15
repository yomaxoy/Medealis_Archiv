# src/warehouse/infrastructure/security/session_manager.py

from typing import Optional
from datetime import datetime, timedelta
import secrets


class SessionManager:
    """
    Einfache Session-Verwaltung für die Anwendung.

    Verwendet In-Memory-Storage für Sessions (für Desktop-Anwendung ausreichend).
    """

    def __init__(self, session_timeout_minutes: int = 480):  # 8 Stunden Default
        self._sessions: dict[str, dict] = {}
        self._session_timeout = timedelta(minutes=session_timeout_minutes)

    def create_session(self, user_id: str, username: str, role: str) -> str:
        """
        Erstellt eine neue Session.

        Args:
            user_id: User ID
            username: Benutzername
            role: Benutzerrolle

        Returns:
            Session Token
        """
        token = secrets.token_urlsafe(32)
        self._sessions[token] = {
            "user_id": user_id,
            "username": username,
            "role": role,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
        }
        return token

    def get_session(self, token: str) -> Optional[dict]:
        """
        Gibt Session-Daten zurück wenn gültig.

        Args:
            token: Session Token

        Returns:
            Session-Daten oder None
        """
        if token not in self._sessions:
            return None

        session = self._sessions[token]

        # Prüfe Timeout
        if datetime.now() - session["last_activity"] > self._session_timeout:
            self.invalidate_session(token)
            return None

        # Aktualisiere letzte Aktivität
        session["last_activity"] = datetime.now()
        return session

    def invalidate_session(self, token: str) -> None:
        """Löscht eine Session."""
        self._sessions.pop(token, None)

    def invalidate_user_sessions(self, user_id: str) -> None:
        """Löscht alle Sessions eines Users."""
        tokens_to_remove = [
            token
            for token, session in self._sessions.items()
            if session["user_id"] == user_id
        ]
        for token in tokens_to_remove:
            self._sessions.pop(token)

    def cleanup_expired_sessions(self) -> int:
        """
        Entfernt abgelaufene Sessions.

        Returns:
            Anzahl entfernter Sessions
        """
        now = datetime.now()
        expired_tokens = [
            token
            for token, session in self._sessions.items()
            if now - session["last_activity"] > self._session_timeout
        ]

        for token in expired_tokens:
            self._sessions.pop(token)

        return len(expired_tokens)

    def get_active_sessions_count(self) -> int:
        """Gibt Anzahl aktiver Sessions zurück."""
        return len(self._sessions)
