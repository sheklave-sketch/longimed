from __future__ import annotations

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.i18n import t
from bot.utils.emergency import is_emergency

logger = logging.getLogger(__name__)

HOSPITAL_MAPS_URL = "https://www.google.com/maps/search/hospital+near+me"


async def handle_emergency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    if not is_emergency(update.message.text):
        return

    lang = context.user_data.get("lang", "en")
    user_id = update.effective_user.id

    logger.warning("EMERGENCY triggered | user_id=%s | text=%s", user_id, update.message.text[:80])

    # Log to DB (non-blocking — don't let DB failure block emergency message)
    try:
        from bot.database import session_factory
        from bot.models.notification import Notification
        async with session_factory() as session:
            session.add(Notification(
                user_id=0,  # placeholder until user is resolved
                type="emergency_trigger",
                payload={"telegram_id": user_id, "text": update.message.text[:200]},
            ))
            await session.commit()
    except Exception as exc:
        logger.error("Failed to log emergency to DB: %s", exc)

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(t("btn_nearest_hospital", lang), url=HOSPITAL_MAPS_URL)
    ]])

    await update.message.reply_text(
        f"{t('emergency_title', lang)}\n\n{t('emergency_body', lang)}",
        reply_markup=keyboard,
    )


# Register with group=-1 so it fires before all ConversationHandlers
emergency_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_emergency)
