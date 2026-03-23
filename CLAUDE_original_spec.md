# MEDIC BOT — Claude Code Build Instructions
### Ethiopian Telegram Medical Consultation Platform

---

## WHAT YOU ARE BUILDING

A Telegram bot called **Medic Bot** that connects Ethiopian patients with verified
doctors via two service tiers:

1. **Public Q&A channel** — users ask health questions, admin moderates, verified
   doctors answer, all subscribers can read and follow up
2. **Private consultations** — paid 1-on-1 sessions between patients and doctors

Plus two strategic extensions:
- **Diaspora gift subscriptions** — Ethiopians abroad pay in USD to give their
  family back home monthly healthcare access
- **Pilot/corporate mode** — employer or NGO bulk accounts covering their staff

---

## TECH STACK

```
Language:      Python 3.11+
Bot framework: python-telegram-bot v21 (async)
Database:      PostgreSQL (via SQLAlchemy async + asyncpg)
Migrations:    Alembic
Payments:      Chapa SDK (local ETB) + Stripe (USD for diaspora)
Background:    Celery + Redis (session timers, notifications, reminders)
Config:        Pydantic Settings (.env file)
Containerised: Docker + docker-compose (postgres, redis, bot, worker)
Testing:       pytest + pytest-asyncio
```

---

## PROJECT STRUCTURE

```
medic_bot/
├── CLAUDE.md                  ← this file
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── alembic/
│   └── versions/
├── bot/
│   ├── __init__.py
│   ├── main.py                ← entry point, Application setup
│   ├── config.py              ← Pydantic settings
│   ├── database.py            ← async SQLAlchemy engine + session factory
│   │
│   ├── models/                ← SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── doctor.py
│   │   ├── question.py
│   │   ├── session.py
│   │   ├── payment.py
│   │   └── subscription.py    ← diaspora gift subscriptions
│   │
│   ├── handlers/              ← Telegram ConversationHandlers
│   │   ├── __init__.py
│   │   ├── start.py           ← /start, language selection, consent gate
│   │   ├── emergency.py       ← keyword scanner, runs on EVERY message
│   │   ├── public_question.py ← Flow 1: ask public question
│   │   ├── private_session.py ← Flow 2: private consultation
│   │   ├── admin.py           ← admin approval/rejection commands
│   │   ├── doctor.py          ← doctor availability, queue, session commands
│   │   ├── diaspora.py        ← gift subscription webhook handler
│   │   └── payment.py         ← Chapa + Stripe webhook handlers
│   │
│   ├── services/              ← business logic (no Telegram awareness)
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── doctor_service.py
│   │   ├── question_service.py
│   │   ├── session_service.py
│   │   ├── payment_service.py
│   │   ├── subscription_service.py
│   │   └── notification_service.py
│   │
│   ├── tasks/                 ← Celery async tasks
│   │   ├── __init__.py
│   │   ├── session_timer.py   ← auto-reassign if doctor doesn't respond
│   │   └── reminders.py       ← session expiry, follow-up notifications
│   │
│   ├── i18n/                  ← translations
│   │   ├── __init__.py
│   │   ├── am.py              ← Amharic strings
│   │   └── en.py              ← English strings
│   │
│   └── utils/
│       ├── __init__.py
│       ├── emergency.py       ← keyword lists + detection function
│       └── keyboards.py       ← reusable InlineKeyboardMarkup builders
│
└── tests/
    ├── conftest.py
    ├── test_emergency.py
    ├── test_flows.py
    └── test_payment.py
```

---

## ENVIRONMENT VARIABLES (.env.example)

```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
ADMIN_CHAT_IDS=123456789,987654321   # comma-separated Telegram IDs of admins
PUBLIC_CHANNEL_ID=-100xxxxxxxxxx     # Telegram channel ID for public Q&A

# Database
DATABASE_URL=postgresql+asyncpg://medic:password@localhost:5432/medicbot

# Redis
REDIS_URL=redis://localhost:6379/0

# Chapa (local ETB payments)
CHAPA_SECRET_KEY=your_chapa_secret
CHAPA_WEBHOOK_SECRET=your_chapa_webhook_secret

# Stripe (diaspora USD payments)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_BASIC=price_...        # $10/month
STRIPE_PRICE_FAMILY=price_...       # $25/month
STRIPE_PRICE_SENIOR=price_...       # $40/month

# Session config
FREE_TRIAL_DURATION_MINS=15
SINGLE_SESSION_DURATION_MINS=30
DOCTOR_RESPONSE_TIMEOUT_MINS=10     # auto-reassign after this

# App
ENVIRONMENT=development             # or production
LOG_LEVEL=INFO
```

---

## DATABASE MODELS

Build these SQLAlchemy models in `bot/models/`:

### user.py
```python
# Fields: id, telegram_id (unique), phone (unique, nullable until verified),
# language ("am" or "en"), consent_given (bool), consent_timestamp,
# free_trial_used (bool), is_blocked (bool), created_at
# Relationships: questions, sessions, subscription
```

### doctor.py
```python
# Fields: id, telegram_id (unique), full_name, license_number (unique),
# specialty (enum: GENERAL, PEDIATRICS, OBGYN, DERMATOLOGY, MENTAL_HEALTH,
#   CARDIOLOGY, OTHER), languages (array), is_verified (bool),
# is_available (bool), bio, rating_avg (float), rating_count (int),
# max_concurrent_patients (int, default 3), created_at
# Relationships: sessions, schedule_slots
```

### question.py
```python
# Fields: id, user_id (FK), category (same enum as doctor specialty),
# text, is_anonymous (bool), status (enum: PENDING, APPROVED, REJECTED,
#   ANSWERED), rejection_reason, channel_message_id (Telegram msg ID after posting),
# created_at, answered_at
# Relationships: answers (one-to-many)
```

### session.py
```python
# Fields: id, user_id (FK), doctor_id (FK, nullable until assigned),
# package (enum: FREE_TRIAL, SINGLE, CUSTOM), status (enum: PENDING_APPROVAL,
#   APPROVED, AWAITING_DOCTOR, ACTIVE, RESOLVED, CANCELLED, EXPIRED),
# issue_description, is_anonymous (bool), group_chat_id (Telegram group ID),
# started_at, ended_at, resolution_confirmed_by_doctor (bool),
# resolution_confirmed_by_patient (bool), rating (int 1-5), rating_comment,
# payment_id (FK, nullable for free trial), created_at
```

### payment.py
```python
# Fields: id, user_id (FK), amount_etb (Decimal, nullable),
# amount_usd (Decimal, nullable), currency (enum: ETB, USD),
# provider (enum: CHAPA, STRIPE, MANUAL), provider_tx_id, status
# (enum: PENDING, COMPLETED, FAILED, REFUNDED), created_at
```

### subscription.py
```python
# Fields: id, diaspora_telegram_id (int, payer abroad),
# diaspora_email, beneficiary_user_id (FK → User in Ethiopia),
# plan (enum: BASIC, FAMILY, SENIOR), sessions_per_month (int),
# stripe_subscription_id, status (enum: ACTIVE, CANCELLED, PAST_DUE),
# next_billing_date, created_at
```

---

## CORE FLOWS TO IMPLEMENT

### PRIORITY 1 — Emergency Scanner (implement FIRST, runs on every message)

In `bot/utils/emergency.py` create:

```python
EMERGENCY_KEYWORDS_EN = [
    "chest pain", "can't breathe", "cannot breathe", "difficulty breathing",
    "not breathing", "heart attack", "stroke", "severe bleeding", "overdose",
    "poisoning", "suicide", "seizure", "not responding", "unconscious",
    "emergency", "dying", "help me", "passing out"
]

EMERGENCY_KEYWORDS_AM = [
    "የጡቤ ደም", "አልተነሳፕም", "ልፊ አልተነሳፕም", "አቃጠለኝ", "ሞት",
    "እርዳኝ", "ድንገተኛ", "ደም ይወጣል"
]

def is_emergency(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in EMERGENCY_KEYWORDS_EN + EMERGENCY_KEYWORDS_AM)
```

In `bot/handlers/emergency.py` create a MessageHandler with `filters.TEXT` that:
1. Checks `is_emergency(update.message.text)`
2. If True: sends bilingual emergency message with 907 / 991 / 939
3. Offers a [📍 Find Nearest Hospital] button (links to Google Maps hospitals search)
4. Does NOT continue to any other handler
5. Logs the emergency trigger to DB for audit

Register this handler BEFORE all other handlers in `main.py`.

---

### PRIORITY 2 — /start Flow

States for ConversationHandler:
```
LANGUAGE_SELECT → CONSENT → MAIN_MENU
```

Steps:
1. Show language buttons: [🇬🇧 English] [🇪🇹 አማርኛ]
2. Store language choice in DB and `context.user_data`
3. Show full disclaimer text (see i18n files) with [✅ I Agree] / [❌ I Disagree]
4. If disagree: thank them, end conversation
5. If agree: record consent + timestamp in DB
6. Show main menu inline keyboard:
   - [1️⃣ Ask a Question (Public)]
   - [2️⃣ Private Consultation]
   - [3️⃣ Browse Q&A & Doctors]
   - [4️⃣ My History]
   - [⚙️ Settings]

---

### PRIORITY 3 — Public Question Flow (Flow 1)

States:
```
SELECT_CATEGORY → ANONYMITY → ENTER_QUESTION → CONFIRM → PHONE_CAPTURE → DONE
```

Steps:
1. Category selection (inline keyboard of specialties)
2. Anonymous or not
3. Free-text question input
4. Show preview, [✅ Confirm] or [✏️ Edit]
5. Phone number: if first time, request via Telegram's `KeyboardButton(request_contact=True)`
6. Save phone to user record (used for free trial abuse prevention)
7. Save question to DB with status=PENDING
8. Notify all admin chat IDs with question text + [✅ Approve] [❌ Reject] inline buttons
9. Admin taps Approve → status=APPROVED, post to PUBLIC_CHANNEL_ID, notify verified doctors
   in that specialty
10. Admin taps Reject → prompt admin for reason → send reason to user
11. Doctors see notification with [💬 Answer This Question] button
12. Doctor's answer is posted as a reply in the channel; no approval needed
13. Notify question author when answer arrives

---

### PRIORITY 4 — Private Session Flow (Flow 2)

States:
```
CHECK_ELIGIBILITY → SELECT_PACKAGE → SELECT_CATEGORY → SELECT_DOCTOR
→ ENTER_ISSUE → ANONYMITY → CONFIRM → PAYMENT (if needed) → AWAITING_APPROVAL
→ ACTIVE_SESSION → RESOLUTION
```

Key logic:
- Eligibility: if `user.free_trial_used` is True AND no active subscription AND
  no completed payment → redirect to payment
- Free trial is locked to `user.phone` (not telegram_id) — check at eligibility step
- Doctor list: only show doctors where `is_available=True` AND in selected specialty
- If no doctors available: show estimated wait time, offer [📋 Join Waitlist]
- On approval: create a new Telegram group via `bot.create_group` (or use invite links
  to a pre-created group), add user and doctor
- Start Celery task: if doctor doesn't send first message within
  `DOCTOR_RESPONSE_TIMEOUT_MINS`, auto-reassign to next available doctor + notify admin
- Session end: doctor uses /verify_resolution → patient confirms → both confirm
  → rate the doctor (1-5 stars)

---

### PRIORITY 5 — Payment Module

**Chapa (ETB):**
- Generate payment link via Chapa API
- Send link to user as inline button
- Receive webhook at `/webhooks/chapa` (FastAPI or Flask endpoint running alongside bot)
- On success: update payment status, trigger session flow

**Manual (bank transfer):**
- Send bank details to user
- Admin manually marks as paid via `/confirm_payment <user_id> <amount>`

**Stripe (USD — diaspora):**
- Separate webhook at `/webhooks/stripe`
- On `customer.subscription.created`: create/activate subscription record, link to
  beneficiary user, grant sessions_per_month credits
- On `invoice.payment_failed`: send notification to diaspora payer's email
- On `customer.subscription.deleted`: deactivate subscription

---

### PRIORITY 6 — Doctor Commands

Register these as CommandHandlers available only to users whose `telegram_id`
exists in the `doctors` table with `is_verified=True`:

```
/set_available      → doctor.is_available = True
/set_unavailable    → doctor.is_available = False
/set_schedule       → ConversationHandler to set weekly time slots
/view_queue         → list PENDING sessions assigned to this doctor
/accept_session X   → update session status to ACTIVE
/end_session X      → trigger resolution flow
/verify_resolution X → set resolution_confirmed_by_doctor = True
```

---

### PRIORITY 7 — Admin Commands

Register as CommandHandlers, check `update.effective_user.id in ADMIN_CHAT_IDS`:

```
/approve_public X     → approve question, post to channel
/reject_public X      → prompt for reason, notify user
/approve_private X    → approve session, create group, invite parties
/reject_private X     → prompt for reason, notify user
/list_pending         → paginated list of pending questions + sessions
/add_doctor           → ConversationHandler: collect license, specialty, languages
/remove_doctor X      → set doctor.is_verified = False
/view_doctors         → list all doctors + current availability status
/confirm_payment X Y  → manually confirm ETB payment for user X amount Y
```

---

### PRIORITY 8 — Diaspora Subscription Flow

This is a **web flow**, not Telegram:

1. Build a simple 1-page HTML/JS form (or use Stripe Checkout hosted page):
   - "Buy healthcare for your family in Ethiopia"
   - Select plan: Basic $10 / Family $25 / Senior $40
   - Enter their own email + Telegram username of beneficiary in Ethiopia
2. On Stripe checkout success:
   - Webhook creates `Subscription` record
   - Bot sends welcome message to beneficiary via their Telegram username/ID
   - Beneficiary is now treated as a paid user with `sessions_per_month` credits
3. Monthly: Celery task resets session credits on billing anniversary
4. Optional: monthly email summary to diaspora payer (Jinja2 template via SendGrid)

---

## i18n SYSTEM

In `bot/i18n/en.py` and `bot/i18n/am.py`, define all strings as a dict:

```python
# en.py
STRINGS = {
    "welcome": "Welcome to Medic Bot! 🏥\nConnecting you with verified Ethiopian doctors.",
    "select_language": "Please choose your language:",
    "disclaimer_title": "⚠️ IMPORTANT NOTICE",
    "disclaimer_body": (
        "Medic Bot provides general health information and facilitates "
        "communication with licensed medical professionals. It does NOT replace "
        "in-person medical care or emergency services.\n\n"
        "Doctors provide their personal professional opinions. Medic Bot is not "
        "liable for any medical outcome.\n\n"
        "🚨 For emergencies, call 907 immediately."
    ),
    "agree_btn": "✅ I Understand & Agree",
    "disagree_btn": "❌ I Do Not Agree",
    "emergency_title": "🚨 THIS IS AN EMERGENCY",
    "emergency_body": (
        "Please call emergency services immediately:\n\n"
        "🚑 Ambulance: 907\n"
        "👮 Police: 991\n"
        "🚒 Fire: 939\n\n"
        "Once you are safe, you may return to use our service."
    ),
    # ... all other strings
}
```

```python
# Helper in i18n/__init__.py
def t(key: str, lang: str, **kwargs) -> str:
    from bot.i18n import en, am
    strings = am.STRINGS if lang == "am" else en.STRINGS
    text = strings.get(key, en.STRINGS.get(key, key))
    return text.format(**kwargs) if kwargs else text
```

Use `t("welcome", user.language)` everywhere instead of hardcoded strings.

---

## KEYBOARDS (bot/utils/keyboards.py)

Build these reusable keyboards:

```python
def main_menu_keyboard(lang: str) -> InlineKeyboardMarkup
def category_keyboard(lang: str) -> InlineKeyboardMarkup
def package_keyboard(lang: str, has_free_trial: bool) -> InlineKeyboardMarkup
def doctor_list_keyboard(doctors: list[Doctor], lang: str) -> InlineKeyboardMarkup
def confirm_cancel_keyboard(lang: str) -> InlineKeyboardMarkup
def rating_keyboard(session_id: int) -> InlineKeyboardMarkup  # 1-5 stars
def admin_question_keyboard(question_id: int) -> InlineKeyboardMarkup  # approve/reject
```

---

## CELERY TASKS (bot/tasks/)

### session_timer.py
```python
@app.task
def check_doctor_response(session_id: int):
    """
    Called DOCTOR_RESPONSE_TIMEOUT_MINS after session is set to AWAITING_DOCTOR.
    If doctor hasn't sent a message yet:
    - Find next available doctor in same specialty
    - Reassign session
    - Notify admin
    - Notify patient of reassignment
    - If no doctor available: notify admin + patient, offer refund/reschedule
    """
```

### reminders.py
```python
@app.task
def send_session_expiry_warning(session_id: int):
    """Send 5-minute warning before session time limit expires."""

@app.task  
def reset_monthly_subscription_credits():
    """Run on 1st of each month. Reset sessions_per_month credits for all
    active subscriptions based on their billing anniversary."""
```

---

## WEBHOOK SERVER

Run a lightweight FastAPI app alongside the bot to receive payment webhooks:

```python
# bot/webhook_server.py
from fastapi import FastAPI, Request, Header
import hmac, hashlib

app = FastAPI()

@app.post("/webhooks/chapa")
async def chapa_webhook(request: Request, ...):
    # Verify signature, update payment status, trigger session flow

@app.post("/webhooks/stripe")  
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    # Verify webhook signature with STRIPE_WEBHOOK_SECRET
    # Handle: customer.subscription.created, invoice.payment_failed,
    #         customer.subscription.deleted, checkout.session.completed
```

Run with: `uvicorn bot.webhook_server:app --host 0.0.0.0 --port 8000`

---

## DOCKER COMPOSE

```yaml
version: "3.9"
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: medic
      POSTGRES_PASSWORD: password
      POSTGRES_DB: medicbot
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  bot:
    build: .
    command: python -m bot.main
    env_file: .env
    depends_on: [db, redis]
    restart: unless-stopped

  worker:
    build: .
    command: celery -A bot.tasks worker --loglevel=info
    env_file: .env
    depends_on: [db, redis]
    restart: unless-stopped

  webhooks:
    build: .
    command: uvicorn bot.webhook_server:app --host 0.0.0.0 --port 8000
    env_file: .env
    ports:
      - "8000:8000"
    depends_on: [db, redis]
    restart: unless-stopped

volumes:
  pgdata:
```

---

## BUILD ORDER FOR CLAUDE CODE

Work through these in order. Do not skip ahead.

**Step 1:** Scaffold the project structure, requirements.txt, docker-compose.yml,
.env.example, Dockerfile, config.py (Pydantic settings), database.py

**Step 2:** Create all SQLAlchemy models and run `alembic init` + first migration

**Step 3:** Implement emergency keyword scanner + register as first handler — test it
manually by sending "chest pain" to the bot

**Step 4:** Implement /start flow with language selection + consent gate

**Step 5:** Implement public question flow end-to-end (user → admin → channel → doctor
→ answer → notification)

**Step 6:** Implement private session flow without payment (free trial only first)

**Step 7:** Add Chapa payment integration for paid sessions

**Step 8:** Add doctor-side commands (/set_available, /view_queue, /accept_session, etc.)

**Step 9:** Add admin commands

**Step 10:** Add Celery tasks (session timer, auto-reassignment)

**Step 11:** Add Stripe + diaspora subscription webhook server

**Step 12:** Write tests for emergency detection, consent gate, and session state machine

**Step 13:** Write deployment README (how to run on a VPS with nginx reverse proxy
for webhooks)

---

## KEY RULES FOR CLAUDE CODE TO FOLLOW

1. **Never hardcode strings** — always use the `t()` i18n helper
2. **Emergency handler must be first** — register before all other handlers in main.py
3. **Free trial is phone-gated** — check `user.phone` not `user.telegram_id` for trial eligibility
4. **All DB operations are async** — use `async with session_factory() as session:`
5. **Inline keyboards everywhere** — no reply keyboards except for phone number capture
6. **Log everything** — use Python `logging` with structured fields (user_id, action, timestamp)
7. **Webhook signatures must be verified** — never trust Chapa/Stripe webhooks without checking signature
8. **Admin check is a decorator** — create `@admin_only` decorator for admin handlers
9. **Doctor check is a decorator** — create `@doctor_only` decorator for doctor handlers
10. **ConversationHandler timeouts** — set `conversation_timeout=600` (10 min) so stale
    conversations don't block users

---

## TESTING THE BOT LOCALLY

```bash
# 1. Copy and fill env
cp .env.example .env

# 2. Start infrastructure
docker-compose up db redis -d

# 3. Run migrations
alembic upgrade head

# 4. Start bot in dev mode
python -m bot.main

# 5. In a second terminal, start webhook server
uvicorn bot.webhook_server:app --reload --port 8000

# 6. For Stripe webhooks locally:
stripe listen --forward-to localhost:8000/webhooks/stripe
```

To test emergency detection: open Telegram, message the bot "I have chest pain"

To create a test admin: set your own Telegram ID in `ADMIN_CHAT_IDS` in .env

To create a test doctor: use `/add_doctor` command as admin

---

## PACKAGES (requirements.txt)

```
python-telegram-bot[job-queue]==21.6
sqlalchemy[asyncio]==2.0.31
asyncpg==0.29.0
alembic==1.13.2
pydantic-settings==2.4.0
fastapi==0.112.2
uvicorn==0.30.6
celery==5.4.0
redis==5.0.8
httpx==0.27.2
stripe==10.8.0
jinja2==3.1.4
python-dotenv==1.0.1
pytest==8.3.2
pytest-asyncio==0.23.8
```
