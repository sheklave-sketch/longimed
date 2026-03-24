"""
Standalone callback handlers for menu buttons and admin actions.
These run at group 0 to ensure they fire before ConversationHandlers.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.i18n import t

logger = logging.getLogger(__name__)


# ── Doctor menu buttons ───────────────────────────────────────────────────

async def handle_doc_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle doctor menu inline button taps."""
    query = update.callback_query
    await query.answer()
    action = query.data.split(":")[1]

    if action == "queue":
        from bot.handlers.doctor import view_queue_cmd
        # Simulate command by calling directly
        update.message = query.message
        context.args = []
        await view_queue_cmd(update, context)

    elif action == "available":
        from bot.handlers.doctor import set_available_cmd
        update.message = query.message
        await set_available_cmd(update, context)

    elif action == "unavailable":
        from bot.handlers.doctor import set_unavailable_cmd
        update.message = query.message
        await set_unavailable_cmd(update, context)

    elif action == "schedule":
        await query.edit_message_text("📅 Schedule management coming soon.")

    elif action == "reviews":
        from bot.database import session_factory
        from bot.models.doctor import Doctor
        from sqlalchemy import select

        async with session_factory() as session:
            result = await session.execute(
                select(Doctor).where(Doctor.telegram_id == update.effective_user.id)
            )
            doctor = result.scalar_one_or_none()

        if doctor:
            avg = round(doctor.rating_avg, 2) if doctor.rating_avg else 0.0
            cnt = doctor.rating_count or 0
            await query.edit_message_text(f"⭐ Your Reviews\n\nRating: {avg}/5 ({cnt} reviews)")
        else:
            await query.edit_message_text("No reviews yet.")

    elif action == "profile":
        from bot.database import session_factory
        from bot.models.doctor import Doctor
        from sqlalchemy import select

        async with session_factory() as session:
            result = await session.execute(
                select(Doctor).where(Doctor.telegram_id == update.effective_user.id)
            )
            doctor = result.scalar_one_or_none()

        if doctor:
            spec = doctor.specialty.value if hasattr(doctor.specialty, 'value') else doctor.specialty
            await query.edit_message_text(
                f"👤 Your Profile\n\n"
                f"Name: Dr. {doctor.full_name}\n"
                f"Specialty: {spec.title()}\n"
                f"License: {doctor.license_number}\n"
                f"Bio: {doctor.bio or 'Not set'}\n"
                f"Available: {'Yes' if doctor.is_available else 'No'}\n"
                f"Rating: {round(doctor.rating_avg, 2)}/5 ({doctor.rating_count} reviews)"
            )
        else:
            await query.edit_message_text("Profile not found.")


# ── Patient menu buttons ──────────────────────────────────────────────────

async def handle_patient_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle patient menu buttons that aren't covered by ConversationHandlers."""
    query = update.callback_query
    await query.answer()
    action = query.data.split(":")[1]
    lang = context.user_data.get("lang", "en")

    if action == "history":
        from bot.database import session_factory
        from bot.models.session import Session as ConsultSession
        from bot.models.question import Question
        from bot.models.user import User
        from sqlalchemy import select

        async with session_factory() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == update.effective_user.id)
            )
            user = result.scalar_one_or_none()
            if not user:
                await query.edit_message_text(t("error_not_registered", lang))
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

        lines = ["📋 Your History\n"]

        if questions:
            lines.append("--- Questions ---")
            for q in questions:
                cat = q.category.value if hasattr(q.category, 'value') else q.category
                lines.append(f"  #{q.id} [{cat}] {q.status.value} — {q.text[:50]}...")
        else:
            lines.append("No questions yet.")

        if sessions:
            lines.append("\n--- Consultations ---")
            for s in sessions:
                lines.append(f"  #{s.id} {s.status.value} — {str(s.created_at)[:16]}")
        else:
            lines.append("\nNo consultations yet.")

        await query.edit_message_text("\n".join(lines))

    elif action == "settings":
        from bot.utils.keyboards import language_keyboard
        await query.edit_message_text(
            "⚙️ Settings\n\nChange your language:",
            reply_markup=language_keyboard(),
        )
