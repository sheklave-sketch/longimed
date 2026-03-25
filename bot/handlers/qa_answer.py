"""
Q&A Answer + Follow-Up flows.

Doctor answers a question → posted as reply in channel → notifies patient.
Any user follows up → goes to moderation → posted as reply in channel.
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
from bot.database import session_factory
from bot.config import settings

logger = logging.getLogger(__name__)

# States
AWAITING_ANSWER = 30
AWAITING_FOLLOWUP = 31
FOLLOWUP_ANON = 32
FOLLOWUP_TEXT = 33


# ── Doctor Answer Flow ────────────────────────────────────────────────────

async def start_answer_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry: /start answer_<question_id> deep link."""
    args = context.args
    if not args or not args[0].startswith("answer_"):
        return ConversationHandler.END

    try:
        question_id = int(args[0].split("_")[1])
    except (IndexError, ValueError):
        await update.message.reply_text("Invalid question link.")
        return ConversationHandler.END

    # Verify user is a verified doctor
    from bot.models.doctor import Doctor
    from bot.models.question import Question, QuestionStatus
    from sqlalchemy import select

    async with session_factory() as session:
        doc_result = await session.execute(
            select(Doctor).where(
                Doctor.telegram_id == update.effective_user.id,
                Doctor.is_verified.is_(True),
            )
        )
        doctor = doc_result.scalar_one_or_none()
        if not doctor:
            await update.message.reply_text(
                "Only verified doctors can answer questions.\n"
                "If you'd like to follow up, use the Follow Up button instead."
            )
            return ConversationHandler.END

        q = await session.get(Question, question_id)
        if not q:
            await update.message.reply_text("Question not found.")
            return ConversationHandler.END

        if q.status == QuestionStatus.ANSWERED:
            await update.message.reply_text(
                "This question has already been answered. "
                "You can still add a follow-up via the channel."
            )
            return ConversationHandler.END

    context.user_data["answering_question_id"] = question_id
    context.user_data["answering_doctor_id"] = doctor.id
    context.user_data["answering_doctor_name"] = doctor.full_name

    cat = q.category.value if hasattr(q.category, 'value') else q.category
    await update.message.reply_text(
        f"💬 Answering Question #{question_id} ({cat.title()})\n\n"
        f"❓ {q.text}\n\n"
        f"Please type your answer, Dr. {doctor.full_name}:"
    )
    return AWAITING_ANSWER


async def receive_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Doctor types their answer."""
    answer_text = update.message.text.strip()
    lang = context.user_data.get("lang", "en")

    if len(answer_text) < 10:
        await update.message.reply_text("Please provide a more detailed answer (at least 10 characters).")
        return AWAITING_ANSWER

    question_id = context.user_data.get("answering_question_id")
    doctor_id = context.user_data.get("answering_doctor_id")
    doctor_name = context.user_data.get("answering_doctor_name", "Doctor")

    from bot.models.question import Question, QuestionStatus
    from bot.models.user import User

    async with session_factory() as session:
        q = await session.get(Question, question_id)
        if not q:
            await update.message.reply_text("Question not found.")
            return ConversationHandler.END

        q.answer_text = answer_text
        q.answered_by_doctor_id = doctor_id
        q.answered_at = datetime.now(timezone.utc)
        q.status = QuestionStatus.ANSWERED
        channel_msg_id = q.channel_message_id
        q_text = q.text

        # Get patient info
        user = await session.get(User, q.user_id)
        patient_tid = user.telegram_id if user else None

        await session.commit()

    # Post answer to discussion group thread (linked to channel post)
    bot_me = await context.bot.get_me()
    answer_text_formatted = (
        f"✅ Answer from Dr. {doctor_name}\n\n"
        f"{answer_text}"
    )

    # Try discussion group first (threaded), fall back to channel reply
    posted = False
    if settings.discussion_group_id and channel_msg_id:
        try:
            await context.bot.send_message(
                chat_id=settings.discussion_group_id,
                text=answer_text_formatted,
                reply_to_message_id=channel_msg_id,
            )
            posted = True
        except Exception as exc:
            logger.warning("Discussion group post failed (will try channel): %s", exc)

    if not posted and settings.public_channel_id:
        try:
            await context.bot.send_message(
                chat_id=settings.public_channel_id,
                text=answer_text_formatted,
                reply_to_message_id=channel_msg_id if channel_msg_id else None,
            )
        except Exception as exc:
            logger.error("Channel answer post failed: %s", exc)

    # Notify patient
    if patient_tid:
        try:
            await context.bot.send_message(
                chat_id=patient_tid,
                text=(
                    f"🩺 Your question has been answered!\n\n"
                    f"❓ {q_text[:100]}...\n\n"
                    f"💬 Dr. {doctor_name}:\n{answer_text[:300]}"
                ),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        "🔄 Ask a Follow-Up",
                        url=f"https://t.me/{bot_me.username}?start=followup_{question_id}",
                    ),
                ]]),
            )
        except Exception:
            pass

    back_btn = InlineKeyboardMarkup([[
        InlineKeyboardButton("← Back to Menu", callback_data="backtomenu")
    ]])
    await update.message.reply_text(
        f"✅ Your answer has been posted to the channel. Thank you, Dr. {doctor_name}!",
        reply_markup=back_btn,
    )

    # Cleanup
    for k in ("answering_question_id", "answering_doctor_id", "answering_doctor_name"):
        context.user_data.pop(k, None)

    return ConversationHandler.END


# ── Follow-Up Flow (any user) ─────────────────────────────────────────────

async def start_followup_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry: /start followup_<question_id> deep link."""
    args = context.args
    if not args or not args[0].startswith("followup_"):
        return ConversationHandler.END

    try:
        question_id = int(args[0].split("_")[1])
    except (IndexError, ValueError):
        await update.message.reply_text("Invalid follow-up link.")
        return ConversationHandler.END

    from bot.models.question import Question
    from bot.models.user import User
    from sqlalchemy import select

    async with session_factory() as session:
        q = await session.get(Question, question_id)
        if not q:
            await update.message.reply_text("Question not found.")
            return ConversationHandler.END

        # Ensure user is registered
        result = await session.execute(
            select(User).where(User.telegram_id == update.effective_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await update.message.reply_text("Please register first with /start")
            return ConversationHandler.END

    context.user_data["followup_question_id"] = question_id
    context.user_data["followup_user_id"] = user.id

    cat = q.category.value if hasattr(q.category, 'value') else q.category

    text = f"🔄 Follow-up on Question #{question_id} ({cat.title()})\n\n"
    text += f"❓ Original: {q.text[:200]}\n"
    if q.answer_text:
        text += f"💬 Answer: {q.answer_text[:200]}\n"
    text += "\nWould you like to ask anonymously?"

    from bot.utils.keyboards import anonymous_keyboard
    await update.message.reply_text(text, reply_markup=anonymous_keyboard("en"))
    return FOLLOWUP_ANON


async def followup_anon_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "back":
        await query.edit_message_text("Follow-up cancelled.")
        return ConversationHandler.END

    context.user_data["followup_anonymous"] = query.data == "anon:yes"
    await query.edit_message_text("Type your follow-up question:")
    return FOLLOWUP_TEXT


async def receive_followup_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()

    if len(text) < 10:
        await update.message.reply_text("Please add more detail (at least 10 characters).")
        return FOLLOWUP_TEXT

    question_id = context.user_data.get("followup_question_id")
    user_id = context.user_data.get("followup_user_id")
    is_anon = context.user_data.get("followup_anonymous", False)

    from bot.models.follow_up import FollowUp, FollowUpStatus

    async with session_factory() as session:
        fu = FollowUp(
            question_id=question_id,
            user_id=user_id,
            text=text,
            is_anonymous=is_anon,
            status=FollowUpStatus.PENDING,
        )
        session.add(fu)
        await session.flush()
        fu_id = fu.id
        await session.commit()

    # Notify admins/moderators
    from bot.models.moderator import Moderator
    from sqlalchemy import select
    from bot.utils.keyboards import admin_question_keyboard

    review_text = (
        f"📋 New Follow-Up Pending Review\n\n"
        f"On Question #{question_id} — Follow-up #{fu_id}\n\n"
        f"{text[:300]}"
    )
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"fumod:approve:{fu_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"fumod:reject:{fu_id}"),
        ]
    ])

    for admin_id in settings.admin_ids:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=review_text,
                reply_markup=keyboard,
            )
        except Exception:
            pass

    async with session_factory() as session:
        result = await session.execute(select(Moderator))
        for mod in result.scalars():
            try:
                await context.bot.send_message(
                    chat_id=mod.telegram_id,
                    text=review_text,
                    reply_markup=keyboard,
                )
            except Exception:
                pass

    back_btn = InlineKeyboardMarkup([[
        InlineKeyboardButton("← Back to Menu", callback_data="backtomenu")
    ]])
    await update.message.reply_text(
        "✅ Your follow-up has been submitted for review!",
        reply_markup=back_btn,
    )

    for k in ("followup_question_id", "followup_user_id", "followup_anonymous"):
        context.user_data.pop(k, None)

    return ConversationHandler.END


# ── Follow-Up Approve/Reject (admin) ──────────────────────────────────────

async def approve_followup_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    fu_id = int(query.data.split(":")[2])

    from bot.models.follow_up import FollowUp, FollowUpStatus
    from bot.models.question import Question
    from bot.models.user import User

    async with session_factory() as session:
        fu = await session.get(FollowUp, fu_id)
        if not fu or fu.status != FollowUpStatus.PENDING:
            await query.edit_message_text("Already processed.")
            return

        fu.status = FollowUpStatus.APPROVED
        q = await session.get(Question, fu.question_id)
        channel_msg_id = q.channel_message_id if q else None
        q_id = fu.question_id

        user = await session.get(User, fu.user_id)
        display = "Anonymous" if fu.is_anonymous else f"Follow-up by User"
        fu_text = fu.text
        await session.commit()

    # Post follow-up to discussion group thread, fall back to channel
    bot_me = await context.bot.get_me()
    fu_post_text = f"🔄 Follow-Up on Question #{q_id}\n\n{fu_text}\n\n— {display}"

    posted = False
    if settings.discussion_group_id and channel_msg_id:
        try:
            await context.bot.send_message(
                chat_id=settings.discussion_group_id,
                text=fu_post_text,
                reply_to_message_id=channel_msg_id,
            )
            posted = True
        except Exception as exc:
            logger.warning("Discussion group follow-up failed: %s", exc)

    if not posted and settings.public_channel_id:
        try:
            await context.bot.send_message(
                chat_id=settings.public_channel_id,
                text=fu_post_text,
                reply_to_message_id=channel_msg_id,
            )
        except Exception as exc:
            logger.error("Channel follow-up post failed: %s", exc)

    # Notify doctors about the follow-up (Answer button in DM only)
    from bot.models.doctor import Doctor
    from sqlalchemy import select as sa_select
    async with session_factory() as session:
        if q:
            doc_result = await session.execute(
                sa_select(Doctor).where(
                    Doctor.is_verified.is_(True),
                    Doctor.is_available.is_(True),
                )
            )
            for doc in doc_result.scalars():
                try:
                    await context.bot.send_message(
                        chat_id=doc.telegram_id,
                        text=f"🔄 Follow-up on Question #{q_id}:\n\n{fu_text[:200]}",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("💬 Answer This", url=f"https://t.me/{bot_me.username}?start=answer_{q_id}"),
                        ]]),
                    )
                except Exception:
                    pass

    # Notify author
    if user:
        try:
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text="Your follow-up has been approved and posted!",
            )
        except Exception:
            pass

    await query.edit_message_text(f"✅ Follow-up #{fu_id} approved and posted.")


async def reject_followup_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    fu_id = int(query.data.split(":")[2])

    from bot.models.follow_up import FollowUp, FollowUpStatus
    from bot.models.user import User

    async with session_factory() as session:
        fu = await session.get(FollowUp, fu_id)
        if not fu or fu.status != FollowUpStatus.PENDING:
            await query.edit_message_text("Already processed.")
            return

        fu.status = FollowUpStatus.REJECTED
        user = await session.get(User, fu.user_id)
        await session.commit()

    if user:
        try:
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text="Your follow-up was not approved.",
            )
        except Exception:
            pass

    await query.edit_message_text(f"❌ Follow-up #{fu_id} rejected.")


# ── Cancel handler ────────────────────────────────────────────────────────

async def cancel_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Cancelled.")
    elif update.message:
        await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


# ── Handler Assembly ──────────────────────────────────────────────────────

answer_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", start_answer_flow),
    ],
    states={
        AWAITING_ANSWER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_answer),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_flow)],
    conversation_timeout=600,
    name="answer_conv",
    per_message=False,
)

followup_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", start_followup_flow),
    ],
    states={
        FOLLOWUP_ANON: [
            CallbackQueryHandler(followup_anon_selected, pattern=r"^(anon:|back)"),
        ],
        FOLLOWUP_TEXT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_followup_text),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_flow)],
    conversation_timeout=600,
    name="followup_conv",
    per_message=False,
)

followup_approve_handler = CallbackQueryHandler(approve_followup_cb, pattern=r"^fumod:approve:\d+$")
followup_reject_handler = CallbackQueryHandler(reject_followup_cb, pattern=r"^fumod:reject:\d+$")
