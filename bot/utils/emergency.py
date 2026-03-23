from __future__ import annotations

EMERGENCY_KEYWORDS_EN: list[str] = [
    "chest pain", "can't breathe", "cannot breathe", "difficulty breathing",
    "not breathing", "heart attack", "stroke", "severe bleeding", "overdose",
    "poisoning", "suicide", "seizure", "not responding", "unconscious",
    "emergency", "dying", "help me", "passing out", "i'm dying", "im dying",
    "can't move", "cannot move", "paralyzed", "fainted", "collapsed",
]

EMERGENCY_KEYWORDS_AM: list[str] = [
    "የጡቤ ደም", "አልተነሳፕም", "ልፊ አልተነሳፕም", "አቃጠለኝ", "ሞት",
    "እርዳኝ", "ድንገተኛ", "ደም ይወጣል", "ሞቼለሁ", "አልተነፈስኩም",
    "ድንገተኛ ህመም", "ደም", "ስቃይ",
]


def is_emergency(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in EMERGENCY_KEYWORDS_EN + EMERGENCY_KEYWORDS_AM)
