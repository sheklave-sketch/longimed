"""
Navigation handlers: /menu, /help, /end, accept_session callback, back-to-menu callback.
Registered at group 0 (before ConversationHandlers).
"""

import logging
from datetime import datetime, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from bot.database import session_factory
from bot.models.session import Session as ConsultSession, SessionStatus, SessionMode
from bot.models.doctor import Doctor
from bot.models.user import User
from bot.models.relay_message import RelayMessage, SenderRole
from bot.i18n import t
from bot.utils.keyboards import main_menu_keyboard, doctor_menu_keyboard, rating_keyboard
from bot.config import settings
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
    """End the user's active consultation session. Works in bot DM and group rooms."""
    lang = context.user_data.get("lang", "en")
    telegram_id = update.effective_user.id
    in_group = update.effective_chat.type in ("group", "supergroup")
    group_chat_id = update.effective_chat.id if in_group else None

    try:
        async with session_factory() as session:
            # If in a group room, find the session for this room directly
            if in_group:
                s_result = await session.execute(
                    select(ConsultSession).where(
                        ConsultSession.group_chat_id == group_chat_id,
                        ConsultSession.status == SessionStatus.ACTIVE,
                    )
                )
                room_session = s_result.scalar_one_or_none()
                if not room_session:
                    await update.message.reply_text("No active session in this room.")
                    return

                # Figure out who typed /end
                doc_result = await session.execute(
                    select(Doctor).where(Doctor.telegram_id == telegram_id)
                )
                doctor = doc_result.scalar_one_or_none()

                is_doctor_ending = doctor and doctor.id == room_session.doctor_id
                patient_user = await session.get(User, room_session.user_id)
                patient_lang = patient_user.language if patient_user else "en"
                doctor_obj = await session.get(Doctor, room_session.doctor_id) if room_session.doctor_id else None

                if is_doctor_ending:
                    room_session.resolution_confirmed_by_doctor = True
                    who_ended = f"Dr. {doctor_obj.full_name}" if doctor_obj else "The doctor"
                else:
                    room_session.resolution_confirmed_by_patient = True
                    who_ended = "The patient"

                both_confirmed = (
                    room_session.resolution_confirmed_by_doctor
                    and room_session.resolution_confirmed_by_patient
                )

                if both_confirmed:
                    room_session.status = SessionStatus.RESOLVED
                    room_session.ended_at = datetime.now(timezone.utc)
                    session_id = room_session.id
                    await session.commit()

                    await update.message.reply_text(
                        t("room_end_resolved", patient_lang),
                        parse_mode="Markdown",
                    )

                    await _cleanup_room(
                        context.bot, group_chat_id,
                        patient_user.telegram_id if patient_user else None,
                        doctor_obj.telegram_id if doctor_obj else None,
                    )

                    # Send rating to patient in DM
                    if patient_user:
                        try:
                            followup_kb = InlineKeyboardMarkup([
                                [InlineKeyboardButton(
                                    f"{'⭐' * i}", callback_data=f"rate:{session_id}:{i}"
                                ) for i in range(1, 6)],
                                [InlineKeyboardButton(
                                    "💬 Send Follow-Up Message",
                                    callback_data=f"session_followup:{session_id}",
                                )],
                            ])
                            await context.bot.send_message(
                                chat_id=patient_user.telegram_id,
                                text=t("session_rate_prompt", patient_lang),
                                reply_markup=followup_kb,
                            )
                        except Exception as exc:
                            logger.error("Failed to send rating to patient: %s", exc)
                else:
                    await session.commit()
                    confirm_kb = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            t("room_end_confirm_button", patient_lang),
                            callback_data=f"confirm_end:{room_session.id}",
                        )],
                    ])
                    await update.message.reply_text(
                        t("room_end_request", patient_lang, who=who_ended),
                        reply_markup=confirm_kb,
                    )
                return

            # ── Private chat /end flow ──
            # Check if user is a doctor
            doc_result = await session.execute(
                select(Doctor).where(Doctor.telegram_id == telegram_id)
            )
            doctor = doc_result.scalar_one_or_none()

            is_doctor_ending = False
            active_session = None

            if doctor:
                s_result = await session.execute(
                    select(ConsultSession).where(
                        ConsultSession.doctor_id == doctor.id,
                        ConsultSession.status == SessionStatus.ACTIVE,
                    )
                )
                active_session = s_result.scalar_one_or_none()
                if active_session and active_session.doctor_id == doctor.id:
                    is_doctor_ending = True

            if not is_doctor_ending:
                user_result = await session.execute(
                    select(User).where(User.telegram_id == telegram_id)
                )
                user = user_result.scalar_one_or_none()
                if not user:
                    await update.message.reply_text("No active session found.", reply_markup=back_btn)
                    return

                s_result = await session.execute(
                    select(ConsultSession).where(
                        ConsultSession.user_id == user.id,
                        ConsultSession.status == SessionStatus.ACTIVE,
                    )
                )
                active_session = s_result.scalar_one_or_none()

            if not active_session:
                await update.message.reply_text("No active session found.", reply_markup=back_btn)
                return

            room_id = active_session.group_chat_id
            session_id = active_session.id
            patient_user = await session.get(User, active_session.user_id)
            patient_lang = patient_user.language if patient_user else "en"
            doctor_obj = await session.get(Doctor, active_session.doctor_id) if active_session.doctor_id else None

            if is_doctor_ending:
                active_session.resolution_confirmed_by_doctor = True
                who_ended = f"Dr. {doctor_obj.full_name}" if doctor_obj else "The doctor"
            else:
                active_session.resolution_confirmed_by_patient = True
                who_ended = "The patient"

            both_confirmed = (
                active_session.resolution_confirmed_by_doctor
                and active_session.resolution_confirmed_by_patient
            )

            if both_confirmed:
                active_session.status = SessionStatus.RESOLVED
                active_session.ended_at = datetime.now(timezone.utc)
                await session.commit()

                await update.message.reply_text(t("room_end_done", lang), reply_markup=back_btn)

                if room_id:
                    try:
                        await context.bot.send_message(
                            chat_id=room_id,
                            text=t("room_end_resolved", patient_lang),
                            parse_mode="Markdown",
                        )
                    except Exception:
                        pass
                    await _cleanup_room(
                        context.bot, room_id,
                        patient_user.telegram_id if patient_user else None,
                        doctor_obj.telegram_id if doctor_obj else None,
                    )

                if patient_user:
                    try:
                        followup_kb = InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                f"{'⭐' * i}", callback_data=f"rate:{session_id}:{i}"
                            ) for i in range(1, 6)],
                            [InlineKeyboardButton(
                                "💬 Send Follow-Up Message",
                                callback_data=f"session_followup:{session_id}",
                            )],
                        ])
                        await context.bot.send_message(
                            chat_id=patient_user.telegram_id,
                            text=t("session_rate_prompt", patient_lang),
                            reply_markup=followup_kb,
                        )
                    except Exception as exc:
                        logger.error("Failed to send rating to patient: %s", exc)

            else:
                await session.commit()

                await update.message.reply_text(
                    t("room_end_waiting", lang), reply_markup=back_btn,
                )

                confirm_kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        t("room_end_confirm_button", patient_lang),
                        callback_data=f"confirm_end:{session_id}",
                    )],
                ])

                if room_id:
                    # Send confirm button in the consultation room
                    try:
                        await context.bot.send_message(
                            chat_id=room_id,
                            text=t("room_end_request", patient_lang, who=who_ended),
                            reply_markup=confirm_kb,
                        )
                    except Exception as exc:
                        logger.error("Failed to send confirm button in room: %s", exc)
                else:
                    # Relay session — send confirm button to the other party's DM
                    other_tg_id = None
                    if is_doctor_ending and patient_user:
                        other_tg_id = patient_user.telegram_id
                    elif not is_doctor_ending and doctor_obj and doctor_obj.telegram_id:
                        other_tg_id = doctor_obj.telegram_id

                    if other_tg_id:
                        try:
                            await context.bot.send_message(
                                chat_id=other_tg_id,
                                text=t("room_end_request", patient_lang if is_doctor_ending else "en", who=who_ended),
                                reply_markup=confirm_kb,
                            )
                        except Exception as exc:
                            logger.error("Failed to send confirm button to other party: %s", exc)

    except Exception as exc:
        logger.error("Error in /end command: %s", exc, exc_info=True)
        await update.message.reply_text(
            "Something went wrong. Please try again.",
            reply_markup=back_btn,
        )


async def confirm_end_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the 'Confirm End Session' button click in the consultation room."""
    query = update.callback_query
    await query.answer()

    session_id = int(query.data.split(":")[1])
    telegram_id = update.effective_user.id
    logger.info("confirm_end_callback fired: session=%d, user=%d, chat=%d", session_id, telegram_id, update.effective_chat.id)

    try:
        async with session_factory() as session:
            active_session = await session.get(ConsultSession, session_id)
            if not active_session or active_session.status != SessionStatus.ACTIVE:
                await query.edit_message_text("This session is no longer active.")
                return

            # Figure out who clicked the button
            doc_result = await session.execute(
                select(Doctor).where(Doctor.telegram_id == telegram_id)
            )
            doctor = doc_result.scalar_one_or_none()

            patient_user = await session.get(User, active_session.user_id)
            doctor_obj = await session.get(Doctor, active_session.doctor_id) if active_session.doctor_id else None

            is_doctor = doctor and doctor.id == active_session.doctor_id
            is_patient = patient_user and patient_user.telegram_id == telegram_id

            if not is_doctor and not is_patient:
                await query.answer("You are not part of this session.", show_alert=True)
                return

            # Only the OTHER party (who hasn't confirmed yet) can click this
            if is_doctor and active_session.resolution_confirmed_by_doctor:
                await query.answer("You already requested to end. Waiting for the other party.", show_alert=True)
                return
            if is_patient and active_session.resolution_confirmed_by_patient:
                await query.answer("You already requested to end. Waiting for the other party.", show_alert=True)
                return

            patient_lang = patient_user.language if patient_user else "en"

            if is_doctor:
                active_session.resolution_confirmed_by_doctor = True
            else:
                active_session.resolution_confirmed_by_patient = True

            both_confirmed = (
                active_session.resolution_confirmed_by_doctor
                and active_session.resolution_confirmed_by_patient
            )

            if not both_confirmed:
                await query.edit_message_text(
                    t("room_end_waiting", patient_lang)
                )
                return

            # Both confirmed — resolve
            active_session.status = SessionStatus.RESOLVED
            active_session.ended_at = datetime.now(timezone.utc)
            room_id = active_session.group_chat_id
            await session.commit()

        await query.edit_message_text(
            t("room_end_resolved", patient_lang),
            parse_mode="Markdown",
        )

        # Send rating to patient in DM
        if patient_user:
            try:
                followup_kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        f"{'⭐' * i}", callback_data=f"rate:{session_id}:{i}"
                    ) for i in range(1, 6)],
                    [InlineKeyboardButton(
                        "💬 Send Follow-Up Message",
                        callback_data=f"session_followup:{session_id}",
                    )],
                ])
                await context.bot.send_message(
                    chat_id=patient_user.telegram_id,
                    text=t("session_rate_prompt", patient_lang),
                    reply_markup=followup_kb,
                )
            except Exception as exc:
                logger.error("Failed to send rating to patient: %s", exc)

        # Notify doctor in DM
        if doctor_obj and doctor_obj.telegram_id:
            try:
                await context.bot.send_message(
                    chat_id=doctor_obj.telegram_id,
                    text=t("room_end_done", "en"),
                )
            except Exception:
                pass

        # Clean up room
        if room_id:
            await _cleanup_room(
                context.bot, room_id,
                patient_user.telegram_id if patient_user else None,
                doctor_obj.telegram_id if doctor_obj else None,
            )

    except Exception as exc:
        logger.error("Error in confirm_end_callback: %s", exc, exc_info=True)
        await query.edit_message_text("Something went wrong. Please try again.")


# ── Consultation room helpers ────────────────────────────────────────────

async def _find_available_room(session_id: int) -> int | None:
    """Find a consultation room not currently used by any non-resolved session."""
    room_ids = settings.room_ids
    if not room_ids:
        return None

    async with session_factory() as session:
        # Check ALL sessions with a room assigned that aren't finished
        result = await session.execute(
            select(ConsultSession.group_chat_id).where(
                ConsultSession.group_chat_id.isnot(None),
                ConsultSession.status.notin_([
                    SessionStatus.RESOLVED,
                    SessionStatus.CANCELLED,
                    SessionStatus.EXPIRED,
                ]),
            )
        )
        occupied = {row[0] for row in result.all()}

    for rid in room_ids:
        if rid not in occupied:
            return rid
    return None


async def _fallback_to_relay(context, session_id: int, patient_user, doctor_tg_id: int) -> None:
    """Switch session to RELAY mode and notify both parties."""
    async with session_factory() as db:
        s = await db.get(ConsultSession, session_id)
        s.session_mode = SessionMode.RELAY
        await db.commit()

    patient_lang = patient_user.language if patient_user else "en"

    if patient_user:
        try:
            await context.bot.send_message(
                chat_id=patient_user.telegram_id,
                text=t("room_fallback_patient", patient_lang),
            )
        except Exception:
            pass

    try:
        await context.bot.send_message(
            chat_id=doctor_tg_id,
            text=t("room_fallback_doctor", "en"),
        )
    except Exception:
        pass

    logger.info("Session #%d fell back to RELAY mode", session_id)


async def _cleanup_room(bot, room_id: int, patient_tg_id: int | None, doctor_tg_id: int | None) -> None:
    """Delete messages, kick users, and revoke invite links for a consultation room."""
    import asyncio

    # Step 1: DELETE MESSAGES FIRST (before kicking — bot needs members present)
    deleted = 0
    try:
        probe = await bot.send_message(chat_id=room_id, text="🧹")
        probe_id = probe.message_id

        # Build list of message IDs to delete (skip 1 — often undeletable system msg)
        all_ids = list(range(2, probe_id + 1))

        # Delete in batches of 100 (Telegram limit)
        for i in range(0, len(all_ids), 100):
            chunk = all_ids[i:i + 100]
            try:
                await bot.delete_messages(chat_id=room_id, message_ids=chunk)
                deleted += len(chunk)
            except Exception:
                # If batch fails, try smaller chunks
                for msg_id in chunk:
                    try:
                        await bot.delete_message(chat_id=room_id, message_id=msg_id)
                        deleted += 1
                    except Exception:
                        pass
    except Exception as exc:
        logger.warning("Room cleanup — could not delete messages in %s: %s", room_id, exc)

    # Step 2: BAN USERS (keeps them out — unbanned when next session assigns this room)
    for user_tg_id, role in [(patient_tg_id, "patient"), (doctor_tg_id, "doctor")]:
        if user_tg_id:
            try:
                await bot.ban_chat_member(chat_id=room_id, user_id=user_tg_id)
                logger.info("Banned %s %s from room %s", role, user_tg_id, room_id)
            except Exception as exc:
                logger.warning("Could not ban %s %s from room %s: %s", role, user_tg_id, room_id, exc)

    # Step 3: Users are BANNED so old invite links won't work.
    # They get unbanned when the next session assigns this room.

    logger.info("Room %s cleaned up (%d messages deleted)", room_id, deleted)


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
            patient_lang = patient_user.language if patient_user else "en"
            is_relay = s.session_mode == SessionMode.RELAY
            is_topic = s.session_mode == SessionMode.TOPIC
            issue_desc = s.issue_description[:100]
            doctor_name = doctor.full_name
            await session.commit()

        await query.edit_message_text(
            f"Session #{session_id} accepted and now ACTIVE.",
            reply_markup=back_btn,
        )

        # ── TOPIC mode: assign a consultation room ──
        if is_topic and settings.room_ids:
            room_id = await _find_available_room(session_id)

            if room_id:
                try:
                    # Save room on session
                    async with session_factory() as db:
                        s2 = await db.get(ConsultSession, session_id)
                        s2.group_chat_id = room_id
                        await db.commit()

                    # Unban users from previous sessions (they were banned on cleanup)
                    if patient_user:
                        try:
                            await context.bot.unban_chat_member(chat_id=room_id, user_id=patient_user.telegram_id)
                        except Exception:
                            pass
                    try:
                        await context.bot.unban_chat_member(chat_id=room_id, user_id=update.effective_user.id)
                    except Exception:
                        pass

                    # Create invite link
                    invite = await context.bot.create_chat_invite_link(
                        chat_id=room_id,
                        name=f"Session #{session_id}",
                    )

                    # Send welcome message in the room (patient's language)
                    await context.bot.send_message(
                        chat_id=room_id,
                        text=t("room_intro", patient_lang, session_id=session_id, doctor_name=doctor_name, issue=issue_desc),
                        parse_mode="Markdown",
                    )

                    room_kb = InlineKeyboardMarkup([
                        [InlineKeyboardButton(t("room_join_button", patient_lang), url=invite.invite_link)]
                    ])

                    # Notify patient
                    if patient_user:
                        try:
                            await context.bot.send_message(
                                chat_id=patient_user.telegram_id,
                                text=t("room_join_patient", patient_lang),
                                reply_markup=room_kb,
                            )
                        except Exception as exc:
                            logger.error("Failed to notify patient with room link: %s", exc)

                    # Notify doctor
                    try:
                        await context.bot.send_message(
                            chat_id=update.effective_user.id,
                            text=t("room_join_doctor", "en", session_id=session_id),
                            reply_markup=room_kb,
                        )
                    except Exception as exc:
                        logger.error("Failed to send room link to doctor: %s", exc)

                    logger.info("Session #%d assigned to room %s", session_id, room_id)

                except Exception as exc:
                    logger.error("Failed to set up room for session #%d: %s", session_id, exc, exc_info=True)
                    # Fallback to relay
                    await _fallback_to_relay(context, session_id, patient_user, update.effective_user.id)
            else:
                logger.warning("No rooms available for session #%d — falling back to relay", session_id)
                await _fallback_to_relay(context, session_id, patient_user, update.effective_user.id)

        # ── RELAY mode: patient stays in bot, doctor gets a room ──
        elif is_relay:
            # Try to assign a room for the doctor
            room_id = await _find_available_room(session_id) if settings.room_ids else None

            if room_id:
                try:
                    async with session_factory() as db:
                        s2 = await db.get(ConsultSession, session_id)
                        s2.group_chat_id = room_id
                        await db.commit()

                    # Unban doctor from previous sessions
                    try:
                        await context.bot.unban_chat_member(chat_id=room_id, user_id=update.effective_user.id)
                    except Exception:
                        pass

                    invite = await context.bot.create_chat_invite_link(
                        chat_id=room_id, name=f"Relay #{session_id}",
                    )

                    # Room intro for doctor
                    await context.bot.send_message(
                        chat_id=room_id,
                        text=(
                            f"🩺 *Anonymous Session #{session_id}*\n\n"
                            f"👨‍⚕️ *Doctor:* Dr. {doctor_name}\n"
                            f"📋 *Topic:* {issue_desc}\n\n"
                            f"The patient is anonymous. Type your messages here — "
                            f"the bot will relay them to the patient.\n"
                            f"Patient messages will appear here as 👤 Patient.\n\n"
                            f"⏹ Use /end when the session is complete."
                        ),
                        parse_mode="Markdown",
                    )

                    room_kb = InlineKeyboardMarkup([
                        [InlineKeyboardButton(t("room_join_button", "en"), url=invite.invite_link)]
                    ])

                    await context.bot.send_message(
                        chat_id=update.effective_user.id,
                        text=t("relay_doctor_instructions", "en"),
                        reply_markup=room_kb,
                    )

                    logger.info("Relay session #%d — doctor assigned to room %s", session_id, room_id)
                except Exception as exc:
                    logger.error("Failed to set up relay room for session #%d: %s", session_id, exc, exc_info=True)
                    # Fallback: pure DM relay
                    try:
                        await context.bot.send_message(
                            chat_id=update.effective_user.id,
                            text=t("relay_doctor_instructions", "en"),
                        )
                    except Exception:
                        pass
            else:
                # No rooms available — pure DM relay
                try:
                    await context.bot.send_message(
                        chat_id=update.effective_user.id,
                        text=t("relay_doctor_instructions", "en"),
                    )
                except Exception as exc:
                    logger.error("Failed to send relay instructions to doctor: %s", exc)

            # Always notify patient (they stay in bot DM)
            if patient_user:
                try:
                    await context.bot.send_message(
                        chat_id=patient_user.telegram_id,
                        text=t("relay_patient_instructions", patient_lang),
                    )
                except Exception as exc:
                    logger.error("Failed to notify patient of acceptance: %s", exc)

        # ── TOPIC mode but no rooms configured — fallback ──
        elif is_topic and not settings.room_ids:
            logger.warning("TOPIC session #%d but no rooms configured — falling back to RELAY", session_id)
            await _fallback_to_relay(context, session_id, patient_user, update.effective_user.id)

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
            declined_doctor_id = s.doctor_id

        await query.edit_message_text(
            f"Session #{session_id} declined. It will be reassigned to another doctor.",
            reply_markup=back_btn,
        )

        # Cancel existing timeout job and trigger immediate reassignment
        jobs = context.job_queue.get_jobs_by_name(f"doctor_timeout_{session_id}")
        for job in jobs:
            job.schedule_removal()
        # Also cancel retry jobs
        for i in range(2, 5):
            for job in context.job_queue.get_jobs_by_name(f"doctor_timeout_{session_id}_r{i}"):
                job.schedule_removal()

        # Notify patient once and start reassignment
        if patient_user:
            try:
                await context.bot.send_message(
                    chat_id=patient_user.telegram_id,
                    text="Your assigned doctor is unavailable. We're finding another doctor for you. Please hold.",
                )
            except Exception:
                pass

        # Trigger immediate reassignment (attempt=2 to skip patient re-notification since we just notified)
        from bot.handlers.private_session import _check_doctor_response
        context.job_queue.run_once(
            _check_doctor_response,
            when=5,  # near-instant
            data={"session_id": session_id, "attempt": 2, "tried_doctors": [declined_doctor_id]},
            name=f"doctor_timeout_{session_id}_decline",
        )

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


# ── Session follow-up (post-consultation message) ──────────────────────

async def session_followup_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Patient clicks 'Send Follow-Up Message' after session resolves."""
    query = update.callback_query
    await query.answer()
    session_id = int(query.data.split(":")[1])

    context.user_data["session_followup_id"] = session_id
    await query.edit_message_text(
        "💬 Type your follow-up message below.\n"
        "This will be sent directly to the doctor who treated you.\n\n"
        "Type /cancel to cancel."
    )


async def session_followup_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Forward a post-session follow-up message from patient to doctor."""
    session_id = context.user_data.get("session_followup_id")
    if not session_id:
        return

    text = update.message.text.strip()
    if text.startswith("/"):
        context.user_data.pop("session_followup_id", None)
        return

    try:
        async with session_factory() as session:
            s = await session.get(ConsultSession, session_id)
            if not s or not s.doctor_id:
                await update.message.reply_text("Session not found.", reply_markup=back_btn)
                context.user_data.pop("session_followup_id", None)
                return

            doctor = await session.get(Doctor, s.doctor_id)
            patient = await session.get(User, s.user_id)

        if doctor:
            patient_label = "Anonymous patient" if s.is_anonymous else f"Patient"
            bot_me = await context.bot.get_me()
            await context.bot.send_message(
                chat_id=doctor.telegram_id,
                text=(
                    f"💬 Post-Session Follow-Up (Session #{session_id})\n\n"
                    f"From: {patient_label}\n\n"
                    f"{text}"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "💬 Reply to Patient",
                        callback_data=f"session_reply:{session_id}",
                    )],
                ]),
            )

        await update.message.reply_text(
            "✅ Your follow-up message has been sent to the doctor.",
            reply_markup=back_btn,
        )

    except Exception as exc:
        logger.error("Session follow-up error: %s", exc, exc_info=True)
        await update.message.reply_text("Something went wrong. Please try again.", reply_markup=back_btn)

    context.user_data.pop("session_followup_id", None)


async def session_reply_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Doctor clicks 'Reply to Patient' for a post-session follow-up."""
    query = update.callback_query
    await query.answer()
    session_id = int(query.data.split(":")[1])

    context.user_data["session_reply_id"] = session_id
    await query.edit_message_text(
        "💬 Type your reply to the patient below.\n\n"
        "Type /cancel to cancel."
    )


async def session_reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Forward doctor's reply to patient for a post-session follow-up."""
    session_id = context.user_data.get("session_reply_id")
    if not session_id:
        return

    text = update.message.text.strip()
    if text.startswith("/"):
        context.user_data.pop("session_reply_id", None)
        return

    try:
        async with session_factory() as session:
            s = await session.get(ConsultSession, session_id)
            if not s:
                await update.message.reply_text("Session not found.", reply_markup=back_btn)
                context.user_data.pop("session_reply_id", None)
                return

            doctor = await session.get(Doctor, s.doctor_id) if s.doctor_id else None
            patient = await session.get(User, s.user_id)

        doc_name = f"Dr. {doctor.full_name}" if doctor else "Doctor"

        if patient:
            await context.bot.send_message(
                chat_id=patient.telegram_id,
                text=(
                    f"💬 Follow-Up Reply from {doc_name} (Session #{session_id})\n\n"
                    f"{text}"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "💬 Send Another Follow-Up",
                        callback_data=f"session_followup:{session_id}",
                    )],
                    [InlineKeyboardButton("← Back to Menu", callback_data="backtomenu")],
                ]),
            )

        await update.message.reply_text(
            "✅ Reply sent to the patient.",
            reply_markup=back_btn,
        )

    except Exception as exc:
        logger.error("Session reply error: %s", exc, exc_info=True)
        await update.message.reply_text("Something went wrong.", reply_markup=back_btn)

    context.user_data.pop("session_reply_id", None)


# ── Export ────────────────────────────────────────────────────────────────

navigation_handlers = [
    CommandHandler("menu", menu_command),
    CommandHandler("help", help_command),
    CommandHandler("end", end_command),
    CallbackQueryHandler(accept_session_callback, pattern=r"^accept_session:(\d+)$"),
    CallbackQueryHandler(decline_session_callback, pattern=r"^decline_session:(\d+)$"),
    CallbackQueryHandler(confirm_end_callback, pattern=r"^confirm_end:\d+$"),
    CallbackQueryHandler(back_to_menu_callback, pattern=r"^backtomenu$"),
    CallbackQueryHandler(session_followup_callback, pattern=r"^session_followup:\d+$"),
    CallbackQueryHandler(session_reply_callback, pattern=r"^session_reply:\d+$"),
]
