from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database import Base


class EarningsStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"


class DoctorEarnings(Base):
    __tablename__ = "doctor_earnings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False, index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False, index=True)
    gross_etb: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    fee_percent: Mapped[float] = mapped_column(Float, nullable=False)
    net_etb: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[EarningsStatus] = mapped_column(
        Enum(EarningsStatus), default=EarningsStatus.PENDING, nullable=False
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_by_admin_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped = relationship("Session", back_populates="earnings", lazy="noload")
    doctor: Mapped = relationship("Doctor", back_populates="earnings", lazy="noload")
