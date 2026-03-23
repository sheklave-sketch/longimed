from __future__ import annotations


def t(key: str, lang: str, **kwargs: object) -> str:
    """
    Look up a translation string.
    Priority: translated cache (am) → English fallback → key name.
    """
    from bot.i18n import en

    if lang == "am":
        # Try live Amharic cache first (populated by TranslationService)
        try:
            from bot.i18n import am
            text = am.STRINGS.get(key)
            if text:
                return text.format(**kwargs) if kwargs else text
        except Exception:
            pass

    text = en.STRINGS.get(key, key)
    return text.format(**kwargs) if kwargs else text
