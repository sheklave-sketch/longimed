from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.i18n import t


def main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_ask_question", lang), callback_data="menu:ask")],
        [InlineKeyboardButton(t("btn_private_consult", lang), callback_data="menu:consult")],
        [InlineKeyboardButton(t("btn_browse_doctors", lang), callback_data="menu:browse")],
        [InlineKeyboardButton(t("btn_call_doctor", lang), callback_data="menu:call")],
        [InlineKeyboardButton(t("btn_my_history", lang), callback_data="menu:history")],
        [InlineKeyboardButton(t("btn_settings", lang), callback_data="menu:settings")],
    ])


def doctor_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_my_queue", lang), callback_data="doc:queue")],
        [
            InlineKeyboardButton(t("btn_set_available", lang), callback_data="doc:available"),
            InlineKeyboardButton(t("btn_set_unavailable", lang), callback_data="doc:unavailable"),
        ],
        [InlineKeyboardButton(t("btn_my_schedule", lang), callback_data="doc:schedule")],
        [InlineKeyboardButton(t("btn_my_reviews", lang), callback_data="doc:reviews")],
        [InlineKeyboardButton(t("btn_my_profile", lang), callback_data="doc:profile")],
    ])


def role_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_patient", lang), callback_data="role:patient")],
        [InlineKeyboardButton(t("btn_doctor", lang), callback_data="role:doctor")],
    ])


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="lang:en"),
            InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="lang:am"),
        ]
    ])


def consent_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_agree", lang), callback_data="consent:agree")],
        [InlineKeyboardButton(t("btn_disagree", lang), callback_data="consent:disagree")],
    ])


def category_keyboard(lang: str) -> InlineKeyboardMarkup:
    from bot.models.doctor import Specialty
    buttons = [
        [InlineKeyboardButton(s.value.title(), callback_data=f"cat:{s.value}")]
        for s in Specialty
    ]
    buttons.append([InlineKeyboardButton(t("btn_back", lang), callback_data="back")])
    return InlineKeyboardMarkup(buttons)


def anonymous_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_anonymous_yes", lang), callback_data="anon:yes")],
        [InlineKeyboardButton(t("btn_anonymous_no", lang), callback_data="anon:no")],
        [InlineKeyboardButton(t("btn_back", lang), callback_data="back")],
    ])


def confirm_cancel_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t("btn_confirm", lang), callback_data="confirm"),
            InlineKeyboardButton(t("btn_cancel", lang), callback_data="cancel"),
        ],
        [InlineKeyboardButton(t("btn_edit", lang), callback_data="edit")],
    ])


def rating_keyboard(session_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(str(i) + "⭐", callback_data=f"rate:{session_id}:{i}")
        for i in range(1, 6)
    ]])


def admin_question_keyboard(question_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"qmod:approve:{question_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"qmod:reject:{question_id}"),
        ]
    ])


def doctor_list_keyboard(doctors: list, lang: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            f"Dr. {d.full_name} — {d.specialty.value.title()} ({'🟢' if d.is_available else '🟡'})",
            callback_data=f"selectdoc:{d.id}"
        )]
        for d in doctors
    ]
    buttons.append([InlineKeyboardButton(t("btn_back", lang), callback_data="back")])
    return InlineKeyboardMarkup(buttons)


def waitlist_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_join_waitlist", lang), callback_data="waitlist:join")],
        [InlineKeyboardButton(t("btn_back", lang), callback_data="back")],
    ])


def report_reason_keyboard(lang: str, target_type: str, target_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_report_misinformation", lang), callback_data=f"report:{target_type}:{target_id}:misinfo")],
        [InlineKeyboardButton(t("btn_report_inappropriate", lang), callback_data=f"report:{target_type}:{target_id}:inappropriate")],
        [InlineKeyboardButton(t("btn_report_other", lang), callback_data=f"report:{target_type}:{target_id}:other")],
        [InlineKeyboardButton(t("btn_cancel", lang), callback_data="cancel")],
    ])
