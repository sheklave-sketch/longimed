"""
Public Q&A flow for LongiMed Telegram bot.

ConversationHandler states:
    CATEGORY         (10) - user picks a medical category
    ANONYMITY        (11) - user chooses anonymous / named
    ENTER_QUESTION   (12) - user types their question
    CONFIRM_QUESTION (13) - preview + confirm or cancel

Standalone callbacks:
    question_approve_handler  - pattern ^qmod:approve:<question_id>
    question_reject_handler   - pattern ^qmod:reject:<question_id>

Exports:
    public_question_conv_handler
    question_approve_handler
    question_reject_handler
"""

import logging
from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from bot.i18n import t
from bot.utils.keyboards import (
    anonymous_keyboard,
    category_keyboard,
    confirm_cancel_keyboard,
    admin_question_keyboard,
)
from bot.database import session_factory
from bot.models.question import Question, QuestionStatus
from bot.models.user import User
from bot.models.doctor import Doctor
from bot.models.moderator import Moderator
from bot.config import settings
from sqlalchemy import select

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Conversation states
# ---------------------------------------------------------------------------
CATEGORY = 10
ANONYMITY = 11
ENTER_QUESTION = 12
CONFIRM_QUESTION = 13


# ---------------------------------------------------------------------------
# Step 1 — Entry point: show categories
# ---------------------------------------------------------------------------

async def ask_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point triggered by menu:ask callback."""
    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("lang", "en")
    await query.edit_message_text(
        text=t("ask.choose_category", lang),
        reply_markup=category_keyboard(lang),
    )
    return CATEGORY


# ---------------------------------------------------------------------------
# Step 2 — Category selected: ask about anonymity
# ---------------------------------------------------------------------------

async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle category selection, then ask anonymity preference."""
    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("lang", "en")
    # Callback data format: "cat:<category_slug>"
    category = query.data.split(":", 1)[1]
    context.user_data["question_category"] = category

    await query.edit_message_text(
        text=t("ask.choose_anonymity", lang),
        reply_markup=anonymous_keyboard(lang),
    )
    return ANONYMITY


# ---------------------------------------------------------------------------
# Step 3 — Anonymity chosen: ask for question text
# ---------------------------------------------------------------------------

async def anonymity_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle anonymity selection, then prompt for question text."""
    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("lang", "en")
    # Callback data: "anon:yes" or "anon:no"
    context.user_data["question_anonymous"] = query.data == "anon:yes"

    await query.edit_message_text(
        text=t("ask.enter_question", lang),
    )
    return ENTER_QUESTION


# ---------------------------------------------------------------------------
# Step 4 — Receive question text: validate + show preview
# ---------------------------------------------------------------------------

async def receive_question_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validate question length and show a preview for confirmation."""
    lang = context.user_data.get("lang", "en")
    text = (update.message.text or "").strip()

    if len(text) < 10:
        await update.message.reply_text(t("ask.too_short", lang))
        return ENTER_QUESTION

    if len(text) > 1000:
        await update.message.reply_text(t("ask.too_long", lang))
        return ENTER_QUESTION

    context.user_data["question_text"] = text

    category = context.user_data.get("question_category", "—")
    anonymous = context.user_data.get("question_anonymous", False)
    anon_label = t("ask.anonymous_yes", lang) if anonymous else t("ask.anonymous_no", lang)

    preview = t(
        "ask.preview",
        lang,
        category=category,
        anonymous=anon_label,
        text=text,
    )
    await update.message.reply_text(
        text=preview,
        reply_markup=confirm_cancel_keyboard(lang),
    )
    return CONFIRM_QUESTION


# ---------------------------------------------------------------------------
# Step 5a — Confirm: save to DB + notify admins/mods
# ---------------------------------------------------------------------------

async def confirm_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Persist the question and broadcast it to admins and moderators."""
    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("lang", "en")
    telegram_id = update.effective_user.id

    question_text = context.user_data.get("question_text", "")
    category = context.user_data.get("question_category", "")
    anonymous = context.user_data.get("question_anonymous", False)

    async with session_factory() as session:
        # Resolve the internal user record
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            await query.edit_message_text(t("error.user_not_found", lang))
            return ConversationHandler.END

        question = Question(
            user_id=user.id,
            category=category,
            text=question_text,
            is_anonymous=anonymous,
            status=QuestionStatus.PENDING,
        )
        session.add(question)
        await session.flush()  # populate question.id before commit
        question_id = question.id

        # Collect admins from settings
        admin_ids: list[int] = []
        if hasattr(settings, "ADMIN_IDS") and settings.ADMIN_IDS:
            admin_ids = list(settings.ADMIN_IDS)

        # Collect moderator telegram_ids from DB
        mod_result = await session.execute(select(Moderator))
        moderators = mod_result.scalars().all()
        mod_telegram_ids = [m.telegram_id for m in moderators]

        await session.commit()

    notify_ids = list(set(admin_ids + mod_telegram_ids))

    # Notify all admins + moderators
    anon_label = t("ask.anonymous_yes", lang) if anonymous else t("ask.anonymous_no", lang)
    notification_text = t(
        "admin.new_question",
        lang,
        question_id=question_id,
        category=category,
        anonymous=anon_label,
        text=question_text,
    )
    keyboard = admin_question_keyboard(question_id, lang)

    for uid in notify_ids:
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=notification_text,
                reply_markup=keyboard,
            )
        except Exception as exc:
            logger.warning("Failed to notify admin/mod %s: %s", uid, exc)

    await query.edit_message_text(t("ask.submitted", lang))

    # Clear conversation scratch data
    for key in ("question_category", "question_anonymous", "question_text"):
        context.user_data.pop(key, None)

    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Step 5b — Cancel
# ---------------------------------------------------------------------------

async def cancel_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User cancelled the question flow."""
    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("lang", "en")
    await query.edit_message_text(t("ask.cancelled", lang))

    for key in ("question_category", "question_anonymous", "question_text"):
        context.user_data.pop(key, None)

    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Standalone: approve a question
# ---------------------------------------------------------------------------

async def approve_question_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Admin/mod approves a pending question.
    Callback data pattern: qmod:approve:<question_id>

    Actions:
      - Set question.status = APPROVED
      - Post formatted question to PUBLIC_CHANNEL_ID
      - Notify the question author
      - Notify all available + verified doctors in the same specialty/category
    """
    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("lang", "en")
    parts = query.data.split(":")  # ["qmod", "approve", "<id>"]
    if len(parts) < 3 or not parts[2].isdigit():
        await query.answer(t("error.invalid_callback", lang), show_alert=True)
        return

    question_id = int(parts[2])

    async with session_factory() as session:
        result = await session.execute(
            select(Question).where(Question.id == question_id)
        )
        question = result.scalar_one_or_none()

        if question is None:
            await query.answer(t("error.question_not_found", lang), show_alert=True)
            return

        if question.status != QuestionStatus.PENDING:
            await query.answer(t("error.already_moderated", lang), show_alert=True)
            return

        question.status = QuestionStatus.APPROVED
        await session.flush()

        # Fetch author's telegram_id
        user_result = await session.execute(
            select(User).where(User.id == question.user_id)
        )
        author = user_result.scalar_one_or_none()
        author_telegram_id = author.telegram_id if author else None

        # Snapshot fields before session closes
        question_category = question.category
        question_text = question.text
        question_is_anonymous = question.is_anonymous

        # Fetch available + verified doctors in matching specialty
        doctor_result = await session.execute(
            select(Doctor).where(
                Doctor.specialty == question_category,
                Doctor.is_available.is_(True),
                Doctor.is_verified.is_(True),
            )
        )
        available_doctors = doctor_result.scalars().all()
        doctor_telegram_ids = [d.telegram_id for d in available_doctors]

        await session.commit()

    # Post to public channel
    anon_label = (
        t("ask.anonymous_yes", lang)
        if question_is_anonymous
        else t("ask.anonymous_no", lang)
    )
    channel_text = t(
        "channel.question_post",
        lang,
        question_id=question_id,
        category=question_category,
        anonymous=anon_label,
        text=question_text,
    )
    try:
        await context.bot.send_message(
            chat_id=settings.PUBLIC_CHANNEL_ID,
            text=channel_text,
        )
    except Exception as exc:
        logger.error("Failed to post question %s to channel: %s", question_id, exc)

    # Notify author
    if author_telegram_id:
        try:
            await context.bot.send_message(
                chat_id=author_telegram_id,
                text=t("ask.approved_notify", lang, question_id=question_id),
            )
        except Exception as exc:
            logger.warning("Failed to notify author %s: %s", author_telegram_id, exc)

    # Notify available doctors
    doctor_notification = t(
        "doctor.new_question_notify",
        lang,
        question_id=question_id,
        category=question_category,
        text=question_text,
    )
    for doc_id in doctor_telegram_ids:
        try:
            await context.bot.send_message(
                chat_id=doc_id,
                text=doctor_notification,
            )
        except Exception as exc:
            logger.warning("Failed to notify doctor %s: %s", doc_id, exc)

    await query.edit_message_text(
        t("admin.question_approved", lang, question_id=question_id)
    )


# ---------------------------------------------------------------------------
# Standalone: reject a question
# ---------------------------------------------------------------------------

async def reject_question_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Admin/mod rejects a pending question.
    Callback data pattern: qmod:reject:<question_id>

    Actions:
      - Set question.status = REJECTED
      - Notify the question author
    """
    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("lang", "en")
    parts = query.data.split(":")  # ["qmod", "reject", "<id>"]
    if len(parts) < 3 or not parts[2].isdigit():
        await query.answer(t("error.invalid_callback", lang), show_alert=True)
        return

    question_id = int(parts[2])

    async with session_factory() as session:
        result = await session.execute(
            select(Question).where(Question.id == question_id)
        )
        question = result.scalar_one_or_none()

        if question is None:
            await query.answer(t("error.question_not_found", lang), show_alert=True)
            return

        if question.status != QuestionStatus.PENDING:
            await query.answer(t("error.already_moderated", lang), show_alert=True)
            return

        question.status = QuestionStatus.REJECTED
        await session.flush()

        user_result = await session.execute(
            select(User).where(User.id == question.user_id)
        )
        author = user_result.scalar_one_or_none()
        author_telegram_id = author.telegram_id if author else None

        await session.commit()

    # Notify author
    if author_telegram_id:
        try:
            await context.bot.send_message(
                chat_id=author_telegram_id,
                text=t("ask.rejected_notify", lang, question_id=question_id),
            )
        except Exception as exc:
            logger.warning(
                "Failed to notify author %s of rejection: %s", author_telegram_id, exc
            )

    await query.edit_message_text(
        t("admin.question_rejected", lang, question_id=question_id)
    )


# ---------------------------------------------------------------------------
# Handler assembly
# ---------------------------------------------------------------------------

public_question_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(ask_entry, pattern=r"^menu:ask$")],
    states={
        CATEGORY: [
            CallbackQueryHandler(category_selected, pattern=r"^cat:"),
        ],
        ANONYMITY: [
            CallbackQueryHandler(anonymity_selected, pattern=r"^anon:(yes|no)$"),
        ],
        ENTER_QUESTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_question_text),
        ],
        CONFIRM_QUESTION: [
            CallbackQueryHandler(confirm_question, pattern=r"^confirm$"),
            CallbackQueryHandler(cancel_question, pattern=r"^cancel$"),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(cancel_question, pattern=r"^cancel$"),
    ],
    allow_reentry=True,
    name="public_question_conv",
)

question_approve_handler = CallbackQueryHandler(
    approve_question_cb, pattern=r"^qmod:approve:\d+$"
)

question_reject_handler = CallbackQueryHandler(
    reject_question_cb, pattern=r"^qmod:reject:\d+$"
)
