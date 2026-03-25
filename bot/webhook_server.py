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


# ── User role check ───────────────────────────────────────────────────────────

@app.get("/api/user/role/{telegram_id}")
async def get_user_role(telegram_id: int):
    from bot.database import session_factory
    from bot.models.doctor import Doctor
    from sqlalchemy import select

    is_admin = telegram_id in settings.admin_ids
    is_doctor = False

    try:
        async with session_factory() as session:
            result = await session.execute(
                select(Doctor).where(
                    Doctor.telegram_id == telegram_id,
                    Doctor.is_verified.is_(True),
                )
            )
            is_doctor = result.scalar_one_or_none() is not None
    except Exception:
        pass

    return {"is_doctor": is_doctor, "is_admin": is_admin}


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


# ── Doctor Dashboard ──────────────────────────────────────────────────────

@app.get("/api/doctors/dashboard/{telegram_id}")
async def doctor_dashboard(telegram_id: int):
    from bot.database import session_factory
    from bot.models.doctor import Doctor
    from bot.models.session import Session as CS, SessionStatus
    from bot.models.doctor_earnings import DoctorEarnings, EarningsStatus
    from sqlalchemy import select, func

    try:
        async with session_factory() as session:
            doc_r = await session.execute(
                select(Doctor).where(Doctor.telegram_id == telegram_id, Doctor.is_verified.is_(True))
            )
            doctor = doc_r.scalar_one_or_none()
            if not doctor:
                raise HTTPException(status_code=404, detail="Not found")

            total = (await session.execute(
                select(func.count()).select_from(CS).where(CS.doctor_id == doctor.id)
            )).scalar() or 0
            active = (await session.execute(
                select(func.count()).select_from(CS).where(CS.doctor_id == doctor.id, CS.status == SessionStatus.ACTIVE)
            )).scalar() or 0
            pending = (await session.execute(
                select(func.count()).select_from(CS).where(CS.doctor_id == doctor.id, CS.status == SessionStatus.AWAITING_DOCTOR)
            )).scalar() or 0
            pending_earn = (await session.execute(
                select(func.coalesce(func.sum(DoctorEarnings.net_etb), 0)).where(
                    DoctorEarnings.doctor_id == doctor.id, DoctorEarnings.status == EarningsStatus.PENDING)
            )).scalar() or 0
            paid_earn = (await session.execute(
                select(func.coalesce(func.sum(DoctorEarnings.net_etb), 0)).where(
                    DoctorEarnings.doctor_id == doctor.id, DoctorEarnings.status == EarningsStatus.PAID)
            )).scalar() or 0
            recent = (await session.execute(
                select(CS).where(CS.doctor_id == doctor.id).order_by(CS.created_at.desc()).limit(10)
            )).scalars().all()
    except HTTPException:
        raise
    except Exception:
        logger.exception("Dashboard error")
        raise HTTPException(status_code=500, detail="Error")

    return {
        "doctor": {
            "full_name": doctor.full_name,
            "specialty": doctor.specialty.value if hasattr(doctor.specialty, "value") else doctor.specialty,
            "is_available": doctor.is_available,
            "rating_avg": round(doctor.rating_avg, 2),
            "rating_count": doctor.rating_count,
        },
        "stats": {
            "total_sessions": total, "active_sessions": active, "pending_queue": pending,
            "pending_earnings": float(pending_earn), "paid_earnings": float(paid_earn),
        },
        "recent_sessions": [
            {"id": s.id, "status": s.status.value if hasattr(s.status, "value") else s.status,
             "issue_description": s.issue_description[:100], "created_at": str(s.created_at)}
            for s in recent
        ],
    }


@app.post("/api/doctors/toggle-availability/{telegram_id}")
async def toggle_availability(telegram_id: int):
    from bot.database import session_factory
    from bot.models.doctor import Doctor
    from sqlalchemy import select
    async with session_factory() as session:
        r = await session.execute(select(Doctor).where(Doctor.telegram_id == telegram_id, Doctor.is_verified.is_(True)))
        doctor = r.scalar_one_or_none()
        if not doctor:
            raise HTTPException(status_code=404)
        doctor.is_available = not doctor.is_available
        await session.commit()
    return {"is_available": doctor.is_available}


# ── Admin Dashboard ──────────────────────────────────────────────────────

@app.get("/api/admin/dashboard/{telegram_id}")
async def admin_dashboard(telegram_id: int):
    if telegram_id not in settings.admin_ids:
        raise HTTPException(status_code=403, detail="Forbidden")
    from bot.database import session_factory
    from bot.models.user import User
    from bot.models.doctor import Doctor, RegistrationStatus
    from bot.models.question import Question, QuestionStatus
    from bot.models.session import Session as CS
    from bot.models.payment import Payment
    from sqlalchemy import select, func
    try:
        async with session_factory() as session:
            tu = (await session.execute(select(func.count()).select_from(User))).scalar() or 0
            td = (await session.execute(select(func.count()).select_from(Doctor).where(Doctor.is_verified.is_(True)))).scalar() or 0
            tq = (await session.execute(select(func.count()).select_from(Question))).scalar() or 0
            ts = (await session.execute(select(func.count()).select_from(CS))).scalar() or 0
            pd = (await session.execute(select(func.count()).select_from(Doctor).where(Doctor.registration_status == RegistrationStatus.PENDING))).scalar() or 0
            pq = (await session.execute(select(func.count()).select_from(Question).where(Question.status == QuestionStatus.PENDING))).scalar() or 0
            pending_docs = (await session.execute(select(Doctor).where(Doctor.registration_status == RegistrationStatus.PENDING).order_by(Doctor.applied_at.desc()))).scalars().all()
            payments = (await session.execute(select(Payment).order_by(Payment.created_at.desc()).limit(20))).scalars().all()
    except Exception:
        logger.exception("Admin dashboard error")
        raise HTTPException(status_code=500)
    return {
        "stats": {"total_users": tu, "total_doctors": td, "total_questions": tq, "total_sessions": ts, "pending_doctors": pd, "pending_questions": pq},
        "pending_doctors": [
            {"id": d.id, "full_name": d.full_name, "specialty": d.specialty.value if hasattr(d.specialty, "value") else d.specialty,
             "license_number": d.license_number, "applied_at": str(d.applied_at) if d.applied_at else ""}
            for d in pending_docs
        ],
        "recent_payments": [
            {"id": p.id, "amount_etb": float(p.amount_etb) if p.amount_etb else 0,
             "status": p.status.value if hasattr(p.status, "value") else p.status,
             "created_at": str(p.created_at), "user_telegram_id": p.user_id}
            for p in payments
        ],
    }


@app.post("/api/admin/doctors/{doctor_id}/{action}")
async def admin_doctor_action(doctor_id: int, action: str):
    if action not in ("approve", "reject"):
        raise HTTPException(status_code=400)
    from bot.database import session_factory
    from bot.models.doctor import Doctor, RegistrationStatus
    async with session_factory() as session:
        doctor = await session.get(Doctor, doctor_id)
        if not doctor:
            raise HTTPException(status_code=404)
        if action == "approve":
            doctor.is_verified = True
            doctor.registration_status = RegistrationStatus.APPROVED
        else:
            doctor.registration_status = RegistrationStatus.REJECTED
        await session.commit()
    return {"status": "ok", "action": action}


# ── Phase II webhooks (stubs) ──────────────────────────────────────────────

@app.post("/webhooks/chapa")
async def chapa_webhook():
    return {"status": "not_implemented"}


@app.post("/webhooks/stripe")
async def stripe_webhook():
    return {"status": "not_implemented"}
