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


BATCH_SIZE = 15  # keys per API call to stay within token limits


class TranslationService:
    @staticmethod
    async def translate_single(text: str) -> str:
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

    @staticmethod
    async def translate_batch(keys_and_texts: list[tuple[str, str]]) -> dict[str, str]:
        """
        Batch-translate multiple strings in one API call.
        Format: send as numbered list, parse numbered responses.
        """
        if not settings.openrouter_api_key or not keys_and_texts:
            return {}

        # Build numbered prompt
        lines = []
        for i, (key, text) in enumerate(keys_and_texts, 1):
            # Collapse newlines for the prompt
            clean = text.replace("\n", " ↵ ")
            lines.append(f"{i}. [{key}] {clean}")

        prompt = (
            "Translate each numbered item below to Ethiopian Amharic. "
            "Return ONLY the translations in the same numbered format: '1. translation\\n2. translation\\n...' "
            "Preserve emoji. Restore ↵ as newlines in output.\n\n"
            + "\n".join(lines)
        )

        try:
            async with httpx.AsyncClient(timeout=60) as client:
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
                            {"role": "user", "content": prompt},
                        ],
                    },
                )
                response.raise_for_status()
                raw = response.json()["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            logger.error("Batch translation failed: %s", exc)
            return {}

        # Parse numbered response
        results: dict[str, str] = {}
        response_lines = raw.split("\n")
        idx = 0
        for line in response_lines:
            line = line.strip()
            if not line:
                continue
            # Try to match "1. ..." or "1) ..." format
            for sep in [". ", ") "]:
                parts = line.split(sep, 1)
                if len(parts) == 2 and parts[0].strip().isdigit():
                    num = int(parts[0].strip()) - 1
                    if 0 <= num < len(keys_and_texts):
                        key = keys_and_texts[num][0]
                        translated = parts[1].strip()
                        # Strip any [key] prefix if model echoed it
                        if translated.startswith(f"[{key}]"):
                            translated = translated[len(f"[{key}]"):].strip()
                        results[key] = translated.replace(" ↵ ", "\n")
                    break
            else:
                # Fallback: assign by order
                if idx < len(keys_and_texts):
                    key = keys_and_texts[idx][0]
                    results[key] = line.replace(" ↵ ", "\n")
                    idx += 1

        return results

    @classmethod
    async def warm_cache(cls) -> None:
        """
        On startup: batch-translate all English strings missing from DB cache.
        Uses batches of BATCH_SIZE to minimize API calls.
        """
        from bot.i18n.en import STRINGS as EN_STRINGS
        from bot.models.translation import Translation
        from bot.i18n import am

        if not settings.openrouter_api_key:
            logger.warning("OPENROUTER_API_KEY not set — Amharic translation skipped.")
            return

        async with session_factory() as session:
            result = await session.execute(
                select(Translation).where(Translation.lang == "am")
            )
            cached = {row.key: row.text for row in result.scalars()}

        missing_keys = [k for k in EN_STRINGS if k not in cached]

        if not missing_keys:
            logger.info("Translation cache up to date (%d keys).", len(cached))
            _load_into_module(cached, am)
            return

        logger.info("Translating %d missing keys to Amharic in batches of %d...", len(missing_keys), BATCH_SIZE)

        translated: dict[str, str] = dict(cached)

        # Process in batches
        for i in range(0, len(missing_keys), BATCH_SIZE):
            batch_keys = missing_keys[i:i + BATCH_SIZE]
            batch_items = [(k, EN_STRINGS[k]) for k in batch_keys]

            batch_results = await cls.translate_batch(batch_items)

            # Fallback: translate individually any that failed in batch
            for key in batch_keys:
                if key not in batch_results:
                    try:
                        batch_results[key] = await cls.translate_single(EN_STRINGS[key])
                    except Exception as exc:
                        logger.warning("Single translate fallback failed for '%s': %s", key, exc)
                        continue

            # Save to DB
            async with session_factory() as session:
                for key, am_text in batch_results.items():
                    translated[key] = am_text
                    session.add(Translation(
                        key=key,
                        lang="am",
                        text=am_text,
                        model_used=AMHARIC_MODEL,
                        created_at=datetime.utcnow(),
                    ))
                await session.commit()

            logger.info("Batch %d/%d done (%d keys).", i // BATCH_SIZE + 1,
                        (len(missing_keys) + BATCH_SIZE - 1) // BATCH_SIZE, len(batch_results))

        _load_into_module(translated, am)
        logger.info("Translation cache warm — %d/%d keys translated.", len(translated), len(EN_STRINGS))


def _load_into_module(strings: dict[str, str], module) -> None:
    """Inject translated strings into the am module at runtime."""
    module.STRINGS.update(strings)
