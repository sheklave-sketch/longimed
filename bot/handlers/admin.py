"""
Admin command handlers for the LongiMed bot.

All handlers require the @admin_only decorator.

Commands:
    /list_pending            - paginated list of pending questions and sessions
    /confirm_payment         - mark a payment as completed and notify user
    /add_moderator           - add a user to the moderators table
    /remove_moderator        - remove a user from the moderators table
    /view_doctors            - list all doctors with status and availability
    /pending_doctors         - list PENDING_VERIFICATION doctor applications
    /approve_doctor          - verify and approve a doctor application
    /reject_doctor           - reject a doctor application with a reason

Also registers:
    question_approve_handler
    question_reject_handler

Exports:
    admin_handlers  (list of Handler objects)
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes

from bot.i18n import t
from bot.utils.decorators import admin_only
from bot.database import session_factory
from bot.models.question import Question, QuestionStatus
from bot.models.user import User
from bot.models.doctor import Doctor
from bot.models.moderator import Moderator
from bot.config import settings
from sqlalchemy import select

logger = logging.getLogger(__name__)

# Page size for paginated listings
PAGE_SIZE = 10


# ---------------------------------------------------------------------------
# /list_pending
# ---------------------------------------------------------------------------

@admin_only
async def list_pending_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show paginated list of pending questions and sessions."""
    lang = context.user_data.get("lang", "en")

    # Parse optional page argument: /list_pending [page]
    args = context.args or []
    page = int(args[0]) if args and args[0].isdigit() else 1
    offset = (page - 1) * PAGE_SIZE

    async with session_factory() as session:
        # Pending questions
        q_result = await session.execute(
            select(Question)
            .where(Question.status == QuestionStatus.PENDING)
            .order_by(Question.created_at.asc())
            .offset(offset)
            .limit(PAGE_SIZE)
        )
        pending_questions = q_result.scalars().all()

        # Pending / active sessions (import inline to avoid circular imports)
        from bot.models.session import Session as ConsultSession, SessionStatus
        s_result = await session.execute(
            select(ConsultSession)
            .where(
                ConsultSession.status.in_(
                    [SessionStatus.AWAITING_DOCTOR, SessionStatus.ACTIVE]
                )
            )
            .order_by(ConsultSession.created_at.asc())
            .offset(offset)
            .limit(PAGE_SIZE)
        )
        pending_sessions = s_result.scalars().all()

    lines: list[str] = [t("admin.list_pending_header", lang, page=page)]

    if pending_questions:
        lines.append(t("admin.section_questions", lang))
        for q in pending_questions:
            lines.append(
                t(
                    "admin.question_item",
                    lang,
                    id=q.id,
                    category=q.category,
                    preview=q.text[:80],
                )
            )
    else:
        lines.append(t("admin.no_pending_questions", lang))

    if pending_sessions:
        lines.append(t("admin.section_sessions", lang))
        for s in pending_sessions:
            lines.append(
                t(
                    "admin.session_item",
                    lang,
                    id=s.id,
                    status=s.status.value,
                    patient_id=s.patient_id,
                )
            )
    else:
        lines.append(t("admin.no_pending_sessions", lang))

    await update.message.reply_text("\n".join(lines))


# ---------------------------------------------------------------------------
# /confirm_payment <user_id> <amount>
# ---------------------------------------------------------------------------

@admin_only
async def confirm_payment_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mark a payment as COMPLETED and notify the user."""
    lang = context.user_data.get("lang", "en")
    args = context.args or []

    if len(args) < 2:
        await update.message.reply_text(t("admin.confirm_payment_usage", lang))
        return

    user_id_str, amount_str = args[0], args[1]
    if not user_id_str.isdigit():
        await update.message.reply_text(t("error.invalid_user_id", lang))
        return

    target_user_id = int(user_id_str)
    admin_telegram_id = update.effective_user.id

    async with session_factory() as session:
        from bot.models.payment import Payment, PaymentStatus

        # Find the most recent pending payment for this user
        pay_result = await session.execute(
            select(Payment)
            .join(User, Payment.user_id == User.id)
            .where(
                User.telegram_id == target_user_id,
                Payment.status == PaymentStatus.PENDING,
            )
            .order_by(Payment.created_at.desc())
            .limit(1)
        )
        payment = pay_result.scalar_one_or_none()

        if payment is None:
            await update.message.reply_text(
                t("admin.no_pending_payment", lang, user_id=target_user_id)
            )
            return

        payment.status = PaymentStatus.COMPLETED
        payment.confirmed_by_admin_id = admin_telegram_id
        payment.amount = float(amount_str)
        await session.flush()

        # Get user's telegram_id for notification
        user_result = await session.execute(
            select(User).where(User.telegram_id == target_user_id)
        )
        user = user_result.scalar_one_or_none()
        await session.commit()

    if user:
        try:
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text=t("payment.confirmed_notify", lang, amount=amount_str),
            )
        except Exception as exc:
            logger.warning("Failed to notify user %s of payment: %s", target_user_id, exc)

    await update.message.reply_text(
        t("admin.payment_confirmed", lang, user_id=target_user_id, amount=amount_str)
    )


# ---------------------------------------------------------------------------
# /add_moderator <telegram_id>
# ---------------------------------------------------------------------------

@admin_only
async def add_moderator_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a user to the moderators table."""
    lang = context.user_data.get("lang", "en")
    args = context.args or []

    if not args or not args[0].isdigit():
        await update.message.reply_text(t("admin.add_moderator_usage", lang))
        return

    telegram_id = int(args[0])

    async with session_factory() as session:
        # Check if already a moderator
        existing = await session.execute(
            select(Moderator).where(Moderator.telegram_id == telegram_id)
        )
        if existing.scalar_one_or_none():
            await update.message.reply_text(
                t("admin.already_moderator", lang, telegram_id=telegram_id)
            )
            return

        moderator = Moderator(telegram_id=telegram_id)
        session.add(moderator)
        await session.commit()

    await update.message.reply_text(
        t("admin.moderator_added", lang, telegram_id=telegram_id)
    )


# ---------------------------------------------------------------------------
# /remove_moderator <telegram_id>
# ---------------------------------------------------------------------------

@admin_only
async def remove_moderator_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove a user from the moderators table."""
    lang = context.user_data.get("lang", "en")
    args = context.args or []

    if not args or not args[0].isdigit():
        await update.message.reply_text(t("admin.remove_moderator_usage", lang))
        return

    telegram_id = int(args[0])

    async with session_factory() as session:
        result = await session.execute(
            select(Moderator).where(Moderator.telegram_id == telegram_id)
        )
        moderator = result.scalar_one_or_none()

        if moderator is None:
            await update.message.reply_text(
                t("admin.moderator_not_found", lang, telegram_id=telegram_id)
            )
            return

        await session.delete(moderator)
        await session.commit()

    await update.message.reply_text(
        t("admin.moderator_removed", lang, telegram_id=telegram_id)
    )


# ---------------------------------------------------------------------------
# /view_doctors
# ---------------------------------------------------------------------------

@admin_only
async def view_doctors_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all doctors with verification status and availability."""
    lang = context.user_data.get("lang", "en")

    async with session_factory() as session:
        result = await session.execute(
            select(Doctor).order_by(Doctor.created_at.desc())
        )
        doctors = result.scalars().all()

    if not doctors:
        await update.message.reply_text(t("admin.no_doctors", lang))
        return

    lines: list[str] = [t("admin.view_doctors_header", lang)]
    for doc in doctors:
        from bot.models.doctor import RegistrationStatus
        status_label = doc.registration_status.value if hasattr(doc, "registration_status") else "unknown"
        avail_label = t("doctor.available", lang) if doc.is_available else t("doctor.unavailable", lang)
        verified_label = t("doctor.verified", lang) if doc.is_verified else t("doctor.not_verified", lang)
        lines.append(
            t(
                "admin.doctor_item",
                lang,
                id=doc.id,
                name=doc.full_name,
                specialty=doc.specialty,
                status=status_label,
                verified=verified_label,
                availability=avail_label,
            )
        )

    # Split long messages if needed
    text = "\n".join(lines)
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            await update.message.reply_text(text[i : i + 4000])
    else:
        await update.message.reply_text(text)


# ---------------------------------------------------------------------------
# /pending_doctors
# ---------------------------------------------------------------------------

@admin_only
async def pending_doctors_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List doctors with PENDING_VERIFICATION status with approve/reject buttons."""
    lang = context.user_data.get("lang", "en")

    async with session_factory() as session:
        from bot.models.doctor import RegistrationStatus
        result = await session.execute(
            select(Doctor).where(
                Doctor.registration_status == RegistrationStatus.PENDING_VERIFICATION
            )
        )
        doctors = result.scalars().all()

    if not doctors:
        await update.message.reply_text(t("admin.no_pending_doctors", lang))
        return

    for doc in doctors:
        text = t(
            "admin.pending_doctor_item",
            lang,
            id=doc.id,
            name=doc.full_name,
            specialty=doc.specialty,
            telegram_id=doc.telegram_id,
        )
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    t("admin.btn_approve_doctor", lang),
                    callback_data=f"docmod:approve:{doc.id}",
                ),
                InlineKeyboardButton(
                    t("admin.btn_reject_doctor", lang),
                    callback_data=f"docmod:reject:{doc.id}",
                ),
            ]
        ])
        await update.message.reply_text(text, reply_markup=keyboard)


# ---------------------------------------------------------------------------
# /approve_doctor <id>
# ---------------------------------------------------------------------------

@admin_only
async def approve_doctor_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Verify and approve a doctor application."""
    lang = context.user_data.get("lang", "en")
    args = context.args or []

    if not args or not args[0].isdigit():
        await update.message.reply_text(t("admin.approve_doctor_usage", lang))
        return

    doctor_id = int(args[0])

    async with session_factory() as session:
        from bot.models.doctor import RegistrationStatus
        result = await session.execute(
            select(Doctor).where(Doctor.id == doctor_id)
        )
        doctor = result.scalar_one_or_none()

        if doctor is None:
            await update.message.reply_text(
                t("admin.doctor_not_found", lang, id=doctor_id)
            )
            return

        doctor.is_verified = True
        doctor.registration_status = RegistrationStatus.APPROVED
        doc_telegram_id = doctor.telegram_id
        await session.commit()

    try:
        await context.bot.send_message(
            chat_id=doc_telegram_id,
            text=t("doctor.approved_notify", lang),
        )
    except Exception as exc:
        logger.warning("Failed to notify doctor %s of approval: %s", doc_telegram_id, exc)

    await update.message.reply_text(
        t("admin.doctor_approved", lang, id=doctor_id)
    )


# ---------------------------------------------------------------------------
# /reject_doctor <id> <reason...>
# ---------------------------------------------------------------------------

@admin_only
async def reject_doctor_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reject a doctor application with a reason."""
    lang = context.user_data.get("lang", "en")
    args = context.args or []

    if len(args) < 2:
        await update.message.reply_text(t("admin.reject_doctor_usage", lang))
        return

    doctor_id_str = args[0]
    if not doctor_id_str.isdigit():
        await update.message.reply_text(t("error.invalid_id", lang))
        return

    doctor_id = int(doctor_id_str)
    reason = " ".join(args[1:])

    async with session_factory() as session:
        from bot.models.doctor import RegistrationStatus
        result = await session.execute(
            select(Doctor).where(Doctor.id == doctor_id)
        )
        doctor = result.scalar_one_or_none()

        if doctor is None:
            await update.message.reply_text(
                t("admin.doctor_not_found", lang, id=doctor_id)
            )
            return

        doctor.is_verified = False
        doctor.registration_status = RegistrationStatus.REJECTED
        doctor.rejection_reason = reason
        doc_telegram_id = doctor.telegram_id
        await session.commit()

    try:
        await context.bot.send_message(
            chat_id=doc_telegram_id,
            text=t("doctor.rejected_notify", lang, reason=reason),
        )
    except Exception as exc:
        logger.warning("Failed to notify doctor %s of rejection: %s", doc_telegram_id, exc)

    await update.message.reply_text(
        t("admin.doctor_rejected", lang, id=doctor_id, reason=reason)
    )


# ---------------------------------------------------------------------------
# Handler assembly
# ---------------------------------------------------------------------------

# Import question moderation handlers (no circular risk — public_question
# does not import from admin.py)
from bot.handlers.public_question import (  # noqa: E402
    question_approve_handler,
    question_reject_handler,
)

admin_handlers = [
    CommandHandler("list_pending", list_pending_cmd),
    CommandHandler("confirm_payment", confirm_payment_cmd),
    CommandHandler("add_moderator", add_moderator_cmd),
    CommandHandler("remove_moderator", remove_moderator_cmd),
    CommandHandler("view_doctors", view_doctors_cmd),
    CommandHandler("pending_doctors", pending_doctors_cmd),
    CommandHandler("approve_doctor", approve_doctor_cmd),
    CommandHandler("reject_doctor", reject_doctor_cmd),
    # Question moderation callbacks
    question_approve_handler,
    question_reject_handler,
]
