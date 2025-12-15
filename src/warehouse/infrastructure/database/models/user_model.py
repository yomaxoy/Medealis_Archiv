# src/warehouse/infrastructure/database/models/user_model.py

from sqlalchemy import Column, String, Boolean, DateTime
from datetime import datetime

from warehouse.infrastructure.database.connection import Base


class UserModel(Base):
    """SQLAlchemy Model für User-Tabelle."""

    __tablename__ = "users"

    user_id = Column(String(50), primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )
    created_by = Column(String(50), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<UserModel(user_id='{self.user_id}', "
            f"username='{self.username}', role='{self.role}')>"
        )
