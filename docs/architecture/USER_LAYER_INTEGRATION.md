# User Layer Integration Guide

## Übersicht

Die User-Layer-Implementierung folgt der Clean Architecture und umfasst:

- **Domain Layer**: User Entity, Value Objects, Repository Interface
- **Application Layer**: UserService mit Business-Logik
- **Infrastructure Layer**: PostgreSQL Repository, Password Hashing, Session Management
- **Presentation Layer**: Login View, User Management

## Schnellstart

### 1. Datenbank-Migration ausführen

```bash
python migration_scripts/06_create_users_table.py
```

Dies erstellt:
- `users` Tabelle mit allen Indices
- Standard-Admin-Benutzer (Username: `admin`, Passwort: `Admin123!`)

### 2. Integration in main.py

```python
import streamlit as st
from warehouse.presentation.auth import (
    show_login_view,
    is_authenticated,
    get_current_user,
    require_authentication,
)

# App-Konfiguration
st.set_page_config(page_title="Medealis Archiv", page_icon="📦")

# Authentifizierung prüfen
if not is_authenticated():
    show_login_view()
    st.stop()

# Eingeloggter User
user = get_current_user()
st.sidebar.write(f"Angemeldet als: {user['username']}")
st.sidebar.write(f"Rolle: {user['role']}")

# Logout-Button
if st.sidebar.button("Abmelden"):
    from warehouse.presentation.auth.login_view import LoginView
    LoginView().logout()

# Hauptanwendung
# ... Ihre bestehende Logik
```

### 3. View mit Berechtigung schützen

```python
from warehouse.presentation.auth import require_permission

@require_permission("delivery.create")
def show_delivery_form():
    st.write("Nur für User mit delivery.create Berechtigung")
    # ... Ihre Logik
```

## Benutzerrollen und Berechtigungen

### Rollen

- **Admin**: Volle Systemberechtigungen
- **Manager**: Verwaltung von Beständen, Bestellungen
- **Operator**: Wareneingänge erfassen, Lieferungen bearbeiten
- **Viewer**: Nur Lesezugriff

### Berechtigungen

Format: `<entity>.<action>`

Beispiele:
- `user.create` - User erstellen
- `delivery.create` - Lieferung erstellen
- `item.read` - Items lesen
- `settings.manage` - Einstellungen verwalten

Siehe `UserRole.permissions` für vollständige Liste.

## User-Management

### User erstellen (Programmatisch)

```python
from warehouse.application.services.user_service import UserService
from warehouse.infrastructure.database.repositories.user_repository_impl import UserRepositoryImpl
from warehouse.domain.enums.user_role import UserRole

user_service = UserService(UserRepositoryImpl())

user = user_service.create_user(
    username="max.mustermann",
    email="max@example.com",
    password="SecurePassword123!",
    role=UserRole.OPERATOR,
    full_name="Max Mustermann",
    created_by="admin_user_id"
)
```

### User-Management UI

```python
from warehouse.presentation.auth import show_user_management_view

# Im Sidebar oder separatem Tab
show_user_management_view()
```

## Authentifizierung

### Programmatisch authentifizieren

```python
from warehouse.application.services.user_service import UserService
from warehouse.infrastructure.database.repositories.user_repository_impl import UserRepositoryImpl
from warehouse.domain.exceptions.user_exceptions import InvalidCredentialsError

user_service = UserService(UserRepositoryImpl())

try:
    user = user_service.authenticate("admin", "Admin123!")
    print(f"Login erfolgreich: {user.username}")
except InvalidCredentialsError:
    print("Ungültige Anmeldedaten")
```

### Session Management

```python
from warehouse.infrastructure.security.session_manager import SessionManager

session_manager = SessionManager(session_timeout_minutes=480)

# Session erstellen
token = session_manager.create_session(
    user_id=user.user_id,
    username=str(user.username),
    role=user.role.value
)

# Session prüfen
session = session_manager.get_session(token)
if session:
    print(f"Session gültig für: {session['username']}")

# Session beenden
session_manager.invalidate_session(token)
```

## Passwort-Management

### Passwort ändern

```python
user_service.change_password(
    user_id=user.user_id,
    old_password="OldPassword123!",
    new_password="NewPassword456!"
)
```

### Passwort zurücksetzen (Admin)

```python
user_service.reset_password(
    user_id=target_user_id,
    new_password="TemporaryPassword123!",
    actor_user_id=admin_user_id
)
```

## Berechtigungsprüfung

### In Views

```python
from warehouse.presentation.auth import get_current_user
from warehouse.domain.enums.user_role import UserRole

user = get_current_user()
role = UserRole(user['role'])

if role.has_permission("delivery.delete"):
    st.button("Lieferung löschen")
else:
    st.info("Keine Berechtigung zum Löschen")
```

### Im Service

```python
from warehouse.domain.exceptions.user_exceptions import InsufficientPermissionsError

def delete_delivery(delivery_id: str, user_id: str):
    user = user_service.get_user_by_id(user_id)

    if not user.has_permission("delivery.delete"):
        raise InsufficientPermissionsError("delivery.delete")

    # ... Logik
```

## Architektur

```
src/warehouse/
├── domain/
│   ├── entities/user.py              # User Entity
│   ├── value_objects/
│   │   ├── email.py                  # Email Value Object
│   │   └── username.py               # Username Value Object
│   ├── enums/user_role.py            # Rollen & Berechtigungen
│   ├── repositories/user_repository.py # Repository Interface
│   └── exceptions/user_exceptions.py  # User-spezifische Exceptions
│
├── application/
│   └── services/user_service.py      # User Business-Logik
│
├── infrastructure/
│   ├── database/
│   │   ├── models/user_model.py      # SQLAlchemy Model
│   │   └── repositories/
│   │       └── user_repository_impl.py # Repository Implementation
│   └── security/
│       ├── password_hasher.py        # Bcrypt Password Hashing
│       └── session_manager.py        # Session Management
│
└── presentation/auth/
    ├── login_view.py                 # Login UI
    └── user_management_view.py       # User-Management UI
```

## Sicherheit

### Passwort-Anforderungen

- Mindestens 8 Zeichen
- Groß- und Kleinbuchstaben
- Mindestens eine Zahl
- Maximal 128 Zeichen

### Password Hashing

- Bcrypt mit 12 Runden
- Automatisches Salting
- Timing-Attack-Schutz bei Authentifizierung

### Sessions

- Secure random token (32 Bytes URL-safe)
- Konfigurierbarer Timeout (Default: 8 Stunden)
- Automatische Cleanup-Funktion

## Best Practices

1. **Standard-Admin-Passwort sofort ändern** nach erster Installation
2. **require_authentication Decorator** für alle geschützten Views verwenden
3. **Berechtigungen granular prüfen** statt nur Rollen
4. **Sessions regelmäßig cleanen** für Performance
5. **User-Actions loggen** für Audit Trail
6. **Passwörter niemals loggen** oder im Klartext speichern

## Troubleshooting

### Migration schlägt fehl

```bash
# Prüfe Datenbankverbindung
python -c "from warehouse.infrastructure.database.connection import get_session; get_session()"

# Prüfe ob Tabelle bereits existiert
psql -d medealis -c "SELECT * FROM users LIMIT 1;"
```

### Login funktioniert nicht

```python
# Test Password Hasher
from warehouse.infrastructure.security.password_hasher import PasswordHasher
hasher = PasswordHasher()
hash = hasher.hash_password("Admin123!")
print(hasher.verify_password("Admin123!", hash))  # Sollte True sein
```

### Session-Probleme

```python
# Session-Status prüfen
import streamlit as st
print("auth_token" in st.session_state)
print("current_user" in st.session_state)
```

## Migration

Falls Sie ein bestehendes User-System migrieren:

1. Exportieren Sie bestehende User-Daten
2. Hashen Sie Passwörter mit `PasswordHasher.hash_password()`
3. Mappen Sie Rollen zu `UserRole` Enum
4. Importieren Sie mit `UserService.create_user()`

## Erweiterungen

### Eigene Berechtigungen hinzufügen

In `UserRole.permissions`:

```python
UserRole.CUSTOM: {
    "custom.permission",
    "another.permission"
}
```

### Audit Logging integrieren

```python
from warehouse.domain.events.audit_events import UserLoginEvent

user = user_service.authenticate(username, password)
# Publish event für Audit Log
```
