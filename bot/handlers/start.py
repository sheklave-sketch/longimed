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
# Doctor registration states
DOC_NAME, DOC_LICENSE, DOC_SPECIALTY, DOC_LANGUAGES, DOC_BIO, DOC_PHOTO, DOC_CONFIRM = range(50, 57)


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
        # Check if already registered
        from bot.database import session_factory
        from bot.models.doctor import Doctor
        from sqlalchemy import select
        async with session_factory() as session:
            result = await session.execute(
                select(Doctor).where(Doctor.telegram_id == update.effective_user.id)
            )
            existing = result.scalar_one_or_none()

        if existing:
            if existing.is_verified:
                await query.edit_message_text(
                    f"Welcome back, Dr. {existing.full_name}! 👨‍⚕️",
                    reply_markup=doctor_menu_keyboard(lang),
                )
                return ConversationHandler.END
            else:
                await query.edit_message_text(
                    "Your application is still under review. We'll notify you once verified. 🕐"
                )
                return ConversationHandler.END

        await query.edit_message_text(
            f"{t('doctor_welcome', lang)}\n\n"
            f"Step 1 of 6 — What is your full name?"
        )
        return DOC_NAME

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


# ── Doctor Registration Steps ─────────────────────────────────────────────

async def doc_receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "en")
    name = update.message.text.strip()
    if len(name) < 3:
        await update.message.reply_text("Please enter your full name (at least 3 characters).")
        return DOC_NAME
    context.user_data["doc_name"] = name
    await update.message.reply_text(
        f"Thank you, Dr. {name}.\n\n"
        f"Step 2 of 6 — What is your medical license number?"
    )
    return DOC_LICENSE


async def doc_receive_license(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "en")
    license_num = update.message.text.strip()
    if len(license_num) < 3:
        await update.message.reply_text("Please enter a valid license number.")
        return DOC_LICENSE

    # Check uniqueness
    from bot.database import session_factory
    from bot.models.doctor import Doctor
    from sqlalchemy import select
    async with session_factory() as session:
        result = await session.execute(
            select(Doctor).where(Doctor.license_number == license_num)
        )
        if result.scalar_one_or_none():
            await update.message.reply_text("This license number is already registered. Please check and try again.")
            return DOC_LICENSE

    context.user_data["doc_license"] = license_num

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from bot.models.doctor import Specialty
    buttons = [
        [InlineKeyboardButton(s.value.title(), callback_data=f"docspec:{s.value}")]
        for s in Specialty
    ]
    await update.message.reply_text(
        "Step 3 of 6 — What is your specialty?",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return DOC_SPECIALTY


async def doc_select_specialty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    specialty = query.data.split(":")[1]
    context.user_data["doc_specialty"] = specialty

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    lang_buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="doclang:en"),
            InlineKeyboardButton("🇪🇹 Amharic", callback_data="doclang:am"),
        ],
        [InlineKeyboardButton("Both", callback_data="doclang:both")],
    ])
    await query.edit_message_text(
        "Step 4 of 6 — What languages do you consult in?",
        reply_markup=lang_buttons,
    )
    return DOC_LANGUAGES


async def doc_select_languages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data.split(":")[1]
    if choice == "both":
        context.user_data["doc_languages"] = ["en", "am"]
    else:
        context.user_data["doc_languages"] = [choice]

    await query.edit_message_text(
        "Step 5 of 6 — Write a short bio about yourself.\n\n"
        "This will be visible to patients. Include your experience and areas of focus."
    )
    return DOC_BIO


async def doc_receive_bio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    bio = update.message.text.strip()
    if len(bio) < 10:
        await update.message.reply_text("Please write at least a few sentences about yourself.")
        return DOC_BIO
    context.user_data["doc_bio"] = bio
    await update.message.reply_text(
        "Step 6 of 6 — Please upload a photo of your medical license.\n\n"
        "This is required for verification. You can send it as a photo or document."
    )
    return DOC_PHOTO


async def doc_receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "en")

    # Accept photo or document
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
    elif update.message.document:
        file_id = update.message.document.file_id
    else:
        await update.message.reply_text("Please send a photo or document of your license.")
        return DOC_PHOTO

    context.user_data["doc_license_file_id"] = file_id

    name = context.user_data.get("doc_name", "")
    license_num = context.user_data.get("doc_license", "")
    specialty = context.user_data.get("doc_specialty", "")
    languages = context.user_data.get("doc_languages", [])
    bio = context.user_data.get("doc_bio", "")

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    await update.message.reply_text(
        f"Please confirm your registration:\n\n"
        f"👤 Name: Dr. {name}\n"
        f"📋 License: {license_num}\n"
        f"🏥 Specialty: {specialty.title()}\n"
        f"🗣 Languages: {', '.join(languages)}\n"
        f"📝 Bio: {bio[:100]}...\n"
        f"📄 License document: Uploaded",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Submit Application", callback_data="docsubmit:yes"),
                InlineKeyboardButton("✖ Cancel", callback_data="docsubmit:no"),
            ]
        ]),
    )
    return DOC_CONFIRM


async def doc_confirm_submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")

    if query.data == "docsubmit:no":
        await query.edit_message_text("Registration cancelled. Send /start to try again.")
        _doc_cleanup(context)
        return ConversationHandler.END

    from bot.database import session_factory
    from bot.models.doctor import Doctor, Specialty, RegistrationStatus
    from datetime import datetime, timezone

    async with session_factory() as session:
        doctor = Doctor(
            telegram_id=update.effective_user.id,
            full_name=context.user_data.get("doc_name", ""),
            license_number=context.user_data.get("doc_license", ""),
            specialty=Specialty(context.user_data.get("doc_specialty", "general")),
            languages=context.user_data.get("doc_languages", ["en"]),
            bio=context.user_data.get("doc_bio", ""),
            license_document_file_id=context.user_data.get("doc_license_file_id"),
            is_verified=False,
            is_available=False,
            registration_status=RegistrationStatus.PENDING,
            applied_at=datetime.now(timezone.utc),
        )
        session.add(doctor)
        await session.flush()
        doctor_id = doctor.id
        await session.commit()

    await query.edit_message_text(t("doctor_submitted", lang))

    # Notify admins with approve/reject buttons
    from bot.config import settings
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    admin_text = (
        f"👨‍⚕️ New Doctor Application (#{doctor_id})\n\n"
        f"Name: Dr. {context.user_data.get('doc_name')}\n"
        f"License: {context.user_data.get('doc_license')}\n"
        f"Specialty: {context.user_data.get('doc_specialty', '').title()}\n"
        f"Languages: {', '.join(context.user_data.get('doc_languages', []))}\n"
        f"Bio: {context.user_data.get('doc_bio', '')[:200]}"
    )
    admin_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"docmod:approve:{doctor_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"docmod:reject:{doctor_id}"),
        ],
        [InlineKeyboardButton("📄 View License", callback_data=f"docmod:license:{doctor_id}")],
    ])

    for admin_id in settings.admin_ids:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_text,
                reply_markup=admin_keyboard,
            )
        except Exception:
            pass

    _doc_cleanup(context)
    return ConversationHandler.END


def _doc_cleanup(context) -> None:
    for k in ("doc_name", "doc_license", "doc_specialty", "doc_languages", "doc_bio", "doc_license_file_id"):
        context.user_data.pop(k, None)


# ── Admin: Approve/Reject Doctor Application ──────────────────────────────

async def approve_doctor_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    from bot.config import settings
    if update.effective_user.id not in settings.admin_ids:
        return

    doctor_id = int(query.data.split(":")[2])

    from bot.database import session_factory
    from bot.models.doctor import Doctor, RegistrationStatus

    async with session_factory() as session:
        doctor = await session.get(Doctor, doctor_id)
        if not doctor:
            await query.edit_message_text("Doctor not found.")
            return
        doctor.is_verified = True
        doctor.registration_status = RegistrationStatus.APPROVED
        telegram_id = doctor.telegram_id
        name = doctor.full_name
        await session.commit()

    # Notify doctor
    try:
        from bot.utils.keyboards import doctor_menu_keyboard
        await context.bot.send_message(
            chat_id=telegram_id,
            text=(
                f"🎉 Congratulations, Dr. {name}!\n\n"
                f"Your application has been approved. You are now a verified LongiMed doctor.\n\n"
                f"Use the menu below to get started:"
            ),
            reply_markup=doctor_menu_keyboard("en"),
        )
    except Exception:
        pass

    await query.edit_message_text(f"✅ Dr. {name} (#{doctor_id}) approved and notified.")


async def reject_doctor_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    from bot.config import settings
    if update.effective_user.id not in settings.admin_ids:
        return

    doctor_id = int(query.data.split(":")[2])

    from bot.database import session_factory
    from bot.models.doctor import Doctor, RegistrationStatus

    async with session_factory() as session:
        doctor = await session.get(Doctor, doctor_id)
        if not doctor:
            await query.edit_message_text("Doctor not found.")
            return
        doctor.registration_status = RegistrationStatus.REJECTED
        doctor.rejection_reason = "Application not approved"
        telegram_id = doctor.telegram_id
        name = doctor.full_name
        await session.commit()

    try:
        await context.bot.send_message(
            chat_id=telegram_id,
            text=(
                f"We're sorry, Dr. {name}. Your application was not approved at this time.\n\n"
                f"You may reapply by sending /start and selecting 'I'm a Doctor' again."
            ),
        )
    except Exception:
        pass

    await query.edit_message_text(f"❌ Dr. {name} (#{doctor_id}) rejected and notified.")


async def view_doctor_license_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    from bot.config import settings
    if update.effective_user.id not in settings.admin_ids:
        return

    doctor_id = int(query.data.split(":")[2])

    from bot.database import session_factory
    from bot.models.doctor import Doctor

    async with session_factory() as session:
        doctor = await session.get(Doctor, doctor_id)
        if not doctor or not doctor.license_document_file_id:
            await query.edit_message_text("No license document found.")
            return
        file_id = doctor.license_document_file_id
        name = doctor.full_name

    try:
        await context.bot.send_document(
            chat_id=update.effective_user.id,
            document=file_id,
            caption=f"License document for Dr. {name} (#{doctor_id})",
        )
    except Exception:
        try:
            await context.bot.send_photo(
                chat_id=update.effective_user.id,
                photo=file_id,
                caption=f"License document for Dr. {name} (#{doctor_id})",
            )
        except Exception as exc:
            await query.edit_message_text(f"Failed to send document: {exc}")


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
        # Doctor registration
        DOC_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, doc_receive_name)],
        DOC_LICENSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, doc_receive_license)],
        DOC_SPECIALTY: [CallbackQueryHandler(doc_select_specialty, pattern=r"^docspec:")],
        DOC_LANGUAGES: [CallbackQueryHandler(doc_select_languages, pattern=r"^doclang:")],
        DOC_BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, doc_receive_bio)],
        DOC_PHOTO: [MessageHandler(filters.PHOTO | filters.Document.ALL, doc_receive_photo)],
        DOC_CONFIRM: [CallbackQueryHandler(doc_confirm_submit, pattern=r"^docsubmit:")],
    },
    fallbacks=[CommandHandler("start", cmd_start)],
    conversation_timeout=600,
    name="start_conv",
    per_message=False,
)

# Standalone admin callbacks for doctor approval
from telegram.ext import CallbackQueryHandler as CQH
doctor_approve_handler = CQH(approve_doctor_cb, pattern=r"^docmod:approve:\d+$")
doctor_reject_handler = CQH(reject_doctor_cb, pattern=r"^docmod:reject:\d+$")
doctor_license_handler = CQH(view_doctor_license_cb, pattern=r"^docmod:license:\d+$")
