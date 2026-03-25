from __future__ import annotations

import functools
import logging
from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import settings

logger = logging.getLogger(__name__)


def admin_only(func: Callable) -> Callable:
    """Allow only users whose Telegram ID is in ADMIN_CHAT_IDS."""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in settings.admin_ids:
            from bot.i18n import t
            lang = context.user_data.get("lang", "en")
            await update.effective_message.reply_text(t("error_not_admin", lang))
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def doctor_only(func: Callable) -> Callable:
    """Allow only verified doctors."""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        from bot.database import session_factory
        from bot.models.doctor import Doctor
        from sqlalchemy import select

        user_id = update.effective_user.id
        async with session_factory() as session:
            result = await session.execute(
                select(Doctor).where(
                    Doctor.telegram_id == user_id,
                    Doctor.is_verified == True,  # noqa: E712
                )
            )
            doctor = result.scalar_one_or_none()

        if not doctor:
            from bot.i18n import t
            lang = context.user_data.get("lang", "en")
            await update.effective_message.reply_text(t("error_not_doctor", lang))
            return

        context.user_data["doctor"] = doctor
        return await func(update, context, *args, **kwargs)
    return wrapper


def moderator_only(func: Callable) -> Callable:
    """Allow admins and designated moderators."""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id

        if user_id in settings.admin_ids:
            return await func(update, context, *args, **kwargs)

        from bot.database import session_factory
        from bot.models.moderator import Moderator
        from sqlalchemy import select

        async with session_factory() as session:
            result = await session.execute(
                select(Moderator).where(Moderator.telegram_id == user_id)
            )
            moderator = result.scalar_one_or_none()

        if not moderator:
            from bot.i18n import t
            lang = context.user_data.get("lang", "en")
            await update.effective_message.reply_text(t("error_not_moderator", lang))
            return

        context.user_data["moderator"] = moderator
        return await func(update, context, *args, **kwargs)
    return wrapper
