"""
Domain Events Package.

Enthält Event-Definitionen für das Audit Logging System.
"""

from .audit_events import AuditAction, AuditEvent

__all__ = ["AuditAction", "AuditEvent"]
