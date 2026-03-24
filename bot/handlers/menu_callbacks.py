"""
Standalone callback handlers for menu buttons and admin actions.
These run at group 0 to ensure they fire before ConversationHandlers.
All logic is self-contained — never calls command handlers (they expect update.message).
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.i18n import t
from bot.database import session_factory

logger = logging.getLogger(__name__)


async def _get_doctor(telegram_id: int):
    from bot.models.doctor import Doctor
    from sqlalchemy import select
    async with session_factory() as session:
        result = await session.execute(
            select(Doctor).where(Doctor.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


# ── Doctor menu buttons ───────────────────────────────────────────────────

async def handle_doc_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    action = query.data.split(":")[1]
    lang = context.user_data.get("lang", "en")

    try:
        if action == "queue":
            await _doc_queue(query, update.effective_user.id)
        elif action == "available":
            await _doc_set_availability(query, update.effective_user.id, True)
        elif action == "unavailable":
            await _doc_set_availability(query, update.effective_user.id, False)
        elif action == "schedule":
            await query.edit_message_text("📅 Schedule management coming soon.")
        elif action == "reviews":
            await _doc_reviews(query, update.effective_user.id)
        elif action == "profile":
            await _doc_profile(query, update.effective_user.id)
    except Exception as exc:
        logger.error("Doc menu error (%s): %s", action, exc, exc_info=True)
        await query.edit_message_text(f"Error: {exc}")


async def _doc_set_availability(query, telegram_id: int, available: bool) -> None:
    from bot.models.doctor import Doctor
    from sqlalchemy import select
    async with session_factory() as session:
        result = await session.execute(
            select(Doctor).where(Doctor.telegram_id == telegram_id)
        )
        doctor = result.scalar_one_or_none()
        if not doctor:
            await query.edit_message_text("Doctor record not found.")
            return
        doctor.is_available = available
        await session.commit()
    if available:
        await query.edit_message_text("✅ You are now available for consultations.")
    else:
        await query.edit_message_text("🔴 You are now unavailable.")


async def _doc_queue(query, telegram_id: int) -> None:
    from bot.models.doctor import Doctor
    from bot.models.session import Session as CS, SessionStatus
    from sqlalchemy import select
    async with session_factory() as session:
        result = await session.execute(
            select(Doctor).where(Doctor.telegram_id == telegram_id)
        )
        doctor = result.scalar_one_or_none()
        if not doctor:
            await query.edit_message_text("Doctor record not found.")
            return
        s_result = await session.execute(
            select(CS).where(
                CS.doctor_id == doctor.id,
                CS.status.in_([SessionStatus.AWAITING_DOCTOR, SessionStatus.ACTIVE]),
            )
        )
        sessions = s_result.scalars().all()

    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("\u2190 Back to Menu", callback_data="backtomenu")]])

    if not sessions:
        await query.edit_message_text("📋 Your Queue\n\nNo pending sessions.", reply_markup=back_btn)
        return

    lines = ["📋 Your Queue\n"]
    for s in sessions:
        status = s.status.value if hasattr(s.status, 'value') else s.status
        lines.append(f"  #{s.id} — {status} — {s.issue_description[:40]}...")
    await query.edit_message_text("\n".join(lines), reply_markup=back_btn)


async def _doc_reviews(query, telegram_id: int) -> None:
    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("\u2190 Back to Menu", callback_data="backtomenu")]])
    doctor = await _get_doctor(telegram_id)
    if doctor:
        avg = round(doctor.rating_avg, 2) if doctor.rating_avg else 0.0
        cnt = doctor.rating_count or 0
        await query.edit_message_text(f"\u2b50 Your Reviews\n\nRating: {avg}/5 ({cnt} reviews)", reply_markup=back_btn)
    else:
        await query.edit_message_text("No reviews yet.", reply_markup=back_btn)


async def _doc_profile(query, telegram_id: int) -> None:
    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("\u2190 Back to Menu", callback_data="backtomenu")]])
    doctor = await _get_doctor(telegram_id)
    if not doctor:
        await query.edit_message_text("Profile not found.", reply_markup=back_btn)
        return
    spec = doctor.specialty.value if hasattr(doctor.specialty, 'value') else doctor.specialty
    await query.edit_message_text(
        f"Your Profile\n\n"
        f"Name: Dr. {doctor.full_name}\n"
        f"Specialty: {spec.title()}\n"
        f"License: {doctor.license_number}\n"
        f"Bio: {doctor.bio or 'Not set'}\n"
        f"Available: {'Yes' if doctor.is_available else 'No'}\n"
        f"Rating: {round(doctor.rating_avg, 2)}/5 ({doctor.rating_count} reviews)",
        reply_markup=back_btn,
    )


# ── Patient menu buttons ──────────────────────────────────────────────────

async def handle_patient_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    action = query.data.split(":")[1]
    lang = context.user_data.get("lang", "en")

    try:
        if action == "browse":
            await _browse_doctors(query, lang)
            return
        await _patient_menu_inner(query, action, lang, update.effective_user.id)
    except Exception as exc:
        logger.error("Patient menu error (%s): %s", action, exc, exc_info=True)
        await query.edit_message_text(f"Error: {exc}")


async def _browse_doctors(query, lang: str) -> None:
    from bot.models.doctor import Doctor
    from sqlalchemy import select
    async with session_factory() as session:
        result = await session.execute(
            select(Doctor).where(
                Doctor.is_verified.is_(True),
            )
        )
        doctors = result.scalars().all()

    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("\u2190 Back to Menu", callback_data="backtomenu")]])

    if not doctors:
        await query.edit_message_text("No doctors registered yet.", reply_markup=back_btn)
        return

    lines = ["Our Doctors\n"]
    for d in doctors:
        spec = d.specialty.value if hasattr(d.specialty, 'value') else d.specialty
        avail = "\U0001f7e2" if d.is_available else "\U0001f534"
        rating = f"{round(d.rating_avg, 1)}/5" if d.rating_count else "New"
        lines.append(f"{avail} Dr. {d.full_name} \u2014 {spec.title()} ({rating})")
    await query.edit_message_text("\n".join(lines), reply_markup=back_btn)


async def _patient_menu_inner(query, action: str, lang: str, telegram_id: int) -> None:
    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("\u2190 Back to Menu", callback_data="backtomenu")]])

    if action == "history":
        from bot.database import session_factory
        from bot.models.session import Session as ConsultSession
        from bot.models.question import Question
        from bot.models.user import User
        from sqlalchemy import select

        async with session_factory() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                await query.edit_message_text(t("error_not_registered", lang), reply_markup=back_btn)
                return

            q_result = await session.execute(
                select(Question).where(Question.user_id == user.id)
                .order_by(Question.created_at.desc()).limit(10)
            )
            questions = q_result.scalars().all()

            s_result = await session.execute(
                select(ConsultSession).where(ConsultSession.user_id == user.id)
                .order_by(ConsultSession.created_at.desc()).limit(10)
            )
            sessions = s_result.scalars().all()

        lines = ["Your History\n"]

        if questions:
            lines.append("--- Questions ---")
            for q in questions:
                cat = q.category.value if hasattr(q.category, 'value') else q.category
                lines.append(f"  #{q.id} [{cat}] {q.status.value} \u2014 {q.text[:50]}...")
        else:
            lines.append("No questions yet.")

        if sessions:
            lines.append("\n--- Consultations ---")
            for s in sessions:
                lines.append(f"  #{s.id} {s.status.value} \u2014 {str(s.created_at)[:16]}")
        else:
            lines.append("\nNo consultations yet.")

        await query.edit_message_text("\n".join(lines), reply_markup=back_btn)

    elif action == "settings":
        from bot.utils.keyboards import language_keyboard
        await query.edit_message_text(
            "Settings\n\nChange your language:",
            reply_markup=language_keyboard(),
        )
