from __future__ import annotations

import logging

from telegram.ext import Application, ApplicationBuilder

from bot.config import settings

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=getattr(logging, settings.log_level.upper()),
)
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    """Run once after the Application is initialised."""
    logger.info("LongiMed bot starting up...")

    # Pre-warm translation cache
    try:
        from bot.services.translation_service import TranslationService
        await TranslationService.warm_cache()
        logger.info("Translation cache warmed.")
    except Exception as exc:
        logger.warning("Translation warm-up skipped: %s", exc)


def register_handlers(app: Application) -> None:
    """
    Register all handlers in strict priority order.
    EMERGENCY must be group=-1 so it fires before ConversationHandlers.
    """
    # ── Priority -1: Emergency scanner (runs on EVERY text message) ──────
    from bot.handlers.emergency import emergency_handler
    app.add_handler(emergency_handler, group=-1)

    # ── Priority 0: Deep link router (/start with payload) ───────────────
    from bot.handlers.deep_link import deep_link_handler
    app.add_handler(deep_link_handler, group=0)

    # ── Priority 1: Onboarding (/start no payload) ───────────────────────
    from bot.handlers.start import start_conv_handler
    app.add_handler(start_conv_handler, group=1)

    # ── Priority 2: Public Q&A ────────────────────────────────────────────
    from bot.handlers.public_question import public_question_conv_handler
    app.add_handler(public_question_conv_handler, group=2)

    # ── Priority 3: Private session ───────────────────────────────────────
    from bot.handlers.private_session import private_session_conv_handler
    app.add_handler(private_session_conv_handler, group=3)

    # ── Priority 4: Search ────────────────────────────────────────────────
    from bot.handlers.search import search_conv_handler
    app.add_handler(search_conv_handler, group=4)

    # ── Priority 5: Doctor commands ───────────────────────────────────────
    from bot.handlers.doctor import doctor_handlers
    for handler in doctor_handlers:
        app.add_handler(handler, group=5)

    # ── Priority 6: Moderator commands ────────────────────────────────────
    from bot.handlers.moderator import moderator_handlers
    for handler in moderator_handlers:
        app.add_handler(handler, group=6)

    # ── Priority 7a: Q&A approve/reject callbacks (global — fired from admin/mod messages) ──
    from bot.handlers.public_question import question_approve_handler, question_reject_handler
    app.add_handler(question_approve_handler, group=7)
    app.add_handler(question_reject_handler, group=7)

    # ── Priority 7b: Admin commands ───────────────────────────────────────
    from bot.handlers.admin import admin_handlers
    for handler in admin_handlers:
        app.add_handler(handler, group=7)

    # ── Priority 8a: Rating callback ───────────────────────────────────
    from bot.handlers.private_session import rating_handler
    app.add_handler(rating_handler, group=8)

    # ── Priority 8b: Payment confirm/reject callbacks ────────────────
    from bot.handlers.private_session import handle_confirm_payment, handle_reject_payment
    from telegram.ext import CallbackQueryHandler
    app.add_handler(CallbackQueryHandler(handle_confirm_payment, pattern=r"^confirmpay:"), group=8)
    app.add_handler(CallbackQueryHandler(handle_reject_payment, pattern=r"^rejectpay:"), group=8)

    # ── Priority 9: Relay forwarding (catch-all for active relay sessions) ──
    from bot.handlers.private_session import relay_patient_message, relay_doctor_message
    from telegram.ext import MessageHandler, filters
    app.add_handler(
        MessageHandler(filters.ChatType.PRIVATE & (filters.TEXT | filters.PHOTO | filters.VOICE | filters.Document.ALL) & ~filters.COMMAND, relay_patient_message),
        group=9,
    )
    app.add_handler(
        MessageHandler(filters.ChatType.PRIVATE & (filters.TEXT | filters.PHOTO | filters.VOICE | filters.Document.ALL) & ~filters.COMMAND, relay_doctor_message),
        group=10,
    )

    logger.info("All handlers registered.")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log all unhandled errors so we can see them in docker logs."""
    logger.error("Unhandled exception: %s", context.error, exc_info=context.error)
    if hasattr(update, "effective_message") and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "Something went wrong. Please try again or send /start."
            )
        except Exception:
            pass


def main() -> None:
    app = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .build()
    )

    register_handlers(app)
    app.add_error_handler(error_handler)

    logger.info("Starting polling...")
    app.run_polling(
        allowed_updates=["message", "callback_query", "chat_member"],
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
