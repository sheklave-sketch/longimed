from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Enum, Float, Integer, String, Text, func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database import Base


class Specialty(str, enum.Enum):
    GENERAL = "general"
    PEDIATRICS = "pediatrics"
    OBGYN = "obgyn"
    DERMATOLOGY = "dermatology"
    MENTAL_HEALTH = "mental_health"
    CARDIOLOGY = "cardiology"
    OTHER = "other"


class RegistrationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    license_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    specialty: Mapped[Specialty] = mapped_column(Enum(Specialty, values_callable=lambda e: [x.value for x in e]), nullable=False)
    languages: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    registration_status: Mapped[RegistrationStatus] = mapped_column(
        Enum(RegistrationStatus, values_callable=lambda e: [x.value for x in e]), default=RegistrationStatus.PENDING, nullable=False
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    license_document_file_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    max_concurrent_patients: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    rating_avg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rating_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    availability_schedule: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    sessions: Mapped[list] = relationship("Session", back_populates="doctor", lazy="noload")
    earnings: Mapped[list] = relationship("DoctorEarnings", back_populates="doctor", lazy="noload")

    def __repr__(self) -> str:
        return f"<Doctor {self.full_name} specialty={self.specialty.value}>"
