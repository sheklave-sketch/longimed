from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.database import Base


class TargetType(str, enum.Enum):
    DOCTOR = "doctor"
    PATIENT = "patient"
    QUESTION = "question"
    ANSWER = "answer"


class ReportStatus(str, enum.Enum):
    OPEN = "open"
    DISMISSED = "dismissed"
    WARNED = "warned"
    SUSPENDED = "suspended"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    target_type: Mapped[TargetType] = mapped_column(Enum(TargetType, values_callable=lambda e: [x.value for x in e]), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    evidence_file_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, values_callable=lambda e: [x.value for x in e]), default=ReportStatus.OPEN, nullable=False, index=True
    )
    reviewed_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
