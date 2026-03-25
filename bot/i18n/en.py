"""
English strings — source of truth for all bot messages.
All Amharic strings are generated from these via TranslationService.
"""

STRINGS: dict[str, str] = {
    # ── Onboarding ──────────────────────────────────────────────────────
    "welcome": (
        "Welcome to LongiMed 🏥\n\n"
        "Connecting you with verified Ethiopian doctors — anytime, anywhere.\n\n"
        "Tap below to get started."
    ),
    "select_language": "Please choose your language / ቋንቋዎን ይምረጡ",
    "btn_english": "🇬🇧 English",
    "btn_amharic": "🇪🇹 አማርኛ",

    # ── Disclaimer ──────────────────────────────────────────────────────
    "disclaimer_title": "⚠️ Before We Begin",
    "disclaimer_body": (
        "LongiMed connects you with licensed Ethiopian medical professionals for "
        "general health guidance.\n\n"
        "• It does NOT replace in-person medical care\n"
        "• Doctors share their professional opinion — LongiMed is not liable for outcomes\n"
        "• All conversations are stored securely\n\n"
        "🚨 For emergencies, call 907 immediately."
    ),
    "btn_agree": "✅ I Understand & Agree",
    "btn_disagree": "❌ I Do Not Agree",
    "disagree_farewell": "No problem. If you change your mind, just send /start. Stay safe! 🙏",

    # ── Role selection ───────────────────────────────────────────────────
    "role_question": "Are you looking for medical help, or are you a healthcare provider?",
    "btn_patient": "👤 I'm a Patient",
    "btn_doctor": "👨‍⚕️ I'm a Doctor",

    # ── Patient onboarding ───────────────────────────────────────────────
    "patient_welcome": "Great! 👋 Just one quick step to get you set up.",
    "phone_request": (
        "Please share your phone number.\n\n"
        "This keeps your account secure and lets doctors reach you if needed."
    ),
    "btn_share_phone": "📱 Share My Phone Number",
    "patient_ready": (
        "You're all set! ✅\n\n"
        "Here's what you can do:"
    ),

    # ── Main menus ───────────────────────────────────────────────────────
    "btn_ask_question": "💬 Ask a Question",
    "btn_private_consult": "🩺 Private Consultation",
    "btn_browse_doctors": "👨‍⚕️ Browse Doctors",
    "btn_my_history": "📋 My History",
    "btn_settings": "⚙️ Settings",
    "btn_back": "← Back",
    "btn_cancel": "✖ Cancel",
    "btn_confirm": "✅ Confirm",
    "btn_edit": "✏️ Edit",

    # ── Doctor onboarding ────────────────────────────────────────────────
    "doctor_welcome": (
        "Welcome, Doctor! 👨‍⚕️\n\n"
        "Registration takes about 3 minutes.\n"
        "We'll verify your medical license and get you set up."
    ),
    "btn_open_registration": "📋 Open Registration Portal",
    "doctor_submitted": (
        "Thank you! ✅ Your application is under review.\n\n"
        "We typically respond within 48 hours. "
        "You'll receive a message here once verified."
    ),
    "doctor_approved": (
        "🎉 Congratulations! You're now a verified LongiMed doctor.\n\n"
        "Here's what you can do:"
    ),
    "doctor_rejected": "Your application was not approved. Reason:\n\n{reason}\n\nYou may reapply after addressing the above.",

    # ── Doctor menu ──────────────────────────────────────────────────────
    "btn_my_queue": "📋 My Queue",
    "btn_set_available": "✅ Set Available",
    "btn_set_unavailable": "🔴 Set Unavailable",
    "btn_my_schedule": "📅 My Schedule",
    "btn_my_reviews": "⭐ My Reviews",
    "btn_my_profile": "👤 My Profile",

    # ── Emergency ────────────────────────────────────────────────────────
    "emergency_title": "🚨 THIS SOUNDS LIKE AN EMERGENCY",
    "emergency_body": (
        "Please contact emergency services immediately:\n\n"
        "🚑 Ambulance: 907\n"
        "👮 Police: 991\n"
        "🚒 Fire: 939\n\n"
        "Once you are safe, you're welcome to return to LongiMed."
    ),
    "btn_nearest_hospital": "📍 Find Nearest Hospital",

    # ── Public Q&A ───────────────────────────────────────────────────────
    "qa_intro": (
        "Ask a health question and get an answer from a verified doctor. "
        "Your question may be seen by other users — this helps the whole community."
    ),
    "qa_select_category": "What area does your question relate to?",
    "qa_anonymous_prompt": "Would you like to ask this anonymously?",
    "btn_anonymous_yes": "🕵️ Yes, keep me anonymous",
    "btn_anonymous_no": "👤 No, show my name",
    "qa_enter_question": "Go ahead — type your question:",
    "qa_preview": "Here's your question:\n\n{text}\n\nLooks good?",
    "qa_submitted": "✅ Your question has been submitted for review. We'll notify you once it's live.",
    "qa_approved_notify": "Your question has been approved and posted to our channel! 📢",
    "qa_rejected_notify": "Your question wasn't approved. Reason:\n\n{reason}",
    "qa_answered_notify": "A doctor has answered your question! 🩺",

    # ── Private session ──────────────────────────────────────────────────
    "session_intro": "Let's connect you with a doctor. This usually takes just a few minutes.",
    "session_select_package": "Choose a consultation type:",
    "btn_free_trial": "🆓 Free Trial (15 min)",
    "btn_single_session": "💳 Single Session (30 min) — {price} ETB",
    "session_select_specialty": "What type of doctor do you need?",
    "session_select_doctor": "Available doctors in {specialty}:",
    "session_no_doctors": (
        "No doctors are available right now in that specialty. 😔\n\n"
        "Would you like to join the waitlist? We'll notify you the moment a doctor is free."
    ),
    "btn_join_waitlist": "📋 Join Waitlist",
    "session_enter_issue": "Briefly describe what's going on (in your own words):",
    "session_awaiting": "Your session is being reviewed. We'll connect you with your doctor shortly. 🕐",
    "session_assigned": "You've been connected with Dr. {name}! Your session is starting now. 🩺",
    "session_expiry_warning": "⏰ 5 minutes remaining in your session.",
    "session_resolved": "Your session has ended. How was your experience with Dr. {name}?",
    "btn_report_doctor": "🚨 Report Doctor",

    # ── Waitlist ─────────────────────────────────────────────────────────
    "waitlist_joined": "You're on the waitlist! 📋 Current position: #{position}",
    "waitlist_slot_available": (
        "Good news! Dr. {name} is now available. 🎉\n\n"
        "You have 5 minutes to confirm your session."
    ),
    "btn_waitlist_confirm": "✅ Confirm Session",
    "btn_waitlist_skip": "❌ Skip",
    "waitlist_expired": "Your slot offer has expired. You've been moved back in the queue.",

    # ── Search ───────────────────────────────────────────────────────────
    "search_prompt": "What are you looking for?",
    "btn_search_qa": "🔍 Search Q&A",
    "btn_search_doctors": "👨‍⚕️ Find a Doctor",
    "search_enter_term": "Type your search:",
    "search_no_results": "No results found for \"{query}\". Try different keywords.",

    # ── Payments ─────────────────────────────────────────────────────────
    "payment_manual_instructions": (
        "To confirm your session, please transfer {amount} ETB to:\n\n"
        "Bank: {bank_name}\n"
        "Account: {account_number}\n"
        "Name: {account_name}\n\n"
        "Once done, our team will confirm your payment within a few minutes."
    ),
    "payment_confirmed": "✅ Payment confirmed! Your session is approved.",
    "payment_pending": "Your payment is being verified. Hang tight! 🕐",

    # ── Errors ───────────────────────────────────────────────────────────
    "error_generic": "Something went wrong. Please try again or type /start to restart.",
    "error_not_registered": "Please complete registration first. Send /start to begin.",
    "error_not_doctor": "This command is for verified doctors only.",
    "error_not_admin": "You don't have permission to do that.",
    "error_not_moderator": "This command is for moderators only.",
    "error_session_not_found": "Session not found.",
    "error_invalid_input": "That didn't look right — could you try again?",
    "timeout_message": "Your session timed out. Send /start whenever you're ready to continue.",

    # ── Ratings ──────────────────────────────────────────────────────────
    "rate_prompt": "How would you rate your experience with Dr. {name}?",
    "rate_thanks": "Thank you for your feedback! ⭐",

    # ── Abuse / Reports ──────────────────────────────────────────────────
    "report_reason_prompt": "What's the issue?",
    "btn_report_misinformation": "❌ Misinformation",
    "btn_report_inappropriate": "⚠️ Inappropriate",
    "btn_report_other": "📋 Other",
    "report_submitted": "Report received. Our team will review it shortly. 🔍",
    "report_warned": "You have received a formal warning for violating our community guidelines.",
    "report_suspended": "Your account has been suspended pending review. Contact support for assistance.",

    # ── Doctor Registration ─────────────────────────────────────────────
    "doc_reg_name": "Step 1 of 6 — What is your full name?",
    "doc_reg_license": "Step 2 of 6 — What is your medical license number?",
    "doc_reg_specialty": "Step 3 of 6 — What is your specialty?",
    "doc_reg_languages": "Step 4 of 6 — What languages do you consult in?",
    "doc_reg_bio": (
        "Step 5 of 6 — Write a short bio about yourself.\n\n"
        "This will be visible to patients. Include your experience and areas of focus."
    ),
    "doc_reg_photo": (
        "Step 6 of 6 — Please upload a photo of your medical license.\n\n"
        "This is required for verification. You can send it as a photo or document."
    ),
    "doc_reg_confirm": "Please confirm your registration:",
    "doc_reg_pending": (
        "Thank you! Your application is under review.\n\n"
        "We typically respond within 48 hours. "
        "You'll receive a message here once verified."
    ),
    "doc_reg_already_pending": "Your application is still under review. We'll notify you once verified. 🕐",
    "doc_reg_approved": (
        "🎉 Congratulations!\n\n"
        "Your application has been approved. You are now a verified LongiMed doctor.\n\n"
        "Use the menu below to get started."
    ),
    "doc_reg_rejected": (
        "We're sorry. Your application was not approved at this time.\n\n"
        "You may reapply by sending /start and selecting 'I'm a Doctor' again."
    ),
    "btn_submit_application": "✅ Submit Application",
    "btn_lang_english": "🇬🇧 English",
    "btn_lang_amharic": "🇪🇹 Amharic",
    "btn_lang_both": "Both",

    # ── Phone confirmation ────────────────────────────────────────────
    "phone_confirm_prompt": "📱 Your phone number: {phone}\n\nIs this correct?",
    "phone_confirmed": "✅ Phone confirmed!",
    "phone_reenter": "Let's try again. Please share your phone number.",

    # ── Schedule ─────────────────────────────────────────────────────
    "schedule_title": "📅 Your Availability Schedule",
    "schedule_instructions": "Tap a slot to toggle it on/off:",

    # ── Session follow-up ────────────────────────────────────────────
    "session_followup_prompt": "💬 Type your follow-up message below.\nThis will be sent to the doctor who treated you.",
    "session_followup_sent": "✅ Your follow-up message has been sent to the doctor.",
    "session_reply_prompt": "💬 Type your reply to the patient below.",
    "session_reply_sent": "✅ Reply sent to the patient.",

    # ── Navigation ──────────────────────────────────────────────────────
    "nav_back_menu": "← Back to Menu",
    "nav_no_active_session": "No active session found. Use /menu to return to your menu.",
    "nav_session_ended": "Session ended. Waiting for the other party to confirm.",
    "nav_session_resolved": "Session resolved! Thank you.",

    # ── Help ────────────────────────────────────────────────────────────
    "help_patient": (
        "📖 How to use LongiMed\n\n"
        "💬 Ask a Question — Post a health question for our doctors\n"
        "🩺 Private Consultation — Book a 1-on-1 session\n"
        "👨‍⚕️ Browse Doctors — See our verified doctors\n"
        "🔍 Search — Find past Q&A or doctors\n"
        "📋 History — View your past questions and sessions\n\n"
        "Commands:\n"
        "/menu — Show your menu\n"
        "/search — Search Q&A or doctors\n"
        "/end — End active consultation\n"
        "/help — Show this message"
    ),
    "help_doctor": (
        "📖 Doctor Commands\n\n"
        "📋 My Queue — View pending sessions\n"
        "✅ Set Available — Accept new patients\n"
        "🔴 Set Unavailable — Stop accepting patients\n"
        "⭐ My Reviews — See your ratings\n"
        "👤 My Profile — View your profile\n\n"
        "Commands:\n"
        "/menu — Show your menu\n"
        "/end — End active consultation\n"
        "/help — Show this message"
    ),
}
