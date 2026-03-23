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

    # ── Priority 7: Admin commands ────────────────────────────────────────
    from bot.handlers.admin import admin_handlers
    for handler in admin_handlers:
        app.add_handler(handler, group=7)

    logger.info("All handlers registered.")


def main() -> None:
    app = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .build()
    )

    register_handlers(app)

    logger.info("Starting polling...")
    app.run_polling(
        allowed_updates=["message", "callback_query", "chat_member"],
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
