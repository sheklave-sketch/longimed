"""
Q&A Answer + Follow-Up flows.

Doctor answers a question → posted as reply in channel → notifies patient.
Follow-ups display the full sequential thread and use inline callbacks (not deep links).
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
FOLLOWUP_TEXT = 33
ANSWERING_FOLLOWUP_TEXT = 34


# ── Thread display helper ────────────────────────────────────────────────

async def _build_thread_text(question_id: int) -> str:
    """Build the full sequential Q&A thread for display."""
    from bot.models.question import Question
    from bot.models.follow_up import FollowUp, FollowUpStatus
    from bot.models.doctor import Doctor
    from sqlalchemy import select

    async with session_factory() as session:
        q = await session.get(Question, question_id)
        if not q:
            return "Question not found."

        cat = q.category.value if hasattr(q.category, 'value') else q.category

        lines = [f"📋 Q&A Thread #{question_id} ({cat.title()})\n"]
        lines.append(f"❓ {q.text}\n")

        if q.answer_text:
            doc_name = "Doctor"
            if q.answered_by_doctor_id:
                doc = await session.get(Doctor, q.answered_by_doctor_id)
                if doc:
                    doc_name = f"Dr. {doc.full_name}"
            lines.append(f"💬 {doc_name}:\n{q.answer_text}\n")

        # Get all approved follow-ups in order
        fu_result = await session.execute(
            select(FollowUp).where(
                FollowUp.question_id == question_id,
                FollowUp.status == FollowUpStatus.APPROVED,
            ).order_by(FollowUp.created_at.asc())
        )
        follow_ups = fu_result.scalars().all()

        for i, fu in enumerate(follow_ups, 1):
            display = "Anonymous" if fu.is_anonymous else "Patient"
            lines.append(f"🔄 Follow-up #{i} ({display}):\n{fu.text}\n")
            if fu.answer_text:
                doc_name = "Doctor"
                if fu.answered_by_doctor_id:
                    doc = await session.get(Doctor, fu.answered_by_doctor_id)
                    if doc:
                        doc_name = f"Dr. {doc.full_name}"
                lines.append(f"💬 {doc_name}:\n{fu.answer_text}\n")
            else:
                lines.append("⏳ Awaiting doctor's response\n")

        # Check for pending follow-ups
        pending_result = await session.execute(
            select(FollowUp).where(
                FollowUp.question_id == question_id,
                FollowUp.status == FollowUpStatus.PENDING,
            )
        )
        pending = pending_result.scalars().all()
        if pending:
            lines.append(f"📝 {len(pending)} follow-up(s) pending review")

    return "\n".join(lines)


def _thread_keyboard(question_id: int, show_followup: bool = True, show_answer_followups: bool = False) -> InlineKeyboardMarkup:
    """Build keyboard for thread display."""
    buttons = []
    if show_followup:
        buttons.append([InlineKeyboardButton(
            "🔄 Ask a Follow-Up", callback_data=f"askfollowup:{question_id}"
        )])
    if show_answer_followups:
        buttons.append([InlineKeyboardButton(
            "💬 Answer Unanswered Follow-Ups", callback_data=f"answerfollowups:{question_id}"
        )])
    buttons.append([InlineKeyboardButton("← Back to Menu", callback_data="backtomenu")])
    return InlineKeyboardMarkup(buttons)


# ── View thread callback (patient or anyone) ────────────────────────────

async def view_thread_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show full Q&A thread when user clicks 'View Thread'."""
    query = update.callback_query
    await query.answer()

    question_id = int(query.data.split(":")[1])
    thread_text = await _build_thread_text(question_id)

    # Check if user is a doctor — show answer buttons if so
    from bot.models.doctor import Doctor
    from sqlalchemy import select
    is_doctor = False
    async with session_factory() as session:
        doc_result = await session.execute(
            select(Doctor).where(
                Doctor.telegram_id == update.effective_user.id,
                Doctor.is_verified.is_(True),
            )
        )
        is_doctor = doc_result.scalar_one_or_none() is not None

    keyboard = _thread_keyboard(
        question_id,
        show_followup=True,
        show_answer_followups=is_doctor,
    )

    try:
        await query.edit_message_text(thread_text, reply_markup=keyboard)
    except Exception:
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=thread_text,
            reply_markup=keyboard,
        )


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
            # Show thread instead — question already answered, but doctor can answer follow-ups
            thread_text = await _build_thread_text(question_id)
            keyboard = _thread_keyboard(question_id, show_followup=False, show_answer_followups=True)
            await update.message.reply_text(
                f"{thread_text}\n\nThis question is already answered. You can answer follow-ups above.",
                reply_markup=keyboard,
            )
            return ConversationHandler.END

    context.user_data["answering_question_id"] = question_id
    context.user_data["answering_doctor_id"] = doctor.id
    context.user_data["answering_doctor_name"] = doctor.full_name

    # Show the thread so doctor sees full context
    thread_text = await _build_thread_text(question_id)
    await update.message.reply_text(
        f"{thread_text}\n\n"
        f"Please type your answer, Dr. {doctor.full_name}:"
    )
    return AWAITING_ANSWER


async def receive_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Doctor types their answer."""
    answer_text = update.message.text.strip()

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

        user = await session.get(User, q.user_id)
        patient_tid = user.telegram_id if user else None

        await session.commit()

    # Post answer to discussion group thread
    answer_text_formatted = (
        f"✅ Answer from Dr. {doctor_name}\n\n"
        f"{answer_text}"
    )

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
            logger.warning("Discussion group post failed: %s", exc)

    if not posted and settings.public_channel_id:
        try:
            await context.bot.send_message(
                chat_id=settings.public_channel_id,
                text=answer_text_formatted,
                reply_to_message_id=channel_msg_id if channel_msg_id else None,
            )
        except Exception as exc:
            logger.error("Channel answer post failed: %s", exc)

    # Notify patient with full thread + follow-up button
    if patient_tid:
        try:
            thread_text = await _build_thread_text(question_id)
            keyboard = _thread_keyboard(question_id, show_followup=True)
            await context.bot.send_message(
                chat_id=patient_tid,
                text=f"🩺 Your question has been answered!\n\n{thread_text}",
                reply_markup=keyboard,
            )
        except Exception:
            pass

    # Show doctor the updated thread
    thread_text = await _build_thread_text(question_id)
    keyboard = _thread_keyboard(question_id, show_followup=False, show_answer_followups=True)
    await update.message.reply_text(
        f"✅ Your answer has been posted. Thank you, Dr. {doctor_name}!\n\n{thread_text}",
        reply_markup=keyboard,
    )

    for k in ("answering_question_id", "answering_doctor_id", "answering_doctor_name"):
        context.user_data.pop(k, None)

    return ConversationHandler.END


# ── Follow-Up Flow (inline callback, not deep link) ─────────────────────

async def start_followup_inline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry: user clicks 'Ask a Follow-Up' callback button."""
    query = update.callback_query
    await query.answer()

    question_id = int(query.data.split(":")[1])

    from bot.models.question import Question
    from bot.models.user import User
    from sqlalchemy import select

    async with session_factory() as session:
        q = await session.get(Question, question_id)
        if not q:
            await query.edit_message_text("Question not found.")
            return ConversationHandler.END

        result = await session.execute(
            select(User).where(User.telegram_id == update.effective_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await query.edit_message_text("Please register first with /start")
            return ConversationHandler.END

    context.user_data["followup_question_id"] = question_id
    context.user_data["followup_user_id"] = user.id
    # Inherit anonymity from original question
    context.user_data["followup_anonymous"] = q.is_anonymous

    # Show full thread + prompt for follow-up
    thread_text = await _build_thread_text(question_id)
    cancel_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✖ Cancel", callback_data="followup_cancel")]
    ])
    await query.edit_message_text(
        f"{thread_text}\n\n✏️ Type your follow-up question below:",
        reply_markup=cancel_kb,
    )
    return FOLLOWUP_TEXT


async def start_followup_deeplink(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Fallback entry: /start followup_<question_id> deep link (backward compat)."""
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

        result = await session.execute(
            select(User).where(User.telegram_id == update.effective_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await update.message.reply_text("Please register first with /start")
            return ConversationHandler.END

    context.user_data["followup_question_id"] = question_id
    context.user_data["followup_user_id"] = user.id
    context.user_data["followup_anonymous"] = q.is_anonymous

    thread_text = await _build_thread_text(question_id)
    cancel_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✖ Cancel", callback_data="followup_cancel")]
    ])
    await update.message.reply_text(
        f"{thread_text}\n\n✏️ Type your follow-up question below:",
        reply_markup=cancel_kb,
    )
    return FOLLOWUP_TEXT


async def receive_followup_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Patient types their follow-up."""
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
                chat_id=admin_id, text=review_text, reply_markup=keyboard,
            )
        except Exception:
            pass

    async with session_factory() as session:
        result = await session.execute(select(Moderator))
        for mod in result.scalars():
            try:
                await context.bot.send_message(
                    chat_id=mod.telegram_id, text=review_text, reply_markup=keyboard,
                )
            except Exception:
                pass

    # Show updated thread with option to add more
    thread_text = await _build_thread_text(question_id)
    result_keyboard = _thread_keyboard(question_id, show_followup=True)
    await update.message.reply_text(
        f"✅ Follow-up submitted for review!\n\n{thread_text}",
        reply_markup=result_keyboard,
    )

    for k in ("followup_question_id", "followup_user_id", "followup_anonymous"):
        context.user_data.pop(k, None)

    return ConversationHandler.END


async def cancel_followup_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel follow-up from inline button."""
    query = update.callback_query
    await query.answer()

    question_id = context.user_data.get("followup_question_id")
    for k in ("followup_question_id", "followup_user_id", "followup_anonymous"):
        context.user_data.pop(k, None)

    if question_id:
        thread_text = await _build_thread_text(question_id)
        keyboard = _thread_keyboard(question_id)
        await query.edit_message_text(thread_text, reply_markup=keyboard)
    else:
        await query.edit_message_text("Follow-up cancelled.")

    return ConversationHandler.END


# ── Doctor answers follow-ups ────────────────────────────────────────────

async def start_answer_followups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Doctor clicks 'Answer Unanswered Follow-Ups' — find first unanswered."""
    query = update.callback_query
    await query.answer()

    question_id = int(query.data.split(":")[1])

    from bot.models.doctor import Doctor
    from bot.models.follow_up import FollowUp, FollowUpStatus
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
            await query.edit_message_text("Only verified doctors can answer follow-ups.")
            return ConversationHandler.END

        # Find first unanswered approved follow-up
        fu_result = await session.execute(
            select(FollowUp).where(
                FollowUp.question_id == question_id,
                FollowUp.status == FollowUpStatus.APPROVED,
                FollowUp.answer_text.is_(None),
            ).order_by(FollowUp.created_at.asc()).limit(1)
        )
        fu = fu_result.scalar_one_or_none()

        if not fu:
            thread_text = await _build_thread_text(question_id)
            await query.edit_message_text(
                f"{thread_text}\n\n✅ All follow-ups have been answered!",
                reply_markup=_thread_keyboard(question_id, show_followup=False, show_answer_followups=False),
            )
            return ConversationHandler.END

    context.user_data["answering_fu_id"] = fu.id
    context.user_data["answering_fu_question_id"] = question_id
    context.user_data["answering_fu_doctor_id"] = doctor.id
    context.user_data["answering_fu_doctor_name"] = doctor.full_name

    thread_text = await _build_thread_text(question_id)
    cancel_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✖ Cancel", callback_data="fu_answer_cancel")]
    ])
    await query.edit_message_text(
        f"{thread_text}\n\n"
        f"💬 Answering follow-up #{fu.id}:\n\"{fu.text[:200]}\"\n\n"
        f"Type your answer, Dr. {doctor.full_name}:",
        reply_markup=cancel_kb,
    )
    return ANSWERING_FOLLOWUP_TEXT


async def receive_followup_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Doctor types their answer to a follow-up."""
    answer_text = update.message.text.strip()

    if len(answer_text) < 10:
        await update.message.reply_text("Please provide a more detailed answer (at least 10 characters).")
        return ANSWERING_FOLLOWUP_TEXT

    fu_id = context.user_data.get("answering_fu_id")
    question_id = context.user_data.get("answering_fu_question_id")
    doctor_id = context.user_data.get("answering_fu_doctor_id")
    doctor_name = context.user_data.get("answering_fu_doctor_name", "Doctor")

    from bot.models.follow_up import FollowUp
    from bot.models.question import Question
    from bot.models.user import User

    async with session_factory() as session:
        fu = await session.get(FollowUp, fu_id)
        if not fu:
            await update.message.reply_text("Follow-up not found.")
            return ConversationHandler.END

        fu.answer_text = answer_text
        fu.answered_by_doctor_id = doctor_id
        fu.answered_at = datetime.now(timezone.utc)

        # Get question for channel posting
        q = await session.get(Question, question_id)
        channel_msg_id = q.channel_message_id if q else None

        # Get follow-up author for notification
        fu_user = await session.get(User, fu.user_id)
        fu_user_tid = fu_user.telegram_id if fu_user else None

        await session.commit()

    # Post to channel/discussion
    reply_formatted = f"💬 Dr. {doctor_name} replied to a follow-up:\n\n{answer_text}"
    posted = False
    if settings.discussion_group_id and channel_msg_id:
        try:
            await context.bot.send_message(
                chat_id=settings.discussion_group_id,
                text=reply_formatted,
                reply_to_message_id=channel_msg_id,
            )
            posted = True
        except Exception as exc:
            logger.warning("Discussion group follow-up answer failed: %s", exc)

    if not posted and settings.public_channel_id:
        try:
            await context.bot.send_message(
                chat_id=settings.public_channel_id,
                text=reply_formatted,
                reply_to_message_id=channel_msg_id,
            )
        except Exception as exc:
            logger.error("Channel follow-up answer failed: %s", exc)

    # Notify follow-up author with full thread
    if fu_user_tid:
        try:
            thread_text = await _build_thread_text(question_id)
            keyboard = _thread_keyboard(question_id, show_followup=True)
            await context.bot.send_message(
                chat_id=fu_user_tid,
                text=f"🩺 Dr. {doctor_name} replied to your follow-up!\n\n{thread_text}",
                reply_markup=keyboard,
            )
        except Exception:
            pass

    # Show doctor the updated thread + option to answer more
    thread_text = await _build_thread_text(question_id)
    keyboard = _thread_keyboard(question_id, show_followup=False, show_answer_followups=True)
    await update.message.reply_text(
        f"✅ Follow-up answered!\n\n{thread_text}",
        reply_markup=keyboard,
    )

    for k in ("answering_fu_id", "answering_fu_question_id", "answering_fu_doctor_id", "answering_fu_doctor_name"):
        context.user_data.pop(k, None)

    return ConversationHandler.END


async def cancel_fu_answer_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel answering a follow-up."""
    query = update.callback_query
    await query.answer()

    question_id = context.user_data.get("answering_fu_question_id")
    for k in ("answering_fu_id", "answering_fu_question_id", "answering_fu_doctor_id", "answering_fu_doctor_name"):
        context.user_data.pop(k, None)

    if question_id:
        thread_text = await _build_thread_text(question_id)
        keyboard = _thread_keyboard(question_id, show_followup=False, show_answer_followups=True)
        await query.edit_message_text(thread_text, reply_markup=keyboard)
    else:
        await query.edit_message_text("Cancelled.")

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
        display = "Anonymous" if fu.is_anonymous else "Follow-up by User"
        fu_text = fu.text
        await session.commit()

    # Post follow-up to channel
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

    # Notify available doctors with full thread + answer button
    from bot.models.doctor import Doctor
    from sqlalchemy import select as sa_select
    async with session_factory() as session:
        doc_result = await session.execute(
            sa_select(Doctor).where(
                Doctor.is_verified.is_(True),
                Doctor.is_available.is_(True),
            )
        )
        for doc in doc_result.scalars():
            try:
                thread_text = await _build_thread_text(q_id)
                keyboard = _thread_keyboard(q_id, show_followup=False, show_answer_followups=True)
                await context.bot.send_message(
                    chat_id=doc.telegram_id,
                    text=f"🔄 New follow-up on Question #{q_id} needs an answer:\n\n{thread_text}",
                    reply_markup=keyboard,
                )
            except Exception:
                pass

    # Notify author with full thread
    if user:
        try:
            thread_text = await _build_thread_text(q_id)
            keyboard = _thread_keyboard(q_id, show_followup=True)
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text=f"✅ Your follow-up has been approved!\n\n{thread_text}",
                reply_markup=keyboard,
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
        CallbackQueryHandler(start_followup_inline, pattern=r"^askfollowup:\d+$"),
        CommandHandler("start", start_followup_deeplink),
    ],
    states={
        FOLLOWUP_TEXT: [
            CallbackQueryHandler(cancel_followup_cb, pattern=r"^followup_cancel$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_followup_text),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(cancel_followup_cb, pattern=r"^followup_cancel$"),
        CommandHandler("cancel", cancel_flow),
    ],
    conversation_timeout=600,
    name="followup_conv",
    per_message=False,
)

answer_followup_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_answer_followups, pattern=r"^answerfollowups:\d+$"),
    ],
    states={
        ANSWERING_FOLLOWUP_TEXT: [
            CallbackQueryHandler(cancel_fu_answer_cb, pattern=r"^fu_answer_cancel$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_followup_answer),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(cancel_fu_answer_cb, pattern=r"^fu_answer_cancel$"),
        CommandHandler("cancel", cancel_flow),
    ],
    conversation_timeout=600,
    name="answer_followup_conv",
    per_message=False,
)

# Standalone callbacks
view_thread_handler = CallbackQueryHandler(view_thread_cb, pattern=r"^viewthread:\d+$")
followup_approve_handler = CallbackQueryHandler(approve_followup_cb, pattern=r"^fumod:approve:\d+$")
followup_reject_handler = CallbackQueryHandler(reject_followup_cb, pattern=r"^fumod:reject:\d+$")
