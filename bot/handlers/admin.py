"""
Admin command handlers for the LongiMed bot.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes

from bot.utils.decorators import admin_only
from bot.database import session_factory
from bot.models.question import Question, QuestionStatus
from bot.models.user import User
from bot.models.doctor import Doctor, RegistrationStatus
from bot.models.moderator import Moderator
from bot.config import settings
from sqlalchemy import select

logger = logging.getLogger(__name__)

PAGE_SIZE = 10


@admin_only
async def list_pending_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    page = int(args[0]) if args and args[0].isdigit() else 1
    offset = (page - 1) * PAGE_SIZE

    async with session_factory() as session:
        q_result = await session.execute(
            select(Question)
            .where(Question.status == QuestionStatus.PENDING)
            .order_by(Question.created_at.asc())
            .offset(offset).limit(PAGE_SIZE)
        )
        pending_questions = q_result.scalars().all()

        from bot.models.session import Session as ConsultSession, SessionStatus
        s_result = await session.execute(
            select(ConsultSession)
            .where(ConsultSession.status.in_([SessionStatus.AWAITING_DOCTOR, SessionStatus.ACTIVE]))
            .order_by(ConsultSession.created_at.asc())
            .offset(offset).limit(PAGE_SIZE)
        )
        pending_sessions = s_result.scalars().all()

    lines = [f"📋 Pending Items (Page {page})"]

    if pending_questions:
        lines.append("\n--- Questions ---")
        for q in pending_questions:
            cat = q.category.value if hasattr(q.category, 'value') else q.category
            lines.append(f"  #{q.id} [{cat}] {q.text[:80]}...")
    else:
        lines.append("\nNo pending questions.")

    if pending_sessions:
        lines.append("\n--- Sessions ---")
        for s in pending_sessions:
            lines.append(f"  #{s.id} status={s.status.value} user_id={s.user_id}")
    else:
        lines.append("\nNo pending sessions.")

    await update.message.reply_text("\n".join(lines))


@admin_only
async def confirm_payment_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("Usage: /confirm_payment <telegram_id> <amount>")
        return

    if not args[0].isdigit():
        await update.message.reply_text("Invalid user ID.")
        return

    target_tg_id = int(args[0])
    amount_str = args[1]

    async with session_factory() as session:
        from bot.models.payment import Payment, PaymentStatus

        pay_result = await session.execute(
            select(Payment)
            .join(User, Payment.user_id == User.id)
            .where(User.telegram_id == target_tg_id, Payment.status == PaymentStatus.PENDING)
            .order_by(Payment.created_at.desc())
            .limit(1)
        )
        payment = pay_result.scalar_one_or_none()

        if not payment:
            await update.message.reply_text(f"No pending payment found for user {target_tg_id}.")
            return

        payment.status = PaymentStatus.COMPLETED
        payment.confirmed_by_admin_id = update.effective_user.id
        payment.amount_etb = float(amount_str)
        await session.commit()

    try:
        await context.bot.send_message(
            chat_id=target_tg_id,
            text=f"✅ Your payment of {amount_str} ETB has been confirmed. Your session is approved!",
        )
    except Exception as exc:
        logger.warning("Failed to notify user %s: %s", target_tg_id, exc)

    await update.message.reply_text(f"✅ Payment confirmed for user {target_tg_id} — {amount_str} ETB.")


@admin_only
async def add_moderator_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /add_moderator <telegram_id>")
        return

    telegram_id = int(args[0])

    async with session_factory() as session:
        existing = await session.execute(
            select(Moderator).where(Moderator.telegram_id == telegram_id)
        )
        if existing.scalar_one_or_none():
            await update.message.reply_text(f"User {telegram_id} is already a moderator.")
            return

        session.add(Moderator(telegram_id=telegram_id))
        await session.commit()

    await update.message.reply_text(f"✅ Moderator {telegram_id} added.")


@admin_only
async def remove_moderator_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /remove_moderator <telegram_id>")
        return

    telegram_id = int(args[0])

    async with session_factory() as session:
        result = await session.execute(
            select(Moderator).where(Moderator.telegram_id == telegram_id)
        )
        moderator = result.scalar_one_or_none()
        if not moderator:
            await update.message.reply_text(f"Moderator {telegram_id} not found.")
            return

        await session.delete(moderator)
        await session.commit()

    await update.message.reply_text(f"✅ Moderator {telegram_id} removed.")


@admin_only
async def view_doctors_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    async with session_factory() as session:
        result = await session.execute(select(Doctor).order_by(Doctor.created_at.desc()))
        doctors = result.scalars().all()

    if not doctors:
        await update.message.reply_text("No doctors registered yet.")
        return

    lines = ["👨‍⚕️ All Doctors:"]
    for d in doctors:
        spec = d.specialty.value if hasattr(d.specialty, 'value') else d.specialty
        avail = "🟢 Available" if d.is_available else "🔴 Unavailable"
        verified = "✅ Verified" if d.is_verified else "⏳ " + d.registration_status.value
        lines.append(f"  #{d.id} Dr. {d.full_name} — {spec} | {verified} | {avail}")

    text = "\n".join(lines)
    for i in range(0, len(text), 4000):
        await update.message.reply_text(text[i:i + 4000])


@admin_only
async def pending_doctors_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    async with session_factory() as session:
        result = await session.execute(
            select(Doctor).where(Doctor.registration_status == RegistrationStatus.PENDING)
        )
        doctors = result.scalars().all()

    if not doctors:
        await update.message.reply_text("No pending doctor applications.")
        return

    for doc in doctors:
        spec = doc.specialty.value if hasattr(doc.specialty, 'value') else doc.specialty
        text = (
            f"📋 Doctor Application #{doc.id}\n\n"
            f"Name: {doc.full_name}\n"
            f"Specialty: {spec}\n"
            f"Telegram ID: {doc.telegram_id}"
        )
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Approve", callback_data=f"docmod:approve:{doc.id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"docmod:reject:{doc.id}"),
        ]])
        await update.message.reply_text(text, reply_markup=keyboard)


@admin_only
async def approve_doctor_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /approve_doctor <doctor_id>")
        return

    doctor_id = int(args[0])

    async with session_factory() as session:
        doctor = await session.get(Doctor, doctor_id)
        if not doctor:
            await update.message.reply_text(f"Doctor #{doctor_id} not found.")
            return

        doctor.is_verified = True
        doctor.registration_status = RegistrationStatus.APPROVED
        doc_tid = doctor.telegram_id
        await session.commit()

    try:
        await context.bot.send_message(
            chat_id=doc_tid,
            text="🎉 Congratulations! Your doctor application has been approved. You are now a verified LongiMed doctor.",
        )
    except Exception as exc:
        logger.warning("Failed to notify doctor %s: %s", doc_tid, exc)

    await update.message.reply_text(f"✅ Doctor #{doctor_id} approved and verified.")


@admin_only
async def reject_doctor_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("Usage: /reject_doctor <doctor_id> <reason...>")
        return

    if not args[0].isdigit():
        await update.message.reply_text("Invalid doctor ID.")
        return

    doctor_id = int(args[0])
    reason = " ".join(args[1:])

    async with session_factory() as session:
        doctor = await session.get(Doctor, doctor_id)
        if not doctor:
            await update.message.reply_text(f"Doctor #{doctor_id} not found.")
            return

        doctor.is_verified = False
        doctor.registration_status = RegistrationStatus.REJECTED
        doctor.rejection_reason = reason
        doc_tid = doctor.telegram_id
        await session.commit()

    try:
        await context.bot.send_message(
            chat_id=doc_tid,
            text=f"Your doctor application was not approved.\n\nReason: {reason}\n\nYou may reapply after addressing the above.",
        )
    except Exception as exc:
        logger.warning("Failed to notify doctor %s: %s", doc_tid, exc)

    await update.message.reply_text(f"❌ Doctor #{doctor_id} rejected. Reason: {reason}")


from bot.handlers.public_question import (
    question_approve_handler,
    question_reject_handler,
)

admin_handlers = [
    CommandHandler("list_pending", list_pending_cmd),
    CommandHandler("confirm_payment", confirm_payment_cmd),
    CommandHandler("add_moderator", add_moderator_cmd),
    CommandHandler("remove_moderator", remove_moderator_cmd),
    CommandHandler("view_doctors", view_doctors_cmd),
    CommandHandler("pending_doctors", pending_doctors_cmd),
    CommandHandler("approve_doctor", approve_doctor_cmd),
    CommandHandler("reject_doctor", reject_doctor_cmd),
    question_approve_handler,
    question_reject_handler,
]
