"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-23

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("language", sa.String(2), nullable=False, server_default="en"),
        sa.Column("consent_given", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("consent_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("free_trial_used", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("warning_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
        sa.UniqueConstraint("phone"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])

    # ── doctors ──────────────────────────────────────────────────────────
    specialty_enum = postgresql.ENUM(
        "general", "pediatrics", "obgyn", "dermatology", "mental_health", "cardiology", "other",
        name="specialty"
    )
    reg_status_enum = postgresql.ENUM("pending", "approved", "rejected", name="registrationstatus")

    op.create_table(
        "doctors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("license_number", sa.String(100), nullable=False),
        sa.Column("specialty", specialty_enum, nullable=False),
        sa.Column("languages", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("registration_status", reg_status_enum, nullable=False, server_default="pending"),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("license_document_file_id", sa.String(200), nullable=True),
        sa.Column("max_concurrent_patients", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("rating_avg", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("rating_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
        sa.UniqueConstraint("license_number"),
    )
    op.create_index("ix_doctors_telegram_id", "doctors", ["telegram_id"])

    # ── moderators ───────────────────────────────────────────────────────
    op.create_table(
        "moderators",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("assigned_specialties", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("added_by_admin_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index("ix_moderators_telegram_id", "moderators", ["telegram_id"])

    # ── questions ────────────────────────────────────────────────────────
    question_status_enum = postgresql.ENUM(
        "pending", "approved", "rejected", "answered", name="questionstatus"
    )
    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("category", specialty_enum, nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("is_anonymous", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", question_status_enum, nullable=False, server_default="pending"),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("channel_message_id", sa.BigInteger(), nullable=True),
        sa.Column("moderator_id", sa.Integer(), sa.ForeignKey("moderators.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_questions_user_id", "questions", ["user_id"])
    op.create_index("ix_questions_status", "questions", ["status"])

    # ── follow_ups ───────────────────────────────────────────────────────
    follow_up_status_enum = postgresql.ENUM("pending", "approved", "rejected", name="followupstatus")
    op.create_table(
        "follow_ups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("is_anonymous", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", follow_up_status_enum, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_follow_ups_question_id", "follow_ups", ["question_id"])

    # ── payments ─────────────────────────────────────────────────────────
    payment_provider_enum = postgresql.ENUM("manual", "chapa", "stripe", name="paymentprovider")
    payment_status_enum = postgresql.ENUM("pending", "completed", "failed", "refunded", name="paymentstatus")
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount_etb", sa.Numeric(10, 2), nullable=True),
        sa.Column("provider", payment_provider_enum, nullable=False, server_default="manual"),
        sa.Column("provider_tx_id", sa.String(200), nullable=True),
        sa.Column("status", payment_status_enum, nullable=False, server_default="pending"),
        sa.Column("confirmed_by_admin_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payments_user_id", "payments", ["user_id"])
    op.create_index("ix_payments_status", "payments", ["status"])

    # ── sessions ─────────────────────────────────────────────────────────
    session_package_enum = postgresql.ENUM("free_trial", "single", "custom", name="sessionpackage")
    session_status_enum = postgresql.ENUM(
        "pending_approval", "approved", "awaiting_doctor", "active",
        "resolved", "cancelled", "expired", name="sessionstatus"
    )
    session_mode_enum = postgresql.ENUM("relay", "topic", name="sessionmode")
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("doctors.id"), nullable=True),
        sa.Column("package", session_package_enum, nullable=False),
        sa.Column("status", session_status_enum, nullable=False, server_default="pending_approval"),
        sa.Column("session_mode", session_mode_enum, nullable=False),
        sa.Column("issue_description", sa.Text(), nullable=False),
        sa.Column("is_anonymous", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("topic_id", sa.Integer(), nullable=True),
        sa.Column("group_chat_id", sa.Integer(), nullable=True),
        sa.Column("resolution_confirmed_by_doctor", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("resolution_confirmed_by_patient", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("rating_comment", sa.Text(), nullable=True),
        sa.Column("payment_id", sa.Integer(), sa.ForeignKey("payments.id"), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_doctor_id", "sessions", ["doctor_id"])
    op.create_index("ix_sessions_status", "sessions", ["status"])

    # ── relay_messages ───────────────────────────────────────────────────
    sender_role_enum = postgresql.ENUM("patient", "doctor", name="senderrole")
    op.create_table(
        "relay_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("sender_role", sender_role_enum, nullable=False),
        sa.Column("telegram_message_id", sa.BigInteger(), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("media_type", sa.String(50), nullable=True),
        sa.Column("media_file_id", sa.String(200), nullable=True),
        sa.Column("forwarded_message_id", sa.BigInteger(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_relay_messages_session_id", "relay_messages", ["session_id"])

    # ── notifications ────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("payload", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    # ── waitlist ─────────────────────────────────────────────────────────
    waitlist_status_enum = postgresql.ENUM(
        "waiting", "notified", "accepted", "expired", "left", name="waitliststatus"
    )
    op.create_table(
        "waitlist",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("doctors.id"), nullable=True),
        sa.Column("specialty", sa.String(50), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("status", waitlist_status_enum, nullable=False, server_default="waiting"),
        sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── doctor_earnings ──────────────────────────────────────────────────
    earnings_status_enum = postgresql.ENUM("pending", "paid", name="earningsstatus")
    op.create_table(
        "doctor_earnings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("doctors.id"), nullable=False),
        sa.Column("gross_etb", sa.Numeric(10, 2), nullable=False),
        sa.Column("fee_percent", sa.Float(), nullable=False),
        sa.Column("net_etb", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", earnings_status_enum, nullable=False, server_default="pending"),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_by_admin_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_doctor_earnings_session_id", "doctor_earnings", ["session_id"])
    op.create_index("ix_doctor_earnings_doctor_id", "doctor_earnings", ["doctor_id"])

    # ── reports ──────────────────────────────────────────────────────────
    target_type_enum = postgresql.ENUM("doctor", "patient", "question", "answer", name="targettype")
    report_status_enum = postgresql.ENUM("open", "dismissed", "warned", "suspended", name="reportstatus")
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reporter_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("target_type", target_type_enum, nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(100), nullable=False),
        sa.Column("evidence_file_id", sa.String(200), nullable=True),
        sa.Column("status", report_status_enum, nullable=False, server_default="open"),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reports_reporter_id", "reports", ["reporter_id"])
    op.create_index("ix_reports_status", "reports", ["status"])

    # ── translations ─────────────────────────────────────────────────────
    op.create_table(
        "translations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(200), nullable=False),
        sa.Column("lang", sa.String(5), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key", "lang", name="uq_translation_key_lang"),
    )
    op.create_index("ix_translations_key", "translations", ["key"])

    # ── app_settings ─────────────────────────────────────────────────────
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )

    # ── subscriptions ────────────────────────────────────────────────────
    sub_plan_enum = postgresql.ENUM("basic", "family", "senior", name="subscriptionplan")
    sub_status_enum = postgresql.ENUM("active", "cancelled", "past_due", name="subscriptionstatus")
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("diaspora_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("diaspora_email", sa.String(255), nullable=False),
        sa.Column("beneficiary_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan", sub_plan_enum, nullable=False),
        sa.Column("sessions_per_month", sa.Integer(), nullable=False),
        sa.Column("stripe_subscription_id", sa.String(200), nullable=True),
        sa.Column("status", sub_status_enum, nullable=False, server_default="active"),
        sa.Column("next_billing_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── pg_trgm for full-text search ──────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE INDEX IF NOT EXISTS ix_questions_text_trgm ON questions USING gin (text gin_trgm_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_doctors_name_trgm ON doctors USING gin (full_name gin_trgm_ops)")


def downgrade() -> None:
    op.drop_table("subscriptions")
    op.drop_table("app_settings")
    op.drop_table("translations")
    op.drop_table("reports")
    op.drop_table("doctor_earnings")
    op.drop_table("waitlist")
    op.drop_table("notifications")
    op.drop_table("relay_messages")
    op.drop_table("sessions")
    op.drop_table("payments")
    op.drop_table("follow_ups")
    op.drop_table("questions")
    op.drop_table("moderators")
    op.drop_table("doctors")
    op.drop_table("users")

    for enum_name in [
        "specialty", "registrationstatus", "questionstatus", "followupstatus",
        "paymentprovider", "paymentstatus", "sessionpackage", "sessionstatus",
        "sessionmode", "senderrole", "waitliststatus", "earningsstatus",
        "targettype", "reportstatus", "subscriptionplan", "subscriptionstatus",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
