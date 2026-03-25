"""
Public Q&A flow — ask a question, admin approves, post to channel.
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
    main_menu_keyboard,
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
        text=f"💬 *Ask a Public Question*\n\n{t('qa_intro', lang)}\n\nStep 1 of 4 — {t('qa_select_category', lang)}",
        
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
        text=f"Step 2 of 4 — {t('qa_anonymous_prompt', lang)}",
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
        text=f"Step 3 of 4 — {t('qa_enter_question', lang)}",
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
        await update.message.reply_text("Please add a bit more detail (at least 10 characters).")
        return ENTER_QUESTION

    if len(text) > 1000:
        await update.message.reply_text("Please keep your question under 1000 characters.")
        return ENTER_QUESTION

    context.user_data["question_text"] = text

    category = context.user_data.get("question_category", "—")
    anonymous = context.user_data.get("question_anonymous", False)
    anon_label = "🕵️ Anonymous" if anonymous else "👤 Public"

    preview = (
        f"Step 4 of 4 — Preview\n\n"
        f"📂 Category: {category.title()}\n"
        f"👁 Visibility: {anon_label}\n\n"
        f"❓ {text}"
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

    from bot.models.doctor import Specialty

    question_text = context.user_data.get("question_text", "")
    category_str = context.user_data.get("question_category", "general")
    category = Specialty(category_str)  # convert string to enum
    anonymous = context.user_data.get("question_anonymous", False)

    async with session_factory() as session:
        # Resolve the internal user record
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            await query.edit_message_text(t("error_not_registered", lang))
            return ConversationHandler.END

        question = Question(
            user_id=user.id,
            category=category,
            text=question_text,
            is_anonymous=anonymous,
            status=QuestionStatus.PENDING,
        )
        session.add(question)
        await session.flush()
        question_id = question.id

        # Collect moderator telegram_ids from DB
        mod_result = await session.execute(select(Moderator))
        moderators = mod_result.scalars().all()
        mod_telegram_ids = [m.telegram_id for m in moderators]

        await session.commit()

    # Notify admins + moderators
    notify_ids = list(set(settings.admin_ids + mod_telegram_ids))
    notification_text = (
        f"📋 *New Question Pending Review* (#{question_id})\n\n"
        f"Category: {category}\n"
        f"_{question_text[:300]}_"
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

    await query.edit_message_text(t("qa_submitted", lang))

    # Clear conversation scratch data
    for key in ("question_category", "question_anonymous", "question_text"):
        context.user_data.pop(key, None)

    return ConversationHandler.END
# ---------------------------------------------------------------------------
# Step 5b — Edit: go back to enter question
# ---------------------------------------------------------------------------

async def edit_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")
    await query.edit_message_text(f"Step 3 of 4 — {t('qa_enter_question', lang)}")
    return ENTER_QUESTION
# ---------------------------------------------------------------------------
# Step 5c — Cancel
# ---------------------------------------------------------------------------

async def cancel_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User cancelled the question flow."""
    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("lang", "en")
    await query.edit_message_text("Cancelled. Send /start to return to the menu.")

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
        await query.answer("Invalid callback", show_alert=True)
        return

    question_id = int(parts[2])

    async with session_factory() as session:
        question = await session.get(Question, question_id)
        if not question:
            await query.answer("Question not found", show_alert=True)
            return
        if question.status != QuestionStatus.PENDING:
            await query.answer("Already processed", show_alert=True)
            return

        question.status = QuestionStatus.APPROVED
        await session.flush()

        user_result = await session.execute(select(User).where(User.id == question.user_id))
        author = user_result.scalar_one_or_none()
        author_tid = author.telegram_id if author else None

        q_category = question.category
        q_text = question.text
        q_anon = question.is_anonymous

        doctor_result = await session.execute(
            select(Doctor).where(
                Doctor.specialty == q_category,
                Doctor.is_available.is_(True),
                Doctor.is_verified.is_(True),
            )
        )
        doc_tids = [d.telegram_id for d in doctor_result.scalars().all()]
        await session.commit()

    # Post to channel — clean, no Answer button (doctors get it in DM)
    display = "Anonymous" if q_anon else f"User #{question_id}"
    cat_name = q_category.value if hasattr(q_category, 'value') else q_category
    channel_text = (
        f"❓ {cat_name.title()} Question (#{question_id})\n\n"
        f"{q_text}\n\n"
        f"— {display}\n\n"
        f"💬 Reply in the discussion thread below to follow up."
    )

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    bot_me = await context.bot.get_me()

    if settings.public_channel_id:
        try:
            msg = await context.bot.send_message(
                chat_id=settings.public_channel_id,
                text=channel_text,
            )
            # Save channel_message_id for threading replies
            async with session_factory() as session:
                q = await session.get(Question, question_id)
                if q:
                    q.channel_message_id = msg.message_id
                    await session.commit()
        except Exception as exc:
            logger.error("Channel post failed: %s", exc)

    if author_tid:
        try:
            await context.bot.send_message(
                chat_id=author_tid,
                text=t("qa_approved_notify", lang),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        "🔄 Ask a Follow-Up",
                        url=f"https://t.me/{bot_me.username}?start=followup_{question_id}",
                    ),
                ]]),
            )
        except Exception:
            pass

    # Notify doctors — ONLY doctors get the Answer button (DM only)
    for doc_id in doc_tids:
        try:
            await context.bot.send_message(
                chat_id=doc_id,
                text=(
                    f"🔔 New {cat_name.title()} question (#{question_id}):\n\n"
                    f"{q_text[:200]}"
                ),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("💬 Answer This", url=f"https://t.me/{bot_me.username}?start=answer_{question_id}"),
                ]]),
            )
        except Exception:
            pass

    await query.edit_message_text(f"✅ Question #{question_id} approved and posted.")
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
    parts = query.data.split(":")
    if len(parts) < 3 or not parts[2].isdigit():
        await query.answer("Invalid callback", show_alert=True)
        return

    question_id = int(parts[2])

    async with session_factory() as session:
        question = await session.get(Question, question_id)
        if not question:
            await query.answer("Question not found", show_alert=True)
            return
        if question.status != QuestionStatus.PENDING:
            await query.answer("Already processed", show_alert=True)
            return

        question.status = QuestionStatus.REJECTED
        await session.flush()

        user_result = await session.execute(select(User).where(User.id == question.user_id))
        author = user_result.scalar_one_or_none()
        author_tid = author.telegram_id if author else None
        await session.commit()

    if author_tid:
        try:
            await context.bot.send_message(
                chat_id=author_tid, text=t("qa_rejected_notify", lang, reason="Not approved by moderator"),
            )
        except Exception:
            pass

    await query.edit_message_text(f"❌ Question #{question_id} rejected.")
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
            CallbackQueryHandler(edit_question, pattern=r"^edit$"),
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
