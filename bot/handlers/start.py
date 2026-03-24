from __future__ import annotations

import logging
from datetime import datetime, timezone

from telegram import Update
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
    consent_keyboard,
    language_keyboard,
    main_menu_keyboard,
    role_keyboard,
    doctor_menu_keyboard,
)

logger = logging.getLogger(__name__)

# States
LANGUAGE, CONSENT, ROLE, PATIENT_PHONE, DONE = range(5)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point — check if returning user, otherwise show language selector."""
    # Skip if this is a deep-link /start (has args)
    if context.args:
        return ConversationHandler.END

    # Check if user already exists and is fully onboarded
    from bot.database import session_factory
    from bot.models.user import User
    from bot.models.doctor import Doctor
    from sqlalchemy import select

    async with session_factory() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == update.effective_user.id)
        )
        user = result.scalar_one_or_none()

        # Check if they're a verified doctor
        doc_result = await session.execute(
            select(Doctor).where(
                Doctor.telegram_id == update.effective_user.id,
                Doctor.is_verified.is_(True),
            )
        )
        doctor = doc_result.scalar_one_or_none()

    # Returning user with phone → straight to menu
    if user and user.consent_given and user.phone:
        lang = user.language
        context.user_data["lang"] = lang

        if doctor:
            await update.message.reply_text(
                f"Welcome back, Dr. {doctor.full_name}! 👨‍⚕️",
                reply_markup=doctor_menu_keyboard(lang),
            )
        else:
            await update.message.reply_text(
                t("patient_ready", lang),
                reply_markup=main_menu_keyboard(lang),
            )
        return ConversationHandler.END

    # Returning user with consent but no phone → skip to role/phone
    if user and user.consent_given and not user.phone:
        lang = user.language
        context.user_data["lang"] = lang
        await update.message.reply_text(
            t("role_question", lang),
            reply_markup=role_keyboard(lang),
        )
        return ROLE

    # New user → full onboarding
    await update.message.reply_text(
        "Welcome to LongiMed 🏥\nConnecting you with verified Ethiopian doctors.\n\n"
        "ወደ LongiMed እንኳን ደህና መጡ 🏥",
        reply_markup=language_keyboard(),
    )
    return LANGUAGE


async def select_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    lang = query.data.split(":")[1]  # "lang:en" or "lang:am"
    context.user_data["lang"] = lang

    await query.edit_message_text(
        f"{t('disclaimer_title', lang)}\n\n{t('disclaimer_body', lang)}",
        reply_markup=consent_keyboard(lang),
    )
    return CONSENT


async def handle_consent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")

    if query.data == "consent:disagree":
        await query.edit_message_text(t("disagree_farewell", lang))
        return ConversationHandler.END

    # Record consent
    from bot.database import session_factory
    from bot.models.user import User
    from sqlalchemy import select

    async with session_factory() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == update.effective_user.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                telegram_id=update.effective_user.id,
                language=lang,
                consent_given=True,
                consent_timestamp=datetime.now(timezone.utc),
            )
            session.add(user)
        else:
            user.consent_given = True
            user.consent_timestamp = datetime.now(timezone.utc)
            user.language = lang

        await session.commit()

    await query.edit_message_text(
        t("role_question", lang),
        reply_markup=role_keyboard(lang),
    )
    return ROLE


async def handle_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")
    role = query.data.split(":")[1]  # "patient" or "doctor"

    if role == "doctor":
        from bot.config import settings
        await query.edit_message_text(
            f"{t('doctor_welcome', lang)}\n\n"
            f"Step 1 of 1 — tap below to open the registration portal.",
        )
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        await update.effective_message.reply_text(
            "The registration portal will open in your browser.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    t("btn_open_registration", lang),
                    web_app={"url": f"{settings.miniapp_url}/register"},
                )
            ]]),
        )
        return ConversationHandler.END

    # Patient — ask for phone
    from telegram import KeyboardButton, ReplyKeyboardMarkup
    await query.edit_message_text(t("patient_welcome", lang))
    await update.effective_message.reply_text(
        f"{t('phone_request', lang)}\n\nStep 1 of 1",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton(t("btn_share_phone", lang), request_contact=True)]],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )
    return PATIENT_PHONE


async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "en")

    if not update.message.contact:
        await update.message.reply_text(t("error_invalid_input", lang))
        return PATIENT_PHONE

    phone = update.message.contact.phone_number

    from bot.database import session_factory
    from bot.models.user import User
    from sqlalchemy import select
    from telegram import ReplyKeyboardRemove

    async with session_factory() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == update.effective_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.phone = phone
            await session.commit()

    await update.message.reply_text(
        t("patient_ready", lang),
        reply_markup=ReplyKeyboardRemove(),
    )
    await update.message.reply_text(
        "Here's your menu:",
        reply_markup=main_menu_keyboard(lang),
    )

    # Execute any pending deep link
    pending = context.user_data.pop("pending_deep_link", None)
    if pending:
        from bot.handlers.deep_link import _execute_deep_link
        await _execute_deep_link(update, context, pending)

    return ConversationHandler.END


async def handle_timeout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        lang = context.user_data.get("lang", "en")
        await update.effective_message.reply_text(t("timeout_message", lang))


start_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", cmd_start)],
    states={
        LANGUAGE: [CallbackQueryHandler(select_language, pattern=r"^lang:")],
        CONSENT: [CallbackQueryHandler(handle_consent, pattern=r"^consent:")],
        ROLE: [CallbackQueryHandler(handle_role, pattern=r"^role:")],
        PATIENT_PHONE: [MessageHandler(filters.CONTACT, handle_phone)],
    },
    fallbacks=[CommandHandler("start", cmd_start)],
    conversation_timeout=600,
    name="start_conv",
    per_message=False,
)
