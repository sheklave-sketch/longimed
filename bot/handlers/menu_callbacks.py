"""
Standalone callback handlers for menu buttons and admin actions.
These run at group 0 to ensure they fire before ConversationHandlers.
All logic is self-contained — never calls command handlers (they expect update.message).
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.i18n import t
from bot.database import session_factory

logger = logging.getLogger(__name__)


async def _get_doctor(telegram_id: int):
    from bot.models.doctor import Doctor
    from sqlalchemy import select
    async with session_factory() as session:
        result = await session.execute(
            select(Doctor).where(Doctor.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


# ── Doctor menu buttons ───────────────────────────────────────────────────

async def handle_doc_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    action = query.data.split(":")[1]
    lang = context.user_data.get("lang", "en")

    try:
        if action == "queue":
            await _doc_queue(query, update.effective_user.id)
        elif action == "waitlist":
            await _doc_waitlist(query, update.effective_user.id)
        elif action == "available":
            await _doc_set_availability(query, update.effective_user.id, True)
        elif action == "unavailable":
            await _doc_set_availability(query, update.effective_user.id, False)
        elif action == "schedule":
            await _doc_schedule(query, update.effective_user.id)
        elif action == "reviews":
            await _doc_reviews(query, update.effective_user.id)
        elif action == "profile":
            await _doc_profile(query, update.effective_user.id)
    except Exception as exc:
        logger.error("Doc menu error (%s): %s", action, exc, exc_info=True)
        await query.edit_message_text(f"Error: {exc}")


async def _doc_set_availability(query, telegram_id: int, available: bool) -> None:
    from bot.models.doctor import Doctor
    from sqlalchemy import select
    async with session_factory() as session:
        result = await session.execute(
            select(Doctor).where(Doctor.telegram_id == telegram_id)
        )
        doctor = result.scalar_one_or_none()
        if not doctor:
            await query.edit_message_text("Doctor record not found.")
            return
        doctor.is_available = available
        await session.commit()
    if available:
        await query.edit_message_text("✅ You are now available for consultations.")
    else:
        await query.edit_message_text("🔴 You are now unavailable.")


async def _doc_queue(query, telegram_id: int) -> None:
    from bot.models.doctor import Doctor
    from bot.models.session import Session as CS, SessionStatus
    from sqlalchemy import select
    async with session_factory() as session:
        result = await session.execute(
            select(Doctor).where(Doctor.telegram_id == telegram_id)
        )
        doctor = result.scalar_one_or_none()
        if not doctor:
            await query.edit_message_text("Doctor record not found.")
            return
        s_result = await session.execute(
            select(CS).where(
                CS.doctor_id == doctor.id,
                CS.status.in_([SessionStatus.AWAITING_DOCTOR, SessionStatus.ACTIVE]),
            )
        )
        sessions = s_result.scalars().all()

    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("\u2190 Back to Menu", callback_data="backtomenu")]])

    if not sessions:
        await query.edit_message_text("📋 Your Queue\n\nNo pending sessions.", reply_markup=back_btn)
        return

    lines = ["📋 Your Queue\n"]
    for s in sessions:
        status = s.status.value if hasattr(s.status, 'value') else s.status
        lines.append(f"  #{s.id} — {status} — {s.issue_description[:40]}...")
    await query.edit_message_text("\n".join(lines), reply_markup=back_btn)


async def _doc_waitlist(query, telegram_id: int) -> None:
    """Show patients waiting for this doctor."""
    from bot.models.doctor import Doctor
    from bot.models.waitlist import Waitlist, WaitlistStatus
    from bot.models.session import Session as CS, SessionStatus
    from bot.models.user import User
    from sqlalchemy import select, or_

    async with session_factory() as session:
        result = await session.execute(
            select(Doctor).where(Doctor.telegram_id == telegram_id)
        )
        doctor = result.scalar_one_or_none()
        if not doctor:
            await query.edit_message_text("Doctor record not found.")
            return

        # Waitlist entries
        wl_result = await session.execute(
            select(Waitlist, User).join(User, Waitlist.user_id == User.id).where(
                Waitlist.status == WaitlistStatus.WAITING,
                or_(
                    Waitlist.doctor_id == doctor.id,
                    Waitlist.specialty == doctor.specialty.value,
                ),
            ).order_by(Waitlist.position.asc())
        )
        waitlist_rows = wl_result.all()

        # Pending sessions
        sess_result = await session.execute(
            select(CS, User).join(User, CS.user_id == User.id).where(
                CS.doctor_id == doctor.id,
                CS.status.in_([SessionStatus.AWAITING_DOCTOR, SessionStatus.PENDING_APPROVAL]),
            ).order_by(CS.created_at.asc())
        )
        pending_rows = sess_result.all()

    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("\u2190 Back to Menu", callback_data="backtomenu")]])

    lines = ["📋 Patients Waiting\n"]

    if pending_rows:
        lines.append("— Pending Sessions —")
        for sess, user in pending_rows:
            status = sess.status.value.replace("_", " ").title()
            phone = f" | 📞 {user.phone}" if user.phone else ""
            lines.append(f"  #{sess.id} {status}{phone}")
            if sess.issue_description:
                lines.append(f"    {sess.issue_description[:60]}...")
        lines.append("")

    if waitlist_rows:
        lines.append("— Waitlist —")
        for wl, user in waitlist_rows:
            phone = f" | 📞 {user.phone}" if user.phone else ""
            lines.append(f"  #{wl.position} Patient #{user.id}{phone} ({wl.specialty})")
        lines.append("")

    if not pending_rows and not waitlist_rows:
        lines.append("No patients waiting right now.")

    total = len(pending_rows) + len(waitlist_rows)
    if total:
        lines.insert(1, f"Total: {total} patient(s)\n")

    await query.edit_message_text("\n".join(lines), reply_markup=back_btn)


async def _doc_reviews(query, telegram_id: int) -> None:
    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("\u2190 Back to Menu", callback_data="backtomenu")]])
    doctor = await _get_doctor(telegram_id)
    if doctor:
        avg = round(doctor.rating_avg, 2) if doctor.rating_avg else 0.0
        cnt = doctor.rating_count or 0
        await query.edit_message_text(f"\u2b50 Your Reviews\n\nRating: {avg}/5 ({cnt} reviews)", reply_markup=back_btn)
    else:
        await query.edit_message_text("No reviews yet.", reply_markup=back_btn)


async def _doc_profile(query, telegram_id: int) -> None:
    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("\u2190 Back to Menu", callback_data="backtomenu")]])
    doctor = await _get_doctor(telegram_id)
    if not doctor:
        await query.edit_message_text("Profile not found.", reply_markup=back_btn)
        return
    spec = doctor.specialty.value if hasattr(doctor.specialty, 'value') else doctor.specialty
    await query.edit_message_text(
        f"Your Profile\n\n"
        f"Name: Dr. {doctor.full_name}\n"
        f"Specialty: {spec.title()}\n"
        f"License: {doctor.license_number}\n"
        f"Bio: {doctor.bio or 'Not set'}\n"
        f"Available: {'Yes' if doctor.is_available else 'No'}\n"
        f"Rating: {round(doctor.rating_avg, 2)}/5 ({doctor.rating_count} reviews)",
        reply_markup=back_btn,
    )


DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
DAY_LABELS = {"monday": "Mon", "tuesday": "Tue", "wednesday": "Wed", "thursday": "Thu",
              "friday": "Fri", "saturday": "Sat", "sunday": "Sun"}
SLOTS = ["morning", "afternoon", "evening"]
SLOT_LABELS = {"morning": "🌅 9-12", "afternoon": "☀️ 12-17", "evening": "🌙 17-21"}


async def _doc_schedule(query, telegram_id: int) -> None:
    """Show doctor's availability schedule with toggle buttons."""
    from bot.models.doctor import Doctor
    from sqlalchemy import select
    async with session_factory() as session:
        result = await session.execute(
            select(Doctor).where(Doctor.telegram_id == telegram_id)
        )
        doctor = result.scalar_one_or_none()
        if not doctor:
            await query.edit_message_text("Doctor record not found.")
            return
        schedule = doctor.availability_schedule or {}

    lines = ["📅 Your Availability Schedule\n"]
    lines.append("Tap a slot to toggle it on/off:\n")

    for day in DAYS:
        day_slots = schedule.get(day, [])
        slot_status = []
        for s in SLOTS:
            if s in day_slots:
                slot_status.append(f"✅ {SLOT_LABELS[s]}")
            else:
                slot_status.append(f"⬜ {SLOT_LABELS[s]}")
        lines.append(f"**{DAY_LABELS[day]}**: {' | '.join(slot_status)}")

    # Build toggle buttons — 3 buttons per day row
    buttons = []
    for day in DAYS:
        day_slots = schedule.get(day, [])
        row = []
        for s in SLOTS:
            is_on = s in day_slots
            label = f"{'✅' if is_on else '⬜'} {DAY_LABELS[day]} {s[:3]}"
            row.append(InlineKeyboardButton(label, callback_data=f"sched:{day}:{s}"))
        buttons.append(row)

    buttons.append([InlineKeyboardButton("← Back to Menu", callback_data="backtomenu")])

    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def handle_schedule_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle a day/slot on or off in doctor's schedule."""
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")  # sched:<day>:<slot>
    day = parts[1]
    slot = parts[2]

    from bot.models.doctor import Doctor
    from sqlalchemy import select
    async with session_factory() as session:
        result = await session.execute(
            select(Doctor).where(Doctor.telegram_id == update.effective_user.id)
        )
        doctor = result.scalar_one_or_none()
        if not doctor:
            await query.edit_message_text("Doctor record not found.")
            return

        schedule = dict(doctor.availability_schedule or {})
        day_slots = list(schedule.get(day, []))

        if slot in day_slots:
            day_slots.remove(slot)
        else:
            day_slots.append(slot)

        schedule[day] = day_slots
        doctor.availability_schedule = schedule
        await session.commit()

    # Re-render the schedule view
    await _doc_schedule(query, update.effective_user.id)


# ── Patient menu buttons ──────────────────────────────────────────────────

async def handle_patient_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    action = query.data.split(":")[1]
    lang = context.user_data.get("lang", "en")

    try:
        if action == "browse":
            await _browse_doctors(query, lang)
            return
        if action == "call":
            await _call_doctor(query, lang)
            return
        await _patient_menu_inner(query, action, lang, update.effective_user.id)
    except Exception as exc:
        logger.error("Patient menu error (%s): %s", action, exc, exc_info=True)
        await query.edit_message_text(f"Error: {exc}")


async def _browse_doctors(query, lang: str) -> None:
    from bot.models.doctor import Doctor
    from sqlalchemy import select
    async with session_factory() as session:
        # Available doctors first, then unavailable
        result = await session.execute(
            select(Doctor).where(
                Doctor.is_verified.is_(True),
            ).order_by(Doctor.is_available.desc(), Doctor.rating_avg.desc())
        )
        doctors = result.scalars().all()

    if not doctors:
        back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("\u2190 Back to Menu", callback_data="backtomenu")]])
        await query.edit_message_text("No doctors registered yet.", reply_markup=back_btn)
        return

    available = [d for d in doctors if d.is_available]
    unavailable = [d for d in doctors if not d.is_available]

    lines = ["👨‍⚕️ Available Doctors\n"]
    if available:
        for d in available:
            spec = d.specialty.value if hasattr(d.specialty, 'value') else d.specialty
            rating = f"⭐ {round(d.rating_avg, 1)}/5" if d.rating_count else "New"
            # Schedule summary
            sched = d.availability_schedule or {}
            active_days = [DAY_LABELS[day] for day in DAYS if sched.get(day)]
            sched_str = f" | {', '.join(active_days)}" if active_days else ""
            lines.append(f"🟢 Dr. {d.full_name} — {spec.title()} ({rating}){sched_str}")
    else:
        lines.append("No doctors are currently available.")

    if unavailable:
        lines.append("\n🔴 Currently Unavailable:")
        for d in unavailable:
            spec = d.specialty.value if hasattr(d.specialty, 'value') else d.specialty
            lines.append(f"  Dr. {d.full_name} — {spec.title()}")

    # Build buttons — book button for each available doctor
    buttons = []
    for d in available:
        buttons.append([InlineKeyboardButton(
            f"📅 Book Dr. {d.full_name}",
            callback_data=f"bookdoc:{d.id}",
        )])

    buttons.append([InlineKeyboardButton("\u2190 Back to Menu", callback_data="backtomenu")])
    await query.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(buttons))


CALL_CENTER_PHONE = "+251944140404"


async def _call_doctor(query, lang: str) -> None:
    """Show call center number with a clickable call button."""
    await query.edit_message_text(
        t("call_center_info", lang),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                t("btn_call_now", lang),
                url=f"tel:{CALL_CENTER_PHONE}",
            )],
            [InlineKeyboardButton("\u2190 Back to Menu", callback_data="backtomenu")],
        ]),
    )


async def handle_book_doctor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Patient clicks 'Book Dr. X' from browse — redirects to consultation flow."""
    query = update.callback_query
    await query.answer()
    doctor_id = int(query.data.split(":")[1])
    lang = context.user_data.get("lang", "en")

    from bot.models.doctor import Doctor
    async with session_factory() as session:
        doctor = await session.get(Doctor, doctor_id)
        if not doctor or not doctor.is_available:
            await query.edit_message_text(
                "This doctor is no longer available. Please try another.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("👨‍⚕️ Browse Doctors", callback_data="menu:browse"),
                    InlineKeyboardButton("← Back to Menu", callback_data="backtomenu"),
                ]]),
            )
            return
        spec = doctor.specialty.value if hasattr(doctor.specialty, 'value') else doctor.specialty

    # Store preselected doctor and redirect to consultation
    context.user_data["preselected_doctor_id"] = doctor_id
    context.user_data["session_specialty"] = spec
    await query.edit_message_text(
        f"📅 Booking with Dr. {doctor.full_name} ({spec.title()})\n\n"
        f"Redirecting to consultation flow...",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🩺 Start Consultation", callback_data="menu:consult")],
            [InlineKeyboardButton("← Back to Menu", callback_data="backtomenu")],
        ]),
    )


async def _patient_menu_inner(query, action: str, lang: str, telegram_id: int) -> None:
    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("\u2190 Back to Menu", callback_data="backtomenu")]])

    if action == "history":
        from bot.database import session_factory
        from bot.models.session import Session as ConsultSession
        from bot.models.question import Question
        from bot.models.user import User
        from sqlalchemy import select

        async with session_factory() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                await query.edit_message_text(t("error_not_registered", lang), reply_markup=back_btn)
                return

            q_result = await session.execute(
                select(Question).where(Question.user_id == user.id)
                .order_by(Question.created_at.desc()).limit(10)
            )
            questions = q_result.scalars().all()

            s_result = await session.execute(
                select(ConsultSession).where(ConsultSession.user_id == user.id)
                .order_by(ConsultSession.created_at.desc()).limit(10)
            )
            sessions = s_result.scalars().all()

        lines = ["Your History\n"]

        if questions:
            lines.append("--- Questions ---")
            for q in questions:
                cat = q.category.value if hasattr(q.category, 'value') else q.category
                lines.append(f"  #{q.id} [{cat}] {q.status.value} \u2014 {q.text[:50]}...")
        else:
            lines.append("No questions yet.")

        if sessions:
            lines.append("\n--- Consultations ---")
            for s in sessions:
                lines.append(f"  #{s.id} {s.status.value} \u2014 {str(s.created_at)[:16]}")
        else:
            lines.append("\nNo consultations yet.")

        await query.edit_message_text("\n".join(lines), reply_markup=back_btn)

    elif action == "settings":
        from bot.utils.keyboards import language_keyboard
        await query.edit_message_text(
            "⚙️ Settings\n\nChange your language:",
            reply_markup=language_keyboard(),
        )


async def handle_language_change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language selection from Settings or initial onboarding (standalone fallback)."""
    query = update.callback_query
    await query.answer()

    lang = query.data.split(":")[1]  # "lang:en" or "lang:am"
    context.user_data["lang"] = lang

    # Check if user exists — if so, update language in DB
    from bot.models.user import User
    from sqlalchemy import select

    async with session_factory() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == update.effective_user.id)
        )
        user = result.scalar_one_or_none()

        if user:
            # Existing user — this is a language change from Settings
            user.language = lang
            await session.commit()

            from bot.i18n import t
            from bot.utils.keyboards import main_menu_keyboard
            lang_name = "English 🇬🇧" if lang == "en" else "አማርኛ 🇪🇹"
            await query.edit_message_text(
                f"✅ Language changed to {lang_name}",
            )
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=t("patient_ready", lang),
                reply_markup=main_menu_keyboard(lang),
            )
        else:
            # New user — they're in onboarding, show disclaimer
            from bot.i18n import t
            from bot.utils.keyboards import consent_keyboard
            await query.edit_message_text(
                f"{t('disclaimer_title', lang)}\n\n{t('disclaimer_body', lang)}",
                reply_markup=consent_keyboard(lang),
            )


