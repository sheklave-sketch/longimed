"""
Private Consultation Flow.

Hybrid approach:
  - Anonymous → RELAY mode (bot forwards msgs between patient ↔ doctor)
  - Non-anonymous → TOPIC mode (forum thread in supergroup)

States:
  CHECK_ELIGIBILITY (20) → SELECT_PACKAGE (21) → SELECT_SPECIALTY (22)
  → SELECT_DOCTOR (23) → ENTER_ISSUE (24) → ANONYMITY (25)
  → CONFIRM (26) → PAYMENT (27) → ACTIVE_RELAY (28)
"""

import logging
from datetime import datetime, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.i18n import t
from bot.utils.keyboards import (
    anonymous_keyboard,
    category_keyboard,
    confirm_cancel_keyboard,
    doctor_list_keyboard,
    rating_keyboard,
    waitlist_keyboard,
)

logger = logging.getLogger(__name__)

# States
CHECK_ELIGIBILITY = 20
SELECT_PACKAGE = 21
SELECT_SPECIALTY = 22
SELECT_DOCTOR = 23
ENTER_ISSUE = 24
ANONYMITY = 25
CONFIRM = 26
PAYMENT = 27
ACTIVE_RELAY = 28


# ── Entry ─────────────────────────────────────────────────────────────────

async def start_private_session(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")

    from bot.database import session_factory
    from bot.models.user import User
    from sqlalchemy import select

    async with session_factory() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == update.effective_user.id)
        )
        user = result.scalar_one_or_none()

    if not user or not user.consent_given:
        await query.edit_message_text(t("error_not_registered", lang))
        return ConversationHandler.END

    context.user_data["session_user_id"] = user.id
    has_free_trial = not user.free_trial_used

    await query.edit_message_text(
        f"🩺 *Private Consultation*\n\n{t('session_intro', lang)}\n\n"
        f"Step 1 of 6 — {t('session_select_package', lang)}",
        parse_mode="Markdown",
        reply_markup=_package_keyboard(lang, has_free_trial),
    )
    return SELECT_PACKAGE


# ── Step 1: Package ───────────────────────────────────────────────────────

def _package_keyboard(lang: str, has_free_trial: bool) -> InlineKeyboardMarkup:
    buttons = []
    if has_free_trial:
        buttons.append([InlineKeyboardButton(
            t("btn_free_trial", lang), callback_data="pkg:free_trial"
        )])
    buttons.append([InlineKeyboardButton(
        t("btn_single_session", lang, price="500"),
        callback_data="pkg:single"
    )])
    buttons.append([InlineKeyboardButton(t("btn_back", lang), callback_data="back")])
    return InlineKeyboardMarkup(buttons)


async def select_package(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "back":
        return await _back_to_menu(update, context)

    lang = context.user_data.get("lang", "en")
    package = query.data.split(":")[1]
    context.user_data["session_package"] = package

    await query.edit_message_text(
        f"Step 2 of 6 — {t('session_select_specialty', lang)}",
        reply_markup=category_keyboard(lang),
    )
    return SELECT_SPECIALTY


# ── Step 2: Specialty ─────────────────────────────────────────────────────

async def select_specialty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "back":
        lang = context.user_data.get("lang", "en")
        has_trial = context.user_data.get("session_package") != "single"
        await query.edit_message_text(
            f"Step 1 of 6 — {t('session_select_package', lang)}",
            reply_markup=_package_keyboard(lang, has_trial),
        )
        return SELECT_PACKAGE

    lang = context.user_data.get("lang", "en")
    specialty = query.data.split(":")[1]
    context.user_data["session_specialty"] = specialty

    # Fetch available doctors
    from bot.database import session_factory
    from bot.models.doctor import Doctor, Specialty
    from sqlalchemy import select

    async with session_factory() as session:
        result = await session.execute(
            select(Doctor).where(
                Doctor.specialty == Specialty(specialty),
                Doctor.is_verified.is_(True),
                Doctor.is_available.is_(True),
            )
        )
        doctors = result.scalars().all()

    if not doctors:
        await query.edit_message_text(
            t("session_no_doctors", lang),
            reply_markup=waitlist_keyboard(lang),
        )
        return SELECT_DOCTOR

    # Check if doctor was preselected via deep link
    preselected = context.user_data.pop("preselected_doctor_id", None)
    if preselected:
        context.user_data["session_doctor_id"] = preselected
        doc = next((d for d in doctors if d.id == preselected), None)
        if doc:
            context.user_data["session_doctor_name"] = doc.full_name
            await query.edit_message_text(
                f"Step 4 of 6 — {t('session_enter_issue', lang)}\n\n"
                f"_Your doctor: Dr. {doc.full_name}_",
                parse_mode="Markdown",
            )
            return ENTER_ISSUE

    await query.edit_message_text(
        f"Step 3 of 6 — {t('session_select_doctor', lang, specialty=specialty.title())}",
        reply_markup=doctor_list_keyboard(doctors, lang),
    )
    return SELECT_DOCTOR


# ── Step 3: Doctor ────────────────────────────────────────────────────────

async def select_doctor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")

    if query.data == "back":
        await query.edit_message_text(
            f"Step 2 of 6 — {t('session_select_specialty', lang)}",
            reply_markup=category_keyboard(lang),
        )
        return SELECT_SPECIALTY

    if query.data == "waitlist:join":
        return await _join_waitlist(update, context)

    doctor_id = int(query.data.split(":")[1])
    context.user_data["session_doctor_id"] = doctor_id

    from bot.database import session_factory
    from bot.models.doctor import Doctor

    async with session_factory() as session:
        doc = await session.get(Doctor, doctor_id)
        if doc:
            context.user_data["session_doctor_name"] = doc.full_name

    await query.edit_message_text(
        f"Step 4 of 6 — {t('session_enter_issue', lang)}",
    )
    return ENTER_ISSUE


# ── Step 4: Issue description ─────────────────────────────────────────────

async def enter_issue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "en")
    text = update.message.text.strip()

    if len(text) < 10:
        await update.message.reply_text("Please provide a bit more detail (at least 10 characters).")
        return ENTER_ISSUE

    context.user_data["session_issue"] = text

    await update.message.reply_text(
        f"Step 5 of 6 — {t('qa_anonymous_prompt', lang)}",
        reply_markup=anonymous_keyboard(lang),
    )
    return ANONYMITY


# ── Step 5: Anonymity ─────────────────────────────────────────────────────

async def select_anonymity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")

    if query.data == "back":
        await query.edit_message_text(f"Step 4 of 6 — {t('session_enter_issue', lang)}")
        return ENTER_ISSUE

    is_anonymous = query.data == "anon:yes"
    context.user_data["session_anonymous"] = is_anonymous
    mode = "RELAY (Anonymous)" if is_anonymous else "TOPIC (Named)"
    doctor_name = context.user_data.get("session_doctor_name", "—")
    package = context.user_data.get("session_package", "")
    pkg_label = "Free Trial (15 min)" if package == "free_trial" else "Single Session (30 min)"

    await query.edit_message_text(
        f"Step 6 of 6 — *Confirm your session*\n\n"
        f"👨‍⚕️ Doctor: Dr. {doctor_name}\n"
        f"📦 Package: {pkg_label}\n"
        f"👁 Mode: {mode}\n"
        f"📝 Issue: _{context.user_data.get('session_issue', '')[:100]}_",
        parse_mode="Markdown",
        reply_markup=confirm_cancel_keyboard(lang),
    )
    return CONFIRM


# ── Step 6: Confirm + save ────────────────────────────────────────────────

async def confirm_session(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")

    if query.data == "cancel":
        await query.edit_message_text("Session cancelled. Send /start to return to the menu.")
        _cleanup(context)
        return ConversationHandler.END

    if query.data == "edit":
        await query.edit_message_text(f"Step 4 of 6 — {t('session_enter_issue', lang)}")
        return ENTER_ISSUE

    package = context.user_data.get("session_package")
    is_anonymous = context.user_data.get("session_anonymous", False)

    from bot.database import session_factory
    from bot.models.session import Session, SessionPackage, SessionStatus, SessionMode
    from bot.models.user import User
    from bot.models.payment import Payment, PaymentProvider, PaymentStatus
    from sqlalchemy import select

    async with session_factory() as session:
        # Get user
        result = await session.execute(
            select(User).where(User.telegram_id == update.effective_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await query.edit_message_text(t("error_not_registered", lang))
            _cleanup(context)
            return ConversationHandler.END

        # Determine package + payment
        pkg_enum = SessionPackage.FREE_TRIAL if package == "free_trial" else SessionPackage.SINGLE
        session_mode = SessionMode.RELAY if is_anonymous else SessionMode.TOPIC
        payment_id = None

        if package == "free_trial":
            # Phone gate: check free trial not used by this phone
            if user.free_trial_used:
                await query.edit_message_text(
                    "You've already used your free trial. Please select a paid session."
                )
                _cleanup(context)
                return ConversationHandler.END
        else:
            # Create pending manual payment
            payment = Payment(
                user_id=user.id,
                amount_etb=500,
                provider=PaymentProvider.MANUAL,
                status=PaymentStatus.PENDING,
            )
            session.add(payment)
            await session.flush()
            payment_id = payment.id

        # Create session
        new_session = Session(
            user_id=user.id,
            doctor_id=context.user_data.get("session_doctor_id"),
            package=pkg_enum,
            status=SessionStatus.PENDING_APPROVAL if package != "free_trial" else SessionStatus.AWAITING_DOCTOR,
            session_mode=session_mode,
            issue_description=context.user_data.get("session_issue", ""),
            is_anonymous=is_anonymous,
            payment_id=payment_id,
        )

        if package == "free_trial":
            user.free_trial_used = True

        session.add(new_session)
        await session.flush()
        session_id = new_session.id
        session_status = new_session.status
        await session.commit()

    # Different flow for free trial vs paid
    if package == "free_trial":
        await query.edit_message_text(t("session_awaiting", lang))
        # Notify the doctor
        await _notify_doctor_new_session(context, session_id, lang)
        # Start response timer
        await _start_doctor_timer(context, session_id)
    else:
        # Send payment instructions
        await query.edit_message_text(
            t("payment_manual_instructions", lang,
              amount="500",
              bank_name="Commercial Bank of Ethiopia",
              account_number="1000XXXXXXXX",
              account_name="LongiMed Health Services"),
        )
        await query.message.reply_text(t("payment_pending", lang))
        # Notify admin of pending payment
        await _notify_admin_pending_payment(context, session_id, update.effective_user.id, lang)

    _cleanup(context)
    return ConversationHandler.END


# ── Relay mode: forward messages ──────────────────────────────────────────

async def relay_patient_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Forward patient message to doctor via relay (anonymous sessions)."""
    from bot.database import session_factory
    from bot.models.session import Session, SessionStatus, SessionMode
    from bot.models.relay_message import RelayMessage, SenderRole
    from bot.models.user import User
    from sqlalchemy import select

    async with session_factory() as session:
        result = await session.execute(
            select(Session).where(
                Session.status == SessionStatus.ACTIVE,
                Session.session_mode == SessionMode.RELAY,
            ).join(User, Session.user_id == User.id).where(
                User.telegram_id == update.effective_user.id
            )
        )
        active_session = result.scalar_one_or_none()

        if not active_session or not active_session.doctor_id:
            return

        # Store message
        msg = RelayMessage(
            session_id=active_session.id,
            sender_role=SenderRole.PATIENT,
            telegram_message_id=update.message.message_id,
            content=update.message.text,
            media_type=_get_media_type(update.message),
            media_file_id=_get_file_id(update.message),
        )
        session.add(msg)
        await session.commit()

        # Get doctor telegram_id
        from bot.models.doctor import Doctor
        doctor = await session.get(Doctor, active_session.doctor_id)

    if doctor:
        prefix = "👤 Patient:"
        if update.message.text:
            await context.bot.send_message(
                chat_id=doctor.telegram_id,
                text=f"{prefix}\n{update.message.text}",
            )
        elif update.message.photo:
            await context.bot.send_photo(
                chat_id=doctor.telegram_id,
                photo=update.message.photo[-1].file_id,
                caption=f"{prefix} [Photo]",
            )
        elif update.message.voice:
            await context.bot.send_voice(
                chat_id=doctor.telegram_id,
                voice=update.message.voice.file_id,
                caption=prefix,
            )
        elif update.message.document:
            await context.bot.send_document(
                chat_id=doctor.telegram_id,
                document=update.message.document.file_id,
                caption=prefix,
            )


async def relay_doctor_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Forward doctor message to patient via relay (anonymous sessions)."""
    from bot.database import session_factory
    from bot.models.session import Session, SessionStatus, SessionMode
    from bot.models.relay_message import RelayMessage, SenderRole
    from bot.models.doctor import Doctor
    from bot.models.user import User
    from sqlalchemy import select

    async with session_factory() as session:
        # Find active relay session for this doctor
        result = await session.execute(
            select(Session).where(
                Session.status == SessionStatus.ACTIVE,
                Session.session_mode == SessionMode.RELAY,
            ).join(Doctor, Session.doctor_id == Doctor.id).where(
                Doctor.telegram_id == update.effective_user.id
            )
        )
        active_session = result.scalar_one_or_none()

        if not active_session:
            return

        msg = RelayMessage(
            session_id=active_session.id,
            sender_role=SenderRole.DOCTOR,
            telegram_message_id=update.message.message_id,
            content=update.message.text,
            media_type=_get_media_type(update.message),
            media_file_id=_get_file_id(update.message),
        )
        session.add(msg)
        await session.commit()

        user = await session.get(User, active_session.user_id)

    if user:
        prefix = "👨‍⚕️ Doctor:"
        if update.message.text:
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text=f"{prefix}\n{update.message.text}",
            )
        elif update.message.photo:
            await context.bot.send_photo(
                chat_id=user.telegram_id,
                photo=update.message.photo[-1].file_id,
                caption=f"{prefix} [Photo]",
            )
        elif update.message.voice:
            await context.bot.send_voice(
                chat_id=user.telegram_id,
                voice=update.message.voice.file_id,
                caption=prefix,
            )
        elif update.message.document:
            await context.bot.send_document(
                chat_id=user.telegram_id,
                document=update.message.document.file_id,
                caption=prefix,
            )


# ── Rating callback ───────────────────────────────────────────────────────

async def handle_rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    session_id = int(parts[1])
    stars = int(parts[2])
    lang = context.user_data.get("lang", "en")

    from bot.database import session_factory
    from bot.models.session import Session
    from bot.models.doctor import Doctor

    async with session_factory() as session:
        s = await session.get(Session, session_id)
        if not s:
            return
        s.rating = stars
        await session.commit()

        # Update doctor average
        if s.doctor_id:
            doctor = await session.get(Doctor, s.doctor_id)
            if doctor:
                total = doctor.rating_avg * doctor.rating_count + stars
                doctor.rating_count += 1
                doctor.rating_avg = round(total / doctor.rating_count, 2)
                await session.commit()

    await query.edit_message_text(f"{'⭐' * stars}\n\n{t('rate_thanks', lang)}")


# ── Helpers ───────────────────────────────────────────────────────────────

async def _notify_doctor_new_session(context, session_id: int, lang: str) -> None:
    from bot.database import session_factory
    from bot.models.session import Session
    from bot.models.doctor import Doctor

    async with session_factory() as session:
        s = await session.get(Session, session_id)
        if not s or not s.doctor_id:
            return
        doctor = await session.get(Doctor, s.doctor_id)

    if doctor:
        mode_label = "Anonymous (relay)" if s.is_anonymous else "Named (topic)"
        try:
            await context.bot.send_message(
                chat_id=doctor.telegram_id,
                text=(
                    f"🔔 *New consultation request* (#{session_id})\n\n"
                    f"Mode: {mode_label}\n"
                    f"Issue: _{s.issue_description[:200]}_\n\n"
                    f"Use /accept_session {session_id} to start."
                ),
                parse_mode="Markdown",
            )
        except Exception as exc:
            logger.error("Failed to notify doctor: %s", exc)


async def _start_doctor_timer(context, session_id: int) -> None:
    from bot.config import settings
    context.job_queue.run_once(
        _check_doctor_response,
        when=settings.doctor_response_timeout_mins * 60,
        data={"session_id": session_id},
        name=f"doctor_timeout_{session_id}",
    )


async def _check_doctor_response(context: ContextTypes.DEFAULT_TYPE) -> None:
    session_id = context.job.data["session_id"]

    from bot.database import session_factory
    from bot.models.session import Session, SessionStatus
    from bot.models.doctor import Doctor
    from bot.models.user import User
    from sqlalchemy import select

    async with session_factory() as session:
        s = await session.get(Session, session_id)
        if not s or s.status != SessionStatus.AWAITING_DOCTOR:
            return

        # Auto-reassign: find another available doctor in same specialty
        current_doctor_id = s.doctor_id
        result = await session.execute(
            select(Doctor).where(
                Doctor.is_verified.is_(True),
                Doctor.is_available.is_(True),
                Doctor.id != current_doctor_id,
            )
        )
        next_doctor = result.scalars().first()

        patient = await session.get(User, s.user_id)

        if next_doctor:
            s.doctor_id = next_doctor.id
            await session.commit()

            # Notify new doctor
            try:
                await context.bot.send_message(
                    chat_id=next_doctor.telegram_id,
                    text=f"🔔 Reassigned session #{session_id}. Use /accept_session {session_id}.",
                )
            except Exception:
                pass

            # Notify patient
            if patient:
                try:
                    await context.bot.send_message(
                        chat_id=patient.telegram_id,
                        text="Your doctor was unavailable. We've reassigned you to another doctor. Please hold. 🕐",
                    )
                except Exception:
                    pass

            # Restart timer for new doctor
            context.job_queue.run_once(
                _check_doctor_response,
                when=600,
                data={"session_id": session_id},
                name=f"doctor_timeout_{session_id}_retry",
            )
        else:
            # No doctors available — notify admin + patient
            s.status = SessionStatus.CANCELLED
            await session.commit()

            if patient:
                try:
                    await context.bot.send_message(
                        chat_id=patient.telegram_id,
                        text="No doctors are available right now. 😔 Your session has been cancelled. You won't be charged.",
                    )
                except Exception:
                    pass

            from bot.config import settings
            for admin_id in settings.admin_chat_ids:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"⚠️ Session #{session_id} cancelled — no doctors responded.",
                    )
                except Exception:
                    pass


async def _notify_admin_pending_payment(context, session_id: int, telegram_id: int, lang: str) -> None:
    from bot.config import settings
    for admin_id in settings.admin_chat_ids:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"💰 *Pending payment* for session #{session_id}\n"
                    f"Patient TG ID: {telegram_id}\n\n"
                    f"Use /confirm_payment {telegram_id} 500 once transfer is verified."
                ),
                parse_mode="Markdown",
            )
        except Exception:
            pass


async def _join_waitlist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    lang = context.user_data.get("lang", "en")

    from bot.database import session_factory
    from bot.models.waitlist import Waitlist, WaitlistStatus
    from bot.models.user import User
    from sqlalchemy import select, func

    async with session_factory() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == update.effective_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await query.edit_message_text(t("error_not_registered", lang))
            return ConversationHandler.END

        # Get current max position
        max_pos = await session.execute(
            select(func.max(Waitlist.position)).where(
                Waitlist.specialty == context.user_data.get("session_specialty", ""),
                Waitlist.status == WaitlistStatus.WAITING,
            )
        )
        position = (max_pos.scalar() or 0) + 1

        entry = Waitlist(
            user_id=user.id,
            doctor_id=context.user_data.get("session_doctor_id"),
            specialty=context.user_data.get("session_specialty", ""),
            position=position,
            status=WaitlistStatus.WAITING,
        )
        session.add(entry)
        await session.commit()

    await query.edit_message_text(t("waitlist_joined", lang, position=position))
    _cleanup(context)
    return ConversationHandler.END


async def _back_to_menu(update, context) -> int:
    lang = context.user_data.get("lang", "en")
    from bot.utils.keyboards import main_menu_keyboard
    await update.callback_query.edit_message_text("Main menu:", reply_markup=main_menu_keyboard(lang))
    _cleanup(context)
    return ConversationHandler.END


def _cleanup(context) -> None:
    for key in ("session_user_id", "session_package", "session_specialty",
                "session_doctor_id", "session_doctor_name", "session_issue",
                "session_anonymous"):
        context.user_data.pop(key, None)


def _get_media_type(message) -> str | None:
    if message.photo:
        return "photo"
    if message.voice:
        return "voice"
    if message.document:
        return "document"
    if message.video:
        return "video"
    return None


def _get_file_id(message) -> str | None:
    if message.photo:
        return message.photo[-1].file_id
    if message.voice:
        return message.voice.file_id
    if message.document:
        return message.document.file_id
    if message.video:
        return message.video.file_id
    return None


# ── Handler assembly ──────────────────────────────────────────────────────

private_session_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_private_session, pattern=r"^menu:consult$"),
    ],
    states={
        SELECT_PACKAGE: [
            CallbackQueryHandler(select_package, pattern=r"^(pkg:|back)"),
        ],
        SELECT_SPECIALTY: [
            CallbackQueryHandler(select_specialty, pattern=r"^(cat:|back)"),
        ],
        SELECT_DOCTOR: [
            CallbackQueryHandler(select_doctor, pattern=r"^(selectdoc:|waitlist:|back)"),
        ],
        ENTER_ISSUE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, enter_issue),
        ],
        ANONYMITY: [
            CallbackQueryHandler(select_anonymity, pattern=r"^(anon:|back)"),
        ],
        CONFIRM: [
            CallbackQueryHandler(confirm_session, pattern=r"^(confirm|cancel|edit)$"),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(_back_to_menu, pattern=r"^cancel$"),
    ],
    conversation_timeout=600,
    name="private_session_conv",
    per_message=False,
)

# Rating handler (standalone — fires from any chat)
rating_handler = CallbackQueryHandler(handle_rating, pattern=r"^rate:\d+:\d+$")
