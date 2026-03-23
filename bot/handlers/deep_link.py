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

    elif deep_link.type == DeepLinkType.REPORT:
        context.user_data["pending_report"] = deep_link.params
        await update.message.reply_text("Opening report form...")

    # Clear after execution
    context.user_data.pop("pending_deep_link", None)


deep_link_handler = CommandHandler("start", handle_deep_link, filters=None)
