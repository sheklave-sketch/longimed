"""
Search handler — search Q&A history and doctor directory.
Uses PostgreSQL ILIKE for now. Phase II: pg_trgm full-text search.
"""

import logging

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

logger = logging.getLogger(__name__)

# States
SEARCH_TYPE = 40
SEARCH_TERM = 41
RESULTS = 42


async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry from /search command or menu:search callback."""
    lang = context.user_data.get("lang", "en")
    text = t("search_prompt", lang)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_search_qa", lang), callback_data="search:qa")],
        [InlineKeyboardButton(t("btn_search_doctors", lang), callback_data="search:doctors")],
        [InlineKeyboardButton(t("btn_back", lang), callback_data="search:back")],
    ])

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=kb)
    else:
        await update.message.reply_text(text, reply_markup=kb)
    return SEARCH_TYPE


async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle search type selection or back button."""
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")

    if query.data == "search:back":
        from bot.utils.keyboards import main_menu_keyboard
        await query.edit_message_text(
            t("main_menu", lang),
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END

    if query.data == "search:restart":
        return await start_search(update, context)

    search_type = query.data.split(":")[1]  # "qa" or "doctors"
    context.user_data["search_type"] = search_type

    prompt = t("search_enter_term_qa", lang) if search_type == "qa" else t("search_enter_term_doctors", lang)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_back", lang), callback_data="search:back_to_type")],
    ])
    await query.edit_message_text(prompt, reply_markup=kb)
    return SEARCH_TERM


async def back_to_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Go back from term entry to type selection."""
    return await start_search(update, context)


async def execute_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Run the search and display results."""
    lang = context.user_data.get("lang", "en")
    term = update.message.text.strip()
    search_type = context.user_data.get("search_type", "qa")

    if len(term) < 2:
        await update.message.reply_text(t("search_term_too_short", lang))
        return SEARCH_TERM

    try:
        if search_type == "qa":
            results = await _search_qa(term)
            text = _format_qa_results(results, term, lang)
        else:
            results = await _search_doctors(term)
            text = _format_doctor_results(results, term, lang)
    except Exception:
        logger.exception("Search failed for term=%r type=%s", term, search_type)
        await update.message.reply_text(
            t("search_error", lang),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(t("btn_search_again", lang), callback_data="search:restart")],
                [InlineKeyboardButton(t("btn_back", lang), callback_data="search:back")],
            ]),
        )
        return RESULTS

    kb_buttons = []

    if not results:
        kb_buttons.append([InlineKeyboardButton(t("btn_search_again", lang), callback_data="search:restart")])
        kb_buttons.append([InlineKeyboardButton(t("btn_back", lang), callback_data="search:back")])
        await update.message.reply_text(
            t("search_no_results", lang, query=term),
            reply_markup=InlineKeyboardMarkup(kb_buttons),
        )
        return RESULTS

    # Doctor results get [Book Consultation] deep link buttons
    if search_type == "doctors":
        bot_username = (await context.bot.get_me()).username
        for r in results[:5]:
            kb_buttons.append([InlineKeyboardButton(
                t("btn_book_consultation", lang) + f" — Dr. {r['name']}",
                url=f"https://t.me/{bot_username}?start=book_doctor_{r['id']}",
            )])

    kb_buttons.append([InlineKeyboardButton(t("btn_search_again", lang), callback_data="search:restart")])
    kb_buttons.append([InlineKeyboardButton(t("btn_back", lang), callback_data="search:back")])

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(kb_buttons),
    )
    return RESULTS


async def handle_results_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle callbacks from the results screen (search again, back)."""
    query = update.callback_query
    await query.answer()

    if query.data == "search:back":
        lang = context.user_data.get("lang", "en")
        from bot.utils.keyboards import main_menu_keyboard
        await query.edit_message_text(
            t("main_menu", lang),
            reply_markup=main_menu_keyboard(lang),
        )
        return ConversationHandler.END

    if query.data == "search:restart":
        return await start_search(update, context)

    return RESULTS


# ── Formatting helpers ──────────────────────────────────────────────────────


def _format_qa_results(results: list[dict], term: str, lang: str) -> str:
    header = t("search_results_header", lang, query=term, count=len(results))
    lines = [header, ""]
    for i, r in enumerate(results, 1):
        cat = r["category"].title() if r["category"] else "General"
        question_preview = r["text"][:80]
        if r.get("answer_text"):
            doctor_name = r.get("doctor_name", "Doctor")
            answer_preview = r["answer_text"][:60]
            lines.append(f"{i}. [{cat}] {question_preview}...")
            lines.append(f"   Dr. {doctor_name}: {answer_preview}...")
        else:
            lines.append(f"{i}. [{cat}] {question_preview}...")
            lines.append(f"   {t('search_awaiting_answer', lang)}")
        lines.append("")
    return "\n".join(lines)


def _format_doctor_results(results: list[dict], term: str, lang: str) -> str:
    header = t("search_results_header", lang, query=term, count=len(results))
    lines = [header, ""]
    for i, r in enumerate(results, 1):
        status = "\U0001f7e2" if r["is_available"] else "\U0001f534"
        rating = round(r["rating"], 1) if r["rating"] else "—"
        lines.append(f"{i}. {status} Dr. {r['name']} — {r['specialty']}")
        lines.append(f"   Rating: {rating}  |  {', '.join(r.get('languages', []))}")
        lines.append("")
    return "\n".join(lines)


# ── Database search functions ───────────────────────────────────────────────


async def _search_qa(term: str) -> list[dict]:
    from bot.database import session_factory
    from bot.models.question import Question, QuestionStatus
    from sqlalchemy import select, or_, func

    try:
        async with session_factory() as session:
            result = await session.execute(
                select(Question).where(
                    Question.status.in_([QuestionStatus.APPROVED, QuestionStatus.ANSWERED]),
                    or_(
                        func.lower(Question.text).contains(term.lower()),
                        func.lower(Question.answer_text).contains(term.lower()),
                    ),
                ).order_by(Question.created_at.desc()).limit(10)
            )
            questions = result.scalars().all()
    except Exception:
        logger.exception("DB error searching Q&A for term=%r", term)
        return []

    return [
        {
            "id": q.id,
            "category": q.category.value if hasattr(q.category, "value") else q.category,
            "text": q.text,
            "answer_text": q.answer_text,
            "doctor_name": None,  # TODO: eager-load doctor relationship
            "is_anonymous": q.is_anonymous,
            "status": q.status.value,
        }
        for q in questions
    ]


async def _search_doctors(term: str) -> list[dict]:
    from bot.database import session_factory
    from bot.models.doctor import Doctor
    from sqlalchemy import select, or_, func
    from sqlalchemy import String

    try:
        async with session_factory() as session:
            result = await session.execute(
                select(Doctor).where(
                    Doctor.is_verified.is_(True),
                    or_(
                        func.lower(Doctor.full_name).contains(term.lower()),
                        func.lower(Doctor.specialty.cast(String)).contains(term.lower()),
                    ),
                ).limit(10)
            )
            doctors = result.scalars().all()
    except Exception:
        logger.exception("DB error searching doctors for term=%r", term)
        return []

    return [
        {
            "id": d.id,
            "name": d.full_name,
            "specialty": d.specialty.value if hasattr(d.specialty, "value") else d.specialty,
            "rating": d.rating_avg,
            "is_available": d.is_available,
            "languages": d.languages or [],
        }
        for d in doctors
    ]


# ── ConversationHandler ────────────────────────────────────────────────────

search_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_search, pattern=r"^menu:search$"),
        CommandHandler("search", start_search),
    ],
    states={
        SEARCH_TYPE: [
            CallbackQueryHandler(choose_type, pattern=r"^search:(qa|doctors|back|restart)$"),
        ],
        SEARCH_TERM: [
            CallbackQueryHandler(back_to_type, pattern=r"^search:back_to_type$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, execute_search),
        ],
        RESULTS: [
            CallbackQueryHandler(handle_results_callback, pattern=r"^search:(back|restart)$"),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(handle_results_callback, pattern=r"^search:back$"),
        CommandHandler("search", start_search),
    ],
    conversation_timeout=600,
    name="search_conv",
    per_message=False,
)
