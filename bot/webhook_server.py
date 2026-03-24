"""
FastAPI webhook server.
Serves:
  - Mini App API  (doctor profiles, directory, Q&A feed)
  - Phase II webhooks  (Chapa, Stripe) — stubs for now
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from bot.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(
    title="LongiMed API",
    docs_url="/docs" if not settings.is_production else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


# ── Mini App: Doctor directory ───────────────────────────────────────────────

@app.get("/api/doctors")
async def list_doctors(specialty: str | None = None):
    """Public doctor directory for Mini App."""
    from bot.database import session_factory
    from bot.models.doctor import Doctor
    from sqlalchemy import select

    try:
        q = select(Doctor).where(Doctor.is_verified.is_(True))
        if specialty:
            from bot.models.doctor import Specialty
            try:
                q = q.where(Doctor.specialty == Specialty(specialty))
            except ValueError:
                pass

        async with session_factory() as session:
            result = await session.execute(q)
            doctors = result.scalars().all()
    except Exception:
        logger.exception("Failed to list doctors")
        raise HTTPException(status_code=500, detail="Internal server error")

    return [
        {
            "id": d.id,
            "full_name": d.full_name,
            "specialty": d.specialty.value if hasattr(d.specialty, "value") else d.specialty,
            "bio": d.bio,
            "is_available": d.is_available,
            "rating_avg": round(d.rating_avg, 2),
            "rating_count": d.rating_count,
            "languages": d.languages,
        }
        for d in doctors
    ]


@app.get("/api/doctors/{doctor_id}")
async def get_doctor(doctor_id: int):
    """Public doctor profile for Mini App."""
    from bot.database import session_factory
    from bot.models.doctor import Doctor

    try:
        async with session_factory() as session:
            doctor = await session.get(Doctor, doctor_id)
    except Exception:
        logger.exception("Failed to fetch doctor %d", doctor_id)
        raise HTTPException(status_code=500, detail="Internal server error")

    if not doctor or not doctor.is_verified:
        raise HTTPException(status_code=404, detail="Doctor not found")

    return {
        "id": doctor.id,
        "full_name": doctor.full_name,
        "specialty": doctor.specialty.value if hasattr(doctor.specialty, "value") else doctor.specialty,
        "bio": doctor.bio,
        "license_number": doctor.license_number,
        "is_available": doctor.is_available,
        "rating_avg": round(doctor.rating_avg, 2),
        "rating_count": doctor.rating_count,
        "languages": doctor.languages,
    }


# ── Mini App: Public Q&A feed ───────────────────────────────────────────────

@app.get("/api/questions")
async def list_questions(limit: int = 20, offset: int = 0):
    """Public Q&A feed for Mini App."""
    from bot.database import session_factory
    from bot.models.question import Question, QuestionStatus
    from sqlalchemy import select

    try:
        async with session_factory() as session:
            result = await session.execute(
                select(Question).where(
                    Question.status.in_([QuestionStatus.APPROVED, QuestionStatus.ANSWERED])
                ).order_by(Question.created_at.desc()).offset(offset).limit(limit)
            )
            questions = result.scalars().all()
    except Exception:
        logger.exception("Failed to list questions")
        raise HTTPException(status_code=500, detail="Internal server error")

    return [
        {
            "id": q.id,
            "category": q.category.value if hasattr(q.category, "value") else q.category,
            "text": q.text,
            "is_anonymous": q.is_anonymous,
            "status": q.status.value,
            "answer_text": q.answer_text,
            "created_at": str(q.created_at),
            "answered_at": str(q.answered_at) if q.answered_at else None,
        }
        for q in questions
    ]


# ── Phase II webhooks (stubs — implement in Step 16) ────────────────────────

@app.post("/webhooks/chapa")
async def chapa_webhook():
    return {"status": "not_implemented"}


@app.post("/webhooks/stripe")
async def stripe_webhook():
    return {"status": "not_implemented"}
