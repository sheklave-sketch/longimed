"""
Doctor command handlers for the LongiMed bot.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes

from bot.utils.decorators import doctor_only
from bot.database import session_factory
from bot.models.doctor import Doctor
from bot.models.user import User
from sqlalchemy import select, func

logger = logging.getLogger(__name__)


@doctor_only
async def set_available_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id
    async with session_factory() as session:
        result = await session.execute(select(Doctor).where(Doctor.telegram_id == telegram_id))
        doctor = result.scalar_one_or_none()
        if not doctor:
            await update.message.reply_text("Doctor record not found.")
            return
        doctor.is_available = True
        await session.commit()
    await update.message.reply_text("✅ You are now available for consultations.")


@doctor_only
async def set_unavailable_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id
    async with session_factory() as session:
        result = await session.execute(select(Doctor).where(Doctor.telegram_id == telegram_id))
        doctor = result.scalar_one_or_none()
        if not doctor:
            await update.message.reply_text("Doctor record not found.")
            return
        doctor.is_available = False
        await session.commit()
    await update.message.reply_text("🔴 You are now unavailable. No new sessions will be assigned.")


@doctor_only
async def view_queue_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id
    async with session_factory() as session:
        result = await session.execute(select(Doctor).where(Doctor.telegram_id == telegram_id))
        doctor = result.scalar_one_or_none()
        if not doctor:
            await update.message.reply_text("Doctor record not found.")
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
        await update.message.reply_text("📋 Your queue is empty. No sessions waiting.")
        return

    lines = ["📋 Your Queue:"]
    for s in sessions:
        lines.append(f"  #{s.id} — user_id={s.user_id} — {str(s.created_at)[:16]}")
    await update.message.reply_text("\n".join(lines))


@doctor_only
async def accept_session_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /accept_session <session_id>")
        return

    session_id = int(args[0])
    telegram_id = update.effective_user.id

    async with session_factory() as session:
        from bot.models.session import Session as ConsultSession, SessionStatus

        doc_result = await session.execute(select(Doctor).where(Doctor.telegram_id == telegram_id))
        doctor = doc_result.scalar_one_or_none()
        if not doctor:
            await update.message.reply_text("Doctor record not found.")
            return

        consult = await session.get(ConsultSession, session_id)
        if not consult:
            await update.message.reply_text("Session not found.")
            return
        if consult.doctor_id != doctor.id:
            await update.message.reply_text("This session is not assigned to you.")
            return
        if consult.status != SessionStatus.AWAITING_DOCTOR:
            await update.message.reply_text(f"Session is in status '{consult.status.value}', cannot accept.")
            return

        consult.status = SessionStatus.ACTIVE
        patient_user_id = consult.user_id

        pat_result = await session.execute(select(User).where(User.id == patient_user_id))
        patient = pat_result.scalar_one_or_none()
        patient_tid = patient.telegram_id if patient else None
        await session.commit()

    if patient_tid:
        try:
            await context.bot.send_message(
                chat_id=patient_tid,
                text=f"🩺 Dr. {doctor.full_name} has accepted your session #{session_id}. Your consultation is now active!",
            )
        except Exception as exc:
            logger.warning("Failed to notify patient: %s", exc)

    await update.message.reply_text(f"✅ Session #{session_id} accepted. You can now chat with the patient.")


@doctor_only
async def end_session_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /end_session <session_id>")
        return

    session_id = int(args[0])
    telegram_id = update.effective_user.id

    async with session_factory() as session:
        from bot.models.session import Session as ConsultSession, SessionStatus

        doc_result = await session.execute(select(Doctor).where(Doctor.telegram_id == telegram_id))
        doctor = doc_result.scalar_one_or_none()
        if not doctor:
            await update.message.reply_text("Doctor record not found.")
            return

        consult = await session.get(ConsultSession, session_id)
        if not consult:
            await update.message.reply_text("Session not found.")
            return
        if consult.doctor_id != doctor.id:
            await update.message.reply_text("This session is not assigned to you.")
            return
        if consult.status != SessionStatus.ACTIVE:
            await update.message.reply_text(f"Session is in status '{consult.status.value}', cannot end.")
            return

        consult.resolution_confirmed_by_doctor = True
        patient_user_id = consult.user_id

        pat_result = await session.execute(select(User).where(User.id == patient_user_id))
        patient = pat_result.scalar_one_or_none()
        patient_tid = patient.telegram_id if patient else None
        await session.commit()

    if patient_tid:
        try:
            await context.bot.send_message(
                chat_id=patient_tid,
                text=f"Dr. {doctor.full_name} has ended session #{session_id}.\n\nPlease confirm resolution with /verify_resolution {session_id}",
            )
        except Exception as exc:
            logger.warning("Failed to notify patient: %s", exc)

    await update.message.reply_text(f"Session #{session_id} — resolution pending patient confirmation. Use /verify_resolution {session_id} to confirm on your side.")


@doctor_only
async def verify_resolution_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /verify_resolution <session_id>")
        return

    session_id = int(args[0])
    telegram_id = update.effective_user.id

    async with session_factory() as session:
        from bot.models.session import Session as ConsultSession, SessionStatus

        doc_result = await session.execute(select(Doctor).where(Doctor.telegram_id == telegram_id))
        doctor = doc_result.scalar_one_or_none()
        if not doctor:
            await update.message.reply_text("Doctor record not found.")
            return

        consult = await session.get(ConsultSession, session_id)
        if not consult:
            await update.message.reply_text("Session not found.")
            return
        if consult.doctor_id != doctor.id:
            await update.message.reply_text("This session is not assigned to you.")
            return
        if consult.status != SessionStatus.ACTIVE:
            await update.message.reply_text(f"Session is in status '{consult.status.value}', cannot verify.")
            return

        consult.resolution_confirmed_by_doctor = True

        # Check if both sides confirmed
        both = consult.resolution_confirmed_by_doctor and consult.resolution_confirmed_by_patient
        if both:
            consult.status = SessionStatus.RESOLVED

        patient_user_id = consult.user_id
        pat_result = await session.execute(select(User).where(User.id == patient_user_id))
        patient = pat_result.scalar_one_or_none()
        patient_tid = patient.telegram_id if patient else None
        await session.commit()

    await update.message.reply_text(f"✅ Resolution confirmed for session #{session_id}.")

    if both and patient_tid:
        rating_kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(f"{i}⭐", callback_data=f"rate:{session_id}:{i}")
            for i in range(1, 6)
        ]])
        try:
            await context.bot.send_message(
                chat_id=patient_tid,
                text=f"Session #{session_id} is now resolved. How would you rate Dr. {doctor.full_name}?",
                reply_markup=rating_kb,
            )
        except Exception as exc:
            logger.warning("Failed to send rating keyboard: %s", exc)


@doctor_only
async def my_stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id

    async with session_factory() as session:
        doc_result = await session.execute(select(Doctor).where(Doctor.telegram_id == telegram_id))
        doctor = doc_result.scalar_one_or_none()
        if not doctor:
            await update.message.reply_text("Doctor record not found.")
            return

        from bot.models.session import Session as ConsultSession
        total_result = await session.execute(
            select(func.count(ConsultSession.id)).where(ConsultSession.doctor_id == doctor.id)
        )
        total = total_result.scalar_one() or 0

    avg = round(doctor.rating_avg, 2) if doctor.rating_avg else 0.0
    cnt = doctor.rating_count or 0

    await update.message.reply_text(
        f"📊 Your Stats\n\n"
        f"⭐ Rating: {avg}/5 ({cnt} reviews)\n"
        f"📋 Total sessions: {total}"
    )


doctor_handlers = [
    CommandHandler("set_available", set_available_cmd),
    CommandHandler("set_unavailable", set_unavailable_cmd),
    CommandHandler("view_queue", view_queue_cmd),
    CommandHandler("accept_session", accept_session_cmd),
    CommandHandler("end_session", end_session_cmd),
    CommandHandler("verify_resolution", verify_resolution_cmd),
    CommandHandler("my_stats", my_stats_cmd),
]
