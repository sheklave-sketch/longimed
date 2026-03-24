from __future__ import annotations

import logging
from datetime import datetime

import httpx
from sqlalchemy import select

from bot.config import settings
from bot.database import session_factory

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
AMHARIC_MODEL = "google/gemini-2.0-flash-001"
MEDICAL_SYSTEM_PROMPT = (
    "You are a professional medical translator specializing in Ethiopian Amharic. "
    "Translate the given text accurately and naturally into Amharic. "
    "Keep medical terminology precise. Preserve any emoji. "
    "Return only the translated text — no explanations."
)


class TranslationService:
    @staticmethod
    async def translate(text: str) -> str:
        """Translate a single string to Amharic via OpenRouter/Gemini."""
        if not settings.openrouter_api_key:
            return text

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": AMHARIC_MODEL,
                    "messages": [
                        {"role": "system", "content": MEDICAL_SYSTEM_PROMPT},
                        {"role": "user", "content": text},
                    ],
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()

    @classmethod
    async def warm_cache(cls) -> None:
        """
        On startup: translate all English strings missing from the DB cache.
        Runs once; subsequent bot restarts only translate new/changed keys.
        """
        from bot.i18n.en import STRINGS as EN_STRINGS
        from bot.models.translation import Translation
        from bot.i18n import am

        if not settings.openrouter_api_key:
            logger.warning("OPENROUTER_API_KEY not set — Amharic translation skipped.")
            return

        async with session_factory() as session:
            # Load existing cache
            result = await session.execute(
                select(Translation).where(Translation.lang == "am")
            )
            cached = {row.key: row.text for row in result.scalars()}

        missing_keys = [k for k in EN_STRINGS if k not in cached]

        if not missing_keys:
            logger.info("Translation cache up to date (%d keys).", len(cached))
            _load_into_module(cached, am)
            return

        logger.info("Translating %d missing keys to Amharic...", len(missing_keys))

        translated: dict[str, str] = dict(cached)
        for key in missing_keys:
            try:
                am_text = await cls.translate(EN_STRINGS[key])
                translated[key] = am_text

                async with session_factory() as session:
                    row = Translation(
                        key=key,
                        lang="am",
                        text=am_text,
                        model_used=AMHARIC_MODEL,
                        created_at=datetime.utcnow(),
                    )
                    session.add(row)
                    await session.commit()
            except Exception as exc:
                logger.warning("Failed to translate key '%s': %s", key, exc)

        _load_into_module(translated, am)
        logger.info("Translation cache warm — %d/%d keys translated.", len(translated), len(EN_STRINGS))


def _load_into_module(strings: dict[str, str], module) -> None:
    """Inject translated strings into the am module at runtime."""
    module.STRINGS.update(strings)
