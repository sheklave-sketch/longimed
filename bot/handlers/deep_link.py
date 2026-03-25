from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from bot.utils.deep_links import parse_payload, DeepLinkType

logger = logging.getLogger(__name__)


async def handle_deep_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles /start <payload> deep links.
    If user is not yet onboarded, store the payload and let start.py handle onboarding first.
    After onboarding completes, execute the stored payload action.
    """
    args = context.args
    if not args:
        return  # plain /start — handled by start_conv_handler

    payload = args[0]
    deep_link = parse_payload(payload)

    if not deep_link:
        logger.debug("Unknown deep link payload: %s", payload)
        return

    # Store for post-onboarding execution
    context.user_data["pending_deep_link"] = deep_link

    # Check if user is already onboarded
    from bot.database import session_factory
    from bot.models.user import User
    from sqlalchemy import select

    async with session_factory() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == update.effective_user.id)
        )
        user = result.scalar_one_or_none()

    if not user or not user.consent_given:
        # Let start handler pick up and onboard first
        return

    # User is onboarded — execute immediately
    await _execute_deep_link(update, context, deep_link)


async def _execute_deep_link(update, context, deep_link) -> None:
    from bot.utils.deep_links import DeepLinkType
    lang = context.user_data.get("lang", "en")

    if deep_link.type == DeepLinkType.BOOK_DOCTOR:
        context.user_data["preselected_doctor_id"] = deep_link.params["doctor_id"]
        await update.message.reply_text("Opening consultation booking... 🩺")
        # Private session flow will pick up preselected_doctor_id

    elif deep_link.type == DeepLinkType.DOCTOR_PROFILE:
        from bot.config import settings
        doc_id = deep_link.params["doctor_id"]
        await update.message.reply_text(
            f"View this doctor's profile:\n{settings.miniapp_url}/doctor/{doc_id}"
        )

    elif deep_link.type == DeepLinkType.WAITLIST_ACCEPT:
        context.user_data["waitlist_session_id"] = deep_link.params["session_id"]
        await update.message.reply_text("Checking your waitlist slot... ⏳")

    elif deep_link.type == DeepLinkType.DOCTOR_SIGNUP:
        await _handle_doctor_signup(update, context, deep_link.params["token"])

    elif deep_link.type == DeepLinkType.REPORT:
        context.user_data["pending_report"] = deep_link.params
        await update.message.reply_text("Opening report form...")

    # Clear after execution
    context.user_data.pop("pending_deep_link", None)


async def _handle_doctor_signup(update, context, token: str) -> None:
    """Link a Telegram account to a pre-registered doctor profile via signup token."""
    from bot.database import session_factory
    from bot.models.doctor import Doctor
    from bot.models.user import User
    from bot.utils.keyboards import doctor_menu_keyboard
    from bot.i18n import t
    from sqlalchemy import select
    from datetime import datetime, timezone

    telegram_id = update.effective_user.id
    lang = context.user_data.get("lang", "en")

    async with session_factory() as session:
        # Find doctor by token
        result = await session.execute(
            select(Doctor).where(Doctor.signup_token == token)
        )
        doctor = result.scalar_one_or_none()

        if not doctor:
            await update.message.reply_text(
                "This signup link is invalid or has already been used. Please contact admin."
            )
            return

        if doctor.telegram_id and doctor.telegram_id != 0 and doctor.telegram_id != telegram_id:
            await update.message.reply_text(
                "This doctor profile is already linked to another Telegram account. Please contact admin."
            )
            return

        # Link telegram account
        doctor.telegram_id = telegram_id
        doctor.signup_token = None  # one-time use

        # Ensure user record exists
        user_result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            user = User(
                telegram_id=telegram_id,
                language=lang,
                consent_given=True,
                consent_timestamp=datetime.now(timezone.utc),
            )
            session.add(user)

        await session.commit()

    context.user_data["lang"] = lang
    await update.message.reply_text(
        f"🎉 Welcome to LongiMed, Dr. {doctor.full_name}!\n\n"
        f"Your account has been verified and is ready to go.\n"
        f"Use the menu below to set your availability and start accepting patients.",
        reply_markup=doctor_menu_keyboard(lang),
    )


deep_link_handler = CommandHandler("start", handle_deep_link, filters=None)
