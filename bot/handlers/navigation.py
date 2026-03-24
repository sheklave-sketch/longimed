"""
Navigation handlers: /menu, /help, /end, accept_session callback, back-to-menu callback.
Registered at group 0 (before ConversationHandlers).
"""

import logging
from datetime import datetime, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from bot.database import session_factory
from bot.models.session import Session as ConsultSession, SessionStatus
from bot.models.doctor import Doctor
from bot.models.user import User
from bot.models.relay_message import RelayMessage, SenderRole
from bot.i18n import t
from bot.utils.keyboards import main_menu_keyboard, doctor_menu_keyboard, rating_keyboard
from sqlalchemy import select

logger = logging.getLogger(__name__)

back_btn = InlineKeyboardMarkup([
    [InlineKeyboardButton("\u2190 Back to Menu", callback_data="backtomenu")]
])


async def _is_doctor(telegram_id: int) -> bool:
    """Check if user is a verified doctor."""
    try:
        async with session_factory() as session:
            result = await session.execute(
                select(Doctor).where(
                    Doctor.telegram_id == telegram_id,
                    Doctor.is_verified.is_(True),
                )
            )
            return result.scalar_one_or_none() is not None
    except Exception as exc:
        logger.error("Error checking doctor status: %s", exc)
        return False


# ── /menu ─────────────────────────────────────────────────────────────────

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the appropriate menu based on user role."""
    lang = context.user_data.get("lang", "en")
    telegram_id = update.effective_user.id

    if await _is_doctor(telegram_id):
        await update.message.reply_text(
            t("menu_doctor_title", lang) if t("menu_doctor_title", lang) != "menu_doctor_title" else "Doctor Menu",
            reply_markup=doctor_menu_keyboard(lang),
        )
    else:
        await update.message.reply_text(
            t("menu_patient_title", lang) if t("menu_patient_title", lang) != "menu_patient_title" else "Main Menu",
            reply_markup=main_menu_keyboard(lang),
        )


# ── /help ─────────────────────────────────────────────────────────────────

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show available commands based on user role."""
    lang = context.user_data.get("lang", "en")
    telegram_id = update.effective_user.id

    if await _is_doctor(telegram_id):
        text = (
            "Available commands:\n\n"
            "/menu \u2014 Show your doctor menu\n"
            "/help \u2014 Show this help message\n"
            "/end \u2014 End your active consultation session\n"
            "/search \u2014 Search Q&A or doctors\n"
            "/start \u2014 Restart the bot\n\n"
            "Session management:\n"
            "\u2022 Use the menu to view your queue, toggle availability, and see reviews\n"
            "\u2022 Accept sessions from the notification buttons\n"
            "\u2022 Use /end when the consultation is complete"
        )
    else:
        text = (
            "Available commands:\n\n"
            "/menu \u2014 Show your menu\n"
            "/help \u2014 Show this help message\n"
            "/end \u2014 End your active consultation session\n"
            "/search \u2014 Search Q&A or doctors\n"
            "/start \u2014 Restart the bot\n\n"
            "What you can do:\n"
            "\u2022 Ask public health questions (free)\n"
            "\u2022 Book private consultations with verified doctors\n"
            "\u2022 Browse our doctor directory\n"
            "\u2022 View your history and past sessions\n"
            "\u2022 Use /end when your consultation is complete"
        )

    await update.message.reply_text(text, reply_markup=back_btn)


# ── /end ──────────────────────────────────────────────────────────────────

async def end_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """End the user's active consultation session."""
    lang = context.user_data.get("lang", "en")
    telegram_id = update.effective_user.id

    try:
        async with session_factory() as session:
            # Check if user is a doctor
            doc_result = await session.execute(
                select(Doctor).where(Doctor.telegram_id == telegram_id)
            )
            doctor = doc_result.scalar_one_or_none()

            if doctor:
                # Find active session as doctor
                s_result = await session.execute(
                    select(ConsultSession).where(
                        ConsultSession.doctor_id == doctor.id,
                        ConsultSession.status == SessionStatus.ACTIVE,
                    )
                )
                active_session = s_result.scalar_one_or_none()

                if not active_session:
                    await update.message.reply_text(
                        "No active session found.",
                        reply_markup=back_btn,
                    )
                    return

                active_session.resolution_confirmed_by_doctor = True

                if active_session.resolution_confirmed_by_patient:
                    # Both confirmed — resolve
                    active_session.status = SessionStatus.RESOLVED
                    active_session.ended_at = datetime.now(timezone.utc)
                    session_id = active_session.id
                    patient_user = await session.get(User, active_session.user_id)
                    await session.commit()

                    await update.message.reply_text(
                        "Session resolved. Thank you!",
                        reply_markup=back_btn,
                    )

                    # Send rating keyboard to patient
                    if patient_user:
                        try:
                            await context.bot.send_message(
                                chat_id=patient_user.telegram_id,
                                text="Your session has been resolved. Please rate your experience:",
                                reply_markup=rating_keyboard(session_id),
                            )
                        except Exception as exc:
                            logger.error("Failed to send rating to patient: %s", exc)
                else:
                    patient_user = await session.get(User, active_session.user_id)
                    await session.commit()

                    await update.message.reply_text(
                        "You've confirmed the session is complete. Waiting for the patient to confirm.",
                        reply_markup=back_btn,
                    )

                    # Notify patient
                    if patient_user:
                        try:
                            await context.bot.send_message(
                                chat_id=patient_user.telegram_id,
                                text="Your doctor has marked the session as complete. Use /end to confirm, or continue the conversation.",
                            )
                        except Exception as exc:
                            logger.error("Failed to notify patient: %s", exc)
            else:
                # User is a patient
                user_result = await session.execute(
                    select(User).where(User.telegram_id == telegram_id)
                )
                user = user_result.scalar_one_or_none()

                if not user:
                    await update.message.reply_text(
                        "No active session found.",
                        reply_markup=back_btn,
                    )
                    return

                s_result = await session.execute(
                    select(ConsultSession).where(
                        ConsultSession.user_id == user.id,
                        ConsultSession.status == SessionStatus.ACTIVE,
                    )
                )
                active_session = s_result.scalar_one_or_none()

                if not active_session:
                    await update.message.reply_text(
                        "No active session found.",
                        reply_markup=back_btn,
                    )
                    return

                active_session.resolution_confirmed_by_patient = True

                if active_session.resolution_confirmed_by_doctor:
                    # Both confirmed — resolve
                    active_session.status = SessionStatus.RESOLVED
                    active_session.ended_at = datetime.now(timezone.utc)
                    session_id = active_session.id
                    await session.commit()

                    await update.message.reply_text(
                        "Session resolved. Please rate your experience:",
                        reply_markup=rating_keyboard(session_id),
                    )
                else:
                    doctor_obj = await session.get(Doctor, active_session.doctor_id) if active_session.doctor_id else None
                    await session.commit()

                    await update.message.reply_text(
                        "You've confirmed the session is complete. Waiting for the doctor to confirm.",
                        reply_markup=back_btn,
                    )

                    # Notify doctor
                    if doctor_obj:
                        try:
                            await context.bot.send_message(
                                chat_id=doctor_obj.telegram_id,
                                text="Your patient has marked the session as complete. Use /end to confirm, or continue the conversation.",
                            )
                        except Exception as exc:
                            logger.error("Failed to notify doctor: %s", exc)

    except Exception as exc:
        logger.error("Error in /end command: %s", exc, exc_info=True)
        await update.message.reply_text(
            "Something went wrong. Please try again.",
            reply_markup=back_btn,
        )


# ── Accept session callback ──────────────────────────────────────────────

async def accept_session_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Doctor accepts a consultation session via inline button."""
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")

    session_id = int(query.data.split(":")[1])

    try:
        async with session_factory() as session:
            s = await session.get(ConsultSession, session_id)
            if not s:
                await query.edit_message_text("Session not found.", reply_markup=back_btn)
                return

            if s.status not in (SessionStatus.AWAITING_DOCTOR,):
                await query.edit_message_text(
                    f"Session #{session_id} is no longer awaiting acceptance (status: {s.status.value}).",
                    reply_markup=back_btn,
                )
                return

            # Verify this doctor owns the session
            doc_result = await session.execute(
                select(Doctor).where(Doctor.telegram_id == update.effective_user.id)
            )
            doctor = doc_result.scalar_one_or_none()

            if not doctor or doctor.id != s.doctor_id:
                await query.edit_message_text("This session is not assigned to you.", reply_markup=back_btn)
                return

            s.status = SessionStatus.ACTIVE
            s.started_at = datetime.now(timezone.utc)
            patient_user = await session.get(User, s.user_id)
            is_relay = s.session_mode.value == "relay"
            await session.commit()

        await query.edit_message_text(
            f"Session #{session_id} accepted and now ACTIVE.",
            reply_markup=back_btn,
        )

        # Notify patient
        if patient_user:
            try:
                if is_relay:
                    await context.bot.send_message(
                        chat_id=patient_user.telegram_id,
                        text=(
                            "Your doctor has accepted the session!\n\n"
                            "This is a relay (anonymous) session. Send your messages here "
                            "and the bot will forward them to your doctor.\n\n"
                            "Use /end when you're done."
                        ),
                    )
                else:
                    await context.bot.send_message(
                        chat_id=patient_user.telegram_id,
                        text=(
                            "Your doctor has accepted the session!\n\n"
                            "Use /end when you're done."
                        ),
                    )
            except Exception as exc:
                logger.error("Failed to notify patient of acceptance: %s", exc)

        # If relay, also instruct the doctor
        if is_relay:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text=(
                        "This is a relay (anonymous) session. The patient's identity is hidden.\n\n"
                        "Send your messages here and the bot will forward them to the patient.\n"
                        "Use /end when the consultation is complete."
                    ),
                )
            except Exception as exc:
                logger.error("Failed to send relay instructions to doctor: %s", exc)

    except Exception as exc:
        logger.error("Error accepting session: %s", exc, exc_info=True)
        await query.edit_message_text(
            "Something went wrong. Please try again.",
            reply_markup=back_btn,
        )


# ── Decline session callback ─────────────────────────────────────────────

async def decline_session_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Doctor declines a consultation session."""
    query = update.callback_query
    await query.answer()

    session_id = int(query.data.split(":")[1])

    try:
        async with session_factory() as session:
            s = await session.get(ConsultSession, session_id)
            if not s or s.status != SessionStatus.AWAITING_DOCTOR:
                await query.edit_message_text("Session not found or already handled.", reply_markup=back_btn)
                return

            # Mark as awaiting — the timeout job will reassign
            patient_user = await session.get(User, s.user_id)

        await query.edit_message_text(
            f"Session #{session_id} declined. It will be reassigned to another doctor.",
            reply_markup=back_btn,
        )

        if patient_user:
            try:
                await context.bot.send_message(
                    chat_id=patient_user.telegram_id,
                    text="Your assigned doctor is unavailable. We're finding another doctor for you. Please hold.",
                )
            except Exception:
                pass

    except Exception as exc:
        logger.error("Error declining session: %s", exc, exc_info=True)
        await query.edit_message_text("Something went wrong.", reply_markup=back_btn)


# ── Back to menu callback ────────────────────────────────────────────────

async def back_to_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the appropriate menu when user clicks Back to Menu."""
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")
    telegram_id = update.effective_user.id

    if await _is_doctor(telegram_id):
        await query.edit_message_text(
            t("menu_doctor_title", lang) if t("menu_doctor_title", lang) != "menu_doctor_title" else "Doctor Menu",
            reply_markup=doctor_menu_keyboard(lang),
        )
    else:
        await query.edit_message_text(
            t("menu_patient_title", lang) if t("menu_patient_title", lang) != "menu_patient_title" else "Main Menu",
            reply_markup=main_menu_keyboard(lang),
        )


# ── Export ────────────────────────────────────────────────────────────────

navigation_handlers = [
    CommandHandler("menu", menu_command),
    CommandHandler("help", help_command),
    CommandHandler("end", end_command),
    CallbackQueryHandler(accept_session_callback, pattern=r"^accept_session:(\d+)$"),
    CallbackQueryHandler(decline_session_callback, pattern=r"^decline_session:(\d+)$"),
    CallbackQueryHandler(back_to_menu_callback, pattern=r"^backtomenu$"),
]
