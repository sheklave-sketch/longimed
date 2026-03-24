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

CHOOSE_TYPE = 30
ENTER_TERM = 31


async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry from /search command or menu:browse callback."""
    lang = context.user_data.get("lang", "en")
    text = f"🔍 {t('search_prompt', lang)}"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_search_qa", lang), callback_data="search:qa")],
        [InlineKeyboardButton(t("btn_search_doctors", lang), callback_data="search:doctors")],
        [InlineKeyboardButton(t("btn_back", lang), callback_data="back")],
    ])

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=kb)
    else:
        await update.message.reply_text(text, reply_markup=kb)
    return CHOOSE_TYPE


async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "back":
        from bot.utils.keyboards import main_menu_keyboard
        lang = context.user_data.get("lang", "en")
        await query.edit_message_text("Main menu:", reply_markup=main_menu_keyboard(lang))
        return ConversationHandler.END

    search_type = query.data.split(":")[1]
    context.user_data["search_type"] = search_type
    lang = context.user_data.get("lang", "en")

    await query.edit_message_text(t("search_enter_term", lang))
    return ENTER_TERM


async def execute_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "en")
    term = update.message.text.strip()
    search_type = context.user_data.get("search_type", "qa")

    if search_type == "qa":
        results = await _search_qa(term)
    else:
        results = await _search_doctors(term)

    if not results:
        await update.message.reply_text(
            t("search_no_results", lang, query=term),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Search again", callback_data="search:restart")],
                [InlineKeyboardButton(t("btn_back", lang), callback_data="back")],
            ]),
        )
        return CHOOSE_TYPE

    # Format results
    lines = []
    for i, r in enumerate(results[:10], 1):
        if search_type == "qa":
            lines.append(f"{i}. *{r['category']}*: {r['text'][:80]}...")
        else:
            status = "🟢" if r["is_available"] else "🔴"
            lines.append(f"{i}. {status} Dr. {r['name']} — {r['specialty']} ⭐{r['rating']}")

    text = f"Found {len(results)} results for \"{term}\":\n\n" + "\n".join(lines)

    kb_buttons = []
    if search_type == "doctors":
        for r in results[:5]:
            kb_buttons.append([InlineKeyboardButton(
                f"📋 Dr. {r['name']}", callback_data=f"selectdoc:{r['id']}"
            )])
    kb_buttons.append([InlineKeyboardButton("🔍 Search again", callback_data="search:restart")])
    kb_buttons.append([InlineKeyboardButton(t("btn_back", lang), callback_data="back")])

    await update.message.reply_text(
        text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb_buttons),
    )
    return CHOOSE_TYPE


async def _search_qa(term: str) -> list[dict]:
    from bot.database import session_factory
    from bot.models.question import Question, QuestionStatus
    from sqlalchemy import select

    async with session_factory() as session:
        result = await session.execute(
            select(Question).where(
                Question.status == QuestionStatus.ANSWERED,
                Question.text.ilike(f"%{term}%"),
            ).limit(10)
        )
        questions = result.scalars().all()

    return [
        {"category": q.category.value if hasattr(q.category, 'value') else q.category,
         "text": q.text, "id": q.id}
        for q in questions
    ]


async def _search_doctors(term: str) -> list[dict]:
    from bot.database import session_factory
    from bot.models.doctor import Doctor
    from sqlalchemy import select, or_

    async with session_factory() as session:
        result = await session.execute(
            select(Doctor).where(
                Doctor.is_verified.is_(True),
                or_(
                    Doctor.full_name.ilike(f"%{term}%"),
                    Doctor.bio.ilike(f"%{term}%"),
                ),
            ).limit(10)
        )
        doctors = result.scalars().all()

    return [
        {
            "id": d.id,
            "name": d.full_name,
            "specialty": d.specialty.value,
            "rating": d.rating_avg,
            "is_available": d.is_available,
        }
        for d in doctors
    ]


search_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_search, pattern=r"^menu:browse$"),
        CommandHandler("search", start_search),
    ],
    states={
        CHOOSE_TYPE: [
            CallbackQueryHandler(choose_type, pattern=r"^(search:|back)"),
        ],
        ENTER_TERM: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, execute_search),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(choose_type, pattern=r"^back$"),
    ],
    conversation_timeout=600,
    name="search_conv",
    per_message=False,
)
