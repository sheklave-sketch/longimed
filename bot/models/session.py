from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database import Base


class SessionPackage(str, enum.Enum):
    FREE_TRIAL = "free_trial"
    SINGLE = "single"
    CUSTOM = "custom"


class SessionStatus(str, enum.Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    AWAITING_DOCTOR = "awaiting_doctor"
    ACTIVE = "active"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class SessionMode(str, enum.Enum):
    RELAY = "relay"    # anonymous — bot forwards messages
    TOPIC = "topic"    # non-anonymous — forum thread in supergroup


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    doctor_id: Mapped[int | None] = mapped_column(ForeignKey("doctors.id"), nullable=True, index=True)
    package: Mapped[SessionPackage] = mapped_column(Enum(SessionPackage), nullable=False)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus), default=SessionStatus.PENDING_APPROVAL, nullable=False, index=True
    )
    session_mode: Mapped[SessionMode] = mapped_column(Enum(SessionMode), nullable=False)
    issue_description: Mapped[str] = mapped_column(Text, nullable=False)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # For TOPIC mode: forum thread in supergroup
    topic_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    group_chat_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Resolution
    resolution_confirmed_by_doctor: Mapped[bool] = mapped_column(Boolean, default=False)
    resolution_confirmed_by_patient: Mapped[bool] = mapped_column(Boolean, default=False)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    payment_id: Mapped[int | None] = mapped_column(ForeignKey("payments.id"), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped = relationship("User", back_populates="sessions", lazy="noload")
    doctor: Mapped = relationship("Doctor", back_populates="sessions", lazy="noload")
    relay_messages: Mapped[list] = relationship("RelayMessage", back_populates="session", lazy="noload")
    earnings: Mapped[list] = relationship("DoctorEarnings", back_populates="session", lazy="noload")
