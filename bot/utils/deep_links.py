from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DeepLinkType(str, Enum):
    BOOK_DOCTOR = "book_doctor"
    BROWSE_SPECIALTY = "browse"
    QUESTION = "question"
    FOLLOW_UP = "follow_up"
    ANSWER_QUESTION = "answer"
    FOLLOWUP_QUESTION = "followup"
    DOCTOR_PROFILE = "doctor_profile"
    WAITLIST_ACCEPT = "waitlist_accept"
    REPORT = "report"


@dataclass
class DeepLink:
    type: DeepLinkType
    params: dict


def parse_payload(payload: str | None) -> DeepLink | None:
    """Parse a /start payload into a structured DeepLink."""
    if not payload:
        return None
    parts = payload.split("_")
    try:
        if payload.startswith("book_doctor_"):
            return DeepLink(DeepLinkType.BOOK_DOCTOR, {"doctor_id": int(parts[-1])})
        if payload.startswith("browse_"):
            return DeepLink(DeepLinkType.BROWSE_SPECIALTY, {"specialty": parts[-1]})
        if payload.startswith("question_"):
            return DeepLink(DeepLinkType.QUESTION, {"question_id": int(parts[-1])})
        if payload.startswith("answer_"):
            return DeepLink(DeepLinkType.ANSWER_QUESTION, {"question_id": int(parts[-1])})
        if payload.startswith("followup_") and not payload.startswith("followup_question"):
            return DeepLink(DeepLinkType.FOLLOWUP_QUESTION, {"question_id": int(parts[-1])})
        if payload.startswith("follow_up_"):
            return DeepLink(DeepLinkType.FOLLOW_UP, {"question_id": int(parts[-1])})
        if payload.startswith("doctor_profile_"):
            return DeepLink(DeepLinkType.DOCTOR_PROFILE, {"doctor_id": int(parts[-1])})
        if payload.startswith("waitlist_accept_"):
            return DeepLink(DeepLinkType.WAITLIST_ACCEPT, {"session_id": int(parts[-1])})
        if payload.startswith("report_"):
            return DeepLink(DeepLinkType.REPORT, {
                "target_type": parts[1],
                "target_id": int(parts[2]),
            })
    except (IndexError, ValueError):
        return None
    return None


def make_book_link(bot_username: str, doctor_id: int) -> str:
    return f"https://t.me/{bot_username}?start=book_doctor_{doctor_id}"


def make_profile_link(bot_username: str, doctor_id: int) -> str:
    return f"https://t.me/{bot_username}?start=doctor_profile_{doctor_id}"


def make_waitlist_link(bot_username: str, session_id: int) -> str:
    return f"https://t.me/{bot_username}?start=waitlist_accept_{session_id}"
