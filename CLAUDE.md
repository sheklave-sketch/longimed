# Agent Instructions — LongiMed

You're working inside the **WAT framework** (Workflows, Agents, Tools). Probabilistic AI handles reasoning; deterministic code handles execution.

> **Save to memory** after significant sessions. Update `C:\Users\HP\.claude\projects\c--Users-HP-Claude-Projects\memory\longimed.md` with key decisions, discoveries, and architectural changes.

---

## The WAT Architecture

**Layer 1: Workflows** — Markdown SOPs in `workflows/`. Define objective, inputs, tools, outputs, edge cases.
**Layer 2: Agent (you)** — Read workflows, run tools in sequence, handle failures, ask when unclear.
**Layer 3: Tools** — Python scripts in `tools/`. API calls, DB ops, transformations. Credentials in `.env`.

Rules:
- Look for existing tools before building new ones
- When things fail: read error → fix → retest → update workflow
- Don't create or overwrite workflows without asking

---

## Brand

```
Primary teal:   #35C8BB   (cross icon, CTAs)
Secondary blue: #1B8FD4   (hand arc, links, accents)
Dark navy:      #1A2540   (text, headers)
Light bg:       #F5FFFE   (page backgrounds)
White:          #FFFFFF
Font:           Inter (UI), system fallback
```

Logos: `LONGI.png` (horizontal), `LONGI2.png` (stacked/icon)

---

## Tech Stack

```
Bot:          python-telegram-bot v21 (async)
Database:     PostgreSQL 16 (SQLAlchemy async + asyncpg)
Migrations:   Alembic
API:          FastAPI + uvicorn (webhooks + Mini App API)
Mini App:     Next.js 14 + TypeScript → Vercel
Translation:  OpenRouter API → Gemini Flash (Amharic, cached in DB)
Search:       PostgreSQL full-text search (pg_trgm)
Background:   PTB job_queue (Phase I) → Celery + Redis (Phase II)
Payments:     Manual bank transfer (Phase I) → Chapa ETB + Stripe USD (Phase II)
Containers:   Docker + docker-compose
```

---

## Project Structure

```
longimed/
├── CLAUDE.md
├── LONGI.png / LONGI2.png
├── .env.example
├── .env                          ← secrets, NEVER commit
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── alembic.ini
├── alembic/
│   └── versions/
│
├── bot/
│   ├── __init__.py
│   ├── main.py                   ← PTB Application entry point
│   ├── config.py                 ← Pydantic settings
│   ├── database.py               ← async engine + session factory
│   ├── webhook_server.py         ← FastAPI (Mini App API + Phase II webhooks)
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── doctor.py
│   │   ├── question.py
│   │   ├── follow_up.py
│   │   ├── session.py
│   │   ├── relay_message.py
│   │   ├── payment.py
│   │   ├── subscription.py
│   │   ├── moderator.py
│   │   ├── notification.py
│   │   ├── waitlist.py
│   │   ├── doctor_earnings.py
│   │   ├── report.py
│   │   ├── translation.py
│   │   └── settings.py
│   │
│   ├── handlers/
│   │   ├── emergency.py          ← FIRST handler, every message
│   │   ├── start.py              ← /start, role split, onboarding
│   │   ├── patient.py            ← patient onboarding flow
│   │   ├── doctor_onboard.py     ← doctor → Mini App handoff
│   │   ├── public_question.py    ← Flow 1: ask + follow-up
│   │   ├── private_session.py    ← Flow 2: relay + topic modes
│   │   ├── search.py             ← /search command
│   │   ├── doctor.py             ← doctor commands
│   │   ├── moderator.py          ← moderator commands
│   │   ├── admin.py              ← admin commands
│   │   ├── payment.py            ← manual payment + Phase II webhooks
│   │   └── deep_link.py          ← /start payload router
│   │
│   ├── services/
│   │   ├── user_service.py
│   │   ├── doctor_service.py
│   │   ├── question_service.py
│   │   ├── session_service.py
│   │   ├── payment_service.py
│   │   ├── notification_service.py
│   │   ├── search_service.py
│   │   ├── translation_service.py ← OpenRouter/Gemini + DB cache
│   │   ├── waitlist_service.py
│   │   ├── payout_service.py
│   │   └── abuse_service.py
│   │
│   ├── tasks/                    ← PTB job_queue tasks
│   │   ├── session_timer.py      ← doctor response timeout + auto-reassign
│   │   ├── reminders.py          ← expiry warnings, rating reminders
│   │   └── waitlist.py           ← slot freed → notify next in queue
│   │
│   ├── i18n/
│   │   ├── __init__.py           ← t() helper
│   │   ├── en.py                 ← English strings (source of truth)
│   │   └── am.py                 ← Amharic strings (generated + cached via Gemini)
│   │
│   └── utils/
│       ├── emergency.py          ← keyword lists + is_emergency()
│       ├── keyboards.py          ← all InlineKeyboardMarkup builders
│       ├── decorators.py         ← @admin_only, @doctor_only, @moderator_only
│       └── deep_links.py         ← deep link generators + parsers
│
├── miniapp/                      ← Next.js 14 Mini App
│   ├── app/
│   │   ├── page.tsx              ← Doctor directory
│   │   ├── doctor/[id]/page.tsx  ← Public doctor profile + license
│   │   ├── register/page.tsx     ← Doctor registration (multi-step)
│   │   ├── dashboard/page.tsx    ← Doctor dashboard (verified only)
│   │   └── admin/page.tsx        ← Admin reports
│   ├── components/
│   ├── lib/
│   │   └── theme.ts              ← Brand colors + design tokens
│   └── public/
│
├── workflows/
└── tests/
    ├── conftest.py
    ├── test_emergency.py
    ├── test_flows.py
    └── test_search.py
```

---

## Roles

| Role | Access |
|---|---|
| PATIENT | Ask questions, book consultations, search, report |
| DOCTOR | Answer questions, manage sessions, set availability |
| MODERATOR | Approve/reject Q&A, manage follow-ups, handle Q&A reports |
| ADMIN | Everything: doctors, payments, payouts, moderators, reports |

---

## Environment Variables

```bash
# Telegram
TELEGRAM_BOT_TOKEN=
ADMIN_CHAT_IDS=123,456           # comma-separated
PUBLIC_CHANNEL_ID=-100xxx
MINIAPP_URL=https://longimed.vercel.app

# Database
DATABASE_URL=postgresql+asyncpg://medic:password@localhost:5432/longimed

# Redis (Phase II)
REDIS_URL=redis://localhost:6379/0

# OpenRouter (Gemini for Amharic)
OPENROUTER_API_KEY=

# Session config
FREE_TRIAL_DURATION_MINS=15
SINGLE_SESSION_DURATION_MINS=30
DOCTOR_RESPONSE_TIMEOUT_MINS=10
WAITLIST_ACCEPT_TIMEOUT_MINS=5

# Platform
PLATFORM_FEE_PERCENT=20.0

# Phase II (leave blank until ready)
CHAPA_SECRET_KEY=
CHAPA_WEBHOOK_SECRET=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

# App
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## Database Models

### users
```
id, telegram_id (unique), phone (unique, nullable), language (am/en),
consent_given, consent_timestamp, free_trial_used, is_blocked,
warning_count, created_at
```

### doctors
```
id, telegram_id (unique), full_name, license_number (unique),
specialty (enum), languages[], bio, is_verified, is_available,
registration_status (PENDING/APPROVED/REJECTED), rejection_reason,
license_document_file_id, max_concurrent_patients (default 3),
rating_avg, rating_count, applied_at, created_at
```

### questions
```
id, user_id→users, category (specialty enum), text, is_anonymous,
status (PENDING/APPROVED/REJECTED/ANSWERED), rejection_reason,
channel_message_id, moderator_id→moderators, created_at, answered_at
```

### follow_ups
```
id, question_id→questions, user_id→users, text, is_anonymous,
status (PENDING/APPROVED/REJECTED), created_at
```

### sessions
```
id, user_id→users, doctor_id→doctors (nullable), package (FREE_TRIAL/SINGLE/CUSTOM),
status (PENDING_APPROVAL/APPROVED/AWAITING_DOCTOR/ACTIVE/RESOLVED/CANCELLED/EXPIRED),
session_mode (RELAY/TOPIC), issue_description, is_anonymous,
topic_id (null if relay), group_chat_id,
resolution_confirmed_by_doctor, resolution_confirmed_by_patient,
rating, rating_comment, payment_id→payments, started_at, ended_at, created_at
```

### relay_messages
```
id, session_id→sessions, sender_role (PATIENT/DOCTOR),
telegram_message_id, content, media_type, forwarded_message_id, sent_at
```

### payments
```
id, user_id→users, amount_etb, provider (MANUAL/CHAPA/STRIPE),
provider_tx_id, status (PENDING/COMPLETED/FAILED/REFUNDED),
confirmed_by_admin_id, created_at
```

### moderators
```
id, telegram_id, assigned_specialties[], added_by_admin_id, created_at
```

### notifications
```
id, user_id, type, payload (JSON), is_read, created_at
```

### waitlist
```
id, user_id→users, doctor_id (nullable), specialty,
position, status (WAITING/NOTIFIED/ACCEPTED/EXPIRED/LEFT),
notified_at, expires_at, created_at
```

### doctor_earnings
```
id, session_id→sessions, doctor_id→doctors, gross_etb,
fee_percent, net_etb, status (PENDING/PAID), paid_at, paid_by_admin_id
```

### reports
```
id, reporter_id→users, target_type (DOCTOR/PATIENT/QUESTION/ANSWER),
target_id, reason, evidence_file_id, status (OPEN/DISMISSED/WARNED/SUSPENDED),
reviewed_by, resolution, created_at
```

### translations
```
key, lang, text, model_used, created_at
```

### settings (key-value store)
```
key, value, updated_at
(platform_fee_percent, session_durations, etc.)
```

---

## Core Flows

### Emergency Scanner (PRIORITY 1 — register FIRST)
- Runs on every message before any other handler
- Keywords: EN (chest pain, stroke, overdose, suicide, etc.) + AM equivalents
- Response: bilingual 907/991/939 + [📍 Nearest Hospital] Google Maps button
- Logs trigger to DB

### /start + Deep Link Router
```
/start [payload]
  → parse payload → store if user not yet onboarded
  → language selection → consent → role split
  → route to: patient onboarding | doctor onboarding
  → after onboarding: execute stored payload action
```

### Deep Link Payloads
```
book_doctor_{id}         → pre-select doctor in session flow
browse_{specialty}        → open doctor directory filtered
question_{id}            → jump to Q&A thread
follow_up_{question_id}  → open follow-up flow
doctor_profile_{id}      → show doctor card + Mini App link
waitlist_accept_{sid}    → accept freed slot (5min expiry)
report_{type}_{id}       → pre-fill abuse report
```

### Session Mode Decision
```
Private session requested
  └─ is_anonymous?
       YES → Relay mode (bot forwards all messages, stored in relay_messages)
       NO  → Topic mode (Forum thread in private supergroup, bot monitors)
```

### Capacity + Waitlist
```
Doctor at max_concurrent_patients → shows as "Busy 🟡"
Patient joins per-doctor waitlist
Slot freed → notify position 1 → 5min to accept → else notify position 2
Patient can check position or leave waitlist
```

### Payout Flow
```
Session completed → create doctor_earnings record (PENDING)
Admin: /payout_doctor {id} → view pending → confirm → mark PAID
Doctor dashboard (Mini App) shows: total earned | pending | paid out
```

### Notification Matrix
See full matrix in architecture doc. Key priorities:
- URGENT: abuse report on session → admin immediately
- HIGH: slot freed → waitlisted patient (5min window)
- HIGH: session assigned → doctor
- HIGH: doctor silent > timeout → auto-reassign + notify patient
- NORMAL: question approved/rejected, payment confirmed, rating received
- LOW: follow-up on old question, rating received by doctor
- DIGEST: moderator queue > 5 pending → daily batch notification

---

## Translation Service

```python
# All strings in bot/i18n/en.py (source of truth)
# TranslationService on startup:
#   1. Scan all keys in en.py
#   2. Check translations table for cached Amharic
#   3. Batch-call OpenRouter → Gemini Flash for missing keys
#      with system prompt: "Medical translation assistant, Ethiopian Amharic"
#   4. Cache in DB
# t("key", "am") always hits cache — no live API calls during runtime
# Fallback: Amharic cache → English → key
```

---

## UX Rules

1. Max 3 buttons per screen
2. Every screen has 1-2 lines of context before asking anything
3. Always show Back button in multi-step flows
4. Progress indicator on steps ("Step 2 of 5")
5. Errors are friendly + actionable — never raw error codes
6. `conversation_timeout=600` on all ConversationHandlers
7. Never hardcode strings — always `t("key", lang)`
8. Emergency handler registered FIRST in main.py
9. Free trial gated on `user.phone`, not `telegram_id`
10. All DB ops async: `async with session_factory() as session:`
11. `@admin_only`, `@doctor_only`, `@moderator_only` decorators
12. Inline keyboards everywhere except phone capture (reply keyboard)

---

## Build Order

| # | Step |
|---|---|
| 1 | ✅ Scaffold: requirements, Dockerfile, docker-compose, config, database |
| 2 | Models + Alembic migrations |
| 3 | TranslationService + OpenRouter/Gemini |
| 4 | Emergency scanner |
| 5 | /start → role split → patient onboarding |
| 6 | Doctor onboarding → Mini App handoff |
| 7 | Mini App: registration, directory, profile, deep links |
| 8 | Admin + moderator doctor approval |
| 9 | Public Q&A + follow-ups + moderation queue |
| 10 | Search (in-bot + Mini App) |
| 11 | Private session flow (relay + topic) |
| 12 | Waitlist + capacity management |
| 13 | Doctor commands |
| 14 | Admin + moderator commands |
| 15 | Payout tracking |
| 16 | Abuse reporting |
| 17 | Notification system |
| 18 | Session timers + auto-reassignment |
| 19 | Admin reports (Mini App) |
| 20 | Tests + deployment README |
| — | Phase II: Chapa, Stripe, Celery, diaspora page |

---

## Testing Locally

```bash
cp .env.example .env          # fill in values
docker-compose up db redis -d
alembic upgrade head
python -m bot.main

# Test emergency: send "I have chest pain" to bot
# Test admin: add your Telegram ID to ADMIN_CHAT_IDS
# Add doctor: /add_doctor as admin
```
