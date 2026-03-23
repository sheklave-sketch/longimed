from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.database import Base


class SubscriptionPlan(str, enum.Enum):
    BASIC = "basic"       # $10/month
    FAMILY = "family"     # $25/month
    SENIOR = "senior"     # $40/month


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"


class Subscription(Base):
    """Phase II — diaspora gift subscriptions via Stripe."""
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    diaspora_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    diaspora_email: Mapped[str] = mapped_column(String(255), nullable=False)
    beneficiary_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    plan: Mapped[SubscriptionPlan] = mapped_column(Enum(SubscriptionPlan), nullable=False)
    sessions_per_month: Mapped[int] = mapped_column(Integer, nullable=False)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False
    )
    next_billing_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
