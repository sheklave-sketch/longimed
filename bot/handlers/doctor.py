"""
Doctor command handlers for the LongiMed bot.

All handlers require the @doctor_only decorator.

Commands:
    /set_available      - mark doctor as available for sessions
    /set_unavailable    - mark doctor as unavailable
    /view_queue         - list sessions AWAITING_DOCTOR assigned to this doctor
    /accept_session     - accept a session and notify the patient
    /end_session        - initiate the resolution / close flow
    /verify_resolution  - confirm resolution on doctor side; close if patient also confirmed
    /my_stats           - show rating average, count, and total sessions

Exports:
    doctor_handlers  (list of Handler objects)
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes

from bot.i18n import t
from bot.utils.decorators import doctor_only
from bot.database import session_factory
from bot.models.doctor import Doctor
from bot.models.user import User
from bot.config import settings
from sqlalchemy import select, func

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# /set_available
# ---------------------------------------------------------------------------

@doctor_only
async def set_available_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mark this doctor as available for new consultations."""
    lang = context.user_data.get("lang", "en")
    telegram_id = update.effective_user.id

    async with session_factory() as session:
        result = await session.execute(
            select(Doctor).where(Doctor.telegram_id == telegram_id)
        )
        doctor = result.scalar_one_or_none()

        if doctor is None:
            await update.message.reply_text(t("error.doctor_not_found", lang))
            return

        doctor.is_available = True
        await session.commit()

    await update.message.reply_text(t("doctor.now_available", lang))


# ---------------------------------------------------------------------------
# /set_unavailable
# ---------------------------------------------------------------------------

@doctor_only
async def set_unavailable_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mark this doctor as unavailable."""
    lang = context.user_data.get("lang", "en")
    telegram_id = update.effective_user.id

    async with session_factory() as session:
        result = await session.execute(
            select(Doctor).where(Doctor.telegram_id == telegram_id)
        )
        doctor = result.scalar_one_or_none()

        if doctor is None:
            await update.message.reply_text(t("error.doctor_not_found", lang))
            return

        doctor.is_available = False
        await session.commit()

    await update.message.reply_text(t("doctor.now_unavailable", lang))


# ---------------------------------------------------------------------------
# /view_queue
# ---------------------------------------------------------------------------

@doctor_only
async def view_queue_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all AWAITING_DOCTOR sessions assigned to this doctor."""
    lang = context.user_data.get("lang", "en")
    telegram_id = update.effective_user.id

    async with session_factory() as session:
        # Resolve doctor record
        doc_result = await session.execute(
            select(Doctor).where(Doctor.telegram_id == telegram_id)
        )
        doctor = doc_result.scalar_one_or_none()

        if doctor is None:
            await update.message.reply_text(t("error.doctor_not_found", lang))
            return

        from bot.models.session import Session as ConsultSession, SessionStatus
        s_result = await session.execute(
            select(ConsultSession).where(
                ConsultSession.doctor_id == doctor.id,
                ConsultSession.status == SessionStatus.AWAITING_DOCTOR,
            ).order_by(ConsultSession.created_at.asc())
        )
        sessions = s_result.scalars().all()

    if not sessions:
        await update.message.reply_text(t("doctor.queue_empty", lang))
        return

    lines: list[str] = [t("doctor.queue_header", lang)]
    for s in sessions:
        lines.append(
            t(
                "doctor.queue_item",
                lang,
                id=s.id,
                patient_id=s.patient_id,
                created_at=str(s.created_at)[:16],
            )
        )

    await update.message.reply_text("\n".join(lines))


# ---------------------------------------------------------------------------
# /accept_session <id>
# ---------------------------------------------------------------------------

@doctor_only
async def accept_session_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Accept an awaiting session and notify the patient."""
    lang = context.user_data.get("lang", "en")
    telegram_id = update.effective_user.id
    args = context.args or []

    if not args or not args[0].isdigit():
        await update.message.reply_text(t("doctor.accept_session_usage", lang))
        return

    session_id = int(args[0])

    async with session_factory() as session:
        from bot.models.session import Session as ConsultSession, SessionStatus

        doc_result = await session.execute(
            select(Doctor).where(Doctor.telegram_id == telegram_id)
        )
        doctor = doc_result.scalar_one_or_none()

        if doctor is None:
            await update.message.reply_text(t("error.doctor_not_found", lang))
            return

        s_result = await session.execute(
            select(ConsultSession).where(ConsultSession.id == session_id)
        )
        consult = s_result.scalar_one_or_none()

        if consult is None:
            await update.message.reply_text(t("error.session_not_found", lang))
            return

        if consult.doctor_id != doctor.id:
            await update.message.reply_text(t("error.session_not_yours", lang))
            return

        if consult.status != SessionStatus.AWAITING_DOCTOR:
            await update.message.reply_text(
                t("error.session_wrong_status", lang, status=consult.status.value)
            )
            return

        consult.status = SessionStatus.ACTIVE
        patient_id = consult.patient_id
        await session.flush()

        # Get patient telegram_id
        pat_result = await session.execute(
            select(User).where(User.id == patient_id)
        )
        patient = pat_result.scalar_one_or_none()
        patient_telegram_id = patient.telegram_id if patient else None

        await session.commit()

    # Notify patient
    if patient_telegram_id:
        try:
            await context.bot.send_message(
                chat_id=patient_telegram_id,
                text=t("session.doctor_accepted_notify", lang, session_id=session_id),
            )
        except Exception as exc:
            logger.warning(
                "Failed to notify patient %s of session acceptance: %s",
                patient_telegram_id,
                exc,
            )

    await update.message.reply_text(
        t("doctor.session_accepted", lang, session_id=session_id)
    )


# ---------------------------------------------------------------------------
# /end_session <id>
# ---------------------------------------------------------------------------

@doctor_only
async def end_session_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Initiate the resolution flow for an active session.
    Asks the doctor to confirm, then notifies the patient.
    Sets session status to AWAITING_RESOLUTION.
    """
    lang = context.user_data.get("lang", "en")
    telegram_id = update.effective_user.id
    args = context.args or []

    if not args or not args[0].isdigit():
        await update.message.reply_text(t("doctor.end_session_usage", lang))
        return

    session_id = int(args[0])

    async with session_factory() as session:
        from bot.models.session import Session as ConsultSession, SessionStatus

        doc_result = await session.execute(
            select(Doctor).where(Doctor.telegram_id == telegram_id)
        )
        doctor = doc_result.scalar_one_or_none()

        if doctor is None:
            await update.message.reply_text(t("error.doctor_not_found", lang))
            return

        s_result = await session.execute(
            select(ConsultSession).where(ConsultSession.id == session_id)
        )
        consult = s_result.scalar_one_or_none()

        if consult is None:
            await update.message.reply_text(t("error.session_not_found", lang))
            return

        if consult.doctor_id != doctor.id:
            await update.message.reply_text(t("error.session_not_yours", lang))
            return

        if consult.status != SessionStatus.ACTIVE:
            await update.message.reply_text(
                t("error.session_wrong_status", lang, status=consult.status.value)
            )
            return

        consult.status = SessionStatus.AWAITING_RESOLUTION
        patient_id = consult.patient_id
        await session.flush()

        pat_result = await session.execute(
            select(User).where(User.id == patient_id)
        )
        patient = pat_result.scalar_one_or_none()
        patient_telegram_id = patient.telegram_id if patient else None

        await session.commit()

    # Notify patient that the doctor has ended the session and resolution is pending
    if patient_telegram_id:
        try:
            await context.bot.send_message(
                chat_id=patient_telegram_id,
                text=t("session.resolution_pending_notify", lang, session_id=session_id),
            )
        except Exception as exc:
            logger.warning(
                "Failed to notify patient %s of resolution pending: %s",
                patient_telegram_id,
                exc,
            )

    await update.message.reply_text(
        t("doctor.session_ending", lang, session_id=session_id)
    )


# ---------------------------------------------------------------------------
# /verify_resolution <id>
# ---------------------------------------------------------------------------

@doctor_only
async def verify_resolution_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Doctor confirms the resolution of a session.
    If both doctor and patient have confirmed, the session is closed
    and a rating keyboard is sent to the patient.
    """
    lang = context.user_data.get("lang", "en")
    telegram_id = update.effective_user.id
    args = context.args or []

    if not args or not args[0].isdigit():
        await update.message.reply_text(t("doctor.verify_resolution_usage", lang))
        return

    session_id = int(args[0])

    async with session_factory() as session:
        from bot.models.session import Session as ConsultSession, SessionStatus

        doc_result = await session.execute(
            select(Doctor).where(Doctor.telegram_id == telegram_id)
        )
        doctor = doc_result.scalar_one_or_none()

        if doctor is None:
            await update.message.reply_text(t("error.doctor_not_found", lang))
            return

        s_result = await session.execute(
            select(ConsultSession).where(ConsultSession.id == session_id)
        )
        consult = s_result.scalar_one_or_none()

        if consult is None:
            await update.message.reply_text(t("error.session_not_found", lang))
            return

        if consult.doctor_id != doctor.id:
            await update.message.reply_text(t("error.session_not_yours", lang))
            return

        if consult.status not in (
            SessionStatus.AWAITING_RESOLUTION,
            SessionStatus.ACTIVE,
        ):
            await update.message.reply_text(
                t("error.session_wrong_status", lang, status=consult.status.value)
            )
            return

        consult.resolution_confirmed_by_doctor = True
        both_confirmed = (
            consult.resolution_confirmed_by_doctor
            and getattr(consult, "resolution_confirmed_by_patient", False)
        )

        if both_confirmed:
            consult.status = SessionStatus.CLOSED

        patient_id = consult.patient_id
        await session.flush()

        pat_result = await session.execute(
            select(User).where(User.id == patient_id)
        )
        patient = pat_result.scalar_one_or_none()
        patient_telegram_id = patient.telegram_id if patient else None

        await session.commit()

    await update.message.reply_text(
        t("doctor.resolution_confirmed", lang, session_id=session_id)
    )

    if both_confirmed and patient_telegram_id:
        # Send rating keyboard to patient
        rating_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⭐ 1", callback_data=f"rate:{session_id}:1"),
                InlineKeyboardButton("⭐ 2", callback_data=f"rate:{session_id}:2"),
                InlineKeyboardButton("⭐ 3", callback_data=f"rate:{session_id}:3"),
                InlineKeyboardButton("⭐ 4", callback_data=f"rate:{session_id}:4"),
                InlineKeyboardButton("⭐ 5", callback_data=f"rate:{session_id}:5"),
            ]
        ])
        try:
            await context.bot.send_message(
                chat_id=patient_telegram_id,
                text=t("session.rate_doctor_prompt", lang, session_id=session_id),
                reply_markup=rating_keyboard,
            )
        except Exception as exc:
            logger.warning(
                "Failed to send rating keyboard to patient %s: %s",
                patient_telegram_id,
                exc,
            )


# ---------------------------------------------------------------------------
# /my_stats
# ---------------------------------------------------------------------------

@doctor_only
async def my_stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show this doctor's rating average, rating count, and total sessions."""
    lang = context.user_data.get("lang", "en")
    telegram_id = update.effective_user.id

    async with session_factory() as session:
        doc_result = await session.execute(
            select(Doctor).where(Doctor.telegram_id == telegram_id)
        )
        doctor = doc_result.scalar_one_or_none()

        if doctor is None:
            await update.message.reply_text(t("error.doctor_not_found", lang))
            return

        from bot.models.session import Session as ConsultSession, SessionStatus
        total_result = await session.execute(
            select(func.count(ConsultSession.id)).where(
                ConsultSession.doctor_id == doctor.id
            )
        )
        total_sessions = total_result.scalar_one() or 0

    rating_avg = round(doctor.rating_avg, 2) if doctor.rating_avg else 0.0
    rating_count = doctor.rating_count or 0

    await update.message.reply_text(
        t(
            "doctor.my_stats",
            lang,
            rating_avg=rating_avg,
            rating_count=rating_count,
            total_sessions=total_sessions,
        )
    )


# ---------------------------------------------------------------------------
# Handler assembly
# ---------------------------------------------------------------------------

doctor_handlers = [
    CommandHandler("set_available", set_available_cmd),
    CommandHandler("set_unavailable", set_unavailable_cmd),
    CommandHandler("view_queue", view_queue_cmd),
    CommandHandler("accept_session", accept_session_cmd),
    CommandHandler("end_session", end_session_cmd),
    CommandHandler("verify_resolution", verify_resolution_cmd),
    CommandHandler("my_stats", my_stats_cmd),
]
